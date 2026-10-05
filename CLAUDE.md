# Motion Lab: guide for Claude Code and other coding agents

Motion Lab turns reference videos into re-usable animation templates. Templates are HyperFrames (HTML + GSAP)
compositions rendered in headless Chrome. The UI is `ui/index.html`, served with its API by `tools/serve.py` on port 8770.

## First run

1. Run `./setup.sh`. Install whatever it reports missing (README → *Install*), then run it again until it prints `Done`.
2. Start the UI: `python3 tools/serve.py` and open http://localhost:8770. It is a long-running server, so start it in
   the background or in its own terminal.
3. For the in-app *Ask for changes* box, the user must run `claude auth login` once. Don't try to sign in for them.

## Where things are

- `templates/registry.json`: every template, with its params, slots, source, status and the renders it owns.
- `templates/<id>/index.html`: the composition. `meta.json` and `hyperframes.json` describe size, fps and duration.
- `tools/render.py <id> --set key=value --slot name=file --format mp4|mov|png-sequence|gif`: render a template.
- `tools/analyze_reference.py <file|url> --seconds 0 --sections 12 --name <slug>`: frames, cuts, story sections,
  contact sheets and palette into `references/<slug>/`.
- `tools/to_after_effects.py <id>`: editable After Effects project (.jsx + `_assets/`). Each template needs a builder in
  `tools/ae/tpl_*.py`. `tools/ae/validate.py` and `tools/ae/preview.py` check an export without After Effects.
- `tools/breakdown.py`: reference-vs-ours side-by-side film, section by section.
- Renders go to `out/`. The gallery's previews are in `out/previews/<id>.mp4|jpg`.

## Rules that matter

- **Every template must also export to After Effects.** A new template needs a `tools/ae/tpl_<name>.py` builder, not just video.
- **Verify replicas against the source at the same frames.** Snapshot the source and the replica on identical
  timestamps and compare them side by side. Timing is right when beats land on the same frame.
- **Reference films are for motion study only.** Replace third-party logos, photos, screenshots and copy, and never
  commit anything under `references/` (it is git-ignored).
- Pin HyperFrames to `0.8.59` (`npx --yes hyperframes@0.8.59 …`).

## HyperFrames gotchas (learned the hard way)

- `<video>` elements must be written **statically in the HTML** and must **not** sit inside a timed `.clip`. The renderer
  pre-extracts video frames by scanning the markup before scripts run, so JS-created or clip-nested videos render as one
  frozen frame. Put them in an untimed wrapper at the root and position them from JS.
- For real motion blur, render at 180 fps and blend 6 sub-frames per output frame:
  `ffmpeg -i in180.mp4 -vf "tmix=frames=6,select='eq(mod(n\,6)\,5)',setpts=N/30/TB" -r 30 out.mp4`.
  Long films at 180 fps need a lot of temporary disk, so render in slices (`templates/site-privacy-v2/make_parts.py`).
- HyperFrames MP4s are BT.601-encoded but tagged BT.709, so saturated colours shift slightly in some players. Decode with
  `scale=in_color_matrix=bt601` when comparing frames numerically.

## After Effects export gotchas

- AE can't use `.woff2`. Exports ship TTFs from `tools/ae/fonts/`, and the runtime reports font substitution.
- Text layout needs real font metrics (`tools/ae/metrics.json`, measured with `tools/ae/measure.html`).
- AE effects can fail silently. Bake blur-heavy glows as PNGs instead of relying on effects.
- AE parenting preserves world position: children follow the parent's change, not its absolute value.
- Running an export's script in AE writes `motion-lab-ae.log` next to it. Fixes go into the shared `tools/ae/runtime.jsx`.

## Pasted links

Links are downloaded with `uvx yt-dlp@latest --js-runtimes node`, trying HLS formats first. Old system yt-dlp builds
often fail on YouTube with 403s or empty results.
