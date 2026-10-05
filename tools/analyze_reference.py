#!/usr/bin/env python3
"""Break a reference animation down frame by frame, so it can be rebuilt as a template.

  analyze_reference.py <file.mp4 | url> [--seconds 20 | 0 = whole film] [--name my-ref] [--sections 8]

Produces references/<name>/: frames, cut list, per-scene contact sheets (every 2nd frame),
palette, motion profile and an analysis.md stub to fill in while reading the sheets.
--sections N also groups the cuts into N story sections (merging at the strongest scene changes,
each at least --min-section seconds long) and writes one contact sheet per section.
A URL is fetched with yt-dlp if it is installed.
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def sh(cmd, **kw):
    return subprocess.run(cmd, check=True, capture_output=True, text=True, **kw).stdout


def ytdlp():
    """Newest yt-dlp via uvx (YouTube breaks old builds); fall back to an installed one."""
    if shutilwhich("uvx"):
        return ["uvx", "--quiet", "yt-dlp@latest", "--js-runtimes", "node"]
    if shutilwhich("yt-dlp"):
        return ["yt-dlp"]
    sys.exit("ERROR: can't download links: neither uv nor yt-dlp is installed (brew install uv)")


def link_title(src):
    try:
        t = subprocess.run(ytdlp() + ["--print", "title", "--skip-download", src], capture_output=True, text=True, timeout=120).stdout.strip()
        return t.splitlines()[-1] if t else None
    except Exception:
        return None


def fetch(src, outdir):
    if not src.startswith(("http://", "https://")):
        if not os.path.exists(src):
            sys.exit(f"ERROR: file not found: {src}")
        link = os.path.join(outdir, "source" + os.path.splitext(src)[1].lower())
        if not os.path.exists(link):
            os.symlink(os.path.abspath(src), link)              # keep the original where it is; serve it from here
        return src
    dst = os.path.join(outdir, "source.mp4")
    print("STAGE download", flush=True)
    # YouTube often refuses direct (DASH) downloads now; its HLS streams still work, so try those first
    for fmt in ("bv*[protocol*=m3u8][height<=1080]+ba/b[protocol*=m3u8][height<=1080]", "bv*[height<=1080]+ba/b[height<=1080]", "b"):
        r = subprocess.run(ytdlp() + ["-f", fmt, "--merge-output-format", "mp4", "-o", dst, src], capture_output=True, text=True)
        if r.returncode == 0 and os.path.exists(dst):
            break
    if r.returncode or not os.path.exists(dst):
        tail = (r.stderr or r.stdout).strip().splitlines()[-1:] or ["unknown error"]
        sys.exit(f"ERROR: couldn't download that link ({tail[0][:200]})")
    return dst


def shutilwhich(x):
    from shutil import which
    return which(x)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("--seconds", type=float, default=0, help="0 = the whole film")
    ap.add_argument("--name")
    ap.add_argument("--sections", type=int, default=12, help="group the cuts into N story sections (0 = off)")
    ap.add_argument("--min-section", type=float, default=2.0, help="shortest section, seconds")
    a = ap.parse_args()

    is_link = a.src.startswith(("http://", "https://"))
    title = (link_title(a.src) if is_link else None) or os.path.splitext(os.path.basename(a.src.rstrip("/")))[0]
    name = a.name or (re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")[:48] or "reference")
    out = os.path.join(ROOT, "references", name)
    fresh = not os.path.isdir(out)
    os.makedirs(os.path.join(out, "frames"), exist_ok=True)
    try:
        src = fetch(a.src, out)
    except SystemExit:
        if fresh:
            shutil.rmtree(out, ignore_errors=True)             # never leave an empty card behind
        raise

    probe = json.loads(sh(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                           "stream=width,height,r_frame_rate:format=duration", "-of", "json", src]))
    w, h = probe["streams"][0]["width"], probe["streams"][0]["height"]
    num, den = probe["streams"][0]["r_frame_rate"].split("/")
    fps = float(num) / float(den)
    if a.seconds <= 0:
        a.seconds = float(probe["format"]["duration"])
    print(f"{w}x{h} @ {fps:.3f} fps, analysing {a.seconds:.1f}s ({round(a.seconds * fps)} frames)")

    print("STAGE frames", flush=True)
    sh(["ffmpeg", "-v", "error", "-y", "-t", str(a.seconds), "-i", src, "-vf", "scale='min(960,iw)':-2", "-q:v", "3", f"{out}/frames/%03d.jpg"])
    sh(["ffmpeg", "-v", "error", "-y", "-ss", str(a.seconds * .3), "-i", src, "-frames:v", "1", "-vf", "scale=640:-2", "-q:v", "3", f"{out}/poster.jpg"])
    sh(["ffmpeg", "-v", "error", "-y", "-t", str(a.seconds), "-i", src, "-vf",
        "fps=2,scale=320:-1,drawtext=text='%{pts\\:hms}':x=4:y=4:fontsize=14:fontcolor=white:box=1:boxcolor=black@0.6,tile=8x5",
        "-frames:v", "1", f"{out}/overview.png"])

    import numpy as np
    from PIL import Image, ImageDraw
    files = sorted(os.listdir(f"{out}/frames"))
    prev, diffs = None, []
    for i, fn in enumerate(files):
        g = np.asarray(Image.open(f"{out}/frames/{fn}").convert("L").resize((320, 180))).astype(float)
        if prev is not None:
            diffs.append((i + 1, float(np.abs(g - prev).mean())))
        prev = g
    print("STAGE cuts", flush=True)
    cuts = [i for i, d in diffs if d > 25]
    scenes = [(s, e) for s, e in zip([1] + cuts, cuts + [len(files) + 1])]
    print("cuts at frames:", cuts)
    print("scenes:", [(s, e, f"{(s-1)/fps:.2f}-{(e-1)/fps:.2f}s") for s, e in scenes])

    for n, (s, e) in enumerate(scenes):            # every 2nd frame, 36 per sheet
        fr = list(range(s, e, 2))
        for part in range(0, len(fr), 36):
            chunk, cols, tw = fr[part:part + 36], 6, 426
            th = int(tw * h / w); rows = (len(chunk) + cols - 1) // cols
            sheet = Image.new("RGB", (cols * tw, rows * (th + 18)), "black"); d = ImageDraw.Draw(sheet)
            for k, fi in enumerate(chunk):
                im = Image.open(f"{out}/frames/{fi:03d}.jpg").resize((tw, th))
                x, y = (k % cols) * tw, (k // cols) * (th + 18)
                sheet.paste(im, (x, y + 18)); d.text((x + 4, y + 3), f"f{fi} {(fi-1)/fps:.2f}s", fill="white")
            sheet.save(f"{out}/scene{n+1}_{part//36}.jpg", quality=88)

    sections = []
    if a.sections:
        print("STAGE sections", flush=True)
        # story sections: many of a film's scene changes are morphs / zoom-throughs / blur dissolves, not hard cuts,
        # so find boundaries by novelty (half a second before vs after each frame, colour + edge features),
        # keep the strongest that leave every section >= --min-section, then snap to a hard cut if one is close
        def feat(fi):
            im = Image.open(f"{out}/frames/{fi:03d}.jpg").convert("RGB")
            c = np.asarray(im.resize((32, 18))).astype(float).ravel()
            g = np.asarray(im.convert("L").resize((96, 54))).astype(float)
            e = np.hypot(np.diff(g, axis=0)[:, :-1], np.diff(g, axis=1)[:-1, :])
            e = np.array(Image.fromarray(e.astype(np.float32)).resize((48, 27))).ravel()
            c -= c.mean(); c /= np.linalg.norm(c) + 1e-9; e -= e.mean(); e /= np.linalg.norm(e) + 1e-9
            return np.concatenate([c, e]) / np.sqrt(2)
        n_frames = len(files)
        Fm = np.array([feat(i) for i in range(1, n_frames + 1)])
        K = max(4, round(fps * .27)); nov = np.zeros(n_frames)
        for i in range(K, n_frames - K):
            A, B = Fm[i - K:i], Fm[i:i + K]
            nov[i] = ((A @ A.T).mean() + (B @ B.T).mean()) / 2 - (A @ B.T).mean()
        peaks = [i for i in range(1, n_frames - 1) if nov[i] == nov[max(0, i - K):i + K + 1].max() and nov[i] > .05]
        hard = [i - 1 for i, d in diffs if d > 5]                     # 0-based frame index of big single-frame changes
        keep = []
        for pk in sorted(peaks, key=lambda q: -nov[q]):
            trial = sorted(keep + [pk]); bb = [0] + trial + [n_frames]
            if all((y - x) / fps >= a.min_section for x, y in zip(bb, bb[1:])):
                keep = trial
            if len(keep) >= a.sections - 1:
                break
        snapped = []
        for pk in keep:
            near = [h for h in hard if abs(h - pk) <= .4 * fps]
            snapped.append(min(near, key=lambda h: abs(h - pk)) if near else pk)
        bounds = [0] + sorted(set(snapped)) + [n_frames]
        for n, (s0, e0) in enumerate(zip(bounds, bounds[1:])):
            sections.append({"n": n + 1, "frames": [s0 + 1, e0], "start": round(s0 / fps, 3), "end": round(e0 / fps, 3),
                             "boundary_strength": round(float(nov[s0]), 3) if s0 else None})
            pick = [min(n_frames, s0 + 1 + round((e0 - s0 - 1) * k / 11)) for k in range(12)]
            tw = 400; th = int(tw * h / w); sheet = Image.new("RGB", (6 * tw, 2 * (th + 18)), "black"); d = ImageDraw.Draw(sheet)
            for k, fi in enumerate(pick):
                im = Image.open(f"{out}/frames/{fi:03d}.jpg").resize((tw, th))
                x, y = (k % 6) * tw, (k // 6) * (th + 18)
                sheet.paste(im, (x, y + 18)); d.text((x + 4, y + 3), f"f{fi} {(fi-1)/fps:.2f}s", fill="white")
            sheet.save(f"{out}/section{n+1:02d}.jpg", quality=86)
        print("sections:", [(x["n"], x["start"], x["end"]) for x in sections])

    pal = {}
    mid = np.asarray(Image.open(f"{out}/frames/{files[len(files)//2]}").convert("RGB")).astype(int)
    cols = mid.reshape(-1, 3)
    pal["mid_frame_common"] = ["#%02x%02x%02x" % tuple(c) for c in
                               np.unique((cols // 16 * 16), axis=0)[np.argsort(-np.unique((cols // 16 * 16), axis=0, return_counts=True)[1])][:8]]
    json.dump({"file": os.path.relpath(src, ROOT), "title": title, "link": a.src if is_link else None, "size": [w, h], "fps": fps, "seconds": a.seconds,
               "cuts": cuts, "scenes": scenes, "sections": sections, "palette": pal,
               "activity": [{"second": int(i / fps), "diff": round(d, 2)} for i, d in diffs]},
              open(f"{out}/analysis.json", "w"), indent=1)

    open(f"{out}/analysis.md", "w").write(f"""# Reference: {name}

`{os.path.relpath(src, ROOT)}` — {w}x{h} @ {fps:.3f} fps, first {a.seconds}s.

Cuts (frames): {cuts}

| # | frames | time | what happens | easing / notes |
|---|--------|------|--------------|----------------|
""" + "\n".join(f"| {n+1} | {s}-{e-1} | {(s-1)/fps:.2f}-{(e-1)/fps:.2f}s | | |" for n, (s, e) in enumerate(scenes)) + """

## Beats to nail
- entrance / exit of every element (frame numbers, not guesses)
- easing: is the middle frame past halfway? (in/out/inOut)
- what is *not* animated (holds are as important as moves)

## Rebuild checklist
- [ ] palette + fonts identified
- [ ] geometry measured at 1:1 (bar sizes, positions, text cap heights)
- [ ] per-beat timings in a table
- [ ] template params decided (what should be editable)
- [ ] side-by-side check against the source at matched frames
""")
    print("STAGE done", flush=True)
    print("wrote", os.path.relpath(out, ROOT), "-> read overview.png, scene sheets, then fill analysis.md")


if __name__ == "__main__":
    main()
