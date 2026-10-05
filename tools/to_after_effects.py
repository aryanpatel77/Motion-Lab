#!/usr/bin/env python3
"""Export a Motion Lab template as an EDITABLE After Effects project.

  to_after_effects.py <template-id> [--set key=value ...] [--out out/name.jsx]

Writes <name>.jsx plus <name>_assets/ (icons etc). In AE:
  File > Scripts > Run Script File…  →  pick the .jsx   (keep the assets folder beside it)

You get live text layers, shape layers with Trim Paths / Repeaters, masks, solids and keyframes —
so text, colour, timing and easing stay editable, and you can export a .mogrt from there for Premiere.
Texture-heavy details (starfields, LED dot texture, particle swarms) are simplified; for a pixel-exact
look, render the alpha ProRes instead: render.py <id> --format mov
"""
import argparse
import json
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ae import icons, tpl_frontier, tpl_lower_third, tpl_lower_third_v1, tpl_promo  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUNTIME = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ae", "runtime.jsx")
BUILDERS = {
    "lower-third-nestgen": lambda p, a: tpl_lower_third.build(p),
    "lower-third-nestgen-v1": lambda p, a: tpl_lower_third_v1.build(p),
    "promo-kinetic-20s": lambda p, a: tpl_promo.build(p, a),
    "frontier-explainer-9s": lambda p, a: tpl_frontier.build(p, a),
}
NEEDS_ICONS = {"promo-kinetic-20s", "frontier-explainer-9s"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("template")
    ap.add_argument("--set", action="append", default=[], metavar="key=value")
    ap.add_argument("--out")
    ap.add_argument("--zip", action="store_true", help="also package script + assets into a .zip")
    a = ap.parse_args()
    if a.template not in BUILDERS:
        sys.exit(f"no After Effects builder for '{a.template}'. Available: {', '.join(BUILDERS)}")

    params = {}
    for s in a.set:
        k, _, v = s.partition("=")
        params[k] = v

    out = os.path.abspath(a.out or os.path.join(ROOT, "out", f"{a.template}.jsx"))
    os.makedirs(os.path.dirname(out), exist_ok=True)
    assets_dir = os.path.splitext(out)[0] + "_assets"
    assets = icons.write_all(assets_dir) if a.template in NEEDS_ICONS else {}
    if a.template == "lower-third-nestgen":                  # bar surface texture sized to this name
        assets.update(tpl_lower_third.write_assets(params, assets_dir))

    # AE cannot use the .woff2 web fonts — ship installable TTFs alongside the script
    fonts_src = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ae", "fonts")
    fonts_dst = os.path.join(assets_dir, "fonts")
    if os.path.isdir(fonts_src):
        os.makedirs(fonts_dst, exist_ok=True)
        for f in os.listdir(fonts_src):
            shutil.copy(os.path.join(fonts_src, f), os.path.join(fonts_dst, f))

    scene = BUILDERS[a.template](params, assets)
    scene.d["assets"] = [{"id": k, "file": f"{os.path.basename(assets_dir)}/{v}"} for k, v in assets.items()]
    scene.d["notes"].insert(0, "Install the TTFs in <script>_assets/fonts first — AE substitutes fonts it does not have.")

    runtime = open(RUNTIME).read()
    body = (f"// Motion Lab — {a.template}\n// Generated; edit the comp in AE, or re-export after changing the template.\n"
            f"{runtime}\nMotionLab.build({scene.json()});\n")
    open(out, "w").write(body)
    n_layers = len(scene.d["layers"])
    print(f"wrote {os.path.relpath(out, ROOT)}  ({n_layers} layers"
          + (f", {len(assets)} icons" if assets else "")
          + (f", {len(os.listdir(fonts_dst))} fonts" if os.path.isdir(fonts_dst) else "") + f" in {os.path.basename(assets_dir)}/)")
    print("Install the fonts in that folder before running the script, or AE will substitute them.")
    if a.zip:
        import zipfile
        zpath = os.path.splitext(out)[0] + ".zip"
        with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
            z.write(out, os.path.basename(out))
            for root, _, files in os.walk(assets_dir):
                for f in files:
                    full = os.path.join(root, f)
                    z.write(full, os.path.relpath(full, os.path.dirname(out)))
        print("zipped:", os.path.relpath(zpath, ROOT))
    print("In After Effects: File > Scripts > Run Script File…  then pick that file (keep the assets folder next to it).")


if __name__ == "__main__":
    main()
