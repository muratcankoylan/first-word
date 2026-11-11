#!/usr/bin/env python3
"""FIRST WORD: the words on the kitchen laptop (shot F03).

    python3 tools/laptopshot.py [--size 1920x1080]     the laptop draft, at its best -> clips/F03.mp4

The director asked for "dumb question:" to be written on the screen in the video itself, not laid over it. The draft
macro_screen was generated with the words on the laptop's screen, and they came back spelled right, in the screen's
own perspective, with the screen's own block cursor blinking after the colon. This tool takes fifteen frames of it,
punches in until the words can be read, and does one thing to the picture: the cursor's dark block is given the
film's cyan, because the cursor is the thing this film follows from its first frame to its last. Its shape and
its place are the video's own.

The words are also typed: the shot opens on "dumb quest" and the last four letters arrive two frames apart, one for
each tap of Rosa's finger. No letter is drawn. A letter that has not been typed yet is covered with the screen's own
page (the same frame's pixels from a little further down, so the grain is the frame's own), and the cursor's block
stands where the next letter will go: the video's own block, moved along the video's own line of type.
"""
import math
import os
import subprocess
import sys

import numpy as np
import cv2

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import conform as C  # noqa: E402

SRC = os.path.join(C.ROOT, "clips", "drafts", "macro_screen.mp4")     # read at its best: the 1080p version when there is one (conform.best)
OUT = os.path.join(C.ROOT, "clips", "F03.mp4")
IN_FRAME = 84                 # source frame the shot starts on: the cursor is off for four frames, then on (it comes on at frame 88)
FRAMES = 15
# Every measure below is in the draft's own pixels (854 by 480). S scales them to the source in use: the 1080p
# version of the draft is the same take, 2.25 times the size, with the words and the block in the same places.
S = 1.0
WINDOW = (104, 150, 344)      # left, top, width of the punch-in
BLOCK = (282, 218, 322, 274)  # where the cursor's block can be
COLON = 286                   # the block starts to the right of this: left of it is the colon
CYAN = np.array([0, 190, 228], np.float32)
W, H = 1920, 1080
LINE = (200.0, 219.0, 0.393)  # the line of type: where it starts (x, y of its middle) and how fast it falls to the right
PITCH = 6.07                  # one letter's width along it; "dumb question:" is 14 letters
LEAN = 0.143                  # the letters' upright strokes lean this much (x for each y), as the block's own edges do
UP, DOWN = 21, 17             # how far above and below the middle of the line a letter (or the block) can reach
TYPED = (10, 10, 11, 11, 12, 12, 13, 13)     # letters on screen on each of the first frames; after that, all 14
BLOCK_FROM = 92               # a source frame where the block is on: its shape is taken from here


def px(v):
    return int(round(v * S))


def block_box():
    return tuple(px(v) for v in BLOCK)


def block_cover(frame):
    """How much of each pixel in BLOCK is the cursor's block (0 to 1), and the page colour round it."""
    bx0, by0, bx1, by1 = block_box()
    reg = frame[by0:by1, bx0:bx1]
    lum = reg.mean(axis=2)
    dark = lum < 112
    dark[:, : max(0, px(COLON) - bx0)] = False                         # not the colon itself
    if dark.sum() <= 60 * S * S:
        return None, None
    page = np.median(reg[~dark].reshape(-1, 3), axis=0)
    floor = float(np.percentile(lum[dark], 20))
    cover = np.clip((float(page.mean()) - lum) / max(1.0, float(page.mean()) - floor), 0, 1)
    cover[:, : max(0, px(COLON) - bx0)] = 0
    # Only the block. The page's own shading across this box is a few percent darker here and there; left in, it
    # was painted over with one flat page colour and showed as a pale box round the block at 1080 lines.
    cover = np.clip((cover - 0.30) / 0.50, 0, 1)
    n, lab, st, _ = cv2.connectedComponentsWithStats((cover > 0.5).astype(np.uint8))
    if n < 2:
        return None, None
    body = (lab == 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA]))).astype(np.uint8)
    r = max(1, px(1.5))
    body = cv2.dilate(body, np.ones((2 * r + 1, 2 * r + 1), np.uint8))
    return cv2.GaussianBlur((cover * body).astype(np.float32), (0, 0), 0.35 * S), page


HOT = np.array([214, 250, 255], np.float32)


def light(f, big, k):
    """The block as light, not as a flat patch: cyan at its edge and nearly white at its heart, the screen's own
    grain still in it, a slow pulse, and its glow on the page round it. big: how much of each pixel is the block."""
    heart = np.clip((cv2.GaussianBlur(big, (0, 0), 7.0 * S) - 0.45) / 0.45, 0, 1) ** 1.4
    pulse = 1.0 + 0.06 * math.sin(2 * math.pi * k / 9.0)
    col = (CYAN[None, None, :] * (1 - 0.62 * heart[..., None]) + HOT[None, None, :] * 0.62 * heart[..., None]) * pulse
    grey = f.mean(axis=2)
    col = col + ((grey - cv2.GaussianBlur(grey, (0, 0), 2.0 * S)) * 0.7)[..., None]
    f = f * (1 - big[..., None]) + np.clip(col, 0, 255) * big[..., None]
    near = cv2.GaussianBlur(big, (0, 0), 5.0 * S) * (1 - big)
    wide = cv2.GaussianBlur(big, (0, 0), 16.0 * S) * (1 - big)
    g = np.clip(0.30 * pulse * near + 0.16 * pulse * wide, 0, 1)[..., None]
    return f * (1 - g) + CYAN * g


