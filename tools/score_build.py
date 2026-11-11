#!/usr/bin/env python3
"""FIRST WORD: the score, cut to the picture from one theme.

    python3 tools/score_build.py                 timing/score.json -> audio/music/score_cut2.wav (the film's 60 seconds)
    python3 tools/score_build.py --map FILE      a bar-by-bar map of any piece of music, to find its bars and its drop

Until the eighth pass the film played one composed track, filtered by passage. Measured bar by bar, that track was
33 seconds of sub bass with nearly nothing above 4 kHz before its drop: on a laptop it was a throb. The score is now
cut from one theme, composed to be bright (timing/sfx.json, "cues": "theme"): eight bars of arpeggio, hi-hats and
choir with no kick drum, then sixteen bars of the full drop. The film uses it the way the theme itself is built:

    frames  120 to  240   the hall of wind       bars 1 to 3 of the theme's opening (no kick: the kick is kept for the key)
    frames  240 to  320   1903                    bars 4 and 5, through a small television's speaker
    frames  320 to  640   the talk                the opening again, turned down and softened, under the voices
    frames  624 to  750   Casey Harrell           a held pad, composed on its own ("still")
    frames  880 to  960   the kitchen             bars 7 and 8, the theme's own two bars before its drop, opening up from far away
    frames  960 to 1260   the flood               the drop: bars 9 to 16 and a half. It stops dead for the whale.
    frames 1260 to 1436   the whale, the end      the two pad takes made for the whale (tools/sound.py pad), and the drop's ring

Where a bar starts in the theme is measured, not assumed: the file opens with 26 ms of nothing, it runs at 144.016
beats a minute, and its drop lands 13.358 s in (timing/score.json records these; --map shows how to find them for
another file, such as one made with Google's Lyria from audio/music/LYRIA_PROMPT.md). Nothing here was judged by ear.
"""
import argparse
import json
import os
import subprocess
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import voices as V  # noqa: E402

SR, FPS = V.SR, 24
TOTAL = 1440
SPEC = V.J("timing", "score.json")
OUT = V.J("audio", "music", "score_cut2.wav")


def stereo(path):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-ac", "2", "-ar", str(SR), "-f", "s16le", "-"], capture_output=True).stdout
    return np.frombuffer(raw, dtype=np.int16).astype(np.float64).reshape(-1, 2) / 32768


def fr(f):
    return int(round(f * SR / FPS))


def rms_db(x):
    return 20 * np.log10(np.sqrt((x ** 2).mean()) + 1e-9)


def shape(x, curve):
    """Zero-phase equaliser: curve(f) gives a gain in dB for each frequency."""
    n = len(x)
    f = np.fft.rfftfreq(n, 1 / SR)
    g = 10 ** (curve(f) / 20)
    return np.stack([np.fft.irfft(np.fft.rfft(x[:, c]) * g, n) for c in range(x.shape[1])], axis=1)


def shelf(f, f0, gain_db, up=True):
    """A gentle shelf: gain_db above f0 (up) or below it."""
    r = (f / f0) ** 2
    w = r / (1 + r) if up else 1 / (1 + r)
    return gain_db * w


def band(x, lo=None, hi=None):
    def curve(f):
        g = np.zeros(len(f))
        if lo:
            g += 20 * np.log10(1 / (1 + (lo / np.maximum(f, 1e-6)) ** 4))
        if hi:
            g += 20 * np.log10(1 / (1 + (f / hi) ** 4))
        return g
    return shape(x, curve)


def sweep(x, f_from, f_to, power=2.0):
    """A low-pass filter that opens over the length of x: the sound comes nearer."""
    n_fft, hop = 2048, 512
    win = np.sqrt(np.hanning(n_fft + 1)[:-1])
    pad = np.concatenate([np.zeros((n_fft, 2)), x, np.zeros((n_fft, 2))])
    out = np.zeros_like(pad)
    f = np.fft.rfftfreq(n_fft, 1 / SR)
    steps = (len(pad) - n_fft) // hop
    for i in range(steps + 1):
        a = i * hop
        t = min(1.0, max(0.0, (a - n_fft / 2) / float(len(x))))
        fc = f_from * (f_to / f_from) ** (t ** power)
        g = 1 / (1 + (f / fc) ** 4)
        for c in range(2):
            out[a:a + n_fft, c] += np.fft.irfft(np.fft.rfft(pad[a:a + n_fft, c] * win) * g, n_fft) * win
    return out[n_fft:n_fft + len(x)] / 1.5          # sqrt-Hann at a quarter hop sums to 1.5


