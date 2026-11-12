#!/usr/bin/env python3
"""FIRST WORD: the data and the web copies of the media for the project page (docs/index.html).

    python3 tools/site.py            write docs/site/data.json from the repository's own data
    python3 tools/site.py --media    also encode the web copies in docs/media/ from film/, clips/ and audio/

The page draws everything it shows from data.json: the 98 shots (shotlist.json), the passages, where each picture
comes from, the persona's dials (persona/persona-prompt.md), one character's fixed description
(timing/characters.json), the archive index (archive/manifest.json), the spending by model (ledger.csv) and the
level of each stem over the minute (audio/stems/). Nothing on the page is typed in twice.

docs/media/versions.mp4 (four of the fifteen versions side by side) is not made here: the earlier versions of the
film are not kept in the repository.
"""
import argparse
import csv
import json
import os
import re
import subprocess
import wave

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
J = lambda *p: os.path.join(ROOT, *p)                                   # noqa: E731

KINDS = [("gen", "Generated video", "#2a78d6"), ("macro", "Generated close-up", "#eb6834"), ("archive", "Public-domain archive", "#1baf7a"),
         ("code", "Drawn in code", "#eda100"), ("ink", "Ink over picture", "#e87ba4")]


def kind(src):
    if "ARCHIVE" in src:
        return "archive"
    if src.startswith("MACRO"):
        return "macro"
    if src.startswith("INK"):
        return "ink"
    if src.startswith("CODE") and "GEN" not in src:
        return "code"
    return "gen"


def frames(clock):
    m, s = clock.split(":")
    return int(round((int(m) * 60 + float(s)) * 24))


def envelope(path, n=600):
    """The level of a stem in n steps across the minute, 0 (silence, -60 dB or less) to 1 (full scale)."""
    w = wave.open(path)
    raw = w.readframes(w.getnframes())
    if w.getsampwidth() == 3:
        a = np.frombuffer(raw, np.uint8).reshape(-1, 3)
        x = (a[:, 0].astype(np.int32) | (a[:, 1].astype(np.int32) << 8) | (a[:, 2].astype(np.int8).astype(np.int32) << 16)) / 8388608.0
    else:
        x = np.frombuffer(raw, np.int16) / 32768.0
    x = x.reshape(-1, w.getnchannels()).mean(axis=1)
    step = len(x) // n
    rms = np.sqrt((x[: step * n].reshape(n, step) ** 2).mean(axis=1))
    return [round(float(v), 3) for v in np.clip((20 * np.log10(rms + 1e-9) + 60) / 60, 0, 1)]


def data():
    sl = json.load(open(J("shotlist.json")))
    shots = [dict(id=s["id"], p=s["passage"], start=s["start"], dur=s["dur"], src=s["source"], kind=kind(s["source"]),
                  picture=s["picture"], line=s["line"], sound=s["sound"], cut=s["transition"]) for s in sl["shots"]]
    kinds = []
    for k, name, colour in KINDS:
        mine = [s for s in shots if s["kind"] == k]
        kinds.append(dict(key=k, name=name, colour=colour, shots=len(mine), frames=sum(s["dur"] for s in mine)))
    passages = [dict(key=p["key"], name=p["name"], start=frames(p["start"]), end=frames(p["end"]), shots=p["shots"]) for p in sl["passages"]]
    prompt = open(J("persona", "persona-prompt.md")).read()
    dials = [[c.strip() for c in ln.strip("|").split("|")] for ln in prompt.split("\n") if re.match(r"\| [A-Z][a-z ]+ \| \d+ \|", ln)]
    people = json.load(open(J("timing", "characters.json")))["people"]
    archive = []
    real = set(x["id"] for x in shots if x["kind"] == "archive")
    for it in json.load(open(J("archive", "manifest.json")))["items"]:
        used = [x for x in it.get("shots") or [] if x in real or "(sound)" in x]      # only what is in the cut: sources that were replaced or kept as alternates are in the manifest, not here
        if not used or it.get("status") != "ok":
            continue
        archive.append(dict(shots=used, title=it["title"], date=it.get("event_date", ""), holder=re.split(r" \(", it["holder"])[0],
                            url=it.get("page_url", ""), rights=it.get("rights", ""), credit=it.get("credit_line", "")))
    cost = {}
    for r in csv.DictReader(open(J("ledger.csv"), newline="")):
        if r["service"] != "runway":
            continue
        what = "Reference stills (Seedream 5 Pro)" if r["model"].startswith("seedream") else ("1080p finishes (Seedance 2.5)" if "enhanced to 1080p" in r["what"] else "480p drafts (Seedance 2.5)")
        c = cost.setdefault(what, dict(what=what, calls=0, usd=0.0))
        c["calls"] += 1
        c["usd"] = round(c["usd"] + float(r["cost_usd"] or 0), 2)
    stems = {}
    for k in ("dialogue", "effects", "score", "whale"):
        p = J("audio", "stems", k + ".wav")
        if os.path.exists(p):
            stems[k] = envelope(p)
    return dict(fps=sl["fps"], bpm=sl["bpm"], frames=sl["frames"], shots=shots, kinds=kinds, passages=passages,
                dials=[dict(name=d[0], value=int(d[1]), low=d[2], high=d[3]) for d in dials], mara=people["mara"].replace("{jacket}", "the reference still"),
                archive=archive, cost=sorted(cost.values(), key=lambda c: -c["usd"]), stems=stems)


