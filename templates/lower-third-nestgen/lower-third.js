/* NestGen lower third v2 — HyperFrames/GSAP template.
 *
 * Frame-accurate rebuild of "Lower Third Template.mp4" (29.97 fps). Every curve below was measured off the
 * source frame by frame and fitted (see README "How it was measured"); `f` = source frames after the first lit frame.
 *
 *   f0–5.6     centre dot grows into the left "[" (power1.in)
 *   f4.6–14.8  light heads run along the bar's top and bottom edges (measured curve)
 *   f13.9–14.8 heads turn in and close the right side
 *   f9.6–25.8  tails chase (measured curve) dragging a purple smear
 *   f22.3–47.3 the right side becomes a beam and sweeps right->left (power3.inOut), revealing the bar;
 *              its glow turns from lavender to neutral at f36; a wide grey haze rides with it
 *              letters animate in right->left, 1.52f apart, from f30 (hidden until the beam uncovers them)
 *   f36.3–58.1 the name settles from -70px (power2.out)
 *   f44.6      purple edge appears under the bar; f42.7–69.7 it sweeps right (power3.inOut), swelling to 20px
 *              and narrowing back to 2px, uncovering the white strip behind a lilac wash
 *   f54.1–67.1 title text slides in from +70px (power2.out)
 *   hold       static (fixed film grain on the bar)
 *   outro      the intro played backwards — the source is an exact time-reverse (frame n == frame 192-n)
 *
 * Name: Briallen Disco (dot-matrix serif) · title/company: Geist Regular.
 *
 * Usage:
 *   el.innerHTML = NGLowerThird.html("lt0", { name, title, company, theme: "purple" | "blue" });
 *   // or any gradient — glow, trail, edge and wash all take its hue:
 *   el.innerHTML = NGLowerThird.html("lt0", { name, title, company, gradient: ["#1F1EBD", "#4074E4"] });
 *   NGLowerThird.animate(tl, "#lt0", { start: 1.0, end: 6.0, outro: true });   // end = when the outro finishes
 */
