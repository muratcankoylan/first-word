#!/usr/bin/env python3
"""FIRST WORD: the wind. Paper strips carrying printed predictions, blown through the hall.

    python3 tools/wind.py            every shot in timing/wind.json
    python3 tools/wind.py B04        one shot
    python3 tools/wind.py --size 1920x1080

For each shot the tool takes its plate (a generated clip, framed as timing/wind.json says), flies about two
hundred strips of paper through a 3D tunnel in front of it, and writes clips/<ID>.mp4. The camera sits at the
origin looking down the hall. Most strips are small and blank at this size. A few pass close and slowly enough
to be read: those carry the predictions, and only the ones in timing/wind.json, each of which is a short dated
quotation or a common saying checked in the plan's source table.

B08 is different: a macro of the paper in her fingers. There the paper is found in every frame and the type is
laid on it: along a strip ("paper" left out), or inside the four corners of a card ("paper": "card"), which is
what her reel shows on her cheek and in her hand.

Depth is faked the cheap way: far strips are drawn only where the plate is lit, so they vanish behind her
silhouette and the benches; near strips pass in front of everything and are blurred, as a lens would blur them.
"""
import argparse
import json
import math
import os
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import conform as C  # noqa: E402

ROOT = C.ROOT
F_PRINT = os.path.join(ROOT, "fonts", "BarlowCondensed-Bold.ttf")
F_YEAR = os.path.join(ROOT, "fonts", "BarlowCondensed-SemiBold.ttf")   # not the mono: its dotted zero reads as an eight in motion
F_HAND = os.path.join(ROOT, "fonts", "Kalam-Bold.ttf")
PAPER = (238, 240, 234)
SUB = 14                   # sub-frames per frame at 720 lines: the motion blur. More at a larger size (see render)
SHUTTER = 0.5              # the share of each frame the shutter is open: half, as a film camera's is. Until the 1080p
                           # pass it was the whole frame, and the ends of a turning strip smeared across 16 pixels: the
                           # year on it could not be read, and at 1080 lines the 14 steps of the smear showed as stripes


def texture(text, year, hand=None, w=1500, h=150, tint=(0.80, 0.95, 0.97), big=False):
    """One strip of paper, printed. Quotation marks are part of the text when the words are someone's."""
    rng = np.random.default_rng(abs(hash(text)) % (2 ** 31))
    a = np.full((h, w, 3), PAPER, np.float32) + rng.normal(0, 3.0, (h, w, 1))
    a *= np.array(tint, np.float32)[None, None, :]                     # the hall's light on the paper
    a *= (0.90 + 0.10 * np.cos(np.linspace(-1.2, 1.2, h)))[:, None, None]   # a little roll across its width
    im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert("RGBA")
    d = ImageDraw.Draw(im)
    size = int(h * (0.56 if not big else 0.74))
    f = ImageFont.truetype(F_PRINT, size)
    fy = ImageFont.truetype(F_YEAR, int(h * 0.44))
    yw = d.textlength(year, font=fy) if year else 0
    fh = ImageFont.truetype(F_HAND, int(h * (0.44 if not big else 0.66))) if hand else None
    room = w - int(h * 0.5) - (yw + h * 0.5 if year else 0) - (d.textlength(hand, font=fh) + h * 0.5 if hand else 0)
    while d.textlength(text, font=f) > room and size > 20:
        size -= 3
        f = ImageFont.truetype(F_PRINT, size)
    d.text((h * 0.25, h * 0.50), text, font=f, fill=(18, 22, 30, 255), anchor="lm")
    if year:
        d.text((w - h * 0.25, h * 0.52), year, font=fy, fill=(18, 22, 30, 255), anchor="rm")
    if hand:
        x = h * 0.25 + d.textlength(text, font=f) + h * 0.35
        d.text((x, h * 0.58), hand, font=fh, fill=(22, 34, 66, 255), anchor="lm")
    return im


