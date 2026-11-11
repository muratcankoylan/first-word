#!/usr/bin/env python3
"""FIRST WORD conform: builds the cut from the shot list.

Every shot is taken from clips/<ID>.mp4 (or .mov, .png, .jpg) when that file exists; otherwise it is drawn as a
placeholder card. On top go the on-screen type (timing/type.json) and the captions of the spoken lines
(timing/lines.json), with the grey guess running half a beat ahead of every line. With no clips at all, the
result is the animatic. As finished shots land in clips/, the same command becomes the edit.

    python3 tools/conform.py --out out/animatic_v001.mp4
    python3 tools/conform.py --stills 30,357,725 --out out/tmp/check.mp4     # also saves those frames as PNG

The typefaces are macOS system fonts standing in for the film's faces.
"""
import argparse
import json
import math
import os
import re
import subprocess
import sys
from functools import lru_cache

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageChops, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import inklayer  # noqa: E402
import light as LT  # noqa: E402


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FPS, BEAT, BAR = 24, 10, 40

# The film's typefaces, all under the SIL Open Font Licence (fonts/OFL-*.txt). Helvetica is only for the burn-in.
FONTS = os.path.join(ROOT, "fonts")
F_DIN = os.path.join(FONTS, "BarlowCondensed-Bold.ttf")               # captions and stamps
F_SERIF = os.path.join(FONTS, "LibreBaskerville-Variable.ttf")        # the sentence
F_SERIF_I = os.path.join(FONTS, "LibreBaskerville-Italic-Variable.ttf")   # doubts, questions, real quotes
F_BRUSH = os.path.join(FONTS, "KaushanScript-Regular.ttf")            # the title on the glass
F_TELE = os.path.join(FONTS, "CourierPrime-Bold.ttf")
F_MONO = os.path.join(FONTS, "IBMPlexMono-Regular.ttf")
F_HAND = os.path.join(FONTS, "Kalam-Regular.ttf")
F_UI = "/System/Library/Fonts/Helvetica.ttc"

WHITE = (244, 244, 240)
GREY = (138, 143, 152)
CYAN = (0, 229, 255)
INK = (22, 34, 66)
TINT = {"GEN": (27, 36, 48), "MACRO": (30, 44, 40), "ARCHIVE": (46, 41, 33), "CODE": (0, 0, 0),
        "INK": (233, 230, 222), "BLUE": (10, 30, 66), "WARM": (66, 45, 22), "WHITE": (240, 240, 236)}
CAP_PX, SERIF_CAP_PX = 34, 30
CAP_Y = 0.915

# shots whose whole picture is type on black: no placeholder text under it
CLEAN = {"A01", "C03", "D02", "D15", "D16", "D17", "D18", "E02", "G10", "G30", "G31", "I01"}
LINEUP = {"A02": "RAY", "A03": "AMARA", "A04": "DEV", "A05": "JUN", "A06": "OSEI", "A07": "PIP", "A08": "ROSA",
          "A09": "MARA", "A10": "MARA", "A12": "MARA", "D01": "JUN", "D04": "RAY", "E01": "RAY"}
CLOSE = {"A13": "MARA", "D05": "MARA", "E03": "MARA", "F04": "PIP"}
WARM_SHOTS = {"G33"}
INKED = {"A02", "A03", "A04", "A05", "A06", "A07", "A08", "A09", "A10", "A12", "D04", "E01"}   # shots whose wall carries ink

W = H = 0
MATTES = {}
LENS_R = 0.47     # radius of the round lens, as a fraction of the frame width
K = 1.0


# ---------------------------------------------------------------- type
@lru_cache(maxsize=None)
def font(path, px):
    return ImageFont.truetype(path, max(6, int(round(px * K))))


def width(text, path, px):
    return font(path, px).getlength(text)


@lru_cache(maxsize=8192)
def tile(text, path, px, color, oblique):
    f = font(path, px)
    asc, desc = f.getmetrics()
    w = int(f.getlength(text)) + 6
    h = asc + desc + 2
    im = Image.new("RGBA", (w + int(0.3 * h), h), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((3, asc), text, font=f, fill=tuple(color) + (255,), anchor="ls")
    if oblique:
        s = 0.2
        im = im.transform(im.size, Image.AFFINE, (1, s, -s * asc, 0, 1, 0), resample=Image.BICUBIC)
    return im, asc


def put(img, x, base, text, path, px, color, oblique=False):
    """Draw text with its left edge at x and its baseline at base. Returns the advance."""
    if text:
        im, asc = tile(text, path, px, tuple(color), oblique)
        img.paste(im, (int(round(x)) - 3, int(round(base)) - asc), im)
    return width(text, path, px)


def cap_height(path, px):
    l, t, r, b = font(path, px).getbbox("H", anchor="ls")
    return -t


def lum(c):
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def mix(a, b, t):
    return tuple(int(round(a[i] * (1 - t) + b[i] * t)) for i in range(3))


def wrap(text, path, px, maxw):
    out, line = [], ""
    for word in text.split():
        trial = (line + " " + word).strip()
        if width(trial, path, px) <= maxw:
            line = trial
        else:
            out.append(line)
            line = word
    if line:
        out.append(line)
    return out


# ---------------------------------------------------------------- placeholder cards
def shot_tint(s):
    pic, src = s["picture"], s["source"].replace("(3D)", "")
    parts = [p.strip() for p in re.split(r"\+|over", src)]
    first = parts[-1] if "over" in src else parts[0]
    if s["passage"] == "F" or s["id"] in WARM_SHOTS:
        return TINT["WARM"]
    if "seamless white" in pic or "White-out" in pic:
        return TINT["WHITE"]
    if "seamless black" in pic:
        return TINT["CODE"]
    if pic.startswith("Blue world") or s["passage"] == "H" or s["id"] == "G41":
        return TINT["BLUE"]
    return TINT.get(first, TINT["GEN"])


def card(s):
    bg = shot_tint(s)
    fg = WHITE if lum(bg) < 128 else INK
    img = Image.new("RGB", (W, H), bg)
    d = ImageDraw.Draw(img)
    if s["id"] in CLEAN:
        return img, bg
    if "ARCHIVE" in s["source"]:  # everything real carries scanlines, the cards too
        a = np.asarray(img).copy()
        step = max(2, int(round(4 * K)))
        a[::step] = (a[::step] * 0.55).astype(np.uint8)
        a[1::step] = (a[1::step] * 0.8).astype(np.uint8)
        img = Image.fromarray(a)
        d = ImageDraw.Draw(img)
    soft = mix(bg, fg, 0.16)
    name = LINEUP.get(s["id"]) or CLOSE.get(s["id"])
    if s["id"] in LINEUP:  # the locked line-up frame: only the person changes
        bowed = "bowed" in s["picture"]
        cx, r = W * 0.5, H * 0.115
        cy = H * (1.04 if name == "PIP" else (0.47 if bowed else 0.43))
        d.ellipse([cx - H * 0.36, H * 0.66 + (H * 0.5 if name == "PIP" else 0), cx + H * 0.36, H * 1.5], fill=soft)
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=soft)
    elif s["id"] in CLOSE:  # extreme close-up
        cx, cy = W * 0.5, H * 0.56
        d.ellipse([cx - H * 0.46, cy - H * 0.6, cx + H * 0.46, cy + H * 0.6], fill=soft)
        for ex in (-0.17, 0.17):
            d.ellipse([cx + H * ex - H * 0.045, cy - H * 0.13, cx + H * ex + H * 0.045, cy - H * 0.085], fill=mix(bg, fg, 0.4))
    if name:
        put(img, W * 0.5 - width(name, F_DIN, 40) / 2, H * 0.17, name, F_DIN, 40, mix(bg, fg, 0.7))
    x = W * 0.04
    put(img, x, H * 0.26, s["id"], F_DIN, 120, mix(bg, fg, 0.3))
    y = H * 0.33
    maxw = W * (0.29 if name else 0.60)
    for ln in wrap(s["picture"], F_UI, 17, maxw)[:9]:
        put(img, x, y, ln, F_UI, 17, mix(bg, fg, 0.62))
        y += 23 * K
    put(img, x, y + 12 * K, (s["source"] + "  ·  " + s["transition"]).upper(), F_DIN, 21, mix(bg, fg, 0.45))
    return img, bg


def fit(im):
    r = max(W / im.width, H / im.height)
    im = im.resize((int(round(im.width * r)), int(round(im.height * r))), Image.LANCZOS)
    x, y = (im.width - W) // 2, (im.height - H) // 2
    return im.crop((x, y, x + W, y + H))


def lens_matte():
    """The round lens of the blue world: black outside one circle, the same for every shot that carries it."""
    if "lens" not in MATTES:
        m = Image.new("L", (W * 2, H * 2), 0)
        r = LENS_R * W * 2
        ImageDraw.Draw(m).ellipse([W - r, H - r, W + r, H + r], fill=255)
        MATTES["lens"] = m.resize((W, H), Image.LANCZOS)
    return MATTES["lens"]


def best(path):
    """A generated clip at its best: the 1080p version of a draft (clips/final/) once its enhancement has finished
    and been recorded, else the draft itself. Framing is given in fractions of the frame, so nothing else changes."""
    d = os.path.join(ROOT, "clips", "drafts") + os.sep
    if path.startswith(d):
        name = os.path.splitext(path[len(d):])[0]
        rec = os.path.join(d, name + "_1080.json")
        fin = os.path.join(ROOT, "clips", "final", name + ".mp4")
        if os.path.exists(rec) and os.path.exists(fin):
            try:
                if json.load(open(rec)).get("status") == "SUCCEEDED":
                    return fin
            except ValueError:
                pass
    return path