def untype(f, n, shape, k=0):
    """Frame f with only the first n letters typed: the rest of the line, and the block at its end, covered with page;
    then the block (shape: its cover map, in BLOCK) set down where letter n will go."""
    sh, sw = f.shape[:2]
    ys, xs = np.mgrid[0:sh, 0:sw].astype(np.float32)
    lx, ly, slope = LINE[0] * S, LINE[1] * S, LINE[2]
    pitch, up, down = PITCH * S, UP * S, DOWN * S
    bx0, by0, bx1, by1 = block_box()
    x_n = lx + pitch * n + 0.8 * S
    mid = ly + slope * (xs - lx)                                       # the middle of the line of type under each pixel
    edge = x_n - 0.6 * S + LEAN * (ys - (ly + slope * (x_n - lx)))     # the leaning left edge of what is covered
    m = np.clip((xs - edge) / (1.2 * S) + 0.5, 0, 1) * np.clip((ys - (mid - up)) / (2.5 * S) + 0.5, 0, 1) * np.clip(((mid + down) - ys) / (2.5 * S) + 0.5, 0, 1) * np.clip((bx1 + 4 * S - xs) / (3.0 * S), 0, 1)
    drop = int(round(up + down + 6 * S))                               # where clean page is: this far down the frame
    clean = np.roll(f, -drop, axis=0)
    hole = (m > 0.01).astype(np.uint8)
    smooth = cv2.inpaint(np.clip(f, 0, 255).astype(np.uint8), hole, max(3, px(5)), cv2.INPAINT_TELEA).astype(np.float32)
    smooth = cv2.GaussianBlur(smooth, (0, 0), 3.0 * S)                 # the page's own shading across the hole
    grain = clean - cv2.GaussianBlur(clean, (0, 0), 3.0 * S)           # and the frame's own grain, from the clean page below
    f = f * (1 - m[..., None]) + (smooth + grain) * m[..., None]
    dx = pitch * (n - 14)
    dy = slope * dx
    big = np.zeros((sh, sw), np.float32)
    big[by0:by1, bx0:bx1] = shape
    big = cv2.warpAffine(big, np.float32([[1, 0, dx], [0, 1, dy]]), (sw, sh), flags=cv2.INTER_LINEAR)
    return light(f, big, k)


def main():
    global S, W, H
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--size", default="1920x1080")
    W, H = [int(v) for v in ap.parse_args().size.split("x")]
    src = C.best(SRC)
    probe = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height", "-of", "csv=p=0", src], capture_output=True, text=True).stdout.strip().split(",")
    sw, sh = int(probe[0]), int(probe[1])
    S = sw / 854.0
    need = (IN_FRAME + FRAMES + 1)
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", src, "-frames:v", str(max(need, BLOCK_FROM + 1)), "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
    a = np.frombuffer(raw, np.uint8).reshape(-1, sh, sw, 3)
    x0, y0, ww = px(WINDOW[0]), px(WINDOW[1]), px(WINDOW[2])
    hh = int(round(ww * H / W))
    enc = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "%dx%d" % (W, H), "-r", "24", "-i", "-",
                            "-c:v", "libx264", "-preset", "medium", "-crf", "12", "-pix_fmt", "yuv420p", OUT], stdin=subprocess.PIPE)
    shape, _ = block_cover(a[BLOCK_FROM].astype(np.float32))
    assert shape is not None, "the block is not on in source frame %d" % BLOCK_FROM
    edge = 0.55 if S < 1.5 else 0.30                                   # a 480-line source needs more of its edge put back after the punch-in than a 1080-line one
    on = 0
    for k in range(FRAMES):
        f = a[IN_FRAME + k].astype(np.float32)
        bx0, by0, bx1, by1 = block_box()
        if k < len(TYPED):                                             # still typing: the block stands after the last letter typed
            f = untype(f, TYPED[k], shape, k)
            on += 1
        else:
            cover, page = block_cover(f)
            if cover is not None:
                on += 1
                reg = f[by0:by1, bx0:bx1]
                hit = (cover > 0.004)[..., None]                          # only the block's own pixels change: the page and the colon stay the video's
                reg[:] = np.where(hit, page, reg)                         # the dark block out, page in; then the light goes on it
                big = np.zeros((sh, sw), np.float32)
                big[by0:by1, bx0:bx1] = cover
                f = light(f, big, k)
        crop = f[y0:y0 + hh, x0:x0 + ww]
        up = cv2.resize(crop, (W, H), interpolation=cv2.INTER_LANCZOS4)
        soft = cv2.GaussianBlur(up, (0, 0), 2.2 * H / 720.0)
        up = np.clip(up + edge * (up - soft), 0, 255)
        enc.stdin.write(up.astype(np.uint8).tobytes())
    enc.stdin.close()
    enc.wait()
    print("wrote %s at %dx%d from a %d-line source, %d frames; the cursor is on in %d of them" % (os.path.relpath(OUT, C.ROOT), W, H, sh, FRAMES, on))


if __name__ == "__main__":
    main()
