#!/usr/bin/env python3
"""Static checks on a generated .jsx before it goes near After Effects.

  python3 tools/ae/validate.py out/promo-kinetic-20s.jsx

Catches what can be caught without AE: malformed scene JSON, unknown layer kinds or properties,
missing parents, keyframes outside the comp, layers that are never visible, missing asset files.
"""
import json
import os
import re
import sys

KINDS = {"solid", "text", "shape", "footage", "null"}
PROPS = {"position", "opacity", "scale", "rotation", "anchor", "sourceText", "trimStart", "trimEnd",
         "fillColor", "strokeWidth"}
EFFECTS = {"glow", "ramp", "blur", "tint"}


def main(path):
    src = open(path).read()
    m = re.search(r"MotionLab\.build\((\{.*\})\);\s*$", src, re.S)
    if not m:
        sys.exit("FAIL: no MotionLab.build(...) call at the end of the file")
    try:
        scene = json.loads(m.group(1))
    except json.JSONDecodeError as e:
        sys.exit(f"FAIL: scene JSON is invalid — {e}")

    errs, warns = [], []
    comp = scene["comp"]
    dur = comp["duration"]
    names = [l["name"] for l in scene["layers"]]
    dupes = {n for n in names if names.count(n) > 1}
    if dupes:
        warns.append(f"duplicate layer names (AE allows it, but parenting picks the first): {sorted(dupes)[:5]}")

    base = os.path.dirname(os.path.abspath(path))
    for a in scene.get("assets", []):
        if not os.path.exists(os.path.join(base, a["file"])):
            errs.append(f"missing asset file: {a['file']}")
    asset_ids = {a["id"] for a in scene.get("assets", [])}

    for l in scene["layers"]:
        n = l["name"]
        if l["kind"] not in KINDS:
            errs.append(f"{n}: unknown kind '{l['kind']}'")
        if l["kind"] == "footage" and l.get("asset") not in asset_ids:
            errs.append(f"{n}: references asset '{l.get('asset')}' that is not declared")
        if l["kind"] == "text" and not str(l.get("text", {}).get("value", "")).strip():
            warns.append(f"{n}: empty text layer")
        for p, spec in (l.get("props") or {}).items():
            if p not in PROPS:
                errs.append(f"{n}: unsupported property '{p}'")
            ts = [k[0] for k in spec["keys"]]
            if ts != sorted(ts):
                errs.append(f"{n}.{p}: keyframes are not in time order")
            if any(t < -0.001 or t > dur + 0.001 for t in ts):
                errs.append(f"{n}.{p}: keyframe outside the comp (0–{dur}s): {ts}")
            if p == "sourceText" and spec["ease"] != "hold":
                warns.append(f"{n}: Source Text keys should be HOLD, got {spec['ease']}")
            dims = {len(k[1]) if isinstance(k[1], list) else 1 for k in spec["keys"]}
            if len(dims) > 1:
                errs.append(f"{n}.{p}: mixed value shapes {dims}")
        for e in l.get("effects", []):
            if e["name"] not in EFFECTS:
                errs.append(f"{n}: unsupported effect '{e['name']}'")
        if l.get("parent") and l["parent"] not in names:
            errs.append(f"{n}: parent '{l['parent']}' does not exist")
        i, o = l.get("in", 0), l.get("out", dur)
        if o <= i:
            errs.append(f"{n}: never visible (in {i} >= out {o})")
        if l.get("mask"):
            for t, r in l["mask"]["keys"]:
                if len(r) != 4:
                    errs.append(f"{n}: mask key at {t} is not [x,y,w,h]")
                elif r[2] <= 0 or r[3] <= 0:
                    errs.append(f"{n}: mask at {t} has non-positive size {r[2]}x{r[3]}")

    print(f"{os.path.basename(path)}: {len(scene['layers'])} layers, {len(scene.get('assets', []))} assets, "
          f"comp {comp['w']}x{comp['h']} @ {comp['fps']}fps, {dur}s")
    for w in warns:
        print("  warn:", w)
    for e in errs:
        print("  ERROR:", e)
    print("  OK — no structural errors" if not errs else f"  {len(errs)} error(s)")
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
