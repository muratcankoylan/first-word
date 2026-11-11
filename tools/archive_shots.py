#!/usr/bin/env python3
"""FIRST WORD: every real archive shot, made again at any size.

    python3 tools/archive_shots.py --size 1920x1080           all of them
    python3 tools/archive_shots.py --size 1920x1080 C04 D08   some of them
    python3 tools/archive_shots.py --check                    compare what this makes with the shots in clips/

Each shot is a crop of a public-domain source moved slowly across, through the scanline pass (tools/scanlines.py).
The crops are in the source's own pixels, so the same recipe gives the same shot at 1280 by 720 or 1920 by 1080; at
the larger size the scanlines are drawn at that size, not enlarged. This file is the recipes from
archive/scanline_recipes.md in a form that runs, with the two that were never written down recovered: the Flyer
(C04) and the bronze (D08) were made on the first day and their commands were not kept, so their crops were found
by matching the finished shots against their sources (the Flyer: a push from 500, 618, 4100 wide to 1150, 980,
3000 wide; the bronze: a pan from 1100, 378 to 1750, 1250 at 1500 wide, with the picture rolling into place).

G32 (the two control rooms) is made by tools/diptych.py and D10 (the print the hand ticks) by tools/printshot.py.
Nothing is done to a real picture here but the crop, the move and the scanline pass; the red wax pencil is drawn
over it, as everywhere.
"""
import argparse
import json
import os
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
A = os.path.join(ROOT, "archive", "src")
S = os.path.join(ROOT, "archive", "selects")

# shot: a list of parts, played one after another. A part: source, frames, start crop, end crop, and what else it takes.
RECIPES = {
    "C01": [dict(src=A + "/C01_nyt-1903-10-09_p6.jp2", frames=35, start="2940,2800,1100", end="2975,2872,1050",
                 marks=[{"kind": "line", "a": [3250, 3153], "b": [3520, 3153], "from": 3, "to": 8},
                        {"kind": "line", "a": [3520, 3153], "b": [3902, 3154], "from": 8, "to": 26},
                        {"kind": "line", "a": [3066, 3210], "b": [3184, 3209], "from": 28, "to": 33}])],
    "C02": [dict(src=A + "/C01_nyt-1903-10-09_p6.jp2", frames=8, start="2150,250,2600", end="2300,250,2450",
                 marks=[{"kind": "ellipse", "c": [4252, 560], "r": [415, 82], "from": 1, "to": 6, "width": 11}]),
            dict(src=A + "/C02_langley-aerodrome-1903-10-07_pl100_wreck-in-water_sck27-p0721.jp2", frames=7, start="330,2190,1640", end="400,2230,1500", roll=2)],
    "C04": [dict(src=A + "/C04_first-flight-1903-12-17_loc-ppprs-00626.tif", frames=25, start="500,618,4100", end="1150,980,3000", keep=17),
            dict(src=A + "/C04_wright-telegram-1903-12-17_loc-wright-papers-02039-0034.tif", frames=8, start="40,800,900", end="52,838,770", roll=2,
                 marks=[{"kind": "line", "a": [76, 1018], "b": [250, 1018], "from": 2, "to": 6, "width": 8}])],
    "D08": [dict(src=A + "/D08_met-23.160.52_DP105609.jpg", frames=25, start="1100,378,1500", end="1750,1250,1500", roll=5)],
    "D09": [dict(src=A + "/D08_met-23.160.52_DP105609.jpg", frames=20, start="1000,400,3000", end="1060,430,2900",
                 marks=[{"kind": "text", "text": "DIVI·NERVAE·F·NERVA", "at": [2455, 812], "cap": 168, "pitch": 176, "from": 2, "per_frame": 2},
                        {"kind": "text", "text": "PTIMVS·AVG·GERM", "at": [2505, 1092], "cap": 172, "pitch": 176, "from": 6, "per_frame": 2},
                        {"kind": "text", "text": "TIFEX·MAXIM·TRIBV", "at": [2565, 1376], "cap": 172, "pitch": 176, "from": 10, "per_frame": 2},
                        {"kind": "text", "text": "T·  XVIII", "at": [2690, 1642], "cap": 168, "pitch": 176, "from": 14, "per_frame": 2}])],
    "G04": [dict(src=A + "/G04_bell-notebook-1876-03-10_loc-magbell-25300201-0022.tif", frames=10, start="2540,140,1500", end="2690,230,1350",
                 marks=[{"kind": "line", "a": [3060, 613], "b": [3400, 611], "from": 1, "to": 4, "width": 10},
                        {"kind": "line", "a": [3545, 611], "b": [3905, 608], "from": 5, "to": 9, "width": 10}])],
    "G05": [dict(src=A + "/G05_switchboard-operators_nara-1633445_86-WWT-28-3.jpg", frames=5, start="250,500,2500", end="330,560,2360")],
    "G11": [dict(src=A + "/G11_ingenuity-first-flight_mastcam-z_liftoff.mp4", at=8.0, frames=5, start="436,470,400", end="440,462,392")],
    "G12": [dict(src=S + "/G12_navcam-first-flight_5-frames.mp4", at=0, frames=5, start="0,50,640", end="8,55,624")],
    "G18": [dict(src=S + "/G18_thruster-ignition_5-frames.mp4", at=0, frames=5, start="778,640,2702", end="798,652,2662")],
    "G20": [dict(src=A + "/G20_hurricane-dorian-eye_iss_2019-09-01_jsc2019m000805.mp4", at=12.0, frames=5, start="50,57,1000", end="60,62,980")],
    "G26": [dict(src=A + "/G26_hubble-milky-way-bulge_wfc3_STScI-2018-01.tif", frames=5, start="200,500,2900", end="260,534,2780")],
}


