#!/usr/bin/env python3
"""Reference-vs-ours breakdown film: the reference and our rebuild play side by side, section by section.

  breakdown.py --ref ref.mp4 --ours ours.mp4 --map map.json --out out/breakdown.mp4

map.json:
  {"title": "...", "ref_label": "Reference", "ours_label": "Ours",
   "sections": [{"name": "Shape morph", "technique": "Shapes nest, rotate and peel into the icon",
                 "ref": [9.3, 11.5], "ours": [10.3, 12.2]}, ...]}

Each section runs for the length of OUR part; the reference part is time-stretched to match (its speed is shown),
so both halves start and land together. Audio comes from our film. Section boundaries for a reference can be
proposed with:  analyze_reference.py <ref> --seconds 0 --sections 20
"""
import argparse
import json
import os
import subprocess
import tempfile

W, H = 1920, 1080
PW, PH = 880, 496                       # each panel, 16:9, with a 40 px gutter between them
PY = 196
PX = (60, W - 60 - PW)
SANS = "/System/Library/Fonts/SFNS.ttf"
MONO = "/System/Library/Fonts/SFNSMono.ttf"
BG, INK, SOFT, ACC = "0x111113", "0xF2F2F4", "0x8E8E96", "0xEF7B2E"


def run(cmd):
    subprocess.run(cmd, check=True)


def text(tmp, s, name):
    p = os.path.join(tmp, name); open(p, "w").write(s); return p


def section_clip(i, n, sec, a, tmp):
    r0, r1 = sec["ref"]; o0, o1 = sec["ours"]
    od, rd = o1 - o0, r1 - r0
    k = od / rd                                             # stretch factor applied to the reference part
    out = os.path.join(tmp, f"sec{i:02d}.mp4")
    T = lambda s, nm: text(tmp, s, f"{nm}{i}.txt")
    lab_r = T(a["ref_label"].upper(), "lr"); lab_o = T(a["ours_label"].upper(), "lo")
    head = T(f"{i + 1:02d} / {n:02d}", "hd"); name = T(sec["name"], "nm"); tech = T(sec.get("technique", ""), "tc")
    spd = T(f"reference x{1 / k:.2f}" if abs(k - 1) > .03 else "reference 1:1", "sp")
    tline = T(f"ref {r0:05.2f}-{r1:05.2f}s    ours {o0:05.2f}-{o1:05.2f}s", "tl")
    # progress strip: one block per section, the current one highlighted, a playhead sweeping across it
    total = a["_total"]; x0, bw, by = 60, W - 120, 1000
    blocks = []
    acc = 0.0
    for j, s in enumerate(a["sections"]):
        d = s["ours"][1] - s["ours"][0]
        bx = x0 + bw * acc / total; bwj = max(2, bw * d / total - 4)
        col = ACC if j == i else ("0x4A4A52" if j < i else "0x2A2A30")
        blocks.append(f"drawbox=x={bx:.1f}:y={by}:w={bwj:.1f}:h=8:color={col}@1:t=fill")
        if j == i:
            cur_x, cur_w = bx, bwj
        acc += d
    dt = lambda font, src, size, color, pos: f"drawtext=fontfile={font}:textfile={src}:fontsize={size}:fontcolor={color}:{pos}"
    fc = (
        f"color=c={BG}:s={W}x{H}:r=30:d={od:.3f}[bg];"
        f"[0:v]trim={r0}:{r1},setpts=(PTS-STARTPTS)*{k:.5f},fps=30,scale={PW}:{PH}:force_original_aspect_ratio=decrease,pad={PW}:{PH}:-1:-1:color={BG}[r];"
        f"[1:v]trim={o0}:{o1},setpts=PTS-STARTPTS,fps=30,scale={PW}:{PH}[o];"
        f"[bg][r]overlay={PX[0]}:{PY}:shortest=1[b1];[b1][o]overlay={PX[1]}:{PY}:shortest=1,"
        + ",".join([
            dt(MONO, head, 22, ACC, "x=60:y=58"),
            dt(SANS, name, 46, INK, "x=60:y=92"),
            dt(MONO, lab_r, 18, SOFT, f"x={PX[0]}:y={PY - 34}"),
            dt(MONO, lab_o, 18, SOFT, f"x={PX[1]}:y={PY - 34}"),
            dt(MONO, spd, 16, SOFT, f"x={PX[0] + PW}-tw:y={PY - 32}"),
            dt(SANS, tech, 30, INK, f"x=60:y={PY + PH + 60}"),
            dt(MONO, tline, 18, SOFT, f"x=60:y={PY + PH + 112}"),
        ] + blocks + [f"drawbox=x={PX[0] - 2}:y={PY - 2}:w={PW + 4}:h={PH + 4}:color=0x2E2E34@1:t=2",
                      f"drawbox=x={PX[1] - 2}:y={PY - 2}:w={PW + 4}:h={PH + 4}:color={ACC}@1:t=2"])
        + "[v0];"
        f"color=c=white:s=4x16:r=30:d={od:.3f}[ph];[v0][ph]overlay=x='{cur_x:.1f}+{cur_w:.1f}*t/{od:.3f}':y={by - 4}[v];"
        f"[1:a]atrim={o0}:{o1},asetpts=PTS-STARTPTS[aud]"
    )
    run(["ffmpeg", "-v", "error", "-y", "-i", a["ref"], "-i", a["ours"], "-filter_complex", fc,
         "-map", "[v]", "-map", "[aud]", "-t", f"{od:.3f}", "-c:v", "libx264", "-preset", "medium", "-crf", "17",
         "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", out])
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ref", required=True); ap.add_argument("--ours", required=True)
    ap.add_argument("--map", required=True); ap.add_argument("--out", required=True)
    a = ap.parse_args()
    m = json.load(open(a.map))
    cfg = {"ref": a.ref, "ours": a.ours, "ref_label": m.get("ref_label", "Reference"), "ours_label": m.get("ours_label", "Ours"),
           "sections": m["sections"]}
    cfg["_total"] = sum(s["ours"][1] - s["ours"][0] for s in m["sections"])
    with tempfile.TemporaryDirectory() as tmp:
        clips = [section_clip(i, len(m["sections"]), s, cfg, tmp) for i, s in enumerate(m["sections"])]
        lst = os.path.join(tmp, "list.txt"); open(lst, "w").write("".join(f"file '{c}'\n" for c in clips))
        run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", a.out])
    print("wrote", a.out, f"({cfg['_total']:.1f}s, {len(clips)} sections)")


if __name__ == "__main__":
    main()
