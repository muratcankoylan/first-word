#!/usr/bin/env python3
"""FIRST WORD: the mix.

Four buses at 48 kHz stereo, each also written as a stem: dialogue (the performed lines, with a little room),
effects (generated sound effects placed on the frames in timing/sound.json and in CUES below), score (the
composed track, sculpted by passage and ducked under speech) and the whale (real NOAA sperm whale clicks, cut
to the 1+1+3 rhythm). The sum is mastered to -14 LUFS by one gain over the whole film, under a soft ceiling at -1.6 dBFS.

    python3 tools/mix.py --out audio/mix_v003.wav

Checked by measurement, not by ear: loudness, peaks, speech against bed in each passage, and the silences.
"""
import argparse
import glob
import json
import os
import subprocess
import sys
import wave

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import voices as V  # noqa: E402

SR, FPS = V.SR, V.FPS
N = 60 * SR
RNG = np.random.default_rng(1903)


def fr(f):
    return int(round(f * SR / FPS))


def stereo(path):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-ac", "2", "-ar", str(SR), "-f", "s16le", "-"], capture_output=True).stdout
    return np.frombuffer(raw, dtype=np.int16).astype(np.float64).reshape(-1, 2) / 32768


def band(x, lo=None, hi=None):
    """Zero-phase band limit by FFT: lo and hi in hertz, soft edges."""
    one = x.ndim == 1
    y = x[:, None] if one else x
    n = len(y)
    f = np.fft.rfftfreq(n, 1 / SR)
    mask = np.ones(len(f))
    if lo:
        mask *= 1 / (1 + (lo / np.maximum(f, 1e-6)) ** 4)
    if hi:
        mask *= 1 / (1 + (f / hi) ** 4)
    out = np.stack([np.fft.irfft(np.fft.rfft(y[:, c]) * mask, n) for c in range(y.shape[1])], axis=1)
    return out[:, 0] if one else out


def reverb_ir(seconds, lo=250, hi=5000):
    n = int(seconds * SR)
    ir = RNG.standard_normal((n, 2)) * np.exp(-np.arange(n) / (seconds * SR / 6.9))[:, None]
    ir[: int(0.008 * SR)] = 0
    return band(ir, lo, hi) / np.sqrt((ir ** 2).sum(axis=0)).mean()


def convolve(x, ir):
    n = len(x) + len(ir) - 1
    m = 1 << (n - 1).bit_length()
    out = np.stack([np.fft.irfft(np.fft.rfft(x[:, c], m) * np.fft.rfft(ir[:, c], m), m)[:n] for c in range(2)], axis=1)
    return out[: len(x)]


class Bus:
    def __init__(self):
        self.x = np.zeros((N, 2))

    def add(self, frame, mono, gain=1.0, pan=0.0):
        a = fr(frame)
        if a >= N or not len(mono):
            return
        if a < 0:
            mono, a = mono[-a:], 0
        mono = mono[: N - a]
        th = (pan + 1) * np.pi / 4
        self.x[a:a + len(mono), 0] += mono * gain * np.cos(th) * 1.4142
        self.x[a:a + len(mono), 1] += mono * gain * np.sin(th) * 1.4142

    def add_stereo(self, frame, st, gain=1.0):
        a = fr(frame)
        st = st[: N - a]
        self.x[a:a + len(st)] += st * gain