def coeffs(dst, src):
    """Perspective coefficients for PIL: the picture point for each output point."""
    m = []
    for (x, y), (u, v) in zip(dst, src):
        m.append([x, y, 1, 0, 0, 0, -u * x, -u * y])
        m.append([0, 0, 0, x, y, 1, -v * x, -v * y])
    b = np.array(src, np.float64).reshape(8)
    return np.linalg.solve(np.array(m, np.float64), b)


def project(p, W, H, focal, vp=(0.5, 0.5)):
    z = np.maximum(p[..., 2], 0.05)
    return np.stack([W * vp[0] + focal * p[..., 0] / z, H * vp[1] + focal * p[..., 1] / z], axis=-1)


def corners(centre, length, width, yaw, pitch, roll):
    """The four corners of a strip in space. Unrotated it faces the camera with its length along x."""
    hx, hy = length / 2, width / 2
    pts = np.array([[-hx, -hy, 0], [hx, -hy, 0], [hx, hy, 0], [-hx, hy, 0]], np.float64)
    cy, sy, cp, sp, cr, sr = math.cos(yaw), math.sin(yaw), math.cos(pitch), math.sin(pitch), math.cos(roll), math.sin(roll)
    Rz = np.array([[cr, -sr, 0], [sr, cr, 0], [0, 0, 1]])
    Ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
    Rx = np.array([[1, 0, 0], [0, cp, -sp], [0, sp, cp]])
    return pts @ (Ry @ Rx @ Rz).T + np.array(centre)


def swarm(n, seed, toward, frames):
    """The blank strips: where each starts, how it flies, how it tumbles."""
    rng = np.random.default_rng(seed)
    out = []
    for i in range(n):
        speed = rng.uniform(7.0, 15.0) / 24.0                       # metres a frame
        z0 = rng.uniform(0.6, 15.0)
        x = rng.uniform(-4.2, 4.2)
        y = rng.uniform(-2.0, 1.25)
        if abs(x) < 0.5 and y > -0.6:                               # keep the middle of the hall, where she walks, thinner
            x += math.copysign(0.9, x if x else 1)
        out.append(dict(x=x, y=y, z0=z0, v=speed * (-1 if toward else 1), length=rng.uniform(0.35, 0.8), width=rng.uniform(0.035, 0.06),
                        yaw=rng.uniform(-1.3, 1.3), pitch=rng.uniform(-0.9, 0.9), roll=rng.uniform(-0.6, 0.6),
                        dyaw=rng.uniform(-0.35, 0.35), droll=rng.uniform(-0.25, 0.25), sway=rng.uniform(0, 6.28), lift=rng.uniform(-0.012, 0.012),
                        tone=rng.uniform(0.72, 1.0)))
    return out


def strip_at(s, t, toward):
    span = 15.0
    z = s["z0"] + s["v"] * t
    z = (z - 0.25) % span + 0.25                                    # recycle: past the lens, back to the far end (or the reverse)
    x = s["x"] + 0.10 * math.sin(s["sway"] + t * 0.35)
    y = s["y"] + s["lift"] * t + 0.05 * math.sin(s["sway"] * 1.7 + t * 0.5)
    return (x, y, z), s["yaw"] + s["dyaw"] * t, s["pitch"], s["roll"] + s["droll"] * t


def figure_matte(lit, fig, W, H):
    """Where she stands, as a soft matte: the dark of her silhouette inside the column she walks in. fig is
    [x0, x1, y0] as fractions of the frame; a fourth number is how dark counts as her."""
    x0, x1, y0 = fig[0] * W, fig[1] * W, fig[2] * H
    thr = fig[3] if len(fig) > 3 else 34.0
    xs = np.arange(W, dtype=np.float32)[None, :]
    ys = np.arange(H, dtype=np.float32)[:, None]
    e = 0.03 * W
    win = np.clip((xs - x0) / e + 1, 0, 1) * np.clip((x1 - xs) / e + 1, 0, 1) * np.clip((ys - y0) / e + 1, 0, 1)
    return np.clip((thr - lit) / 14.0, 0, 1) * win


