#!/usr/bin/env python3
"""FIRST WORD: the scanline pass. Everything real takes it, and nothing else does.

Turns a public-domain still into a shot: a slow move across it, then scanlines, a one-pixel colour split,
a little bloom, grain and a vignette, as if the past were playing on a monitor in the hall.

    python3 tools/scanlines.py SRC OUT.mp4 --frames 25 --start x0,y0,w --end x0,y0,w [--size 1280x720] [--roll]
    python3 tools/scanlines.py CLIP.mp4 OUT.mp4 --at 6.5 --frames 5 --start 0,0,1280 --end 20,11,1240

--marks adds the red wax pencil: our own underline or ring on a real page. It is drawn over the picture, after
the scanlines, because it is not part of the real thing.

start and end are crops of the source in its own pixels (left, top, width; height follows the output shape).
"""
import argparse
import json
import subprocess

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

Image.MAX_IMAGE_PIXELS = None


def look(img, k, rng, roll=0.0):
    a = np.asarray(img).astype(np.float32) / 255
    h, w = a.shape[:2]
    lum = a.mean(axis=2, keepdims=True)
    a = lum + (a - lum) * 0.82                                   # a little less colour than life
    bloom = np.asarray(img.filter(ImageFilter.GaussianBlur(6 * k))).astype(np.float32) / 255
    a = a + 0.22 * np.maximum(bloom - 0.55, 0)
    a[..., 0] = np.roll(a[..., 0], -max(1, int(round(k))), axis=1)   # the colour split of a tube
    a[..., 2] = np.roll(a[..., 2], max(1, int(round(k))), axis=1)
    period = max(2.0, 3.0 * k)
    lines = 0.80 + 0.20 * np.cos(np.arange(h) * 2 * np.pi / period)
    a = a * lines[:, None, None]
    if roll > 0:                                                 # the picture finds its vertical hold
        a = np.roll(a, int(roll * h), axis=0)
        bar = int(roll * h)
        a[max(0, bar - int(8 * k)): bar + int(8 * k)] *= 0.25
    a = a + rng.normal(0, 0.018, a.shape).astype(np.float32)
    yy, xx = np.mgrid[0:h, 0:w]
    vig = 1 - 0.35 * (((xx - w / 2) / (w / 2)) ** 2 + ((yy - h / 2) / (h / 2)) ** 2) ** 1.2
    a = a * vig[..., None]
    return (np.clip(a, 0, 1) * 255).astype(np.uint8)


RED = (224, 44, 40)


def wax(img, marks, f, to_out, k):
    """The red wax pencil: our own marks on a real page, drawn over the picture and never under the scanlines.

    A mark is a line (a, b) or an ellipse (centre c, radii r), in the source's own pixels, drawn from frame
    `from` to frame `to` of the shot."""
    if not marks:
        return img
    rng = np.random.default_rng(7)
    layer = Image.new("L", img.size, 0)
    d = ImageDraw.Draw(layer)
    for m in marks:
        t = (f - m["from"] + 1) / max(1, m["to"] - m["from"])
        jit = np.convolve(rng.normal(0, 1.0, 420), np.ones(9) / 3.0, mode="same")[10:410]   # a slow wobble, the same on every frame
        if t <= 0:
            continue
        t = min(1.0, t)
        if m["kind"] == "line":
            n = 60
            pts = [(m["a"][0] + (m["b"][0] - m["a"][0]) * i / n, m["a"][1] + (m["b"][1] - m["a"][1]) * i / n + jit[i] * m.get("wobble", 1.5)) for i in range(n + 1)]
        else:
            n = 140
            a0 = np.radians(m.get("start", 200))
            pts = [(m["c"][0] + (m["r"][0] + jit[i] * 3) * np.cos(a0 + 2 * np.pi * 1.07 * i / n),
                    m["c"][1] + (m["r"][1] + jit[i + 150] * 2 + 10 * i / n) * np.sin(a0 + 2 * np.pi * 1.07 * i / n)) for i in range(n + 1)]
        pts = [to_out(p) for p in pts[: max(2, int(round(len(pts) * t)))]]
        wd = m.get("width", 9) * k
        for i in range(len(pts) - 1):
            d.line([pts[i], pts[i + 1]], fill=255, width=max(2, int(round(wd * (0.85 + 0.3 * abs(jit[i + 200]) / 2)))))
        for p in pts:
            d.ellipse([p[0] - wd / 2, p[1] - wd / 2, p[0] + wd / 2, p[1] + wd / 2], fill=255)
    a = np.asarray(layer).astype(np.float32) / 255
    grain = np.random.default_rng(11).random(a.shape).astype(np.float32)   # wax skips on the paper's tooth
    a = a * (0.72 + 0.28 * (grain > 0.22)) * 0.93
    base = np.asarray(img).astype(np.float32)
    out = base * (1 - a[..., None]) + np.array(RED, np.float32) * a[..., None]
    return Image.fromarray(out.astype(np.uint8))


