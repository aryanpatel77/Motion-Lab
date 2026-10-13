#!/usr/bin/env python3
"""Render every element of the film as its own layer (all original artwork): assets/layers/*.png
  paper.png, dark.png          textured backgrounds
  icon_<name>.png              32-px pixel icons with rim light, shade, outline and a sticker edge, x16
  head_heat.png / head_cold.png    the agent's head in profile, heat-mapped and cooled
  palm_heat.png                an open palm, heat-mapped
  star_cyan.png, star_red.png  four-point stars with bloom
  ink_<n>.png                  organic ink blots
"""
import os

import cv2
import numpy as np
from PIL import Image, ImageDraw

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "layers")
os.makedirs(OUT, exist_ok=True)
rs = np.random.default_rng(3)


def save(arr, name):
    Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).save(os.path.join(OUT, name), optimize=True)


def lowfreq(h, w, scale, seed):
    r = np.random.default_rng(seed).standard_normal((max(2, h // scale), max(2, w // scale))).astype(np.float32)
    return cv2.resize(cv2.GaussianBlur(r, (0, 0), 1.2), (w, h), interpolation=cv2.INTER_CUBIC)


# ---- backgrounds ------------------------------------------------------------------------------
def paper():
    H, W = 1080, 1440
    y, x = np.mgrid[0:H, 0:W].astype(np.float32)
    d = np.sqrt(((x - W * .52) / (W * .62)) ** 2 + ((y - H * .46) / (H * .66)) ** 2)
    base = 241 - 30 * np.clip(d, 0, 1.3) ** 1.8
    base += 2.2 * lowfreq(H, W, 90, 1) + 1.2 * lowfreq(H, W, 18, 2)
    fib = np.zeros((H, W), np.float32)
    for _ in range(900):                                         # faint paper fibres
        x0, y0 = rs.integers(0, W), rs.integers(0, H); a = rs.uniform(0, np.pi); L = rs.uniform(6, 26)
        cv2.line(fib, (int(x0), int(y0)), (int(x0 + L * np.cos(a)), int(y0 + L * np.sin(a))), float(rs.uniform(.5, 1)), 1, cv2.LINE_AA)
    base -= 2.5 * cv2.GaussianBlur(fib, (0, 0), .6)
    rgb = np.stack([base - 1.2, base - 1.6, base + .6], -1)          # a hair cool
    save(rgb, "paper.png")


def dark():
    H, W = 1080, 1440
    y, x = np.mgrid[0:H, 0:W].astype(np.float32)
    d = np.sqrt(((x - W / 2) / (W * .6)) ** 2 + ((y - H / 2) / (H * .62)) ** 2)
    base = 27 - 12 * np.clip(d, 0, 1.4) ** 1.6 + 1.6 * lowfreq(H, W, 70, 5)
    save(np.stack([base + .8, base - .4, base + 1.2], -1), "dark.png")


# ---- pixel icons (32x32) ------------------------------------------------------------------------
OUTL, EDGE = (27, 26, 31), (52, 47, 58)
C = dict(w=(244, 242, 236), g=(185, 182, 191), G=(120, 116, 130), d=(70, 66, 80), D=(38, 35, 44), c=(71, 227, 242), C=(196, 245, 250),
         b=(61, 107, 255), B=(157, 181, 255), n=(39, 71, 184), r=(217, 36, 28), R=(255, 122, 110), y=(242, 194, 48), Y=(255, 235, 160),
         o=(240, 122, 26), gr=(53, 178, 74), h=(155, 232, 138), p=(138, 92, 255), P=(205, 184, 255), br=(138, 86, 49), k=(27, 26, 31))


def icon_draw(name):
    im = Image.new("RGBA", (32, 32), (0, 0, 0, 0)); dr = ImageDraw.Draw(im)
    R = lambda box, col, rad=0: dr.rounded_rectangle(box, rad, fill=C[col] + (255,)) if rad else dr.rectangle(box, fill=C[col] + (255,))
    E = lambda box, col: dr.ellipse(box, fill=C[col] + (255,))
    Lw = lambda pts, col, w: dr.line(pts, fill=C[col] + (255,), width=w)
    P = lambda pts, col: dr.polygon(pts, fill=C[col] + (255,))
    if name == "robot":
        Lw([(16, 3), (16, 7)], "G", 2); E((14, 1, 18, 5), "r")
        R((2, 12, 5, 18), "G", 1); R((26, 12, 29, 18), "G", 1)
        R((5, 7, 26, 23), "w", 4); R((8, 11, 23, 19), "D", 2)
        R((10, 13, 13, 16), "c"); R((18, 13, 21, 16), "c"); R((11, 13, 11, 13), "C"); R((19, 13, 19, 13), "C")
        R((13, 18, 18, 18), "c"); R((13, 23, 18, 25), "G"); R((8, 25, 23, 30), "b", 2); R((15, 26, 16, 27), "y")
    elif name == "term":
        R((2, 5, 29, 27), "D", 2); R((2, 5, 29, 9), "g", 2); R((2, 8, 29, 9), "g")
        E((4, 6, 6, 8), "r"); E((8, 6, 10, 8), "y"); E((12, 6, 14, 8), "gr")
        Lw([(5, 12), (8, 14), (5, 16)], "h", 2); R((10, 14, 19, 15), "gr"); R((5, 19, 23, 20), "h"); R((5, 23, 13, 24), "gr"); R((15, 22, 17, 24), "w")
    elif name == "lens":
        Lw([(19, 19), (28, 28)], "br", 5); Lw([(26, 26), (29, 29)], "k", 3)
        E((2, 2, 23, 23), "g"); E((5, 5, 20, 20), "C"); dr.arc((7, 7, 18, 18), 190, 260, fill=C["w"] + (255,), width=2)
    elif name == "chat":
        R((2, 4, 29, 22), "p", 5); P([(7, 21), (14, 21), (6, 28)], "p")
        R((6, 9, 24, 10), "w"); R((6, 13, 20, 14), "P"); R((6, 17, 14, 18), "P")
    elif name == "branch":
        Lw([(9, 7), (9, 25)], "gr", 3); Lw([(23, 14), (23, 17), (19, 21), (10, 22)], "gr", 3)
        for cx, cy in [(9, 6), (9, 26), (23, 11)]:
            E((cx - 4, cy - 4, cx + 4, cy + 4), "gr"); E((cx - 2, cy - 2, cx + 1, cy + 1), "h")
    elif name == "db":
        R((6, 6, 26, 26), "b"); E((6, 22, 26, 29), "b"); E((6, 3, 26, 10), "B")
        for yy in (12, 18):
            dr.arc((6, yy - 3, 26, yy + 3), 0, 180, fill=C["n"] + (255,), width=2)
        for yy in (14, 20, 25):
            R((20, yy, 21, yy + 1), "h")
    elif name == "shield":
        P([(16, 2), (28, 6), (27, 17), (16, 29), (5, 17), (4, 6)], "b"); P([(16, 4), (16, 27), (7, 17), (6, 7)], "B")
        Lw([(9, 15), (14, 20), (23, 9)], "w", 3)
    elif name == "bug":
        for yy in (14, 19, 24):
            Lw([(4, yy - 2), (9, yy)], "k", 2); Lw([(27, yy - 2), (22, yy)], "k", 2)
        Lw([(13, 4), (10, 1)], "k", 1); Lw([(19, 4), (22, 1)], "k", 1)
        E((8, 9, 24, 29), "r"); E((11, 3, 21, 11), "d"); Lw([(16, 11), (16, 28)], "k", 1)
        E((10, 15, 13, 18), "k"); E((19, 17, 22, 20), "k"); E((11, 22, 14, 25), "k"); R((11, 11, 12, 12), "R")
    elif name == "lock":
        dr.arc((8, 2, 24, 20), 180, 360, fill=C["g"] + (255,), width=3); R((8, 10, 10, 14), "g"); R((22, 10, 24, 14), "g")
        R((4, 13, 27, 29), "y", 3); R((6, 15, 25, 16), "Y"); E((14, 18, 18, 22), "k"); R((15, 21, 16, 25), "k")
    elif name == "warn":
        P([(16, 2), (30, 28), (2, 28)], "y"); P([(16, 6), (18, 10), (7, 26), (5, 26)], "Y")
        R((15, 11, 17, 20), "k"); R((15, 23, 17, 25), "k")
    elif name == "server":
        for i, yy in enumerate((3, 12, 21)):
            R((4, yy, 27, yy + 7), "d", 1); R((5, yy + 1, 26, yy + 2), "G"); R((7, yy + 4, 17, yy + 4), "g")
            R((21, yy + 3, 22, yy + 4), "gr" if i != 1 else "r"); R((24, yy + 3, 25, yy + 4), "h")
    elif name == "chip":
        for t in range(10, 23, 3):
            R((t, 3, t, 7), "g"); R((t, 24, t, 28), "g"); R((3, t, 7, t), "g"); R((24, t, 28, t), "g")
        R((7, 7, 24, 24), "gr", 2); R((12, 12, 19, 19), "y"); R((13, 13, 14, 14), "Y"); R((9, 9, 10, 10), "h")
    elif name == "flame":
        P([(16, 1), (24, 11), (27, 20), (23, 28), (9, 28), (5, 20), (8, 11), (12, 15)], "o")
        P([(16, 9), (21, 17), (21, 25), (11, 25), (11, 18), (14, 19)], "y"); P([(16, 16), (19, 22), (16, 25), (13, 22)], "Y")
    elif name == "report":
        R((5, 4, 26, 30), "br", 2); R((8, 7, 23, 28), "w"); R((12, 2, 19, 7), "g", 1)
        for yy in (11, 15, 19):
            R((10, yy, 21, yy), "G")
        Lw([(10, 25), (13, 22), (16, 24), (21, 19)], "r", 2)
    return im


def pixel_icon(name, scale=16):
    base = np.array(icon_draw(name)).astype(np.float32)
    a = base[..., 3] > 0
    pad = lambda m: np.pad(m, 2)
    A = pad(a); B = np.pad(base, ((2, 2), (2, 2), (0, 0)))
    up = np.roll(A, 1, 0); lf = np.roll(A, 1, 1); dn = np.roll(A, -1, 0); rt = np.roll(A, -1, 1)
    rgb = B[..., :3].copy()
    hi = A & (~up | ~lf); sh = A & (~dn | ~rt)
    rgb[hi] = rgb[hi] * .7 + 255 * .3
    rgb[sh] = rgb[sh] * .72
    yy = np.arange(A.shape[0])[:, None] / A.shape[0]
    rgb[A] = (rgb * (1 - .14 * np.repeat(yy, A.shape[1], 1)[..., None]))[A]          # a little darker toward the bottom
    rgb = np.round(rgb / 6) * 6
    k = np.ones((3, 3), np.uint8)
    out_m = cv2.dilate(A.astype(np.uint8), k) > 0
    ext = np.zeros_like(A)
    for dy, dx in ((1, 0), (1, 1), (2, 1)):                           # sticker thickness, down-right
        ext |= np.roll(np.roll(out_m, dy, 0), dx, 1)
    H, W = A.shape; img = np.zeros((H, W, 4), np.float32)
    img[ext] = EDGE + (255,); img[out_m] = OUTL + (255,); img[A, :3] = rgb[A]; img[A, 3] = 255
    big = cv2.resize(img, (W * scale, H * scale), interpolation=cv2.INTER_NEAREST)
    save(big, f"icon_{name}.png")


# ---- heat silhouettes ---------------------------------------------------------------------------
LUT_PTS = [(0, (110, 14, 6)), (.18, (178, 26, 8)), (.38, (226, 62, 12)), (.56, (246, 112, 24)), (.72, (255, 160, 60)), (.86, (255, 212, 128)), (1, (255, 246, 226))]


def heatmap(v):
    v = np.clip(v, 0, 1); out = np.zeros(v.shape + (3,), np.float32)
    for (a, ca), (b, cb) in zip(LUT_PTS[:-1], LUT_PTS[1:]):
        m = (v >= a) & (v <= b); t = ((v - a) / (b - a))[m][:, None]
        out[m] = np.array(ca) * (1 - t) + np.array(cb) * t
    return out


def smooth_union(mask, r):
    m = cv2.GaussianBlur(mask.astype(np.float32), (0, 0), r); return (m > .5).astype(np.uint8)


def heat_layer(mask, name, cold_name=None, lift=.45):
    H, W = mask.shape
    dist = cv2.distanceTransform(mask, cv2.DIST_L2, 5); dist = (dist / dist.max()) ** .55
    y = np.linspace(0, 1, H)[:, None] * np.ones((1, W))
    v = .58 * dist + lift * y ** 1.6 + .05 * lowfreq(H, W, 60, 9) - .05
    v = cv2.GaussianBlur(v.astype(np.float32), (0, 0), 6)
    alpha = cv2.GaussianBlur(mask.astype(np.float32), (0, 0), 2.2)
    rgb = heatmap(v)
    save(np.dstack([rgb, alpha * 255]), name)
    if cold_name:
        g = 34 + 26 * dist + 10 * y
        save(np.dstack([g - 2, g - 3, g, alpha * 255]), cold_name)


def capsule(m, p, q, w):
    cv2.line(m, tuple(int(v) for v in p), tuple(int(v) for v in q), 1, int(w)); return m


def head():
    H, W = 1200, 1340; m = np.zeros((H, W), np.uint8)
    cv2.rectangle(m, (380, 200), (830, 640), 1, -1)                              # skull (rounded below)
    cv2.rectangle(m, (338, 330), (400, 520), 1, -1)                              # visor ridge, facing left
    cv2.rectangle(m, (420, 600), (760, 700), 1, -1)                              # chin plate
    cv2.rectangle(m, (520, 660), (700, 870), 1, -1)                              # neck
    cv2.ellipse(m, (640, 1230), (600, 390), 0, 0, 360, 1, -1)                     # shoulders
    m = smooth_union(m, 30)
    cv2.circle(m, (720, 430), 74, 1, -1)                                          # ear disc
    capsule(m, (600, 205), (630, 70), 22); cv2.circle(m, (634, 56), 36, 1, -1)   # antenna
    m = smooth_union(m, 6)
    heat_layer(m, "head_heat.png", "head_cold.png")


def palm():
    H, W = 1300, 1100; m = np.zeros((H, W), np.uint8)
    cv2.ellipse(m, (560, 760), (245, 275), 0, 0, 360, 1, -1)
    for p, q, w in [((420, 560), (360, 210), 108), ((540, 520), (528, 130), 116), ((655, 535), (705, 170), 110), ((760, 600), (850, 320), 96), ((360, 760), (190, 560), 118)]:
        capsule(m, p, q, w)
    cv2.rectangle(m, (420, 900), (720, 1300), 1, -1)
    m = smooth_union(m, 16)
    heat_layer(m, "palm_heat.png", lift=.5)


# ---- stars --------------------------------------------------------------------------------------
def star(name, W, H, cx, cy, ar, al, bu, bd, p, core, body, edge, bloom_col, bloom):
    y, x = np.mgrid[0:H, 0:W].astype(np.float32)
    ax = np.where(x >= cx, ar, al); by = np.where(y >= cy, bd, bu)
    s = np.abs((x - cx) / ax) ** p + np.abs((y - cy) / by) ** p
    t = np.clip(1 - s, 0, 1)                                            # 0 at the edge, 1 at the centre
    m = cv2.GaussianBlur((s < 1).astype(np.float32), (0, 0), 1.2)
    k1 = np.clip(t / .22, 0, 1)[..., None]; k2 = np.clip((t - .55) / .3, 0, 1)[..., None]
    rgb = np.array(edge) * (1 - k1) + np.array(body) * k1
    rgb = rgb * (1 - k2) + np.array(core) * k2
    a = m
    if bloom:
        bl = cv2.GaussianBlur(m * (.4 + .6 * t), (0, 0), bloom); bl = np.clip(bl / bl.max() * 1.1, 0, 1) * .8
        a2 = np.clip(a + bl * (1 - a), 0, 1)
        rgb = (rgb * a[..., None] + np.array(bloom_col) * (bl * (1 - a))[..., None]) / np.maximum(a2, 1e-4)[..., None]; a = a2
    save(np.dstack([rgb, a * 255]), name)


# ---- ink ----------------------------------------------------------------------------------------
def ink(n, size, seed):
    r = np.random.default_rng(seed); S = size; m = np.zeros((S, S), np.float32)
    ang = np.linspace(0, 2 * np.pi, 400, endpoint=False); k = r.uniform(0, 6.28, 6)
    rad = S * .3 * (1 + .12 * np.sin(3 * ang + k[0]) + .08 * np.sin(5 * ang + k[1]) + .05 * np.sin(9 * ang + k[2]))
    pts = np.stack([S / 2 + rad * np.cos(ang), S / 2 + rad * np.sin(ang)], 1).astype(np.int32)
    cv2.fillPoly(m, [pts], 1)
    for _ in range(r.integers(3, 7)):                                  # droplets
        a = r.uniform(0, 6.28); d = r.uniform(.36, .46) * S; rr = r.uniform(.015, .04) * S
        cv2.circle(m, (int(S / 2 + d * np.cos(a)), int(S / 2 + d * np.sin(a))), int(rr), 1, -1)
    m = cv2.GaussianBlur(m, (0, 0), S * .006); m = np.clip((m - .5) * 6 + .5, 0, 1)
    edge = cv2.GaussianBlur(m, (0, 0), S * .012)
    shine = np.clip(cv2.GaussianBlur(np.roll(np.roll(m, -int(S * .05), 0), -int(S * .05), 1) * m, (0, 0), S * .04) - .55, 0, 1) * 0
    g = 14 + 8 * (1 - edge) + 30 * shine
    save(np.dstack([g, g - 2, g + 2, np.maximum(m, edge * .55) * 255]), f"ink_{n}.png")


if __name__ == "__main__":
    paper(); dark()
    for nm in ["robot", "term", "lens", "chat", "branch", "db", "shield", "bug", "lock", "warn", "server", "chip", "flame", "report"]:
        pixel_icon(nm)
    head(); palm()
    star("star_cyan.png", 2300, 1500, 900, 750, 1060, 900, 720, 720, .42, (238, 254, 255), (78, 236, 255), (34, 118, 255), (60, 200, 255), 46)
    star("star_blue.png", 2300, 1500, 900, 750, 1060, 900, 720, 720, .42, (200, 240, 255), (46, 120, 255), (24, 52, 210), (40, 110, 255), 46)
    star("star_red.png", 800, 800, 400, 400, 330, 330, 360, 360, .55, (250, 70, 60), (214, 24, 30), (150, 10, 14), (200, 20, 24), 0)
    for i in range(6):
        ink(i, 400, 40 + i)
    print("layers ->", OUT, len(os.listdir(OUT)))
