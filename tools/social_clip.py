#!/usr/bin/env python3
"""FIRST WORD: a short clip of the film for a social post.

A clip is made from a recipe folder, which holds a frozen copy of everything the clip needs from the cut, so
the clip stays the same while the film keeps changing.

    python3 tools/social_clip.py new out/social/teaser_v2_src       freeze the cut as it stands into a recipe
    python3 tools/social_clip.py render out/social/teaser_v1_src    build out/social/teaser_v1.mp4 from its recipe
    python3 tools/social_clip.py render out/social/teaser_v1_src --card film --out out/social/teaser_v1_filmcard.mp4

The clip is stretches of the cut (by default the opening line-up and the whale ending) rendered clean at
1920x1080 with the film's own captions and type, joined, over the same stretches of the film mix.

In a recipe:
    clip.json       the stretches, the end card, the mix, and any line taken from a generated shot's own sound
    manifest.json   which clip and in-point each shot plays
    clips/          its own copies of those clips (drafts in the project get deleted once a take is chosen)
    shotlist.json, lines.json, type.json, words.json, scratch_durations.json    the cut, frozen
    conform.py      the caption and type code, frozen
    audio.wav       the finished soundtrack, built on the first render (delete it to rebuild)

"new" changes three things that are not ready to be seen, in the recipe only:
  - the cyan blocks standing in for the ink layer and the maker's mark are left out (at render time);
  - a shot that is still a card inside a run of footage plays the footage before it on through;
  - Osei's line-up shot comes from the repair draft while the cut still points at the draft that cast him wrong.
A card can never reach a clip: the render stops if a stretch contains a shot with no picture.

This tool writes only under out/social/. It never changes the cut, the mix or the ledger.
"""
import argparse
import glob
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import wave

import numpy as np
from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FPS, SR = 24, 48000
SPF = SR // FPS  # samples per frame
FROZEN = {"shotlist.json": ("shotlist.json",), "lines.json": ("timing", "lines.json"), "type.json": ("timing", "type.json"),
          "words.json": ("timing", "words.json"), "scratch_durations.json": ("timing", "scratch_durations.json")}
CREDIT = [[1390, 0.60, "A 60-SECOND FILM, IN PRODUCTION."],
          [1400, 0.665, "WRITTEN, DIRECTED AND CUT BY CLAUDE FABLE 5.2."],
          [1410, 0.73, "PICTURE BY SEEDANCE 2.5. EVERYONE ON SCREEN WAS GENERATED."]]
C = None  # the conform module in use


def J(*p):
    return os.path.join(ROOT, *p)


def load_conform(path):
    global C
    spec = importlib.util.spec_from_file_location("conform_for_clip", path)
    C = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(C)


# ---------------------------------------------------------------- picture
def source_height(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=height",
                          "-of", "csv=p=0", path], capture_output=True, text=True).stdout.strip()
    return int(out.split(",")[0]) if out else C.H


