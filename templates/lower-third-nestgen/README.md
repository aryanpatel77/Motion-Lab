# NestGen lower third — v2 (HyperFrames template + After Effects export)

Frame-accurate rebuild of `reference/lower-third-v2-source.mp4` ("Lower Third Template.mp4", 1920x1080, 29.97 fps,
191 frames). The previous design is kept as `templates/lower-third-nestgen-v1`.

- `lower-third.js` — the template (`NGLowerThird.html()` builds the markup, `NGLowerThird.animate()` adds the timeline)
- `lower-third.css` — look (bar, fonts, strip, edge, haze)
- `index.html` — standalone 1920x1080 project with editable variables (defaults reproduce the source)
- Fonts: **Briallen Disco** (speaker name) and **Geist Regular** (designation + company), in `assets/fonts/`

## Render one

```bash
npx hyperframes@0.8.59 render --fps 30000/1001 --variables '{"name":"Patrick Barnett","title":"Technical Director, GIS Services","company":"CSX","bg":"none","theme":"purple"}' --format mov -o patrick.mov
```

`bg`: `black` (as the source) | `green` | `dark` | `none` (transparent, MOV/WebM). `theme`: `purple` (source) | `blue`.
`outro`: the source's outro is the intro played backwards; on by default.

## Use inside another composition

```html
<link rel="stylesheet" href="lower-third.css"><script src="lower-third.js"></script>
<div id="lt" class="clip" data-start="29.6" data-duration="6" data-track-index="30"></div>
<script>
  document.getElementById("lt").innerHTML = NGLowerThird.html("lt0", { name, title, company, theme: "purple" });
  NGLowerThird.animate(tl, "#lt0", { start: 29.6, end: 35.6, outro: true });   // end = when the outro finishes
</script>
```

Intro and outro are 70 frames (2.34 s) each, so give a lower third at least ~5 s. Scale it by transforming the
container (all internal sizes are 1080p px).

## After Effects

```bash
python3 tools/to_after_effects.py lower-third-nestgen --set name="Patrick Barnett" --set title="Technical Director" --set company=CSX --zip
```

Install the two fonts from `_assets/fonts`, then File > Scripts > Run Script File. You get live text layers
(one per name letter, title, company), solids and masks. Every property is keyed once per source frame from
the same curves as the HTML, so AE lands on the HTML's values at each frame. Glows use AE's Glow effect
(close, not identical to the HTML's fitted glow); the bar surface is a sampled PNG.

## Timing (29.97 fps, f = frames after the first lit frame)

| f | beat | curve |
|---|---|---|
| 0–5.6 | centre dot grows into the left "[" | power1.in |
| 4.6–14.8 | light heads run along the bar's top/bottom edges | measured, per frame |
| 6.1–10.7 | left side is eaten from the centre outward | power1.in |
| 10.4–25.8 | tails chase the heads, dragging a purple smear (length ∝ speed) | measured, per frame |
| 14.3–18.8 | right side closes | power1.out |
| 22.3–47.3 | right side becomes the beam, sweeps right→left revealing the bar | power3.inOut |
| 34.8 | one-frame additive white bloom (intro only — absent from the source's outro) | — |
| 35.8 | beam glow turns lavender → neutral; grey haze rides with it until f46 | — |
| 30 + 1.52·j | letter j (counted from the right) smears in from −40px, ×1.6 wide | power2.out, 6f |
| 36.3–58.1 | name settles from −70px | power2.out |
| 42.6–69.6 | purple edge sweeps right, uncovering the white strip behind a lilac wash | power3.inOut |
| 54.1–67.1 | title text slides in from +70px | power2.out |
| outro | the intro reversed (source frame n == frame 192 − n) | reversed eases |

## How it was measured

Head/tail/beam/edge positions were tracked on every source frame and fitted (RMS error: beam 1.5px, strip
front 2.5px, text slide 0.7px, drift 0.6px). The line glow is a sum of six gaussians (σ 1.5–64px) fitted to the
source's cross-section (within ±7 levels out to 60px); wide layers blur a dilated copy so 8-bit filters don't band.
The bar is the source's own colour field (27×8 samples, text masked out) plus seeded grain σ≈4.5.

Frame-by-frame, the render differs from the source by 4.8/255 mean absolute error over the lower-third region;
the static remainder is film grain and the dot-matrix name rasterising a fraction of a pixel differently from AE.

**Colour note:** the source is untagged BT.601. HyperFrames encodes BT.601 but tags its MP4s as BT.709, which makes
players show saturated purples slightly greener. Compare frames by decoding with `scale=in_color_matrix=bt601`, or
retag deliverables (see motion-lab README).
