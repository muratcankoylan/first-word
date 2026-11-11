#!/usr/bin/env python3
"""FIRST WORD: four figures of how the film was made, set as figures in a research paper are set.

    python3 tools/process_figures.py            all four -> out/process/figure_1..4.png
    python3 tools/process_figures.py 3          only the third

White page, panels lettered a, b, c, tables with three rules and no boxes, charts with one axis, a caption
under each figure. Everything shown is the project's own material: the user's messages (verbatim), the persona
prompt (persona/persona-prompt.md), the shot list, a real prompt, frames of the reels and of the finished film,
the stems, code from tools/, lines the checking tools printed, measurements of every mix, and the same moments
in eight of the fifteen versions in out/. Two "before" pictures in the fourth figure are kept in
out/process/src/ because the shots they show have since been fixed.

The first version of these (11 November 2026) was a dark board with large headlines; the user called it AI slop
and asked for something like a research paper. Charts follow the dataviz rules: bars no thicker than 24 px with
a rounded data end, one colour for one series, 2 px gaps between touching marks, text never in a data colour,
and the five-colour categorical set was run through the palette validator (it passes; three of the five are
light on white, so every use carries a text label).

Type: Helvetica for the figures, STIX General for the captions (both ship with macOS), IBM Plex Mono for code.
"""
import json
import os
import re
import subprocess
import sys
from collections import Counter

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
J = lambda *p: os.path.join(ROOT, *p)
W, H, M = 2400, 1350, 96
PAPER, INK, SEC, MUTED, GRID, HAIR = (255, 255, 255), (17, 17, 17), (74, 74, 72), (120, 120, 116), (226, 226, 222), (196, 196, 192)
BLUE = (42, 120, 214)                                                  # categorical slot 1: the one colour of a one-series chart
KINDS = (("gen", "Generated shot", (42, 120, 214)), ("macro", "Generated close-up", (235, 104, 52)), ("archive", "Real archive", (27, 175, 122)),
         ("code", "Drawn in code", (237, 161, 0)), ("ink", "Ink drawing", (232, 123, 164)))
KCOL = {k: c for k, _, c in KINDS}
HELV = "/System/Library/Fonts/Helvetica.ttc"
SUPP = "/System/Library/Fonts/Supplemental/"
FACES = {"r": (HELV, 0), "b": (HELV, 1), "i": (HELV, 2), "cap": (SUPP + "STIXGeneral.otf", 0), "capb": (SUPP + "STIXGeneralBol.otf", 0),
         "capi": (SUPP + "STIXGeneralItalic.otf", 0), "mono": (J("fonts", "IBMPlexMono-Regular.ttf"), 0)}
MASTER = J("out", "first_word_v015_1080.mp4")
_fonts = {}


def font(face, size):
    key = (face, size)
    if key not in _fonts:
        path, index = FACES[face]
        _fonts[key] = ImageFont.truetype(path, size, index=index)
    return _fonts[key]


# ------------------------------------------------------------------ text
def wrap(d, s, f, width):
    out = []
    for para in s.split("\n"):
        line = ""
        for word in para.split(" "):
            t = (line + " " + word).strip()
            if d.textlength(t, font=f) <= width or not line:
                line = t
            else:
                out.append(line)
                line = word
        out.append(line)
    return out


def clip_text(d, s, f, width):
    if d.textlength(s, font=f) <= width:
        return s
    while s and d.textlength(s + "…", font=f) > width:
        s = s[:-1]
    return s.rstrip(" ,.;:") + "…"


def panel(d, x, y, letter, title):
    """A panel's letter and what it shows, as a journal sets them. Returns where its content starts."""
    d.text((x, y), letter, font=font("b", 34), fill=INK)
    d.text((x + 40, y + 6), title, font=font("r", 26), fill=INK)
    return y + 58