def smoke_lines(n, seed):
    """Wind-tunnel smoke: thin ribbons that run the length of the hall, each with its own slow wave and its own puffs."""
    rng = np.random.default_rng(seed)
    out = []
    for i in range(n):
        x, y = rng.uniform(-3.8, 3.8), rng.uniform(-1.8, 1.05)
        if abs(x) < 0.6:
            x += math.copysign(0.75, x if x else 1)
        out.append(dict(x=x, y=y, a=rng.uniform(0.02, 0.07), b=rng.uniform(0.01, 0.04), kz=rng.uniform(0.5, 1.2), ph=rng.uniform(0, 6.28),
                        kp=rng.uniform(0.35, 0.9), ph2=rng.uniform(0, 6.28), w=rng.uniform(0.6, 1.3)))
    return out


def draw_smoke(lines, t, v, W, H, focal, vp, zf, behind, front):
    zs = np.geomspace(0.45, 16.0, 46)
    s = zs + v * t                                                    # the pattern rides the wind
    for ln in lines:
        xs = ln["x"] + ln["a"] * np.sin(ln["kz"] * s + ln["ph"])
        ys = ln["y"] + ln["b"] * np.sin(ln["kz"] * 1.3 * s + ln["ph"] * 1.7)
        puff = (0.5 + 0.5 * np.sin(ln["kp"] * s + ln["ph2"])) ** 2
        fade = np.clip((zs - 0.5) / 0.7, 0, 1) * (0.3 + 0.7 * np.exp(-zs / 7.0))
        q = project(np.stack([xs, ys, zs], axis=1), W, H, focal, vp)
        for i in range(len(zs) - 1):
            al = float(puff[i] * fade[i])
            if al < 0.04:
                continue
            p0, p1 = q[i], q[i + 1]
            if max(p0[0], p1[0]) < -40 or min(p0[0], p1[0]) > W + 40 or max(p0[1], p1[1]) < -40 or min(p0[1], p1[1]) > H + 40:
                continue
            wd = int(max(1, min(9, focal * 0.011 * ln["w"] / zs[i])))
            (behind if zs[i] > zf else front).line([tuple(p0), tuple(p1)], fill=int(255 * al), width=wd)


def load_plates(spec, n):
    """One plate, or several in a row when the shot holds a cut. Returns the frames and, for each, its plate's settings."""
    if "plates" in spec:
        frames, meta = [], []
        for i, pl in enumerate(spec["plates"]):
            f = C.clip_frames(os.path.join(ROOT, "clips", pl["clip"]), pl["frames"], pl)
            frames += f
            meta += [dict(pl, index=i)] * len(f)
        return frames[:n], meta[:n]
    return C.clip_frames(os.path.join(ROOT, "clips", spec["plate"]["clip"]), n, spec["plate"]), [dict(spec["plate"], index=0)] * n


