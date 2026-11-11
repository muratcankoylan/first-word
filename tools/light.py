#!/usr/bin/env python3
"""FIRST WORD: the cursor and its family, drawn as light.

Everything cyan that the film draws itself used to be a flat rectangle: the cursor, the block over a word, the
block that wipes the wall, the bar that becomes the cursor at the end. They are now all made here, out of the same
few parts, so that they read as one thing and as the same light as the tubes in the hall and the baton in Pip's
hand: a hot core, a cyan body, a tight glow and a wide one, a little flicker, and a streak along the way it moves.

Every function draws into a float picture (height, width, 3; 0 to 255) in place. k is the picture's scale against
1280 by 720. Nothing here is random from run to run: flicker and noise come from the frame number.
"""
import numpy as np
import cv2

CYAN = np.array([0, 229, 255], np.float32)
HOT = np.array([214, 250, 255], np.float32)          # the core of a light, on a dark ground
DEEP = np.array([0, 176, 214], np.float32)           # the same light where it sits on white paper
DARK = np.array([2, 24, 38], np.float32)             # the unlit body of a block


def h01(*v):
    """A number from 0 to 1 that depends only on the integers given (arrays allowed)."""
    x = np.zeros((), np.uint64)
    with np.errstate(over="ignore"):
        for i, p in zip(v, (73856093, 19349663, 83492791, 2654435761, 40503)):
            x = x ^ (np.asarray(i).astype(np.int64).astype(np.uint64) * np.uint64(p))
        x = (x ^ (x >> np.uint64(13))) * np.uint64(1274126177)
        return ((x ^ (x >> np.uint64(16))) & np.uint64(0xFFFF)).astype(np.float32) / 65535.0


def over(a, alpha, color):
    a[:] = a * (1 - alpha[..., None]) + np.asarray(color, np.float32) * alpha[..., None]


def region(shape, box, pad):
    H, W = shape[:2]
    x0, y0 = max(0, int(np.floor(box[0] - pad))), max(0, int(np.floor(box[1] - pad)))
    x1, y1 = min(W, int(np.ceil(box[2] + pad))), min(H, int(np.ceil(box[3] + pad)))
    return x0, y0, x1, y1


def box_mask(shape, box, x0, y0, x1, y1, round_=0.0):
    """A filled box with soft pixel edges, drawn in the region [x0:x1, y0:y1]. round_ is the corner radius."""
    m = np.zeros((y1 - y0, x1 - x0), np.float32)
    S = 16
    p0 = (int(round((box[0] - x0) * S)), int(round((box[1] - y0) * S)))
    p1 = (int(round((box[2] - x0) * S)), int(round((box[3] - y0) * S)))
    cv2.rectangle(m, p0, p1, 1.0, -1, cv2.LINE_AA, 4)
    if round_ > 0.6:
        m = cv2.GaussianBlur(m, (0, 0), round_ * 0.5)
        m = np.clip((m - 0.5) * 4.0 + 0.5, 0, 1)
    return m