def clip_frames(path, n, o=None):
    """Frames of a clip for one shot. o: in (seconds), zoom (a punch-in), dx and dy (the centre of the punch-in,
    as a fraction of the frame, 0 is the middle), speed (the picture played faster or slower), matte, fade_in,
    whiteout and blackout (frames), ramp ([end second, power]: a speed ramp from in to that second), wash (a still
    knocked back toward its paper), bg (the colour the type is set against), and place, lift and whip (see finish)."""
    o = o or {}
    path = best(path)
    if o.get("lead") or o.get("tail"):
        # a cut inside the shot: its first frames (lead) or its last (tail) come from another moment of the same
        # clip, {"in": seconds, "frames": n, "speed": 1}. The picture between them carries on from where it
        # would have been, so a mouth that was in sync stays in sync.
        skip = ("lead", "tail", "in", "speed", "ramp", "fade_in", "whiteout", "blackout", "black_in", "place", "patch", "lift", "whip")
        base = {k: v for k, v in o.items() if k not in skip}
        nl = int(o["lead"]["frames"]) if o.get("lead") else 0
        nt = int(o["tail"]["frames"]) if o.get("tail") else 0
        main = {k: v for k, v in o.items() if k not in ("lead", "tail", "place", "patch", "lift", "whip")}
        main["in"] = float(o.get("in", 0)) + nl / FPS * float(o.get("speed", 1.0))
        a = clip_frames(path, nl, dict(base, **{"in": o["lead"]["in"], "speed": o["lead"].get("speed", 1.0)})) if nl else []
        b = clip_frames(path, nt, dict(base, **{"in": o["tail"]["in"], "speed": o["tail"].get("speed", 1.0)})) if nt else []
        return finish(a + clip_frames(path, n - nl - nt, main) + b, {k: o[k] for k in ("place", "patch", "lift", "whip") if k in o})   # a push belongs to the middle part alone
    zoom, speed = float(o.get("zoom", 1.0)), float(o.get("speed", 1.0))
    if path.lower().endswith((".png", ".jpg", ".jpeg")):
        im = Image.open(path).convert("RGB")
        if zoom > 1.001:                      # the same punch-in a clip gets, on a still
            w, h = im.size[0] / zoom, im.size[1] / zoom
            cx = im.size[0] * (0.5 + float(o.get("dx", 0)))
            cy = im.size[1] * (0.5 + float(o.get("dy", 0)))
            x0 = min(im.size[0] - w, max(0, cx - w / 2))
            y0 = min(im.size[1] - h, max(0, cy - h / 2))
            im = im.crop((int(x0), int(y0), int(x0 + w), int(y0 + h)))
        im = fit(im)
        if o.get("wash"):                     # a drawing knocked back toward the paper, so a stamp can sit on it
            im = Image.blend(im, Image.new("RGB", im.size, tuple(o.get("bg", (244, 244, 240)))), float(o["wash"]))
        return finish([im] * n, o)
    sw, sh = int(round(W * zoom / 2)) * 2, int(round(H * zoom / 2)) * 2
    x = min(sw - W, max(0, int(round((sw - W) / 2 + float(o.get("dx", 0)) * sw))))
    y = min(sh - H, max(0, int(round((sh - H) / 2 + float(o.get("dy", 0)) * sh))))
    vf = "%sfps=%d,scale=%d:%d:force_original_aspect_ratio=increase,crop=%d:%d:%d:%d" % (
        "" if abs(speed - 1) < 0.005 else "setpts=PTS/%.4f," % speed, FPS, sw, sh, W, H, x, y)
    take = n
    if o.get("ramp"):                           # a speed ramp: read to the end point, then pick frames along a curve
        take = int(round((float(o["ramp"][0]) - float(o.get("in", 0))) * FPS)) + 1
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(o.get("in", 0)), "-i", path, "-frames:v", str(take), "-vf", vf,
                          "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
    size = W * H * 3
    frames = [Image.frombytes("RGB", (W, H), raw[i * size:(i + 1) * size]) for i in range(len(raw) // size)]
    if o.get("ramp") and frames:                # slow at first, then falling: frame k of n shows time (k/n) ** power
        power = float(o["ramp"][1])
        frames = [frames[min(len(frames) - 1, int(round((len(frames) - 1) * ((k + 1) / n) ** power)))] for k in range(n)]
    if o.get("matte") == "lens":
        black = Image.new("RGB", (W, H), (0, 0, 0))
        frames = [Image.composite(f, black, lens_matte()) for f in frames]
    while frames and len(frames) < n:
        frames.append(frames[-1])
    bo = int(o.get("blackout", 0))                                   # the last frames drop to near black: a light going out
    for k in range(min(bo, len(frames))):
        frames[len(frames) - bo + k] = Image.eval(frames[len(frames) - bo + k], lambda v: int(v * 0.12))
    wo = int(o.get("whiteout", 0))                                   # the last frames burn out to white
    for k in range(min(wo, len(frames))):
        i = len(frames) - wo + k
        frames[i] = Image.blend(frames[i], Image.new("RGB", (W, H), (255, 255, 255)), (k + 1) / wo)
    for k in range(min(int(o.get("fade_in", 0)), len(frames))):      # up from black over the first frames
        frames[k] = Image.eval(frames[k], lambda v, a=(k + 1) / (int(o["fade_in"]) + 1): int(v * a))
    for k in range(min(int(o.get("black_in", 0)), len(frames))):     # the shot arrives out of black: its first frames are black
        frames[k] = Image.new("RGB", (W, H), (0, 0, 0))
    return finish(frames, o)


def whip(frames, w):
    """A whip tilt through the sky: the camera is thrown upward, so the picture runs down the frame and smears,
    its top row carrying on above it (out: the last frames of a shot). The next shot is found by tilting back
    down out of its own sky: it starts low in the frame under a smear of its top row and rises into place
    (in: its first frames)."""
    def smear(im, shift, blur):
        a = np.asarray(im, np.float32)
        s = int(round(shift * H))
        if s > 0:
            a = np.concatenate([np.repeat(a[:1], s, axis=0), a[:H - s]], axis=0)
        n = int(round(blur * H))
        if n > 1:
            pad = np.concatenate([np.repeat(a[:1], n // 2, axis=0), a, np.repeat(a[-1:], n - n // 2, axis=0)], axis=0)
            cs = np.concatenate([np.zeros_like(pad[:1]), np.cumsum(pad, axis=0)], axis=0)
            a = (cs[n:n + H] - cs[:H]) / n
        return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))

    frames = list(frames)
    n = int(w.get("out", 0))
    for i in range(1, min(n, len(frames)) + 1):
        t = i / n
        k = len(frames) - n + i - 1
        frames[k] = smear(frames[k], 0.85 * t ** 2.2, 0.5 * t ** 1.5)
    n = int(w.get("in", 0))
    for i in range(min(n, len(frames))):
        t = 1 - (i + 1) / (n + 1)
        frames[i] = smear(frames[i], 0.6 * t ** 1.6, 0.45 * t)
    return frames


def finish(frames, o):
    """What a shot's picture gets after it is framed: place (the line-up), patch (the cursor patch on a jacket),
    lift (a dark shot's shadows opened, the highlights left alone), whip (a whip tilt in or out), rings (a ring
    across the water for each click of the whale), blink (a flare on a small light, two frames at a time), tint
    (a stray red turned cyan; the relay's spark kept cool) and push (a slow push in)."""
    if not frames:
        return frames
    if o.get("place"):
        frames = place(frames, o["place"])
    if o.get("patch"):
        frames = chest_patch(frames, o["patch"])
    if o.get("lift"):
        g = 1.0 / float(o["lift"])
        lut = [int(round(255 * (v / 255) ** g)) for v in range(256)] * 3
        frames = [f.point(lut) for f in frames]
    if o.get("whip"):
        frames = whip(frames, o["whip"])
    if o.get("rings"):                   # each click of the whale sends a ring across the water overhead
        r = o["rings"]
        ys, xs = np.mgrid[0:H, 0:W].astype(np.float32)
        out = []
        for k, f in enumerate(frames):
            a = np.asarray(f, np.float32)
            water = np.clip((a[:, :, 2] - a[:, :, 0] - 38) / 30, 0, 1) * np.clip((a[:, :, 2] - 95) / 40, 0, 1) * np.clip((0.50 * H - ys) / (0.08 * H), 0, 1)
            add = np.zeros((H, W), np.float32)
            for k0, cx, cy in r["clicks"]:
                age = k - k0
                if age < 0 or age > r.get("life", 18):
                    continue
                rad = (0.012 + r.get("speed", 0.021) * age) * W
                d = np.sqrt((xs - cx * W) ** 2 + ((ys - cy * H) / r.get("flat", 0.5)) ** 2)
                fade = (1 - age / r.get("life", 18)) ** 1.5
                add += fade * (np.exp(-((d - rad) / (3.2 * K)) ** 2) + 0.45 * np.exp(-((d - rad * 0.72) / (2.6 * K)) ** 2))
            if add.max() > 0:
                a = a + (add * water * r.get("gain", 0.85))[..., None] * np.array([70, 100, 110], np.float32)
                f = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
            out.append(f)
        frames = out
    if o.get("blink"):                   # a small light in a wide shot blinks: a flare on it for two frames at a time
        import cv2
        b = o["blink"]
        x0, y0, x1, y1 = [int(v * s) for v, s in zip(b["box"], (W, H, W, H))]
        out = []
        for k, f in enumerate(frames):
            age = min([k - k0 for k0 in b["at"] if 0 <= k - k0 < b.get("hold", 2)], default=None)
            if age is None:
                out.append(f)
                continue
            a = np.asarray(f, np.float32)
            m = np.zeros((H, W), np.float32)
            m[y0:y1, x0:x1] = ((a[y0:y1, x0:x1, 1] > 205) & (a[y0:y1, x0:x1, 2] > 205))
            if m.sum() < 3:
                out.append(f)
                continue
            glow = cv2.GaussianBlur(m, (0, 0), 9 * K) * 14 + cv2.GaussianBlur(m, (0, 0), 2.2 * K) * 2.5
            streak = cv2.GaussianBlur(m, (0, 0), sigmaX=30 * K, sigmaY=1.2 * K) * 10          # the streak a lens gives a point of light
            g = np.clip(glow + streak, 0, 1) * float(b.get("gain", 1.0)) * (1.0 if age == 0 else 0.55)
            out.append(Image.fromarray(np.clip(a + g[..., None] * np.array([90, 235, 255], np.float32), 0, 255).astype(np.uint8)))
        frames = out
    if o.get("tint") == "nored":         # red belongs to the wax pencil alone: a stray red wire or pot turns cyan
        import cv2
        out = []
        for f in frames:
            hsv = cv2.cvtColor(np.asarray(f), cv2.COLOR_RGB2HSV).astype(np.float32)
            hh, ss, vv = hsv[:, :, 0], hsv[:, :, 1], hsv[:, :, 2]
            red = np.clip((5.5 - np.minimum(hh, 180 - hh)) / 2.0, 0, 1) * np.clip((ss - 150) / 35.0, 0, 1) * np.clip((vv - 50) / 30.0, 0, 1)
            if o.get("tint_box"):                                     # only inside this part of the frame (lips are red too)
                bx0, by0, bx1, by1 = o["tint_box"]
                gy, gx = np.mgrid[0:H, 0:W].astype(np.float32)
                red = red * ((gx >= bx0 * W) & (gx <= bx1 * W) & (gy >= by0 * H) & (gy <= by1 * H))
            red = cv2.GaussianBlur(red, (0, 0), 0.8 * K)
            turned = hsv.copy()
            turned[:, :, 0] = 94
            turned[:, :, 1] = ss * 0.85
            rgb2 = cv2.cvtColor(np.clip(turned, 0, 255).astype(np.uint8), cv2.COLOR_HSV2RGB).astype(np.float32)
            a = np.asarray(f, np.float32)
            out.append(Image.fromarray(np.clip(a * (1 - red[..., None]) + rgb2 * red[..., None], 0, 255).astype(np.uint8)))
        frames = out
    if o.get("tint") == "spark":         # the relay's spark is the film's cyan, never warm
        out = []
        for f in frames:
            a = np.asarray(f, np.float32)
            lum = a.max(axis=2)
            warm = np.clip((a[:, :, 0] - a[:, :, 2] + 26) / 40, 0, 1) * np.clip((lum - 120) / 80, 0, 1)    # neutral white counts as warm too: the core goes cyan-white
            cool = np.stack([lum * 0.72, lum * 0.97, lum], axis=2)
            out.append(Image.fromarray(np.clip(a * (1 - warm[..., None]) + cool * warm[..., None], 0, 255).astype(np.uint8)))
        frames = out
    if o.get("push"):                    # a slow push in over the shot: [from, to] or [from, to, centre x, centre y]
        z0, z1 = float(o["push"][0]), float(o["push"][1])
        cx, cy = (float(o["push"][2]), float(o["push"][3])) if len(o["push"]) > 3 else (0.5, 0.5)
        out = []
        for k, f in enumerate(frames):
            t = k / max(1, len(frames) - 1)
            z = z0 + (z1 - z0) * (t * t * (3 - 2 * t))
            w, h = W / z, H / z
            x0 = min(W - w, max(0, cx * W - w / 2))
            y0 = min(H - h, max(0, cy * H - h / 2))
            out.append(f.resize((W, H), Image.LANCZOS, box=(x0, y0, x0 + w, y0 + h)))
        frames = out
    return frames


def chest_patch(frames, p):
    """The team's patch: a white block cursor sewn on the chest of the jacket. p gives where its middle is on the
    first frame (at, as fractions of the frame), how wide it is (w, a fraction of the frame's width; it is 1.8
    times as tall) and its tilt in degrees. The cloth round it is followed from frame to frame, so the patch
    moves with the wearer, and it takes the jacket's own light: bright where the cloth is lit, dim in shadow."""
    import cv2
    cx, cy = p["at"][0] * W, p["at"][1] * H
    pw = p.get("w", 0.021) * W
    ph = pw * 1.8
    tilt = math.radians(p.get("tilt", 0.0))
    grays = [cv2.cvtColor(np.asarray(f), cv2.COLOR_RGB2GRAY) for f in frames]
    a0 = np.asarray(frames[0], np.int16)
    cloth = ((a0[:, :, 2] > a0[:, :, 0] + 8) & (a0.mean(axis=2) < 125)).astype(np.uint8)        # the navy of the jacket
    bl, br, bu, bd = p.get("box", [0.13, 0.17, 0.20, 0.16])            # how much of the cloth round it is followed
    box = np.zeros((H, W), np.uint8)
    box[max(0, int(cy - bu * H)):int(cy + bd * H), max(0, int(cx - bl * W)):int(cx + br * W)] = 1
    pts = cv2.goodFeaturesToTrack(grays[0], 120, 0.004, 5, mask=cloth * box)
    T = np.eye(3)
    poses = [(cx, cy, 0.0, 1.0)]
    for k in range(1, len(frames)):
        if pts is not None and len(pts) >= 8:
            nxt, st, _ = cv2.calcOpticalFlowPyrLK(grays[k - 1], grays[k], pts, None, winSize=(25, 25), maxLevel=3)
            ok = st.ravel() == 1
            if ok.sum() >= 8:
                A, _ = cv2.estimateAffinePartial2D(pts[ok], nxt[ok], method=cv2.RANSAC, ransacReprojThreshold=1.5)
                if A is not None:
                    T = np.vstack([A, [0, 0, 1]]) @ T
                pts = nxt[ok].reshape(-1, 1, 2)
        if pts is None or len(pts) < 30:                              # top the points up where the cloth is now
            c = T @ np.array([cx, cy, 1.0])
            box[:] = 0
            box[max(0, int(c[1] - bu * H)):int(c[1] + bd * H), max(0, int(c[0] - bl * W)):int(c[0] + br * W)] = 1
            more = cv2.goodFeaturesToTrack(grays[k], 120, 0.004, 5, mask=cloth * box)
            pts = more if pts is None or more is None else np.concatenate([pts, more])
        c = T @ np.array([cx, cy, 1.0])
        poses.append((c[0], c[1], math.atan2(T[1, 0], T[0, 0]), math.hypot(T[0, 0], T[1, 0])))
    wall = np.concatenate([a0[int(0.03 * H):int(0.12 * H), int(0.05 * W):int(0.25 * W)].reshape(-1, 3),
                           a0[int(0.03 * H):int(0.12 * H), int(0.75 * W):int(0.95 * W)].reshape(-1, 3)]).astype(np.float32)
    white = np.clip(np.median(wall, axis=0) * 1.05, 120, 238)         # white cloth under this light: about the wall's own white
    if p.get("white"):                                                # away from the wall the light has to be told
        white = np.array(p["white"], np.float32)
    near = cloth[max(0, int(cy - 0.12 * H)):int(cy + 0.12 * H), max(0, int(cx - 0.10 * W)):int(cx + 0.10 * W)] > 0
    ref = float(np.percentile(a0[max(0, int(cy - 0.12 * H)):int(cy + 0.12 * H), max(0, int(cx - 0.10 * W)):int(cx + 0.10 * W)].mean(axis=2)[near], 70)) if near.sum() > 50 else 60.0
    rng = np.random.default_rng(11)
    out = []
    S = 4
    for k, f in enumerate(frames):
        px, py, ang, sc = poses[k]
        ang += tilt
        hw, hh = pw * sc / 2, ph * sc / 2
        ca, sa = math.cos(ang), math.sin(ang)
        quad = [(px + ca * u - sa * v, py + sa * u + ca * v) for u, v in ((-hw, -hh), (hw, -hh), (hw, hh), (-hw, hh))]
        x0, y0 = int(min(q[0] for q in quad)) - 6, int(min(q[1] for q in quad)) - 6
        x1, y1 = int(max(q[0] for q in quad)) + 7, int(max(q[1] for q in quad)) + 7
        if x0 < 0 or y0 < 0 or x1 >= W or y1 >= H:
            out.append(f)
            continue
        m = Image.new("L", ((x1 - x0) * S, (y1 - y0) * S), 0)
        ImageDraw.Draw(m).polygon([((q[0] - x0) * S, (q[1] - y0) * S) for q in quad], fill=255)
        inner = [(px + ca * u - sa * v, py + sa * u + ca * v) for u, v in ((-hw * 0.78, -hh * 0.88), (hw * 0.78, -hh * 0.88), (hw * 0.78, hh * 0.88), (-hw * 0.78, hh * 0.88))]
        st_ = Image.new("L", m.size, 0)
        ImageDraw.Draw(st_).line([((q[0] - x0) * S, (q[1] - y0) * S) for q in inner + inner[:1]], fill=255, width=S)
        al = np.asarray(m.resize((x1 - x0, y1 - y0), Image.LANCZOS).filter(ImageFilter.GaussianBlur(0.8 * K)), np.float32) / 255
        stitch = np.asarray(st_.resize((x1 - x0, y1 - y0), Image.LANCZOS), np.float32) / 255
        a = np.asarray(f, np.float32)
        reg = a[y0:y1, x0:x1]
        soft = cv2.GaussianBlur(reg, (0, 0), 5 * K)
        fine = (reg.mean(axis=2) + 4) / (soft.mean(axis=2) + 4)       # the folds of the cloth carry through
        level = np.clip(soft.mean(axis=2) / max(1.0, ref), 0.74, 1.04)  # and so does its light and shade
        lit = white[None, None, :] * (level * np.clip(fine, 0.7, 1.25) ** 0.7)[..., None]
        lit = np.clip(lit + rng.normal(0, 1.6, lit.shape[:2])[..., None], 0, 240)
        lit *= (1 - 0.10 * stitch)[..., None]
        shadow = np.asarray(Image.fromarray((al * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(2.2 * K)), np.float32) / 255
        reg2 = reg * (1 - 0.22 * np.clip(shadow - al, 0, 1))[..., None]      # the patch stands a thread proud of the cloth
        a = a.copy()
        a[y0:y1, x0:x1] = reg2 * (1 - al[..., None]) + lit * al[..., None]
        out.append(Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)))
    return out


def bump(img, k, b):
    """An impact: the picture lands a little large and settles. b is [amount, frames]."""
    amount, n = float(b[0]), int(b[1])
    if k >= n:
        return img
    z = 1 + amount * (1 - k / n) ** 2
    big = img.resize((int(round(W * z)), int(round(H * z))), Image.LANCZOS)
    x0, y0 = (big.width - W) // 2, (big.height - H) // 2
    return big.crop((x0, y0, x0 + W, y0 + H))


def place(frames, p):
    """The line-up frame is locked, so everybody stands at the same height in it. A person the model framed too
    high is moved down (down, a fraction of the frame; scale enlarges them first) and the empty wall of a plate
    (plate, plate_in: a moment of the same wall with nobody in front of it) fills in above them. The plate is
    matched to the shot's own wall just under the join, and the join is feathered. keep ([cx, cy, rx, ry] in the
    finished frame) is a part of the person that reaches the top of their own picture and must not fade."""
    s, down, right = float(p.get("scale", 1.0)), float(p.get("down", 0.0)), float(p.get("right", 0.0))
    plates = clip_frames(os.path.join(ROOT, "clips", p["plate"]), len(frames), {"in": p.get("plate_in", 0)})
    if not plates:
        return frames
    top, fe = int(round(down * H)), max(2, int(round(float(p.get("feather", 0.08)) * H)))
    sw, sh = int(round(W * s)), int(round(H * s))
    ox = int(round((W - sw) / 2 + right * W))
    ys, xs = np.mgrid[0:H, 0:W].astype(np.float32)
    t = np.clip((ys - top) / fe, 0, 1)
    m = t * t * (3 - 2 * t)
    if p.get("keep"):
        cx, cy, rx, ry = p["keep"]
        e = ((xs - cx * W) / (rx * W)) ** 2 + ((ys - cy * H) / (ry * H)) ** 2
        k = np.clip((1.25 - e) / 0.5, 0, 1) * (ys >= top)
        m = np.maximum(m, k)
    m = m[:, :, None]
    gain = None
    out = []
    for i, f in enumerate(frames):
        g = f.resize((sw, sh), Image.LANCZOS) if s != 1.0 else f
        moved = Image.new("RGB", (W, H))
        moved.paste(g, (ox, top))
        a = np.asarray(moved, np.float32)
        b = np.asarray(plates[min(i, len(plates) - 1)], np.float32)
        if gain is None:                 # match the plate to this shot's wall, bin by bin across the frame
            band = slice(top + fe, top + fe + int(0.10 * H))
            edges = np.linspace(0, W, 11).astype(int)
            centre = float(p.get("centre", 0.5)) * W
            xsb, rs = [], []
            for j in range(10):
                x0, x1 = edges[j], edges[j + 1]
                if abs((x0 + x1) / 2 - centre) < 0.17 * W:
                    continue                                   # the person
                rs.append(np.median(a[band, x0:x1].reshape(-1, 3), axis=0) / np.maximum(1, np.median(b[band, x0:x1].reshape(-1, 3), axis=0)))
                xsb.append((x0 + x1) / 2)
            rs = np.array(rs)
            gain = np.stack([np.interp(np.arange(W), xsb, rs[:, c]) for c in range(3)], axis=1)[None, :, :]
        out.append(Image.fromarray(np.clip(a * m + b * gain * (1 - m), 0, 255).astype(np.uint8)))
    return out


def find_clip(sid, manifest):
    if sid in manifest:
        return os.path.join(ROOT, "clips", manifest[sid]["file"]), manifest[sid]
    for ext in (".mp4", ".mov", ".png", ".jpg"):
        p = os.path.join(ROOT, "clips", sid + ext)
        if os.path.exists(p):
            return p, {}
    return None, {}


# ---------------------------------------------------------------- looks applied to whole frames
def tube_tv(img, f, k, dur, halves=False):
    """What every real archive shot gets on top of its scanlines: the picture rolls into place over its first
    frames, a soft band of brightness drifts down the tube, and the corners are round. halves: the frame holds
    two real pictures side by side (tools/diptych.py), and each gets a tube of its own."""
    a = np.asarray(img).astype(np.float32)
    n_roll = 2 if dur >= 10 else 1
    if k < n_roll:
        off = int(H * 0.42 * (1 - (k + 1) / (n_roll + 1)))
        a = np.roll(a, off, axis=0)
        bar = max(4, int(10 * K))
        a[max(0, off - bar): off + bar] *= 0.2
    yy = np.arange(H, dtype=np.float32)
    y0 = (f * 0.021 * H) % (1.4 * H) - 0.2 * H
    band = 1 + 0.085 * np.exp(-((yy - y0) / (0.085 * H)) ** 2)
    a *= band[:, None, None]
    a[..., 0] *= (1 + 0.02 * np.exp(-((yy - y0 + 0.03 * H) / (0.06 * H)) ** 2))[:, None]
    a[..., 2] *= (1 + 0.02 * np.exp(-((yy - y0 - 0.03 * H) / (0.06 * H)) ** 2))[:, None]
    out = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
    key = "tube2" if halves else "tube"
    if key not in MATTES:
        m = Image.new("L", (W * 2, H * 2), 0)
        r = int(0.075 * H * 2)
        ex, ey = int(0.004 * W * 2), int(0.006 * H * 2)
        if halves:
            g = int(round(4 * K)) * 2                       # half the gutter between the two pictures, at the matte's double size
            ImageDraw.Draw(m).rounded_rectangle([ex, ey, W - g, H * 2 - ey], radius=r, fill=255)
            ImageDraw.Draw(m).rounded_rectangle([W + g, ey, W * 2 - ex, H * 2 - ey], radius=r, fill=255)
        else:
            ImageDraw.Draw(m).rounded_rectangle([ex, ey, W * 2 - ex, H * 2 - ey], radius=r, fill=255)
        MATTES[key] = m.resize((W, H), Image.LANCZOS)
    return Image.composite(out, Image.new("RGB", (W, H), (0, 0, 0)), MATTES[key])


def boil(img, step, amp=1.6):
    """Ink is redrawn every second frame: the same drawing, a hair different. A coarse grid is nudged and the
    picture is pulled through it."""
    rng = np.random.default_rng(9000 + step)
    nx, ny = 9, 6
    gx = np.linspace(0, W, nx + 1)
    gy = np.linspace(0, H, ny + 1)
    jx = rng.normal(0, amp * K, (ny + 1, nx + 1))
    jy = rng.normal(0, amp * K, (ny + 1, nx + 1))
    jx[0, :] = jx[-1, :] = jx[:, 0] = jx[:, -1] = 0
    jy[0, :] = jy[-1, :] = jy[:, 0] = jy[:, -1] = 0
    mesh = []
    for j in range(ny):
        for i in range(nx):
            box = (int(gx[i]), int(gy[j]), int(gx[i + 1]), int(gy[j + 1]))
            quad = (gx[i] + jx[j, i], gy[j] + jy[j, i], gx[i] + jx[j + 1, i], gy[j + 1] + jy[j + 1, i],
                    gx[i + 1] + jx[j + 1, i + 1], gy[j + 1] + jy[j + 1, i + 1], gx[i + 1] + jx[j, i + 1], gy[j] + jy[j, i + 1])
            mesh.append((box, quad))
    return img.transform((W, H), Image.MESH, mesh, resample=Image.BICUBIC)


def datamosh(img, f, f0):
    """The frame crashes: rows of blocks slip sideways, blocks freeze in the wrong colour, the channels part."""
    a = np.asarray(img).astype(np.float32)
    rng = np.random.default_rng(1969 * 31 + f)
    B = max(8, int(16 * K))
    n = f - f0 + 1
    for _ in range(10 * n):
        by = int(rng.integers(0, H // B)) * B
        bh = B * int(rng.integers(1, 5))
        a[by:by + bh] = np.roll(a[by:by + bh], int(rng.integers(-14, 15)) * B, axis=1)
    for _ in range(46 * n):
        bx, by = int(rng.integers(0, W // B)) * B, int(rng.integers(0, H // B)) * B
        bw = B * int(rng.integers(1, 7))
        col = np.array([CYAN, (255, 0, 170), WHITE, (0, 0, 0), (40, 60, 120)][int(rng.integers(0, 5))], np.float32)
        a[by:by + B, bx:bx + bw] = a[by:by + B, bx:bx + bw] * 0.3 + col * 0.7
    for _ in range(6 * n):                                     # whole macroblocks smeared down the frame
        bx, by = int(rng.integers(0, W // B)) * B, int(rng.integers(0, H // B - 6)) * B
        a[by:by + 6 * B, bx:bx + B] = a[by:by + 1, bx:bx + B]
    a[..., 0] = np.roll(a[..., 0], 5 * n * int(K + 0.5), axis=1)
    a[..., 2] = np.roll(a[..., 2], -5 * n * int(K + 0.5), axis=1)
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


def bright_band(img):
    """Where the baton's light is in a frame: the box round its bright cyan, and its colour."""
    a = np.asarray(img).astype(np.float32)
    m = (a[..., 1] > 170) & (a[..., 2] > 130) & (a[..., 1] > a[..., 0] * 1.08)
    if m.sum() < 50:
        return None
    cols = np.where(m.mean(axis=0) > 0.35)[0]
    if len(cols) < 4:
        cols = np.where(m.any(axis=0))[0]
    rows = np.where(m[:, cols.min():cols.max() + 1].any(axis=1))[0]
    box = (int(cols.min()), int(rows.min()), int(cols.max()) + 1, int(rows.max()) + 1)
    return box, tuple(int(v) for v in a[m].mean(axis=0))


BATON = {}        # where the baton's light was on the last frame of the shot before the end card, and that frame

# ---------------------------------------------------------------- drawn light (tools/light.py)
LIGHTS = []       # what the type asked for on this frame: the cursor, its rings, the block over a word, the wipe
TUBE_BLINK = (1.0, 1.15, 1.0, 1.0, 1.0, 0.92, 0.40, 0.15, 0.05, 0.0)   # a beat of the cursor: it overshoots as it strikes, and it has an afterglow
RING_LIFE = 16
FX = {}           # timing/fx.json: what a shot's whole frame gets once its picture and type are down


def flush_lights(img, f):
    """Draw the frame's lights. They are held back until the type is down, so that they sit on top of it."""
    if not LIGHTS:
        return
    a = np.asarray(img).astype(np.float32).copy()
    wall = None
    for item in LIGHTS:
        kind = item[0]
        if kind == "tube":
            _, box, power, flare, t, seed, *rest = item
            LT.tube(a, box, power=power, k=K, t=t, seed=seed, flare=flare, paper=rest[0] if rest else None)
        elif kind == "ring":
            _, cx, cy, age, gain = item
            LT.ring(a, cx, cy, (0.012 + 0.030 * age) * W, K, gain=gain * (1 - age / float(RING_LIFE + 1)) ** 1.4)
        elif kind == "redact":
            _, box, seed, age, halo = item
            LT.redact(a, box, f, K, seed=seed, age=age, halo=halo)
        elif kind == "spikes":
            _, box, level, n, seed = item
            LT.spikes(a, box, f, K, level=level, n=n, seed=seed)
        elif kind == "blade":
            _, xb, xp = item
            if wall is None:                                   # bare wall is bright and has no colour: the blade passes behind whoever stands on it
                import cv2
                wall = np.clip((a.min(axis=2) - 135) / 40, 0, 1) * np.clip(1 - (a.max(axis=2) - a.min(axis=2)) / 40, 0, 1)
                wall = cv2.GaussianBlur(wall.astype(np.float32), (0, 0), 2 * K)
            LT.blade(a, xb, xp, f, K, wall=wall)
    LIGHTS.clear()
    img.paste(Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)))


def pile_up(img, k, n, o):
    """A drawing that arrives over the shot. "pile": the marks appear in patches, as years of marker would
    (start share, share of the shot it takes). "grow": the drawing rises inside a box from its bottom edge
    (x0, y0, x1, y1 as fractions, share of the shot it takes): a tree being sketched from the root."""
    paper = np.array(o.get("bg", (244, 244, 240)), np.float32)
    a = np.asarray(img).astype(np.float32)
    if o.get("pile"):
        start, share = o["pile"]
        p = min(1.0, start + (1 - start) * k / max(1.0, n * share))
        if "pile" not in MATTES:
            rng = np.random.default_rng(10)
            small = Image.fromarray((rng.random((27, 48)) * 255).astype(np.uint8)).resize((W, H), Image.BICUBIC).filter(ImageFilter.GaussianBlur(10 * K))
            m = np.asarray(small).astype(np.float32)
            MATTES["pile"] = (m - m.min()) / (m.max() - m.min() + 1e-6)
        show = np.clip((p - MATTES["pile"]) / 0.05 + 0.5, 0, 1)[..., None]
        a = a * show + paper * (1 - show)
    if o.get("grow"):
        x0, y0, x1, y1, share = o["grow"]
        p = min(1.0, (k + 1) / max(1.0, n * share))
        line = y1 - (y1 - y0) * p                                   # everything below this line in the box is drawn
        yy = np.arange(H, dtype=np.float32)[:, None] / H
        xx = np.arange(W, dtype=np.float32)[None, :] / W
        fe = 0.03                                                   # the box fades outward at its sides
        inside = (np.clip((xx - x0) / fe + 1, 0, 1) * np.clip((x1 - xx) / fe + 1, 0, 1) * (yy > y0) * (yy < y1)).astype(np.float32)
        hide = inside * np.clip((line - yy) / 0.02 + 0.5, 0, 1)
        box = a[int(y0 * H):int(y1 * H), int(x0 * W):int(x1 * W)]
        page = np.percentile(box.reshape(-1, 3), 92, axis=0)        # the page's own white

        def u8(v):
            return Image.fromarray((np.clip(v, 0, 1) * 255).astype(np.uint8))

        def f32(im):
            return np.asarray(im, np.float32) / 255

        ink = np.clip((page.mean() - a.mean(axis=2) - 6) / 24, 0, 1)
        dense = f32(u8(ink).filter(ImageFilter.BoxBlur(4 * K)))     # a pen stroke is solid; halftone dots are not
        stroke = f32(u8((dense - 0.5) / 0.2).filter(ImageFilter.MaxFilter(2 * int(5 * K) + 1)).filter(ImageFilter.GaussianBlur(1.5 * K)))
        keep = 1 - f32(u8(ink).filter(ImageFilter.MaxFilter(2 * int(3 * K) + 1)))
        num = np.asarray(Image.fromarray((a * keep[..., None]).astype(np.uint8)).filter(ImageFilter.GaussianBlur(12 * K)), np.float32)
        den = f32(u8(keep).filter(ImageFilter.GaussianBlur(12 * K)))[..., None]
        local = np.where(den > 0.05, num / np.maximum(den, 0.05), page)                # the paper round each stroke
        hide = (hide * stroke)[..., None]                           # only the strokes are held back; the paper keeps its grain
        a = a * (1 - hide) + local * hide
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


# ---------------------------------------------------------------- captions
class Cap:
    pass


def est_frames(text):
    return max(8, len(re.findall(r"[aeiouy]+", text.lower())) / 4.8 * FPS)


def token_times(tokens, heard):
    """Start offset of each caption word, from the transcribed word times of the chosen take."""
    marks, n = [], 0
    for text, off in heard:
        marks.append((n, off))
        n += len(re.sub(r"[^a-z0-9]", "", text.lower()))
    letters = [len(re.sub(r"[^a-z0-9]", "", t.lower())) for t in tokens]
    total, acc, out = max(1, sum(letters)), 0, []
    for k in letters:
        pos = acc / total * max(1, n)
        out.append(max([o for i, o in marks if i <= pos + 0.5] or [0]))
        acc += k
    return out


def build_caps(data, durs, heard=None):
    lead = data.get("guess_lead", 5)
    caps = []
    for ln in data["lines"]:
        if not ln.get("cap"):
            continue
        c = Cap()
        c.id, c.style = ln["id"], ln.get("style", "caps")
        s = ln["start"]
        quoted = c.style in ("serif", "docked")
        c.words = []
        if ln.get("parts"):
            end = s
            for i, p in enumerate(ln["parts"]):
                pd = p.get("dur", 5) if p.get("bleep") else durs.get("%s#%d" % (ln["id"], i), est_frames(p.get("say", "")))
                toks = p["cap"].split()
                tot = max(1, sum(len(t) for t in toks))
                acc = 0
                for t in toks:
                    c.words.append([t, p["at"] + pd * acc / tot])
                    acc += len(t)
                end = max(end, p["at"] + pd)
            if quoted:
                c.words[0][0] = "“" + c.words[0][0]
                c.words[-1][0] = c.words[-1][0] + "”"
        else:
            d = durs.get(ln["id"], est_frames(ln["text"]))
            toks = ln["cap"].split()
            tot = max(1, sum(len(t) for t in toks))
            acc = 0
            for t in toks:
                c.words.append([t, s + d * acc / tot])
                acc += len(t)
            wt = (heard or {}).get(ln["id"])
            if isinstance(wt, list) and wt:
                for w, off in zip(c.words, token_times(toks, wt)):
                    w[1] = s + off
            end = s + d
        c.start, c.end = s, end
        c.guess = ln.get("guess")
        c.mode = ln.get("guess_mode", "caption")
        c.bs_at = ln.get("backspace_at")
        c.wipe_at = ln.get("wipe_at")
        c.guess_at = ln.get("guess_at", s - lead)
        c.cap_from = ln.get("cap_from")
        c.tail = None
        if c.guess:
            for w in c.words:
                w[1] = max(w[1], c.bs_at + 5)
        c.until = (c.wipe_at + 5) if c.wipe_at is not None else end + 10
        if ln.get("cap_until") is not None:
            c.until = min(c.until, ln["cap_until"])
        caps.append(c)
    caps.sort(key=lambda c: c.start)
    caps[0].show_from = caps[0].cap_from if caps[0].cap_from is not None else caps[0].guess_at
    for a, b in zip(caps, caps[1:]):
        if b.guess and b.mode in ("caption", "caption+card"):
            # a wrong guess is typed straight after the previous speaker's sentence, as autocomplete would
            a.tail = dict(text=b.guess, at=b.guess_at, bs=b.bs_at, mode=b.mode)
            a.until = b.bs_at + 5 if b.mode == "caption" else b.bs_at
            b.show_from = b.bs_at + 5
            continue
        if b.guess:  # the guess is on a black card; the caption only carries what is then said
            b.show_from = b.bs_at + 5
        elif b.cap_from is not None:
            b.show_from = b.cap_from
        else:  # the guess never cuts off someone who is still speaking
            b.show_from = min(b.start, max(b.guess_at, int(a.end) + 1))
        if a.wipe_at is None:
            a.until = min(a.until, b.show_from)
    return caps


def cap_segments(c, f):
    """What the caption shows on frame f: a list of (text, state), state w = said, g = guessed."""
    if c.guess:
        return [(w, "w") for w, t in c.words if t <= f]
    out = [(w, "w" if t <= f else "g") for w, t in c.words]
    if c.wipe_at is not None and f >= c.wipe_at:
        total = sum(len(w) for w, _ in out) + len(out) - 1
        keep = int(total * (1 - (f - c.wipe_at + 1) / 5.0))
        cut, n = [], 0
        for w, st in out:
            if n + len(w) <= keep:
                cut.append((w, st))
                n += len(w) + 1
            else:
                if keep - n > 0 and "[BLOCK]" not in w:
                    cut.append((w[:keep - n], st))
                break
        out = cut
    if c.tail and f >= c.tail["at"]:
        g = c.tail["text"]
        if f >= c.tail["bs"]:
            g = g[:int(len(g) * (1 - (f - c.tail["bs"] + 1) / 5.0))] if c.tail["mode"] == "caption" else ""
        if g:
            out.append((g, "g"))
    return out


def cap_reserve(c):
    """The widest the line will ever be, so that it never shifts sideways while it changes."""
    return [w for w, _ in c.words] + ([c.tail["text"]] if c.tail else [])


def draw_cap_line(img, d, segs, style, bg, cursor=True, prefix=None, reserve=None):
    """One caption line, centred at the bottom: white upright = said, grey italic = guessed."""
    serif = style in ("serif", "docked")
    path, px = (F_SERIF_I, SERIF_CAP_PX) if serif else (F_DIN, CAP_PX)
    space = width(" ", path, px)
    block_w = px * K * 2.2
    runs = []
    if prefix:
        runs.append((prefix, F_DIN, CAP_PX, "w"))
    for text, st in segs:
        runs.append((text, path, px, st))
    if not runs:
        return

    def run_w(t, p, q):
        return block_w if t.strip("“”") == "[BLOCK]" else width(t, p, q)

    widths = [run_w(t, p, q) for t, p, q, _ in runs]
    total = sum(widths) + space * (len(runs) - 1)
    if reserve:
        full = ([(prefix, F_DIN, CAP_PX)] if prefix else []) + [(t, path, px) for t in reserve]
        total = sum(run_w(t, p, q) for t, p, q in full) + space * (len(full) - 1)
    x = (W - total) / 2
    base = H * CAP_Y
    ch = cap_height(F_DIN, CAP_PX)
    paper = lum(bg) > 128
    if not paper:
        # The shot's tint says dark, but the picture under the words can be as bright as paper (a white studio, daisies
        # in a flash, the baton held to the lens). So look at it. A white frame is paper, and gets paper's box. A bright
        # thing in a darker frame gets a soft dark shade under the whole line, deeper the more of it is bright. Found in the 1080p
        # review: "NOBODY PREDICTS THE FUTURE." sat on the daisies and "START THE PROOF." on white with only a shadow.
        box = (max(0, int(x - 14 * K)), max(0, int(base - ch - 10 * K)), min(W, int(x + total + 14 * K)), min(H, int(base + 12 * K)))
        under = np.asarray(img.crop(box).convert("L"), np.float32)
        bright = float((under > 150).mean()) if under.size else 0.0
        whole = float(np.median(np.asarray(img.resize((96, 54)).convert("L"))))
        if whole > 150 and bright > 0.2:                 # the whole frame is white (a studio, a sheet of drawings): paper
            paper = True
        elif bright > 0.04:                              # a bright thing in a dark frame: a shade, so no box jumps in as it arrives
            depth = 0.68 * min(1.0, (bright - 0.04) / 0.26)      # from nothing: a shade that switched on at a third showed as a flicker from cut to cut in the line-up
            pad = ch * 0.9
            shade = Image.new("L", (W, H), 0)
            ImageDraw.Draw(shade).rectangle([x - pad, base - ch - pad * 0.8, x + total + pad, base + pad * 0.8], fill=int(255 * depth))
            img.paste(Image.new("RGB", (W, H), (0, 6, 12)), (0, 0), shade.filter(ImageFilter.GaussianBlur(ch * 0.7)))
    if paper:  # white type cannot sit on paper: back it
        shown = sum(widths) + space * (len(runs) - 1)
        d.rectangle([x - 14 * K, base - ch - 10 * K, x + shown + 14 * K, base + 12 * K], fill=(0, 0, 0, 170))
    bar_x = None
    for (text, p, q, st), w in zip(runs, widths):
        if st == "g" and bar_x is None:
            bar_x = x - space * 0.5
        if text.strip("“”") == "[BLOCK]":
            if text.startswith("“"):
                put(img, x - width("“", p, q), base, "“", p, q, WHITE if st == "w" else GREY)
            if st == "w":
                LIGHTS.append(("redact", (x, base - ch, x + w, base + 2 * K), 5, None, 0.45))
            else:
                d.rectangle([x, base - ch, x + w, base + 2 * K], fill=mix((0, 0, 0), CYAN, 0.30))
        else:
            put(img, x + 2 * K, base + 2 * K, text, p, q, (0, 0, 0), oblique=(st == "g" and not serif))
            put(img, x, base, text, p, q, WHITE if st == "w" else GREY, oblique=(st == "g" and not serif))
        x += w + space
    if cursor:
        if bar_x is None:
            bar_x = x - space * 0.6
        LIGHTS.append(("tube", (bar_x - 1.5 * K, base - ch - 2 * K, bar_x + 1.5 * K, base + 3 * K), 1.0, 0.0, 0, 3))


# ---------------------------------------------------------------- on-screen type events
STYLE = {"prompt": (F_SERIF, 64), "doubt": (F_SERIF_I, 40), "stamp": (F_DIN, CAP_PX * 4), "stamp2": (F_DIN, CAP_PX * 2),
         "small": (F_DIN, CAP_PX), "fine": (F_DIN, 21), "quote": (F_SERIF_I, 52), "guess": (F_DIN, 104),
         "tele": (F_TELE, 150), "term": (F_MONO, 24), "title": (F_BRUSH, 150), "hand": (F_HAND, 46), "ask": (F_SERIF_I, 86)}


def draw_text_event(img, d, e, f, bg, anchors):
    style = e["style"]
    face = e.get("face", style)
    path, px = STYLE[face]
    px = px * e.get("scale", 1.0)
    text = e.get("text", "")
    full = text
    if style == "steps":
        text = ""
        for at, t in e["steps"]:
            if f >= at:
                text = t
        full = max((t for _, t in e["steps"]), key=len)
    color = INK if lum(bg) > 128 else WHITE                 # by the plate; "ink", "pencil" and "white" overrule it
    if e.get("color") == "ink":
        color = INK
    if e.get("color") == "pencil":
        color = (92, 92, 100)
    if e.get("color") == "white":
        color = WHITE
    if e.get("color") == "grey":
        color = GREY
    oblique = False
    if style == "guess":
        color, oblique = GREY, True
        bs = e.get("backspace")
        if bs is not None and f >= bs:
            text = text[:int(len(text) * (1 - (f - bs + 1) / 5.0))]
    scramble = ""
    if "type" in e:
        t0 = e.get("type_from", e["in"])
        head = int(e.get("type_head", 0))
        text = text[:head + max(0, int((f - t0 + 1) * e["type"]))] if f >= t0 else text[:head]
        if e.get("decode") and f >= t0 and len(text) < len(full):      # being decoded: the next letters are still noise, a different guess every frame
            ahead = full[len(text): len(text) + int(e["decode"])]
            scramble = "".join(c if c in " .,'’“”\"" else "abcdefghijklmnopqrstuvwxyz"[int(float(LT.h01(f, i, len(text))) * 25.99)] for i, c in enumerate(ahead))
    if style == "fine":
        color = mix(bg, color, 0.72)
    # stamps and other long lines shrink to fit the frame
    while width(full, path, px) > W * 0.90 and px > 10:
        px *= 0.94
    wfull = width(full, path, px)
    x = e.get("x", 0.5) * W
    base = e.get("y", 0.5) * H
    if "after" in e:  # completions stack like an autocomplete list, left edge after the prompt's cursor
        ax, abase, apx = anchors[e["after"]]
        x = ax
        base = abase + e.get("row", 0) * apx * K * 0.98
    elif e.get("align") == "center":
        x -= wfull / 2
    if e.get("backing") and text:        # over a busy picture: a soft dark patch under the words, as wide as the whole line will be
        chb = cap_height(path, px)
        pad = chb * 0.9
        shade = Image.new("L", (W, H), 0)
        ImageDraw.Draw(shade).rectangle([x - pad, base - chb - pad, x + wfull + pad, base + pad * 0.8], fill=int(255 * float(e["backing"])))
        img.paste(Image.new("RGB", (W, H), (0, 6, 12)), (0, 0), shade.filter(ImageFilter.GaussianBlur(chb * 0.9)))
    born, prev = e["in"], ""
    if style == "steps":
        for at, t in e["steps"]:
            if f >= at:
                born = at
        prev = max((t for at, t in e["steps"] if at < born and text.startswith(t)), key=len, default="")
    age = f - born
    slam = e.get("slam", 0.60 if face in ("stamp", "stamp2") else 0.22 if style == "guess" else 0)
    if slam and 0 <= age < 4 and "type" not in e and text and len(text) > len(prev) and e.get("backspace", 10 ** 9) > f:
        # it lands. A whole stamp comes in large and settles in four frames, never past the frame's edge; a second
        # part is pressed on beside the first, coming down onto the line. What was already there holds still.
        adv = put(img, x, base, prev, path, px, color, oblique) if prev else 0
        new = text[len(prev):]
        wn, chh = width(new, path, px), cap_height(path, px)
        if prev and e.get("punch_parts"):      # every part lands with a punch of its own, hot at first; it grows away from what is already there
            s = 1 + float(slam) * (1 - age / 4.0) ** 3
            ws = width(new, path, px * s)
            put(img, min(x + adv, W - ws - 0.012 * W), base + chh * (s - 1) / 2, new, path, px * s,
                mix(CYAN, color, min(1.0, 0.2 + age / 4.0)) if e.get("hot") else color, oblique)
        elif prev:
            put(img, x + adv, base - 0.55 * chh * max(0.0, 1 - age / 3.0) ** 2, new, path, px, color, oblique)
        else:
            s = min(1 + float(slam) * (1 - age / 4.0) ** 3, max(1.0, 0.97 * W / max(1.0, wn)))
            ws = width(new, path, px * s)
            xn = min(max(x + wn / 2 - ws / 2, 0.012 * W), W - ws - 0.012 * W)
            put(img, xn, base + chh * (s - 1) / 2, new, path, px * s, mix(CYAN, color, min(1.0, 0.2 + age / 4.0)) if e.get("hot") else color, oblique)
        adv += wn
    else:
        adv = put(img, x, base, text, path, px, color, oblique)
    if scramble:
        adv += put(img, x + adv, base, scramble, path, px, mix(bg, CYAN, 0.62), oblique)
    if style == "guess" and text and e.get("backspace", 10 ** 9) > f:      # the machine's guess: a light passes along it
        im, asc = tile(text, path, px, (255, 255, 255), oblique)
        al = np.asarray(im.getchannel("A"), np.float32) / 255.0
        ph = ((f - e["in"]) / 16.0) % 1.0
        xsb = np.arange(al.shape[1], dtype=np.float32)[None, :]
        band = np.exp(-((xsb - (ph * 1.5 - 0.25) * al.shape[1]) / (0.07 * al.shape[1] + 1)) ** 2)
        shine = Image.fromarray(np.clip(al * band * 215, 0, 255).astype(np.uint8))
        img.paste(Image.new("RGB", im.size, (214, 250, 255)), (int(round(x)) - 3, int(round(base)) - asc), shine)
    if e.get("id"):
        anchors[e["id"]] = (x + wfull + px * K * 0.95, base, px)
    if e.get("cursor") == "block":
        typing = "type" in e and f >= e.get("type_from", e["in"]) and text != full
        solid = f >= e.get("solid_from", 10 ** 9)                   # the last beat: the cursor stays lit, as on frame 0
        power = 1.0 if (typing or solid) else TUBE_BLINK[(f - e.get("cursor_from", e["in"])) % BEAT]
        ch = cap_height(path, px)
        cx = x + adv + px * K * float(e.get("cursor_gap", 0.12))
        box = (cx, base - ch * 1.05, cx + px * K * 0.42, base + ch * 0.12)
        lit = f - e.get("ignite", -10 ** 9)                         # the frame it comes on: a flare for a few frames
        flare = (1 - lit / 6.0) ** 2 if 0 <= lit < 6 else 0.0
        if typing and (f - e.get("type_from", e["in"])) % 2 == 0:
            power = 1.12                                            # each letter it sets down, it brightens
        if e.get("cursor_from", -10 ** 9) <= f < e.get("cursor_until", 10 ** 9):      # a cursor can leave one line for another
            LIGHTS.append(("tube", box, max(power, 1.0 + 0.5 * flare) if flare else power, flare, 0 if solid else f - e.get("cursor_from", e["in"]), 1))
        for r in e.get("rings", ()):                                # every click sends a ring out from it
            ra = f - r
            if 1 <= ra <= RING_LIFE:
                LIGHTS.append(("ring", (box[0] + box[2]) / 2, (box[1] + box[3]) / 2, ra, e.get("ring_gain", 0.85)))


def draw_screen(img, e, f):
    """Words on a screen that is in the picture. They are set flat, as the screen itself would show them, and then
    laid into the screen's own four corners, so they lean and shrink as it does. Lines type on one after another."""
    import cv2
    vw, vh = e.get("canvas", (880, 536))
    layer = Image.new("RGBA", (vw, vh), (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    ink, paper = tuple(e.get("ink", INK)), tuple(e.get("paper", (244, 244, 240)))
    faces = {"mono": F_MONO, "tele": F_TELE, "din": F_DIN, "serif": F_SERIF}
    budget = max(0.0, (f - e.get("type_from", e["in"]) + 1) * float(e.get("rate", 4.0)))      # letters typed so far, across the lines that flow
    cur = None
    for ln in e["lines"]:
        fnt = ImageFont.truetype(faces[ln.get("face", "tele")], int(ln["px"]))
        text = ln["text"]
        if ln.get("flow", True):
            n = int(min(len(text), budget))
            budget -= n
            if n == 0 and cur is not None:
                continue
        else:
            n = len(text) if f >= ln.get("at", e["in"]) else 0
            if not n:
                continue
        col = mix(paper, ink, ln.get("weight", 1.0))
        ld.text((ln["x"], ln["y"]), text[:n], font=fnt, fill=tuple(col) + (255,), anchor="ls")
        if ln.get("flow", True):
            l_, t_, r_, b_ = fnt.getbbox("H", anchor="ls")
            adv = fnt.getlength(text[:n])
            cur = (ln["x"] + adv + ln["px"] * 0.10, ln["y"] + t_ * 1.05, ln["x"] + adv + ln["px"] * 0.56, ln["y"] - t_ * 0.12)
            if n < len(text):
                budget = 0.0
    if cur is not None and (((f - e["in"]) % BEAT) < 6 or budget == 0.0):          # the cursor, on this screen
        ld.rounded_rectangle(cur, radius=int((cur[2] - cur[0]) * 0.22), fill=(0, 176, 214, 255))
    quad = np.float32([[qx * W, qy * H] for qx, qy in e["quad"]])                  # top left, top right, bottom right, bottom left
    M = cv2.getPerspectiveTransform(np.float32([[0, 0], [vw, 0], [vw, vh], [0, vh]]), quad)
    src = cv2.GaussianBlur(np.asarray(layer), (0, 0), 0.7)
    warped = cv2.warpPerspective(src, M, (W, H), flags=cv2.INTER_LINEAR).astype(np.float32)
    if e.get("soft"):
        warped = cv2.GaussianBlur(warped, (0, 0), float(e["soft"]) * K)
    al = warped[..., 3:4] / 255.0 * float(e.get("opacity", 0.94))
    base = np.asarray(img).astype(np.float32)
    img.paste(Image.fromarray(np.clip(base * (1 - al) + warped[..., :3] * al, 0, 255).astype(np.uint8)))


def draw_events(img, d, events, f, bg, anchors):
    for e in events:
        if not (e["in"] <= f < e["out"]):
            continue
        st = e["style"]
        if st == "rect":    # the block over a word: a slab of lit cells that lands hot and keeps changing
            LIGHTS.append(("redact", (e["x"] * W, e["y"] * H, (e["x"] + e["w"]) * W, (e["y"] + e["h"]) * H), int(e["x"] * 100), f - e["in"], 1.0))
        elif st == "screen":
            draw_screen(img, e, f)
        elif st == "spikes":  # a row of slits of light, one for each electrode: how busy they are is set frame by frame ("levels")
            lv = float(np.interp(f, [p[0] for p in e["levels"]], [p[1] for p in e["levels"]]))
            LIGHTS.append(("spikes", (e["x"] * W, e["y"] * H, (e["x"] + e["w"]) * W, (e["y"] + e["h"]) * H), lv, int(e.get("n", 256)), int(e.get("seed", 0))))
        elif st == "ghost":  # a word being sent: the letters that have arrived are white, the rest stand grey, as the film's guesses do
            path, px = STYLE[e.get("face", "tele")]
            px = px * e.get("scale", 1.0)
            word = e["word"]
            n, born = 0, e["in"]
            for at, k in e["steps"]:
                if f >= at:
                    n, born = k, at
            gap = px * K * 0.62 if e.get("cursor") else 0.0
            total = width(word, path, px) + gap
            x0 = e["x"] * W - total / 2
            adv = put(img, x0, e["y"] * H, word[:max(0, n - 1)], path, px, WHITE)
            if n:                                             # the newest letter arrives hot and cools to white over three frames
                adv += put(img, x0 + adv, e["y"] * H, word[n - 1:n], path, px, mix(CYAN, WHITE, min(1.0, 0.25 + (f - born) / 3.0)))
            put(img, x0 + adv + gap, e["y"] * H, word[n:], path, px, mix((0, 0, 0), GREY, 0.62))
            dark = any(a <= f < b for a, b in e.get("cursor_off", ()))        # the far computer is down: no cursor
            if e.get("cursor") and not dark:
                ch = cap_height(path, px)
                cx = x0 + adv + px * K * 0.10
                LIGHTS.append(("tube", (cx, e["y"] * H - ch * 1.05, cx + px * K * 0.42, e["y"] * H + ch * 0.12), TUBE_BLINK[(f - born) % BEAT] if not e.get("solid") else 1.0, 0.0, f - born, 1))
        elif st == "mark":  # the maker's mark, when there is one (clips/mark.png): it lands like a stamp. Until then its place is left empty.
            mk = os.path.join(ROOT, "clips", "mark.png")
            if os.path.exists(mk):
                im = Image.open(mk).convert("RGBA")
                hh = e["h"] * H * (1 + 0.5 * max(0.0, 1 - (f - e["in"]) / 4.0) ** 3)
                im = im.resize((max(1, int(im.size[0] * hh / im.size[1])), max(1, int(hh))), Image.LANCZOS)
                img.paste(im, (int(e["x"] * W + e["w"] * W / 2 - im.size[0] / 2), int(e["y"] * H + e["h"] * H / 2 - im.size[1] / 2)), im)
        elif st == "sweep":  # backspace: a blade of light runs right to left and takes the wall's ink with it
            xb = W * (0.80 - 0.19 * (f - e["in"]))
            LIGHTS.append(("blade", xb, xb + 0.19 * W))
        elif st == "bar":   # the baton's band of light, as the shot before left it, draws itself in to the cursor's place
            n, k = e["out"] - e["in"], f - e["in"]
            t = (k + 1) / float(n)
            sm = lambda v: v * v * (3 - 2 * v)
            path, px = STYLE["prompt"]
            px = px * e.get("scale", 1.0)                             # the reel sets the last screen's type smaller: the bar lands where that cursor is
            x = e["x"] * W + width(e["text"], path, px) + px * K * 0.12
            ch = cap_height(path, px)
            to = (x, e["y"] * H - ch * 1.05, x + px * K * 0.42, e["y"] * H + ch * 0.12)
            fr = BATON.get("box", (W * 0.44, 0, W * 0.56, H))
            last = BATON.get("frame")
            if last is not None and k < 3:                           # the frame before fades under it: the light is carried over the cut
                img.paste(Image.blend(img, last, (0.50, 0.24, 0.08)[k]))
            for j, back in enumerate((0.34, 0.20, 0.09)):            # where it was a moment ago
                tb = max(0.0, t - back)
                LIGHTS.append(("tube", [fr[i] + (to[i] - fr[i]) * sm(tb) for i in range(4)], 0.16 + 0.07 * j, 0.0, f, 1, False))
            LIGHTS.append(("tube", [fr[i] + (to[i] - fr[i]) * sm(t) for i in range(4)], 1.2, 0.55 * t, f, 1, False))
            for r in e.get("rings", ()):                             # the click that starts it sends a ring out from where it is going
                if 1 <= f - r <= RING_LIFE:
                    LIGHTS.append(("ring", (to[0] + to[2]) / 2, (to[1] + to[3]) / 2, f - r, 0.85))
        elif st == "title":   # brush lettering on the glass: light, a little soft, glowing into the haze
            path, px = STYLE["title"]
            px = px * e.get("scale", 1.0)
            wd = width(e["text"], path, px)
            layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            put(layer, e["x"] * W - wd / 2, e["y"] * H, e["text"], path, px, (226, 252, 255))
            glow = layer.filter(ImageFilter.GaussianBlur(9 * K))
            glow.putalpha(glow.getchannel("A").point(lambda v: int(v * 0.55)))
            sharp = layer.filter(ImageFilter.GaussianBlur(0.7 * K))
            sharp.putalpha(sharp.getchannel("A").point(lambda v: int(v * 0.86)))
            base = img.convert("RGBA")
            base = Image.alpha_composite(Image.alpha_composite(base, glow), sharp)
            img.paste(base.convert("RGB"))
            ph = (f - e["in"] + 0.5) / float(e["out"] - e["in"])         # a glint travels along the lettering, once
            al = np.asarray(layer.getchannel("A"), np.float32) / 255.0
            band = np.exp(-((np.arange(W, dtype=np.float32)[None, :] - (0.10 + 0.80 * ph) * W) / (0.045 * W)) ** 2)
            hot = Image.fromarray(np.clip(al * band * 255, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.0 * K))
            img.paste(Image.new("RGB", (W, H), (150, 240, 255)), (0, 0), hot.filter(ImageFilter.GaussianBlur(12 * K)).point(lambda v: min(255, int(v * 1.6))))
            img.paste(Image.new("RGB", (W, H), (255, 255, 255)), (0, 0), hot)
        elif st == "caption":
            draw_cap_line(img, d, [(e["text"], "w")], "caps", bg, cursor=False)
        elif st == "docked":
            draw_cap_line(img, d, [(e["text"], "w")], "docked", bg, cursor=False, prefix="THE FUTURE IS")
        else:
            draw_text_event(img, d, e, f, bg, anchors)
    flush_lights(img, f)


# ---------------------------------------------------------------- burn-in
def tc(frame):
    s = frame / FPS
    return "%d:%05.2f" % (int(s // 60), s % 60)


def burnin(img, d, f, shot, index, total_shots, passages, total, label):
    band = int(H * 0.058)
    d.rectangle([0, 0, W, band], fill=(0, 0, 0, 150))
    base = band * 0.66
    put(img, W * 0.012, base, label, F_UI, 14, (200, 200, 200))
    mid = "%s    f%04d    bar %02d.%d" % (tc(f), f, f // BAR + 1, (f % BAR) // BEAT + 1)
    put(img, W * 0.5 - width(mid, F_MONO, 15) / 2, base, mid, F_MONO, 15, WHITE)
    right = "%s  ·  %s  ·  cut %d/%d" % (shot["id"], shot["source"], index + 1, total_shots)
    put(img, W * 0.972 - width(right, F_UI, 14), base, right, F_UI, 14, (200, 200, 200))
    if f % BEAT < 2:  # beat light, brighter on the bar
        r = band * (0.2 if f % BAR < 2 else 0.11)
        d.ellipse([W * 0.986 - r, band * 0.5 - r, W * 0.986 + r, band * 0.5 + r], fill=CYAN)
    y0, y1 = band, band + max(3, int(H * 0.008))
    for i, p in enumerate(passages):
        a = p["a"] / total * W
        b = p["b"] / total * W
        d.rectangle([a, y0, b - 1, y1], fill=(70, 74, 84) if i % 2 else (44, 47, 54))
    d.rectangle([f / total * W - 1, y0 - 2, f / total * W + 1, y1 + 2], fill=CYAN)


# ---------------------------------------------------------------- reading load
def read_report(events, path):
    rows = []
    for e in events:
        text = e.get("text") or e.get("word") or (e["steps"][-1][1] if e.get("steps") else "")
        if e["style"] == "screen":
            text = " ".join(l["text"] for l in e["lines"])
        if e["style"] in ("rect", "sweep", "spikes") or not text:
            continue
        frames = e["out"] - max(e["in"], e.get("type_from", e["in"]))
        if e["style"] == "guess" and e.get("backspace") is not None:
            frames = max(1, e["backspace"] - e["in"]) + 5
        n = len(re.sub(r"[^A-Za-z0-9]", "", text))
        cps = n / (frames / FPS)
        verdict = "easy" if cps <= 17 else ("fast" if cps <= 26 else "freeze-frame only")
        rows.append((e["in"], e.get("shot", ""), text, frames, cps, verdict))
    rows.sort()
    out = ["# Reading load: can the type be read in the time it is on screen?", "",
           "Letters and digits per second. Subtitle practice is about 17. Up to 26 is a fast read. Above that the "
           "words are for a second viewing or the pause button, which is on purpose for some and a problem for others.", "",
           "| In | Shot | Type | Frames | Characters per second | Verdict |", "| --- | --- | --- | --- | --- | --- |"]
    for a, shot, text, frames, cps, verdict in rows:
        out.append("| %s | %s | %s | %d | %.0f | %s |" % (tc(a), shot, text, frames, cps, verdict))
    open(path, "w").write("\n".join(out) + "\n")
    return rows


# ---------------------------------------------------------------- main
def load_state(clean=False, label="FIRST WORD  animatic"):
    """Everything a frame needs besides its own shot: the cut, the type, the captions, the looks."""
    sl = json.load(open(os.path.join(ROOT, "shotlist.json")))
    shots, total = sl["shots"], sl["frames"]
    lines = json.load(open(os.path.join(ROOT, "timing", "lines.json")))
    events = json.load(open(os.path.join(ROOT, "timing", "type.json")))["events"]
    dp = os.path.join(ROOT, "timing", "scratch_durations.json")
    durs = json.load(open(dp)) if os.path.exists(dp) else {}
    mp = os.path.join(ROOT, "clips", "manifest.json")
    manifest = json.load(open(mp)) if os.path.exists(mp) else {}
    wp = os.path.join(ROOT, "timing", "words.json")
    caps = build_caps(lines, durs, json.load(open(wp)) if os.path.exists(wp) else None)
    passages = []
    for p in sl["passages"]:
        ss = [s for s in shots if s["passage"] == p["key"]]
        passages.append(dict(key=p["key"], a=ss[0]["start"], b=ss[-1]["start"] + ss[-1]["dur"]))
    silent = set()
    for e in events:
        if e["style"] in ("caption", "docked"):
            silent.update(range(e["in"], e["out"]))
    fp = os.path.join(ROOT, "timing", "fx.json")
    FX.clear()
    if os.path.exists(fp):
        FX.update(json.load(open(fp)))
    return dict(shots=shots, total=total, events=events, caps=caps, passages=passages, silent=silent, manifest=manifest,
                anchors={}, clean=clean, label=label)


def load_shot(st, s):
    """A shot's picture: its frames, or the card that stands in for it, and what its type is set against."""
    path, opts = find_clip(s["id"], st["manifest"])
    frames = clip_frames(path, s["dur"], opts) if path else None
    if frames:
        return frames, None, tuple(opts.get("bg", (20, 20, 20))), opts       # a light plate takes ink
    base, bg = card(s)
    return None, base, bg, opts


def compose(st, s, index, k, frames, base, bg, opts):
    """One finished frame: the shot's picture, its looks, the type, what the whole frame then gets, the captions."""
    f = s["start"] + k
    events, caps = st["events"], st["caps"]
    fx = FX.get("shots", {}).get(s["id"], {})
    archive = "ARCHIVE" in s["source"]
    img = (frames[k] if frames else base).copy()
    if frames and archive:                              # everything real: the tube it plays on
        img = tube_tv(img, f, k, s["dur"], halves=opts.get("tubes") == 2)
    if frames and (opts.get("pile") or opts.get("grow")):
        img = pile_up(img, k, s["dur"], opts)
    if frames and opts.get("boil"):                     # an ink drawing, redrawn every second frame
        img = boil(img, f // 2, float(opts["boil"]))
    if frames and opts.get("bump"):                     # an impact: it lands large and settles
        img = bump(img, k, opts["bump"])
    if frames and s["id"] in INKED:                     # the doubts drawn on the wall round the people
        ink = inklayer.layer(f, W, H)
        if ink is not None:
            img = ImageChops.multiply(img, boil(ink, f // 2, 1.3))
    bl = FX.get("bloom") or {}
    if frames and bl and not archive and s["id"] not in bl.get("skip", ()) and any(t in s["source"] for t in bl.get("sources", ())):
        img = Image.fromarray(np.clip(LT.bloom(np.asarray(img).astype(np.float32), bl.get("amount", 0.2), K), 0, 255).astype(np.uint8))
    if frames and opts.get("bar_from") and k == s["dur"] - 1:      # remember where the baton's light ended, and the frame itself
        found = bright_band(img)
        if found:
            BATON["box"], BATON["color"] = found
        BATON["frame"] = img.copy()
    d = ImageDraw.Draw(img, "RGBA")
    draw_events(img, d, events, f, bg, st["anchors"])
    for e in events:                                    # a crash takes the whole frame, type and all
        if e.get("glitch_from") is not None and e["in"] <= f < e["out"] and e["glitch_from"] <= f < e.get("glitch_to", 10 ** 9):
            img = datamosh(img, f, e["glitch_from"])
    if fx:                                              # what the whole frame gets, picture and type together (timing/fx.json)
        a = np.asarray(img).astype(np.float32)
        if fx.get("creep"):                             # a slow push over the shot: [from, to, centre x, centre y]
            c = fx["creep"]
            t = k / float(max(1, s["dur"] - 1))
            a = LT.creep(a, c[0] + (c[1] - c[0]) * t, *(c[2:4] if len(c) > 3 else (0.5, 0.5)))
        if fx.get("punch") and k < fx["punch"][1]:      # it lands a little large on the cut and settles: [amount, frames]
            a = LT.creep(a, 1 + fx["punch"][0] * (1 - k / float(fx["punch"][1])) ** 2, *(fx["punch"][2:4] if len(fx["punch"]) > 3 else (0.5, 0.5)))
        if fx.get("tear") and k < int(fx["tear"]):      # the picture slips for a frame as it arrives
            a = LT.tear(a, f, K, seed=index, strength=float(fx.get("tear_strength", 1.0)))
        if fx.get("shock") and k < int(fx["shock"]):    # an impact: a flash, and the colours pulled apart
            a = LT.shock(a, k, K, frames=int(fx["shock"]), flash=float(fx.get("flash", 0.55)))
        for kf, amt, n in fx.get("kicks", ()):          # a punch-in on a frame inside the shot: [film frame, amount, frames]
            if 0 <= f - kf < n:
                a = LT.creep(a, 1 + amt * (1 - (f - kf) / float(n)) ** 2, *fx.get("kick_centre", (0.5, 0.5)))
        for sf, n, fl in fx.get("shocks", ()):          # an impact on a frame inside the shot: [film frame, frames, flash]
            if 0 <= f - sf < n:
                a = LT.shock(a, f - sf, K, frames=int(n), flash=float(fl))
        if fx.get("crt_off") and k >= s["dur"] - int(fx["crt_off"]):     # the tube switches off on the shot's last frames
            n = int(fx["crt_off"])
            a = LT.crt_off(a, (k - (s["dur"] - n) + 1) / float(n + 1))
        img = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
    d = ImageDraw.Draw(img, "RGBA")
    for c in caps:
        if f in st["silent"]:  # a silent caption owns the line
            break
        if c.show_from <= f < c.until:
            draw_cap_line(img, d, cap_segments(c, f), c.style, bg, cursor=f <= c.end + 2,
                          prefix="THE FUTURE IS" if c.style == "docked" else None, reserve=cap_reserve(c))
            break
    flush_lights(img, f)
    if not st["clean"]:
        burnin(img, ImageDraw.Draw(img, "RGBA"), f, s, index, len(st["shots"]), st["passages"], st["total"], st["label"])
    return img


def main():
    global W, H, K
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(ROOT, "out", "animatic.mp4"))
    ap.add_argument("--size", default="1280x720")
    ap.add_argument("--audio", default=os.path.join(ROOT, "audio", "temp_mix.wav"))
    ap.add_argument("--label", default="FIRST WORD  animatic")
    ap.add_argument("--clean", action="store_true", help="no burn-in")
    ap.add_argument("--stills", default="", help="comma-separated frames to save as PNG next to the output")
    ap.add_argument("--crf", default="18")
    ap.add_argument("--preset", default="medium")
    ap.add_argument("--master", default="", help="also write this file (.mov): ProRes 422 HQ with the sound uncompressed")
    a = ap.parse_args()
    W, H = [int(v) for v in a.size.split("x")]
    K = H / 720.0
    st = load_state(a.clean, a.label)
    shots, total = st["shots"], st["total"]

    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    cmd = ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "%dx%d" % (W, H), "-r", str(FPS), "-i", "-"]
    if a.audio and os.path.exists(a.audio):
        cmd += ["-i", a.audio, "-c:a", "aac", "-b:a", "256k"]         # at 192k the encoder overshoots full scale on one relay click (measured)
    # The colours go to the file by the HD rule (BT.709) and the file says so. Until the 1080p pass neither was done:
    # ffmpeg's own default turns RGB into video by the old SD rule (BT.601) and writes no tag, and a player then reads
    # an HD file by the HD rule, so every colour came out a little wrong (skin a touch redder, the cyan a touch greener).
    to709 = "scale=in_range=full:out_range=limited:out_color_matrix=bt709:flags=accurate_rnd+full_chroma_int"
    said = ",setparams=color_primaries=bt709:color_trc=bt709:colorspace=bt709:range=tv"     # the frames carry the tags to the encoder
    tags = ["-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709", "-color_range", "tv"]
    cmd += ["-vf", to709 + ",format=yuv420p" + said, "-c:v", "libx264", "-preset", a.preset, "-crf", a.crf] + tags + ["-r", str(FPS),
            "-t", "%.6f" % (total / FPS), "-movflags", "+faststart", a.out]
    enc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    mast = None
    if a.master:                                        # the same frames once more, hardly compressed: ProRes 422 HQ, 10-bit, the sound as it is in the mix
        mc = ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "%dx%d" % (W, H), "-r", str(FPS), "-i", "-"]
        if a.audio and os.path.exists(a.audio):
            mc += ["-i", a.audio, "-c:a", "pcm_s24le"]
        mc += ["-vf", to709 + ",format=yuv422p10le" + said, "-c:v", "prores_ks", "-profile:v", "3", "-vendor", "apl0"] + tags + ["-r", str(FPS),
               "-t", "%.6f" % (total / FPS), a.master]
        mast = subprocess.Popen(mc, stdin=subprocess.PIPE)

    stills = set(int(v) for v in a.stills.split(",") if v.strip())
    thumbs, used = [], 0
    for index, s in enumerate(shots):
        frames, base, bg, opts = load_shot(st, s)
        used += 1 if frames else 0
        for k in range(s["dur"]):
            f = s["start"] + k
            img = compose(st, s, index, k, frames, base, bg, opts)
            if f in stills:
                img.save(os.path.splitext(a.out)[0] + "_f%04d.png" % f)
            if k == s["dur"] // 2:
                th = img.resize((256, 144), Image.LANCZOS)
                td = ImageDraw.Draw(th, "RGBA")
                td.rectangle([0, 118, 62, 144], fill=(0, 0, 0, 190))
                td.text((5, 121), s["id"], font=ImageFont.truetype(F_DIN, 22), fill=WHITE)
                thumbs.append(th)
            raw = img.tobytes()
            enc.stdin.write(raw)
            if mast:
                mast.stdin.write(raw)
    enc.stdin.close()
    if enc.wait() != 0:
        sys.exit("ffmpeg failed")
    if mast:
        mast.stdin.close()
        if mast.wait() != 0:
            sys.exit("ffmpeg failed on the master")

    cols = 10
    rows = (len(thumbs) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * 260 + 4, rows * 148 + 4), (12, 12, 14))
    for i, th in enumerate(thumbs):
        sheet.paste(th, (4 + (i % cols) * 260, 4 + (i // cols) * 148))
    sheet.save(os.path.splitext(a.out)[0] + "_sheet.jpg", quality=88)
    rr = read_report(st["events"], os.path.join(ROOT, "out", "read_report.md"))
    print("wrote %s: %d frames, %d shots, %d from clips, %d placeholders" % (a.out, total, len(shots), used, len(shots) - used))
    print("type events: %d, of which freeze-frame only: %d" % (len(rr), sum(1 for r in rr if r[5].startswith("freeze"))))


if __name__ == "__main__":
    main()
