"""Write part_N.html slices of index.html (shifted clip/video times) so long high-fps renders fit on disk."""
import re, sys
src = open("index.html").read()
parts = [(0, 23.4), (23.4, 23.4), (46.8, 23.2)]
for k, (off, dur) in enumerate(parts):
    s = src.replace("const OFF = 0, DUR = 70;", f"const OFF = {off}, DUR = {dur};")
    s = s.replace('data-duration="70" data-width', f'data-duration="{dur}" data-width')
    def fix(m):
        tag = m.group(0)
        st = float(re.search(r'data-start="([\d.]+)"', tag).group(1)); du = float(re.search(r'data-duration="([\d.]+)"', tag).group(1))
        ms = float(re.search(r'data-media-start="([\d.]+)"', tag).group(1))
        a, b = st - off, st + du - off
        if b <= 0 or a >= dur: return ""
        if a < 0: ms -= a; a = 0
        b = min(b, dur)
        tag = re.sub(r'data-start="[\d.]+"', f'data-start="{a:.4f}"', tag); tag = re.sub(r'data-duration="[\d.]+"', f'data-duration="{b - a:.4f}"', tag)
        return re.sub(r'data-media-start="[\d.]+"', f'data-media-start="{ms:.4f}"', tag)
    s = re.sub(r'<div id="vl-[^"]+" class="vlayer">.*?</video></div>', fix, s)
    open(f"part_{k}.html", "w").write(s)
    print(k, off, dur, len(re.findall("<video", s)), "videos")