def caption(d, y, n, lead, body):
    """The figure's caption: its number and one sentence in bold, then the panels in order. **x** is bold."""
    x0, width, size, leading = M, W - 2 * M, 31, 43
    toks = []
    for part in re.split(r"(\*\*.+?\*\*)", "**Figure %d. %s** %s" % (n, lead, body)):
        bold = part.startswith("**")
        for w in (part.strip("*") if bold else part).split(" "):
            if w:
                toks.append((w, "capb" if bold else "cap"))
    x = x0
    for w, face in toks:
        f = font(face, size)
        ww = d.textlength(w, font=f)
        if x + ww > x0 + width and x > x0:
            x, y = x0, y + leading
        d.text((x, y), w, font=f, fill=INK)
        x += ww + d.textlength(" ", font=f)
    return y + leading


def table(d, x, y, widths, head, rows, size=24, lead=31, faces=None, pad=11, right=()):
    """Three rules and no boxes. A cell wraps inside its column; a cell may be (text, swatch colour)."""
    faces = faces or ["r"] * len(widths)
    total = sum(widths)
    d.line([x, y, x + total, y], fill=INK, width=3)
    yy = y + pad
    cx = x
    for i, (w, h) in enumerate(zip(widths, head)):
        f = font("b", size)
        for k, line in enumerate(wrap(d, h, f, w - 18)):
            d.text((cx + w - 18 if i in right else cx, yy + k * lead), line, font=f, fill=INK, anchor="ra" if i in right else "la")
        cx += w
    hh = max(len(wrap(d, h, font("b", size), w - 18)) for w, h in zip(widths, head))
    yy += hh * lead + pad - 4
    d.line([x, yy, x + total, yy], fill=INK, width=1)
    yy += pad
    for row in rows:
        cx, tall = x, 1
        for i, (w, cell) in enumerate(zip(widths, row)):
            sw = None
            if isinstance(cell, tuple):
                cell, sw = cell
            f = font(faces[i], size - 3 if faces[i] == "mono" else size)
            off = 30 if sw else 0
            lines = wrap(d, str(cell), f, w - 18 - off)
            if sw:
                d.rectangle([cx, yy + 5, cx + 18, yy + 23], fill=sw)
            for k, line in enumerate(lines):
                d.text((cx + w - 18 if i in right else cx + off, yy + k * lead), line, font=f, fill=INK if i == 0 or faces[i] == "mono" else SEC, anchor="ra" if i in right else "la")
            tall = max(tall, len(lines))
            cx += w
        yy += tall * lead + pad
    d.line([x, yy, x + total, yy], fill=INK, width=3)
    return yy


def listing(d, x, y, width, lines, size=20, lead=29):
    """Code as a paper prints it: numbered lines on a faint ground, long lines broken with a mark."""
    f = font("mono", size)
    cw = d.textlength("m", font=f)
    room = int((width - 86) / cw)
    out = []
    for n, s in enumerate(lines, 1):
        s = s.rstrip()
        indent = len(s) - len(s.lstrip())
        first = True
        while True:
            if len(s) <= room:
                out.append((n if first else None, s))
                break
            cut = s.rfind(" ", 0, room)
            cut = cut if cut > indent + 8 else room
            out.append((n if first else None, s[:cut]))
            s = " " * (indent + 4) + s[cut:].lstrip()
            first = False
    h = 24 + lead * len(out)
    d.rectangle([x, y, x + width, y + h], fill=(246, 246, 243))
    for i, (n, s) in enumerate(out):
        yy = y + 12 + lead * i
        d.text((x + 50, yy), str(n) if n else "↪", font=f, fill=MUTED, anchor="ra")
        d.text((x + 70, yy), s, font=f, fill=INK)
    return y + h


