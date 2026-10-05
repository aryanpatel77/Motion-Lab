# NestGen lower third (HyperFrames template)

Frame-accurate rebuild of `Lower Thirds (1).mp4`, driven by text instead of a baked video.

- `lower-third.js`: the template (`NGLowerThird.html()` builds the markup, `NGLowerThird.animate()` adds the timeline)
- `lower-third.css`: look (bar gradient, starfield, LED dot-matrix name, glow)
- `index.html`: standalone 1920x1080 project with editable variables

## Render one

```bash
npx hyperframes@0.8.59 render --fps 30000/1001 --variables '{"name":"Patrick Barnett","title":"Technical Director, GIS Services","company":"CSX","bg":"none","outro":true}' --format mov -o patrick.mov
```

`bg`: `green` | `dark` | `none` (transparent, MOV/WebM). `outro`: plays the build in reverse at the end (the source has no outro).

## Use inside another composition

```html
<link rel="stylesheet" href="lower-third.css"><script src="lower-third.js"></script>
<div id="lt" class="clip" data-start="29.6" data-duration="6" data-track-index="30"></div>
<script>
  document.getElementById("lt").innerHTML = NGLowerThird.html("lt0", { name, title, company });
  NGLowerThird.animate(tl, "#lt0", { start: 29.6, end: 35.6, outro: true });
</script>
```

Scale it by transforming the `#lt` container (all internal sizes are 1080p px). Fonts load synchronously from
`assets/fonts/` before the bar is measured; pass `fontBase` if the fonts live elsewhere.

## Timing (29.97 fps, t = 0 at the first lit frame)

| t (s) | beat | ease |
|---|---|---|
| 0.00–0.13 | dot blooms, grows into a vertical line | power2.out |
| 0.13–0.47 | light heads run along the bar's top and bottom edges | power1.inOut |
| 0.47–0.53 | heads turn inward, close the right side | linear |
| 0.30–0.77 | tails chase with a grey motion ghost | power1.out |
| 0.83–1.43 | beam sweeps right→left revealing the bar; letters snap in right→left with smear, name settles from −45px | power2.inOut |
| 1.47 | purple edge appears under the bar | — |
| 1.70–2.17 | white title bar wipes in, edge rides the front, text trails from +80px | power1.out |

Verified against the source: final geometry matches to the pixel (bar 64,810 → 583,947); beam and title-wipe phases
align at 0 frames of lag.

The name face is Libre Caslon Text Bold condensed to 83% (the original font file wasn't available); swap
`LibreCaslonText-700.woff2` for the real font and set `SX` to 1 if you have it.