def make(shot, size, out):
    with tempfile.TemporaryDirectory() as tmp:
        parts = []
        for i, p in enumerate(RECIPES[shot]):
            dest = os.path.join(tmp, "part%d.mp4" % i)
            cmd = [sys.executable, os.path.join(ROOT, "tools", "scanlines.py"), p["src"], dest, "--frames", str(p["frames"]),
                   "--start", p["start"], "--end", p["end"], "--size", size]
            if "at" in p:
                cmd += ["--at", str(p["at"])]
            if p.get("roll"):
                cmd += ["--roll", "--roll-frames", str(p["roll"])]
            if p.get("marks"):
                cmd += ["--marks", json.dumps(p["marks"])]
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL)
            if p.get("keep"):                                   # only the first frames of this part are in the shot
                cut = os.path.join(tmp, "cut%d.mp4" % i)
                subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", dest, "-frames:v", str(p["keep"]), "-c:v", "libx264", "-crf", "10", "-pix_fmt", "yuv420p", cut], check=True)
                if shot == "C04":                               # the whole move is kept too: it is the shot's own first-day form
                    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", dest, "-c", "copy", os.path.join(os.path.dirname(out), "C04_flight_only.mp4")], check=True)
                dest = cut
            parts.append(dest)
        if len(parts) == 1:
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", parts[0], "-c", "copy", out], check=True)
        else:
            ins = sum((["-i", p] for p in parts), [])
            graph = "".join("[%d:v]" % i for i in range(len(parts))) + "concat=n=%d:v=1[v]" % len(parts)
            subprocess.run(["ffmpeg", "-v", "error", "-y"] + ins + ["-filter_complex", graph, "-map", "[v]", "-c:v", "libx264", "-crf", "10", "-pix_fmt", "yuv420p", "-r", "24", out], check=True)


def likeness(a, b):
    """How alike two clips are, frame for frame, both looked at small and grey (1.0 is identical)."""
    import numpy as np

    def read(path):
        raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-vf", "scale=320:180,format=gray", "-f", "rawvideo", "-pix_fmt", "gray", "-"], capture_output=True).stdout
        return np.frombuffer(raw, np.uint8).reshape(-1, 180, 320).astype("float32")
    x, y = read(a), read(b)
    n = min(len(x), len(y))
    out = []
    for i in range(n):
        p, q = x[i] - x[i].mean(), y[i] - y[i].mean()
        out.append(float((p * q).sum() / (((p * p).sum() * (q * q).sum()) ** 0.5 + 1e-9)))
    return len(x), len(y), sum(out) / n, min(out), out.index(min(out))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("shots", nargs="*")
    ap.add_argument("--size", default="1920x1080")
    ap.add_argument("--check", action="store_true", help="make each shot at 1280x720 in a scratch folder and compare it with the one in clips/")
    a = ap.parse_args()
    shots = a.shots or list(RECIPES)
    if a.check:
        with tempfile.TemporaryDirectory() as tmp:
            for s in shots:
                out = os.path.join(tmp, s + ".mp4")
                make(s, "1280x720", out)
                na, nb, mean, worst, at = likeness(os.path.join(ROOT, "clips", s + ".mp4"), out)
                print("%s: %d frames in clips/, %d made here; likeness mean %.3f, worst %.3f at frame %d%s" % (s, na, nb, mean, worst, at, "" if na == nb and worst > 0.9 else "   <-- LOOK"))
        return
    for s in shots:
        make(s, a.size, os.path.join(ROOT, "clips", s + ".mp4"))
        print("wrote clips/%s.mp4 at %s" % (s, a.size))


if __name__ == "__main__":
    main()
