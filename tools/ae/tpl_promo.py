"""AE scene for `promo-kinetic-20s`.

Same beat table as the HTML template (source frames / 24). AE idioms used:
  word builds   -> one text layer per word, coral 'enter' copy crossfading to the settled copy
  scramble/typing -> a single text layer with HOLD keyframes on Source Text
  light/pixel grids -> shape layers with two Repeaters (columns x rows)
  orbit tiles   -> position keyframes baked from the positions measured off the source
"""
from .scene import Scene, text_width

F = 1 / 24
CREAM, INK, CORAL, CORAL_T, DARK = "#fcf8ed", "#1a1714", "#d95640", "#c9604f", "#0e0d09"
SANS, SERIF, MONO = "Inter", "Instrument Serif", "JetBrains Mono"
W, H = 1920, 1080


def _w(text, size, serif=False):
    """real advance width, measured from the shipped fonts (tools/ae/metrics.json)"""
    return text_width(text, size, "Instrument Serif" if serif else "Inter")


def _line_x(words, size, gap, serif=False):
    total = sum(_w(t, size, serif) for t in words) + gap * (len(words) - 1)
    x = (W - total) / 2
    out = []
    for t in words:
        out.append(x)
        x += _w(t, size, serif) + gap
    return out


def word(s, wid, text, x, y, size, t_in, t_settle, dy=0.0, serif=False, stay_coral=False, ink=INK, out=None):
    """A word that lands coral + off-baseline and settles to `ink` (two crossfading text layers)."""
    t_settle = max(t_in + 1 / 24, t_settle - 2 / 24)
    a = s.text(wid + " (enter)", text, x, y + dy * size, size=size, color=CORAL_T, font=SERIF if serif else SANS, italic=serif)
    a.key("position", [[t_in, [x, y + dy * size]], [t_settle, [x, y]]], ease="out")
    a.life(t_in, out)
    if stay_coral:
        return a
    a.key("opacity", [[t_settle, 100], [t_settle + 0.06, 0]], ease="hold")
    b = s.text(wid, text, x, y, size=size, color=ink, font=SERIF if serif else SANS, italic=serif)
    b.key("opacity", [[t_settle, 0], [t_settle + 0.02, 100]], ease="hold")
    b.life(t_settle, out)
    return b


def pix_ring(s, name, ix, iy, iw, ih, th, color, t_in, t_out, cell=27, square=17):
    for tag, (x, y, w, h) in {
        "top": (ix - th, iy - th, iw + 2 * th, th), "bottom": (ix - th, iy + ih, iw + 2 * th, th),
        "left": (ix - th, iy, th, ih), "right": (ix + iw, iy, th, ih)}.items():
        g = s.grid(f"{name} {tag}", x, y, w, h, cell, square, color)
        g.life(t_in, t_out)