def load(path, n, start, zoom):
    """n frames of a clip from a start time, filled to the frame. Small sources are scaled with Lanczos and
    lightly sharpened; zoom > 1 punches in on the centre, as in the conform."""
    W, H = C.W, C.H
    if path.lower().endswith((".png", ".jpg", ".jpeg")):
        return [C.fit(Image.open(path).convert("RGB"))] * n
    zw, zh = int(round(W * zoom / 2)) * 2, int(round(H * zoom / 2)) * 2
    vf = "fps=%d,scale=%d:%d:force_original_aspect_ratio=increase:flags=lanczos,crop=%d:%d" % (FPS, zw, zh, W, H)
    if zh / source_height(path) > 1.6:
        vf += ",unsharp=5:5:0.45:5:5:0.0"
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(start), "-i", path, "-frames:v", str(n), "-vf", vf,
                          "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
    size = W * H * 3
    frames = [Image.frombytes("RGB", (W, H), raw[i * size:(i + 1) * size]) for i in range(len(raw) // size)]
    if not frames:
        sys.exit("no frames from %s at %s" % (path, start))
    while len(frames) < n:
        frames.append(frames[-1])
    return frames


def have_file(sid):
    return any(os.path.exists(J("clips", sid + ext)) for ext in (".mp4", ".mov", ".png", ".jpg"))


def inside(s, ranges):
    return any(a < s["start"] + s["dur"] and s["start"] < b for a, b in ranges)


def overrides(shots, manifest, ranges, clean):
    """Picture for shots that are not ready. Each one lapses by itself when the cut is fixed."""
    m = {k: dict(v) for k, v in manifest.items()}
    notes = []
    fix = "drafts/lineup_fix.mp4"
    if m.get("A06", {}).get("file") == "drafts/lineup_t1.mp4" and os.path.exists(J("clips", fix)):
        m["A06"] = {"file": fix, "in": 0.6}
        notes.append("A06: Osei from the repair draft")
    for prev, s in zip(shots, shots[1:]):
        if not inside(s, ranges) or s["id"] in m or s["id"] in clean or have_file(s["id"]):
            continue
        if prev["id"] in m and prev["start"] + prev["dur"] == s["start"]:
            m[s["id"]] = {"file": m[prev["id"]]["file"], "in": round(float(m[prev["id"]].get("in", 0)) + prev["dur"] / FPS, 4),
                          "zoom": m[prev["id"]].get("zoom", 1.0)}
            notes.append("%s: no picture yet, so %s plays on through it" % (s["id"], prev["id"]))
    return m, notes


SOURCES = ""  # a recipe's own copies of the clips it plays, when it has them


def src(rel):
    own = os.path.join(SOURCES, rel) if SOURCES else ""
    return own if own and os.path.exists(own) else J("clips", rel)


def clip_for(sid, m):
    if sid in m:
        return src(m[sid]["file"]), float(m[sid].get("in", 0)), float(m[sid].get("zoom", 1.0))
    for ext in (".mp4", ".mov", ".png", ".jpg"):
        if os.path.exists(J("clips", sid + ext)):
            return J("clips", sid + ext), 0.0, 1.0
    return None, 0.0, 1.0


def type_events(events, ranges, clip, card, hold, total):
    out = []
    for e in events:
        if e["style"] in ("rect", "sweep") and any(a < e["out"] and e["in"] < b for a, b in ranges):
            continue  # stand-ins for layers that are not drawn yet
        e = dict(e)
        if card == "credit" and e.get("shot") == "I01" and e["style"] == "small":
            continue
        if e["out"] >= total:  # the last card holds a little longer than the film does
            e["out"] = total + hold
        out.append(e)
    if card == "credit":
        for at, y, text in clip.get("credit", CREDIT):
            out.append({"shot": "I01", "in": at, "out": total + hold, "style": "small", "text": text, "x": 0.15, "y": y,
                        "scale": clip.get("credit_scale", 1.15)})
    return out


# ---------------------------------------------------------------- sound
def decode(path, ss=None, t=None):
    cmd = ["ffmpeg", "-v", "error"] + (["-ss", str(ss)] if ss is not None else []) + (["-t", str(t)] if t is not None else [])
    raw = subprocess.run(cmd + ["-i", path, "-vn", "-f", "f32le", "-ac", "2", "-ar", str(SR), "-"], capture_output=True).stdout
    return np.frombuffer(raw, np.float32).reshape(-1, 2).astype(np.float64)


def band(x, lo, hi):
    X = np.fft.rfft(x, axis=0)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    X[(f < lo) | (f > hi)] = 0
    return np.fft.irfft(X, len(x), axis=0)


def speech_level(x):
    """RMS of the speech band over the stretches where someone is actually speaking."""
    m = band(x.mean(axis=1), 300, 3400)
    hop = SR // 50
    e = np.array([np.mean(m[i:i + hop] ** 2) for i in range(0, len(m) - hop + 1, hop)])
    if not len(e) or e.max() <= 0:
        return 0.0
    return float(np.sqrt(e[e > e.max() / 100.0].mean()))


def ramp(n, up=True):
    r = 0.5 - 0.5 * np.cos(np.linspace(0, np.pi, n))
    return (r if up else r[::-1])[:, None]


def loudness(path):
    err = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", path, "-af", "loudnorm=print_format=json",
                          "-f", "null", "-"], capture_output=True, text=True).stderr
    d = json.loads(err[err.rindex("{"):err.rindex("}") + 1])
    return float(d["input_i"]), float(d["input_tp"])


