#!/usr/bin/env python3
"""FIRST WORD: look at a generated clip without playing it.

    python3 tools/checkclip.py clips/drafts/ray_reel.mp4 [--step 0.5] [--cols 6]

Writes out/check/<name>.jpg, a contact sheet with the time burnt into every frame, prints where the picture
cuts, and prints every word heard in the clip's own sound with its time. A shot's in-point is set from
these: the time the line starts in the clip, less the frames between the shot's start and the line's start.

The words come from a transcription (ElevenLabs Scribe). Nothing here listens to how a voice sounds.
"""
import argparse
import json
import math
import os
import subprocess
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import voices as V  # noqa: E402

FPS = 24


def cuts(path):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-vf", "fps=%d,scale=64:36,format=gray" % FPS,
                          "-f", "rawvideo", "-"], capture_output=True).stdout
    x = np.frombuffer(raw, np.uint8).reshape(-1, 36 * 64).astype(np.float32)
    d = np.abs(np.diff(x, axis=0)).mean(axis=1)
    return len(x), [int(i) + 1 for i in np.where(d > 22)[0]]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("clip")
    ap.add_argument("--step", type=float, default=0.5)
    ap.add_argument("--cols", type=int, default=6)
    ap.add_argument("--width", type=int, default=400)
    ap.add_argument("--no-words", action="store_true")
    a = ap.parse_args()
    name = os.path.splitext(os.path.basename(a.clip))[0]
    out = V.J("out", "check")
    os.makedirs(out, exist_ok=True)
    n, cs = cuts(a.clip)
    shots = math.ceil(n / FPS / a.step)
    rows = math.ceil(shots / a.cols)
    sheet = os.path.join(out, name + ".jpg")
    vf = ("fps=1/%s,scale=%d:-2,drawtext=text='%%{pts\\:hms}':x=6:y=6:fontsize=16:fontcolor=white:box=1:boxcolor=black@0.6,"
          "tile=%dx%d") % (a.step, a.width, a.cols, rows)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", a.clip, "-vf", vf, "-frames:v", "1", "-q:v", "4", sheet], check=True)
    print("%s: %d frames (%.2f s), sheet %s" % (name, n, n / FPS, os.path.relpath(sheet, V.ROOT)))
    print("cuts at: " + ", ".join("%.2f s" % (c / FPS) for c in cs))
    if a.no_words:
        return
    mp3 = os.path.join(out, name + ".mp3")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", a.clip, "-vn", "-ac", "1", "-ar", "44100", "-b:a", "128k", mp3], check=True)
    if os.path.exists(mp3 + ".stt.json"):
        os.remove(mp3 + ".stt.json")
    t = V.transcribe(mp3)
    words = [w for w in t.get("words", []) if w.get("type", "word") == "word"]
    json.dump([[w["text"], round(w["start"], 3), round(w["end"], 3)] for w in words], open(os.path.join(out, name + ".words.json"), "w"))
    print("heard: " + t.get("text", "").strip())
    line, last = [], None
    for w in words:
        if last is not None and w["start"] - last > 0.6:
            print("   " + "  ".join(line))
            line = []
        line.append("%s@%.2f" % (w["text"], w["start"]))
        last = w["end"]
    if line:
        print("   " + "  ".join(line))


if __name__ == "__main__":
    main()
