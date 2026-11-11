#!/usr/bin/env python3
"""FIRST WORD: the ink on the line-up wall.

The doubts are drawn on the wall round the people: shouting mouths, a skull, the four doubts in quotation
marks. They pile up across the eight swaps of the opening, the cyan block deletes them, they come back
round Ray when he doubts again, and they un-draw when he gives way.

timing/ink.json lists every mark: which drawing from the sheet (clips/stills/ink_wall.png, a 5 by 4 grid),
where it sits (centre x, centre y, width, as fractions of the frame; rotation in degrees), the frame it
appears on and the frame it goes. The ink is multiplied onto the picture, so the wall's own light stays. It is
kept to the two sides of the frame, clear of whoever stands in the middle, so no matte is needed.

    layer(frame, W, H) -> an image to multiply onto that frame, or None when the wall is clean
"""
import json
import os

from PIL import Image, ImageChops, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
F_HAND = os.path.join(ROOT, "fonts", "Kalam-Bold.ttf")
INK = (22, 34, 66)
_spec = None
_sprites = {}
_cache = {}


def spec():
    global _spec
    if _spec is None:
        _spec = json.load(open(os.path.join(ROOT, "timing", "ink.json")))
    return _spec


def sprite(col, row):
    if (col, row) not in _sprites:
        s = spec()
        sheet = Image.open(os.path.join(ROOT, s["sheet"])).convert("RGB")
        xs, ys = s["grid"]["x"], s["grid"]["y"]
        w, h = sheet.size
        im = sheet.crop((int(xs[col] * w), int(ys[row] * h), int(xs[col + 1] * w), int(ys[row + 1] * h)))
        im = im.point(lambda v: 255 if v >= 232 else v)          # the paper goes to pure white: only ink multiplies
        _sprites[(col, row)] = im
    return _sprites[(col, row)]


def alive(f):
    """Indices of the marks and texts on the wall at frame f."""
    s = spec()
    out = []
    for i, m in enumerate(s["marks"] + s["texts"]):
        for a, b in m["on"]:
            if a <= f < b:
                out.append(i)
                break
    sw = s.get("sweep")
    if sw and sw["in"] <= f < sw["out"]:                          # the block runs right to left and deletes what it passes
        edge = sw["x0"] - sw["step"] * (f - sw["in"])
        out = [i for i in out if (s["marks"] + s["texts"])[i]["x"] < edge]
    return tuple(out)


def layer(f, W, H):
    key = (alive(f), W, H)
    if not key[0]:
        return None
    if key not in _cache:
        s = spec()
        items = s["marks"] + s["texts"]
        img = Image.new("RGB", (W, H), (255, 255, 255))
        for i in key[0]:
            m = items[i]
            if "sprite" in m:
                sp = sprite(*m["sprite"])
                w = max(8, int(m["w"] * W))
                sp = sp.resize((w, max(8, int(sp.size[1] * w / sp.size[0]))), Image.LANCZOS)
            else:
                font = ImageFont.truetype(F_HAND, max(8, int(m["size"] * H)))
                box = font.getbbox(m["text"])
                sp = Image.new("RGB", (box[2] + 12, box[3] + 12), (255, 255, 255))
                ImageDraw.Draw(sp).text((6, 4), m["text"], font=font, fill=INK)
            sp = sp.rotate(m.get("rot", 0), expand=True, fillcolor=(255, 255, 255), resample=Image.BICUBIC)
            x = int(m["x"] * W - (sp.size[0] / 2 if "sprite" in m else 0))
            y = int(m["y"] * H - sp.size[1] / 2)
            box = (max(0, x), max(0, y), min(W, x + sp.size[0]), min(H, y + sp.size[1]))
            if box[2] <= box[0] or box[3] <= box[1]:
                continue
            part = sp.crop((box[0] - x, box[1] - y, box[2] - x, box[3] - y))
            img.paste(ImageChops.multiply(img.crop(box), part), box)
        _cache[key] = img
    return _cache[key]