def tube(a, box, power=1.0, k=1.0, t=0, seed=0, flare=0.0, paper=None):
    """A small tube of light filling box (x0, y0, x1, y1): the cursor. power dims or overdrives it; flare adds the
    streak a lens gives a light that has just come on."""
    if power <= 0.004:
        return
    w, h = max(1.0, box[2] - box[0]), max(1.0, box[3] - box[1])
    thin = min(w, h)
    s1, s2 = max(2.0 * k, 0.65 * thin), max(7.0 * k, 2.4 * thin)
    pad = 3.2 * s2 + (flare > 0) * 16 * thin
    x0, y0, x1, y1 = region(a.shape, box, pad)
    if x1 <= x0 or y1 <= y0:
        return
    r = a[y0:y1, x0:x1]
    m = box_mask(a.shape, box, x0, y0, x1, y1, round_=thin * 0.32)
    bx0, by0 = max(0, int(box[0]) - x0), max(0, int(box[1]) - y0)
    ground = r[by0:by0 + max(1, int(h)), bx0:bx0 + max(1, int(w))]
    if paper is None:
        paper = ground.size > 0 and float(ground.mean()) > 150           # on white there is no glow to see: the light is ink
    p = power * (1.0 + 0.045 * np.sin(t * 2.3 + seed) + 0.05 * (float(h01(t, seed)) - 0.5))
    g1 = cv2.GaussianBlur(m, (0, 0), s1)
    g2 = cv2.GaussianBlur(m, (0, 0), s2)
    if paper:
        over(r, np.clip(0.20 * p * g2, 0, 1), CYAN)
        over(r, np.clip(0.40 * p * g1, 0, 1), CYAN)
        over(r, np.clip(m * min(1.0, p), 0, 1), DEEP)
        inner = cv2.GaussianBlur(m, (0, 0), max(0.8, 0.22 * thin)) * m
        over(r, np.clip((inner - 0.55) * 1.4, 0, 1) * min(1.0, p) * 0.55, CYAN)
        return
    tall = cv2.GaussianBlur(m, (0, 0), sigmaX=max(1.0, 0.7 * w), sigmaY=max(2.0, 1.6 * h))
    over(r, np.clip(0.11 * p * tall, 0, 1), CYAN)
    over(r, np.clip(0.30 * p * g2, 0, 1), CYAN)
    over(r, np.clip(0.62 * p * g1, 0, 1), CYAN)
    over(r, np.clip(m * min(1.0, p), 0, 1), CYAN)
    inner = cv2.GaussianBlur(m, (0, 0), max(0.8, 0.20 * thin)) * m
    over(r, np.clip((inner - 0.35) * 1.7, 0, 1) * min(1.0, p), HOT)
    if flare > 0.01:
        wide = cv2.GaussianBlur(m, (0, 0), sigmaX=max(4.0, 9.0 * thin), sigmaY=max(0.8, 0.10 * h))
        over(r, np.clip(1.6 * flare * wide, 0, 1), CYAN)
        over(r, np.clip(0.9 * flare * g2, 0, 1), HOT)


def ring(a, cx, cy, radius, k=1.0, gain=1.0, flat=1.0, width=2.0):
    """A ring of light, the mark a click leaves: thin, with a soft edge, and a fainter echo inside it."""
    if gain <= 0.004 or radius <= 0:
        return
    pad = radius + 14 * k
    x0, y0, x1, y1 = region(a.shape, (cx, cy - (pad - radius) - radius * flat, cx, cy + (pad - radius) + radius * flat), 0)
    x0, x1 = max(0, int(cx - pad)), min(a.shape[1], int(cx + pad) + 1)
    if x1 <= x0 or y1 <= y0:
        return
    ys, xs = np.mgrid[y0:y1, x0:x1].astype(np.float32)
    d = np.sqrt((xs - cx) ** 2 + ((ys - cy) / flat) ** 2)
    prof = np.exp(-((d - radius) / (width * k)) ** 2) + 0.30 * np.exp(-((d - radius) / (width * 4.5 * k)) ** 2) \
        + 0.35 * np.exp(-((d - radius * 0.74) / (width * 0.8 * k)) ** 2)
    over(a[y0:y1, x0:x1], np.clip(gain * prof, 0, 1), CYAN)


