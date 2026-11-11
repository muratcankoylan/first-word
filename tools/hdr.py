#!/usr/bin/env python3
"""FIRST WORD: an HDR version, in which only the film's own lights are brighter than white.

    python3 tools/hdr.py --out out/first_word_v013_hdr_test.mp4 --audio audio/mix_v013.wav
    python3 tools/hdr.py --sheet out/hdr_key.jpg --frames 5,150,190,960,1300,1410     what it would brighten, as pictures

The user asked for HDR so that the film's highlights stand out on a phone. This builds every frame exactly as the
conform does (the same code, no second encode in between) and then writes it as 10-bit HEVC in HLG (BT.2020, ARIB
STD-B67), the form phones and the social platforms play as HDR.

What is ordinary stays ordinary. The whole picture is placed where the standard (ITU-R BT.2408) puts a normal
picture inside HDR: white paper and white type at 203 nits, which is 75 percent of the HLG signal. Faces, paper,
type, a white-out, the flash-lit flowers: none of it is touched.

What is lifted is the film's own light: the cursor, its rings, the tube lights in the hall, the baton, a word that
lands cyan-hot. A pixel counts as that light when it is bright and cyan (green and blue both high, red low), or
when it is the near-white heart of such a light: bright, not warmer than white, and right beside cyan. Those
pixels are raised by up to PEAK times (white there reaches about 800 nits, cyan about 500).

Three limits, so that it glows and does not glare:
  - Real archive footage is never lifted. It takes its scanlines and nothing else, here as everywhere. Nor are
    the ink drawings on white paper: on paper the film's light is ink.
  - When the light fills much of the frame (the baton pushed into the lens), the lift is turned down: a small
    light gets all of it, a frame full of light gets about a third.
  - Nothing goes above the lift named here. There is no stretch of the picture's own shadows or skin.

The generated shots are 8-bit video. Their dark blues are not stretched (stretching them is what shows banding);
only pixels that are already near the top of the range move.

NOT SEEN. I cannot look at an HDR screen. What is checked is arithmetic: which pixels the key picks (--sheet),
and the levels in the finished file. Whether it looks right is for a person with an HDR phone.
"""
import argparse
import os
import subprocess
import sys

import numpy as np
import cv2

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import conform as C  # noqa: E402

FPS = 24
PEAK = 4.0            # the film's lights at most this many times brighter than the same pixel in the standard version
AREA = 0.035          # the share of the frame a light can fill and still get the whole lift
FLOOR = 0.34          # what is left of the lift when the frame is full of light
WHITE_NITS = 203.0    # where white sits in HDR (BT.2408)
M709_2020 = np.array([[0.6274, 0.3293, 0.0433], [0.0691, 0.9195, 0.0114], [0.0164, 0.0880, 0.8956]], np.float32)
Y2020 = np.array([0.2627, 0.6780, 0.0593], np.float32)


def light_key(a, k):
    """How much of each pixel is the film's own light, 0 to 1. a: the finished frame, 8-bit values as floats."""
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    lo = np.minimum(g, b)
    cyan = np.clip((lo - r - 45) / 70.0, 0, 1) * np.clip((lo - 150) / 80.0, 0, 1)        # bright, and cyan: green and blue both high, red low
    luma = 0.2126 * r + 0.7152 * g + 0.0722 * b
    cool = np.clip((b - r + 4) / 22.0, 0, 1)                                              # not warmer than white (white type and lit skin are)
    # The heart of a light is nearly white, so it is found by what surrounds it. Close by (a cursor, a ring): bright
    # and right beside cyan. Further in (the middle of the baton held to the lens, the core of a tube): only what is
    # brighter than any paper in the film (the strips measure 220 at most) and inside a field of cyan.
    near = np.clip(cv2.GaussianBlur(cyan, (0, 0), 9.0 * k) * 3.0 - 0.12, 0, 1)
    far = np.clip(cv2.GaussianBlur(cyan, (0, 0), 60.0 * k) * 6.0 - 0.15, 0, 1)
    heart = np.maximum(np.clip((luma - 185) / 55.0, 0, 1) * near, np.clip((luma - 226) / 14.0, 0, 1) * far) * cool
    return np.maximum(cyan, heart)


def to_hlg(a, key, lift):
    """An 8-bit frame to HLG, 16-bit RGB in BT.2020. key and lift say which pixels are raised and by how much."""
    lin = (a / 255.0) ** 2.4                                         # the standard picture as light on a screen, 1.0 = white
    lin = lin @ M709_2020.T
    lin *= (1.0 + (lift - 1.0) * key)[..., None]
    fd = np.clip(lin * (WHITE_NITS / 1000.0), 0, 1)                  # light on a 1,000 nit HLG screen, 1.0 = its peak
    yd = np.maximum(fd @ Y2020, 1e-6)
    e = fd * (yd ** ((1 - 1.2) / 1.2))[..., None]                    # HLG is light at the camera: undo the screen's 1.2 system gamma
    e = np.clip(e, 0, 1)
    sig = np.where(e <= 1 / 12.0, np.sqrt(3 * e), 0.17883277 * np.log(np.maximum(12 * e - 0.28466892, 1e-6)) + 0.55991073)
    return (np.clip(sig, 0, 1) * 65535 + 0.5).astype(np.uint16), fd @ Y2020 * 1000.0


