/* NestGen lower third — HyperFrames/GSAP template.
 *
 * Replicates "Lower Thirds (1).mp4" frame by frame (timings measured at 29.97 fps, t=0 = first lit frame):
 *   0.00–0.13  dot blooms and grows into a vertical line                         (power2.out)
 *   0.13–0.47  two light heads run along the top/bottom edge to the right end    (power1.inOut)
 *   0.47–0.53  heads turn inward and close the right side "]"                    (linear)
 *   0.30–0.77  tails chase the heads, leaving a grey motion ghost                 (power1.out)
 *   0.83–1.43  the remaining vertical beam sweeps right->left revealing the bar   (power2.inOut)
 *              letters snap in right->left as the beam passes (horizontal smear), name drifts +45px -> 0
 *   1.47       purple edge line appears under the bar, holds ~0.2s
 *   1.70–2.17  white title bar wipes left->right, edge rides the front, text catches up from +80px (power1.out)
 *   hold       star bokeh twinkles gently
 *   outro      (not in the source) the build reversed, ~0.9s
 *
 * Usage:
 *   el.innerHTML = NGLowerThird.html("lt0", { name, title, company, theme: "purple" | "blue" });
 *   NGLowerThird.animate(tl, "#lt0", { start: 1.0, end: 6.0, outro: true });
 */
