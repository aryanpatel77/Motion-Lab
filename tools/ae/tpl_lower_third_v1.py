"""AE scene for `lower-third-nestgen-v1` (the first NestGen lower third, kept for old projects)."""
from .scene import Scene

F = 1 / 29.97
THEME = {
    "blue":   {"a": "#1257f0", "b": "#0a1c62", "edge": "#1f6bff"},
    "purple": {"a": "#6000b6", "b": "#430a6c", "edge": "#7a1fd8"},
}


def build(p):
    name = str(p.get("name", "Aban Aryan")).upper()
    title = str(p.get("title", "Head of Engineering")).upper()
    company = str(p.get("company", "") or "").upper()
    sub = title + (", " + company if company else "")
    th = THEME[p.get("theme", "blue")]
    start = float(p.get("start", 1.034))
    hold = float(p.get("hold", 5.0))
    outro = str(p.get("outro", "true")).lower() != "false"

    X, Y, BH, SUBT, SUBH = 64, 810, 82, 88, 50
    BW = max(520, int(len(name) * 26.5 + 132))          # same rule as the HTML (name + star space)
    SW = max(300, int(len(sub) * 12.4 + 40))
    end = start + hold + (0.9 if outro else 0)
    s = Scene(f"Lower Third — {name}", 1920, 1080, 29.97, end + 0.6, "#000000")
    s.note("Text layers are live — retype the name/title and the bar keeps its animation.")
    s.note("Starfield + LED dot texture from the HTML version are not reproduced; add a texture layer if you want them.")

    # --- name bar: gradient solid revealed right->left by an animated mask ---
    bar = s.solid("name bar", th["a"], BW, BH, X, Y)
    bar.effect("ramp", start=[X, 0], startColor=_rgb(th["a"]), end=[X + BW, 0], endColor=_rgb(th["b"]))
    bar.mask([[start + 25 * F, [BW, 0, 1, BH]], [start + 43 * F, [0, 0, BW, BH]]], ease="inout")
    bar.life(start)

    # --- name (live text), revealed by the same sweep, drifting +45px into place ---
    nm = s.text("name", name, X + 19, Y + 60, size=62, color="#ffffff",
                font="Libre Caslon Text", stretch=83)
    nm.key("position", [[start + 25 * F, [X + 19 - 45, Y + 60]], [start + 43 * F, [X + 19, Y + 60]]], ease="out")
    nm.mask([[start + 25 * F, [X + BW, Y, 1, BH]], [start + 43 * F, [X, Y, BW, BH]]], ease="inout")
    nm.life(start)

    # --- light trace: rect path + Trim Paths (head then tail), exactly the source's motion ---
    tr = s.rect_outline_trim("light trace", X - 2, Y - 1, BW + 38, BH + 2, stroke="#ffffff", stroke_w=4)
    tr.key("trimEnd", [[start, 0], [start + 14 * F, 100]], ease="inout")
    tr.key("trimStart", [[start + 9 * F, 0], [start + 23 * F, 96]], ease="out")
    tr.key("opacity", [[start + 25 * F, 100], [start + 25.5 * F, 0]], ease="hold")
    tr.effect("glow", radius=26, threshold=40, intensity=1.4)
    tr.life(start)

    # --- beam that sweeps the bar open ---
    beam = s.solid("beam", "#ffffff", 4, BH + 14, X, Y - 7)
    beam.key("position", [[start + 25 * F, [X + BW + 38, Y - 7]], [start + 43 * F, [X, Y - 7]]], ease="inout")
    beam.key("opacity", [[start + 25 * F, 100], [start + 40 * F, 100], [start + 43 * F, 0]], ease="in")
    beam.effect("glow", radius=30, threshold=35, intensity=1.6)
    beam.life(start + 25 * F)

    # --- title bar: white bar wipes left->right, text trails +80px, purple edge rides the front ---
    sb = s.solid("title bar", "#fdfdfd", SW, SUBH, X, Y + SUBT)
    sb.mask([[start + 51 * F, [0, 0, 1, SUBH]], [start + 65 * F, [0, 0, SW, SUBH]]], ease="out")
    sb.life(start + 51 * F)

    st = s.text("title", sub, X + 19, Y + SUBT + 33, size=25, color="#4b4b4b", font="Inter")
    st.key("position", [[start + 51 * F, [X + 19 + 80, Y + SUBT + 33]], [start + 65 * F, [X + 19, Y + SUBT + 33]]], ease="out")
    st.mask([[start + 51 * F, [X, Y + SUBT, 1, SUBH]], [start + 65 * F, [X, Y + SUBT, SW, SUBH]]], ease="out")
    st.life(start + 51 * F)

    edge = s.solid("edge", th["edge"], 5, SUBH, X, Y + SUBT)
    edge.key("position", [[start + 51 * F, [X, Y + SUBT]], [start + 65 * F, [X + SW, Y + SUBT]]], ease="out")
    edge.key("opacity", [[start + 44 * F, 0], [start + 45 * F, 100]], ease="hold")
    edge.effect("glow", radius=12, threshold=50, intensity=1)
    edge.life(start + 44 * F)

    if outro:                                            # reverse of the build
        o = start + hold
        for lay, key in ((sb, "mask"), (st, "mask")):
            pass
        sb.mask([[start + 51 * F, [0, 0, 1, SUBH]], [start + 65 * F, [0, 0, SW, SUBH]],
                 [o, [0, 0, SW, SUBH]], [o + 0.3, [0, 0, 1, SUBH]]], ease="inout")
        st.mask([[start + 51 * F, [X, Y + SUBT, 1, SUBH]], [start + 65 * F, [X, Y + SUBT, SW, SUBH]],
                 [o, [X, Y + SUBT, SW, SUBH]], [o + 0.3, [X, Y + SUBT, 1, SUBH]]], ease="inout")
        edge.key("position", [[start + 51 * F, [X, Y + SUBT]], [start + 65 * F, [X + SW, Y + SUBT]],
                              [o, [X + SW, Y + SUBT]], [o + 0.3, [X, Y + SUBT]]], ease="inout")
        bar.mask([[start + 25 * F, [BW, 0, 1, BH]], [start + 43 * F, [0, 0, BW, BH]],
                  [o + 0.34, [0, 0, BW, BH]], [o + 0.76, [0, 0, 1, BH]]], ease="inout")
        nm.mask([[start + 25 * F, [X + BW, Y, 1, BH]], [start + 43 * F, [X, Y, BW, BH]],
                 [o + 0.34, [X, Y, BW, BH]], [o + 0.76, [X, Y, 1, BH]]], ease="inout")
        beam.key("position", [[start + 25 * F, [X + BW + 38, Y - 7]], [start + 43 * F, [X, Y - 7]],
                              [o + 0.34, [X, Y - 7]], [o + 0.76, [X + BW, Y - 7]]], ease="inout")
        beam.key("opacity", [[start + 25 * F, 100], [start + 40 * F, 100], [start + 43 * F, 0],
                             [o + 0.33, 0], [o + 0.36, 100], [o + 0.86, 0]], ease="hold")
        for lay in (sb, st, edge, bar, nm, beam):
            lay.life(lay.d.get("in", start), o + 0.95)
    return s


def _rgb(h):
    h = h.lstrip("#")
    return [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
