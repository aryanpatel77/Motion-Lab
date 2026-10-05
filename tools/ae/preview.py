#!/usr/bin/env python3
"""Render a generated .jsx scene WITHOUT After Effects, to check layout before it goes to AE.

  python3 tools/ae/preview.py out/promo-kinetic-20s.jsx --at 0.5,2.3,5.2 --out out/ae-preview

Draws the same scene description the AE runtime consumes (solids, shapes, grids, text with the shipped
TTFs, footage, rect masks, parenting, position/opacity/scale keys) using PIL. It is an approximation —
no glows, blurs or trim paths — but it catches the things that actually go wrong: positions, text
widths, grid patterns that collapse into slabs, layers that never appear.
"""
import argparse
import json
import os
import re
import sys

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = {
    "Inter": "Inter-Regular.ttf", "Inter-600": "Inter-SemiBold.ttf",
    "Instrument Serif": "InstrumentSerif-Italic.ttf", "JetBrains Mono": "JetBrainsMono-Regular.ttf",
    "Libre Caslon Text": "LibreCaslonText-Bold.ttf",
    "Briallen Disco": "BriallenDisco-Regular.ttf", "Geist": "Geist-Regular.otf",
}
_cache = {}


def font(name, size, assets_dir=None):
    key = (name, int(size))
    if key in _cache:
        return _cache[key]
    fn = FONTS.get(name or "Inter", FONTS["Inter"])
    for base in ([assets_dir] if assets_dir else []) + [os.path.join(HERE, "fonts")]:
        p = os.path.join(base or "", fn)
        if os.path.exists(p):
            _cache[key] = ImageFont.truetype(p, int(size))
            return _cache[key]
    _cache[key] = ImageFont.load_default()
    return _cache[key]


def val_at(spec, t, default=None):
    """sample a keyframed property (linear between keys; hold for text/hold eases)"""
    if not spec:
        return default
    keys = spec["keys"]
    if len(keys) == 1 or t <= keys[0][0]:
        return keys[0][1]
    if t >= keys[-1][0]:
        return keys[-1][1]
    for i in range(len(keys) - 1):
        t0, v0 = keys[i]
        t1, v1 = keys[i + 1]
        if t0 <= t <= t1:
            if spec["ease"] == "hold" or isinstance(v0, str):
                return v0
            f = (t - t0) / (t1 - t0) if t1 > t0 else 0
            f = f * f * (3 - 2 * f) if spec["ease"] == "inout" else f
            if isinstance(v0, list):
                return [a + (b - a) * f for a, b in zip(v0, v1)]
            return v0 + (v1 - v0) * f
    return keys[-1][1]


def col(c, a=1.0):
    return tuple(int(max(0, min(1, x)) * 255) for x in c) + (int(a * 255),)


