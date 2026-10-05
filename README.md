# Motion Lab

Turn a reference video into a **re-usable animation template**, then render it with your own words, colours,
photos and screen recordings. Paste a link, and Motion Lab breaks the film into frames, cuts and story sections.
Rebuild it as an HTML/GSAP composition, render to MP4 (with real motion blur), alpha MOV, or an **editable
After Effects project**. Every page has an **Ask for changes** box that sends your request to Claude Code
running on your own machine and shows the result in the UI.

Everything runs locally: rendering uses your Chrome and ffmpeg, and nothing is uploaded anywhere.

## Quick start

```bash
git clone https://github.com/aryanpatel77/Motion-Lab.git
cd Motion-Lab
./setup.sh                 # checks tools, fetches the HyperFrames renderer and its Chrome
python3 tools/serve.py     # → http://localhost:8770
```

**Using Claude Code?** Open a terminal anywhere and say:

> Clone https://github.com/aryanpatel77/Motion-Lab, run its setup, and start Motion Lab.

Claude reads [`CLAUDE.md`](CLAUDE.md), which explains how the project works and its rules.

## Install: everything that must be on the machine

> **AI agents: read this first.** The repo has no bundled binaries. Install every item below before running
> anything. `./setup.sh` checks all of them and prints the exact command for anything missing. Run it, fix what
> it reports, and run it again until it prints `Done`.

### 1. System tools

