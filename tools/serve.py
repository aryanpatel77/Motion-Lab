#!/usr/bin/env python3
"""Motion Lab UI — local gallery + render console.

  python3 tools/serve.py [--port 8770]      then open http://localhost:8770

Serves the template gallery, runs renders through render.py, and shows the reference analyses.
Local only: rendering needs this machine's ffmpeg/Chrome, so it is not a hosted page.
"""
import argparse
import json
import mimetypes
import os
import re
import subprocess
import threading
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, unquote, quote

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UI = os.path.join(ROOT, "ui")
JOBS = {}


def registry():
    return json.load(open(os.path.join(ROOT, "templates", "registry.json")))


def previews():
    d = os.path.join(ROOT, "out", "previews")
    out = {}
    for f in sorted(os.listdir(d)) if os.path.isdir(d) else []:
        k, ext = os.path.splitext(f)
        if ext == ".mp4":                                    # a preview video: also give it a poster
            out[k] = f"/out/previews/{f}"; out[k + ":poster"] = thumb(os.path.join("out", "previews", f))
        elif k not in out:
            out[k] = f"/out/previews/{f}"
    return out


def references():
    base = os.path.join(ROOT, "references")
    out = []
    if not os.path.isdir(base):
        return out
    for name in sorted(os.listdir(base), key=lambda n: -os.path.getmtime(os.path.join(base, n))):
        d = os.path.join(base, name)
        if not os.path.isdir(d) or name in ("ae-feedback",) or name.startswith("_"):
            continue
        files = os.listdir(d)
        src = next((f for f in files if f.startswith("source.")), None)
        u = f"/references/{quote(name)}"                       # names can contain ? or # (old URL-named folders)
        vid_rel = os.path.join("references", name, src) if src else None
        if not vid_rel and os.path.exists(f"{d}/analysis.json"):
            f0 = json.load(open(f"{d}/analysis.json")).get("file")
            f0 = os.path.normpath(os.path.join(ROOT, f0)) if f0 else None
            if f0 and f0.startswith(ROOT) and os.path.exists(f0):
                vid_rel = os.path.relpath(f0, ROOT)
        if "poster.jpg" not in files and vid_rel:               # older references: pick a real frame, not the sheet grid
            try:
                t = thumb(vid_rel)
                os.link(os.path.join(ROOT, "out", ".thumbs", t.split("/")[-1].split("?")[0]), os.path.join(d, "poster.jpg"))
                files.append("poster.jpg")
            except Exception:
                pass
        info = {"name": name, "title": name, "overview": f"{u}/overview.png" if "overview.png" in files else None,
                "poster": f"{u}/poster.jpg" if "poster.jpg" in files else (f"{u}/overview.png" if "overview.png" in files else None),
                "video": f"{u}/{src}" if src else None,
                "sheets": sorted(f"{u}/{f}" for f in files if f.startswith("scene") and f.endswith(".jpg")),
                "breakdowns": sorted(f for f in files if f.startswith("breakdown") and f.endswith(".json")),
                "complete": "analysis.json" in files}
        if info["complete"]:
            a = json.load(open(f"{d}/analysis.json"))
            fps = a.get("fps") or 30
            info |= {"title": a.get("title") or name, "link": a.get("link"), "size": a.get("size"), "fps": fps, "seconds": a.get("seconds"),
                     "cuts": a.get("cuts"), "scenes": a.get("scenes"), "palette": (a.get("palette") or {}).get("mid_frame_common", []),
                     "sections": [dict(x, sheet=f"{u}/section{x['n']:02d}.jpg" if f"section{x['n']:02d}.jpg" in files else
                                       (f"{u}/section{x['n']}.jpg" if f"section{x['n']}.jpg" in files else None))
                                  for x in (a.get("sections") or [])]}
            if not info["video"] and a.get("file"):
                f = os.path.normpath(os.path.join(ROOT, a["file"]))
                if f.startswith(ROOT) and os.path.exists(f):
                    info["video"] = "/" + os.path.relpath(f, ROOT).replace(os.sep, "/")
        out.append(info)
    return out


