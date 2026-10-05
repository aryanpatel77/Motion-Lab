#!/bin/sh
# One-time setup for Motion Lab. Safe to re-run.
cd "$(dirname "$0")"
ok()   { printf "  \033[32m✓\033[0m %s\n" "$1"; }
miss() { printf "  \033[31m✗\033[0m %s — %s\n" "$1" "$2"; MISSING=1; }

echo "Checking tools…"
command -v python3 >/dev/null && ok "python3 $(python3 -c 'import sys;print(sys.version.split()[0])')" || miss python3 "install Python 3.10+"
command -v ffmpeg  >/dev/null && ok "ffmpeg"  || miss ffmpeg "brew install ffmpeg  (or apt install ffmpeg)"
command -v ffprobe >/dev/null && ok "ffprobe" || miss ffprobe "comes with ffmpeg"
command -v node    >/dev/null && ok "node $(node -v)" || miss node "install Node.js 20+ (HyperFrames needs it to render)"
command -v uv      >/dev/null && ok "uv"      || miss uv "brew install uv  (or curl -LsSf https://astral.sh/uv/install.sh | sh), needed to analyse pasted links"
[ -n "$MISSING" ] && { printf "\nInstall the missing tools above, then run ./setup.sh again.\n"; exit 1; }

echo "Python packages…"
python3 -c "import PIL, numpy" 2>/dev/null && ok "Pillow, numpy" || { python3 -m pip install --user -r requirements.txt && ok "Pillow, numpy" || miss python-packages "python3 -m pip install --user -r requirements.txt"; }

echo "HyperFrames (HTML → MP4 renderer)…"
npx --yes hyperframes@0.8.59 --version >/dev/null 2>&1 && ok "hyperframes 0.8.59" || miss hyperframes "npx hyperframes@0.8.59 failed — check Node/npm"
npx --yes hyperframes@0.8.59 browser ensure </dev/null >/dev/null 2>&1 && ok "headless Chrome for rendering" || miss chrome "run: npx hyperframes@0.8.59 browser ensure"
[ -n "$MISSING" ] && { printf "\nFix the items above, then run ./setup.sh again.\n"; exit 1; }

echo "Claude Code (optional, powers 'Ask for changes')…"
if command -v claude >/dev/null; then
  claude auth status 2>/dev/null | grep -q '"loggedIn": *true' && ok "Claude Code signed in" || echo "  • Claude Code is installed but not signed in: run  claude auth login"
  npx --yes hyperframes@0.8.59 skills </dev/null >/dev/null 2>&1 && ok "HyperFrames agent skills installed" || echo "  • HyperFrames skills: run 'npx hyperframes@0.8.59 skills' manually if you want them"
else
  echo "  • Not installed. Everything works without it except the in-app 'Ask for changes' box (claude.com/code)."
fi

mkdir -p out references
[ -f templates/lower-third-nestgen/assets/fonts/BriallenDisco-Regular.ttf ] && ok "Briallen Disco font found" || \
  echo "  • Optional: the lower third uses the licensed Briallen Disco font; without it names fall back to Geist (see README → Fonts)"

printf "\nDone. Start Motion Lab with:  python3 tools/serve.py   →  http://localhost:8770\n"
