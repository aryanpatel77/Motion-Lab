#!/usr/bin/env python3
"""Measure the reference reel element by element (motion only: positions, scales, rotations, blur, timing).
Reads references/video-by-jordans-archivess/frames (960x720 of a 1440x1080 film, 24 fps) and writes ref_curves.json
in film pixels (x1.5). Nothing from the frames is kept as an asset."""
import json
import os

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
FR = os.path.join(HERE, "..", "..", "references", "video-by-jordans-archivess", "frames")
K = 1.5
out = {}


def img(f):
    return cv2.imread(os.path.join(FR, f"{f:03d}.jpg"))


def hsv(f):
    return cv2.cvtColor(img(f), cv2.COLOR_BGR2HSV)


def stats(mask):
    a = int(mask.sum() // 255)
    if a < 30:
        return None
    ys, xs = np.nonzero(mask)
    return {"area": round(a * K * K), "cx": round(xs.mean() * K, 1), "cy": round(ys.mean() * K, 1),
            "x0": round(xs.min() * K), "x1": round(xs.max() * K), "y0": round(ys.min() * K), "y1": round(ys.max() * K)}


def edge_sharp(gray, mask):
    """mean gradient magnitude on the mask boundary: high = crisp edge, low = blurred"""
    b = cv2.morphologyEx(mask, cv2.MORPH_GRADIENT, np.ones((3, 3), np.uint8)) > 0
    if b.sum() < 20:
        return None
    gx = cv2.Sobel(gray, cv2.CV_32F, 1, 0); gy = cv2.Sobel(gray, cv2.CV_32F, 0, 1)
    return round(float(np.sqrt(gx * gx + gy * gy)[b].mean()), 1)


def series(frames, fn):
    return {str(f): fn(f) for f in frames}


# 1. glowing star (cyan/blue), f51-93
def star(f):
    h = hsv(f); m = cv2.inRange(h, (80, 90, 70), (130, 255, 255)); s = stats(m)
    if s:
        s["hue"] = round(float(h[..., 0][m > 0].mean()), 1)
    return s
out["star"] = series(range(51, 95), star)

# 2. spotlight: corner brightness vs centre, f51-95
def spot(f):
    g = cv2.cvtColor(img(f), cv2.COLOR_BGR2GRAY).astype(np.float32)
    c = g[300:420, 480:640].mean(); e = np.concatenate([g[:80, 700:].ravel(), g[640:, 700:].ravel()]).mean()
    return {"centre": round(float(c), 1), "edge": round(float(e), 1)}
out["spot"] = series(range(51, 96), spot)

# 3. heat silhouettes (orange), f91-160 (head) and f331-383 (hand)
def heat(f):
    h = hsv(f); m = cv2.inRange(h, (0, 110, 110), (28, 255, 255)) | cv2.inRange(h, (170, 110, 110), (180, 255, 255))
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8)); s = stats(m)
    if s:
        s["sharp"] = edge_sharp(cv2.cvtColor(img(f), cv2.COLOR_BGR2GRAY), m)
        s["hue"] = round(float(h[..., 0][m > 0].mean()), 1)
    return s
out["head"] = series(range(91, 160), heat)
out["hand"] = series(range(331, 384), heat)

# 4. icon rings (anything not paper), f159-200 and f287-332: extent, plus rotation/scale between frames (log-polar)
def ring_mask(f):
    h = hsv(f); return ((h[..., 1] > 70) | (h[..., 2] < 80)).astype(np.uint8) * 255
def ring(f):
    s = stats(cv2.morphologyEx(ring_mask(f), cv2.MORPH_OPEN, np.ones((3, 3), np.uint8)))
    return s
def rotscale(frames, centre):
    res = {}
    prev = None
    for f in frames:
        g = cv2.cvtColor(img(f), cv2.COLOR_BGR2GRAY).astype(np.float32)
        lp = cv2.warpPolar(g, (360, 360), centre, 340, cv2.WARP_POLAR_LOG)
        if prev is not None:
            (dx, dy), r = cv2.phaseCorrelate(prev, lp)
            res[str(f)] = {"drot": round(dy * 360 / 360, 2), "dlogscale": round(dx, 2), "resp": round(r, 2)}
        prev = lp
    return res