def write_wav(path, x):
    y = (np.clip(x, -1, 1) * 32767.0).astype("<i2")
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(y.tobytes())


def frame_of(t, shot, entry):
    """Film frame at which a moment of a shot's clip plays."""
    return shot["start"] + (t - float(entry.get("in", 0))) * FPS


def build_audio(clip, shots, manifest, ranges, hold, out_wav, target=-14.0, ceiling=-1.0):
    film = decode(J(clip["mix"]))
    by_id = {s["id"]: s for s in shots}
    notes = []
    stems = None
    for p in clip.get("production", []):
        # A line spoken on camera, taken from the generated shot's own sound so the lips match. The stand-in
        # line is cut out of the mix: from cut_at to the end of its stretch the mix is rebuilt from the stems.
        if stems is None:
            stems = {k: decode(J("audio", "stems", k + ".wav")) for k in ("dialogue", "effects", "score", "whale")}
            n = min([len(film)] + [len(v) for v in stems.values()])
            total_stems = sum(v[:n] for v in stems.values())
            bed = sum(stems[k][:n] for k in ("effects", "score", "whale"))
        shot, entry = by_id[p["shot"]], manifest[p["shot"]]
        ra, rb = [r for r in ranges if r[0] <= shot["start"] < r[1]][0]
        a, b = int(round(p["cut_at"] * SPF)), rb * SPF
        w0 = max(0, a - 40 * SPF)
        g = float((film[w0:a] * total_stems[w0:a]).sum() / ((total_stems[w0:a] ** 2).sum() + 1e-20))  # the master's gain here
        rebuilt = g * bed[a:b]
        line = decode(src(entry["file"]), ss=p["from"], t=p["to"] - p["from"])
        line = band(line, 80, 16000)
        fi, fo = int(0.04 * SR), int(0.08 * SR)
        line[:fi] *= ramp(fi)
        line[-fo:] *= ramp(fo, up=False)
        ref, cur = speech_level(g * stems["dialogue"][a:b]), speech_level(line)
        gain = ref / cur if cur > 0 and ref > 0 else 1.0
        gain = min(gain, 0.9 / (np.abs(line).max() + 1e-9))
        s0 = int(round(frame_of(p["from"], shot, entry) * SPF)) - a
        if s0 < 0:
            sys.exit("%s: the line starts before cut_at" % p["line"])
        k = min(len(line), len(rebuilt) - s0)
        rebuilt[s0:s0 + k] += gain * line[:k]
        x = int(0.015 * SR)
        rebuilt[:x] = rebuilt[:x] * ramp(x) + film[a:a + x] * ramp(x, up=False)
        film[a:b] = rebuilt
        notes.append("%s: the voice from %s, %.2f to %.2f s, lands at frame %.1f (gain %+.1f dB, master gain here %.2f)" % (
            p["line"], entry["file"], p["from"], p["to"], frame_of(p["from"], shot, entry), 20 * np.log10(gain), g))
    parts = []
    for a, b in ranges:
        seg = film[a * SPF:b * SPF].copy()
        if len(seg) < (b - a) * SPF:
            seg = np.vstack([seg, np.zeros(((b - a) * SPF - len(seg), 2))])
        n = int(0.008 * SR)  # 8 ms: enough to stop a click, short enough to keep the cut hard
        seg[:n] *= ramp(n)
        seg[-n:] *= ramp(n, up=False)
        parts.append(seg)
    parts.append(np.zeros((hold * SPF, 2)))
    y = np.vstack(parts)
    write_wav(out_wav, y)
    i0, tp0 = loudness(out_wav)
    gain = min(target - i0, ceiling - tp0)
    write_wav(out_wav, y * 10 ** (gain / 20.0))
    i1, tp1 = loudness(out_wav)
    notes.append("sound: %.1f LUFS, true peak %.1f dBTP (was %.1f LUFS, %.1f dBTP; gain %+.2f dB)" % (i1, tp1, i0, tp0, gain))
    return notes