def render(shot, spec, W, H):
    C.W, C.H, C.K = W, H, H / 720.0
    K = H / 720.0
    n = spec["frames"]
    frames, meta = load_plates(spec, n)
    toward = spec["toward"]
    focal = 0.92 * W
    blank = swarm(spec.get("strips", 200), spec.get("seed", 7), toward, n)
    smoke = smoke_lines(spec["smoke"].get("n", 28), spec["smoke"].get("seed", 5)) if spec.get("smoke") else []
    heroes = []
    for hero in spec.get("heroes", []):
        heroes.append(dict(hero, tex=texture(hero["text"], hero.get("year"), hero.get("hand"), w=int(1500 * max(1.0, K)), h=int(150 * max(1.0, K)))))
    subs = int(round(SUB * max(1.0, K)))                               # steps closer than a pixel apart at any size
    cyan = np.array([150, 236, 244], np.float32)
    keys4 = ("far", "midb", "mid", "near")                            # far and midb are behind her, mid and near in front
    out = []
    for k in range(n):
        pl = meta[k]
        vp = tuple(pl.get("vanish", (0.5, 0.5)))
        zf = float(pl.get("depth", 4.0))                              # how far from the lens she is, in metres
        shift = 53.7 * pl["index"]                                    # after a cut inside the shot the air is different air
        base = frames[k].convert("RGB")
        lit = np.asarray(base.filter(ImageFilter.GaussianBlur(3 * K))).astype(np.float32).mean(axis=2)
        matte = figure_matte(lit, pl["figure"], W, H) if pl.get("figure") else None
        layers = {key: np.zeros((H, W, 4), np.float32) for key in keys4}
        sm_b, sm_f = np.zeros((H, W), np.float32), np.zeros((H, W), np.float32)
        for sub in range(subs):
            t = k + SHUTTER * sub / subs
            ims = {key: Image.new("RGBA", (W, H), (0, 0, 0, 0)) for key in keys4}
            draws = {key: ImageDraw.Draw(ims[key]) for key in ims}
            for s in blank:
                centre, yaw, pitch, roll = strip_at(s, t + shift, toward)
                z = centre[2]
                if z < 0.3:
                    continue
                q = project(corners(centre, s["length"], s["width"], yaw, pitch, roll), W, H, focal, vp)
                if q[:, 0].max() < -50 or q[:, 0].min() > W + 50 or q[:, 1].max() < -50 or q[:, 1].min() > H + 50:
                    continue
                key = "near" if z < 1.6 else ("mid" if z <= zf else ("midb" if z < 5.5 else "far"))
                haze = min(1.0, max(0.0, (z - 2.0) / 12.0))
                col = (np.array(PAPER, np.float32) * (1 - 0.55 * haze) + cyan * 0.55 * haze) * s["tone"] * (1.0 - 0.45 * haze)
                alpha = int(255 * (0.95 - 0.5 * haze))
                draws[key].polygon([tuple(p) for p in q], fill=tuple(int(v) for v in col) + (alpha,))
            for hero in heroes:
                keys = hero["keys"]                                   # [frame, x, y, z]: fast in, a slow drift where it can be read, fast out
                if t < keys[0][0] or t > keys[-1][0]:
                    continue
                for a, b in zip(keys[:-1], keys[1:]):
                    if a[0] <= t <= b[0]:
                        u = (t - a[0]) / max(1e-6, b[0] - a[0])
                        centre = [a[i] + (b[i] - a[i]) * u for i in (1, 2, 3)]
                        break
                centre[1] += 0.03 * math.sin(t * 0.9 + keys[0][0])
                yaw = hero.get("yaw", 0.0) + 0.16 * math.sin(t * 0.33 + keys[0][0])
                roll = hero.get("roll", 0.0) + 0.07 * math.sin(t * 0.5 + keys[0][0])
                q = project(corners(centre, hero.get("length", 1.5), hero.get("length", 1.5) / 10.0, yaw, hero.get("pitch", 0.15), roll), W, H, focal, vp)
                x0, y0 = int(math.floor(q[:, 0].min())) - 2, int(math.floor(q[:, 1].min())) - 2
                x1, y1 = int(math.ceil(q[:, 0].max())) + 2, int(math.ceil(q[:, 1].max())) + 2
                if x1 <= 0 or y1 <= 0 or x0 >= W or y0 >= H or (x1 - x0) > 3 * W:
                    continue
                tex = hero["tex"]
                tw, th = tex.size
                cf = coeffs([(p[0] - x0, p[1] - y0) for p in q], [(0, 0), (tw, 0), (tw, th), (0, th)])
                warped = tex.transform((x1 - x0, y1 - y0), Image.PERSPECTIVE, tuple(cf), resample=Image.BICUBIC)
                key = "near" if centre[2] < 1.0 else "mid"
                ims[key].alpha_composite(warped, (max(0, x0), max(0, y0)), (max(0, -x0), max(0, -y0)))
            for key in layers:
                a = np.asarray(ims[key]).astype(np.float32)
                a[..., :3] *= a[..., 3:4] / 255.0                     # premultiplied, so the blur of motion adds up right
                layers[key] += a / subs
            if smoke:
                bi, fi = Image.new("L", (W, H), 0), Image.new("L", (W, H), 0)
                draw_smoke(smoke, t + shift, (-1 if toward else 1) * spec["smoke"].get("speed", 0.42), W, H, focal, vp, zf, ImageDraw.Draw(bi), ImageDraw.Draw(fi))
                sm_b += np.asarray(bi, np.float32) / subs
                sm_f += np.asarray(fi, np.float32) / subs
        img = np.asarray(base).astype(np.float32)
        hide = (1 - matte) if matte is not None else np.clip((lit - 22) / 30.0, 0, 1)
        if smoke:                                                     # behind her first, then the strips, then what passes in front
            g = spec["smoke"].get("gain", 0.5)
            sb = np.asarray(Image.fromarray(np.clip(sm_b, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.4 * K)), np.float32) / 255.0
            img = img + (sb * hide * g)[..., None] * np.array([190, 236, 244], np.float32)
        for key, blur in (("far", 0.6), ("midb", 1.0), ("mid", 1.0), ("near", 7.0)):
            lay = layers[key]
            im = Image.fromarray(np.clip(lay, 0, 255).astype(np.uint8), "RGBA")
            if blur:
                im = im.filter(ImageFilter.GaussianBlur(blur * K))
            lay = np.asarray(im).astype(np.float32)
            alpha = lay[..., 3:4] / 255.0
            if key in ("far", "midb") and (matte is not None or key == "far"):      # behind her: she covers them
                alpha = alpha * hide[..., None]
                lay[..., :3] *= hide[..., None]
            img = img * (1 - alpha) + lay[..., :3]
        if smoke:
            sf = np.asarray(Image.fromarray(np.clip(sm_f, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(3.2 * K)), np.float32) / 255.0
            img = img + (sf * spec["smoke"].get("gain", 0.5) * 0.9)[..., None] * np.array([200, 240, 246], np.float32)
        out.append(Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)))
    return out


