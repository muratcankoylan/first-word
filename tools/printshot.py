#!/usr/bin/env python3
"""FIRST WORD: the printed photograph the red pencil ticks (shot D10).

    python3 tools/printshot.py [--size 1280x720]      writes clips/D10.mp4

The generated plate shows a hand ticking a print on a steel bench, but the print the model drew is of a bronze
that does not exist. This puts the real one there: the Met's photograph of the diploma (archive/src/D08...), with
the restoration printed in the Aeneas paper's Fig. 1 set beside it in grey, the same four lines shot D09 draws.
The print is laid on the card in the plate's own perspective and takes the plate's light and shadow; the hand,
the pencil and the tick stay the plate's.
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
import scanlines as S  # noqa: E402

ROOT = C.ROOT
PHOTO = os.path.join(ROOT, "archive", "src", "D08_met-23.160.52_DP105609.jpg")
PLATE = {"clip": "drafts/macro_hands.mp4", "in": 6.0}
# the card's corners in the plate, as fractions of the frame: near left, far, and near (the fourth follows)
CARD = {"a": (0.010, 0.592), "b": (0.404, 0.288), "d": (0.200, 0.934)}
INSET = 0.045                 # the print's white border
LINES = [("DIVI·NERVAE·F·NERVA", (2455, 812), 168), ("PTIMVS·AVG·GERM", (2505, 1092), 172),
         ("TIFEX·MAXIM·TRIBV", (2565, 1376), 172), ("T·  XVIII", (2690, 1642), 168)]


def the_print():
    """The photograph, its ground carried on to the right, and the restored letters where the bronze breaks off."""
    ph = Image.open(PHOTO).convert("RGB")
    a = np.asarray(ph, np.float32)
    ground = np.median(np.concatenate([a[40:200, 3700:3960].reshape(-1, 3), a[3700:3960, 3700:3960].reshape(-1, 3)]), axis=0)
    wide = np.empty((4000, 6300, 3), np.float32)
    wide[:] = ground
    wide[:, :4000] = a
    ramp = np.clip((np.arange(6300) - 3700) / 300.0, 0, 1)[None, :, None]       # no seam where the photograph ends
    wide = wide * (1 - ramp) + ground * ramp
    img = Image.fromarray(np.clip(wide, 0, 255).astype(np.uint8))
    marks = [dict(kind="text", text=t, at=list(at), cap=cap, pitch=176, per_frame=99, color=[84, 88, 96]) for t, at, cap in LINES]
    marks = [dict(m, **{"from": 0}) for m in marks]
    img = S.letters(img, marks, 5, lambda p: p, 1.0)
    return img.crop((560, 330, 6090, 3830))                                     # 1.58 to 1, the card's own shape


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--size", default="1280x720")
    a = ap.parse_args()
    W, H = [int(v) for v in a.size.split("x")]
    C.W, C.H, C.K = W, H, H / 720.0
    n = 15
    frames = C.clip_frames(os.path.join(ROOT, "clips", PLATE["clip"]), n, PLATE)
    A, B, D = [np.array([CARD[k][0] * W, CARD[k][1] * H], np.float32) for k in "abd"]
    def at(u, v):
        return A + u * (B - A) + v * (D - A)
    pr = the_print()
    pw, ph_ = 1100, int(1100 / 1.58)
    pr = np.asarray(pr.resize((pw, ph_), Image.LANCZOS), np.float32)
    src = np.array([[0, 0], [pw, 0], [0, ph_]], np.float32)
    dst = np.array([at(INSET, INSET * 1.58), at(1 - INSET, INSET * 1.58), at(INSET, 1 - INSET * 1.58)], np.float32)
    M = cv2.getAffineTransform(src, dst)
    warped = cv2.warpAffine(pr, M, (W, H), flags=cv2.INTER_AREA)
    inside = cv2.warpAffine(np.ones((ph_, pw), np.float32), M, (W, H), flags=cv2.INTER_LINEAR)
    inside = cv2.GaussianBlur(inside, (0, 0), 1.2 * C.K)
    f0 = np.asarray(frames[0], np.float32)
    lum0 = f0.mean(axis=2)
    sat0 = f0.max(axis=2) - f0.min(axis=2)
    xs = np.arange(W, dtype=np.float32)[None, :] / W
    # what the model drew on the card: dark, and not skin or pencil, left of where the hand ever comes
    drawn = ((lum0 < 122) & (f0[:, :, 0] - f0[:, :, 2] < 22) & (inside > 0.5) & (xs < 0.475)).astype(np.uint8)
    drawn = cv2.dilate(cv2.morphologyEx(drawn, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8)), np.ones((13, 13), np.uint8))
    drawn_soft = cv2.GaussianBlur(drawn.astype(np.float32), (0, 0), 3 * C.K)
    # the bare card's own light, as a plane fitted where nothing is drawn and no shadow falls
    ys_, xs_ = np.nonzero((inside > 0.9) & (drawn == 0) & (lum0 > 128) & (xs < 0.43))
    G = np.stack([xs_, ys_, np.ones_like(xs_)], axis=1).astype(np.float32)
    plane = []
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    for c in range(3):
        coef, *_ = np.linalg.lstsq(G, f0[ys_, xs_, c], rcond=None)
        plane.append(coef[0] * xx + coef[1] * yy + coef[2])
    plane = np.stack(plane, axis=2)
    out = []
    for f in frames:
        p = np.asarray(f, np.float32)
        shade = np.clip(p.mean(axis=2) / np.maximum(1, plane.mean(axis=2)), 0.12, 1.12)
        shade = shade * (1 - drawn_soft) + drawn_soft                     # under the drawn bronze the card is taken as bare
        sat = p.max(axis=2) - p.min(axis=2)
        keep = np.clip((sat - 20) / 22.0, 0, 1) * (1 - drawn_soft)        # skin, the pencil and its mark stay the plate's
        keep = np.maximum(keep, np.clip((0.33 - shade) / 0.12, 0, 1))     # and so does the deep shadow of the hand
        printed = warped * (plane / 228.0) * shade[..., None]
        printed = cv2.GaussianBlur(printed, (0, 0), 0.9 * C.K)
        mix = (inside * (1 - keep))[..., None]
        out.append(Image.fromarray(np.clip(p * (1 - mix) + printed * mix, 0, 255).astype(np.uint8)))
    path = os.path.join(ROOT, "clips", "D10.mp4")
    enc = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "%dx%d" % (W, H), "-r", "24", "-i", "-",
                            "-c:v", "libx264", "-preset", "medium", "-crf", "14", "-pix_fmt", "yuv420p", path], stdin=subprocess.PIPE)
    for f in out:
        enc.stdin.write(f.tobytes())
    enc.stdin.close()
    enc.wait()
    print("wrote clips/D10.mp4, %d frames" % len(out))


if __name__ == "__main__":
    main()
