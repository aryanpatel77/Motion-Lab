"""AE scene for `frontier-explainer-9s` — same beats as the HTML template (source frames / 24).

Structure: a pan null carries the pink label, wire, icons and captions; then a node diagram
(INSTRUCTION types on via Source Text hold keys); then a chat card slides in.
"""
from .scene import Scene, text_width

F = 1 / 24
INK, GREY, DARK = "#141414", "#f1f1f1", "#1e1e1e"
SANS, MONO = "Inter", "JetBrains Mono"
W, H = 1920, 1080
PAN = 13.7                      # px per frame, measured off the source


def _w(t, size):
    return text_width(t, size, SANS)


def build(p, assets):
    dur = 9.208
    accent = p.get("accent", "#ec79a2")
    label = p.get("label", "RLHF")
    line1 = p.get("line1", "The post ¶ training algorithm").split(" ")
    line2 = p.get("line2", "behind most frontier AI").split(" ")
    line3 = p.get("line3", "Instruction Following").split(" ")
    line4 = p.get("line4", "Chat")
    s = Scene("Frontier explainer (9s)", W, H, 24, dur, "#ffffff")
    s.note("Copy is on text layers; the pan null 'camera' carries the label, icons and captions.")
    s.note("INSTRUCTION types on with HOLD keys on Source Text — open that layer's Text > Source Text.")
    s.note("Icons, grid and orbit are PNGs in the _assets folder (generic stand-ins, not brand logos).")
    for k, f in assets.items():
        s.asset(k, f)

    s.solid("bg", "#ffffff", W, H, 0, 0)
    if "grid" in assets:
        s.footage("grid", "grid", 0, 0, W, H)

    # ---------- phase 1: pan group ----------
    cam = s.null("pan", 0, 0)
    cam.key("position", [[F, [0, 0]], [72 * F, [-PAN * 72, 0]], [96 * F, [-2600, 0]]], ease="none").life(0, 100 * F)

    s.solid("wire in", INK, 430, 3, -260, 470).parent("pan").life(0, 100 * F)
    s.solid("wire elbow", INK, 3, 92, 166, 380).parent("pan").life(0, 100 * F)
    s.rect("label chip", 528, 386, 372, 185, fill=accent).parent("pan").life(0, 100 * F)
    s.text("label text", label, 528 + (372 - _w(label, 84)) / 2, 386 + 120, size=84, color=INK, font=SANS) \
        .parent("pan").life(0, 100 * F)
    s.solid("wire out", INK, 210, 3, 900, 470).parent("pan").life(0, 100 * F)

    for i, key in enumerate(["knot_dark", "burst", "spark", "slash"]):
        if key not in assets:
            continue
        ic = s.footage(f"icon {key}", key, 1130 + i * 132, 424, 96, 96).parent("pan")
        ic.key("opacity", [[(17 + i * 7) * F, 0], [(22 + i * 7) * F, 100]], ease="out").life((17 + i * 7) * F, 100 * F)

    def caption(words, times, y, size, parent=None, life=(0, dur), name="cap", left=None):
        x = left if left is not None else (W - sum(_w(w, size) for w in words) - 0.3 * size * (len(words) - 1)) / 2
        for w_, t in zip(words, times):
            lay = s.text(f"{name} {w_}", w_, x, y, size=size, color=INK, font=SANS)
            if parent:
                lay.parent(parent)
            lay.key("opacity", [[t * F, 0], [(t + 4) * F, 100]], ease="out").life(t * F, life[1])
            x += _w(w_, size) + 0.3 * size

    caption(line1, [1, 3, 5, 9], 700, 104, "pan", (0, 24 * F), "l1", left=1056)
    caption(line2, [23, 33, 39, 45], 700, 104, "pan", (0, 100 * F), "l2", left=1056)

    # ---------- phase 2/3: node diagram ----------
    dia = s.null("diagram", 0, 0)
    dia.key("position", [[0, [0, 0]], [83 * F, [60, 0]], [114 * F, [0, 0]], [182 * F, [0, 0]],
                         [198 * F, [-2300, 0]]], ease="inout").life(84 * F, 192 * F)
    top = s.text("INSTRUCTION", p.get("node_top", "INSTRUCTION"), 560, 285, size=30, color=INK, font=MONO, tracking=180)
    word = p.get("node_top", "INSTRUCTION")
    top.key("sourceText", [[(88 + i * 1.4) * F, word[:i + 1]] for i in range(len(word))], ease="hold")
    top.parent("diagram").life(88 * F, 192 * F)
    if "chevron" in assets:
        ch = s.footage("chevron", "chevron", 640, 400, 60, 70).parent("diagram")
        ch.key("position", [[97 * F, [640, 392]], [110 * F, [640, 410]], [134 * F, [640, 392]], [158 * F, [640, 410]]], ease="inout")
        ch.key("opacity", [[97 * F, 0], [103 * F, 100]], ease="out").life(97 * F, 192 * F)
    hum = s.rect("human chip", 523, 449, 168, 56, fill=GREY, radius=9).parent("diagram")
    hum.key("opacity", [[92 * F, 0], [97 * F, 100]], ease="out").life(92 * F, 192 * F)
    if "person" in assets:
        s.footage("human icon", "person", 537, 463, 28, 28).parent("diagram").life(92 * F, 192 * F)
    s.text("human label", p.get("node_left", "Human"), 573, 489, size=26, color=INK, font=SANS) \
        .parent("diagram").life(92 * F, 192 * F)
    sq = s.rect("stack chip", 700, 449, 56, 56, fill=GREY, radius=9).parent("diagram")
    sq.key("opacity", [[101 * F, 0], [106 * F, 100]], ease="out").life(101 * F, 192 * F)
    if "layers" in assets:
        s.footage("stack icon", "layers", 713, 462, 30, 30).parent("diagram").life(101 * F, 192 * F)
    if "orbit" in assets:
        orb = s.footage("orbit", "orbit", 790, 362, 230, 230).parent("diagram")
        orb.key("opacity", [[106 * F, 0], [111 * F, 100]], ease="out")
        orb.key("rotation", [[106 * F, 0], [186 * F, 360]], ease="none").life(106 * F, 192 * F)
    pill = s.rect("response pill", 1112, 449, 224, 56, fill="#101010", radius=11).parent("diagram")
    pill.key("opacity", [[121 * F, 0], [127 * F, 100]], ease="out").life(121 * F, 192 * F)
    s.text("response label", p.get("node_right", "Response"), 1138, 489, size=30, color="#ffffff", font=SANS) \
        .parent("diagram").life(121 * F, 192 * F)
    caption(line3, [155, 163], 700, 92, "diagram", (0, 192 * F), "l3")

    # ---------- phase 4: chat card ----------
    chat = s.null("chat", 0, 0)
    chat.key("position", [[0, [0, 0]], [190 * F, [0, 0]], [190.5 * F, [-420, 0]], [199 * F, [0, 0]]],
             ease="out").life(191 * F, dur)
    card = s.rect("chat card", 314, 104, 1261, 660, fill="#ffffff", stroke="#ededed", stroke_w=2).parent("chat")
    card.key("opacity", [[191 * F, 0], [195 * F, 100]], ease="out").life(191 * F, dur)
    s.rect("chat bar", 314, 104, 1261, 66, fill=DARK).parent("chat").life(191 * F, dur)
    s.text("chat title", p.get("chat_title", "ChatGPT") + "  ▾", 336, 148, size=26, color="#ffffff", font=SANS) \
        .parent("chat").life(191 * F, dur)
    user = s.rect("user bubble", 950, 235, 560, 137, fill="#eef2fd", radius=22).parent("chat")
    user.key("opacity", [[194 * F, 0], [199 * F, 100]], ease="out").life(194 * F, dur)
    s.text("user text", p.get("chat_user", "Summarize this document in\nthree bullet points."),
           978, 285, size=34, color=INK, font=SANS, leading=53).parent("chat").life(194 * F, dur)
    bot = s.rect("reply bubble", 385, 460, 505, 140, fill="#f2f2f2", radius=22).parent("chat")
    bot.key("opacity", [[204 * F, 0], [209 * F, 100]], ease="out").life(204 * F, dur)
    s.text("reply text", p.get("chat_reply", "Sure. Here are Three key\npoints of the document:"),
           415, 510, size=34, color=INK, font=SANS, leading=53).parent("chat").life(204 * F, dur)

    lay = s.text("cap chat", line4, (W - _w(line4, 104) - 120) / 2, 880, size=104, color=INK, font=SANS)
    lay.key("opacity", [[199 * F, 0], [203 * F, 100]], ease="out").life(199 * F, dur)
    if "sticker" in assets:
        st = s.footage("chat sticker", "sticker", (W - _w(line4, 104) - 120) / 2 + _w(line4, 104) + 34, 806, 86, 86)
        st.key("opacity", [[209 * F, 0], [213 * F, 100]], ease="out").life(209 * F, dur)
    return s
