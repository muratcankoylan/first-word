#!/usr/bin/env python3
"""FIRST WORD: sound effects and the score, generated with ElevenLabs from timing/sfx.json.

    python3 tools/sound.py sfx      every effect, with its variants, into audio/sfx/
    python3 tools/sound.py score    two takes of the score into audio/music/, with a measurement of each
    python3 tools/sound.py pad      the pad under the whale, generated on its own (timing/sfx.json, "pad")
    python3 tools/sound.py score2   the score recomposed on the eighth pass: three takes, measured section by section
    python3 tools/sound.py cue      the engine and the drop composed on their own, as alternates
    python3 tools/sound.py sfx2     the effects made again with the newer effects model, into audio/sfx2/, each measured
"""
import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import voices as V  # noqa: E402

SR = V.SR


def sfx():
    spec = json.load(open(V.J("timing", "sfx.json")))["sfx"]
    os.makedirs(V.J("audio", "sfx"), exist_ok=True)
    jobs = [(name, k, s) for name, s in spec.items() for k in range(s.get("n", 1))]

    def one(job):
        name, k, s = job
        path = V.J("audio", "sfx", "%s_%d.mp3" % (name, k + 1))
        if os.path.exists(path):
            return name, k, "kept"
        body = dict(text=s["text"], duration_seconds=s["seconds"], prompt_influence=0.5)
        if s.get("loop"):
            body["loop"] = True
        try:
            open(path, "wb").write(V.call("POST", "/v1/sound-generation", body=body, raw=True, query="output_format=mp3_44100_192"))
        except RuntimeError as ex:
            return name, k, "FAILED " + str(ex)[:200]
        x = V.decode(path)
        return name, k, "%.2f s, peak %.2f" % (len(x) / SR, np.abs(x).max() if len(x) else 0)

    with ThreadPoolExecutor(4) as ex:
        for name, k, res in ex.map(one, jobs):
            print("%-14s %d  %s" % (name, k + 1, res))


