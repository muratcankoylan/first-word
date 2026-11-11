#!/usr/bin/env python3
"""FIRST WORD: the whale crossing the reflection in Pip's eye (shot H02).

    python3 tools/eyeshot.py [--size 1280x720]      writes clips/H02.mp4

The generated macro of the eye reflects the sky and the skyline but no whale. A sperm whale's outline, drawn
here, is carried small and dark across the bright patch of sky in the eye, from right to left: a mirror shows
it the other way round from the wide shot. It is drawn only where the eye reflects sky, so it passes behind
the skyline and the lashes.
"""
import argparse
import json
import os
import subprocess
import sys

import cv2
import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import conform as C  # noqa: E402

ROOT = C.ROOT


WHALE = [(0.000, 0.300), (0.012, 0.215), (0.060, 0.165), (0.180, 0.135), (0.330, 0.125), (0.520, 0.150), (0.640, 0.195), (0.672, 0.160),
         (0.700, 0.168), (0.725, 0.225), (0.800, 0.290), (0.880, 0.345), (0.925, 0.372), (0.955, 0.300), (0.985, 0.245), (1.000, 0.250),
         (0.982, 0.400), (1.000, 0.560), (0.982, 0.565), (0.950, 0.505), (0.922, 0.452), (0.870, 0.470), (0.780, 0.535), (0.660, 0.615),
         (0.540, 0.668), (0.430, 0.690), (0.372, 0.680), (0.395, 0.790), (0.352, 0.842), (0.318, 0.760), (0.300, 0.690), (0.252, 0.668),
         (0.238, 0.700), (0.085, 0.660), (0.070, 0.628), (0.215, 0.622), (0.190, 0.590), (0.040, 0.545), (0.004, 0.470)]


def whale_outline(W, H):
    """A sperm whale in profile, head to the left: the square head, the thin jaw under it, the low hump, the flukes.
    Drawn, not traced: in the wide shot the frame cuts the whale off, so there is no whole outline there to take."""
    S = 1200
    im = Image.new("L", (S, int(S * 0.9)), 0)
    from PIL import ImageDraw
    ImageDraw.Draw(im).polygon([(x * S, y * S) for x, y in WHALE], fill=255)
    m = np.asarray(im, np.float32) / 255
    m = cv2.GaussianBlur(m, (0, 0), 7)                                    # round the corners of the drawing
    m = np.clip((m - 0.5) * 6 + 0.5, 0, 1)
    ys, xs = np.nonzero(m > 0.5)
    return m[ys.min():ys.max() + 1, xs.min():xs.max() + 1]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--size", default="1280x720")
    a = ap.parse_args()
    W, H = [int(v) for v in a.size.split("x")]
    C.W, C.H, C.K = W, H, H / 720.0
    man = json.load(open(os.path.join(ROOT, "clips", "manifest.json")))
    man = man.get("shots", man)
    src = dict(man["H02"]) if man.get("H02", {}).get("file", "").startswith("whale") else {"file": "whale_1080.mp4", "in": 7.4}
    n = 16
    frames = C.clip_frames(os.path.join(ROOT, "clips", src["file"]), n, {"in": src.get("in", 7.4)})
    whale = whale_outline(W, H)
    out = []
    for k, f in enumerate(frames):
        p = np.asarray(f, np.float32)
        sky = ((p[:, :, 2] > 150) & (p[:, :, 2] > p[:, :, 0] + 60) & (p[:, :, 1] > 90)).astype(np.uint8)     # the patch of sky in the eye
        nlab, lab, stats, _ = cv2.connectedComponentsWithStats(sky)
        if nlab < 2:
            out.append(f)
            continue
        j = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
        x, y, w, h = [int(stats[j, c]) for c in (cv2.CC_STAT_LEFT, cv2.CC_STAT_TOP, cv2.CC_STAT_WIDTH, cv2.CC_STAT_HEIGHT)]
        region = cv2.GaussianBlur((lab == j).astype(np.float32), (0, 0), 1.2 * C.K)
        ww = int(w * 0.58)
        wh = max(2, int(ww * whale.shape[0] / whale.shape[1]))
        small = cv2.resize(whale, (ww, wh), interpolation=cv2.INTER_AREA)
        t = k / (n - 1)
        cx = x + w * (1.12 - 1.30 * t)                                      # in from the right, out to the left
        cy = y + h * (0.36 + 0.05 * np.sin(t * 3.1))
        x0, y0 = int(cx - ww / 2), int(cy - wh / 2)
        matte = np.zeros((H, W), np.float32)
        xa, ya, xb, yb = max(0, x0), max(0, y0), min(W, x0 + ww), min(H, y0 + wh)
        if xb > xa and yb > ya:
            matte[ya:yb, xa:xb] = small[ya - y0:yb - y0, xa - x0:xb - x0]
        matte = cv2.GaussianBlur(matte, (0, 0), 1.7 * C.K) * region * 0.80
        body = np.array([34, 58, 104], np.float32)                           # a dark shape against the reflected sky
        out.append(Image.fromarray(np.clip(p * (1 - matte[..., None]) + body * matte[..., None], 0, 255).astype(np.uint8)))
    path = os.path.join(ROOT, "clips", "H02.mp4")
    enc = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "%dx%d" % (W, H), "-r", "24", "-i", "-",
                            "-c:v", "libx264", "-preset", "medium", "-crf", "13", "-pix_fmt", "yuv420p", path], stdin=subprocess.PIPE)
    for f in out:
        enc.stdin.write(f.tobytes())
    enc.stdin.close()
    enc.wait()
    print("wrote clips/H02.mp4, %d frames" % len(out))


if __name__ == "__main__":
    main()