def ring(tail, seconds, lo=200, hi=6000, seed=7):
    """What a hall does with the last thing it heard: tail convolved with a decaying burst of noise."""
    n = int(seconds * SR)
    rng = np.random.default_rng(seed)
    ir = rng.standard_normal((n, 2)) * np.exp(-np.arange(n) / (seconds * SR / 6.9))[:, None]
    ir[: int(0.012 * SR)] = 0
    ir = band(ir, lo, hi)
    ir /= np.sqrt((ir ** 2).sum(axis=0)).mean()
    m = 1 << (len(tail) + n - 2).bit_length()
    return np.stack([np.fft.irfft(np.fft.rfft(tail[:, c], m) * np.fft.rfft(ir[:, c], m), m)[: len(tail) + n - 1] for c in range(2)], axis=1)


def ease(x, over_db):
    """Hits that stand more than over_db above the passage's own level are eased down to that height, five milliseconds
    early and let back up quickly (a look-ahead limiter). The theme's opening has a tick on every beat that measures
    20 dB over the rest of it: left alone, it would be the loudest thing in the hall of wind."""
    from scipy.ndimage import minimum_filter1d, uniform_filter1d
    ceiling = 10 ** ((rms_db(x) + over_db) / 20)
    pk = np.abs(x).max(axis=1)
    need = np.minimum(1.0, ceiling / np.maximum(pk, 1e-9))
    w = int(0.004 * SR)
    need = minimum_filter1d(need, size=2 * w + 1, mode="nearest")
    g = need.copy()
    a = np.exp(-1.0 / (0.04 * SR))
    cur = 1.0
    for i in range(len(g)):
        cur = min(need[i], a * cur + (1 - a))
        g[i] = cur
    g = uniform_filter1d(minimum_filter1d(g, size=w + 1, mode="nearest"), size=w + 1, mode="nearest")
    return x * g[:, None]


def to_level(x, db, of=None):
    return x * 10 ** ((db - rms_db(x if of is None else of)) / 20)


