"""AE scene for `lower-third-nestgen` (v2) — the same frame-accurate motion as lower-third.js.

Every animated property is sampled once per source frame from the same curves the HTML template uses
(measured off "Lower Third Template.mp4"), and written as linear keyframes, so AE lands on the HTML's
values at every frame. The outro is the intro mirrored in time, exactly like the source.

Editable in AE: name letters, title and company are live text layers (Briallen Disco / Geist), colours are
solids, timing is keyframes. The bar surface (sampled colour field + film grain) is a PNG so it matches the
source; tint it with Hue/Saturation if you need another colour. Glows use AE's Glow effect (approximation
of the HTML's fitted multi-gaussian glow) — see README for the exact values.
"""
import os
import random
import re

from .scene import Scene, metrics, text_width

F = 1 / 29.97
HERE = os.path.dirname(os.path.abspath(__file__))
JS = os.path.join(HERE, "..", "..", "templates", "lower-third-nestgen", "lower-third.js")

X, Y = 63, 810                     # bar top-left in the 1080p frame (source)
BAR_H, NAME_X, PAD_R = 83, 17, 117
NAME_SIZE, NAME_TRACK, NAME_BASE = 68, -0.7, 63.5
SUB_TOP, SUB_H, SUB_SIZE, SUB_TRACK, SUB_BASE, SUB_PAD = 88, 51, 26, 0.35, 121, (19, 24)
INTRO = 70                         # intro frames; the outro mirrors them
THEMES = {
    "purple": {"edge": "#9a2ad2", "trail": "#7d00c8", "wash": "#d8a6fb", "glowA": [0.86, 0.66, 1], "glowB": [0.79, 0.54, 1]},
    "blue":   {"edge": "#2a78ff", "trail": "#145af0", "wash": "#aacdff", "glowA": [0.62, 0.78, 1], "glowB": [0.5, 0.68, 1]},
}


def _js_arrays():
    src = open(JS).read()
    fix = lambda s: eval(re.sub(r"(?<![\d.])\.(\d)", r"0.\1", s))           # ".0267" -> "0.0267"
    grab = lambda name: fix(re.search(name + r"\s*=\s*(\[.*?\]);", src, re.S).group(1))
    return grab("FIELD"), grab("HEAD"), grab("TAIL")


# ---- the HTML template's eases ----
def _clamp(p):
    return 0.0 if p < 0 else 1.0 if p > 1 else p


EASES = {
    "none": lambda p: p,
    "power1.in": lambda p: p * p,
    "power1.out": lambda p: 1 - (1 - p) ** 2,
    "power2.out": lambda p: 1 - (1 - p) ** 3,
    "inOut3": lambda p: 8 * p ** 4 if p < .5 else 1 - (-2 * p + 2) ** 4 / 2,
}


def _table(pts):
    f0, d = pts[0][0], pts[-1][0] - pts[0][0]

    def ease(p):
        f = f0 + p * d
        for i in range(1, len(pts)):
            if f <= pts[i][0]:
                (a, pa), (b, pb) = pts[i - 1], pts[i]
                return pa + (pb - pa) * (f - a) / (b - a)
        return 1.0
    return f0, d, ease


def _m(x, y, w, h):
    """A mask rect; an empty one becomes a tiny rect off the layer (AE dislikes zero-area paths)."""
    return [round(x, 3), round(y, 3), round(w, 3), round(h, 3)] if w > 0.01 and h > 0.01 else [-8, -8, 0.5, 0.5]


def _layer_masks(scene):
    """Every mask here is in layer space (what AE uses); tag them so preview.py maps them the same way."""
    for L in scene.d["layers"]:
        if L.get("mask"):
            L["mask"]["space"] = "layer"


def _seq(u, init, tweens):
    """GSAP semantics for one property: the latest tween that has started decides the value."""
    v = init
    for u0, d, a, b, ease in sorted(tweens, key=lambda t: t[0]):
        if u >= u0:
            fn = EASES[ease] if isinstance(ease, str) else ease
            v = a + (b - a) * fn(_clamp((u - u0) / d if d else 1))
    return v