# ---------------------------------------------------------------- commands
def newest_mix():
    mixes = sorted(glob.glob(J("audio", "mix_v*.wav")), key=lambda p: int(re.search(r"v(\d+)", os.path.basename(p)).group(1)))
    if not mixes:
        sys.exit("no film mix found")
    return os.path.relpath(mixes[-1], ROOT)


def cmd_new(a):
    load_conform(J("tools", "conform.py"))
    os.makedirs(a.recipe, exist_ok=True)
    if os.path.exists(os.path.join(a.recipe, "clip.json")):
        sys.exit("%s already holds a recipe" % a.recipe)
    ranges = [[int(v) for v in r.split("-")] for r in a.ranges.split(",")]
    for name, src in FROZEN.items():
        if os.path.exists(J(*src)):
            shutil.copyfile(J(*src), os.path.join(a.recipe, name))
    shutil.copyfile(J("tools", "conform.py"), os.path.join(a.recipe, "conform.py"))
    shots = json.load(open(J("shotlist.json")))["shots"]
    mp = J("clips", "manifest.json")
    manifest, notes = overrides(shots, json.load(open(mp)) if os.path.exists(mp) else {}, ranges, C.CLEAN)
    keep = {s["id"] for s in shots if inside(s, ranges)}
    manifest = {k: v for k, v in manifest.items() if k in keep}
    json.dump(manifest, open(os.path.join(a.recipe, "manifest.json"), "w"), indent=1)
    for rel in sorted({v["file"] for v in manifest.values()}):  # the clips themselves: drafts get deleted
        dst = os.path.join(a.recipe, "clips", rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copyfile(J("clips", rel), dst)
    clip = {"about": "A clip of the cut for a social post. Everything it needs from the cut is frozen in this folder.",
            "ranges": ranges, "hold": a.hold, "card": a.card, "credit": CREDIT, "credit_scale": 1.15,
            "size": "1920x1080", "mix": newest_mix(), "production": []}
    json.dump(clip, open(os.path.join(a.recipe, "clip.json"), "w"), indent=1)
    print("recipe written to %s" % a.recipe)
    for n in notes:
        print("changed for the clip: " + n)


def cmd_render(a):
    global SOURCES
    R = lambda name: os.path.join(a.recipe, name)  # noqa: E731
    SOURCES = R("clips")
    clip = json.load(open(R("clip.json")))
    load_conform(R("conform.py") if os.path.exists(R("conform.py")) else J("tools", "conform.py"))
    C.W, C.H = [int(v) for v in clip.get("size", "1920x1080").split("x")]
    C.K = C.H / 720.0
    W, H = C.W, C.H
    ranges = [tuple(r) for r in clip["ranges"]]
    sl = json.load(open(R("shotlist.json")))
    shots, total = sl["shots"], sl["frames"]
    by_id = {s["id"]: s for s in shots}
    lines = json.load(open(R("lines.json")))
    events = json.load(open(R("type.json")))["events"]
    durs = json.load(open(R("scratch_durations.json"))) if os.path.exists(R("scratch_durations.json")) else {}
    heard = json.load(open(R("words.json"))) if os.path.exists(R("words.json")) else {}
    manifest = json.load(open(R("manifest.json")))
    starts = {l["id"]: l["start"] for l in lines["lines"]}
    for p in clip.get("production", []):  # the captions follow the words as they are spoken in the shot
        shot, entry = by_id[p["shot"]], manifest[p["shot"]]
        heard[p["line"]] = [[w, round(frame_of(t, shot, entry) - starts[p["line"]], 2)] for w, t in p["words"]]
        durs[p["line"]] = round(frame_of(p["end"], shot, entry) - starts[p["line"]], 2)
    caps = C.build_caps(lines, durs, heard)
    card = a.card or clip.get("card", "credit")
    holds = ranges[-1][1] >= total
    hold = clip.get("hold", 18) if holds else 0
    events = type_events(events, ranges, clip, card if holds else "film", hold, total)
    silent = set()
    for e in events:
        if e["style"] in ("caption", "docked"):
            silent.update(range(e["in"], e["out"]))

    out = a.out or os.path.join(os.path.dirname(os.path.abspath(a.recipe)), re.sub(r"_src$", "", os.path.basename(os.path.normpath(a.recipe))) + ".mp4")
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    notes = []
    if not os.path.exists(R("audio.wav")):
        notes = build_audio(clip, shots, manifest, ranges, hold, R("audio.wav"))
    cmd = ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "%dx%d" % (W, H), "-r", str(FPS),
           "-i", "-", "-i", R("audio.wav"),
           "-vf", "scale=out_color_matrix=bt709:out_range=tv,format=yuv420p",
           "-c:v", "libx264", "-preset", "slow", "-crf", a.crf, "-profile:v", "high", "-r", str(FPS),
           "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709", "-color_range", "tv",
           "-c:a", "aac", "-b:a", "256k", "-ar", str(SR), "-movflags", "+faststart", "-shortest", out]
    enc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    anchors, written, used = {}, 0, []
    for ra, rb in ranges:
        for s in shots:
            last = s is shots[-1]
            dur = s["dur"] + (hold if last else 0)
            lo, hi = max(ra, s["start"]), min(rb + (hold if last else 0), s["start"] + dur)
            if lo >= hi:
                continue
            path, t_in, zoom = clip_for(s["id"], manifest)
            if path:
                frames, bg = load(path, s["dur"], t_in, zoom), (20, 20, 20)
                used.append("%s %s@%.2f" % (s["id"], os.path.basename(path), t_in))
            elif s["id"] in C.CLEAN:
                base, bg = C.card(s)
                frames = None
            else:
                enc.stdin.close()
                enc.kill()
                sys.exit("%s has no picture yet: it cannot go in a public clip" % s["id"])
            for f in range(lo, hi):
                img = (frames[min(f - s["start"], s["dur"] - 1)] if frames else base).copy()
                d = ImageDraw.Draw(img, "RGBA")
                C.draw_events(img, d, events, f, bg, anchors)
                for c in caps:
                    if f in silent:
                        break
                    if c.show_from <= f < c.until:
                        C.draw_cap_line(img, d, C.cap_segments(c, f), c.style, bg, cursor=f <= c.end + 2,
                                        prefix="THE FUTURE IS" if c.style == "docked" else None, reserve=C.cap_reserve(c))
                        break
                enc.stdin.write(img.tobytes())
                written += 1
    enc.stdin.close()
    if enc.wait() != 0:
        sys.exit("ffmpeg failed")
    print("wrote %s: %d frames, %.2f seconds, end card: %s" % (out, written, written / FPS, card))
    for n in notes:
        print(n)
    print("picture: " + ", ".join(used))


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    n = sub.add_parser("new")
    n.add_argument("recipe")
    n.add_argument("--ranges", default="0-120,1255-1440", help="stretches of the cut, in frames")
    n.add_argument("--hold", type=int, default=18, help="extra frames on the last card")
    n.add_argument("--card", default="credit", choices=["credit", "film"])
    r = sub.add_parser("render")
    r.add_argument("recipe")
    r.add_argument("--card", default="", choices=["", "credit", "film"])
    r.add_argument("--out", default="")
    r.add_argument("--crf", default="16")
    a = ap.parse_args()
    (cmd_new if a.cmd == "new" else cmd_render)(a)


if __name__ == "__main__":
    main()