def bar_map(path):
    x = stereo(path).mean(axis=1)
    bar = 240.0 / 144.0
    hop = SR // 1000
    e = np.sqrt((x[:len(x) // hop * hop].reshape(-1, hop) ** 2).mean(axis=1))
    print("%s: %.2f s. First sound %d ms in." % (os.path.basename(path), len(x) / SR, int(np.argmax(e > 0.02 * e.max()))))
    print("bar   from    below 100 Hz   100-400   400-4k   above 4k   (dB; bars counted from zero at 144 BPM)")
    for b in range(int(len(x) / SR / bar)):
        seg = x[int(b * bar * SR): int((b + 1) * bar * SR)]
        S = np.abs(np.fft.rfft(seg)) ** 2
        f = np.fft.rfftfreq(len(seg), 1 / SR)
        lv = [10 * np.log10(S[(f >= a) & (f < c)].sum() / len(seg) ** 2 * 2 + 1e-12) for a, c in ((20, 100), (100, 400), (400, 4000), (4000, 20000))]
        print("%3d  %6.2f     %7.1f     %7.1f  %7.1f   %7.1f" % (b + 1, b * bar, lv[0], lv[1], lv[2], lv[3]))
    d = np.maximum(0, np.diff(np.convolve(e, np.ones(3) / 3, "same")))
    lowe = np.sqrt((band(np.stack([x, x], axis=1), None, 110)[:, 0][:len(x) // hop * hop].reshape(-1, hop) ** 2).mean(axis=1))
    k = int(np.argmax(np.convolve(lowe, np.ones(200) / 200, "same") > 0.5 * np.convolve(lowe, np.ones(200) / 200, "same").max()))
    w = d[max(0, k - 300): k + 300]
    print("The bass arrives near %.2f s; the sharpest hit round there is at %.3f s. Put that in timing/score.json as the drop." % (k / 1000.0, (max(0, k - 300) + int(np.argmax(w)) + 1) / 1000.0))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--map", default="")
    a = ap.parse_args()
    if a.map:
        return bar_map(a.map)
    sp = json.load(open(SPEC))
    th = stereo(V.J(sp["theme"]["file"]))
    beat = 60.0 / sp["theme"]["bpm"]
    drop = sp["theme"]["drop_s"]
    intro_bars = sp["theme"]["intro_bars"]
    bar = 4 * beat
    origin = drop - intro_bars * bar                       # where bar 1 starts

    def bars(a_, b_, lead=0.0):
        """Bars a_ up to b_ of the theme (bar 1 is its first; halves allowed), as samples."""
        t0, t1 = origin + (a_ - 1) * bar - lead, origin + (b_ - 1) * bar
        return th[max(0, int(round(t0 * SR))): int(round(t1 * SR))].copy()

    # the theme measures 8 dB heavier below 100 Hz than in its middle: on a small speaker that is nothing, on a large
    # one it is all there is. One gentle tilt for everything cut from it.
    tilt = lambda f: shelf(f, 110, sp["tilt"]["low_db"], up=False) + shelf(f, 5000, sp["tilt"]["high_db"], up=True) - 60 * (f < 28)
    out = np.zeros((fr(TOTAL), 2))
    L = sp["levels_db"]

    def lay(frame, x):
        a_ = fr(frame)
        x = x[: len(out) - a_]
        out[a_: a_ + len(x)] += x

    def fade(x, n_in=0, n_out=0):
        if n_in:
            x[:n_in] *= np.linspace(0, 1, n_in)[:, None]
        if n_out:
            x[-n_out:] *= np.linspace(1, 0, n_out)[:, None]
        return x

    ms = lambda v: int(v * SR / 1000)

    # ---- the hall of wind (frames 120 to 240) and 1903 (240 to 320): the opening, bars 1 to 5
    open5 = ease(shape(bars(1, 6), tilt), sp["ease_db"])
    n3 = fr(240) - fr(120)
    hall = to_level(open5[:n3].copy(), L["hall"])
    g = 10 ** ((L["hall"] - rms_db(open5[:n3])) / 20)
    lay(120, fade(hall, n_out=ms(4)))
    tv = open5[n3: n3 + fr(320) - fr(240)].copy() * g
    tv = band(tv, 380, 2600)
    tv = np.repeat(tv.mean(axis=1, keepdims=True), 2, axis=1)                 # one small speaker
    tv = np.tanh(tv * 6) / 6 * 10 ** ((L["tv"] - L["hall"]) / 20) * 10 ** (sp["tv_makeup_db"] / 20)
    tv = tv[: fr(318) - fr(240)]                                               # the set is switched off two frames before the cut
    lay(240, fade(tv, n_in=ms(4), n_out=ms(40)))

    # ---- the talk (320 to 640): the opening goes round again, softened and turned down
    order = sp["talk_bars"]                                                    # eight bars, by number
    parts = [shape(bars(b, b + 1, lead=0.02), tilt) for b in order]
    xf = ms(20)
    talk = parts[0][xf:]
    for p in parts[1:]:
        talk = np.concatenate([talk[:-xf], talk[-xf:] * np.linspace(1, 0, xf)[:, None] + p[:xf] * np.linspace(0, 1, xf)[:, None], p[xf:]])
    talk = talk[: fr(640) - fr(320)]
    talk = shape(talk, lambda f: shelf(f, 3000, sp["talk_high_db"], up=True) + shelf(f, 90, -3.0, up=False))
    talk = to_level(ease(talk, sp["ease_db"] - 1.0), L["talk"])
    k0, k1 = ms(60), ms(15)
    talk[-k0:-k1] *= (np.linspace(1, 0, k0 - k1) ** 2)[:, None]
    talk[-k1:] = 0
    lay(320, fade(talk, n_in=ms(6)))
    tail = ring(talk[-ms(420):], 2.2) * 10 ** (-9 / 20)                        # it stops on the click at 640 and the hall keeps it a moment
    lay(640 - 420 * FPS / 1000.0, tail)

    # ---- Casey Harrell (624 to 750): the held pad
    st = stereo(V.J(sp["still"]["file"]))
    st = st[int(sp["still"]["from_s"] * SR):][: fr(750) - fr(624)]
    env = np.interp(np.arange(len(st)) / SR * FPS + 624, [624, 660, 700, 724, 742, 750], [0.0, 0.7, 0.8, 1.0, 0.8, 0.0])
    st = to_level(st, L["still"]) * env[:, None]
    lay(624, st)

    # ---- the kitchen (880 to 960): the two bars before the drop, coming nearer; a frame and a half of nothing; the key
    pre = shape(bars(intro_bars - 1, intro_bars + 1), tilt)[: fr(960) - fr(880)]
    pre = sweep(pre, 260.0, 15000.0, power=1.6)
    t = np.arange(len(pre)) / SR * FPS + 880
    env = 10 ** (np.interp(t, [880, 904, 925, 948, 958.3, 958.5, 960], [-120, -34, -20, -9, -2, -120, -120]) / 20)
    pre = pre * 10 ** ((L["flood"] - rms_db(shape(bars(intro_bars + 1, intro_bars + 5), tilt))) / 20) * env[:, None]
    lay(880, pre)

    # ---- the flood (960 to 1260): the drop, seven and a half bars, and it stops dead
    dr = shape(bars(intro_bars + 1, intro_bars + 9), tilt)
    dr = dr[: fr(1260) - fr(960)]
    dr = to_level(dr, L["flood"])
    k0, k1 = ms(60), ms(15)
    stopped = dr.copy()
    stopped[-k0:-k1] *= (np.linspace(1, 0, k0 - k1) ** 2)[:, None]
    stopped[-k1:] = 0
    lay(960, stopped)
    lay(1260 - 400 * FPS / 1000.0, ring(dr[-ms(400):], 3.6, lo=250, hi=5000, seed=11) * 10 ** (sp["ring_db"] / 20))

    # ---- the whale and the end card: the two pad takes, held under the last words and gone before the film loops
    for item in sp["pads"]:
        p = stereo(V.J(item["file"]))
        half = SR // 2
        loud = max(rms_db(p[i:i + half]) for i in range(0, len(p) - half, half // 2))
        p *= 10 ** ((L["pad_peak"] - loud) / 20)
        lay(1260 + item["after_s"] * FPS, p)
    t = np.arange(len(out)) / SR * FPS
    out *= np.interp(t, [0, sp["end_fade"][0], sp["end_fade"][1], TOTAL], [1, 1, 0, 0])[:, None]

    out *= 10 ** (sp["headroom_db"] / 20)                 # written down, so that no peak is clipped; the mix brings it back
    pcm = (np.clip(out, -1, 1) * 32767).astype(np.int16)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "s16le", "-ar", str(SR), "-ac", "2", "-i", "-", OUT], input=pcm.tobytes(), check=True)
    print("wrote %s, %.2f s, peak %.2f" % (os.path.relpath(OUT, V.ROOT), len(out) / SR, np.abs(out).max()))
    m = out.mean(axis=1)

    def bands(seg):
        S = np.abs(np.fft.rfft(seg)) ** 2
        f = np.fft.rfftfreq(len(seg), 1 / SR)
        return [10 * np.log10(S[(f >= lo) & (f < hi)].sum() / len(seg) ** 2 * 2 + 1e-12) for lo, hi in ((20, 100), (100, 400), (400, 4000), (4000, 20000))]

    print("passage                 frames         level    below 100   100-400   400-4k   above 4k")
    for name, f0, f1 in (("the hall of wind", 120, 240), ("1903, on a television", 240, 318), ("the talk", 320, 640), ("Casey Harrell", 660, 740), ("the kitchen", 920, 958),
                         ("the flood", 960, 1260), ("the whale", 1262, 1380), ("the end card", 1380, 1436)):
        seg = m[fr(f0):fr(f1)]
        b = bands(seg)
        print("%-22s %5d to %4d  %6.1f dB    %6.1f    %6.1f   %6.1f   %6.1f    peaks %4.1f dB over its level" % (name, f0, f1, rms_db(seg), b[0], b[1], b[2], b[3], 20 * np.log10(np.abs(out[fr(f0):fr(f1)]).max() + 1e-9) - rms_db(seg)))
    hop = SR // 1000
    e = np.sqrt((m[:len(m) // hop * hop].reshape(-1, hop) ** 2).mean(axis=1))
    d = np.maximum(0, np.diff(np.convolve(e, np.ones(3) / 3, "same")))
    for name, f0 in (("the music's first hit", 120), ("the drop", 960)):
        a0 = int(f0 / FPS * 1000)
        i = a0 - 60 + int(np.argmax(d[a0 - 60:a0 + 120]))
        print("%s is %+.0f ms from frame %d" % (name, i + 1 - a0, f0))
    print("the two frames before the drop (958.5 to 960): %.1f dB; the first second after the drums stop: %.1f dB" % (rms_db(m[fr(958.6):fr(960)]), rms_db(m[fr(1260):fr(1284)])))


if __name__ == "__main__":
    main()