(function () {
  const F = 1 / 29.97;                       // one source frame
  const PAD_R = 113;                         // star space to the right of the name (source: 521px bar for "NITIN GUPTA")
  const SX = 0.83;                           // condense Libre Caslon Bold to the source face's letter widths

  // Fonts must be ready before the bar is measured (the timeline is built synchronously at load).
  // Load them synchronously from bytes: a FontFace built from a buffer is usable immediately.
  let fontsReady = false;
  function ensureFonts(base) {
    if (fontsReady) return; fontsReady = true;
    base = base || "assets/fonts/";
    for (const [family, file, weight] of [["NGL Serif", "LibreCaslonText-700.woff2", "700"], ["NGL Sans", "Inter.woff2", "100 900"]]) {
      try {
        const x = new XMLHttpRequest();
        x.open("GET", base + file, false); x.overrideMimeType("text/plain; charset=x-user-defined"); x.send();
        const str = x.responseText, bytes = new Uint8Array(str.length);
        for (let i = 0; i < str.length; i++) bytes[i] = str.charCodeAt(i) & 0xff;
        const ff = new FontFace(family, bytes.buffer, { weight });
        document.fonts.add(ff);
      } catch (e) { /* fall back to the @font-face rules in lower-third.css */ }
    }
  }

  function esc(s) { return String(s).replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c])); }

  // deterministic PRNG for the starfield
  function rng(seed) { let s = seed >>> 0 || 1; return () => ((s = (s * 1664525 + 1013904223) >>> 0) / 4294967296); }

  function starfield(seed, w, h) {
    const r = rng(seed), dust = [], orbs = [];
    for (let i = 0; i < 190; i++) {
      // denser towards the right, like the source
      const x = Math.round(Math.pow(r(), 0.55) * w), y = Math.round(r() * h);
      const a = (0.25 + r() * 0.65).toFixed(2), sz = r() < 0.15 ? 1 : 0;
      dust.push(`${x}px ${y}px 0 ${sz}px rgba(255,255,255,${a})`);
    }
    for (let i = 0; i < 14; i++) {
      const d = Math.round(8 + r() * 14);
      orbs.push({ x: Math.round((0.35 + r() * 0.65) * w - d / 2), y: Math.round(r() * h - d / 2), d, o: (0.25 + r() * 0.45).toFixed(2) });
    }
    return { dust: dust.join(","), orbs };
  }

  function html(id, o) {
    ensureFonts(o.fontBase);
    const letters = [...String(o.name).toUpperCase()].map((c, i) =>
      c === " " ? `<span class="ngl-sp"></span>` : `<span class="ngl-ch" id="${id}-c${i}">${esc(c)}</span>`).join("");
    const sf = starfield(o.seed || 7, 900, 82);
    const orbs = sf.orbs.map((b, i) =>
      `<div class="ngl-orb" id="${id}-orb${i}" style="left:${b.x}px;top:${b.y}px;width:${b.d}px;height:${b.d}px;opacity:${b.o}"></div>`).join("");
    return `
<div class="ngl${o.theme === "blue" ? " ngl--blue" : ""}" id="${id}-root">
  <div class="ngl-win" id="${id}-win" data-layout-allow-overflow>
    <div class="ngl-bar" id="${id}-bar" data-layout-allow-overflow>
      <div class="ngl-stars" style="box-shadow:${sf.dust}"></div>${orbs}
      <div class="ngl-name" id="${id}-name"><span class="ngl-name-in" id="${id}-namein" style="transform:scaleX(${SX})">${letters}</span></div>
    </div>
  </div>
  <div class="ngl-subwin" id="${id}-subwin" data-layout-allow-overflow>
    <div class="ngl-subin" id="${id}-subin" data-layout-allow-overflow>
      <div class="ngl-sub" id="${id}-sub"><span class="ngl-subtxt" id="${id}-subtxt"><span class="ngl-role">${esc(String(o.title).toUpperCase())}${o.company ? ",&nbsp;" : ""}</span>${o.company ? `<span class="ngl-co">${esc(String(o.company).toUpperCase())}</span>` : ""}</span></div>
    </div>
    <div class="ngl-subwash" id="${id}-subwash"></div>
  </div>
  <div class="ngl-edge" id="${id}-edge"></div>
  <div class="ngl-ghosts" id="${id}-ghosts" data-layout-allow-overflow></div>
  <div class="ngl-light" id="${id}-light" data-layout-allow-overflow></div>
</div>`;
  }

  // inverse of power2.inOut (cubic in-out), for "when does the beam pass x?"
  function invInOutCubic(p) {
    return p < 0.5 ? Math.cbrt(p / 4) : 1 - Math.cbrt((1 - p) * 2) / 2;
  }

  function animate(tl, sel, opt) {
    ensureFonts(opt.fontBase);
    const root = document.querySelector(sel + "-root") || document.querySelector(sel);
    const id = root.id.replace(/-root$/, "");
    const q = s => document.getElementById(id + "-" + s);
    const T = opt.start || 0;

    // ---- measure & size ----
    const name = q("name"), bar = q("bar"), win = q("win");
    const nameW = Math.round(q("namein").offsetWidth * SX);
    const barW = Math.round(19 + nameW + PAD_R), barH = 82;
    bar.style.width = barW + "px"; win.style.width = barW + "px";
    const sub = q("sub"), subW = sub.offsetWidth;
    q("subwin").style.width = subW + "px"; q("subin").style.width = subW + "px";

    // bracket box (source: arms run along the bar's top/bottom edges, right side 38px past the bar)
    const L = -2, R = barW + 38, TOP = -1, BOT = barH + 1, CY = barH / 2;
    const V = CY - TOP, H = R - L;

    // ---- build light segments: top path  (L,CY)->(L,TOP)->(R,TOP)->(R,CY); bottom path mirrored ----
    const light = q("light"), ghosts = q("ghosts");
    function seg(key, x, y, len, rot) {
      const w = document.createElement("div");
      w.className = "ngl-seg"; w.style.left = x + "px"; w.style.top = (y - 2) + "px"; w.style.width = len + "px";
      w.style.transform = `rotate(${rot}deg)`;
      // window (tail) > bar (head): visible span = [tail, head] without the two tweens fighting
      const win = document.createElement("div"); win.className = "ngl-segwin"; win.id = `${id}-${key}w`; win.style.width = len + "px";
      const i = document.createElement("i"); i.id = `${id}-${key}`; i.style.width = len + "px";
      win.appendChild(i); w.appendChild(win); light.appendChild(w); return "#" + i.id;
    }
    const s = {
      tv1: seg("tv1", L, CY, V, -90), th: seg("th", L, TOP, H, 0), tv2: seg("tv2", R, TOP, V, 90),
      bv1: seg("bv1", L, CY, V + 1, 90), bh: seg("bh", L, BOT, H, 0), bv2: seg("bv2", R, BOT, V + 1, -90),
    };
    for (const [key, y] of [["gt", TOP], ["gb", BOT]]) {
      const g = document.createElement("div"); g.className = "ngl-ghost"; g.id = `${id}-${key}`;
      g.style.left = (L - 80) + "px"; g.style.top = (y - 6) + "px"; ghosts.appendChild(g);
    }
    const bloom = document.createElement("div"); bloom.className = "ngl-bloom"; bloom.id = id + "-bloom";
    bloom.style.left = (L - 110) + "px"; bloom.style.top = (CY - 110) + "px"; ghosts.parentNode.insertBefore(bloom, ghosts);
    const beam = document.createElement("div"); beam.className = "ngl-beam"; beam.id = id + "-beam";
    beam.style.left = (-2) + "px"; beam.style.top = "-7px"; beam.style.height = (barH + 14) + "px"; light.appendChild(beam);
    const halo = document.createElement("div"); halo.className = "ngl-halo"; halo.id = id + "-halo";
    halo.style.left = "-90px"; halo.style.top = (barH / 2 - 110) + "px"; ghosts.parentNode.insertBefore(halo, ghosts);
    const wash = document.createElement("div"); wash.className = "ngl-wash"; wash.id = id + "-wash";
    wash.style.left = "2px"; wash.style.top = "0px"; wash.style.height = barH + "px"; win.appendChild(wash);

    const $ = k => "#" + id + "-" + k;
    const all = Object.values(s);

    // ---- initial state (applied from t=0 so nothing flashes before the intro) ----
    tl.set(all, { scaleX: 0, x: 0, opacity: 1 }, 0);
    tl.set(all.map(k => k + "w"), { x: 0 }, 0);
    tl.set([$("gt"), $("gb")], { opacity: 0, x: 0 }, 0);
    tl.set($("beam"), { opacity: 0, x: R + 2, scaleY: 1 }, 0);
    tl.set($("halo"), { opacity: 0, x: R + 2 }, 0);
    tl.set($("win"), { x: R }, 0);
    tl.set($("bar"), { x: -R }, 0);
    tl.set($("edge"), { opacity: 0, x: 0 }, 0);
    tl.set($("subwin"), { x: -subW }, 0);
    tl.set($("subin"), { x: subW }, 0);
    tl.set($("subtxt"), { x: 80 }, 0);
    tl.set($("subwash"), { opacity: 0 }, 0);
    tl.set($("wash"), { opacity: 0 }, 0);

    // 1. dot -> vertical line (f32-36)
    tl.fromTo($("bloom"), { opacity: 0, scale: 0.3 }, { opacity: 1, scale: 1, duration: 4 * F, ease: "power2.out" }, T);
    tl.to($("bloom"), { opacity: 0, x: 60, duration: 10 * F, ease: "power1.in" }, T + 5 * F);
    tl.to([s.tv1, s.bv1], { scaleX: 1, duration: 4 * F, ease: "power2.out" }, T);
    // 2. heads run along top/bottom (f36-46), then close the right side (f46-47)
    tl.to([s.th, s.bh], { scaleX: 1, duration: 10 * F, ease: "power1.inOut" }, T + 4 * F);
    tl.to([s.tv2, s.bv2], { scaleX: 1, duration: 2 * F, ease: "none" }, T + 14 * F);
    // 3. tails chase (f41-55) with a grey ghost behind them
    const tail = (segs, len, d, ease, at) => {
      tl.to(segs.map(k => k + "w"), { x: len, duration: d, ease }, at);
      tl.to(segs, { x: -len, duration: d, ease }, at);
    };
    tail([s.tv1, s.bv1], V + 1, 1.2 * F, "none", T + 9 * F);
    tail([s.th, s.bh], H, 12.5 * F, "power1.out", T + 10.5 * F);
    tl.to([$("gt"), $("gb")], { opacity: 1, duration: 4 * F, ease: "power1.out" }, T + 6 * F);
    tl.to([$("gt"), $("gb")], { x: H - 20, duration: 12.5 * F, ease: "power1.out" }, T + 10.5 * F);
    tl.to([$("gt"), $("gb")], { opacity: 0, duration: 5 * F, ease: "power1.in" }, T + 16 * F);

    // 4. the right vertical becomes the beam and sweeps left, revealing the bar (f57-75)
    const B0 = T + 25 * F, BD = 18 * F;
    tl.set([s.tv2, s.bv2], { opacity: 0 }, B0);
    tl.set($("beam"), { opacity: 1 }, B0);
    tl.to($("beam"), { x: 2, duration: BD, ease: "power2.inOut" }, B0);
    tl.to($("halo"), { opacity: 1, duration: 4 * F }, T + 20 * F);
    tl.to($("halo"), { x: 2, duration: BD, ease: "power2.inOut" }, B0);
    tl.to($("halo"), { opacity: 0, duration: 5 * F, ease: "power1.in" }, B0 + BD - 3 * F);
    tl.to($("win"), { x: 0, duration: BD, ease: "power2.inOut" }, B0);
    tl.to($("bar"), { x: 0, duration: BD, ease: "power2.inOut" }, B0);
    tl.set($("wash"), { opacity: 1 }, B0);
    tl.to($("wash"), { opacity: 0, duration: 5 * F, ease: "power1.in" }, B0 + BD - 3 * F);
    tl.to($("beam"), { opacity: 0, duration: 3 * F, ease: "power1.in" }, B0 + BD - 3 * F);
    // name drifts right and settles while letters snap in (f66-80)
    tl.fromTo($("name"), { x: -45 }, { x: 0, duration: 14 * F, ease: "power2.out" }, T + 34 * F);
    const letters = [...name.querySelectorAll(".ngl-ch")];
    letters.forEach(ch => {
      const lx = 19 + ch.offsetLeft * SX - 45 * 0.5;                 // where the letter is when the beam reaches it
      const p = Math.min(1, Math.max(0, (R - lx) / R));          // beam progress needed to pass it
      const t = B0 + invInOutCubic(p) * BD - F;
      tl.fromTo(ch, { opacity: 0, scaleX: 1.6, x: -40 }, { opacity: 1, scaleX: 1, x: 0, duration: 9 * F, ease: "power2.out" }, t);
    });

    // 5. edge line appears under the bar (f76), title bar wipes in (f83-97)
    tl.to($("edge"), { opacity: 1, duration: 2 * F, ease: "power1.out" }, T + 44 * F);
    const W0 = T + 51 * F, WD = 14 * F;
    tl.to($("subwin"), { x: 0, duration: WD, ease: "power1.out" }, W0);
    tl.to($("subin"), { x: 0, duration: WD, ease: "power1.out" }, W0);
    tl.to($("subtxt"), { x: 0, duration: WD, ease: "power1.out" }, W0);
    tl.to($("edge"), { x: subW, duration: WD, ease: "power1.out" }, W0);
    tl.fromTo($("subwash"), { opacity: 0 }, { opacity: 1, duration: 2 * F }, W0 - 2 * F);
    tl.to($("subwash"), { x: subW, duration: WD, ease: "power1.out" }, W0);
    tl.to($("subwash"), { opacity: 0, duration: 3 * F, ease: "power1.in" }, W0 + 1 * F);

    // 6. hold: gentle bokeh twinkle (finite, seek-safe)
    const holdStart = T + 70 * F;
    const holdEnd = opt.end != null ? opt.end - (opt.outro === false ? 0 : 0.9) : holdStart + 6;
    const orbs = [...bar.querySelectorAll(".ngl-orb")];
    orbs.forEach((o, i) => {
      const period = 0.9 + (i % 4) * 0.35, reps = Math.max(0, Math.floor((holdEnd - holdStart) / period) - 1);
      if (reps > 0) tl.to(o, { opacity: 0.12, scale: 0.8, duration: period / 2, ease: "sine.inOut", yoyo: true, repeat: reps * 2 - 1 }, holdStart + i * 0.17);
    });

    // 7. outro (not in the source): reverse of the build
    if (opt.end != null && opt.outro !== false) {
      const O = opt.end - 0.9;
      tl.to($("subwin"), { x: -subW, duration: 0.3, ease: "power2.in" }, O);
      tl.to($("subin"), { x: subW, duration: 0.3, ease: "power2.in" }, O);
      tl.to($("edge"), { x: 0, duration: 0.3, ease: "power2.in" }, O);
      tl.to($("edge"), { opacity: 0, duration: 0.1 }, O + 0.3);
      tl.set($("beam"), { x: 2, scaleY: 1 }, O + 0.3);
      tl.to($("beam"), { opacity: 1, duration: 2 * F }, O + 0.3);
      tl.to($("beam"), { x: R, duration: 0.42, ease: "power2.inOut" }, O + 0.34);
      tl.to($("win"), { x: R, duration: 0.42, ease: "power2.inOut" }, O + 0.34);
      tl.to($("bar"), { x: -R, duration: 0.42, ease: "power2.inOut" }, O + 0.34);
      tl.to($("beam"), { scaleY: 0, opacity: 0, duration: 0.14, ease: "power2.in" }, O + 0.76);
    }
  }

  window.NGLowerThird = { html, animate };
})();