(function () {
  const F = 1 / 29.97;                       // one source frame
  const NAME_X = 17;                         // name inset inside the bar
  const PAD_R = 117;                         // bar space right of the name (source: 521px bar for "NITIN GUPTA")
  const BAR_H = 83;
  const INTRO = 70 * F;                      // intro length; the outro takes the same time

  // glow: additive gaussian layers fitted to the source's cross-section (σ px -> gain, tint)
  const GLOW = [[1.5, 0.121, 0], [4, 0.758, 0], [9, 2.319, 1], [18, 5.182, 2], [36, 7.139, 3], [64, 5.832, 3]];
  const BEAM_BOOST = [1.35, 1.35, 1.45, 1.55, 1.6, 1.6];      // the beam glows harder than the lines
  const TINTS = {
    purple: [[0.93, 0.85, 1], [0.86, 0.66, 1], [0.82, 0.58, 1], [0.79, 0.54, 1]],
    purpleBeam: [[1, 0.97, 1], [0.95, 0.86, 1], [0.9, 0.76, 1], [0.85, 0.68, 1]],
    blueBeam: [[0.95, 0.98, 1], [0.8, 0.9, 1], [0.7, 0.84, 1], [0.62, 0.78, 1]],
    blue:   [[0.82, 0.9, 1], [0.62, 0.78, 1], [0.54, 0.72, 1], [0.5, 0.68, 1]],
    neutral:[[1, 1, 1], [1, 1, 1], [1, 1, 1], [1, 1, 1]],
  };

  // measured head/tail progress along the top edge, [frame after T, progress]
  const HEAD = [[4.6, 0], [5.8, .0267], [6.8, .0963], [7.8, .1961], [8.8, .3316], [9.8, .5045], [10.8, .6756],
                [11.8, .8111], [12.8, .9109], [13.8, .9804], [14.8, 1]];
  const TAIL = [[10.4, 0], [10.8, .0107], [11.8, .0749], [12.8, .164], [13.8, .2888], [14.8, .4439], [15.8, .5989],
                [16.8, .7237], [17.8, .8128], [18.8, .8752], [19.8, .9216], [20.8, .9519], [21.8, .9733],
                [22.8, .9875], [23.8, .9947], [24.8, .9964], [25.8, 1]];

  // the bar's colour field, sampled from the source (27 x 8, text masked out); painted bilinearly at any width
  const FIELD = [[[98,0,186],[98,0,186],[99,0,186],[101,0,186],[102,0,187],[104,1,186],[105,2,185],[109,6,188],[110,9,188],[111,12,189],[113,14,190],[115,19,191],[116,20,191],[117,22,191],[118,24,191],[119,25,190],[118,27,189],[116,26,186],[112,26,181],[108,24,174],[103,22,165],[95,18,155],[88,15,144],[82,14,134],[75,11,126],[71,10,119],[66,8,113]],[[99,0,186],[99,0,186],[99,0,186],[101,0,186],[102,0,186],[104,1,186],[105,2,186],[108,5,187],[109,7,187],[110,11,188],[112,14,188],[114,17,189],[114,18,190],[115,20,189],[116,22,190],[116,23,188],[115,23,186],[113,23,183],[110,23,178],[106,21,170],[98,18,161],[91,16,151],[85,13,140],[78,11,130],[72,9,121],[67,9,113],[65,8,110]],[[92,2,173],[92,2,173],[98,0,185],[100,0,186],[102,0,185],[103,1,185],[104,2,185],[107,5,186],[107,6,186],[109,9,186],[110,11,187],[110,12,186],[113,16,188],[112,15,186],[112,17,186],[113,19,185],[111,19,182],[109,19,179],[105,18,173],[101,18,166],[93,15,156],[86,12,145],[80,10,134],[73,8,124],[67,7,115],[63,6,107],[61,6,104]],[[98,0,186],[98,0,186],[98,0,185],[101,0,186],[101,0,185],[102,0,185],[103,1,184],[105,4,185],[107,6,185],[107,8,185],[108,8,185],[108,10,185],[109,12,185],[109,12,184],[109,13,183],[107,13,181],[105,12,177],[103,12,174],[100,12,168],[96,13,161],[90,11,151],[83,9,141],[76,8,129],[69,6,119],[64,5,110],[60,5,102],[57,3,98]],[[97,0,185],[97,0,185],[98,0,185],[100,0,185],[101,0,185],[102,0,184],[102,1,184],[104,3,184],[105,4,183],[106,6,184],[107,7,184],[106,8,183],[106,8,182],[106,9,181],[106,10,181],[103,9,177],[102,9,175],[101,9,172],[97,9,165],[92,8,157],[86,7,146],[80,7,137],[73,6,124],[66,6,114],[61,4,105],[56,4,98],[53,3,93]],[[97,0,185],[97,0,185],[98,0,185],[99,0,184],[100,0,184],[101,1,184],[102,1,183],[103,2,183],[104,3,182],[105,5,182],[104,5,183],[105,7,182],[103,6,180],[103,6,179],[103,7,179],[100,6,175],[100,6,173],[98,6,169],[95,7,163],[89,5,154],[82,5,142],[77,5,133],[69,4,121],[63,4,110],[57,3,101],[54,3,94],[50,2,89]],[[98,0,185],[98,0,185],[98,0,184],[99,0,184],[100,0,183],[101,0,183],[101,1,182],[102,1,182],[103,2,181],[103,3,181],[103,3,181],[103,4,180],[103,5,179],[102,4,178],[100,4,177],[99,4,174],[98,4,171],[95,3,167],[91,3,161],[87,3,153],[80,3,142],[74,3,130],[67,3,118],[60,3,107],[55,3,96],[51,3,90],[47,2,86]],[[97,0,184],[97,0,184],[98,0,184],[99,0,185],[99,0,183],[102,0,183],[101,1,182],[101,1,182],[101,2,181],[102,3,180],[102,3,179],[101,4,180],[100,2,178],[101,3,178],[100,3,176],[99,3,174],[95,1,170],[93,1,166],[88,2,160],[86,2,152],[80,2,141],[72,2,128],[65,2,116],[59,2,105],[52,2,94],[48,2,87],[48,2,83]]];

  let fontsReady = false;
  function ensureFonts(base) {
    if (fontsReady) return; fontsReady = true;
    base = base || "assets/fonts/";
    for (const [family, file] of [["NGL Disco", "BriallenDisco-Regular.ttf"], ["NGL Geist", "Geist-Regular.otf"]]) {
      try {
        const x = new XMLHttpRequest();
        x.open("GET", base + file, false); x.overrideMimeType("text/plain; charset=x-user-defined"); x.send();
        const str = x.responseText, bytes = new Uint8Array(str.length);
        for (let i = 0; i < str.length; i++) bytes[i] = str.charCodeAt(i) & 0xff;
        document.fonts.add(new FontFace(family, bytes.buffer, { weight: "400" }));
      } catch (e) { /* fall back to the @font-face rules in lower-third.css */ }
    }
  }

  function esc(s) { return String(s).replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c])); }
  function rng(seed) { let s = seed >>> 0 || 1; return () => ((s = (s * 1664525 + 1013904223) >>> 0) / 4294967296); }

  // ---- custom gradients: every colour of the effect is derived from the gradient's hue ----
  const hexRGB = h => { h = String(h).replace("#", ""); if (h.length === 3) h = h.replace(/./g, "$&$&");
    return [0, 2, 4].map(i => parseInt(h.slice(i, i + 2), 16)); };
  const lum = c => 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2];
  const mixW = (c, w) => c.map(v => v * (1 - w) + w);                      // toward white, 0..1 channels
  function palette(grad) {
    const [A, B] = grad.map(hexRGB);
    const src = lum(B) >= lum(A) ? B : A, mx = Math.max(...src) || 1;
    const c = src.map(v => v / mx);                                        // hue at full strength
    // same white-mix steps as the source's purple glow; scaled to the purple glow's brightness so
    // bright hues (green, orange) glow no harder than the original
    const fit = (w, ref) => { const t = mixW(c, w), k = Math.min(1, lum(ref) / lum(t)); return t.map(v => +(v * k).toFixed(3)); };
    // outer layers more saturated than the purple's: blues/greens carry a lot of green light and wash out to
    // white-grey at the purple's white mix, so the hue would stop reading
    const tints = [0.6, 0.35, 0.22, 0.15].map((w, i) => fit(w, TINTS.purple[i]));
    const beam = [0.9, 0.6, 0.4, 0.3].map((w, i) => fit(w, TINTS.purpleBeam[i]));
    const rgb = (t, k) => t.map(v => Math.round(v * k)).join(",");
    return { tints, beam, css:
      `--ngl-edge:rgb(${rgb(mixW(c, .2), 210)});--ngl-edge-glow:rgba(${rgb(mixW(c, .2), 210)},.9);` +
      `--ngl-edge-glow2:rgba(${rgb(c, 180)},.75);--ngl-trail:rgb(${rgb(c, 200)});` +
      `--ngl-wash:${rgb(mixW(c, .66), 251)};--ngl-beamwash:${rgb(mixW(c, .85), 255)};` };
  }
  const GRAD = {};                                                          // id -> [from, to]

  // bar surface: the sampled colour field + static mono grain (source σ≈4.5, same on every frame), seeded
  function paintBar(w, h, theme, grad) {
    const G2 = grad && grad.map(hexRGB);
    // with a custom gradient, keep only the source's vertical light (top-centre lift, darker lower right)
    const colMean = FIELD[0].map((_, c) => FIELD.reduce((a, row) => a + lum(row[c]), 0) / FIELD.length);
    try {
      const c = document.createElement("canvas"); c.width = w; c.height = h;
      const g = c.getContext("2d"), img = g.createImageData(w, h), r = rng(11);
      const rows = FIELD.length, cols = FIELD[0].length;
      for (let y = 0; y < h; y++) {
        const fy = Math.min(rows - 1, Math.max(0, (y - 1) / (h - 3) * (rows - 1))), y0 = Math.floor(fy), y1 = Math.min(rows - 1, y0 + 1), ty = fy - y0;
        for (let x = 0; x < w; x++) {
          const fx = Math.min(cols - 1, Math.max(0, (x - 2) / (w - 5) * (cols - 1))), x0 = Math.floor(fx), x1 = Math.min(cols - 1, x0 + 1), tx = fx - x0;
          const n = (r() + r() + r() - 1.5) * 7.8, i = (y * w + x) * 4;
          for (let ch = 0; ch < 3; ch++) {
            const a = FIELD[y0][x0][ch] * (1 - tx) + FIELD[y0][x1][ch] * tx, b = FIELD[y1][x0][ch] * (1 - tx) + FIELD[y1][x1][ch] * tx;
            img.data[i + ch] = a * (1 - ty) + b * ty;
          }
          if (G2) {
            const fl = lum([0, 1, 2].map(k => img.data[i + k])), cm = colMean[x0] * (1 - tx) + colMean[x1] * tx;
            const v = cm ? fl / cm : 1, u = w > 1 ? x / (w - 1) : 0;
            for (let ch = 0; ch < 3; ch++) img.data[i + ch] = Math.min(255, (G2[0][ch] * (1 - u) + G2[1][ch] * u) * v);
          } else if (theme === "blue") {                // purple field -> bright blue / navy, same light
            const R = img.data[i], G = img.data[i + 1], B = img.data[i + 2];
            img.data[i] = 0.18 * R; img.data[i + 1] = 0.55 * R + G; img.data[i + 2] = Math.min(255, 1.3 * B);
          }
          for (let ch = 0; ch < 3; ch++) img.data[i + ch] = Math.max(0, Math.min(255, img.data[i + ch] + n));
          img.data[i + 3] = 255;
        }
      }
      g.putImageData(img, 0, 0); return c.toDataURL("image/png");
    } catch (e) { return ""; }
  }

  // Chrome runs SVG filters at 8 bits: a wide blur of a 2px line peaks at ~3/255, so a big gain would band.
  // Wide layers therefore blur a dilated copy (same energy, gain ~1) instead of amplifying a thin one.
  function glowFilter(fid, tint, boost) {
    const t = Array.isArray(tint) ? tint : TINTS[tint];
    let s = `<filter id="${fid}" filterUnits="userSpaceOnUse" x="-260" y="-260" width="1240" height="620" color-interpolation-filters="sRGB">`;
    GLOW.forEach(([sd, w, ti], i) => {
      const [r, g, b] = t[ti], G = w * (boost ? boost[i] : 1);
      const rad = Math.min(8, Math.max(0, Math.round(G / 1.2 - 1))), gain = G / (1 + rad);
      const src = rad ? `m${i}` : "SourceAlpha";
      if (rad) s += `<feMorphology in="SourceAlpha" operator="dilate" radius="${rad}" result="m${i}"/>`;
      s += `<feGaussianBlur in="${src}" stdDeviation="${sd}" result="b${i}"/>`
         + `<feColorMatrix in="b${i}" type="matrix" values="0 0 0 0 ${r}  0 0 0 0 ${g}  0 0 0 0 ${b}  0 0 0 ${gain.toFixed(3)} 0" result="c${i}"/>`;
      if (i) s += `<feComposite in="a${i - 1}" in2="c${i}" operator="arithmetic" k1="0" k2="1" k3="1" k4="0" result="a${i}"/>`;
      else s += `<feOffset in="c0" dx="0" dy="0" result="a0"/>`;
    });
    return s + `<feMerge><feMergeNode in="a${GLOW.length - 1}"/><feMergeNode in="SourceGraphic"/></feMerge></filter>`;
  }

  function html(id, o) {
    ensureFonts(o.fontBase);
    const theme = o.theme === "blue" ? "blue" : "purple";
    const grad = Array.isArray(o.gradient) && o.gradient.length === 2 && o.gradient.every(Boolean) ? o.gradient : null;
    const pal = grad ? palette(grad) : null;
    if (grad) GRAD[id] = grad;
    const letters = [...String(o.name).toUpperCase()].map((c, i) =>
      c === " " ? `<span class="ngl-sp"></span>` : `<span class="ngl-ch" id="${id}-c${i}">${esc(c)}</span>`).join("");
    return `
<div class="ngl${theme === "blue" && !grad ? " ngl--blue" : ""}" id="${id}-root"${pal ? ` style="${pal.css}"` : ""}>
  <svg width="0" height="0" style="position:absolute" aria-hidden="true"><defs>${glowFilter(id + "-glow", pal ? pal.tints : theme)}${glowFilter(id + "-glowB", pal ? pal.beam : theme + "Beam", BEAM_BOOST)}${glowFilter(id + "-glowN", "neutral")}</defs></svg>
  <div class="ngl-halo" id="${id}-halo"></div>
  <div class="ngl-flash" id="${id}-flash"></div>
  <div class="ngl-win" id="${id}-win" data-layout-allow-overflow>
    <div class="ngl-bar" id="${id}-bar" data-layout-allow-overflow>
      <div class="ngl-name" id="${id}-name"><span class="ngl-name-in" id="${id}-namein">${letters}</span></div>
    </div>
    <div class="ngl-wash" id="${id}-wash"></div>
  </div>
  <div class="ngl-subwin" id="${id}-subwin" data-layout-allow-overflow>
    <div class="ngl-subin" id="${id}-subin" data-layout-allow-overflow>
      <div class="ngl-sub" id="${id}-sub"><span class="ngl-subtxt" id="${id}-subtxt"><span class="ngl-role">${esc(String(o.title).toUpperCase())}${o.company ? ",&nbsp;" : ""}</span>${o.company ? `<span class="ngl-co">${esc(String(o.company).toUpperCase())}</span>` : ""}</span></div>
    </div>
    <div class="ngl-subwash" id="${id}-subwash"></div>
  </div>
  <div class="ngl-edge" id="${id}-edge"></div>
  <div class="ngl-ghosts" id="${id}-ghosts" data-layout-allow-overflow></div>
  <div class="ngl-light" id="${id}-light" style="filter:url(#${id}-glow)" data-layout-allow-overflow></div>
  <div class="ngl-light" id="${id}-lightB" style="filter:url(#${id}-glowB)" data-layout-allow-overflow></div>
  <div class="ngl-light" id="${id}-lightN" style="filter:url(#${id}-glowN)" data-layout-allow-overflow></div>
</div>`;
  }

  const inOut3 = p => p < .5 ? 8 * p ** 4 : 1 - (-2 * p + 2) ** 4 / 2;         // power3.inOut
  const out2 = p => 1 - (1 - p) ** 3;                                            // power2.out
  // an ease through measured samples: [[frame, progress], ...] -> (ease, start frame, duration frames)
  function table(pts) {
    const f0 = pts[0][0], d = pts[pts.length - 1][0] - f0;
    const ease = p => {
      const f = f0 + p * d;
      for (let i = 1; i < pts.length; i++) if (f <= pts[i][0]) {
        const [a, pa] = pts[i - 1], [b, pb] = pts[i];
        return pa + (pb - pa) * (f - a) / (b - a);
      }
      return 1;
    };
    return { ease, f0, d };
  }
  function reverseEase(e) {
    const fn = typeof e === "function" ? e : gsap.parseEase(e || "none");
    return p => 1 - fn(1 - p);
  }

  function animate(tl, sel, opt) {
    ensureFonts(opt.fontBase);
    const root = document.querySelector(sel + "-root") || document.querySelector(sel);
    const id = root.id.replace(/-root$/, "");
    const q = s => document.getElementById(id + "-" + s);
    const T = opt.start || 0;
    const at = f => T + f * F;

    // ---- measure & size ----
    const name = q("name"), bar = q("bar"), win = q("win");
    const nameW = q("namein").offsetWidth;
    const barW = Math.round(NAME_X + nameW + PAD_R);
    bar.style.width = barW + "px"; win.style.width = barW + "px";
    const surf = paintBar(barW, BAR_H, root.classList.contains("ngl--blue") ? "blue" : "purple", GRAD[id]);
    if (surf) bar.style.background = `url(${surf}) 0 0 / ${barW}px ${BAR_H}px no-repeat`;
    const sub = q("sub"), subW = sub.offsetWidth;
    q("subwin").style.width = subW + "px"; q("subin").style.width = subW + "px";
    q("subwash").style.left = (subW - 30) + "px";

    // bracket geometry (source: top edge on the bar's first row, bottom on row 83, right side 38px past the bar)
    const L = -0.5, R = barW + 38, TOP = 0, BOT = BAR_H, CY = BAR_H / 2;
    const V = CY - TOP, H = R - L;

    const light = q("light"), lightB = q("lightB"), lightN = q("lightN"), ghosts = q("ghosts");
    function seg(key, x, y, len, rot, th) {
      const w = document.createElement("div");
      w.className = "ngl-seg"; w.style.left = x + "px"; w.style.top = (y - th / 2) + "px"; w.style.width = len + "px";
      w.style.height = th + "px"; w.style.transform = `rotate(${rot}deg)`; w.style.transformOrigin = `0 ${th / 2}px`;
      const sw = document.createElement("div"); sw.className = "ngl-segwin"; sw.id = `${id}-${key}w`;
      sw.style.width = len + "px"; sw.style.height = th + "px";
      const i = document.createElement("i"); i.id = `${id}-${key}`; i.style.width = len + "px"; i.style.height = th + "px";
      sw.appendChild(i); w.appendChild(sw); light.appendChild(w); return "#" + i.id;
    }
    const s = {
      tv1: seg("tv1", L, CY, V, -90, 2.5), th: seg("th", L, TOP, H, 0, 2), tv2: seg("tv2", R, TOP, V, 90, 2.5),
      bv1: seg("bv1", L, CY, V, 90, 2.5), bh: seg("bh", L, BOT, H, 0, 2), bv2: seg("bv2", R, BOT, V, -90, 2.5),
    };
    for (const [key, y] of [["gt", TOP], ["gb", BOT]]) {
      const g = document.createElement("div"); g.className = "ngl-ghost"; g.id = `${id}-${key}`;
      g.style.left = (L - 75) + "px"; g.style.top = (y - 7) + "px"; ghosts.appendChild(g);
    }
    const mkBeam = (host, key) => {
      const b = document.createElement("div"); b.className = "ngl-beam"; b.id = `${id}-${key}`;
      b.style.left = "-1.25px"; b.style.top = "0px"; b.style.height = BAR_H + "px"; host.appendChild(b);
    };
    mkBeam(lightB, "beam"); mkBeam(lightN, "beamN");
    const halo = q("halo"); halo.style.left = "-300px"; halo.style.top = (CY - 300) + "px";
    const flash = q("flash"); flash.style.left = "-450px"; flash.style.top = (CY - 450) + "px";
    const wash = q("wash"); wash.style.height = BAR_H + "px";

    const $ = k => "#" + id + "-" + k;
    const all = Object.values(s);

    // ---- recorder: every intro tween is kept so the outro can replay it backwards ----
    const rec = [];
    const K = (target, from, to, f, d, ease) => {
      ease = ease || "none";
      tl.fromTo(target, { ...from }, { ...to, duration: d * F, ease, immediateRender: false }, at(f));
      rec.push({ target, from, to, t: at(f), dur: d * F, ease });
    };
    const KT = (target, from, to, tb) => K(target, from, to, tb.f0, tb.d, tb.ease);

    // ---- initial state ----
    const letters = [...name.querySelectorAll(".ngl-ch")];
    const init = [
      [all, { scaleX: 0, x: 0, opacity: 1 }], [all.map(k => k + "w"), { x: 0 }],
      [[$("gt"), $("gb")], { opacity: 0, x: 0, scaleX: .05 }],
      [[$("beam"), $("beamN")], { opacity: 0, x: R }], [$("halo"), { opacity: 0, x: R }], [$("flash"), { opacity: 0 }],
      [$("win"), { x: R }], [$("bar"), { x: -R }], [$("wash"), { opacity: 0 }], [$("name"), { x: -70 }],
      [letters, { opacity: 0, scaleX: 1.6, x: -40 }],
      [$("edge"), { opacity: 0, x: 0, scaleX: 1 }], [$("subwin"), { x: -subW }], [$("subin"), { x: subW }],
      [$("subtxt"), { x: 70 }], [$("subwash"), { opacity: 0, scaleX: .2 }],
    ];
    for (const [t, v] of init) tl.set(t, v, 0);

    // 1. centre dot grows into "["
    K([s.tv1, s.bv1], { scaleX: 0 }, { scaleX: 1 }, 0, 5.6, "power1.in");
    // 2. heads run along the edges, then close the right side
    KT([s.th, s.bh], { scaleX: 0 }, { scaleX: 1 }, table(HEAD));
    K([s.tv2, s.bv2], { scaleX: 0 }, { scaleX: 1 }, 14.3, 4.5, "power1.out");
    // 3. tails chase with a purple smear
    K([s.tv1, s.bv1].map(k => k + "w"), { x: 0 }, { x: V + 3 }, 6.1, 4.6, "power1.in");
    K([s.tv1, s.bv1], { x: 0 }, { x: -V - 3 }, 6.1, 4.6, "power1.in");
    const tail = table(TAIL);
    KT([s.th, s.bh].map(k => k + "w"), { x: 0 }, { x: H + 3 }, tail);
    KT([s.th, s.bh], { x: 0 }, { x: -H - 3 }, tail);
    KT([$("gt"), $("gb")], { x: 0 }, { x: H }, tail);
    K([$("gt"), $("gb")], { opacity: 0 }, { opacity: 1 }, 9.4, 1.4);
    [[10.4, .05], [11.8, .5], [13.8, 1], [15.8, 1.35], [17.8, .9], [19.8, .55], [21.8, .3], [23.8, .1]].reduce((a, b) => {
      K([$("gt"), $("gb")], { scaleX: a[1] }, { scaleX: b[1] }, a[0], b[0] - a[0]); return b; });
    K([$("gt"), $("gb")], { opacity: 1 }, { opacity: 0 }, 19.8, 4, "power1.in");

    // 4. the right side becomes the beam and sweeps left, revealing the bar
    const B0 = 22.3, BD = 25;
    const beamX0 = f => R * (1 - inOut3(Math.min(1, Math.max(0, (f - B0) / BD))));
    K([s.tv2, s.bv2], { opacity: 1 }, { opacity: 0 }, B0 - 0.5, 0.01);
    K($("beam"), { opacity: 0 }, { opacity: 1 }, B0 - 0.5, 0.01);
    K([$("beam"), $("beamN"), $("halo")], { x: R }, { x: 0 }, B0, BD, inOut3);
    K($("win"), { x: R }, { x: 0 }, B0, BD, inOut3);
    K($("bar"), { x: -R }, { x: 0 }, B0, BD, inOut3);
    K($("beam"), { opacity: 1 }, { opacity: 0 }, 35.8, 1.5);            // glow turns neutral
    K($("beamN"), { opacity: 0 }, { opacity: 1 }, 35.8, 1.5);
    K($("beamN"), { opacity: 1 }, { opacity: 0 }, 42.3, 2, "power1.in");
    K($("halo"), { opacity: 0 }, { opacity: 1 }, 35.3, 1);
    K($("halo"), { opacity: 1 }, { opacity: 0 }, 42.3, 4, "power1.in");
    // one-frame white bloom as the beam passes its top speed — intro only (the source's outro has none)
    tl.set($("flash"), { opacity: 1, x: beamX0(34.8) }, at(34.3));
    tl.set($("flash"), { opacity: 0 }, at(35.3));
    K($("wash"), { opacity: 0 }, { opacity: 1 }, B0, 2);
    K($("wash"), { opacity: 1 }, { opacity: 0 }, 38.8, 4, "power1.in");

    // name settles; letters land right->left behind the beam
    K($("name"), { x: -70 }, { x: 0 }, 36.3, 21.8, "power2.out");
    // letters animate in right->left on a fixed stagger; the ones the beam hasn't reached yet are still hidden
    // behind the bar window, so they appear crisp the moment it uncovers them (source: 1.52f per character)
    const nChars = q("namein").children.length;
    letters.forEach(ch => {
      const j = nChars - 1 - +ch.id.slice(ch.id.lastIndexOf("-c") + 2);
      K(ch, { opacity: 0, scaleX: 1.6, x: -40 }, { opacity: 1, scaleX: 1, x: 0 }, 30 + 1.52 * j, 6, "power2.out");
    });

    // 5. purple edge under the bar sweeps right, uncovering the white strip behind a lilac wash
    K($("edge"), { opacity: 0 }, { opacity: 1 }, 44.6, 1.2);
    K($("edge"), { scaleX: 1 }, { scaleX: 0.5 }, 60.8, 6, "power1.out");
    K($("edge"), { x: 0 }, { x: subW }, 42.6, 27, inOut3);
    K($("subwin"), { x: -subW }, { x: 0 }, 42.6, 27, inOut3);
    K($("subin"), { x: subW }, { x: 0 }, 42.6, 27, inOut3);
    K($("subwash"), { opacity: 0 }, { opacity: 1 }, 45.8, 1);
    [[45.8, .2], [50.8, .3], [52.8, .7], [55.8, 1], [57.8, .5], [59.8, .3], [61.8, .23], [63.8, .2], [65.8, .13], [67.8, 0]].reduce((a, b) => {
      K($("subwash"), { scaleX: a[1] }, { scaleX: b[1] }, a[0], b[0] - a[0]); return b; });
    K($("subtxt"), { x: 70 }, { x: 0 }, 54.1, 13, "power2.out");

    // 6. outro: the intro, time-reversed. `end` = when it finishes (mirror of T).
    if (opt.end != null && opt.outro !== false) {
      const E = Math.max(opt.end, T + 2 * INTRO);          // a window shorter than intro+outro would overlap them
      for (const r of rec) {
        tl.fromTo(r.target, { ...r.to }, { ...r.from, duration: r.dur, ease: reverseEase(r.ease), immediateRender: false },
          E - (r.t + r.dur - T));
      }
    }
  }

  window.NGLowerThird = { html, animate, INTRO };
})();