def redact(a, box, f, k=1.0, seed=0, age=None, halo=1.0):
    """The block over a word: a slab of lit cells that keep changing, a band of scan that travels down it, a bright
    rim, and its glow on whatever is round it. age counts frames since it landed: it lands large and hot."""
    x0f, y0f, x1f, y1f = box
    if age is not None and age < 3:
        s = 1 + 0.42 * (1 - age / 3.0) ** 2
        cx, cy = (x0f + x1f) / 2, (y0f + y1f) / 2
        x0f, x1f = cx + (x0f - cx) * s, cx + (x1f - cx) * s
        y0f, y1f = cy + (y0f - cy) * s, cy + (y1f - cy) * s
    H, W = a.shape[:2]
    x0, y0, x1, y1 = max(0, int(round(x0f))), max(0, int(round(y0f))), min(W, int(round(x1f))), min(H, int(round(y1f)))
    bw, bh = x1 - x0, y1 - y0
    if bw < 4 or bh < 4:
        return
    ys, xs = np.mgrid[0:bh, 0:bw]
    cw = int(np.clip(bw / 20.0, 5 * k, 15 * k))
    chh = max(3, int(round(cw * 0.62)))
    cells = h01(xs // cw, ys // chh, f // 2, seed)
    lit = np.where(cells < 0.16, 0.10, np.where(cells < 0.50, 0.52, np.where(cells < 0.88, 0.82, 1.0))).astype(np.float32)
    gaps = ((xs % cw) < cw - max(1, int(k))) & ((ys % chh) < chh - max(1, int(k)))
    scan = 0.80 + 0.20 * ((ys % max(2, int(round(3 * k)))) == 0)
    pos = ((f * 0.085 + seed * 0.37) % 1.0) * (bh + 0.3 * bh) - 0.15 * bh
    band = np.exp(-((ys - pos) / (0.11 * bh + 2.0)) ** 2)
    body = (0.16 + 0.84 * lit * gaps) * scan * (1.0 + 0.9 * band)
    col = DARK[None, None, :] * (1 - np.clip(body, 0, 1))[..., None] + CYAN[None, None, :] * np.clip(body, 0, 1)[..., None] \
        + (HOT - CYAN)[None, None, :] * np.clip(body - 1.0, 0, 1)[..., None]
    if float(h01(f, seed, 7)) < 0.34:                                    # now and then a slice of it slips sideways
        for n in range(2):
            ya = int(float(h01(f, seed, n, 11)) * bh)
            hh = max(2, int((0.06 + 0.16 * float(h01(f, seed, n, 13))) * bh))
            dx = int((float(h01(f, seed, n, 17)) - 0.5) * 0.36 * bw)
            col[ya:ya + hh] = np.roll(col[ya:ya + hh], dx, axis=1)
            col[ya:ya + hh, :, 0] = np.roll(col[ya:ya + hh, :, 0], int(3 * k) + 1, axis=1) + 60
    a[y0:y1, x0:x1] = np.clip(col, 0, 255)
    rim = max(1, int(round(1.6 * k)))
    for sl in ((slice(y0, y0 + rim), slice(x0, x1)), (slice(y1 - rim, y1), slice(x0, x1)), (slice(y0, y1), slice(x0, x0 + rim)), (slice(y0, y1), slice(x1 - rim, x1))):
        a[sl] = a[sl] * 0.15 + HOT * 0.85
    pad = int(70 * k)
    rx0, ry0, rx1, ry1 = region(a.shape, (x0, y0, x1, y1), pad)
    m = np.zeros((ry1 - ry0, rx1 - rx0), np.float32)
    m[y0 - ry0:y1 - ry0, x0 - rx0:x1 - rx0] = 1
    out = 1 - m
    r = a[ry0:ry1, rx0:rx1]
    over(r, np.clip(0.40 * halo * cv2.GaussianBlur(m, (0, 0), 8 * k * halo) * out, 0, 1), CYAN)
    over(r, np.clip(0.18 * halo * cv2.GaussianBlur(m, (0, 0), 26 * k * halo) * out, 0, 1), CYAN)
    if age is not None and age < 2:
        over(r, np.clip((0.85 if age == 0 else 0.35) * cv2.GaussianBlur(m, (0, 0), 3 * k), 0, 1), HOT)


def blade(a, xb, x_prev, f, k=1.0, wall=None):
    """The wipe: a blade of light the full height of the frame, standing at xb, with the trail of where it was a
    frame ago (x_prev, to its right). wall is 1 where the frame is bare wall and 0 where a person stands in front
    of it: the light passes behind people."""
    H, W = a.shape[:2]
    xs = np.arange(W, dtype=np.float32)[None, :]
    ys = np.arange(H)[:, None]
    span = max(8.0, x_prev - xb)
    trail = np.where((xs > xb) & (xs < x_prev + 30 * k), np.exp(-(xs - xb) / (0.42 * span)), 0.0)
    rows = h01(ys // max(1, int(round(2 * k))), f, 3)
    streaks = (rows > 0.80).astype(np.float32) * trail * (0.35 + 0.65 * h01(ys // max(1, int(round(2 * k))), f, 5))
    g1 = np.exp(-((xs - xb) / (15 * k)) ** 2)
    g2 = np.exp(-((xs - xb) / (60 * k)) ** 2)
    alpha = np.clip(0.50 * trail + 0.50 * streaks + 0.80 * g1 + 0.34 * g2, 0, 1) * np.ones((H, 1), np.float32)
    sparks = (h01(np.arange(W)[None, :] // max(2, int(3 * k)), ys // max(2, int(3 * k)), f, 9) > 0.992) * (trail > 0.12)
    core = np.exp(-((xs - xb) / (4.6 * k)) ** 2) * np.ones((H, 1), np.float32)
    if wall is not None:
        alpha = alpha * (0.16 + 0.84 * wall)
        core = core * (0.10 + 0.90 * wall)
        sparks = sparks * (wall > 0.5)
    over(a, alpha.astype(np.float32), CYAN)
    over(a, np.clip(sparks.astype(np.float32) * 0.9, 0, 1), HOT)
    over(a, np.clip(core, 0, 1).astype(np.float32), HOT)


def shock(a, age, k=1.0, frames=4, flash=0.55):
    """An impact on the whole frame: a flash, and for a few frames the colours pulled apart from the centre."""
    if age >= frames:
        return a
    s = (1 - age / float(frames)) ** 1.5
    H, W = a.shape[:2]
    out = a.copy()
    for c, z in ((0, 1 + 0.022 * s), (2, 1 - 0.022 * s)):
        M = np.array([[z, 0, (1 - z) * W / 2], [0, z, (1 - z) * H / 2]], np.float32)
        out[..., c] = cv2.warpAffine(a[..., c], M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    fl = flash * (1.0 if age == 0 else 0.38 if age == 1 else 0.12 if age == 2 else 0.0)
    return out + (255 - out) * fl


def tear(a, f, k=1.0, seed=0, strength=1.0):
    """One frame of a picture slipping: three bands pushed sideways and the colours a few pixels apart."""
    H, W = a.shape[:2]
    out = a.copy()
    d = int(round(5 * k * strength)) + 1
    out[..., 0] = np.roll(a[..., 0], d, axis=1)
    out[..., 2] = np.roll(a[..., 2], -d, axis=1)
    for n in range(3):
        y = int(float(h01(f, seed, n, 21)) * H * 0.9)
        hh = int((0.02 + 0.07 * float(h01(f, seed, n, 23))) * H)
        dx = int((float(h01(f, seed, n, 29)) - 0.5) * 0.10 * W * strength)
        out[y:y + hh] = np.roll(out[y:y + hh], dx, axis=1)
    return out


def crt_off(a, t):
    """A tube switching off: the picture folds to a bright line, then to a point. t runs from 0 (whole) to 1 (gone)."""
    H, W = a.shape[:2]
    out = np.zeros_like(a)
    sy = max(0.006, (1 - min(1.0, t * 1.5)) ** 2.2)
    sx = 1.0 if t < 0.66 else max(0.02, 1 - (t - 0.66) / 0.34)
    hh, ww = max(2, int(H * sy)), max(2, int(W * sx))
    small = cv2.resize(a, (ww, hh), interpolation=cv2.INTER_AREA)
    small = small + (255 - small) * min(0.85, 0.25 + t * 0.9)
    y0, x0 = (H - hh) // 2, (W - ww) // 2
    out[y0:y0 + hh, x0:x0 + ww] = small
    glow = cv2.GaussianBlur(out, (0, 0), 6 + 10 * t)
    return np.clip(out + glow * 0.9, 0, 255)


def spikes(a, box, f, k=1.0, level=0.1, n=256, seed=0):
    """A row of n slits of light, one for each electrode: each fires now and then and fades over three frames.
    level (0 to 1) is how busy they are. When they are busy a wave of firing runs along the row, left to right,
    toward whatever is being written from them. A slit that has just fired is tall and hot; a resting one is a
    low ember. Nothing here is measured data: it is a drawing of a signal being read."""
    x0f, y0f, x1f, y1f = box
    H, W = a.shape[:2]
    pad = int(10 * k)
    x0, y0, x1, y1 = max(0, int(x0f) - pad), max(0, int(y0f) - pad), min(W, int(x1f) + pad), min(H, int(y1f) + pad)
    if x1 - x0 < 8 or y1 - y0 < 4 or level <= 0.002:
        return
    i = np.arange(n)
    fire = np.zeros(n, np.float32)
    for age in range(4):                                             # this frame's firing, and the three before it still glowing
        ff = f - age
        pos = ((ff * 0.043 + seed * 0.19) % 1.25) - 0.12              # the wave's place along the row
        wave = np.exp(-((i / float(n) - pos) / 0.085) ** 2)
        p = np.clip(level * (0.30 + 1.25 * wave * min(1.0, level * 2.2)), 0, 0.95)
        hit = (h01(i, ff, seed) < p).astype(np.float32) * (0.55 + 0.45 * h01(i, ff, seed, 3))
        fire = np.maximum(fire, hit * (0.58 ** age))
    bw, bh = x1f - x0f, y1f - y0f
    m = np.zeros((y1 - y0, x1 - x0), np.float32)
    hot = np.zeros_like(m)
    cx = x0f + (i + 0.5) * bw / n - x0                                # each slit's centre, in the region
    wd = max(1.0, 0.36 * bw / n)
    cy = (y0f + y1f) / 2.0 - y0
    xs = np.arange(x1 - x0, dtype=np.float32)
    ys = np.arange(y1 - y0, dtype=np.float32)
    for j in range(n):
        amp = 0.14 + 0.86 * fire[j]
        col = np.clip(1.0 - np.abs(xs - cx[j]) / wd, 0, 1)
        if col.max() <= 0:
            continue
        row = np.clip((amp * bh / 2.0 - np.abs(ys - cy)) / max(1.0, 1.2 * k) + 0.5, 0, 1)
        lo, hi = max(0, int(cx[j] - wd - 1)), min(x1 - x0, int(cx[j] + wd + 2))
        cell = row[:, None] * col[None, lo:hi]
        m[:, lo:hi] = np.maximum(m[:, lo:hi], cell * (0.20 + 0.80 * fire[j]))
        if fire[j] > 0.6:
            hot[:, lo:hi] = np.maximum(hot[:, lo:hi], cell * (fire[j] - 0.6) / 0.4)
    r = a[y0:y1, x0:x1]
    g = cv2.GaussianBlur(m, (0, 0), 4.0 * k)
    over(r, np.clip(0.85 * g, 0, 1), CYAN)
    over(r, np.clip(m * 1.15, 0, 1), CYAN)
    over(r, np.clip(hot, 0, 1) * 0.85, HOT)


def bloom(a, amount=0.25, k=1.0):
    """The film's own cyan lights glow a little further than the lens gave them."""
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    m = np.clip((b - r - 45) / 70.0, 0, 1) * np.clip((np.maximum(g, b) - 150) / 80.0, 0, 1)
    if float(m.max()) < 0.05:
        return a
    H, W = a.shape[:2]
    small = cv2.resize(a * m[..., None], (W // 4, H // 4), interpolation=cv2.INTER_AREA)
    small = cv2.GaussianBlur(small, (0, 0), 5.0 * k) + 0.6 * cv2.GaussianBlur(small, (0, 0), 14.0 * k)
    glow = cv2.resize(small, (W, H), interpolation=cv2.INTER_LINEAR)
    return 255 - (255 - a) * (1 - np.clip(amount * glow / 255.0, 0, 1))


def creep(a, z, cx=0.5, cy=0.5):
    """The frame a little larger, about a point: a slow push."""
    if abs(z - 1) < 0.0005:
        return a
    H, W = a.shape[:2]
    M = np.array([[z, 0, (1 - z) * cx * W], [0, z, (1 - z) * cy * H]], np.float32)
    return cv2.warpAffine(a, M, (W, H), flags=cv2.INTER_LANCZOS4, borderMode=cv2.BORDER_REFLECT)