def media():
    out = J("docs", "media")
    os.makedirs(os.path.join(out, "stems"), exist_ok=True)
    tags = ["-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709", "-pix_fmt", "yuv420p", "-movflags", "+faststart"]
    x264 = ["-c:v", "libx264", "-preset", "slow"]
    film = J("film", "first_word_1080.mp4")
    jobs = [
        ["-i", film] + x264 + ["-crf", "21", "-maxrate", "6M", "-bufsize", "12M", "-profile:v", "high"] + tags + ["-c:a", "aac", "-b:a", "192k", os.path.join(out, "film.mp4")],
        # the shot explorer loops a few frames at a time, so this copy has a key frame every six
        ["-i", film, "-an", "-vf", "scale=640:360:flags=lanczos"] + x264 + ["-crf", "24", "-g", "6", "-keyint_min", "6", "-sc_threshold", "0"] + tags + [os.path.join(out, "explorer.mp4")],
        ["-i", J("film", "first_word_vertical.mp4"), "-vf", "scale=720:1280:flags=lanczos"] + x264 + ["-crf", "22", "-maxrate", "4M", "-bufsize", "8M"] + tags + ["-c:a", "aac", "-b:a", "160k", os.path.join(out, "vertical.mp4")],
        ["-i", J("clips", "final", "mara_reel.mp4"), "-an", "-vf", "scale=960:540:flags=lanczos"] + x264 + ["-crf", "24"] + tags + [os.path.join(out, "reel_mara.mp4")],
        ["-ss", "6.7", "-i", film, "-frames:v", "1", "-q:v", "3", os.path.join(out, "poster.jpg")],
        ["-ss", "55.9", "-i", film, "-frames:v", "1", "-vf", "scale=1200:675,crop=1200:630", "-q:v", "3", os.path.join(out, "og.jpg")],
        ["-ss", "5.9", "-i", J("film", "first_word_vertical.mp4"), "-frames:v", "1", "-vf", "scale=720:1280", "-q:v", "4", os.path.join(out, "vertical_poster.jpg")],
        ["-ss", "12.5", "-i", J("clips", "final", "mara_reel.mp4"), "-frames:v", "1", "-vf", "scale=960:540", "-q:v", "4", os.path.join(out, "reel_mara_poster.jpg")],
    ]
    for k in ("dialogue", "effects", "score", "whale"):
        jobs.append(["-i", J("audio", "stems", k + ".wav"), "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", os.path.join(out, "stems", k + ".m4a")])
    for j in jobs:
        subprocess.run(["ffmpeg", "-v", "error", "-y"] + j, check=True)
        print("wrote", os.path.relpath(j[-1], ROOT), "%.1f MB" % (os.path.getsize(j[-1]) / 1e6))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--media", action="store_true", help="also encode the web copies of the media")
    a = ap.parse_args()
    if a.media:
        media()
    os.makedirs(J("docs", "site"), exist_ok=True)
    d = data()
    json.dump(d, open(J("docs", "site", "data.json"), "w"), separators=(",", ":"), ensure_ascii=False)
    print("wrote docs/site/data.json: %d shots, %d passages, %d archive items, %d stems, %.0f KB" %
          (len(d["shots"]), len(d["passages"]), len(d["archive"]), len(d["stems"]), os.path.getsize(J("docs", "site", "data.json")) / 1024.0))


if __name__ == "__main__":
    main()