def track_strip(frames, spec, W, H):
    """B08: find the one strip in her fingers in every frame and lay the printed words along it."""
    K = H / 720.0
    tex = texture(spec["text"], None, spec.get("hand"), w=spec["tex"][0], h=spec["tex"][1], tint=(1, 1, 1), big=True)
    fits = []
    for im in frames:
        a = np.asarray(im).astype(np.float32)
        r, g, b = a[..., 0], a[..., 1], a[..., 2]
        m = (r > 150) & (g > 140) & (b > 95) & (r - b > 6) & (r - b < 75) & (r >= g - 4)     # warm white: the paper, not the cold lights, not skin
        m = np.asarray(Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.MinFilter(5)).filter(ImageFilter.MaxFilter(5))) > 127
        ys, xs = np.nonzero(m)
        if len(xs) >= 400:                                            # keep the long body of the strip: drop stray patches far from it
            cx, cy = np.median(xs), np.median(ys)
            keep = (np.abs(ys - cy) < 0.16 * H)
            xs, ys = xs[keep], ys[keep]
        if len(xs) < 400:
            fits.append(None)
            continue
        pts = np.stack([xs, ys], 1).astype(np.float64)
        c = pts.mean(axis=0)
        cov = np.cov((pts - c).T)
        val, vec = np.linalg.eigh(cov)
        ax = vec[:, 1] if vec[0, 1] >= 0 else -vec[:, 1]              # along the strip, pointing right
        nrm = np.array([-ax[1], ax[0]])
        if nrm[1] < 0:
            nrm = -nrm
        s = (pts - c) @ ax
        t = (pts - c) @ nrm
        fits.append((c, ax, nrm, np.percentile(s, 1), np.percentile(s, 99), np.percentile(t, 4), np.percentile(t, 96)))
    good = [f for f in fits if f is not None]
    out = []
    for i, im in enumerate(frames):
        fit = fits[i]
        if fit is None:
            out.append(im)
            continue
        near = [fits[j] for j in range(max(0, i - 1), min(len(fits), i + 2)) if fits[j] is not None]     # a little smoothing in time
        c = np.mean([f[0] for f in near], axis=0)
        ax = np.mean([f[1] for f in near], axis=0)
        ax /= np.linalg.norm(ax)
        nrm = np.array([-ax[1], ax[0]])
        if nrm[1] < 0:
            nrm = -nrm
        s0, s1, t0, t1 = [float(np.mean([f[k] for f in near])) for k in (3, 4, 5, 6)]
        a0, a1 = s0 + (s1 - s0) * spec["along"][0], s0 + (s1 - s0) * spec["along"][1]
        b0, b1 = t0 + (t1 - t0) * 0.04, t1 - (t1 - t0) * 0.04
        quad = [c + ax * a0 + nrm * b0, c + ax * a1 + nrm * b0, c + ax * a1 + nrm * b1, c + ax * a0 + nrm * b1]
        x0, y0 = int(min(p[0] for p in quad)) - 2, int(min(p[1] for p in quad)) - 2
        x1, y1 = int(max(p[0] for p in quad)) + 2, int(max(p[1] for p in quad)) + 2
        tw, th = tex.size
        cf = coeffs([(p[0] - x0, p[1] - y0) for p in quad], [(0, 0), (tw, 0), (tw, th), (0, th)])
        warped = tex.transform((x1 - x0, y1 - y0), Image.PERSPECTIVE, tuple(cf), resample=Image.BICUBIC)
        ink = Image.new("RGBA", warped.size, (0, 0, 0, 0))            # keep only the ink: the paper under it is the real strip
        wa = np.asarray(warped).astype(np.float32)
        dark = np.clip((200 - wa[..., :3].mean(axis=2)) / 150.0, 0, 1) * (wa[..., 3] / 255.0)
        inka = np.zeros(wa.shape, np.uint8)
        inka[..., :3] = np.clip(wa[..., :3], 0, 255).astype(np.uint8)
        inka[..., 3] = (dark * 235).astype(np.uint8)
        ink = Image.fromarray(inka, "RGBA").filter(ImageFilter.GaussianBlur(spec.get("soft", 1.2) * K))
        base = im.convert("RGBA")
        base.alpha_composite(ink, (max(0, x0), max(0, y0)), (max(0, -x0), max(0, -y0)))
        out.append(base.convert("RGB"))
    return out