def _paint_bar(path, w, h, field, theme):
    """Same painter as the HTML: bilinear colour field + mono grain (seeded)."""
    from PIL import Image
    rows, cols = len(field), len(field[0])
    rnd = random.Random(11)
    img = Image.new("RGB", (w, h))
    px = img.load()
    for y in range(h):
        fy = min(rows - 1, max(0, (y - 1) / (h - 3) * (rows - 1))); y0 = int(fy); y1 = min(rows - 1, y0 + 1); ty = fy - y0
        for x in range(w):
            fx = min(cols - 1, max(0, (x - 2) / (w - 5) * (cols - 1))); x0 = int(fx); x1 = min(cols - 1, x0 + 1); tx = fx - x0
            c = [(field[y0][x0][k] * (1 - tx) + field[y0][x1][k] * tx) * (1 - ty) + (field[y1][x0][k] * (1 - tx) + field[y1][x1][k] * tx) * ty
                 for k in range(3)]
            if theme == "blue":
                c = [0.18 * c[0], 0.55 * c[0] + c[1], min(255, 1.3 * c[2])]
            n = (rnd.random() + rnd.random() + rnd.random() - 1.5) * 7.8
            px[x, y] = tuple(int(max(0, min(255, v + n))) for v in c)
    img.save(path)


def write_assets(p, assets_dir):
    """Bar surface PNG for this name length / theme. Returns {asset_id: filename}."""
    field, _, _ = _js_arrays()
    theme = p.get("theme", "purple")
    bw = _bar_w(str(p.get("name", "Nitin Gupta")).upper())
    os.makedirs(assets_dir, exist_ok=True)
    fn = f"bar_{theme}_{bw}.png"
    _paint_bar(os.path.join(assets_dir, fn), bw, BAR_H, field, theme)
    return {"bar": fn}


def _letters(name):
    """Letter lefts/widths exactly as the HTML lays them out (one inline-block per letter, no cross-kerning)."""
    adv = metrics()["Briallen Disco"]["adv"]
    out, x = [], 0.0
    for c in name:
        if c == " ":
            x += 0.25 * NAME_SIZE
            out.append(None)
            continue
        w = adv.get(c, 0.6) * NAME_SIZE + NAME_TRACK
        out.append((c, x, w))
        x += w
    return out, x


def _bar_w(name):
    _, w = _letters(name)
    return round(NAME_X + w + PAD_R)


