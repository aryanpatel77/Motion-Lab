"""Generate the promo's generic stand-in icons as transparent PNGs for the AE export."""
import math
import os

from PIL import Image, ImageDraw

S = 256


def _img():
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    return im, ImageDraw.Draw(im)


def burst(c=(227, 118, 95, 255)):
    im, d = _img()
    for a in range(0, 180, 30):
        r = math.radians(a)
        dx, dy = math.cos(r) * 95, math.sin(r) * 95
        d.line([(128 - dx, 128 - dy), (128 + dx, 128 + dy)], fill=c, width=17)
    return im


def knot():
    im, d = _img()
    for a in (0, 60, 120):
        e = Image.new("RGBA", (S, S), (0, 0, 0, 0))
        ImageDraw.Draw(e).ellipse([32, 88, 224, 168], outline=(255, 255, 255, 255), width=15)
        im.alpha_composite(e.rotate(a, resample=Image.BICUBIC, center=(128, 128)))
    return im


def knot_dark():
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    for a in (0, 60, 120):
        e = Image.new("RGBA", (S, S), (0, 0, 0, 0))
        ImageDraw.Draw(e).ellipse([32, 88, 224, 168], outline=(20, 20, 20, 255), width=13)
        im.alpha_composite(e.rotate(a, resample=Image.BICUBIC, center=(128, 128)))
    return im


def infinity():
    im, d = _img()
    for cx in (92, 164):
        d.ellipse([cx - 52, 96, cx + 52, 160], outline=(28, 124, 244, 255), width=22)
    return im


def wave():
    im, d = _img()
    d.line([(36, 88), (72, 174), (103, 108), (134, 174), (165, 108), (196, 174), (222, 88)],
           fill=(255, 255, 255, 255), width=22, joint="curve")
    return im


def cube():
    im, d = _img()
    d.polygon([(128, 30), (215, 76), (128, 122), (41, 76)], fill=(214, 212, 209, 255))
    d.polygon([(215, 76), (215, 180), (128, 226), (128, 122)], fill=(156, 154, 151, 255))
    d.polygon([(41, 76), (128, 122), (128, 226), (41, 180)], fill=(111, 109, 106, 255))
    return im


def spark():
    im, d = _img()
    pts = []
    for i in range(4):
        a = math.radians(i * 90)
        pts.append((128 + math.cos(a) * 115, 128 + math.sin(a) * 115))
        a2 = math.radians(i * 90 + 45)
        pts.append((128 + math.cos(a2) * 34, 128 + math.sin(a2) * 34))
    d.polygon(pts, fill=(226, 110, 140, 255))
    return im


def dots():
    im, d = _img()
    ring = [(128, 56), (190, 92), (190, 164), (128, 200), (66, 164), (66, 92), (128, 128)]
    for i, (x, y) in enumerate(ring):
        d.ellipse([x - 28, y - 28, x + 28, y + 28], fill=(39, 195, 160, 255) if i % 2 else (63, 140, 246, 255))
    return im


def bot():
    im, d = _img()
    d.rounded_rectangle([46, 66, 210, 200], radius=46, fill=(232, 227, 222, 255))
    for x in (97, 159):
        d.ellipse([x - 18, 115, x + 18, 151], fill=(21, 17, 15, 255))
    d.rounded_rectangle([118, 30, 138, 70], radius=10, fill=(232, 227, 222, 255))
    return im


def branch():
    im, d = _img()
    c = (217, 86, 64, 255)
    d.ellipse([52, 30, 104, 82], outline=c, width=20)
    d.ellipse([52, 174, 104, 226], outline=c, width=20)
    d.ellipse([160, 60, 212, 112], outline=c, width=20)
    d.line([(78, 82), (78, 174)], fill=c, width=20)
    d.line([(186, 112), (186, 140), (78, 168)], fill=c, width=20, joint="curve")
    return im


def cursor():
    im, d = _img()
    d.polygon([(40, 24), (216, 106), (140, 126), (108, 214)], fill=(17, 17, 17, 255))
    return im