def card_texture(text, hand, w, h):
    """What is on the card in her fingers: one printed line, and a word in pencil under it. Only the ink; the paper is the real card."""
    im = Image.new("RGBA", (w, h), (255, 255, 255, 0))
    d = ImageDraw.Draw(im)
    size = int(h * 0.19)
    f = ImageFont.truetype(F_PRINT, size)
    while d.textlength(text, font=f) > w * 0.78 and size > 20:
        size -= 2
        f = ImageFont.truetype(F_PRINT, size)
    d.text((w * 0.07, h * 0.36), text, font=f, fill=(18, 22, 30, 255), anchor="lm")
    if hand:
        fh = ImageFont.truetype(F_HAND, int(h * 0.27))
        word = Image.new("RGBA", (int(w * 0.4), int(h * 0.5)), (255, 255, 255, 0))
        ImageDraw.Draw(word).text((word.size[0] // 2, word.size[1] // 2), hand, font=fh, fill=(22, 34, 66, 255), anchor="mm")
        word = word.rotate(5, resample=Image.BICUBIC)
        im.alpha_composite(word, (int(w * 0.34), int(h * 0.44)))
    return im


def track_card(frames, spec, W, H):
    """B08, when the paper is a card: find its four corners in every frame and lay the ink on it in its own perspective."""
    import cv2
    K = H / 720.0
    tex = card_texture(spec["text"], spec.get("hand"), spec["tex"][0], spec["tex"][1])
    quads = []
    for im in frames:
        a = np.asarray(im).astype(np.float32)
        pale = ((a.min(axis=2) > 72) & (a.max(axis=2) - a.min(axis=2) < 40)).astype(np.uint8)        # grey and without colour: the card, not skin, not the navy, not the cyan lights
        pale = cv2.morphologyEx(pale, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
        n, lab, st, _ = cv2.connectedComponentsWithStats(pale)
        if n < 2:
            quads.append(None)
            continue
        i = 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA]))
        if st[i, cv2.CC_STAT_AREA] < 0.02 * W * H:
            quads.append(None)
            continue
        ys, xs = np.nonzero(lab == i)
        box = cv2.boxPoints(cv2.minAreaRect(np.stack([xs, ys], 1).astype(np.float32)))
        box = box[np.argsort(box[:, 1])]
        top, bot = box[:2][np.argsort(box[:2, 0])], box[2:][np.argsort(box[2:, 0])]
        quads.append(np.array([top[0], top[1], bot[1], bot[0]], np.float64))                           # top left, top right, bottom right, bottom left
    out = []
    for i, im in enumerate(frames):
        near = [quads[j] for j in range(max(0, i - 1), min(len(quads), i + 2)) if quads[j] is not None]
        if quads[i] is None or not near:
            out.append(im)
            continue
        q = np.mean(near, axis=0)
        x0, y0 = int(q[:, 0].min()) - 2, int(q[:, 1].min()) - 2
        x1, y1 = int(q[:, 0].max()) + 2, int(q[:, 1].max()) + 2
        tw, th = tex.size
        cf = coeffs([(p[0] - x0, p[1] - y0) for p in q], [(0, 0), (tw, 0), (tw, th), (0, th)])
        warped = tex.transform((x1 - x0, y1 - y0), Image.PERSPECTIVE, tuple(cf), resample=Image.BICUBIC)
        wa = np.asarray(warped).astype(np.float32)
        wa[..., 3] *= 0.90
        # how soft the ink is: as soft as the card it lies on. A 1080-line plate is sharper than a draft enlarged, so its ink is too
        soft = spec.get("soft_hd", spec.get("soft", 1.0)) if H >= 1080 else spec.get("soft", 1.0)
        ink = Image.fromarray(np.clip(wa, 0, 255).astype(np.uint8), "RGBA").filter(ImageFilter.GaussianBlur(soft * K))
        base = im.convert("RGBA")
        base.alpha_composite(ink, (max(0, x0), max(0, y0)), (max(0, -x0), max(0, -y0)))
        out.append(base.convert("RGB"))
    return out


