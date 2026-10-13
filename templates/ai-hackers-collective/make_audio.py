#!/usr/bin/env python3
"""Original music bed for ai-hackers-collective: a warm pad and a soft pulse that duck under the voice, low hits on
the slammed words and a lift on the turn ("AI.") and the name. Mixes assets/vo/vo.wav on top -> assets/mix.wav."""
import json
import os
import wave

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__)); SR = 48000; T = 43.0; n = int(SR * T)
rs = np.random.default_rng(5)


def read(p):
    with wave.open(p) as w:
        a = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
        return a.reshape(-1, w.getnchannels()).mean(1), w.getframerate()


vo, sr = read(os.path.join(HERE, "assets", "vo", "vo.wav")); assert sr == SR
vo = np.pad(vo, (0, max(0, n - len(vo))))[:n]
t = np.arange(n) / SR
bed = np.zeros(n)
# chords change with the story: childhood warm (0-16), grown-up flat (11-19), the turn opens up (19-38), name (38+)
prog = [(0, 11, [220, 277.2, 329.6]), (11, 19.3, [196, 233.1, 293.7]), (19.3, 30.4, [261.6, 329.6, 392]), (30.4, 37.9, [220, 293.7, 349.2]), (37.9, T, [261.6, 329.6, 392, 523.3])]
for a, b, fs in prog:
    m = (t >= a) & (t < b); env = np.clip((t - a) / .6, 0, 1) * np.clip((b - t) / .4, 0, 1)
    for f in fs:
        bed[m] += (np.sin(2 * np.pi * f * t[m]) * .5 + np.sin(2 * np.pi * f * 2.001 * t[m]) * .12) * env[m] * .05
pulse_start = 19.3
for k in np.arange(pulse_start, 40.4, 60 / 92):                     # a soft pulse arrives with the new tool
    i = int(k * SR); L = int(.22 * SR); tt = np.arange(L) / SR
    if i + L < n:
        bed[i:i + L] += np.sin(2 * np.pi * (52 + 60 * np.exp(-tt * 30)) * tt) * np.exp(-tt / .07) * .22
words = json.load(open(os.path.join(HERE, "assets", "vo", "words.json")))
def hit(at, g=.35):
    i = int(at * SR); L = int(.5 * SR); tt = np.arange(L) / SR
    if i + L < n: bed[i:i + L] += np.sin(2 * np.pi * (44 + 50 * np.exp(-tt * 18)) * tt) * np.exp(-tt / .14) * g
for at in [.72, 1.72, 6.76, 10.3, 13.86, 17.28, 22.16, 23.98, 25.55, 32.52, 35.52, 38.34, 39.32]:
    hit(at)
for at in [3.3, 9.82, 16.7, 21.95, 30.45, 37.9, 40.45]:                # card cuts: a short airy tick
    i = int(at * SR); L = int(.06 * SR); x = rs.standard_normal(L) * np.exp(-np.arange(L) / (.012 * SR)); bed[i:i + L] += np.diff(x, prepend=0) * .15
# duck the bed under the voice
envv = np.convolve(np.abs(vo), np.ones(int(.05 * SR)) / int(.05 * SR), "same")
duck = 1 - .55 * np.clip(envv / (envv.max() * .25), 0, 1)
duck = np.convolve(duck, np.ones(int(.12 * SR)) / int(.12 * SR), "same")
mix = vo * 1.0 + bed * duck
mix *= np.clip((T - t) / 1.2, 0, 1)
mix /= np.abs(mix).max() / .9
pcm = (np.stack([mix, mix], 1) * 32767).astype(np.int16)
with wave.open(os.path.join(HERE, "assets", "mix.wav"), "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
print("wrote assets/mix.wav")
