#!/usr/bin/env python3
"""FIRST WORD: two pictures in one frame, for the two shots that answer "We'll fix it."

    python3 tools/diptych.py [--size 1280x720]      clips/G32.mp4 (1969 beside 2021) and clips/G33.mp4 (Rosa beside Ray)

The first message between two computers on the network that became the internet needs more than twenty frames to be
read: what was being typed, that it crashed, and that it was fixed. Ten frames were found for it here. The four cuts
that followed it (a control room in 1969, Rosa laughing, a control room in 2021, Ray laughing) are now two frames of
five, each holding a pair: the two rooms side by side, jumping the same jump 52 years apart, and the two people side
by side, one in her kitchen and one out at blue hour.

Nothing is done to the real pictures but the crop. Each room is made by tools/scanlines.py at the half frame's own
size, so its scanlines are drawn at full sharpness and are not scaled, and the conform then gives each half a tube of
its own (the "tubes": 2 entry in timing/cutin.json). The 1969 film is four by three, so its half is taken at one
source pixel to one film pixel, where the whole-frame shot it replaces was enlarged by a third.

The people come from the same reels and the same moments as the two shots they replace (rosa_pip_reel at 11.6 s,
ray_reel at 16.6 s), framed by the conform's own code. When the drafts are enhanced to 1080p, run this again with
--size 1920x1080.
"""
import argparse
import os
import subprocess
import sys
import tempfile

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import conform as C  # noqa: E402

A = os.path.join(C.ROOT, "archive", "src")
FRAMES = 5
GUTTER = 8                      # black between the two pictures, in pixels of a 1280 frame
ROOMS = [                       # source, the second it is taken from, start crop and end crop (left, top, width) in the source's pixels
    ("G32_apollo11-mocr-celebration-film_1969-07-24_nasa-hd-resource-reel-part09.mp4", 24.5, (300, 0, 636), (308, 5, 626)),
    ("G34_perseverance-landing_jpl-control-room.mp4", 6.2, (330, 0, 636), (338, 5, 626)),
]
PEOPLE = [                      # clip, what the conform's framing takes, and the centre of the half that is kept (0 to 1 across the frame)
    ("drafts/rosa_pip_reel.mp4", {"in": 11.6}, 0.45),
    ("drafts/ray_reel.mp4", {"in": 16.6, "zoom": 1.08, "dx": 0.0, "dy": -0.035}, 0.50),
]


def read(path, w, h):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(-1, h, w, 3)


def write(path, frames, w, h):
    enc = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "%dx%d" % (w, h), "-r", "24", "-i", "-",
                            "-c:v", "libx264", "-preset", "medium", "-crf", "14", "-pix_fmt", "yuv420p", path], stdin=subprocess.PIPE)
    for f in frames:
        enc.stdin.write(np.ascontiguousarray(f).tobytes())
    enc.stdin.close()
    if enc.wait() != 0:
        sys.exit("ffmpeg failed on " + path)
    print("wrote", os.path.relpath(path, C.ROOT))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--size", default="1280x720")
    a = ap.parse_args()
    W, H = [int(v) for v in a.size.split("x")]
    k = H / 720.0
    g = int(round(GUTTER * k / 2)) * 2
    hw = (W - g) // 2                                         # one half's width

    # the two rooms: each through the scanline pass at the half's own size
    halves = []
    with tempfile.TemporaryDirectory() as tmp:
        for i, (src, at, c0, c1) in enumerate(ROOMS):
            out = os.path.join(tmp, "half%d.mp4" % i)
            subprocess.run([sys.executable, os.path.join(C.ROOT, "tools", "scanlines.py"), os.path.join(A, src), out, "--at", str(at), "--frames", str(FRAMES),
                            "--start", "%d,%d,%d" % c0, "--end", "%d,%d,%d" % c1, "--size", "%dx%d" % (hw, H)], check=True)
            halves.append(read(out, hw, H))
    frames = []
    for j in range(FRAMES):
        f = np.zeros((H, W, 3), np.uint8)
        f[:, :hw] = halves[0][min(j, len(halves[0]) - 1)]
        f[:, W - hw:] = halves[1][min(j, len(halves[1]) - 1)]
        frames.append(f)
    write(os.path.join(C.ROOT, "clips", "G32.mp4"), frames, W, H)

    # the two people: the conform's own framing of each, and the half of it they are in
    C.W, C.H, C.K = W, H, k
    strips = []
    for clip, opts, centre in PEOPLE:
        fr = C.clip_frames(os.path.join(C.ROOT, "clips", clip), FRAMES, opts)
        x0 = int(round(min(W - hw, max(0, centre * W - hw / 2))))
        strips.append([np.asarray(im)[:, x0:x0 + hw] for im in fr])
    frames = []
    for j in range(FRAMES):
        f = np.zeros((H, W, 3), np.uint8)
        f[:, :hw] = strips[0][j]
        f[:, W - hw:] = strips[1][j]
        frames.append(f)
    write(os.path.join(C.ROOT, "clips", "G33.mp4"), frames, W, H)


if __name__ == "__main__":
    main()
