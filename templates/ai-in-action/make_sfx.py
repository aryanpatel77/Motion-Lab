#!/usr/bin/env python3
"""Synthesised sound for ai-in-action: a soft pad and pulse, key clicks for every typed letter, pen scratches,
whooshes, hits, ink splats and pops on the film's own beats. Writes assets/sfx.wav (48 kHz stereo)."""
import os
import wave

import numpy as np

SR, T = 48000, 23.6
n = int(SR * T)
L = np.zeros(n); R = np.zeros(n)
rs = np.random.default_rng(11)


def add(sig, t, gain=1.0, pan=0.0):
    i = int(t * SR); j = min(n, i + len(sig))
    if i >= n or j <= i:
        return
    L[i:j] += sig[: j - i] * gain * (1 - max(0, pan)); R[i:j] += sig[: j - i] * gain * (1 + min(0, pan))


def env(d, a=0.002, r=None):
    k = max(1, int(d * SR)); e = np.ones(k); ka = max(1, int(a * SR)); e[:ka] = np.linspace(0, 1, ka)
    e *= np.exp(-np.linspace(0, d, k) / (r or d / 4)); return e


def noise(d): return rs.standard_normal(max(1, int(d * SR)))


def hp(x, k=8): return x - np.convolve(x, np.ones(k) / k, "same")


def lp(x, k=30): return np.convolve(x, np.ones(k) / k, "same")


def click():
    d = 0.03; x = hp(noise(d), 4) * env(d, 0.0003, 0.004)
    t = np.arange(len(x)) / SR; x += np.sin(2 * np.pi * rs.uniform(1800, 2600) * t) * env(d, 0.0002, 0.003) * 0.4
    return x * rs.uniform(.6, 1.0)


def thump(d=0.18):
    t = np.arange(int(d * SR)) / SR; return np.sin(2 * np.pi * (70 + 120 * np.exp(-t * 40)) * t) * env(d, 0.001, 0.05)


def kick(d=0.3):
    t = np.arange(int(d * SR)) / SR; return np.sin(2 * np.pi * np.cumsum(46 + 80 * np.exp(-t * 30)) / SR) * env(d, 0.001, 0.08)


def whoosh(d=0.25):
    x = lp(noise(d), 18); x /= np.abs(x).max() + 1e-9; return x * np.sin(np.linspace(0, np.pi, len(x))) ** 2


def scratch(d=0.12):
    x = hp(noise(d), 3); m = (np.sin(np.linspace(0, 40, len(x))) > 0) * .6 + .4; return x * m * env(d, 0.004, d / 2) * 0.5


def hit(d=0.7):
    t = np.arange(int(d * SR)) / SR
    return np.sin(2 * np.pi * (40 + 70 * np.exp(-t * 16)) * t) * env(d, 0.001, 0.22) + hp(noise(d), 3) * env(d, 0.0005, 0.02) * 0.6


def splat(d=0.22):
    x = lp(noise(d), 6) * env(d, 0.001, 0.05); t = np.arange(len(x)) / SR
    return x * 1.4 + np.sin(2 * np.pi * (180 * np.exp(-t * 20) + 60) * t) * env(d, 0.001, 0.06) * 0.6


def pop(f=900, d=0.09):
    t = np.arange(int(d * SR)) / SR; return np.sin(2 * np.pi * f * (1 + 0.8 * np.exp(-t * 60)) * t) * env(d, 0.0005, 0.025)


def glitch(d=0.08):
    t = np.arange(int(d * SR)) / SR; return np.sign(np.sin(2 * np.pi * 1500 * t)) * (rs.random(len(t)) > .45) * env(d, 0.0005, .03) * .3


def shimmer(d=0.9):
    t = np.arange(int(d * SR)) / SR; f = 900 + 1400 * t / d
    return (np.sin(2 * np.pi * np.cumsum(f) / SR) + .5 * np.sin(2 * np.pi * np.cumsum(f * 1.5) / SR)) * env(d, .15, d / 2) * .25


def typing(t0, t1, k, gain=0.32):
    for i in range(k):
        add(click(), t0 + (t1 - t0) * i / max(1, k), gain, pan=rs.uniform(-.3, .3))


# --- bed: a soft pad and a 96 BPM pulse, out on the end card's last second ---------------------
t = np.arange(n) / SR
pad = np.zeros(n)
for f, a in [(110, .5), (164.8, .32), (220, .26), (329.6, .14)]:
    pad += a * np.sin(2 * np.pi * f * t + 0.7 * np.sin(2 * np.pi * 0.21 * t))
pad *= np.clip(t / 1.5, 0, 1) * np.clip((T - t) / 1.2, 0, 1) * 0.07
L += pad; R += pad * .96
for b in np.arange(2.083, 20.3, 60 / 96):
    add(kick(), b, 0.42)
    add(hp(noise(0.04), 3) * env(0.04, .0005, .01), b + 30 / 96, 0.12, pan=.2)

