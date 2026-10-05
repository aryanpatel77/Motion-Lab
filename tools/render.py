#!/usr/bin/env python3
"""Render a Motion Lab template with your own copy, colours and media.

  render.py <template-id> [--set name="Neel Sharma" --set theme=blue]
            [--slot screen=/path/app-recording.mp4]
            [--format mp4|mov|png-sequence|gif] [--out out/my-clip.mp4] [--fps 30] [--list]

mov = ProRes 4444 with alpha (for Premiere / After Effects / Descript).
Params come from templates/registry.json; anything not set falls back to the template's default.
"""
import argparse
import json
import os
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REG = os.path.join(ROOT, "templates", "registry.json")
CLI = "hyperframes@0.8.59"
EXT = {"mp4": ".mp4", "mov": ".mov", "gif": ".gif", "png-sequence": ""}


def registry():
    return json.load(open(REG))


def find(tid):
    for t in registry()["templates"]:
        if t["id"] == tid:
            return t
    sys.exit(f"unknown template '{tid}'. Known: " + ", ".join(t['id'] for t in registry()['templates']))


def coerce(spec, raw):
    k = spec.get("type")
    if k == "boolean":
        return raw.lower() in ("1", "true", "yes", "on")
    if k == "number":
        return float(raw)
    if k == "enum" and raw not in spec.get("options", []):
        sys.exit(f"value '{raw}' not in {spec['options']}")
    return raw


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("template", nargs="?")
    ap.add_argument("--set", action="append", default=[], metavar="key=value")
    ap.add_argument("--slot", action="append", default=[], metavar="id=path")
    ap.add_argument("--format", default="mp4", choices=list(EXT))
    ap.add_argument("--fps")
    ap.add_argument("--out")
    ap.add_argument("--quality", default="delivery")
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args()

    if a.list or not a.template:
        for t in registry()["templates"]:
            ps = ", ".join(k for k in t.get("params", {}) if not k.startswith("$"))
            print(f"{t['id']:<22} {t['title']:<42} {t['duration']}s  params: {ps or '-'}")
        return

    t = find(a.template)
    proj = os.path.join(ROOT, "templates", t["id"])
    specs = {k: v for k, v in t.get("params", {}).items() if not k.startswith("$")}
    vals = {k: v["default"] for k, v in specs.items()}
    for s in a.set:
        k, _, raw = s.partition("=")
        if k not in specs:
            sys.exit(f"'{k}' is not a param of {t['id']}. Available: {', '.join(specs) or 'none'}")
        vals[k] = coerce(specs[k], raw)

    for s in a.slot:                                     # drop-in media (e.g. an app screen recording)
        sid, _, path = s.partition("=")
        if sid not in [x["id"] for x in t.get("slots", [])]:
            sys.exit(f"'{sid}' is not a slot of {t['id']}")
        if not os.path.isfile(path):
            sys.exit(f"no such file: {path}")
        dst = os.path.join(proj, "assets", f"slot-{sid}{os.path.splitext(path)[1]}")
        shutil.copy(path, dst)
        print(f"slot {sid} -> {os.path.relpath(dst, ROOT)}")

    fps = a.fps or str(t.get("fps", 30))
    out = a.out or os.path.join(ROOT, "out", f"{t['id']}{EXT[a.format]}" if a.format != "png-sequence" else f"{t['id']}-frames")
    os.makedirs(os.path.dirname(os.path.abspath(out)) or ".", exist_ok=True)
    cmd = ["npx", "--yes", CLI, "render", "--fps", fps, "--quality", a.quality, "-o", os.path.abspath(out)]
    if a.format != "mp4":
        cmd += ["--format", a.format]
    if vals:
        cmd += ["--variables", json.dumps(vals)]
    print("$", " ".join(cmd))
    r = subprocess.run(cmd, cwd=proj)
    if r.returncode:
        sys.exit(r.returncode)
    print("wrote", out)
    if a.format == "mov":
        print("ProRes 4444 with alpha — drag straight onto a Premiere / After Effects timeline.")


if __name__ == "__main__":
    main()