def build(p):
    name = str(p.get("name", "Nitin Gupta")).upper()
    title = str(p.get("title", "Founder & CEO")).upper()
    company = str(p.get("company", "FlytBase") or "").upper()
    theme = p.get("theme", "purple") if p.get("theme") in THEMES else "purple"
    th = THEMES[theme]
    T = float(p.get("start", 0.2 * F))
    hold = float(p.get("hold", 49.6 * F))          # source: 191 frames in all
    outro = str(p.get("outro", "true")).lower() != "false"
    E = T + (2 * INTRO) * F + hold                 # outro finishes at E (mirror of T)
    _, HEAD, TAIL = _js_arrays()

    letters, _ = _letters(name)
    barW = _bar_w(name)
    role = title + (", " if company else "")
    roleW = text_width(role, SUB_SIZE, "Geist") + SUB_TRACK * len(role)
    coW = text_width(company, SUB_SIZE, "Geist") + SUB_TRACK * len(company) if company else 0
    subW = round(SUB_PAD[0] + roleW + coW + SUB_PAD[1])
    L, R, TOP, BOT, CY = -0.5, barW + 38, 0, BAR_H, BAR_H / 2
    V, H = CY - TOP, R + 0.5
    B0, BD = 22.3, 25

    s = Scene(f"Lower Third v2 — {name}", 1920, 1080, 29.97, (E if outro else T + INTRO * F + hold) + 0.5, "#000000")
    s.note("Keys are baked once per source frame (linear) so AE matches the HTML frame for frame; "
           "retime by stretching the layers, not by editing single keys.")
    s.note("Name letters, title and company are live text (Briallen Disco / Geist) — install both fonts from _assets/fonts.")
    s.note("Bar surface is a PNG sampled from the source (colour field + grain); tint it with Hue/Saturation if needed.")
    s.note("Glows use AE Glow; the HTML uses a fitted multi-gaussian glow, so glow falloff is close, not identical.")

    # ---- sampling: intro frames 0..INTRO, then the same frames mirrored for the outro ----
    def keys(fn, intro_only=False, dedupe=True):
        out = [[T + u * F, fn(u)] for u in range(INTRO + 1)]
        if outro and not intro_only:
            out += [[E - u * F, fn(u)] for u in range(INTRO, -1, -1)]
        if not dedupe:
            return out
        slim = [out[0]]
        for i in range(1, len(out) - 1):               # drop keys inside flat runs
            if not (out[i][1] == out[i - 1][1] == out[i + 1][1]):
                slim.append(out[i])
        slim.append(out[-1])
        return slim

    head_f0, head_d, head_e = _table(HEAD)
    tail_f0, tail_d, tail_e = _table(TAIL)
    beamx = lambda u: _seq(u, R, [(B0, BD, R, 0, "inOut3")])
    sx_h = lambda u: _seq(u, 0, [(head_f0, head_d, 0, 1, head_e)])
    tail_h = lambda u: _seq(u, 0, [(tail_f0, tail_d, 0, H + 3, tail_e)])
    grow_v = lambda u: _seq(u, 0, [(0, 5.6, 0, 1, "power1.in")])
    tail_v = lambda u: _seq(u, 0, [(6.1, 4.6, 0, V + 3, "power1.in")])
    close_v = lambda u: _seq(u, 0, [(14.3, 4.5, 0, 1, "power1.out")])
    right_op = lambda u: _seq(u, 1, [(B0 - 0.5, 0.01, 1, 0, "none")])
    edge_e = lambda u: EASES["inOut3"](_clamp((u - 42.6) / 27))
    drift = lambda u: _seq(u, -70, [(36.3, 21.8, -70, 0, "power2.out")])

    # 1. haze + one-frame flash (soft blobs)
    halo = s.solid("haze", "#ffffff", 260, 260, 0, 0).effect("blur", amount=90)
    halo.key("position", keys(lambda u: [X + beamx(u) - 130, Y + CY - 130]), ease="none")
    halo.key("opacity", keys(lambda u: 12 * _seq(u, 0, [(35.3, 1, 0, 1, "none"), (42.3, 4, 1, 0, "power1.in")])), ease="none")
    fl = s.solid("flash", "#ffffff", 320, 320, X + beamx(34.8) - 160, Y + CY - 160).effect("blur", amount=120)
    fl.key("opacity", [[T + 34.2 * F, 0], [T + 34.3 * F, 22], [T + 35.2 * F, 22], [T + 35.3 * F, 0]], ease="hold")

    # 2. name bar surface, revealed by the beam window
    bar = s.footage("name bar", "bar", X, Y, barW, BAR_H)
    bar.mask(keys(lambda u: _m(*[min(barW, max(0, beamx(u))), 0, max(0, barW - max(0, beamx(u))), BAR_H])), ease="none")
    # soft white wash riding just behind the beam (4 steps of the HTML gradient)
    wash_op = lambda u: _seq(u, 0, [(B0, 2, 0, 1, "none"), (38.8, 4, 1, 0, "power1.in")])
    for i, a in enumerate((0.48, 0.34, 0.2, 0.07)):
        w = s.solid(f"beam wash {i + 1}", "#ebd7ff", 11, BAR_H, X, Y)
        w.key("position", keys(lambda u, i=i: [X + beamx(u) + 11 * i, Y]), ease="none")
        w.key("opacity", keys(lambda u, a=a: 100 * a * wash_op(u)), ease="none")
        w.mask(keys(lambda u, i=i: _m(*[0, 0, max(0, min(11, barW - beamx(u) - 11 * i)), BAR_H])), ease="none")

    # 3. name: one live text layer per letter (drift + right-to-left stagger + window clip)
    n = len(letters)
    for idx, lt in enumerate(letters):
        if lt is None:
            continue
        ch, lx, lw = lt
        j = n - 1 - idx
        t0 = 30 + 1.52 * j
        pr = lambda u, t0=t0: EASES["power2.out"](_clamp((u - t0) / 6))
        sxl = lambda u, pr=pr: 1.6 + (1 - 1.6) * pr(u)
        posx = lambda u, lx=lx, lw=lw, pr=pr, sxl=sxl: X + NAME_X + drift(u) + lx + (-40 + 40 * pr(u)) + (1 - sxl(u)) * lw
        t = s.text(f"name {idx + 1} ({ch})", ch, X + NAME_X + lx, Y + NAME_BASE, size=NAME_SIZE, color="#ffffff",
                   font="Briallen Disco", tracking=round(NAME_TRACK / NAME_SIZE * 1000, 1))
        t.d["text"]["ps"] = "BriallenDisco-Regular"
        t.key("position", keys(lambda u, posx=posx: [posx(u), Y + NAME_BASE]), ease="none")
        t.key("scale", keys(lambda u, sxl=sxl: [100 * sxl(u), 100]), ease="none")
        t.key("opacity", keys(lambda u, pr=pr: 100 * pr(u)), ease="none")
        # window [X+beam, X+barW] in the letter's own (scaled) layer space
        t.mask(keys(lambda u, posx=posx, sxl=sxl: _m(*[
            (X + max(0, beamx(u)) - posx(u)) / sxl(u), -NAME_BASE,
            max(0, (barW - max(0, beamx(u))) / sxl(u)), BAR_H])), ease="none")

    # 4. title strip: white bar + lilac wash + live text, revealed left->right; edge rides the front
    strip = s.solid("title strip", "#fdfdfd", subW, SUB_H, X, Y + SUB_TOP)
    strip.mask(keys(lambda u: _m(*[0, 0, subW * edge_e(u), SUB_H])), ease="none")
    txt_x = lambda u: _seq(u, 70, [(54.1, 13, 70, 0, "power2.out")])
    for nm, val, off, col in (("title", role.rstrip(), 0, "#434343"), ("company", company, roleW, "#000000")):
        if not val:
            continue
        tl = s.text(nm, val, X + SUB_PAD[0] + off, Y + SUB_BASE, size=SUB_SIZE, color=col, font="Geist",
                    tracking=round(SUB_TRACK / SUB_SIZE * 1000, 1))
        tl.d["text"]["ps"] = "Geist-Regular"
        px = lambda u, off=off: X + SUB_PAD[0] + off + txt_x(u)
        tl.key("position", keys(lambda u, px=px: [px(u), Y + SUB_BASE]), ease="none")
        tl.mask(keys(lambda u, px=px: _m(*[X - px(u), -SUB_BASE + SUB_TOP, max(0, subW * edge_e(u)), SUB_H])), ease="none")
    wash_s = [(45.8, .2), (50.8, .3), (52.8, .7), (55.8, 1), (57.8, .5), (59.8, .3), (61.8, .23), (63.8, .2), (65.8, .13), (67.8, 0)]
    wash_sx = lambda u: _seq(u, .2, [(a[0], b[0] - a[0], a[1], b[1], "none") for a, b in zip(wash_s, wash_s[1:])])
    wash_op2 = lambda u: _seq(u, 0, [(45.8, 1, 0, 1, "none")])
    for i, a in enumerate((0.33, 0.66, 1.0)):
        w = s.solid(f"strip wash {i + 1}", th["wash"], 10, SUB_H, X, Y + SUB_TOP)
        right = lambda u: subW * edge_e(u)
        left_i = lambda u, i=i: right(u) - 30 * wash_sx(u) + 10 * wash_sx(u) * i
        w.key("position", keys(lambda u, left_i=left_i: [X + left_i(u), Y + SUB_TOP]), ease="none")
        w.key("scale", keys(lambda u: [100 * max(0.001, wash_sx(u)), 100]), ease="none")
        w.key("opacity", keys(lambda u, a=a: 100 * a * wash_op2(u)), ease="none")
        w.mask(keys(lambda u, left_i=left_i: _m(*[max(0, -left_i(u)) / max(0.001, wash_sx(u)), 0, 10, SUB_H])), ease="none")
    edge = s.solid("edge", th["edge"], 4, SUB_H, X - 2, Y + SUB_TOP).effect("glow", radius=18, threshold=20, intensity=1.2)
    esx = lambda u: _seq(u, 1, [(60.8, 6, 1, 0.5, "power1.out")])
    edge.key("position", keys(lambda u: [X + 2 + subW * edge_e(u) - 4 * esx(u), Y + SUB_TOP]), ease="none")
    edge.key("scale", keys(lambda u: [100 * esx(u), 100]), ease="none")
    edge.key("opacity", keys(lambda u: 100 * _seq(u, 0, [(44.6, 1.2, 0, 1, "none")])), ease="none")

    # 5. purple smear behind the tails (length follows tail speed, like AE motion blur)
    tr_s = [(10.4, .05), (11.8, .5), (13.8, 1), (15.8, 1.35), (17.8, .9), (19.8, .55), (21.8, .3), (23.8, .1)]
    tr_sx = lambda u: _seq(u, .05, [(a[0], b[0] - a[0], a[1], b[1], "none") for a, b in zip(tr_s, tr_s[1:])])
    tr_op = lambda u: _seq(u, 0, [(9.4, 1.4, 0, 1, "none"), (19.8, 4, 1, 0, "power1.in")])
    for key, yy in (("top", TOP), ("bottom", BOT)):
        g = s.solid(f"trail {key}", th["trail"], 40, 14, 0, 0).effect("blur", amount=9)
        g.key("position", keys(lambda u, yy=yy: [X + L - 75 + tail_h(u) + 25 + (1 - tr_sx(u)) * 40, Y + yy - 7]), ease="none")
        g.key("scale", keys(lambda u: [100 * max(0.001, tr_sx(u)), 100]), ease="none")
        g.key("opacity", keys(lambda u: 100 * tr_op(u)), ease="none")

    # 6. light trace: six segments, each a solid showing only [tail, head]
    glow = dict(radius=40, threshold=10, intensity=1.6, colorA=th["glowA"], colorB=th["glowB"])
    top = s.solid("light top", "#ffffff", H, 2, X + L, Y + TOP - 1).effect("glow", **glow)
    bot = s.solid("light bottom", "#ffffff", H, 2, X + L, Y + BOT - 1).effect("glow", **glow)
    for lay in (top, bot):
        lay.mask(keys(lambda u: _m(*[min(H * sx_h(u), tail_h(u)), 0, max(0, H * sx_h(u) - tail_h(u)), 2])), ease="none")
    lv_t = s.solid("light left top", "#ffffff", 2.5, V, X + L - 1.25, Y + TOP).effect("glow", **glow)
    lv_t.mask(keys(lambda u: _m(*[0, V - V * grow_v(u), 2.5, max(0, V * grow_v(u) - tail_v(u))])), ease="none")
    lv_b = s.solid("light left bottom", "#ffffff", 2.5, V, X + L - 1.25, Y + CY).effect("glow", **glow)
    lv_b.mask(keys(lambda u: _m(*[0, min(V, tail_v(u)), 2.5, max(0, V * grow_v(u) - tail_v(u))])), ease="none")
    rv_t = s.solid("light right top", "#ffffff", 2.5, V, X + R - 1.25, Y + TOP).effect("glow", **glow)
    rv_t.mask(keys(lambda u: _m(*[0, 0, 2.5, V * close_v(u)])), ease="none")
    rv_b = s.solid("light right bottom", "#ffffff", 2.5, V, X + R - 1.25, Y + CY).effect("glow", **glow)
    rv_b.mask(keys(lambda u: _m(*[0, V - V * close_v(u), 2.5, V * close_v(u)])), ease="none")
    for lay in (rv_t, rv_b):
        lay.key("opacity", keys(lambda u: 100 * right_op(u)), ease="none")

    # 7. the beam: lavender glow until f36, then neutral (two layers crossfading, as in the HTML)
    bop = lambda u: _seq(u, 0, [(B0 - 0.5, 0.01, 0, 1, "none"), (35.8, 1.5, 1, 0, "none")])
    nop = lambda u: _seq(u, 0, [(35.8, 1.5, 0, 1, "none"), (42.3, 2, 1, 0, "power1.in")])
    for nm, op, g in (("beam", bop, glow), ("beam neutral", nop, dict(radius=40, threshold=10, intensity=1.6))):
        b = s.solid(nm, "#ffffff", 2.5, BAR_H, X + R - 1.25, Y).effect("glow", **g)
        b.key("position", keys(lambda u: [X + beamx(u) - 1.25, Y]), ease="none")
        b.key("opacity", keys(lambda u, op=op: 100 * op(u)), ease="none")
    _layer_masks(s)
    return s