def render(scene, t, assets_dir):
    c = scene["comp"]
    img = Image.new("RGBA", (c["w"], c["h"]), col(c["bg"]))
    by_name = {l["name"]: l for l in scene["layers"]}
    for L in scene["layers"]:
        if t < L.get("in", 0) - 1e-6 or t > L.get("out", c["duration"]) + 1e-6:
            continue
        props = L.get("props", {})
        op = val_at(props.get("opacity"), t, 100) / 100.0
        if op <= 0.01:
            continue
        pos = val_at(props.get("position"), t, L.get("pos", [0, 0]))
        sc = val_at(props.get("scale"), t, [100, 100])
        sc = sc if isinstance(sc, list) else [sc, sc]
        chain, cur, guard = [], L, 0                     # AE resolves parent chains; follow them all
        while cur.get("parent") and cur["parent"] in by_name and guard < 8:
            cur = by_name[cur["parent"]]; chain.append(cur); guard += 1
        for p in chain:                                      # AE keeps world position when parenting:
            pp = p.get("props", {})                          # the child only follows the parent's change
            t0 = min([k[0] for k in pp.get("position", {}).get("keys", [[0]])] + [0])
            p_now = val_at(pp.get("position"), t, p.get("pos", [0, 0]))
            p_ref = val_at(pp.get("position"), t0, p.get("pos", [0, 0]))
            s_now = val_at(pp.get("scale"), t, [100, 100]); s_now = s_now if isinstance(s_now, list) else [s_now, s_now]
            s_ref = val_at(pp.get("scale"), t0, [100, 100]); s_ref = s_ref if isinstance(s_ref, list) else [s_ref, s_ref]
            k = [s_now[0] / (s_ref[0] or 100), s_now[1] / (s_ref[1] or 100)]
            pos = [p_now[0] + (pos[0] - p_ref[0]) * k[0], p_now[1] + (pos[1] - p_ref[1]) * k[1]]
            sc = [sc[0] * k[0], sc[1] * k[1]]

        lay = Image.new("RGBA", (c["w"], c["h"]), (0, 0, 0, 0))
        d = ImageDraw.Draw(lay)
        x, y = pos
        if L["kind"] == "solid":
            w, h = L["size"][0] * sc[0] / 100, L["size"][1] * sc[1] / 100
            d.rectangle([x, y, x + w, y + h], fill=col(L["color"]))
        elif L["kind"] == "shape":
            sh = L["shape"]
            if sh["kind"] == "grid":
                cell, sq = sh["cell"], sh["square"]
                for gx in range(max(1, int(sh["size"][0] // cell))):
                    for gy in range(max(1, int(sh["size"][1] // cell))):
                        px, py = x + gx * cell, y + gy * cell
                        d.rectangle([px, py, px + sq, py + sq], fill=col(sh["fill"]))
            else:
                w, h = sh["size"][0] * sc[0] / 100, sh["size"][1] * sc[1] / 100
                box = [x, y, x + w, y + h]
                r = min(sh.get("radius", 0), w / 2, h / 2)
                fill = col(sh["fill"]) if sh.get("fill") else None
                outline = col(sh["stroke"]) if sh.get("stroke") else None
                if sh.get("trim"):
                    fill = None
                    outline = outline or (255, 255, 255, 255)
                if r > 1:
                    d.rounded_rectangle(box, radius=r, fill=fill, outline=outline, width=int(sh.get("strokeW", 0) or 0))
                else:
                    d.rectangle(box, fill=fill, outline=outline, width=int(sh.get("strokeW", 0) or 0))
        elif L["kind"] == "text":
            tx = L["text"]
            txt = val_at(props.get("sourceText"), t, tx["value"])
            f = font(tx.get("font"), tx["size"] * (tx.get("stretch", 100) / 100), None)
            lead = tx.get("leading") or tx["size"] * 1.2
            for i, line in enumerate(str(txt).split("\n")):
                try:                                              # AE point text sits on its baseline
                    d.text((x, y + i * lead), line, font=f, fill=col(tx["color"]), anchor="ls")
                except ValueError:
                    d.text((x, y - tx["size"] * 0.72 + i * lead), line, font=f, fill=col(tx["color"]))
        elif L["kind"] == "footage":
            f = os.path.join(assets_dir, os.path.basename(next(
                (a["file"] for a in scene.get("assets", []) if a["id"] == L.get("asset")), "")))
            if os.path.exists(f):
                im = Image.open(f).convert("RGBA")
                w, h = (L["size"] or [im.width, im.height])
                im = im.resize((max(1, int(w * sc[0] / 100)), max(1, int(h * sc[1] / 100))))
                lay.alpha_composite(im, (int(x), int(y)))

        if L.get("mask"):
            r = val_at(L["mask"], t)
            if L["mask"].get("space") == "layer":                # AE masks live in layer space
                r = [x + r[0] * sc[0] / 100, y + r[1] * sc[1] / 100, r[2] * sc[0] / 100, r[3] * sc[1] / 100]
            m = Image.new("L", (c["w"], c["h"]), 0)
            ImageDraw.Draw(m).rectangle([r[0], r[1], r[0] + r[2], r[1] + r[3]], fill=255)
            lay.putalpha(Image.composite(lay.getchannel("A"), Image.new("L", m.size, 0), m))
        if op < 1:
            lay.putalpha(lay.getchannel("A").point(lambda v: int(v * op)))
        img.alpha_composite(lay)
    return img.convert("RGB")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("jsx")
    ap.add_argument("--at", default="1,3,5,8,11,14,17,19")
    ap.add_argument("--out", default=None)
    ap.add_argument("--scale", type=float, default=0.5)
    a = ap.parse_args()
    src = open(a.jsx).read()
    scene = json.loads(re.search(r"MotionLab\.build\((\{.*\})\);\s*$", src, re.S).group(1))
    assets_dir = os.path.splitext(a.jsx)[0] + "_assets"
    out = a.out or os.path.splitext(a.jsx)[0] + "_preview"
    os.makedirs(out, exist_ok=True)
    for ts in a.at.split(","):
        t = float(ts)
        im = render(scene, t, assets_dir)
        if a.scale != 1:
            im = im.resize((int(im.width * a.scale), int(im.height * a.scale)))
        im.save(os.path.join(out, f"t{t:06.2f}.jpg"), quality=85)
    print(f"wrote {len(a.at.split(','))} frames to {out}")


if __name__ == "__main__":
    main()
