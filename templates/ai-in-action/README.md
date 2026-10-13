# AI in Action event promo (23.6 s, 1440x1080, 24 fps)

Promo for the AI in Action session "How To Build Multi Agent Systems That Don't Break in Production" (8 Oct).
Motion timing and visual language were measured frame by frame from an Instagram kinetic-type reel
(`references/video-by-jordans-archivess`). Everything on screen is original artwork: the layers come from `make_layers.py`, the type and pen marks from `index.html`. There are no photos or footage. The sound is synthesised by `make_sfx.py`.

| Time | Beat |
|---|---|
| 0-0.67 | Hand-written "how", a yellow frame, huge type travelling left with a redaction bar and dashed rules, collapse to dashes |
| 0.67-2.0 | The sentence types in small: selection handles, pen echo, a loop, a strike, a circle, an underline; new words land grey, then dark |
| 2.0 | Red flash: waveform burst, the word BREAK crushed and spinning |
| 2.08-3.92 | Icons drift in, a glowing four-point star, the spotlight closes, "agents" stays lit, a red flare |
| 3.92-6.58 | The agent's head in heat: "not in a demo." / "you give them real work.", orbits, the light comes up, the heat drains |
| 6.58-8.33 | Ring of 12 pixel icons; ink arcs in and hits three; the ring rushes the lens |
| 8.33-11.92 | One-word beats on black (evidence. / guardrails. / memory.) with conveyors of icons on grey between |
| 11.92-13.83 | The ring returns and breaks; ink takes the pieces: 1M-token context, dead connection, disk full, a claim it shouldn't make |
| 13.83-15.92 | A palm in heat: "know when to act," / "and when to stop." |
| 15.92-17.25 | S · A · F · E, one letter and one icon per beat on paper / black / red / black |
| 17.25-20.38 | Letters scatter, red pen loops, they gather into an ink scribble |
| 20.38-23.6 | Event card: AI in Action, the title with "don't break" underlined, 8 Oct, by the FlytBase team |

## How it is built (v2): layers + measured motion

1. **Measure** the reference, element by element: `python3 measure_ref.py` tracks the star, the spotlight, both heat
   silhouettes, the wreath (scale, and rotation speed by log-polar phase correlation), the conveyors (speed per frame), the
   word-beat icons and words, the letter pops and the scattered letters. It writes `ref_curves.json`. Only motion is
   taken; no pixels from the reference are kept.
2. **Render the layers**: `python3 make_layers.py` writes `assets/layers/`: the paper and dark grounds, 14 pixel icons
   (32 px, rim light, shade, outline, sticker edge, x16), the agent's head and the palm heat-mapped from distance fields,
   a cooled head, cyan and blue four-point stars with bloom, a red star, and six ink blots. All drawn here.
3. **Animate the layers** in `index.html` on the measured curves: `curve()` interpolates measured keyframes and
   `integrate()` turns measured per-frame speeds into positions, so the overshoots and speed ramps are the reference's.

What the measurements changed: the star overshoots to 1.22x in two frames and settles; the spotlight closes on an
ease-in; the head rises 150 px and sways left 74 px before settling, sharpening over 15 frames; the wreath lands at
1.11x and spins on a ramp (9 deg/frame down to 0.55, back up to 7); the conveyors run 300 -> 12 -> 360 px/frame; the
caret slides ~47 px after each word; the second wreath spins up to 41 deg/frame before it breaks.

```bash
python3 measure_ref.py && python3 make_layers.py
python3 make_sfx.py
npx hyperframes@0.8.59 render --fps 120 --quality delivery --workers 4 -o /tmp/aia120.mp4
ffmpeg -i /tmp/aia120.mp4 -i assets/sfx.wav -filter_complex "[0:v]tmix=frames=5,select='eq(mod(n\,5)\,4)',setpts=N/24/TB[v]" \
  -map "[v]" -map 1:a -r 24 -c:v libx264 -crf 15 -pix_fmt yuv420p -c:a aac -b:a 192k -shortest out/ai-in-action.mp4
```