def slash():
    im, d = _img()
    d.ellipse([46, 46, 210, 210], outline=(20, 20, 20, 255), width=12)
    d.line([(60, 196), (196, 60)], fill=(20, 20, 20, 255), width=12)
    return im


def chevron():
    im, d = _img()
    for dy in (0, 74):
        d.line([(40, 56 + dy), (128, 128 + dy), (216, 56 + dy)], fill=(20, 20, 20, 255), width=22, joint="curve")
    return im


def person():
    im, d = _img()
    d.ellipse([96, 48, 160, 112], outline=(20, 20, 20, 255), width=14)
    d.arc([54, 118, 202, 250], 180, 360, fill=(20, 20, 20, 255), width=14)
    return im


def layers():
    im, d = _img()
    d.polygon([(128, 40), (224, 92), (128, 144), (32, 92)], outline=(20, 20, 20, 255), width=12)
    d.line([(32, 140), (128, 192), (224, 140)], fill=(20, 20, 20, 255), width=12, joint="curve")
    return im


def orbit():
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    for a in (0, 60, 120):
        e = Image.new("RGBA", (S, S), (0, 0, 0, 0))
        ImageDraw.Draw(e).ellipse([28, 96, 228, 160], outline=(20, 20, 20, 60), width=4)
        im.alpha_composite(e.rotate(a, resample=Image.BICUBIC, center=(128, 128)))
    ImageDraw.Draw(im).ellipse([110, 110, 146, 146], fill=(20, 20, 20, 255))
    rnd = [(0.2, 0.35), (0.75, 0.2), (0.9, 0.6), (0.6, 0.85), (0.25, 0.8), (0.08, 0.55)]
    for fx, fy in rnd:
        x, y = 30 + fx * 196, 60 + fy * 136
        ImageDraw.Draw(im).ellipse([x - 5, y - 5, x + 5, y + 5], fill=(20, 20, 20, 220))
    return im


def sticker():
    im, d = _img()
    d.polygon([(24, 60), (168, 60), (216, 108), (216, 188), (72, 188), (24, 140)],
              outline=(20, 20, 20, 255), width=12)
    d.polygon([(196, 20), (208, 50), (238, 62), (208, 74), (196, 104), (184, 74), (154, 62), (184, 50)],
              fill=(20, 20, 20, 255))
    return im


def grid_png(w=1920, h=1080, cell=177, color=(240, 240, 240, 255)):
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for x in range(-1, w, cell):
        d.line([(x, 0), (x, h)], fill=color, width=1)
    for y in range(43, h, cell):
        d.line([(0, y), (w, y)], fill=color, width=1)
    return im


def glow(color=(110, 26, 16), w=1024, h=512):
    """Soft radial glow baked into a PNG — AE effects can fail; a PNG cannot."""
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    px = im.load()
    cx, cy = w / 2, h / 2
    for y in range(h):
        for x in range(0, w, 2):
            d = ((x - cx) / cx) ** 2 + ((y - cy) / cy) ** 2
            a = max(0.0, 1.0 - d) ** 1.8
            v = (color[0], color[1], color[2], int(a * 235))
            px[x, y] = v
            if x + 1 < w:
                px[x + 1, y] = v
    return im


ICONS = {"burst": burst, "knot": knot, "inf": infinity, "wave": wave, "cube": cube,
         "spark": spark, "dots": dots, "bot": bot, "branch": branch, "cursor": cursor,
         "slash": slash, "chevron": chevron, "person": person, "layers": layers,
         "orbit": orbit, "sticker": sticker, "knot_dark": knot_dark}


GLOWS = {"glow-red": (110, 26, 16), "glow-deep": (90, 20, 16), "glow-warm": (243, 174, 155)}


def write_all(outdir):
    os.makedirs(outdir, exist_ok=True)
    made = {}
    for name, fn in ICONS.items():
        p = os.path.join(outdir, f"{name}.png")
        fn().save(p)
        made[name] = os.path.basename(p)
    grid_png().save(os.path.join(outdir, "grid.png"))
    made["grid"] = "grid.png"
    for name, c in GLOWS.items():
        p = os.path.join(outdir, f"{name}.png")
        glow(c).save(p)
        made[name] = os.path.basename(p)
    return made