out["ring1"] = series(range(159, 201), ring)
out["ring1_rot"] = rotscale(range(159, 200), (480, 360))
out["ring2"] = series(range(287, 333), ring)
out["ring2_rot"] = rotscale(range(287, 302), (480, 360))

# 5. conveyors: horizontal speed of the middle band, f221-238 and f255-266
def speed(frames):
    res = {}; prev = None
    for f in frames:
        g = cv2.cvtColor(img(f), cv2.COLOR_BGR2GRAY).astype(np.float32)[240:480]
        if prev is not None:
            (dx, dy), r = cv2.phaseCorrelate(prev, g); res[str(f)] = {"dx": round(dx * K, 1), "dy": round(dy * K, 1), "resp": round(r, 2)}
        prev = g
    return res
out["conv1"] = speed(range(221, 238)); out["conv2"] = speed(range(255, 266))

# 6. word beats on black: the icon (left half, not dark) and the white word (right half), f201-220, 239-254, 267-286
def beat(f):
    im = img(f); h = hsv(im if False else f); g = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
    icon = ((g[:, :560] > 60) | (h[:, :560, 1] > 90)).astype(np.uint8) * 255
    icon = cv2.morphologyEx(icon, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    word = ((g[:, 560:] > 200) & (h[:, 560:, 1] < 40)).astype(np.uint8) * 255
    si = stats(icon); sw = stats(word)
    if si:
        cnts, _ = cv2.findContours(icon, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        big = max(cnts, key=cv2.contourArea); (cx, cy), (w, hh), ang = cv2.minAreaRect(big)
        si["angle"] = round(ang, 1); si["w"] = round(w * K); si["h"] = round(hh * K)
        si["sharp"] = edge_sharp(g[:, :560], icon)
    if sw:
        sw["x0"] += round(560 * K); sw["x1"] += round(560 * K)
    return {"icon": si, "word": sw}
out["beat1"] = series(range(201, 221), beat); out["beat2"] = series(range(239, 255), beat); out["beat3"] = series(range(267, 287), beat)

# 7. letter beats, f383-414: the centre object
def centre_obj(f):
    im = img(f); h = hsv(f); g = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
    bgv = np.median(g[:60, :]); m = (np.abs(g.astype(int) - bgv) > 45) | (h[..., 1] > 120)
    m = m.astype(np.uint8) * 255; m[:, :120] = 0; m[:, 840:] = 0
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    cnts, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cnts = [c for c in cnts if cv2.contourArea(c) > 60]
    if not cnts:
        return None
    c = min(cnts, key=lambda c: abs(cv2.boundingRect(c)[0] + cv2.boundingRect(c)[2] / 2 - 480))
    x, y, w, hh = cv2.boundingRect(c); (_, _), (_, _), ang = cv2.minAreaRect(c)
    return {"cx": round((x + w / 2) * K), "cy": round((y + hh / 2) * K), "w": round(w * K), "h": round(hh * K), "angle": round(ang, 1)}
out["letters_beats"] = series(range(383, 415), centre_obj)

# 8. scattered letters, f421-489: small dark marks, tracked as a set
def marks(f):
    g = cv2.cvtColor(img(f), cv2.COLOR_BGR2GRAY); m = (g < 90).astype(np.uint8) * 255
    n, lab, st, cen = cv2.connectedComponentsWithStats(m)
    pts = [[round(cen[i][0] * K), round(cen[i][1] * K), int(st[i][4])] for i in range(1, n) if 4 < st[i][4] < 900]
    return pts
out["marks"] = series(range(421, 490, 2), marks)

# 9. opener: the big type's horizontal travel and the small sentence's growth
def dark_extent(f):
    g = cv2.cvtColor(img(f), cv2.COLOR_BGR2GRAY); m = (g < 70).astype(np.uint8) * 255
    return stats(m)
out["opener"] = series(range(1, 49), dark_extent)

json.dump(out, open(os.path.join(HERE, "ref_curves.json"), "w"), indent=1)
print("wrote ref_curves.json")