import os
F_ROMAN = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "fonts", "Cinzel-Variable.ttf")   # Roman capitals, OFL


def letters(img, marks, f, to_out, zoom):
    """Letters set on a real photograph in its own space: a restoration carried on past a break.

    A mark of kind "text" gives the words, where the first letter stands (at: left and baseline, in the source's
    pixels), the height of a capital and the pitch from letter to letter in those pixels, the frame the first
    letter lands on and how many land on each frame. They are drawn over the scanlines: they are not the object."""
    todo = [m for m in marks if m["kind"] == "text" and f >= m["from"]]
    if not todo:
        return img
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    for m in todo:
        size = 10
        probe = ImageFont.truetype(F_ROMAN, 400)
        box = probe.getbbox("H")
        size = max(6, int(round(m["cap"] * zoom * 400 / (box[3] - box[1]))))
        font = ImageFont.truetype(F_ROMAN, size)
        shown = min(len(m["text"]), int(m.get("per_frame", 2) * (f - m["from"] + 1)))
        x = m["at"][0]
        for ch in m["text"][:shown]:
            step = m["pitch"] * (0.45 if ch in "· " else 1.0)
            if ch != " ":
                cx, base = to_out((x + step / 2, m["at"][1]))
                wd = d.textlength(ch, font=font)
                d.text((cx - wd / 2, base), ch, font=font, fill=tuple(m.get("color", [88, 92, 100])) + (225,), anchor="ls")
            x += step
    return Image.alpha_composite(img.convert("RGBA"), layer).convert("RGB")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("out")
    ap.add_argument("--frames", type=int, default=24)
    ap.add_argument("--start", required=True)
    ap.add_argument("--end", required=True)
    ap.add_argument("--size", default="1280x720")
    ap.add_argument("--roll", action="store_true", help="open with the picture rolling into place")
    ap.add_argument("--roll-frames", type=int, default=5, help="how many frames the roll takes")
    ap.add_argument("--at", type=float, default=0.0, help="for a film clip: the second it is taken from")
    ap.add_argument("--marks", default="", help="JSON list of red wax pencil marks, in the source's pixels and the shot's frames")
    a = ap.parse_args()
    W, H = [int(v) for v in a.size.split("x")]
    k = H / 720.0
    stills = None
    if a.src.lower().endswith((".mp4", ".mov", ".m4v", ".webm")):       # a real film clip: the same pass, frame by frame
        probe = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height",
                                "-of", "csv=p=0", a.src], capture_output=True, text=True).stdout.strip().split(",")
        sw, sh = int(probe[0]), int(probe[1])
        raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(a.at), "-i", a.src, "-frames:v", str(a.frames), "-vf", "fps=24",
                              "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
        stills = [Image.frombytes("RGB", (sw, sh), raw[i * sw * sh * 3:(i + 1) * sw * sh * 3]) for i in range(len(raw) // (sw * sh * 3))]
        while len(stills) < a.frames:
            stills.append(stills[-1])
        src = stills[0]
    else:
        src = Image.open(a.src).convert("RGB")
    s, e = [[float(v) for v in t.split(",")] for t in (a.start, a.end)]
    rng = np.random.default_rng(1903)
    marks = json.loads(a.marks) if a.marks else []
    enc = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "%dx%d" % (W, H), "-r", "24", "-i", "-",
                            "-c:v", "libx264", "-preset", "medium", "-crf", "16", "-pix_fmt", "yuv420p", a.out], stdin=subprocess.PIPE)
    for f in range(a.frames):
        t = f / max(1, a.frames - 1)
        t = t * t * (3 - 2 * t) * 0.5 + t * 0.5                  # eased, but never stops
        x0, y0, w = [s[i] + (e[i] - s[i]) * t for i in range(3)]
        h = w * H / W
        frame = (stills[f] if stills else src).resize((W, H), Image.LANCZOS, box=(x0, y0, x0 + w, y0 + h))
        roll = max(0.0, 1 - f / float(a.roll_frames)) * 0.6 if a.roll else 0.0
        out = Image.fromarray(look(frame, k, rng, roll))
        out = wax(out, [m for m in marks if m["kind"] != "text"], f, lambda p: ((p[0] - x0) / w * W, (p[1] - y0) / h * H), k)
        out = letters(out, marks, f, lambda p: ((p[0] - x0) / w * W, (p[1] - y0) / h * H), W / w)
        enc.stdin.write(out.tobytes())
    enc.stdin.close()
    enc.wait()
    print("wrote", a.out, a.frames, "frames")


if __name__ == "__main__":
    main()