def encode(frames, path, W, H):
    enc = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "%dx%d" % (W, H), "-r", "24", "-i", "-",
                            "-c:v", "libx264", "-preset", "medium", "-crf", "14", "-pix_fmt", "yuv420p", path], stdin=subprocess.PIPE)
    for f in frames:
        enc.stdin.write(f.tobytes())
    enc.stdin.close()
    enc.wait()
    print("wrote %s, %d frames" % (os.path.relpath(path, ROOT), len(frames)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("shots", nargs="*")
    ap.add_argument("--size", default="1280x720")
    ap.add_argument("--spec", default=os.path.join(ROOT, "timing", "wind.json"), help="another spec: the reel's keeps its lettered strips inside a 4:5 window (timing/wind_reel.json)")
    ap.add_argument("--outdir", default=os.path.join(ROOT, "clips"))
    a = ap.parse_args()
    W, H = [int(v) for v in a.size.split("x")]
    spec = json.load(open(a.spec))
    os.makedirs(a.outdir, exist_ok=True)
    for shot, s in spec["shots"].items():
        if a.shots and shot not in a.shots:
            continue
        if s.get("kind") == "track":
            C.W, C.H, C.K = W, H, H / 720.0
            frames = C.clip_frames(os.path.join(ROOT, "clips", s["plate"]["clip"]), s["frames"], s["plate"])
            frames = (track_card if s.get("paper") == "card" else track_strip)(frames, s, W, H)
        else:
            frames = render(shot, s, W, H)
        encode(frames, os.path.join(a.outdir, shot + ".mp4"), W, H)


if __name__ == "__main__":
    main()