def one_shot(name, k=None, peak=0.5):
    files = sorted(glob.glob(V.J("audio", "sfx", name + "_*.mp3")))
    path = files[(k if k is not None else int(RNG.integers(0, len(files)))) % len(files)]
    x = V.decode(path)
    a, b = V.speech_span(x)
    x = x[a:b] if b > a else x
    m = np.abs(x).max()
    x = x * (peak / m) if m > 0 else x
    n = min(len(x) // 3, 480)
    if n:
        x[-n:] *= np.linspace(1, 0, n)
    return x


def bed(name, frames, level_db, fade=6):
    """An ambience stretched over a span by looping with crossfades, at a given RMS level."""
    x = V.decode(sorted(glob.glob(V.J("audio", "sfx", name + "_*.mp3")))[0])
    rms = np.sqrt((x ** 2).mean()) + 1e-9
    x = x * (10 ** (level_db / 20) / rms)
    need = fr(frames)
    xf = int(0.25 * SR)
    out = x.copy()
    while len(out) < need:
        tail, head = out[-xf:], x[:xf]
        out = np.concatenate([out[:-xf], tail * np.linspace(1, 0, xf) + head * np.linspace(0, 1, xf), x[xf:]])
    out = out[:need]
    n = fr(fade)
    out[:n] *= np.linspace(0, 1, n)
    out[-n:] *= np.linspace(1, 0, n)
    return out


def automation(points):
    """Gain curve from (frame, dB) points, linear in dB between them."""
    t = np.arange(N) / SR * FPS
    db = np.interp(t, [p[0] for p in points], [p[1] for p in points])
    return 10 ** (db / 20)


def envelope(x, ms=80):
    mono = np.abs(x).mean(axis=1) if x.ndim == 2 else np.abs(x)
    win = int(ms / 1000 * SR)
    cs = np.cumsum(np.concatenate([[0.0], mono]))
    e = (cs[win:] - cs[:-win]) / win
    return np.concatenate([np.full(win // 2, e[0]), e, np.full(len(mono) - len(e) - win // 2, e[-1])])


def key_hit(peak):
    """A hit that carries on any speaker: a sine falling from 150 Hz to 42 in a few hundredths of a second, with a slap of noise on its front."""
    t = np.arange(int(0.9 * SR)) / SR
    f = 42 + 110 * np.exp(-t / 0.035)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.22)
    slap = band(np.random.default_rng(960).standard_normal(len(t)), 180, 5000) * np.exp(-t / 0.028)
    x = body + 0.5 * slap / np.abs(slap).max()
    return x / np.abs(x).max() * peak


def ping(peak):
    """The ring a click sends out, as sound: two high notes of the film's key (D and the A above it) that die away
    in a third of a second. It sits far under the click itself, which stays dry."""
    t = np.arange(int(0.55 * SR)) / SR
    x = (np.sin(2 * np.pi * 1174.66 * t) + 0.6 * np.sin(2 * np.pi * 1760.0 * t) + 0.25 * np.sin(2 * np.pi * 2349.32 * t)) * np.exp(-t / 0.11)
    x[: int(0.004 * SR)] *= np.linspace(0, 1, int(0.004 * SR))
    return x / np.abs(x).max() * peak


def metal_room(frames, level_db):
    """A metal room for the bronze: a handful of high, slightly sour partials that beat slowly, as a plate rings
    when the air moves. Written out as arithmetic because the sound model answers "silent gallery" with silence."""
    n = fr(frames)
    t = np.arange(n) / SR
    rng = np.random.default_rng(113)
    x = np.zeros(n)
    for f0, a in ((412.0, 1.0), (957.0, 0.7), (1483.0, 0.5), (2231.0, 0.32), (3170.0, 0.2), (4411.0, 0.1)):
        for det in (0.0, rng.uniform(0.6, 2.2)):                    # each partial twice, a hertz or two apart: it beats
            x += a * np.sin(2 * np.pi * (f0 + det) * t + rng.uniform(0, 6.28)) * (0.6 + 0.4 * np.sin(2 * np.pi * rng.uniform(0.3, 0.9) * t + rng.uniform(0, 6.28)))
    x += band(rng.standard_normal(n), 300, 5000) * 0.25             # air
    x *= 10 ** (level_db / 20) / (np.sqrt((x ** 2).mean()) + 1e-9)
    k = fr(5)
    x[:k] *= np.linspace(0, 1, k)
    x[-k:] *= np.linspace(1, 0, k)
    return x


# effects that are not in timing/sound.json: frame, sound, variant, peak, pan
CUES = [
    (155, "paper_snap", 0, 0.30, -0.5), (165, "paper_snap", 1, 0.25, 0.6), (185, "paper_snap", 0, 0.30, 0.4), (195, "paper_snap", 1, 0.25, -0.6),     # on the off-beats
    (205, "paper_slap", 0, 0.45, 0.0), (238, "paper_slap", 0, 0.70, 0.0),          # on her cheek as the shot opens; flat on the lens at frame 238
    (243, "pencil_squeak", 0, 0.28, -0.2), (249, "pencil_squeak", 1, 0.26, 0.2), (268, "pencil_squeak", 0, 0.25, 0.0),     # the three strokes under the 1903 line
    (312.0, "telegraph", 0, 0.22, 0.3), (313.7, "telegraph", 0, 0.20, 0.3), (315.4, "telegraph", 0, 0.20, 0.3), (314.5, "pencil_squeak", 1, 0.25, -0.1),
    (427, "cap_pop", 0, 0.40, 0.0), (487, "pencil_squeak", 1, 0.35, 0.0), (500, "paper_rip", 0, 0.50, 0.0), (604, "send_whoosh", 0, 0.30, 0.2),
    (945, "inhale", 0, 0.35, 0.0), (981, "pencil_squeak", 0, 0.16, 0.2), (985, "pencil_squeak", 1, 0.16, 0.3), (1000, "pencil_write", 0, 0.45, 0.0), (1190, "modem", 0, 0.30, 0.0), (1196, "glitch", 0, 0.45, 0.0),
    (1257, "whip", 0, 0.40, 0.0),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=V.J("audio", "mix.wav"))
    ap.add_argument("--score", default=V.J("audio", "music", "score_cut1.wav"))    # take 1 with its drop moved onto the Enter key: tools/score_edit.py
    a = ap.parse_args()
    lines = json.load(open(V.J("timing", "lines.json")))["lines"]
    cues = json.load(open(V.J("timing", "sound.json")))
    score_at = json.load(open(V.J("timing", "sfx.json")))["score"]["starts_at_seconds"] * FPS

    # ---------------- dialogue
    dx, hall_send = Bus(), Bus()
    missing = []
    # sound that belongs to a generated shot (a voice the video model performed): it replaces the line it carries
    pp = V.J("timing", "production_audio.json")
    prod = json.load(open(pp))["cues"] if os.path.exists(pp) else []
    replaced = set(i for c in prod for i in c.get("replaces", []))
    prod_bus = Bus()
    for c in prod:
        raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(c["in"]), "-t", str(c["dur"]), "-i", V.J(c["file"]), "-vn", "-ac", "2", "-ar", str(SR), "-f", "s16le", "-"], capture_output=True).stdout
        st = np.frombuffer(raw, dtype=np.int16).astype(np.float64).reshape(-1, 2) / 32768
        n = min(len(st) // 4, int(0.05 * SR))
        if n:
            st[:n] *= np.linspace(0, 1, n)[:, None]
            st[-n:] *= np.linspace(1, 0, n)[:, None]
        prod_bus.add_stereo(c["frame"], st, 10 ** (c.get("gain_db", 0) / 20))
    for ln in lines:
        if ln["id"] in replaced:
            continue
        parts = ln.get("parts") or [{"at": ln["start"]}]
        voices = range(len(ln["voices"])) if ln.get("voices") else [0]
        for pi, part in enumerate(parts):
            if part.get("bleep"):
                continue
            for vi in voices:
                path = V.J("audio", "lines", "%s_%d_%d.wav" % (ln["id"], pi, vi))
                if not os.path.exists(path):
                    missing.append(ln["id"])
                    continue
                with wave.open(path) as w:
                    x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float64) / 32768
                act = x[np.abs(x) > 0.02]
                x = band(x * (0.15 / (np.sqrt((act ** 2).mean()) if len(act) else 1.0)), lo=85)
                many = len(voices) > 1
                gain = (0.55 if many else 1.0) * ln.get("gain", 1.0) * (0.8 if ln.get("soft") else 1.0)
                pan = (vi - (len(voices) - 1) / 2) * 0.35 if many else ln.get("pan", 0.0)
                dx.add(part["at"] + vi * 0.4, x, gain, pan)
                if ln["id"] in ("mara3", "mara5", "osei4"):       # spoken in the hall
                    hall_send.add(part["at"], x, gain, pan)
    room = convolve(dx.x, reverb_ir(0.35)) * 10 ** (-21 / 20)
    hall = convolve(hall_send.x, reverb_ir(1.4, hi=3500)) * 10 ** (-13 / 20)
    dialogue = dx.x + room + hall + prod_bus.x

    # ---------------- effects
    fx = Bus()
    for f, lvl in cues["clicks"]:
        if lvl <= 0.35:
            fx.add(f, one_shot("key_tap", peak=0.22 * lvl / 0.3), pan=float(RNG.uniform(-0.2, 0.2)))
        else:
            fx.add(f, one_shot("relay_click", peak=0.55 * lvl))
    b0, b1 = cues["bleep"]
    buzz = np.tile(one_shot("relay_buzz", 0, peak=0.32), 3)[: fr(b1 - b0)]
    buzz[-240:] *= np.linspace(1, 0, 240)
    fx.add(b0, buzz)
    for f in cues["keys"]:
        fx.add(f, one_shot("key_tap", peak=0.30))
    for f, name, k, peak, pan in CUES:
        x = one_shot(name, k, peak)
        if name == "modem":
            x = x[: fr(6)]
        fx.add(f, x, pan=pan)
    fx.add(120, bed("fan_wind", 118, -24))
    fx.add(0, bed("hall_tone", 120, -46))
    fx.add(320, bed("hall_tone", 300, -46))
    fx.add(880, bed("kitchen_tone", 80, -34))
    fx.add(1260, bed("underwater", 120, -30))
    riser = one_shot("riser", 0, 0.5)
    fx.add(960 - len(riser) / SR * FPS, riser)
    # the Enter key. The generated impact is a drone below 60 Hz that holds for a second and a half: on a small
    # speaker it is silent, and on a large one it buries the drop it is there to launch. So it is cut to a tail,
    # and the hit itself is drawn: the key's own click, a thump that falls from 150 Hz to 42, and a slap of noise.
    boom = one_shot("enter_impact", 0, 0.34)
    boom *= np.exp(-np.arange(len(boom)) / (0.45 * SR))
    fx.add(960, boom)
    fx.add(960, key_hit(0.62))
    fx.add(959.4, one_shot("key_tap", 0, 0.42))
    fx.add(1260, one_shot("sub_swell", 0, 0.14))                    # all of it is below 150 Hz: kept under the pad, not over it
    # the seventh pass's picture: every click of the cursor sends a ring out, a stamp lands, the wipe is a blade of
    # light, the tube the archive plays on switches off
    ring_bus = Bus()
    for f in (0, 10, 20, 25, 30, 1380, 1390, 1400, 1405, 1410):
        ring_bus.add(f, ping(0.05), pan=0.0)
    fx.x += ring_bus.x + convolve(ring_bus.x, reverb_ir(1.3, 600, 6000)) * 0.6
    for f, pk in ((290, 0.22), (472, 0.20), (520, 0.20), (545, 0.20)):          # 69 DAYS LATER. / SUGGESTED. / 10 YEARS. / 2 DAYS.
        fx.add(f, key_hit(pk))
    fx.add(95, one_shot("whip", 0, 0.20), pan=0.3)                              # the blade that wipes the wall
    fx.add(318, one_shot("tube_off", 0, 0.26))                                  # 1903 switches off
    h0, h1 = cues["heartbeat"]                     # the pulse under the turn: felt more than heard
    t = np.arange(int(0.3 * SR)) / SR
    thump = np.sin(2 * np.pi * 50 * t) * np.exp(-t / 0.06)
    for f in range(h0, h1, 20):
        fx.add(f, thump, 0.30)
        fx.add(f + 6, thump, 0.18)

    # the hall's tube lights come on out of three frames of black, pair after pair (measured from the shot: frames 123, 126, 129)
    for n, f in enumerate((123, 126, 129)):
        fx.add(f, one_shot("tube_on", n, 0.32), pan=(-0.5, 0.5, 0.0)[n])
    fx.add(145, bed("paper_flurry", 90, -26))                     # the blizzard of strips, under the fan
    fx.add(215, bed("paper_flutter", 10, -21, fade=2))            # the one strip in her fingers
    fx.add(878, one_shot("tube_off", 0, 0.36))                    # the tube beside Osei goes out
    fx.add(1380, one_shot("bar_zip", 0, 0.26))                    # the baton's light falls into the cursor
    fx.add(295, band(bed("fan_wind", 25, -30), 500, 2400))        # 1903: wind, thin and old
    fx.add(620, bed("hall_tone", 260, -50, fade=12))              # room tone under the quiet middle of the film: no dead air
    fx.add(440, metal_room(25, -41))                              # the bronze: a metal room
    # breaths, all from the one inhale that is real breath noise (the model's "soft breath" takes came back as rumble):
    gasp = one_shot("inhale", 0, 0.22)                            # after "...a prediction.", cut off by two frames of nothing, then the drop
    cut = fr(118) - fr(112.5)
    gasp = gasp[:cut].copy()
    gasp[-240:] *= np.linspace(1, 0, 240)
    fx.add(112.5, gasp)
    slow = one_shot("inhale", 0, 0.055)                            # near silence, one breath: it ends on the cut to Ray, who then speaks
    slow = np.interp(np.arange(0, len(slow), 1 / 1.6), np.arange(len(slow)), slow)
    fx.add(750 - len(slow) / SR * FPS, band(slow, hi=1800))
    for n, f in enumerate((41, 46, 51, 56, 61, 66, 71, 76, 81)):  # ink arriving on the wall, a stroke for each swap
        fx.add(f, one_shot("ink_scratch", n, 0.13), pan=float(RNG.uniform(-0.7, 0.7)))
    for f in range(541, 559, 2):                                  # the laptop types its label and the four lines of the hypothesis
        fx.add(f, one_shot("key_tap", peak=0.11))
    for f in range(563, 588, 3):                                  # the email types its question
        fx.add(f, one_shot("key_tap", peak=0.08))
    # the two control rooms: the real room, 18 February 2021 (the clip the picture comes from, where nobody is speaking)
    real = V.J("audio", "sfx_real_jpl_cheer.wav")
    if os.path.exists(real):
        st = stereo(real)
        st = st * (10 ** (-17 / 20) / (np.sqrt((st ** 2).mean()) + 1e-9))
        n_in, n_out = fr(2), fr(8)
        st[:n_in] *= np.linspace(0, 1, n_in)[:, None]
        st[-n_out:] *= np.linspace(1, 0, n_out)[:, None]
        fx.add_stereo(1208, st)
    # the riser and the kitchen step back for Pip's whisper, then come up into the Enter key
    # ... and three decibels for the two lines at the top of the flood (START IT WRONG. / WE'LL FIX IT.)
    # ... and before the first drop there is nothing at all for two frames (118 and 119)
    fx.x *= automation([(0, 0), (117.9, 0), (118, -120), (119.95, -120), (120, 0), (925, 0), (929, -14), (946, -14), (951, 0), (1186, 0), (1190, -3), (1246, -3), (1250, 0), (1440, 0)])[:, None]

    # ---------------- the whale: real clicks, in the rhythm of the coda
    wh = Bus()
    src = glob.glob(V.J("archive", "src", "H01_*.mp3"))
    if src:
        w = V.decode(src[0])
        e = envelope(w, 2)
        peaks = [i for i in range(200, len(e) - 200) if e[i] == e[i - 200:i + 200].max() and e[i] > 0.25 * e.max()]
        clicks = [w[max(0, p - 100): p + int(0.05 * SR)] * np.hanning(100 + int(0.05 * SR)) for p in peaks[:5]] or [w[: int(0.05 * SR)]]
        for i, f in enumerate(cues["whale"]):
            c = clicks[i % len(clicks)]
            wh.add(f, c / (np.abs(c).max() + 1e-9) * 0.5, pan=0.4 if i % 2 else -0.4)
        whale = wh.x * 0.6 + convolve(band(wh.x, 150, 2500), reverb_ir(2.6, 120, 2200)) * 0.9
    else:
        whale = wh.x

    # ---------------- score
    sc = Bus()
    sc.add_stereo(score_at, stereo(a.score))
    tv = band(sc.x, 350, 2800) * 10 ** (8 / 20)             # a small speaker has no bass: what is left is brought up so it can be heard at all
    in_c = automation([(0, -120), (239, -120), (240, 0), (318, 0), (320, -120), (1440, -120)])[:, None]
    under = band(sc.x, None, 2600)
    in_d = automation([(0, -120), (319, -120), (322, 0), (638, 0), (642, -120), (1440, -120)])[:, None]
    full = automation([(0, -120), (119, -120), (120, 0), (238, 0), (240, -120), (958, -120), (960, 0), (1259, 0), (1260, -120), (1440, -120)])[:, None]
    wide = automation([(0, -120), (1259, -120), (1260, 0), (1374, 0), (1380, -120), (1440, -120)])[:, None]
    # by passage: the wind, 1903, under the talk, nothing, then the flood (three decibels up now that the drop is
    # on the key and the boom no longer covers it), and the whale's pad where it can be heard under two voices
    level = automation([(0, -120), (119, -120), (120, -7), (240, -4), (320, -13), (640, -13), (662, -40), (690, -120), (958, -120), (960, -3), (1186, -3), (1190, -6.5), (1246, -6.5), (1250, -3), (1259.9, -3), (1260, -4), (1374, -6), (1380, -120), (1440, -120)])[:, None]
    t_f = np.arange(N) / SR * FPS
    no_kick = np.interp(t_f, [1239, 1240, 1259.6, 1260], [0, 1, 1, 0])[:, None]       # the kick leaves on the last two beats before the whale
    flood = sc.x * (1 - no_kick) + band(sc.x, 190, None) * no_kick
    music = (flood * full + tv * in_c + under * in_d + sc.x * wide) * level
    pad_file = V.J("audio", "music", "whale_pad_take1.mp3")                           # when the kick goes at 0:26.7: a held pad, the whale's voices heard early
    if os.path.exists(pad_file):
        pad = stereo(pad_file)[int(1.1 * SR): int(1.1 * SR) + fr(40)]
        pad = pad * (10 ** (-31 / 20) / (np.sqrt((pad ** 2).mean()) + 1e-9))
        n_in, n_out = fr(5), fr(16)
        pad[:n_in] *= np.linspace(0, 1, n_in)[:, None]
        pad[-n_out:] *= np.linspace(1, 0, n_out)[:, None]
        music[fr(638): fr(638) + len(pad)] += pad
    a0, a1, cell = fr(1200), fr(1210), fr(2.5)                   # IT CRASHED ON THE THIRD LETTER: the music stutters for one beat
    grain = music[a0:a0 + cell].copy()
    grain[:240] *= np.linspace(0, 1, 240)[:, None]
    grain[-240:] *= np.linspace(1, 0, 240)[:, None]
    music[a0:a1] = np.tile(grain, (int(np.ceil((a1 - a0) / cell)), 1))[: a1 - a0]
    duck = 1 - 0.45 * np.clip(envelope(dialogue, 120) / 0.02, 0, 1)
    music = music * duck[:, None]

    # ---------------- sum and master
    stems = dict(dialogue=dialogue, effects=fx.x, score=music, whale=whale)
    os.makedirs(V.J("audio", "stems"), exist_ok=True)

    def write(path, x):
        with wave.open(path, "wb") as w:
            w.setnchannels(2)
            w.setsampwidth(2)
            w.setframerate(SR)
            w.writeframes((np.clip(x, -1, 1) * 32767).astype(np.int16).tobytes())

    for k, v in stems.items():
        write(V.J("audio", "stems", k + ".wav"), v)
    # The master is one gain for the whole film and a soft ceiling, nothing that rides the level. (The loudness
    # filter used until v008 turned the quiet middle of the film up by six decibels and let the first heartbeat
    # after it land that much too loud: measured, frame by frame, against the stems.)
    pre = a.out.replace(".wav", "_pre.wav")

    def loudness(path):
        r = subprocess.run(["ffmpeg", "-nostats", "-i", path, "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True).stderr
        t = r[r.rfind("Summary:"):]
        import re
        g = lambda pat: float((re.search(pat, t) or [None, "nan"])[1])
        return g(r"I:\s+(-?[\d.]+) LUFS"), g(r"Peak:\s+(-?[\d.]+) dBFS")

    raw = sum(stems.values())
    ceiling = 10 ** (-1.6 / 20)
    gain = 1.0
    for _ in range(4):                                             # the ceiling takes a little loudness off, so the gain is found in a few steps
        mix = ceiling * np.tanh(raw * gain / ceiling)
        write(pre, mix)
        lufs, peak = loudness(pre)
        if abs(lufs + 14.0) < 0.1:
            break
        gain *= 10 ** ((-14.0 - lufs) / 20)
    os.replace(pre, a.out)
    print("master: one gain of %+.1f dB and a soft ceiling at %.1f dBFS" % (20 * np.log10(gain), 20 * np.log10(ceiling)))

    # ---------------- what the meters say
    r = subprocess.run(["ffmpeg", "-nostats", "-i", a.out, "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True).stderr
    tail = r[r.rfind("Summary:"):]
    import re
    g = lambda pat: (re.search(pat, tail) or [None, "?"])[1]
    print("loudness %s LUFS, range %s LU, true peak %s dBFS" % (g(r"I:\s+(-?[\d.]+) LUFS"), g(r"LRA:\s+(-?[\d.]+) LU"), g(r"Peak:\s+(-?[\d.]+) dBFS")))

    def db(x):
        return 20 * np.log10(np.sqrt((x ** 2).mean()) + 1e-9)

    print("passage          speech   bed (score+effects+whale)")
    for name, f0, f1 in (("A open", 0, 120), ("B wind", 120, 240), ("C 1903", 240, 320), ("D talk", 320, 620), ("D3 voice", 620, 750), ("E turn", 750, 880),
                         ("F kitchen", 880, 960), ("G flood", 960, 1260), ("H whale", 1260, 1380), ("I end", 1380, 1440)):
        s = slice(fr(f0), fr(f1))
        print("%-14s %7.1f dB %7.1f dB" % (name, db(dialogue[s]), db(music[s] + fx.x[s] + whale[s])))
    if missing:
        print("no performed voice for: %s" % ", ".join(sorted(set(missing))))


if __name__ == "__main__":
    main()