# ------------------------------------------------------------------ pictures
def size_of(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height", "-of", "csv=p=0", path], capture_output=True, text=True).stdout.strip().split(",")
    return int(r[0]), int(r[1])


def grab(path, ns):
    ns = sorted(set(ns))
    w, h = size_of(path)
    sel = "+".join("eq(n\\,%d)" % n for n in ns)
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-vf", "select='%s'" % sel, "-vsync", "0", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
    a = np.frombuffer(raw, np.uint8).reshape(-1, h, w, 3)
    assert len(a) == len(ns), (path, len(a), ns)
    return {n: Image.fromarray(a[i]) for i, n in enumerate(ns)}


def fit(im, w, h):
    s = max(w / im.size[0], h / im.size[1])
    im = im.resize((max(w, int(round(im.size[0] * s))), max(h, int(round(im.size[1] * s)))), Image.LANCZOS)
    x, y = (im.size[0] - w) // 2, (im.size[1] - h) // 2
    return im.crop((x, y, x + w, y + h))


def place(img, im, x, y):
    img.paste(im, (x, y))
    ImageDraw.Draw(img).rectangle([x, y, x + im.size[0] - 1, y + im.size[1] - 1], outline=HAIR)


def kind(src):
    if "ARCHIVE" in src:
        return "archive"
    if src.startswith("MACRO"):
        return "macro"
    if src.startswith("INK"):
        return "ink"
    if src.startswith("CODE") and "GEN" not in src:
        return "code"
    return "gen"


def shots():
    return json.load(open(J("shotlist.json")))["shots"]


def page():
    img = Image.new("RGB", (W, H), PAPER)
    return img, ImageDraw.Draw(img)


def hbar(d, x0, y, length, thick=22, color=BLUE):
    """A bar from a baseline at x0: square at the baseline, rounded at the data end."""
    if length >= 6:
        d.rounded_rectangle([x0, y, x0 + length, y + thick], radius=4, fill=color, corners=(False, True, True, False))
    else:
        d.rectangle([x0, y, x0 + max(1, length), y + thick], fill=color)


# ------------------------------------------------------------------ figure 1
def figure1():
    img, d = page()
    # a: what the user wrote
    y = panel(d, M, 70, "a", "What the user wrote (10 November 2026)")
    rows = [("17:05", "“The end goal is to create a video about AI and futurism, create a buzz, and create some excitement in the user, in the viewer.”", "Analysed the five reference films attached to it"),
            ("17:21", "“I want you to write a persona prompt that will be creating this video. This is basically a creator who reads futuristic books like Ender’s Game, Asimov, or maybe books like The Beginning of Infinity, believes in futurism, is a techno-optimist, and listens to things like Grimes.”", "Ran deep research on those books and records, then wrote the persona prompt (b, c)"),
            ("20:20", "“approved […] you decide everything after that”", "Made the film from the plan (d)")]
    table(d, M, y, [104, 560, 250], ["UTC", "Message, verbatim", "What the agent did next"], rows, size=24, lead=31, faces=["r", "i", "r"])
    # b: the persona's settings
    bx = 1090
    y = panel(d, bx, 70, "b", "The six settings of the persona prompt the agent wrote for itself")
    t = open(J("persona", "persona-prompt.md")).read()
    dials = [[c.strip() for c in l.strip("|").split("|")] for l in t.split("\n") if re.match(r"\| [A-Z][a-z ]+ \| \d+ \|", l)]
    table(d, bx, y, [270, 110, 396, 438], ["Dial", "Set to (1 to 10)", "At 1", "At 10"], dials, size=24, lead=31)
    # c: how long each part of it is
    cy = 640
    y = panel(d, M, cy, "c", "Length of each section of the 3,801-word prompt")
    parts = re.split(r"\n(?=## )", t)
    names = {"Settings": "Settings", "Who you are": "Who you are", "What you believe": "What you believe", "What you argue": "What you argue with yourself about",
             "Taste": "Taste: eyes, ears, hands", "Voice": "Voice", "Keyword bank": "Keyword bank", "The film": "The film (the assignment)", "How you work": "How you work"}
    data = [("Preamble", len(parts[0].split()))]
    for p in parts[1:]:
        head = p.split("\n")[0][3:]
        data.append((next(v for k, v in names.items() if head.startswith(k)), len(p.split())))
    x0, x1 = M + 400, M + 400 + 420
    top = y + 4
    step = 40
    for v in (0, 200, 400, 600, 800):
        gx = x0 + (x1 - x0) * v / 800.0
        d.line([gx, top - 4, gx, top + step * len(data)], fill=GRID if v else MUTED, width=1)
        d.text((gx, top + step * len(data) + 10), str(v), font=font("r", 22), fill=SEC, anchor="ma")
    for i, (name, n) in enumerate(data):
        yy = top + i * step + 6
        d.text((x0 - 16, yy + 11), name, font=font("r", 24), fill=INK, anchor="rm")
        hbar(d, x0, yy, (x1 - x0) * n / 800.0)
        d.text((x0 + (x1 - x0) * n / 800.0 + 10, yy + 11), str(n), font=font("r", 22), fill=SEC, anchor="lm")
    d.text(((x0 + x1) / 2, top + step * len(data) + 42), "Words", font=font("r", 23), fill=SEC, anchor="ma")
    # d: the plan written from it
    dx = 1090
    y = panel(d, dx, cy, "d", "Nine of the 98 rows of the shot list written from it")
    by = {s["id"]: s for s in shots()}
    kname = dict((k, n) for k, n, _ in KINDS)
    rows = []
    for sid in ("A01", "B04", "C01", "D09", "D16", "F03", "G04", "G31", "H03"):
        s = by[sid]
        pic = clip_text(d, s["picture"], font("r", 23), 600)
        rows.append((sid, "%.2f" % (s["start"] / 24.0), str(s["dur"]), (kname[kind(s["source"])], KCOL[kind(s["source"])]), pic))
    table(d, dx, y, [84, 104, 104, 300, 622], ["Shot", "In (s)", "Frames", "Made by", "Picture"], rows, size=23, lead=30, pad=8, right=(1, 2))
    caption(d, 1180, 1, "From one message to a shot plan.",
            "**a,** The user’s messages that set the film up, with what the agent did after each (one dictation error corrected: “Anders Game”). "
            "**b,** The persona is a way of judging work: six dials with both ends described. **c,** Its sections, in the order they are written. "
            "**d,** The plan that persona wrote: 98 shots, 1,440 frames at 24 frames a second, cut on a 144 BPM grid.")
    return img


# ------------------------------------------------------------------ figure 2
def figure2():
    img, d = page()
    job = json.load(open(J("timing", "generations.json")))
    job = job.get("jobs", job)
    # a: references
    y = panel(d, M, 70, "a", "Reference images generated first: places and objects, never faces")
    tw, th, gap = 222, 125, 14
    for i, n in enumerate(("wall", "jacket", "hall", "kitchen", "rooftop", "tube")):
        place(img, fit(Image.open(J("refs", n + ".jpg")).convert("RGB"), tw, th), M + i * (tw + gap), y)
        d.text((M + i * (tw + gap), y + th + 8), n.capitalize(), font=font("r", 23), fill=SEC)
    # b: a prompt
    y = panel(d, M, y + th + 62, "b", "Opening of one reel’s prompt, as sent")
    text = job["mara_reel"]["body"]["promptText"].split("\n")[0]
    lw = 6 * tw + 5 * gap
    f = font("mono", 20)
    lines = wrap(d, text, f, lw - 40)
    d.rectangle([M, y, M + lw, y + 22 + 29 * len(lines)], fill=(246, 246, 243))
    for i, line in enumerate(lines):
        d.text((M + 20, y + 11 + 29 * i), line, font=f, fill=INK)
    # c: what each reel was given
    cx = 1580
    yc = panel(d, cx, 70, "c", "What each cast reel was given")
    rows = []
    for k, who in (("mara_reel", "Mara"), ("ray_reel", "Ray"), ("jun_reel", "Jun"), ("osei_reel", "Osei"), ("amara_dev_reel", "Amara, Dev"), ("rosa_pip_reel", "Rosa, Pip")):
        fl = job[k].get("files") or {}
        rows.append((who, str(len(fl.get("references", []))), str(len(fl.get("referenceAudio", []))), str(job[k]["body"]["duration"])))
    table(d, cx, yc, [226, 166, 166, 166], ["Reel", "Reference images", "Voice lines as audio", "Length (s)"], rows, size=24, lead=30, pad=8, right=(1, 2, 3))
    # d: the cast
    y2 = 500
    y = panel(d, M, y2, "d", "The cast in the finished film: one reel per person, so a face stays the same face")
    cast = [("Mara", 110, (0.50, 0.41), 860), ("Ray", 397, (0.493, 0.33), 440), ("Jun", 332, (0.50, 0.35), 440), ("Osei", 862, (0.51, 0.35), 500),
            ("Amara", 1055, (0.49, 0.43), 500), ("Dev", 1070, (0.505, 0.46), 640), ("Rosa", 892, (0.36, 0.34), 320), ("Pip", 940, (0.52, 0.44), 840)]
    fr = grab(MASTER, [c[1] for c in cast])
    pw = (lw - 7 * 14) // 8
    for i, (name, fno, (cx0, cy0), s) in enumerate(cast):
        x0 = int(min(max(cx0 * 1920 - s / 2, 0), 1920 - s))
        y0 = int(min(max(cy0 * 1080 - s / 2, 0), 1080 - s))
        place(img, fr[fno].crop((x0, y0, x0 + s, y0 + s)).resize((pw, pw), Image.LANCZOS), M + i * (pw + 14), y)
        d.text((M + i * (pw + 14), y + pw + 8), name, font=font("r", 23), fill=SEC)
    # e: a draft and the same take finished
    ye = panel(d, cx, y2, "e", "One frame: 480p draft, and the take finished at 1080p")
    idx = int(round(8.898 * 24)) + 7
    tw2, th2 = (724 - 16) // 2, 250
    box = (0.36, 0.235, 0.66, 0.235 + 0.30 * 16 * th2 / (9.0 * tw2))
    for k, (path, how, name) in enumerate(((J("clips", "drafts", "rosa_pip_reel.mp4"), Image.BICUBIC, "854 × 480"), (J("clips", "final", "rosa_pip_reel.mp4"), Image.LANCZOS, "1920 × 1080"))):
        im = grab(path, [idx])[idx]
        iw, ih = im.size
        place(img, im.crop((int(box[0] * iw), int(box[1] * ih), int(box[2] * iw), int(box[3] * ih))).resize((tw2, th2), how), cx + k * (tw2 + 16), ye)
        d.text((cx + k * (tw2 + 16), ye + th2 + 8), name, font=font("r", 23), fill=SEC)
    # f: the stems
    y3 = 870
    y = panel(d, M, y3, "f", "Amplitude of the four stems of the mix")
    px0, px1 = M + 150, M + lw
    rowh = 46
    for i, (name, cap) in enumerate((("dialogue", "Dialogue"), ("effects", "Effects"), ("score", "Score"), ("whale", "Whale"))):
        raw = subprocess.run(["ffmpeg", "-v", "error", "-i", J("audio", "stems", name + ".wav"), "-ac", "1", "-ar", "8000", "-f", "f32le", "-"], capture_output=True).stdout
        x = np.abs(np.frombuffer(raw, np.float32))
        ww = px1 - px0
        n = len(x) // ww
        env = x[: n * ww].reshape(ww, n).max(axis=1)
        env = env / max(1e-6, float(np.percentile(env, 99.7)))
        mid = y + i * rowh + rowh // 2
        d.text((px0 - 16, mid), cap, font=font("r", 24), fill=INK, anchor="rm")
        d.line([px0, mid, px1, mid], fill=GRID, width=1)
        for k in range(ww):
            v = int(min(1.0, float(env[k])) * (rowh // 2 - 3))
            if v:
                d.line([px0 + k, mid - v, px0 + k, mid + v], fill=BLUE)
    ay = y + 4 * rowh + 4
    d.line([px0, ay, px1, ay], fill=MUTED, width=1)
    for s in range(0, 61, 10):
        gx = px0 + (px1 - px0) * s / 60.0
        d.line([gx, ay, gx, ay + 8], fill=MUTED, width=1)
        d.text((gx, ay + 12), "%d s" % s, font=font("r", 22), fill=SEC, anchor="ma")
    # g: where each comes from
    yg = panel(d, cx, y3, "g", "Where each stem comes from")
    rows = [("Dialogue", "11 library voices of real people, performed as 9 scenes"), ("Effects", "95 generated files, each measured on arrival"),
            ("Score", "1 generated theme (3 takes), cut to the picture"), ("Whale", "A real recording of sperm whale clicks (NOAA)")]
    table(d, cx, yg, [150, 574], ["Stem", "Source"], rows, size=23, lead=29, pad=7)
    caption(d, 1212, 2, "Generation.",
            "**a, b,** Places and objects are fixed by reference images; the prompt binds them, and the finished voice lines, by name. "
            "**c, d,** Each person comes from a single job. **e,** Drafts were reviewed at 480p; the takes kept were then finished at 1080p. "
            "**f, g,** The sound. Video: Seedance 2.5 on Runway. Voices, effects and score: ElevenLabs.")
    return img


# ------------------------------------------------------------------ figure 3
def figure3():
    img, d = page()
    # a: a transition as code
    y = panel(d, M, 70, "a", "A transition is a function: the impact (tools/light.py)")
    src = open(J("tools", "light.py")).read().split("\n")
    a = next(i for i, l in enumerate(src) if l.startswith("def shock"))
    body = [l for l in src[a:a + 13] if l.strip()]
    listing(d, M, y, 1090, body, size=19, lead=27)
    # b: animation
    bx = 1270
    y = panel(d, bx, 70, "b", "Animation drawn in code")
    tw, th, gap = 331, 186, 20
    plate = grab(J("clips", "final", "hall_fan.mp4"), [258])[258]
    done = grab(J("clips", "B06.mp4"), [11])[11]
    ring = grab(MASTER, [22])[22]
    for i, (im, cap) in enumerate(((plate, "Generated shot"), (done, "200 paper strips flown through it"), (ring, "Cursor of light, a ring per click"))):
        place(img, im.resize((tw, th), Image.LANCZOS), bx + i * (tw + gap), y)
        d.text((bx + i * (tw + gap), y + th + 8), cap, font=font("r", 22), fill=SEC)
    # c: how long the shots are
    y = panel(d, bx, y + th + 58, "c", "Shot length: 46 of the 98 shots last five frames")
    cnt = Counter(s["dur"] for s in shots())
    x0, x1, base, top = bx + 60, bx + 3 * tw + 2 * gap, y + 150, y + 6
    for v in (0, 20, 40):
        gy = base - (base - top) * v / 50.0
        d.line([x0, gy, x1, gy], fill=GRID if v else MUTED, width=1)
        d.text((x0 - 12, gy), str(v), font=font("r", 21), fill=SEC, anchor="rm")
    for dur, n in sorted(cnt.items()):
        gx = x0 + (x1 - x0 - 30) * (dur - 2) / 60.0 + 14
        hh = (base - top) * n / 50.0
        if hh >= 6:
            d.rounded_rectangle([gx - 6, base - hh, gx + 6, base], radius=4, fill=BLUE, corners=(True, True, False, False))
        else:
            d.rectangle([gx - 6, base - max(2, hh), gx + 6, base], fill=BLUE)
        if n == max(cnt.values()):
            d.text((gx + 14, base - hh + 2), str(n), font=font("r", 21), fill=SEC)
    for dur in range(5, 61, 5):
        gx = x0 + (x1 - x0 - 30) * (dur - 2) / 60.0 + 14
        d.text((gx, base + 8), str(dur), font=font("r", 21), fill=SEC, anchor="ma")
    d.text((x1, base + 36), "Shot length (frames)", font=font("r", 22), fill=SEC, anchor="ra")
    # d: transitions
    y = panel(d, M, 610, "d", "Six transitions, four frames of each (frame numbers below)")
    strips = (("Whip tilt", [1258, 1260, 1262, 1264]), ("Television switching off", [315, 316, 317, 318]), ("Impact: the colours pulled apart", [1409, 1410, 1411, 1412]),
              ("Glitch on the word that crashed", [1195, 1196, 1197, 1198]), ("Picture rolling into place", [440, 441, 442, 443]), ("Baton becoming the cursor", [1376, 1379, 1381, 1387]))
    fr = grab(MASTER, [f for _, fs in strips for f in fs])
    sw = (W - 2 * M - 2 * 48) // 3
    fw = (sw - 3 * 6) // 4
    fh = fw * 9 // 16
    rowh = 30 + fh + 30 + 10
    for i, (name, fs) in enumerate(strips):
        x0 = M + (i % 3) * (sw + 48)
        y0 = y + (i // 3) * rowh
        d.text((x0, y0), name, font=font("r", 23), fill=INK)
        for j, fno in enumerate(fs):
            place(img, fr[fno].resize((fw, fh), Image.LANCZOS), x0 + j * (fw + 6), y0 + 30)
            d.text((x0 + j * (fw + 6), y0 + 30 + fh + 4), str(fno), font=font("r", 19), fill=MUTED)
    # e: the edit
    title = "The edit: every shot in order, by how it was made"
    y = panel(d, M, y + 2 * rowh + 6, "e", title)
    lx = M + 40 + d.textlength(title, font=font("r", 26)) + 50
    ss = shots()
    kc = Counter(kind(s["source"]) for s in ss)
    for k, name, col in KINDS:
        d.rectangle([lx, y - 46, lx + 18, y - 28], fill=col)
        t = "%s (%d)" % (name, kc[k])
        d.text((lx + 26, y - 50), t, font=font("r", 22), fill=SEC)
        lx += 26 + d.textlength(t, font=font("r", 22)) + 30
    gx, gw = M, W - 2 * M
    for s in ss:
        x0 = gx + gw * s["start"] / 1440.0
        x1 = gx + gw * (s["start"] + s["dur"]) / 1440.0
        d.rectangle([x0, y, x1 - 2, y + 40], fill=KCOL[kind(s["source"])])
    ay = y + 48
    d.line([gx, ay, gx + gw, ay], fill=MUTED, width=1)
    for b in range(0, 1441, 40):                                       # one bar of the 144 BPM grid is forty frames
        x = gx + gw * b / 1440.0
        d.line([x, ay, x, ay + 5], fill=MUTED, width=1)
    for s in range(0, 61, 10):
        x = gx + gw * s / 60.0
        d.line([x, ay, x, ay + 11], fill=INK, width=1)
        d.text((x, ay + 14), "%d s" % s, font=font("r", 21), fill=SEC, anchor="ma" if 0 < s < 60 else ("la" if s == 0 else "ra"))
    caption(d, 1222, 3, "The edit is code.",
            "About 7,000 lines of Python and no editing timeline. **a,** Each transition is a function applied to the frame. **b,** Animation is drawn over generated shots. "
            "**c, e,** Cuts sit on a 144 BPM grid (small ticks in **e** are bars of forty frames). **d,** From the finished film.")
    return img


# ------------------------------------------------------------------ figure 4
def figure4():
    img, d = page()
    y = panel(d, M, 70, "a", "Two moments of the film in eight of its fifteen versions")
    vers = [1, 3, 5, 7, 9, 11, 13, 15]
    frames = [160, 1430]
    x0 = M + 110
    gap = 10
    tw = (W - M - x0 - 7 * gap) // 8
    th = tw * 9 // 16
    for j, v in enumerate(vers):
        fr = grab(J("out", "animatic_v%03d.mp4" % v), frames)
        x = x0 + j * (tw + gap)
        d.text((x, y), "v%d" % v, font=font("b" if v == 15 else "r", 24), fill=INK)
        for i, fno in enumerate(frames):
            place(img, fr[fno].resize((tw, th), Image.LANCZOS), x, y + 34 + i * (th + gap))
    for i, fno in enumerate(frames):
        d.text((M, y + 34 + i * (th + gap) + th // 2), "%.1f s" % (fno / 24.0), font=font("r", 24), fill=SEC, anchor="lm")
    y2 = y + 34 + 2 * (th + gap) + 30
    # b: the checks
    yb = panel(d, M, y2, "b", "Checks the agent wrote for itself, and a line each one printed")
    rows = [("Reading speed", "0:01.25 | A01 | “already decided.” | 10 | 34 | freeze-frame only"),
            ("Lip sync", "D01 … line jun1, 5 of 6 words on screen, worst slip 1.0 frames"),
            ("Loudness", "loudness -14.1 LUFS, range 6.8 LU, true peak -2.1 dBFS"),
            ("1080p against draft", "E05 845+35 GEN likeness mean 0.992 … detail 8.4 vs 5.2 (x1.63)"),
            ("Colour", "frame 372: mean shift R -0.01 G -0.00 B -0.00; mean error 0.82 of 255"),
            ("Stray frames", "C04  frame 319 is black (shot median 97)")]
    ye = table(d, M, yb, [230, 920], ["Check", "Line printed"], rows, size=24, lead=30, faces=["r", "mono"], pad=7)
    # e: the user's notes
    yn = panel(d, M, ye + 30, "e", "Three of the user’s notes, and what changed")
    rows = [("10 Nov, 22:03", "“These are real AI voices. You need to write better prompts and use the latest ElevenLabs model.”", "Recast with real people’s voices, performed as scenes"),
            ("11 Nov, 04:23", "“The dumb question needs to be written on the screen, so it needs to come from the video.”", "The laptop’s words are in the generated shot itself"),
            ("11 Nov, 06:06", "“These writings are great, but they are passing so fast.”", "Each paper strip now hangs for about a second")]
    table(d, M, yn, [190, 560, 400], ["UTC", "Note, verbatim", "Change"], rows, size=23, lead=29, faces=["r", "i", "r"], pad=7)
    # c: the mix, measured
    cx = 1330
    yc = panel(d, cx, y2, "c", "Every mix, measured")
    rows = [("v4 to v8", "−13.5 to −13.6", "7.9 to 8.5", "−1.0"), ("v9, v10", "−14.0 to −14.1", "7.4", "−1.9"), ("v11 to v15", "−14.1", "6.8", "−2.1")]
    ye = table(d, cx, yc, [200, 270, 240, 264], ["Versions", "Loudness (LUFS)", "Range (LU)", "True peak (dBFS)"], rows, size=24, lead=30, pad=7, right=(1, 2, 3))
    # d: two faults, before and after
    yd = panel(d, cx, ye + 30, "d", "Two faults found at full size, before and after the code change")
    src = J("out", "process", "src")
    hh = min(1146 - yd, 260)                                           # no taller than the cursor picture has pixels for
    before = Image.open(os.path.join(src, "strip_before.png")).convert("RGB")
    after = grab(J("clips", "B06.mp4"), [11])[11].crop((120, 180, 1020, 440)).resize((1800, 520), Image.NEAREST)
    cb = Image.open(os.path.join(src, "cursor_before.png")).convert("RGB")
    ca = grab(J("clips", "F03.mp4"), [12])[12].crop((880, 400, 1400, 800)).resize((1040, 800), Image.NEAREST)
    sw, cw = 600, 170
    sh = (hh - 12) // 2
    for k, im in enumerate((before, after)):                           # the strip: before above, after below
        place(img, fit(im.crop((700, 160, 1760, 160 + int(1060 * sh / sw))), sw, sh), cx, yd + k * (sh + 12))
    d.text((cx, yd + hh + 6), "Strip text: before (top), after", font=font("r", 22), fill=SEC)
    x = cx + sw + 22
    for im, cap in ((cb, "Cursor, before"), (ca, "after")):
        place(img, fit(im.crop((470 - 230, 390 - int(230 * hh / cw), 470 + 230, 390 + int(230 * hh / cw))), cw, hh), x, yd)
        d.text((x, yd + hh + 6), cap, font=font("r", 22), fill=SEC)
        x += cw + 11
    caption(d, 1212, 4, "The checking loop.",
            "The agent cannot hear and cannot watch video play, so it judges sound by measurement and picture by still frames. "
            "**a,** Grey cards are shots not yet made. **b,** Lines are verbatim. **c,** The mix converges on −14 LUFS with headroom. "
            "**d,** The years on the paper strips were striped; the laptop’s cursor sat in a pale box. **e,** The user’s notes are the other half of the loop.")
    return img


def main():
    os.makedirs(J("out", "process"), exist_ok=True)
    figs = {1: figure1, 2: figure2, 3: figure3, 4: figure4}
    for n in [int(v) for v in sys.argv[1:]] or [1, 2, 3, 4]:
        out = J("out", "process", "figure_%d.png" % n)
        figs[n]().save(out, optimize=True)
        print("wrote", os.path.relpath(out, ROOT), "%.1f MB" % (os.path.getsize(out) / 1e6))


if __name__ == "__main__":
    main()
