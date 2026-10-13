# NestGen behind the scenes (24.6 s, 1440x1080, 25 fps)

A run-and-gun behind-the-scenes edit. The edit rhythm and overlay timing were measured frame by frame from an
Instagram BTS reel (`references/video-by-photovirus`). Every shot, word, colour and sound here is NestGen's own: the
stills are stand-ins until real BTS clips are dropped in.

| Time | Beat |
|---|---|
| 0-1.84 | Whip-pan burst: 2-6 frame shots travelling sideways, an inset punch at 1.04 (the next shot opens as a framed inset for two frames) |
| 1.84-2.88 | Wide shot whips in. Title: 1 frame of letters filled with another shot, 2 frames white, then brand colour with BEHIND · THE · SCENES spread across it; a negative flash at 2.64, a defocused shot under the title at 2.72 |
| 2.88-5.80 | Cut run with one-frame staccato bursts (4.44-4.68, 4.84-5.00) |
| 5.80-6.36 | 3x3 tile reveal of the next shot: each tile lands overexposed for a frame, then settles; white flash out at 6.48 |
| 6.52-10.16 | Cut run, first time stamp (7.96-8.56), a shot that racks out of focus |
| 10.16-13.04 | Talking-head hold with a jump cut in, second stamp |
| 13.04-18.04 | Third stamp (13.96-14.84), cut run with drone footage |
| 18.04-21.92 | Credit-line hold (BUILT · TESTED · FLOWN · BY), negative flash out |
| 21.92-24.6 | Black end card |

A metadata frame (six small labels in the corners and centres), film grain and a vignette sit over everything until
the end card. Every shot drifts handheld (three detuned sines per axis).

Everything in the text is a variable: `title`, `subtitle`, `hud_top_left|center|right`, `hud_bottom_left|center|right`,
`clocks` (comma-separated), `credits`, `end`, `accent`. The title uses the system's Helvetica Neue Condensed Black
(not shipped, macOS) and falls back to Impact.

Real footage: replace the `shot(…, "ng05", …)` image names with clips. A clip needs a static `<video>` tag in
`#root` (see the four drone clips) and `shot(t0, t1, null, { vid: "<id>" })`.

```bash
python3 make_sfx.py                                    # original synthesised pulse + whooshes + hits -> assets/sfx.wav
npx hyperframes@0.8.59 render --fps 125 --quality delivery --workers 4 -o /tmp/bts125.mp4
ffmpeg -i /tmp/bts125.mp4 -i assets/sfx.wav -filter_complex "[0:v]tmix=frames=5,select='eq(mod(n\,5)\,4)',setpts=N/25/TB[v]" \
  -map "[v]" -map 1:a -r 25 -c:v libx264 -crf 15 -pix_fmt yuv420p -c:a aac -b:a 192k -shortest out/nestgen-bts.mp4
```