# --- opener ------------------------------------------------------------------------------------
add(scratch(0.08), 0.0, .7); add(hit(.35), 0.083, .55); add(glitch(), 0.09, .6)
for i in range(13):
    add(thump(), 0.167 + i * 0.026, 0.42)
add(whoosh(0.15), 0.31, 0.5); add(glitch(0.05), 0.583, 0.7)
for a, b, k in [(.667, .75, 16), (.875, 1.04, 7), (1.2, 1.32, 5), (1.36, 1.46, 6), (1.58, 1.7, 6), (1.75, 1.82, 3), (1.84, 2.04, 11)]:
    typing(a, b, k)
for tt in [.83, 1.17, 1.33, 1.42, 1.5]:
    add(scratch(), tt, .45, pan=rs.uniform(-.4, .4))
add(hit(), 2.0, 0.95); add(glitch(), 2.02, .5); add(whoosh(.3), 2.06, .55); add(shimmer(), 2.17, .9)
add(hit(1.0), 3.75, 0.7); add(whoosh(.35), 3.83, .35)
# --- head ----------------------------------------------------------------------------------------
typing(3.917, 4.04, 14, .28); add(whoosh(.2), 4.4, .3, .4); add(whoosh(.22), 4.8, .3, -.4)
typing(5.333, 5.42, 3, .28); typing(5.5, 5.6, 5, .28); typing(5.67, 5.78, 5, .28); typing(5.85, 6.0, 11, .28)
add(whoosh(.2), 6.33, .4); add(pop(300, .12), 6.42, .5)
# --- ring ----------------------------------------------------------------------------------------
add(whoosh(.3), 6.5, .6); add(pop(700), 6.6, .5)
for tt in [7.17, 7.42, 7.79]:
    add(whoosh(.16), tt - .15, .35); add(splat(), tt, .8); add(glitch(.05), tt + .02, .4)
add(whoosh(.25), 8.12, .6)
# --- word beats and conveyors --------------------------------------------------------------------
for t0, k in [(8.333, 9), (9.917, 11), (11.083, 7)]:
    add(hit(.5), t0, .7); typing(t0, t0 + .13, k, .4)
add(whoosh(.15), 8.97, .45)
for a, b in [(9.167, 9.917), (10.583, 11.083)]:
    add(whoosh(b - a), a, .5)
    for i in range(int((b - a) * 11)):
        add(pop(rs.uniform(500, 900), .05), a + i / 11, .18, pan=rs.uniform(-.6, .6))
for i in range(4):
    add(pop(1100 + i * 140), 11.2 + i * .09, .35)
# --- ring breaks into ink ------------------------------------------------------------------------
add(whoosh(.3), 11.9, .6); add(hit(.5), 12.5, .6)
for tt in [12.69, 12.94, 13.14, 13.34]:
    add(splat(), tt, .75); typing(tt + .08, tt + .26, 12, .2)
for tt in [12.7, 12.92, 13.25, 13.62]:
    add(scratch(.15), tt, .4)
# --- palm ----------------------------------------------------------------------------------------
add(whoosh(.35), 13.8, .5); typing(13.9, 14.2, 17, .3); typing(14.3, 14.62, 17, .3); add(whoosh(.25), 15.62, .4)
# --- letters -------------------------------------------------------------------------------------
for i, tt in enumerate([15.917, 16.25, 16.583, 16.833]):
    add(whoosh(.1), tt - .03, .4); add(pop(600 + 160 * i, .12), tt + .06, .65); add(thump(.12), tt + .06, .4)
add(whoosh(.4), 17.22, .7)
for i in range(6):
    add(pop(rs.uniform(800, 1300), .06), 17.4 + i * .05, .25, pan=rs.uniform(-.6, .6))
for tt in [19.5, 19.62, 19.72, 19.82, 19.95, 20.05]:
    add(scratch(.14), tt, .35, pan=rs.uniform(-.5, .5))
add(whoosh(.3), 19.98, .55); add(scratch(.16), 20.22, .6)
# --- event card ----------------------------------------------------------------------------------
add(pop(500, .16), 20.45, .7); add(shimmer(.6), 20.5, .5)
for a, b, k in [(20.55, 20.8, 21), (20.8, 21.45, 32), (21.48, 21.6, 4), (21.6, 21.88, 11), (21.88, 22.2, 14), (22.5, 22.95, 31)]:
    typing(a, b, k, .3)
add(scratch(.3), 22.3, .45)
for i in range(5):
    add(pop(1400 + i * 90, .05), 21.0 + i * .25, .2)

mx = max(np.abs(L).max(), np.abs(R).max()); L /= mx / 0.89; R /= mx / 0.89
pcm = (np.stack([L, R], 1) * 32767).astype(np.int16)
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "sfx.wav")
with wave.open(out, "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
print("wrote", out)