| Tool | Why | macOS | Ubuntu / Debian |
|---|---|---|---|
| **Python 3.10+** | UI server and tools | `brew install python` | `sudo apt install python3 python3-pip` |
| **ffmpeg** (with libx264) | frames, posters, motion-blur blend, encoding | `brew install ffmpeg` | `sudo apt install ffmpeg` |
| **Node.js 20+** and npm | runs HyperFrames, the renderer | `brew install node` | [nodejs.org](https://nodejs.org) or `nvm install 20` |
| **uv** | runs the newest yt-dlp for pasted links (YouTube breaks old builds) | `brew install uv` | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| **Claude Code** (optional) | powers the in-app *Ask for changes* box | [claude.com/code](https://claude.com/code) | same |

Check them with `python3 --version && ffmpeg -version | head -1 && node -v && uv --version`.

### 2. Python packages

```bash
python3 -m pip install --user -r requirements.txt     # Pillow, numpy
```

### 3. HyperFrames: HTML → MP4 renderer (pinned to 0.8.59)

Each template is an HTML/GSAP composition that [HyperFrames](https://github.com/heygen-com/hyperframes) renders in
headless Chrome. It runs through `npx`, so nothing is vendored, but it must be fetched once with its Chrome:

```bash
npx --yes hyperframes@0.8.59 --version                # downloads the CLI
npx --yes hyperframes@0.8.59 browser ensure           # downloads headless Chrome for rendering
npx --yes hyperframes@0.8.59 doctor                   # checks ffmpeg, Chrome, disk (whisper/Docker/TTS lines are optional)
```

Optional, for AI agents: `npx --yes hyperframes@0.8.59 skills` installs HyperFrames' own agent skills into Claude Code.

### 4. Sign Claude Code in (for *Ask for changes*)

```bash
claude auth login                                     # once; the UI shows a notice until this is done
```

The UI runs `claude -p` in this folder with file edits and a short list of commands (python3, npx, ffmpeg…) allowed, keeps one conversation per
template, and backs up the files before every change so **Undo last change** can restore them.

### 5. Start

```bash
python3 tools/serve.py                                # → http://localhost:8770
```

### Disk space

A 70-second film rendered at 180 fps for motion blur needs several GB of temporary frames. Render long films in
slices (see `templates/site-privacy-v2/make_parts.py`) or set `HYPERFRAMES_EXTRACT_CACHE_DIR=/path/with/space`.

## Using the app

- **Home**: paste a link (YouTube, X, Instagram, or a direct file) or drop a video to analyse it.
- **Templates**: hover to preview, open one to see its versions, render it with your own fields, download the
  **After Effects project** (zip with .jsx, assets and fonts), or **Check without AE**.
- **References**: every analysed film, with a section timeline synced to playback, contact sheets and palette.
- **Renders**: everything you made, grouped by project. Pick two to compare them side by side, frame by frame.
- **Ask for changes**: type a change in plain words ("make it 9:16", "swap the end text"). Claude edits the template
  on your machine, re-renders, and the new version appears. Each change can be undone.

## Use a template

```bash
python3 tools/render.py --list

python3 tools/render.py lower-third-nestgen \
  --set name="Patrick Barnett" --set title="Technical Director, GIS Services" \
  --set company=CSX --set theme=blue --format mov --out out/patrick.mov
```

`--format`: `mp4` (flat) · `mov` (ProRes 4444 **with alpha**, for editing) · `png-sequence` · `gif`.
`--slot screen=/path/app-recording.mp4` drops your own footage into a template that declares that slot.

## Plan a reference into story sections

```bash
python3 tools/analyze_reference.py ref.mp4 --seconds 0 --name my-ref --sections 20
```
`--seconds 0` analyses the whole film. `--sections N` finds the N strongest scene changes by *novelty* (the half-second
before vs after each frame, colour + edge features), so morphs, zoom-throughs and blur dissolves count, not only
hard cuts. Each boundary is snapped to a hard cut within 0.4 s, sections are at least `--min-section` long, and
`section01.jpg…` contact sheets are written. The boundaries land on the story beats; check them on the sheets.

## Reference-vs-ours breakdown film

```bash
python3 tools/breakdown.py --ref ref.mp4 --ours out/our-film.mp4 \
  --map references/my-ref/breakdown-our-film.json --out out/our-film-breakdown.mp4
```
The two films play side by side, section by section, with the technique named and a progress strip. The
reference part is time-stretched to our section length (its speed is shown), and the audio is ours.
Example map: `references/_examples/breakdown-site-privacy.json`.

## Add a new animation from a reference

1. **Analyse** — `python3 tools/analyze_reference.py <file.mp4 | url> --seconds 20 --name my-ref`
   Writes `references/my-ref/`: every frame, the cut list, per-scene contact sheets (every 2nd frame),
   a motion profile, a palette and an `analysis.md` table to fill in.
2. **Read the sheets** and write down each beat: entrance/exit frame of every element, easing, what holds.
3. **Build** the template as a HyperFrames composition in `templates/<id>/` (copy an existing one as a start).
4. **Verify** against the source: snapshot the replica at the *same frames* and stack them side by side.
   Timing is right when the beats land on the same frame, not when it "looks close".
5. **Register** it in `templates/registry.json` with its params, slots and source note.

Reusable motion blocks already identified (see `registry.json` → `blocks`): word-build, glyph-scramble,
pixel-ring-bloom, orbit-tiles, light-trace-reveal, typed-wordmark, cursor-click.

## Editing in Premiere / After Effects

Every template exports **both** ways:

```bash
python3 tools/render.py <id> --format mov          # ProRes 4444 + alpha  -> Premiere, Descript, any NLE
python3 tools/to_after_effects.py <id> --set name="…"   # editable AE comp (.jsx + _assets/)
python3 tools/ae/validate.py out/<id>.jsx          # static check before running it in AE
```

In After Effects: **File > Scripts > Run Script File…** and pick the `.jsx` (keep its `_assets` folder
beside it). You get live text layers, shape layers with Trim Paths and Repeaters, mask wipes, solids and
keyframes — so copy, colour, timing and easing stay editable. From there, **Essential Graphics > export
.mogrt** gives Premiere editors a template whose text they can change.

How it works: a template builder emits a declarative scene (`tools/ae/scene.py`), and one shared
`tools/ae/runtime.jsx` builds it in AE. Adding an AE export for a new template means describing layers,
not writing ExtendScript.

| | alpha .mov | AE `.jsx` |
|---|---|---|
| Pixel-identical to the HTML render | yes | no — textures are simplified |
| Editable text / colour / timing | no | yes |
| Works without After Effects | yes | no |

What the AE version simplifies: starfields, the LED dot texture on the name, particle swarms, blur-heavy
glows and per-letter stagger (approximated with a sweep). Everything structural — word builds, scramble
via Source Text hold keys, light traces, pixel-grid rings, orbit tiles, wipes, the cursor and UI reveal —
is real, keyframed AE.

### Checking an export without After Effects

No After Effects? Two tools stand in for it:

```bash
python3 tools/ae/validate.py out/<id>.jsx              # structural check (keyframe order, parents, masks, assets)
python3 tools/ae/preview.py  out/<id>.jsx --at 2,5,9   # draws the scene with PIL to eyeball layout
```

The preview models AE's semantics (top-left anchors, parent chains that preserve world position, rect masks,
hold keys on Source Text), so layout bugs surface here instead of in AE.

**Fonts:** AE cannot use the `.woff2` files the HTML templates use. Every export ships installable TTFs in
`<script>_assets/fonts` — install them before running the script, or AE silently substitutes fonts and the
layout drifts. The runtime detects substitution and reports it.

**Feedback loop:** running the script writes `motion-lab-ae.log` next to it, listing anything AE refused.
Send that file back after a run and the fixes go into the shared runtime, so every template benefits.

## Templates included

| id | what | length |
|---|---|---|
| `site-privacy-v2` | Light motion-graphics product film: collage opener, word-split carousels, shape morph, icon-as-cursor UI, rolodex text, toggle zoom-through, lockup | 70 s |
| `nestgen-burst` | 3D cube → radial word burst → photo grid → kinetic lines → logo | 10.8 s |
| `promo-kinetic-20s` | 8-scene kinetic promo: word builds, glyph scramble, pixel rings, orbit tiles, terminal, UI reveal | 20 s |
| `frontier-explainer-9s` | Label → icon row → node diagram → chat card | 9 s |
| `lower-third-nestgen` | Light-trace lower third with editable name, title, company and colours | 6 s |
| `lower-third-nestgen-v1`, `site-privacy` | Earlier versions, kept for comparison | |

The Site Privacy footage is FlytBase's own product video. The NestGen photos and logos belong to NestGen / FlytBase;
swap in your own before publishing anything made from those two templates.

## Fonts

All bundled fonts are open licence (Inter, Geist, JetBrains Mono, Libre Caslon, Instrument Serif). The lower third
was designed with **Briallen Disco**, a licensed font that is not included. Without it, names fall back to Geist. If
you own it, put `BriallenDisco-Regular.ttf` in `templates/lower-third-nestgen/assets/fonts/` and `tools/ae/fonts/`.

## Repo layout

```
templates/      one folder per template (index.html composition + assets) and registry.json
tools/          serve.py (UI server) · analyze_reference.py · render.py · breakdown.py · to_after_effects.py · ae/
ui/             the web app (single index.html)
references/     analysed reference films land here (not committed)
out/            renders land here; out/previews holds the gallery previews
```

## House rules

- Every template states its **source** and whether the replica was checked against it, frame by frame.
- Reference films are for **motion study** only. Replace their logos, photos, screenshots and copy before anything
  ships, and don't commit them (`references/` is git-ignored).
- Fonts live inside each template's `assets/fonts/` so renders are reproducible.