def build(p, assets):
    dur = 20.0
    s = Scene("Kinetic promo (20s)", W, H, 24, dur, DARK)
    s.note("Copy lives on text layers — retype any of them; motion is on transforms, not on the text.")
    s.note("Scramble + wordmark typing use HOLD keyframes on Source Text (open the layer's Text > Source Text).")
    s.note("Pixel grids are shape Repeaters: change Copies/Position to resize the pattern.")
    s.note("Particles, dither and starfields are simplified; the orbit tiles use baked position keys.")
    for k, f in assets.items():
        s.asset(k, f"assets/{f}")

    # ---------------- scene 1: "Engineers are shipping everyday" ----------------
    s.solid("s1 bg", CREAM, W, H, 0, 0).life(0, 44 * F)
    dith = s.grid("s1 dither", 1180, 0, 740, 430, 48, 26, "#f0b7a8")
    dith.key("opacity", [[4 * F, 0], [8 * F, 55], [18 * F, 55], [28 * F, 0]], ease="inout").life(0, 44 * F)
    d2 = s.grid("s1 dither 2", 0, 640, 620, 440, 48, 26, "#f0b7a8")
    d2.key("opacity", [[5 * F, 0], [9 * F, 45], [18 * F, 45], [28 * F, 0]], ease="inout").life(0, 44 * F)
    words1 = ["Engineers", "are", "shipping", "everyday"]
    xs = _line_x(words1, 46, 14)
    times = [(3, 5, 0.0), (13, 17, 0.45), (17, 20, 0.2), (19, 27, 0.35)]
    for i, (t_in, t_set, dy) in enumerate(times):
        word(s, f"s1 {words1[i]}", words1[i], xs[i], 560, 46, t_in * F, t_set * F, dy,
             serif=(i == 3), out=44 * F)
    for i, (x, y) in enumerate([(300, 300), (1500, 250), (1700, 700), (380, 780), (900, 200), (1250, 860)]):
        px = s.solid(f"s1 px{i}", CORAL, 13, 13 if i % 3 else 26, x, y)
        px.key("opacity", [[(5 + i * 2) * F, 0], [(6 + i * 2) * F, 100], [(20 + i * 3) * F, 100],
                           [(21 + i * 3) * F, 0], [(26 + i * 2) * F, 100]], ease="hold").life(0, 44 * F)

    # ---------------- scene 2: "with AI" + orbiting tiles ----------------
    s.solid("s2 bg", DARK, W, H, 0, 0).life(44 * F, 109 * F)
    if "glow-red" in assets:
        s.footage("s2 glow", "glow-red", 160, 620, 1600, 700).set("opacity", 70).life(44 * F, 109 * F)
    T = [56 * F, 68 * F, 80 * F, 92 * F, 104 * F, 108 * F]
    tiles = [
        ("wave", 240, [(.045, .575), (.14, .48), (.21, .41), (.315, .33), (.486, .20), (.62, .13)], 46),
        ("burst", 348, [(.69, .645), (.535, .75), (.444, .80), (.324, .84), (.15, .91), (.04, .91)], 46),
        ("knot", 336, [(.946, .43), (.856, .53), (.787, .59), (.685, .68), (.51, .80), (.38, .88)], 48),
        ("inf", 204, [(.40, .36), (.465, .25), (.555, .20), (.676, .16), (.85, .09), (.97, .05)], 52),
        ("cube", 288, [(.30, .97), (.195, .87), (.12, .88), (.02, .95), (-.1, 1.0), (-.14, 1.0)], 50),
        ("bot", 252, [(.02, .86), (-.02, .7), (-.08, .6), (-.16, .5), (-.25, .4), (-.3, .36)], 48),
        ("dots", 264, [(-.12, .8), (-.06, .72), (.015, .63), (.036, .58), (.13, .44), (.23, .34)], 66),
        ("spark", 300, [(1.1, .3), (1.06, .36), (1.02, .4), (.967, .43), (.87, .57), (.78, .67)], 82),
    ]
    for ic, sz, pts, born in tiles:
        px = [(x * W - sz / 2, y * H - sz / 2) for x, y in pts]
        # keep only the measured points after this tile is born, and fly it in from slightly further out
        kept = [(T[i], px[i]) for i in range(len(T)) if T[i] > born * F]
        if not kept:
            kept = [(T[-1], px[-1])]
        f0 = kept[0][1]
        entry = [f0[0] + (f0[0] + sz / 2 - W / 2) * 0.18, f0[1] + (f0[1] + sz / 2 - H / 2) * 0.18]
        plate = s.rect(f"s2 {ic} tile", entry[0], entry[1], sz, sz, fill="#171311", stroke=CORAL, stroke_w=2, radius=sz * 0.22)
        keys = [[born * F, entry]] + [[t, list(v)] for t, v in kept]
        plate.key("position", keys, ease="inout").life(born * F, 109 * F)
        if ic in assets:
            icon = s.footage(f"s2 {ic} icon", ic, px[0][0] + sz * 0.24, px[0][1] + sz * 0.24, int(sz * 0.52), int(sz * 0.52))
            icon.key("position", [[t, [v[0] + sz * 0.24, v[1] + sz * 0.24]] for t, v in keys], ease="inout")
            icon.life(born * F, 109 * F)
    gap_w, gap_a = _w("with", 44), _w("AI", 44)
    wx = W / 2 - (gap_w + 14 + gap_a) / 2
    wa = s.text("s2 with", "with", wx, 548, size=44, color="#f4efe6", font=SANS)
    wa.key("position", [[104 * F, [wx, 548]], [108 * F, [wx, 530]]], ease="in").life(44 * F, 109 * F)
    ax = wx + gap_w + 14
    ai = s.text("s2 AI", "AI", ax, 548, size=44, color=CORAL_T, font=SANS)
    ai.key("position", [[104 * F, [ax, 548]], [108 * F, [ax, 574]]], ease="in").life(46 * F, 109 * F)

    # ---------------- scene 3: scramble -> sentences -> Meet ----------------
    s.solid("s3 bg", CREAM, W, H, 0, 0).life(109 * F, 257 * F)
    sx = W / 2 - _w("&*[]#<>", 72) / 2
    scram = s.text("s3 scramble A", "&*[]#<>", sx - 150, 500, size=72, color=CORAL_T, font=SANS)
    scram.key("sourceText", [[(109 + i * 2) * F, t] for i, t in enumerate(
        ["&*[]#<>", "&&[]*#<>", "&&<>*&<>", "[]&<>&#*", "*[]<>& *#", "<>** & *&", "<>#[] *"])], ease="hold")
    scram.key("position", [[109 * F, [sx - 150, 500]], [121 * F, [sx + 150, 500]]], ease="inout").life(109 * F, 122 * F)
    scram2 = s.text("s3 scramble B", "[]&&*#<>", sx + 150, 596, size=72, color=CORAL_T, font=SANS)
    scram2.key("sourceText", [[(109 + i * 2) * F, t] for i, t in enumerate(
        ["[]&&*#<>", "[]##*&<>", "<>*#&#<>", "<>*&&*<>", "<> &#& **", "* &*[] *#", "#&** &&"])], ease="hold")
    scram2.key("position", [[109 * F, [sx + 150, 596]], [121 * F, [sx - 150, 596]]], ease="inout").life(109 * F, 122 * F)

    sent = ["But", "hiring", "hasn't", "caught", "up", "yet."]
    xs = _line_x(sent, 50, 15)
    for i, (t_in, t_set, dy) in enumerate([(122, 129, .35), (124, 129, .2), (126, 131, .15),
                                           (124, 131, -.45), (124, 130, -.15), (122, 130, -.3)]):
        out = {0: 145, 1: 157, 2: 151, 3: 147, 4: 153, 5: 149}[i] * F
        word(s, f"s3 {sent[i]}", sent[i], xs[i], 540, 50, t_in * F, t_set * F, dy, out=out)

    trad = ["Traditional", "technical", "interviews"]
    xs = _line_x(trad, 50, 15)
    for i, (t_in, t_set) in enumerate([(159, 163), (163, 167), (165, 171)]):
        word(s, f"s3 {trad[i]}", trad[i], xs[i], 540, 50, t_in * F, t_set * F, out=179 * F)
    for i, (x, y, ch) in enumerate([(430, 380, "}"), (1450, 360, "*"), (520, 700, "\\"), (1350, 690, "}"),
                                    (700, 300, "*"), (1200, 780, "{")]):
        pc = s.text(f"s3 particle {i}", ch, x, y, size=44, color=[INK, CORAL_T, "#e2cf3a"][i % 3], font=SANS)
        pc.key("position", [[159 * F, [x, y]], [201 * F, [x + (x - 960) * .25, y + (y - 540) * .25]]], ease="none")
        pc.key("opacity", [[159 * F, 0], [161 * F, 100], [196 * F, 100], [201 * F, 0]], ease="inout").life(159 * F, 201 * F)

    dsh = ["<", "don't", "show", "how", ">"]
    xs = _line_x(dsh, 50, 40)
    for i, (t_in, t_set) in enumerate([(179, 179), (179, 183), (182, 186), (186, 190), (179, 179)]):
        lay = word(s, f"s3 {dsh[i]}", dsh[i], xs[i], 540, 50, t_in * F, t_set * F, out=201 * F)
        if i in (0, 4):                                    # brackets drift apart
            d = -60 if i == 0 else 60
            lay.key("position", [[179 * F, [xs[i], 540]], [201 * F, [xs[i] + d, 540]]], ease="out")

    s.grid("s3 dot grid", 10, 10, W, H, 44, 21, "#f1ebe1").key(
        "opacity", [[201 * F, 0], [204 * F, 100], [241 * F, 100]], ease="out").life(201 * F, 242 * F)
    eng = ["engineers", "actually", "work", "today"]
    xs = _line_x(eng, 50, 26)
    for i, (t_in, t_set, dy) in enumerate([(201, 204, .2), (201, 205, .2), (204, 208, .2), (206, 210, .25)]):
        lay = word(s, f"s3 {eng[i]}", eng[i], xs[i], 540, 50, t_in * F, t_set * F, dy,
                   serif=(i == 1), stay_coral=(i == 1), out=242 * F)
        off = (i - 1.5) * 34                                # words spread apart as the scene holds
        lay.key("position", [[214 * F, [xs[i], 540]], [236 * F, [xs[i] + off, 540]]], ease="inout")
    pix_ring(s, "s3 ring 1", 640, 490, 640, 100, 54, CORAL, 235 * F, 237 * F)
    pix_ring(s, "s3 ring 2", 560, 420, 800, 240, 150, CORAL, 237 * F, 239 * F)
    pix_ring(s, "s3 ring 3", 400, 300, 1130, 480, 300, CORAL, 239 * F, 241 * F)
    pix_ring(s, "s3 ring 4", 330, 330, 1260, 420, 700, CORAL, 241 * F, 242 * F)

    s.solid("s4 bg", CREAM, W, H, 0, 0).life(242 * F, 257 * F)
    meet = s.text("s4 Meet", "Meet", 880, 580, size=104, color=INK, font=SERIF, italic=True)
    meet.key("opacity", [[242 * F, 100], [256 * F, 100], [256.5 * F, 0]], ease="hold").life(242 * F, 257 * F)
    for tag, (bx, by, d) in {"TL": (.351 * W, .33 * H, -.089 * W), "BR": (.658 * W - 236, .67 * H - 288, .081 * W)}.items():
        br = s.rect(f"s4 bracket {tag}", bx, by, 236, 58 if tag == "TL" else 236, fill=CORAL)
        br.key("position", [[242 * F, [bx, by]], [254 * F, [bx + d, by]]], ease="out").life(242 * F, 257 * F)
        arm = s.rect(f"s4 bracket {tag} arm", bx if tag == "TL" else bx + 178, by, 58, 288, fill=CORAL)
        arm.key("position", [[242 * F, [arm.d["pos"][0], by]], [254 * F, [arm.d["pos"][0] + d, by]]], ease="out").life(242 * F, 257 * F)

    # ---------------- scene 5: logo + "See who's engineering" ----------------
    s.solid("s5 bg", DARK, W, H, 0, 0).life(257 * F, 305 * F)
    if "glow-deep" in assets:
        g1 = s.footage("s5 glow", "glow-deep", 700, 480, 1500, 800)
        g1.set("opacity", 75)
        g1.key("position", [[257 * F, [700, 480]], [304 * F, [420, 360]]], ease="inout").life(257 * F, 305 * F)
    mark_x = W / 2 - (84 + 26 + _w("outship", 104)) / 2
    mark_a = s.rect("s5 mark back", mark_x, 496, 56, 70, fill=None, stroke="#ffffff", stroke_w=13).life(257 * F, 305 * F)
    mark_b = s.rect("s5 mark front", mark_x + 30, 526, 54, 68, fill="#ffffff").life(259 * F, 305 * F)
    wm = s.text("s5 wordmark", "outship", mark_x + 110, 588, size=104, color="#ffffff", font=SANS)
    wm.key("sourceText", [[259 * F, "ou"], [261 * F, "outs"], [263 * F, "outshi"], [265 * F, "outship"]], ease="hold")
    wm.key("opacity", [[259 * F, 100], [283 * F, 100], [284 * F, 0]], ease="hold").life(259 * F, 305 * F)
    for lay in (mark_a, mark_b):
        lay.key("opacity", [[lay.d.get("in", 257 * F), 100], [283 * F, 100], [284 * F, 0]], ease="hold")
    see = ["See", "who's", "engineering"]
    xs = _line_x(see, 72, 20)
    for i, (t_in, t_set) in enumerate([(285, 289), (287, 289), (287, 291)]):
        word(s, f"s5 {see[i]}", see[i], xs[i], 540, 72, t_in * F, t_set * F,
             serif=(i == 2), ink="#f4efe6", out=305 * F)

    # ---------------- scene 6: card list ----------------
    s.solid("s6 bg", "#e9836f", W, H, 0, 0).life(305 * F, 342 * F)
    if "glow-warm" in assets:
        s.footage("s6 bg 2", "glow-warm", 200, -100, 1700, 1300).set("opacity", 45).life(305 * F, 342 * F)
    cards = [("Memoized list filter to kill avoidable re-renders", "Full-Stack Execution"),
             ("Added Redis cache + invalidation on order write paths", "Full-Stack Execution"),
             ("Pushed back on a hallucinated Pydantic validator", "Agent Communication"),
             ("Added timeout on outbound HTTP the agent missed", "Verification & Shipping"),
             ("Used plan mode before touching the auth flow", "Architectural Research"),
             ("Cleaned dead branches the agent left behind", "Codebase Orientation"),
             ("Caught N+1 query the agent left unbatched", "Verification & Shipping"),
             ("Stopped the agent mid-edit when it duplicated existing logic", "Agent Communication")]
    scroll = s.null("s6 list", 0, 0)
    scroll.key("position", [[305 * F, [0, 0]], [314 * F, [0, -232]], [326 * F, [0, -464]],
                            [336 * F, [0, -696]], [338 * F, [0, -928]], [341 * F, [0, -1160]]], ease="out")
    scroll.life(305 * F, 342 * F)
    for i, (title, cat) in enumerate(cards):
        y = 60 + i * 232
        c = s.rect(f"s6 card {i+1}", 420, y, 1080, 176, fill="#fbf6ee", radius=20).parent("s6 list")
        c.key("position", [[325 * F, [420, y]], [341 * F, [420 + i * 44, y]]], ease="in").life(305 * F, 342 * F)
        s.text(f"s6 card {i+1} title", title, 476, y + 78, size=33, color="#2a2522", font=SANS).parent(f"s6 card {i+1}").life(305 * F, 342 * F)
        s.text(f"s6 card {i+1} cat", cat, 476, y + 120, size=24, color="#a79e94", font=SANS).parent(f"s6 card {i+1}").life(305 * F, 342 * F)

    # ---------------- scene 7: "and who's just vibe-coding" + terminal ----------------
    s.solid("s7 bg", DARK, W, H, 0, 0).life(342 * F, 407 * F)
    vibe = ["and", "who's", "just", "vibe-coding"]
    xs = _line_x(vibe, 74, 22)
    for i, (t_in, t_set) in enumerate([(342, 346), (344, 348), (344, 348), (346, 350)]):
        word(s, f"s7 {vibe[i]}", vibe[i], xs[i], 540, 74, t_in * F, t_set * F,
             serif=(i == 3), ink="#f4efe6", out=362 * F)
    term = s.rect("s7 terminal", 580, 200, 760, 780, fill="#15110f", stroke=CORAL, stroke_w=2, radius=16)
    term.key("opacity", [[362 * F, 0], [364 * F, 100]], ease="out").life(362 * F, 407 * F)
    body = "\n".join(["● Read (api/routes.ts)", "● Read (db/schema.sql)", "● Update (db/migrations/005_indexes.sql)",
                      "  Added 12 lines, removed 3 lines", "Added indexes on the three hottest query paths.", "",
                      "> [Pasted text #1 +203 lines] this is failing in prod", "✻ Thought",
                      "● Read (services/order.ts)", "● Update (services/order.ts)",
                      "Patched the null branch in the order service.", "", "> why is memory climbing", "✻ Thought",
                      "● Read (workers/consumer.ts)", "Closed a leaking subscription in the event consumer.", "",
                      "> [Pasted text #2 +91 lines] still broken", "● Update (services/cache.ts)",
                      "Stale cache key. Added TTL + invalidation on write."])
    tb = s.text("s7 terminal log", body, 614, 270, size=20, color="#cfc6bd", font=MONO, leading=30)
    tb.key("position", [[366 * F, [614, 270]], [406 * F, [614, -430]]], ease="none")
    tb.mask([[364 * F, [596, 246, 728, 700]]])          # clip the scroll to the window, like overflow:hidden
    tb.life(364 * F, 407 * F)
    for i, (txt, x, y, a, b) in enumerate([("memory climbing", 1370, 915, 366, 381), ("failing in prod", 1390, 820, 374, 389),
                                           ("still broken", 1360, 720, 380, 395), ("it's spiking", 1380, 620, 386, 400),
                                           ("timing out", 1350, 520, 390, 405), ("failing again", 300, 560, 394, 407),
                                           ("fix it", 330, 680, 398, 407), ("pool exhausted", 270, 800, 402, 407)]):
        tag = s.rect(f"s7 tag {i+1}", x, y, 26 + len(txt) * 18, 70, fill="#4a0a20", stroke="#a01744", stroke_w=2, radius=9)
        tag.key("position", [[a * F, [x, y]], [b * F, [x, y - 30]]], ease="none")
        tag.key("opacity", [[a * F, 0], [(a + 2) * F, 100], [(b - 1) * F, 100], [b * F, 0]], ease="inout").life(a * F, b * F)
        s.text(f"s7 tag {i+1} text", txt, x + 20, y + 46, size=30, color="#ff3d6e", font=MONO).parent(f"s7 tag {i+1}").life(a * F, b * F)

    # ---------------- scene 8: "Create [icon] a task" -> app window ----------------
    s.solid("s8 bg", CREAM, W, H, 0, 0).life(407 * F, dur)
    cw, aw, tilew = _w("Create", 62), _w("a task", 62), 310
    cx = W / 2 - (cw + 80 + tilew + 80 + aw) / 2
    s.text("s8 Create", "Create", cx, 560, size=62, color=INK, font=SANS).key(
        "opacity", [[407 * F, 100], [434 * F, 100], [436 * F, 0]], ease="inout").life(407 * F, 443 * F)
    s.text("s8 a task", "a task", cx + cw + 80 + tilew + 80, 560, size=62, color=INK, font=SANS).key(
        "opacity", [[407 * F, 100], [434 * F, 100], [436 * F, 0]], ease="inout").life(407 * F, 443 * F)
    tile = s.rect("s8 icon tile", 805, 385, 310, 310, fill="#ffffff", stroke="#f1d7cf", stroke_w=2, radius=72)
    tile.key("scale", [[424 * F, [100, 100]], [426 * F, [94, 94]], [431 * F, [155, 155]]], ease="out").life(407 * F, 443 * F)
    if "branch" in assets:
        s.footage("s8 icon", "branch", 865, 445, 186, 186).key(
            "scale", [[424 * F, [73, 73]], [426 * F, [69, 69]], [431 * F, [113, 113]]], ease="out").life(407 * F, 443 * F)
    if "cursor" in assets:
        cur = s.footage("s8 cursor", "cursor", 1400, 980, 50, 50)
        cur.key("position", [[407 * F, [1400, 980]], [420 * F, [1050, 620]], [426 * F, [1075, 660]]], ease="out")
        cur.life(407 * F, 443 * F)
    you = s.rect("s8 You pill", 1444, 1024, 96, 44, fill="#111111", radius=20)
    you.key("position", [[407 * F, [1444, 1024]], [420 * F, [1094, 664]], [426 * F, [1119, 704]]], ease="out").life(407 * F, 443 * F)
    s.text("s8 You", "You", 1462, 1054, size=28, color="#ffffff", font=SANS).parent("s8 You pill").life(407 * F, 443 * F)
    sheet = s.rect("s8 sheet", 260, 120, 1400, 840, fill="#fbf8f2", stroke="#e5ddd0", stroke_w=2, radius=22)
    sheet.key("opacity", [[431 * F, 0], [434 * F, 100]], ease="out")
    sheet.key("scale", [[431 * F, [80, 80]], [441 * F, [100, 100]]], ease="out").life(431 * F, 443 * F)

    win = s.rect("s8 window", 150, 60, 1620, 1150, fill="#fbf8f2", stroke="#e5ddd0", stroke_w=2, radius=22).life(443 * F, dur)
    s.rect("s8 window header", 150, 60, 1620, 84, fill="#16120f").life(443 * F, dur)
    pix_ring(s, "s8 ring coral", 600, 430, 720, 200, 110, CORAL, 443 * F, 447 * F, cell=38, square=30)
    pix_ring(s, "s8 ring lime", 380, 300, 1160, 460, 150, "#d8f23a", 447 * F, 449 * F, cell=38, square=30)
    s.text("s8 page title", "Voice-Powered Travel Search", 210, 230, size=34, color=INK, font=SANS).life(449 * F, dur)
    s.text("s8 page sub", "Build a voice-driven travel search application that lets users find listings by speaking naturally.",
           210, 285, size=20, color="#6f675f", font=SANS).life(449 * F, dur)
    s.rect("s8 page panel", 210, 320, 1500, 760, fill="#f1ece4", radius=14).life(449 * F, dur)
    shot = s.rect("s8 screenshot", 240, 500, 1440, 500, fill="#ffffff", radius=10).life(449 * F, dur)
    cover = s.rect("s8 screenshot cover", 240, 500, 1440, 500, fill="#e8836f", radius=10)
    cover.key("position", [[451 * F, [240, 500]], [465 * F, [1140, 500]]], ease="none")
    cover.key("opacity", [[451 * F, 100], [465 * F, 0]], ease="none").life(449 * F, 466 * F)
    cta = s.rect("s8 CTA", 1330, 74, 410, 56, fill="#ffffff", stroke="#d9d2c6", stroke_w=1.5, radius=18)
    cta.key("opacity", [[470 * F, 0], [472 * F, 100]], ease="out").life(466 * F, dur)
    s.text("s8 CTA text", "Give access to real coding agents", 1352, 112, size=26, color=INK, font=SANS).parent("s8 CTA").life(466 * F, dur)
    cam = s.null("s8 camera", 0, 0)
    cam.key("scale", [[443 * F, [90, 90]], [466 * F, [100, 100]], [475 * F, [230, 230]]], ease="inout")
    cam.key("position", [[443 * F, [96, 54]], [466 * F, [0, 0]], [475 * F, [-2753, 287]]], ease="inout").life(443 * F, dur)
    for lay in s.d["layers"]:                                # everything in the app scene rides the camera,
        if (lay["name"].startswith("s8 ") and lay["name"] not in ("s8 camera", "s8 bg")
                and lay.get("in", 0) >= 443 * F - 1e-3 and not lay.get("parent")):   # unless it already has a parent
            lay["parent"] = "s8 camera"
    return s
