#!/usr/bin/env python3
"""Synthesised sound for nestgen-bts: a 120 BPM pulse, whooshes on the whip pans, hits on the title,
glitches on the negative flashes, ticks on the tiles and stamps. Writes assets/sfx.wav (48 kHz stereo)."""
import os
import wave

import numpy as np

SR, T = 48000, 24.6
n = int(SR * T)
L = np.zeros(n); R = np.zeros(n)
rs = np.random.default_rng(7)


def add(sig, t, gain=1.0, pan=0.0):
    i = int(t * SR); j = min(n, i + len(sig))
    if i >= n:
        return
    L[i:j] += sig[: j - i] * gain * (1 - max(0, pan)); R[i:j] += sig[: j - i] * gain * (1 + min(0, pan))


def env(d, a=0.002, r=None):
    k = int(d * SR); e = np.ones(k); ka = max(1, int(a * SR)); e[:ka] = np.linspace(0, 1, ka)
    e *= np.exp(-np.linspace(0, d, k) / (r or d / 4)); return e


def kick(d=0.35):
    t = np.arange(int(d * SR)) / SR; f = 48 + 90 * np.exp(-t * 28)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * env(d, 0.001, 0.09)


def hat(d=0.05):
    x = rs.standard_normal(int(d * SR)); x = np.diff(x, prepend=0); return x * env(d, 0.0005, 0.012) * 0.5


def whoosh(d=0.22, up=True):
    x = rs.standard_normal(int(d * SR)); k = len(x)
    c = np.cumsum(x); c -= np.convolve(c, np.ones(40) / 40, "same")      # band-ish
    shape = np.sin(np.linspace(0, np.pi, k)) ** 2
    return c / (np.abs(c).max() + 1e-9) * shape


def hit(d=0.9):
    t = np.arange(int(d * SR)) / SR
    body = np.sin(2 * np.pi * (38 + 60 * np.exp(-t * 18)) * t) * env(d, 0.001, 0.25)
    crack = rs.standard_normal(len(t)) * env(d, 0.0005, 0.03) * 0.5
    return body + crack


def glitch(d=0.08):
    t = np.arange(int(d * SR)) / SR
    sq = np.sign(np.sin(2 * np.pi * 1800 * t)) * (rs.random(len(t)) > 0.4)
    return sq * env(d, 0.0005, 0.03) * 0.35


def tick(f=2600, d=0.035):
    t = np.arange(int(d * SR)) / SR; return np.sin(2 * np.pi * f * t) * env(d, 0.0003, 0.006)


# pulse bed: 120 BPM, kick on beats, hats on off-beats, out at the end card
for b in np.arange(0, 21.9, 0.5):
    add(kick(), b, 0.55)
    add(hat(), b + 0.25, 0.22, pan=0.25)
    if int(b * 2) % 4 == 3:
        add(hat(0.03), b + 0.375, 0.14, pan=-0.25)
sub = np.sin(2 * np.pi * 41 * np.arange(int(21.9 * SR)) / SR) * 0.08
sub *= np.minimum(1, np.arange(len(sub)) / (0.4 * SR)) * np.minimum(1, (len(sub) - np.arange(len(sub))) / (0.3 * SR))
L[: len(sub)] += sub; R[: len(sub)] += sub

# whip pans (the shots that travel)
for t, up in [(0.0, 1), (0.16, 0), (0.28, 1), (0.40, 1), (0.88, 0), (1.84, 1), (3.40, 1), (3.52, 0), (3.96, 1),
              (4.68, 1), (8.56, 0), (9.36, 1), (15.16, 0), (17.92, 1)]:
    add(whoosh(0.2, up), max(0, t - 0.06), 0.42, pan=0.35 if up else -0.35)
add(whoosh(0.5), 1.0, 0.25)                       # inset punch
# title: a hit on the white frame, a second on the colour, glitch on the negative
add(hit(), 2.30, 0.9); add(hit(0.6), 2.40, 0.55); add(glitch(), 2.64, 0.8); add(glitch(0.05), 2.68, 0.6)
# tile reveal ticks, flash, stamps, credits, end card
for t in [5.80, 5.84, 5.92, 5.96, 6.08, 6.12, 6.16, 6.20, 6.28]:
    add(tick(2200 + 300 * rs.random()), t, 0.35, pan=rs.uniform(-.5, .5))
add(whoosh(0.3), 6.36, 0.3); add(glitch(0.05), 6.48, 0.5)
for t in [7.96, 10.28, 13.96]:
    add(tick(3200, 0.05), t, 0.45); add(tick(1600, 0.06), t + 0.05, 0.25)
add(hit(0.5), 19.08, 0.35)
add(glitch(), 21.88, 0.85); add(hit(1.6), 21.92, 0.7)

mx = max(np.abs(L).max(), np.abs(R).max()); L /= mx / 0.89; R /= mx / 0.89
pcm = (np.stack([L, R], 1) * 32767).astype(np.int16)
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "sfx.wav")
with wave.open(out, "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
print("wrote", out)