def ae_feedback():
    d = os.path.join(ROOT, "references", "ae-feedback")
    out = {"sheets": [], "logs": [], "renders": []}
    if not os.path.isdir(d):
        return out
    for f in sorted(os.listdir(d)):
        p = os.path.join(d, f)
        if not os.path.isfile(p):
            continue
        if f.endswith((".jpg", ".png")):
            out["sheets"].append({"url": f"/references/ae-feedback/{f}", "name": f})
        elif f.endswith((".log", ".txt")):
            out["logs"].append({"url": f"/references/ae-feedback/{f}", "name": f,
                                "text": open(p, errors="replace").read()[:4000]})
        elif f.endswith((".mp4", ".mov")):
            out["renders"].append({"url": f"/references/ae-feedback/{f}", "name": f})
    return out


def scene_previews():
    d = os.path.join(ROOT, "out")
    out = {}
    if not os.path.isdir(d):
        return out
    for name in os.listdir(d):
        if name.endswith("_scene"):
            frames = sorted(f for f in os.listdir(os.path.join(d, name)) if f.endswith(".jpg"))
            out[name[:-6]] = [f"/out/{name}/{f}" for f in frames]
    return out


_PROBE = {}


def probe(path):
    key = (path, os.path.getmtime(path))
    if key not in _PROBE:
        try:
            r = json.loads(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=width,height",
                                           "-select_streams", "v:0", "-of", "json", path], capture_output=True, text=True).stdout)
            st = (r.get("streams") or [{}])[0]
            _PROBE[key] = {"duration": round(float(r["format"]["duration"]), 2), "w": st.get("width"), "h": st.get("height")}
        except Exception:
            _PROBE[key] = {}
    return _PROBE[key]


def thumb(rel):
    """Poster frame for a video: five candidates, keep the most detailed / colourful one (cached in out/.thumbs)."""
    src = os.path.join(ROOT, rel)
    tdir = os.path.join(ROOT, "out", ".thumbs"); os.makedirs(tdir, exist_ok=True)
    dst = os.path.join(tdir, re.sub(r"[^a-zA-Z0-9._-]", "_", rel) + ".jpg")
    if not os.path.exists(dst) or os.path.getmtime(dst) < os.path.getmtime(src):
        from PIL import Image, ImageStat
        dur = probe(src).get("duration") or 2
        best, best_score = None, -1
        for k, f in enumerate((.15, .3, .45, .6, .75)):
            cand = f"{dst}.{k}.jpg"
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{min(dur * f, dur - .1):.2f}", "-i", src, "-frames:v", "1",
                            "-vf", "scale=640:-2", "-q:v", "4", cand])
            if not os.path.exists(cand):
                continue
            im = Image.open(cand).convert("RGB")
            hsv = im.convert("HSV")
            score = ImageStat.Stat(im.convert("L")).stddev[0] + .6 * ImageStat.Stat(hsv).mean[1]   # contrast + colour
            if score > best_score:
                best, best_score = cand, score
        if best:
            os.replace(best, dst)
        for k in range(5):
            if os.path.exists(f"{dst}.{k}.jpg"):
                os.remove(f"{dst}.{k}.jpg")
    return "/out/.thumbs/" + os.path.basename(dst) + f"?v={int(os.path.getmtime(dst))}"


def project_of(fname, ids, owned=None):
    if owned and fname in owned:                            # explicit ownership in registry.json ("renders": [...])
        return owned[fname]
    stem = fname.rsplit(".", 1)[0]
    best = max((i for i in ids if stem.startswith(i)), key=len, default=None)
    return best or re.sub(r"[-_]?(v\d+|\d{9,}|silent|breakdown)$", "", stem)


def renders():
    d = os.path.join(ROOT, "out")
    reg = registry()["templates"]
    ids = [t["id"] for t in reg]
    owned = {f: t["id"] for t in reg for f in t.get("renders", [])}
    items = []
    for f in sorted(os.listdir(d), key=lambda f: -os.path.getmtime(os.path.join(d, f))) if os.path.isdir(d) else []:
        p = os.path.join(d, f)
        ext = os.path.splitext(f)[1]
        if os.path.isfile(p) and ext in (".mp4", ".mov", ".gif", ".jsx", ".zip"):
            it = {"file": f, "url": f"/out/{f}", "size": os.path.getsize(p), "mtime": os.path.getmtime(p), "kind": ext[1:],
                  "project": project_of(f, ids, owned), "title": re.sub(r"[-_]+", " ", f.rsplit(".", 1)[0])}
            if ext in (".mp4", ".mov"):
                it |= probe(p)
                it["thumb"] = thumb(os.path.join("out", f))
            items.append(it)
    return items[:80]