def measure(x):
    """What can be said of a sound without hearing it: how long the sound itself lasts, where its loudest moment is,
    where its energy sits, and how much of it is below 150 Hz (a sound that is nearly all there is a rumble: a phone
    or a laptop will not play it at all)."""
    if not len(x) or np.abs(x).max() < 1e-4:
        return dict(silent=True)
    e = envelope(x, SR // 200)
    on = np.where(e > 0.1 * e.max())[0]
    S = np.abs(np.fft.rfft(x * np.hanning(len(x)))) ** 2
    f = np.fft.rfftfreq(len(x), 1 / SR)
    tot = S.sum() + 1e-12
    return dict(silent=False, seconds=round(len(x) / SR, 2), sound=round((on[-1] - on[0] + 1) / 200.0, 2), loudest_at=round(float(np.argmax(e)) / 200.0, 2),
                low=round(float(S[f < 150].sum() / tot), 2), mid=round(float(S[(f >= 150) & (f < 2000)].sum() / tot), 2), high=round(float(S[f >= 2000].sum() / tot), 2),
                centre=int((S * f).sum() / tot), peak=round(float(np.abs(x).max()), 2))


def sfx2():
    spec = json.load(open(V.J("timing", "sfx.json")))["sfx2"]
    os.makedirs(V.J("audio", "sfx2"), exist_ok=True)
    only = sys.argv[2:]
    jobs = [(name, k, s) for name, s in spec["items"].items() for k in range(s.get("n", 1)) if not only or name in only]

    def one(job):
        name, k, s = job
        path = V.J("audio", "sfx2", "%s_%d.mp3" % (name, k + 1))
        made = "kept"
        if not os.path.exists(path):
            body = dict(text=s["text"], duration_seconds=s["seconds"], prompt_influence=0.5, model_id=spec["model"])
            if s.get("loop"):
                body["loop"] = True
            try:
                open(path, "wb").write(V.call("POST", "/v1/sound-generation", body=body, raw=True, query="output_format=mp3_44100_192"))
            except RuntimeError as ex:
                return name, k, "FAILED " + str(ex)[:300], None
            made = "made"
        return name, k, made, measure(V.decode(path))

    report = {}
    with ThreadPoolExecutor(4) as ex:
        for name, k, res, m in ex.map(one, jobs):
            if m is None:
                print("%-14s %d  %s" % (name, k + 1, res))
                continue
            report["%s_%d" % (name, k + 1)] = m
            if m.get("silent"):
                print("%-14s %d  %s  SILENT" % (name, k + 1, res))
                continue
            print("%-14s %d  %s  sound %.2f of %.2f s, loudest at %.2f s   low %2d%% mid %2d%% high %2d%%   centre %5d Hz%s" % (
                name, k + 1, res, m["sound"], m["seconds"], m["loudest_at"], round(100 * m["low"]), round(100 * m["mid"]), round(100 * m["high"]), m["centre"],
                "   <-- RUMBLE ONLY" if m["low"] > 0.8 else ""))
    rp = V.J("audio", "sfx2", "measured.json")
    old = json.load(open(rp)) if os.path.exists(rp) else {}
    old.update(report)
    json.dump(old, open(rp, "w"), indent=1)


def envelope(x, hop):
    n = len(x) // hop
    return np.sqrt((x[:n * hop].reshape(n, hop) ** 2).mean(axis=1))


def tempo(x):
    """Tempo of a stretch of music from the autocorrelation of its onset strength."""
    hop = SR // 200
    e = envelope(x, hop)
    o = np.maximum(0, np.diff(e))
    o = o - o.mean()
    ac = np.correlate(o, o, "full")[len(o) - 1:]
    lo, hi = int(200 * 60 / 200), int(200 * 60 / 60)      # 200 to 60 beats a minute
    k = lo + int(np.argmax(ac[lo:hi]))
    return 60.0 * 200 / k


def score():
    spec = json.load(open(V.J("timing", "sfx.json")))["score"]
    os.makedirs(V.J("audio", "music"), exist_ok=True)
    bounds = np.cumsum([0] + [c["duration_ms"] for c in spec["chunks"]]) / 1000.0
    for seed in (1, 2):
        path = V.J("audio", "music", "score_take%d.mp3" % seed)
        if not os.path.exists(path):
            try:
                blob = V.call("POST", "/v1/music", raw=True, query="output_format=mp3_44100_192",
                              body=dict(composition_plan=dict(chunks=spec["chunks"]), model_id=spec["model"], seed=seed))
            except RuntimeError as ex:
                print("take %d FAILED %s" % (seed, str(ex)[:400]))
                continue
            open(path, "wb").write(blob)
        x = V.decode(path)
        print("take %d: %.2f s (plan %.2f s)" % (seed, len(x) / SR, bounds[-1]))
        for i, c in enumerate(spec["chunks"]):
            seg = x[int(bounds[i] * SR): int(bounds[i + 1] * SR)]
            if not len(seg):
                continue
            rms = 20 * np.log10(np.sqrt((seg ** 2).mean()) + 1e-9)
            bpm = tempo(seg) if len(seg) > 3 * SR else 0
            print("   %-16s %5.1f to %5.1f s   level %6.1f dB   tempo about %5.1f" % (c["text"].split("\n")[0], bounds[i], bounds[i + 1], rms, bpm))


def pad():
    """The whale's pad: a few takes of one short piece, with what can be measured of each (no drum hits, which notes)."""
    spec = json.load(open(V.J("timing", "sfx.json")))["pad"]
    names = "C C# D D# E F F# G G# A A# B".split()
    for seed in range(1, spec.get("takes", 2) + 1):
        path = V.J("audio", "music", "whale_pad_take%d.mp3" % seed)
        if not os.path.exists(path):
            try:
                blob = V.call("POST", "/v1/music", raw=True, query="output_format=mp3_44100_192",
                              body=dict(composition_plan=dict(chunks=spec["chunks"]), model_id=spec["model"], seed=seed))
            except RuntimeError as ex:
                print("take %d FAILED %s" % (seed, str(ex)[:400]))
                continue
            open(path, "wb").write(blob)
        x = V.decode(path)
        e = envelope(x, SR // 100)
        jump = 20 * np.log10((e[1:] + 1e-5) / (e[:-1] + 1e-5))            # the largest rise in level from one 10 ms to the next
        S = np.abs(np.fft.rfft(x * np.hanning(len(x)))) ** 2
        f = np.fft.rfftfreq(len(x), 1 / SR)
        keep = (f > 60) & (f < 2000)
        pc = np.zeros(12)
        np.add.at(pc, np.round(12 * np.log2(f[keep] / 440.0) + 9).astype(int) % 12, S[keep])
        order = np.argsort(pc)[::-1]
        print("take %d: %.2f s, level %.1f dB, largest jump in 10 ms %.1f dB, strongest notes %s" % (
            seed, len(x) / SR, 20 * np.log10(np.sqrt((x ** 2).mean()) + 1e-9), jump[20:].max(),
            " ".join("%s %d%%" % (names[i], round(100 * pc[i] / pc.sum())) for i in order[:5])))


def beat_report(x, t0, t1, bpm=144.0):
    """How a stretch keeps time: its tempo, and how far its hits sit from a 144 BPM grid that starts at t0 (in ms)."""
    seg = x[int(t0 * SR): int(t1 * SR)]
    if len(seg) < 2 * SR:
        return 0.0, 0.0
    hop = SR // 1000
    e = envelope(seg, hop)
    o = np.maximum(0, np.diff(np.convolve(e, np.ones(8) / 8, "same")))
    beat = 60000.0 / bpm
    ph = (np.arange(len(o)) % beat) / beat * 2 * np.pi
    z = (o * np.exp(1j * ph)).sum()
    off = (np.angle(z) / (2 * np.pi)) * beat                  # ms after (plus) or before (minus) the grid
    return tempo(seg), off


def score2():
    """The recomposed score: a few takes of one plan, each measured section by section. Nothing is judged by ear."""
    spec = json.load(open(V.J("timing", "sfx.json")))["score2"]
    bounds = np.cumsum([0] + [c["duration_ms"] for c in spec["chunks"]]) / 1000.0

    def one(seed):
        path = V.J("audio", "music", "score2_take%d.mp3" % seed)
        if not os.path.exists(path):
            blob = V.call("POST", "/v1/music", raw=True, query="output_format=mp3_44100_192",
                          body=dict(composition_plan=dict(chunks=spec["chunks"]), model_id=spec["model"], seed=seed))
            open(path, "wb").write(blob)
        return seed, path

    with ThreadPoolExecutor(3) as ex:
        done = []
        for seed in range(1, spec.get("takes", 3) + 1):
            done.append(ex.submit(one, seed))
        for fu in done:
            try:
                seed, path = fu.result()
            except RuntimeError as exn:
                print("a take FAILED %s" % str(exn)[:400])
                continue
            x = V.decode(path)
            print("take %d: %.2f s (plan %.2f s)" % (seed, len(x) / SR, bounds[-1]))
            for i, name in enumerate(spec["sections"]):
                seg = x[int(bounds[i] * SR): int(bounds[i + 1] * SR)]
                if not len(seg):
                    continue
                bpm, off = beat_report(x, bounds[i], bounds[i + 1])
                S = np.abs(np.fft.rfft(seg * np.hanning(len(seg)))) ** 2
                f = np.fft.rfftfreq(len(seg), 1 / SR)
                low = S[f < 150].sum() / S.sum()
                cen = (S * f).sum() / S.sum()
                print("   %-10s %5.2f to %5.2f s   level %6.1f dB   tempo %5.1f   hits %+4.0f ms from the grid   below 150 Hz %2d%%   centre %5d Hz" % (
                    name, bounds[i], bounds[i + 1], 20 * np.log10(np.sqrt((seg ** 2).mean()) + 1e-9), bpm, off, round(100 * low), cen))


def cue():
    """The alternates: the engine and the drop composed on their own from plain prompts."""
    spec = json.load(open(V.J("timing", "sfx.json")))["cues"]
    jobs = [(name, k + 1, it) for name, it in spec["items"].items() for k in range(it.get("takes", 2))]

    def one(job):
        name, seed, it = job
        path = V.J("audio", "music", "cue_%s_take%d.mp3" % (name, seed))
        if not os.path.exists(path):
            body = dict(prompt=it["prompt"], music_length_ms=it["music_length_ms"], model_id=spec["model"], seed=seed, force_instrumental=bool(it.get("instrumental")))
            try:
                blob = V.call("POST", "/v1/music", raw=True, query="output_format=mp3_44100_192", body=body)
            except RuntimeError as exn:
                if "seed" not in str(exn):
                    raise
                body.pop("seed")                                  # a plain prompt may not take a seed
                blob = V.call("POST", "/v1/music", raw=True, query="output_format=mp3_44100_192", body=body)
            open(path, "wb").write(blob)
        return name, seed, path

    with ThreadPoolExecutor(3) as ex:
        for fu in [ex.submit(one, j) for j in jobs]:
            try:
                name, seed, path = fu.result()
            except RuntimeError as exn:
                print("a cue FAILED %s" % str(exn)[:400])
                continue
            x = V.decode(path)
            m = measure(x)
            print("%-10s take %d: %.2f s   level %6.1f dB   tempo %5.1f   low %2d%% mid %2d%% high %2d%%   centre %5d Hz" % (
                name, seed, len(x) / SR, 20 * np.log10(np.sqrt((x ** 2).mean()) + 1e-9), tempo(x), round(100 * m["low"]), round(100 * m["mid"]), round(100 * m["high"]), m["centre"]))


if __name__ == "__main__":
    {"sfx": sfx, "score": score, "pad": pad, "score2": score2, "cue": cue, "sfx2": lambda: sfx2()}[sys.argv[1]]()
