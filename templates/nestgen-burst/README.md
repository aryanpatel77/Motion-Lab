# NestGen burst promo (10.8 s, 1920×1080, 30 fps)

A NestGen re-skin of the Pinterest "every inspiration in one place" ad. Timings are frame-matched to the reference;
see `../../references/pinterest-burst/BREAKDOWN.md`.

1. **3D cube** (built from the logo's three faces) flies up, then becomes the flat logo (f8–30).
2. **Radial burst**: wedges and NestGen topic keywords, push-in, pull-back (f30–93).
3. **Hero photo card**; a small cube pins its corner and becomes a badge (f94–108).
4. **Photo grid**, with category cuts at f124 and f136 (f109–152).
5. **Session detail card** with comments (f153–175).
6. **Kinetic lines on purple** (f176–271).
7. **NestGen logo** end card.

## Edit
Everything you'd change is in `CONTENT` at the top of `index.html`:
- `keywords`: text, angle, distance, size, style
- `sets`: hero photo, label and grid photos for each category
- `detail`: the detail card's image, title and comments
- `lines`: the end text

Photos live in `assets/img/` (referenced by file name, without `.jpg`).

## Motion
Every move is driven frame by frame from curves measured on the reference: the pin path and size, the logo settle, the
keyword camera (0.3 -> 1.3 -> 0.57), the card landing (690 -> 504 px), the pin slide, the grid fly-in, the detail card's
widen and fall, the text-shrink curves and the end-logo settle. See `curve()` / `drive()` in `index.html`.

The reference only motion-blurs the 3D pin and the pull-back, so the render does too:

## Render (240 fps -> 30 fps, motion blur only on f7-29 and f89-93)
```bash
npx hyperframes@0.8.59 render --fps 240 --quality delivery --workers 4 -o /tmp/ng240.mp4
ffmpeg -i /tmp/ng240.mp4 -i assets/sfx.wav -filter_complex "[0:v]split[a][b];\
[a]select='eq(mod(n\,8)\,0)',setpts=N/30/TB[crisp];[b]tmix=frames=8,select='eq(mod(n\,8)\,7)',setpts=N/30/TB[blur];\
[crisp][blur]overlay=enable='between(n\,7\,29)+between(n\,89\,93)':eof_action=pass,tpad=stop_mode=clone:stop=2,format=yuv420p[v]" \
  -map "[v]" -map 1:a -frames:v 324 -r 30 -c:v libx264 -preset slow -crf 14 \
  -color_primaries smpte170m -color_trc smpte170m -colorspace smpte170m -c:a aac -b:a 192k -t 10.8 ../../out/nestgen-burst-v2.mp4
```
`assets/sfx.wav` is a synthesized effects layer (no music).

## Photos
`ng01-ng24`: the client's NestGen behind-the-scenes photos and session screenshots ("images for vid").
`dr01-dr15`: drone and dock stills from the DOCK OPENING, Asheville Dock 3, oil inspection, construction Dock 3 and
Kling solar clips. `CONTENT.focus` sets a crop point for photos whose subject is off-centre.