def frames_of(st, need=None):
    """Every frame of the film (or only those in need), built as the conform builds it, with its shot."""
    for index, s in enumerate(st["shots"]):
        fs = range(s["start"], s["start"] + s["dur"])
        carry = need is not None and s["id"] == "H03" and any(f >= 1380 for f in need)     # the end card needs the baton's last frame
        if need is not None and not carry and not any(f in need for f in fs):
            continue
        frames, base, bg, opts = C.load_shot(st, s)
        for k in range(s["dur"]):
            f = s["start"] + k
            if need is not None and f not in need and not (carry and k == s["dur"] - 1):
                continue
            img = C.compose(st, s, index, k, frames, base, bg, opts)
            if need is None or f in need:
                yield s, f, img


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="")
    ap.add_argument("--audio", default="")
    ap.add_argument("--size", default="1280x720")
    ap.add_argument("--sheet", default="", help="write a sheet of chosen frames beside what the key picks in each, and stop")
    ap.add_argument("--frames", default="5,150,190,300,640,960,1000,1300,1360,1383,1410,1430")
    a = ap.parse_args()
    C.W, C.H = [int(v) for v in a.size.split("x")]
    C.K = C.H / 720.0
    W, H, K = C.W, C.H, C.K
    st = C.load_state(True, "hdr")
    want = set(int(v) for v in a.frames.split(",")) if a.sheet else None
    enc = None
    if not a.sheet:
        cmd = ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb48le", "-s", "%dx%d" % (W, H), "-r", str(FPS), "-i", "-"]
        if a.audio:
            cmd += ["-i", a.audio, "-c:a", "aac", "-b:a", "256k"]
        cmd += ["-vf", "scale=in_range=full:out_range=limited:out_color_matrix=bt2020:flags=accurate_rnd+full_chroma_int,format=yuv420p10le",
                "-c:v", "libx265", "-preset", "medium", "-crf", "15", "-tag:v", "hvc1",
                "-x265-params", "colorprim=bt2020:transfer=arib-std-b67:colormatrix=bt2020nc:range=limited:log-level=error",
                "-color_primaries", "bt2020", "-color_trc", "arib-std-b67", "-colorspace", "bt2020nc", "-color_range", "tv",
                "-r", str(FPS), "-t", "%.6f" % (st["total"] / FPS), "-movflags", "+faststart", a.out]
        enc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    tiles, ease, last_shot = [], 1.0, None
    peak_nits, lit_frames, top = 0.0, 0, []
    for s, f, img in frames_of(st, want):
        arr = np.asarray(img).astype(np.float32)
        # What is real is never lifted. Nor is a drawing on white paper: there the film's light is ink, as it is in the
        # standard version (and an impact's colour fringes on a white page would be taken for light).
        plain = "ARCHIVE" in s["source"] or s["source"].startswith("INK")
        key = np.zeros((H, W), np.float32) if plain else light_key(arr, K)
        area = float(key.mean())
        scale = max(FLOOR, min(1.0, (AREA / max(area, 1e-6)) ** 0.5))
        ease = scale if s["id"] != last_shot else 0.5 * ease + 0.5 * scale          # the turn-down eases in over a few frames, and starts afresh at a cut
        last_shot = s["id"]
        lift = 1.0 + (PEAK - 1.0) * ease
        out, nits = to_hlg(arr, key, lift)
        m = float(np.percentile(nits, 99.9))
        peak_nits = max(peak_nits, float(nits.max()))
        lit_frames += m > WHITE_NITS * 1.15
        top.append((m, f, s["id"], area, lift))
        if a.sheet:
            from PIL import Image, ImageDraw
            w2 = 480
            h2 = w2 * H // W
            pic = img.resize((w2, h2), Image.LANCZOS)
            km = Image.fromarray(np.clip(key * 255, 0, 255).astype(np.uint8)).resize((w2, h2), Image.LANCZOS).convert("RGB")
            ImageDraw.Draw(km).text((4, 3), "%s f%d  lit %.1f%% of frame  lift x%.2f  top %.0f nits" % (s["id"], f, 100 * area, lift, float(nits.max())), fill=(255, 255, 0))
            t = Image.new("RGB", (w2 * 2, h2))
            t.paste(pic, (0, 0))
            t.paste(km, (w2, 0))
            tiles.append(t)
        else:
            enc.stdin.write(out.tobytes())
    if a.sheet:
        from PIL import Image
        cols = 2
        rows = (len(tiles) + cols - 1) // cols
        sheet = Image.new("RGB", (tiles[0].size[0] * cols, tiles[0].size[1] * rows))
        for i, t in enumerate(tiles):
            sheet.paste(t, ((i % cols) * t.size[0], (i // cols) * t.size[1]))
        sheet.save(a.sheet, quality=88)
        print("wrote", a.sheet, sheet.size)
        return
    enc.stdin.close()
    if enc.wait() != 0:
        sys.exit("ffmpeg failed")
    top.sort(reverse=True)
    print("wrote %s: %d frames. White sits at %.0f nits. Brightest pixel anywhere: %.0f nits. Frames with light above white: %d of %d." % (
        a.out, len(top), WHITE_NITS, peak_nits, lit_frames, len(top)))
    print("the brightest frames (99.9th percentile of the frame, nits): " + ", ".join("f%d %s %.0f" % (f, sid, m) for m, f, sid, _, _ in top[:8]))


if __name__ == "__main__":
    main()
