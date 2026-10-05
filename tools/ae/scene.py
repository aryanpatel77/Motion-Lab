"""Scene graph for the After Effects exporter.

A template builder produces a Scene (comp + layers + keyframes + masks + effects); `runtime.jsx`
interprets it inside AE. Keeping the description declarative means every new template gets an AE
export by describing layers, not by writing ExtendScript.

Coordinates are top-left based like the HTML templates; the runtime sets anchor points to [0,0]
for solids/shapes so positions map 1:1.
"""
import json
import os

_METRICS = None


def metrics():
    """Per-character advance widths measured from the real fonts (tools/ae/measure.html)."""
    global _METRICS
    if _METRICS is None:
        f = os.path.join(os.path.dirname(os.path.abspath(__file__)), "metrics.json")
        _METRICS = json.load(open(f)) if os.path.exists(f) else {}
    return _METRICS


def text_width(text, size, font="Inter"):
    m = metrics().get(font) or metrics().get("Inter")
    if not m:
        return len(text) * size * 0.52
    adv, kern = m["adv"], m.get("kern", {})
    w = sum(adv.get(c, 0.55) for c in text) + sum(kern.get(text[i:i + 2], 0) for i in range(len(text) - 1))
    return w * size


def cap_height(size, font="Inter"):
    m = metrics().get(font) or metrics().get("Inter")
    return (m["cap"] if m else 0.72) * size


EASE = {"none": "linear", "in": "in", "out": "out", "inout": "inout", "hold": "hold"}


def rgb(hex_or_list):
    if isinstance(hex_or_list, (list, tuple)):
        return list(hex_or_list)
    h = hex_or_list.lstrip("#")
    return [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]


class Layer:
    def __init__(self, kind, name, **kw):
        self.d = {"kind": kind, "name": name, **kw}
        self.d.setdefault("props", {})

    def key(self, prop, keys, ease="inout"):
        """keys: [[time, value], ...]  value: number | [x,y] | string (sourceText)"""
        self.d["props"][prop] = {"keys": [[round(t, 4), v] for t, v in keys], "ease": EASE.get(ease, "inout")}
        return self

    def set(self, prop, value):
        self.d["props"][prop] = {"keys": [[0, value]], "ease": "hold"}
        return self

    def mask(self, rect_keys, ease="inout", invert=False):
        """rect_keys: [[time, [x, y, w, h]], ...] — animated rectangular mask (wipes/reveals)"""
        self.d["mask"] = {"keys": [[round(t, 4), r] for t, r in rect_keys], "ease": EASE.get(ease, "inout"), "invert": invert}
        return self

    def effect(self, name, **params):
        self.d.setdefault("effects", []).append({"name": name, "params": params})
        return self

    def life(self, start, end=None):
        self.d["in"] = round(start, 4)
        if end is not None:
            self.d["out"] = round(end, 4)
        return self

    def parent(self, name):
        self.d["parent"] = name
        return self


class Scene:
    def __init__(self, name, w, h, fps, duration, bg="#000000"):
        self.d = {"comp": {"name": name, "w": w, "h": h, "fps": fps, "duration": round(duration, 3), "bg": rgb(bg)},
                  "assets": [], "layers": [], "notes": []}

    # ---- layer factories (added bottom-up; AE draws the last added on top unless index is set) ----
    def solid(self, name, color, w, h, x=0, y=0):
        return self._add(Layer("solid", name, color=rgb(color), size=[w, h], pos=[x, y]))

    def text(self, name, value, x, y, size=48, color="#ffffff", font=None, italic=False,
             tracking=0, justify="left", stretch=100, leading=None):
        return self._add(Layer("text", name, text={"value": value, "size": size, "color": rgb(color),
                                                   "font": font, "italic": italic, "tracking": tracking,
                                                   "justify": justify, "stretch": stretch, "leading": leading},
                               pos=[x, y]))

    def rect(self, name, x, y, w, h, fill=None, stroke=None, stroke_w=0, radius=0):
        return self._add(Layer("shape", name, shape={"kind": "rect", "size": [w, h], "radius": radius,
                                                     "fill": rgb(fill) if fill else None,
                                                     "stroke": rgb(stroke) if stroke else None, "strokeW": stroke_w},
                               pos=[x, y]))

    def rect_outline_trim(self, name, x, y, w, h, stroke, stroke_w, radius=0):
        """A rectangle stroked path with Trim Paths — the light-trace primitive."""
        l = self.rect(name, x, y, w, h, stroke=stroke, stroke_w=stroke_w, radius=radius)
        l.d["shape"]["trim"] = True
        return l

    def grid(self, name, x, y, w, h, cell, square, color):
        """Square-pixel grid via shape repeaters (pixel rings, dot grids, dither).
        The square is always smaller than the cell, otherwise the copies touch and it renders as a slab."""
        square = min(square, cell - 4)
        return self._add(Layer("shape", name, shape={"kind": "grid", "size": [w, h], "cell": cell,
                                                     "square": square, "fill": rgb(color)}, pos=[x, y]))

    def footage(self, name, asset, x, y, w=None, h=None):
        return self._add(Layer("footage", name, asset=asset, pos=[x, y], size=[w, h] if w else None))

    def null(self, name, x=0, y=0):
        return self._add(Layer("null", name, pos=[x, y]))

    def asset(self, id_, path):
        self.d["assets"].append({"id": id_, "file": path})
        return id_

    def note(self, text):
        self.d["notes"].append(text)

    def _add(self, layer):
        self.d["layers"].append(layer.d)
        return layer

    def json(self):
        return json.dumps(self.d, separators=(",", ":"))