def template_videos(rs):
    """Latest render per template, used for hover-to-play in the gallery."""
    out = {}
    for r in rs:
        if r["kind"] == "mp4" and r["project"] not in out and "breakdown" not in r["file"]:
            out[r["project"]] = {"video": r["url"], "thumb": r.get("thumb")}
    return out


def run_steps(job, steps):
    for cmd in steps:
        JOBS[job].setdefault("cmd", " ".join(cmd))
        p = subprocess.Popen(cmd, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
        for line in p.stdout:
            JOBS[job]["log"].append(line.rstrip()[:300])
        p.wait()
        if p.returncode:
            JOBS[job]["ok"] = False
            JOBS[job]["done"] = True
            return
    JOBS[job]["ok"] = True
    JOBS[job]["done"] = True


def run_job(job, cmd):
    JOBS[job]["cmd"] = " ".join(cmd)
    JOBS[job]["started"] = time.time()
    p = subprocess.Popen(cmd, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
    for line in p.stdout:
        line = line.rstrip()
        if line.startswith("STAGE "):
            JOBS[job]["stage"] = line[6:].strip()
        elif line.startswith("ERROR:"):
            JOBS[job]["error"] = line[6:].strip()
        m = re.search(r"wrote (references/[^ ]+)", line)
        if m:
            JOBS[job]["ref"] = m.group(1).split("/", 1)[1]
        JOBS[job]["log"].append(line[:300])
    p.wait()
    JOBS[job]["done"] = True
    JOBS[job]["ok"] = p.returncode == 0
    JOBS[job]["ended"] = time.time()
    if not JOBS[job]["ok"] and not JOBS[job].get("error"):
        JOBS[job]["error"] = next((l for l in reversed(JOBS[job]["log"]) if l.strip()), "it stopped without a message")[:200]
    out = JOBS[job].get("out")
    if p.returncode == 0 and out and os.path.exists(os.path.join(ROOT, out)):
        JOBS[job]["url"] = "/" + out.replace(os.sep, "/")


# ---------------------------------------------------------------- "Ask for changes": Claude Code, headless, in this project
ASSIST = os.path.join(ROOT, "out", ".assistant")
CLAUDE_TOOLS = ["Read", "Edit", "Write", "Glob", "Grep", "Bash(python3:*)", "Bash(npx:*)", "Bash(ffmpeg:*)", "Bash(ffprobe:*)",
                "Bash(ls:*)", "Bash(cp:*)", "Bash(mkdir:*)", "Bash(cat:*)", "Bash(sips:*)", "Bash(du:*)", "Bash(rm -rf snapshots*)"]


def store():
    os.makedirs(ASSIST, exist_ok=True)
    p = os.path.join(ASSIST, "threads.json")
    return json.load(open(p)) if os.path.exists(p) else {}


def save_store(st):
    json.dump(st, open(os.path.join(ASSIST, "threads.json"), "w"), indent=1)


def target_dir(kind, tid):
    return os.path.join(ROOT, "templates" if kind == "template" else "references", tid)


def backup(kind, tid):
    """Copy the editable files of a template (and the registry) before Claude touches them, for one-click undo."""
    src = target_dir(kind, tid)
    dst = os.path.join(ASSIST, "backups", f"{kind}-{tid}-{int(time.time())}")
    os.makedirs(dst, exist_ok=True)
    for f in os.listdir(src) if os.path.isdir(src) else []:
        if os.path.splitext(f)[1] in (".html", ".js", ".css", ".json", ".md", ".py") and os.path.isfile(os.path.join(src, f)):
            subprocess.run(["cp", "-p", os.path.join(src, f), dst])
    subprocess.run(["cp", "-p", os.path.join(ROOT, "templates", "registry.json"), os.path.join(dst, "__registry.json")])
    return dst


def system_prompt(kind, tid):
    if kind == "template":
        t = next((x for x in registry()["templates"] if x["id"] == tid), {})
        where = f"the Motion Lab template \"{tid}\" ({t.get('title', '')}) in templates/{tid}/"
        render = (f"Then render a new version so it shows up in the UI. If templates/{tid}/README.md describes a render recipe, follow it; "
                  f"otherwise run: python3 tools/render.py {tid} --format mp4 --out out/{tid}-<unix-time>.mp4 . "
                  f"Add the new file name to the \"renders\" list of \"{tid}\" in templates/registry.json (create the list if missing).")
    else:
        where = f"the Motion Lab reference \"{tid}\" in references/{tid}/ (analysis.json, section sheets, BREAKDOWN.md if present)"
        render = "If they ask for a new video, build it as a new template folder in templates/, register it in templates/registry.json, and render it to out/."
    return (f"You are working inside Motion Lab (current directory). The person talks to you through the Motion Lab web UI, not a terminal, "
            f"and may not know After Effects or code. This conversation is about {where}. Read the relevant README first. "
            f"Do what they ask, change nothing else, and make sensible choices instead of asking questions unless the request is truly ambiguous. "
            f"{render} Reply in 2-4 short plain sentences: what you changed, and the name of the new video file if you made one. "
            f"Never print secrets or tokens.")


def run_claude(job, kind, tid, message):
    st = store(); key = f"{kind}:{tid}"; th = st.setdefault(key, {"session": None, "messages": []})
    th["messages"].append({"role": "user", "text": message, "ts": time.time()}); save_store(st)
    JOBS[job]["backup"] = backup(kind, tid)
    cmd = ["claude", "-p", message, "--output-format", "stream-json", "--verbose", "--permission-mode", "acceptEdits",
           "--allowedTools", *CLAUDE_TOOLS, "--append-system-prompt", system_prompt(kind, tid)]
    if th.get("session"):
        cmd += ["--resume", th["session"]]
    env = {k: v for k, v in os.environ.items() if k != "ANTHROPIC_BASE_URL"}
    JOBS[job]["started"] = time.time()
    try:
        p = subprocess.Popen(cmd, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1, env=env)
    except FileNotFoundError:
        JOBS[job] |= {"done": True, "ok": False, "error": "Claude Code isn't installed on this Mac.", "code": "missing"}
        return
    final, err = None, None
    for line in p.stdout:
        line = line.strip()
        try:
            ev = json.loads(line)
        except Exception:
            if line:
                JOBS[job]["events"].append({"kind": "note", "text": line[:300]})
                if "authenticate" in line.lower() or "oauth" in line.lower() or "log in" in line.lower():
                    err = "auth"
            continue
        t = ev.get("type")
        if t == "system" and ev.get("session_id"):
            th["session"] = ev["session_id"]; save_store(st)
        elif t == "assistant":
            for b in (ev.get("message") or {}).get("content", []):
                if b.get("type") == "text" and b.get("text", "").strip():
                    JOBS[job]["events"].append({"kind": "text", "text": b["text"].strip()[:1200]})
                elif b.get("type") == "tool_use":
                    inp = b.get("input") or {}
                    what = inp.get("file_path") or inp.get("command") or inp.get("pattern") or inp.get("path") or ""
                    label = {"Read": "Reading", "Edit": "Editing", "Write": "Writing", "Bash": "Running", "Glob": "Looking for", "Grep": "Searching"}.get(b.get("name"), b.get("name"))
                    if b.get("name") == "Bash" and ("render" in what or "hyperframes" in what):
                        label = "Rendering"
                    JOBS[job]["events"].append({"kind": "tool", "text": f"{label} {os.path.relpath(what, ROOT) if what.startswith(ROOT) else what}"[:200]})
        elif t == "result":
            final = ev.get("result") or ""
            if ev.get("is_error"):
                err = err or ("auth" if "authenticat" in final.lower() else "failed")
            if ev.get("session_id"):
                th["session"] = ev["session_id"]
    p.wait()
    ok = p.returncode == 0 and not err
    if err == "auth":
        msg = "Claude isn't signed in on this Mac. Open Terminal, run  claude auth login  once, then send your request again."
    elif not ok:
        msg = (final or "Claude stopped without finishing.")[:800]
    else:
        msg = final or "Done."
    th["messages"].append({"role": "assistant", "text": msg, "ts": time.time(), "ok": ok, "backup": JOBS[job]["backup"]}); save_store(st)
    JOBS[job] |= {"done": True, "ok": ok, "result": msg, "code": err, "ended": time.time()}


class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _send(self, code, body, ctype="application/json"):
        if isinstance(body, (dict, list)):
            body = json.dumps(body).encode()
        elif isinstance(body, str):
            body = body.encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _file(self, path):
        if not os.path.isfile(path):
            return self._send(404, {"error": "not found"})
        ctype = mimetypes.guess_type(path)[0] or "application/octet-stream"
        size = os.path.getsize(path)
        rng = self.headers.get("Range")                      # video scrubbing
        with open(path, "rb") as fh:
            if rng and rng.startswith("bytes="):
                s, _, e = rng[6:].partition("-")
                s = int(s or 0); e = int(e) if e else size - 1
                fh.seek(s); data = fh.read(e - s + 1)
                self.send_response(206)
                self.send_header("Content-Range", f"bytes {s}-{e}/{size}")
            else:
                data = fh.read()
                self.send_response(200)
            self.send_header("Content-Type", ctype)
            self.send_header("Cache-Control", "no-cache")           # always revalidate: renders and the UI change often
            self.send_header("Accept-Ranges", "bytes")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

    def do_GET(self):
        path = unquote(urlparse(self.path).path)
        if path == "/":
            return self._file(os.path.join(UI, "index.html"))
        if path == "/api/thread":
            q = dict(x.split("=", 1) for x in urlparse(self.path).query.split("&") if "=" in x)
            return self._send(200, store().get(f"{unquote(q.get('kind', ''))}:{unquote(q.get('id', ''))}", {"messages": []}))
        if path == "/api/claude-status":
            try:
                r = subprocess.run(["claude", "auth", "status"], capture_output=True, text=True, timeout=30)
                txt = (r.stdout + r.stderr).strip()
                try:
                    signed = bool(json.loads(r.stdout).get("loggedIn"))
                except Exception:
                    signed = r.returncode == 0 and "not" not in txt.lower()[:80]
                return self._send(200, {"installed": True, "signed_in": signed})
            except FileNotFoundError:
                return self._send(200, {"installed": False, "signed_in": False})
        if path == "/api/jobs":
            return self._send(200, [dict(v, id=k, log=v["log"][-3:]) for k, v in JOBS.items() if not v.get("done") or time.time() - v.get("ended", 0) < 20])
        if path == "/api/data":
            rs = renders()
            return self._send(200, {"templates": registry()["templates"], "blocks": registry().get("blocks", []),
                                    "previews": previews(), "template_videos": template_videos(rs), "references": references(), "renders": rs,
                                    "ae_builders": [t["id"] for t in registry()["templates"] if "after-effects" in (t.get("exports") or [])],
                                    "ae_feedback": ae_feedback(), "scene_previews": scene_previews()})
        if path.startswith("/api/job/"):
            return self._send(200, JOBS.get(path.rsplit("/", 1)[1], {"error": "unknown job"}))
        for prefix in ("/out/", "/references/", "/templates/", "/ui/", "/tools/"):
            if path.startswith(prefix):
                p = os.path.normpath(os.path.join(ROOT, path.lstrip("/")))
                if p.startswith(ROOT):
                    return self._file(p)
        return self._send(404, {"error": "not found"})

    def do_POST(self):
        path = urlparse(self.path).path
        if path == "/api/upload":                          # a dropped video file -> references/_uploads, then analyse it
            name = re.sub(r"[^a-zA-Z0-9._-]", "_", unquote(self.headers.get("X-Filename", "upload.mp4")))[-80:]
            d = os.path.join(ROOT, "references", "_uploads"); os.makedirs(d, exist_ok=True)
            dst = os.path.join(d, name); left = int(self.headers.get("Content-Length", 0))
            with open(dst, "wb") as fh:
                while left > 0:
                    chunk = self.rfile.read(min(left, 1 << 20)); fh.write(chunk); left -= len(chunk)
            return self._send(200, {"path": os.path.relpath(dst, ROOT)})
        body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or "{}")
        job = uuid.uuid4().hex[:10]
        if path == "/api/render":
            tid, fmt = body["id"], body.get("format", "mp4")
            ext = {"mp4": ".mp4", "mov": ".mov", "gif": ".gif", "png-sequence": ""}[fmt]
            name = f"{tid}-{int(time.time())}{ext}"
            out = os.path.join("out", name)
            cmd = ["python3", "tools/render.py", tid, "--format", fmt, "--out", out]
            for k, v in (body.get("params") or {}).items():
                cmd += ["--set", f"{k}={v}"]
            JOBS[job] = {"log": [], "done": False, "out": out, "kind": "render", "label": tid, "stage": "rendering"}
        elif path == "/api/after-effects":
            tid = body["id"]
            out = os.path.join("out", f"{tid}.jsx")
            cmd = ["python3", "tools/to_after_effects.py", tid, "--out", out, "--zip"]
            for k, v in (body.get("params") or {}).items():
                cmd += ["--set", f"{k}={v}"]
            JOBS[job] = {"log": [], "done": False, "out": os.path.join("out", f"{tid}.zip"), "kind": "jsx"}
        elif path == "/api/ae-check":                      # validate + draw the scene without After Effects
            tid = body["id"]
            jsx = os.path.join(ROOT, "out", f"{tid}.jsx")
            at = body.get("at") or "1,3,5,9,13,17,19"
            steps = []
            if not os.path.exists(jsx):
                steps.append(["python3", "tools/to_after_effects.py", tid, "--out", os.path.join("out", f"{tid}.jsx"), "--zip"])
            steps.append(["python3", "tools/ae/validate.py", os.path.join("out", f"{tid}.jsx")])
            steps.append(["python3", "tools/ae/preview.py", os.path.join("out", f"{tid}.jsx"),
                          "--at", at, "--out", os.path.join("out", f"{tid}_scene")])
            JOBS[job] = {"log": [], "done": False, "kind": "check", "steps": len(steps)}
            threading.Thread(target=run_steps, args=(job, steps), daemon=True).start()
            return self._send(200, {"job": job})
        elif path == "/api/ae-log":                        # paste back what AE reported
            d = os.path.join(ROOT, "references", "ae-feedback")
            os.makedirs(d, exist_ok=True)
            name = re.sub(r"[^a-zA-Z0-9._-]", "_", body.get("name") or f"ae-{int(time.time())}.log")
            open(os.path.join(d, name), "w").write(body.get("text", "")[:200000])
            return self._send(200, {"saved": name})
        elif path == "/api/metrics":                       # font metrics measured in the browser
            open(os.path.join(ROOT, "tools", "ae", "metrics.json"), "w").write(json.dumps(body, indent=1))
            return self._send(200, {"saved": len(body)})
        elif path == "/api/ask":
            kind, tid, msg = body.get("kind", "template"), body["id"], body["message"].strip()
            JOBS[job] = {"log": [], "events": [], "done": False, "kind": "ask", "label": f"Claude · {tid}", "stage": "thinking", "target": f"{kind}:{tid}"}
            threading.Thread(target=run_claude, args=(job, kind, tid, msg), daemon=True).start()
            return self._send(200, {"job": job})
        elif path == "/api/ask/undo":
            kind, tid = body.get("kind", "template"), body["id"]
            st = store(); th = st.get(f"{kind}:{tid}", {"messages": []})
            last = next((m for m in reversed(th["messages"]) if m.get("backup") and not m.get("undone")), None)
            if not last or not os.path.isdir(last["backup"]):
                return self._send(200, {"error": "nothing to undo"})
            for f in os.listdir(last["backup"]):
                dst = os.path.join(ROOT, "templates", "registry.json") if f == "__registry.json" else os.path.join(target_dir(kind, tid), f)
                subprocess.run(["cp", "-p", os.path.join(last["backup"], f), dst])
            last["undone"] = True
            th["messages"].append({"role": "assistant", "text": "Undone: the files are back to how they were before that change.", "ts": time.time(), "ok": True})
            save_store(st)
            return self._send(200, {"ok": True})
        elif path == "/api/analyze":
            src = body["src"].strip()
            cmd = ["python3", "tools/analyze_reference.py", src, "--seconds", str(body.get("seconds", 0)), "--sections", str(body.get("sections", 12))]
            if body.get("name"):
                cmd += ["--name", body["name"]]
            JOBS[job] = {"log": [], "done": False, "kind": "analyze", "label": src.split("?")[0][-60:], "stage": "starting"}
        else:
            return self._send(404, {"error": "not found"})
        threading.Thread(target=run_job, args=(job, cmd), daemon=True).start()
        return self._send(200, {"job": job})


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8770)
    a = ap.parse_args()
    print(f"Motion Lab UI  ->  http://localhost:{a.port}")
    ThreadingHTTPServer(("127.0.0.1", a.port), H).serve_forever()
