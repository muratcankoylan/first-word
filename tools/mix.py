#!/usr/bin/env python3
"""FIRST WORD: the mix.

Four buses at 48 kHz stereo, each also written as a stem: dialogue (the performed lines, with a little room),
effects (generated and drawn sounds placed on the frames in timing/sound.json and in the passages below), score
(the theme as cut to the picture by tools/score_build.py, ridden here and opened up where the voices are) and the
whale (real NOAA sperm whale clicks, cut to the 1+1+3 rhythm). The sum is mastered to -14 LUFS by one gain over the
whole film and a look-ahead limiter at -2.6 dBFS (about -1.6 between samples).

    python3 tools/mix.py --out audio/mix_v011.wav

Rebuilt on the eighth pass. The effects are made with the newer effects model where it measured as a whole sound
(audio/sfx2/, see timing/sfx.json "sfx2"). No sound in the film is drawn in arithmetic any more: where a model gave
only rumble (a heartbeat, a television switching off, the low end of a hit) the sound was asked for again, and what
came back is shaped here (cut short, tuned by a few cents, its middle brought up) rather than replaced. The score no
longer fills the first half of the film with sub bass. The
voices no longer push the whole score down: they open a space in its middle. And the ceiling is a limiter, not a
soft clip, which was bending the loudest passage.

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
SCORE_DB = 5.0        # tools/score_build.py writes the score this far down, for headroom
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


SKIP = {"teletype_key_3", "stamp_hit_2", "tube_off_1", "crt_off_2", "cine_hit_3", "bronze_tone_1"}     # came back as rumble and nothing else (audio/sfx2/measured.json), or the weaker of two


def takes(name):
    """The files of a sound: the eighth pass's set when it has the sound, the first set when it does not."""
    for folder in ("sfx2", "sfx"):
        files = [f for f in sorted(glob.glob(V.J("audio", folder, name + "_*.mp3"))) if os.path.basename(f)[:-4] not in SKIP]
        if files:
            return files
    raise FileNotFoundError(name)


SNAP = {"relay_click", "key_tap", "teletype_key", "stamp_hit", "cine_hit", "tube_on", "tube_off", "paper_snap", "paper_slap", "paper_rip", "cap_pop", "projector", "crt_switch_off", "ring_ping"}
SWELL = {"whoosh"}        # sounds that pass by: their loudest moment, not their start, belongs on the frame


def one_shot(name, k=None, peak=0.5):
    files = takes(name)
    path = files[(k if k is not None else int(RNG.integers(0, len(files)))) % len(files)]
    x = V.decode(path)
    a, b = V.speech_span(x)
    x = x[a:b] if b > a else x
    if name in SNAP and len(x) > SR // 50:
        # A hit belongs on its frame. The generated files have air before the hit (measured: the first set and the
        # second both landed about two thirds of a frame late). The sound now starts two milliseconds before its
        # first sharp rise.
        hop = SR // 2000
        e = np.sqrt((x[:len(x) // hop * hop].reshape(-1, hop) ** 2).mean(axis=1))
        d = np.maximum(0, np.diff(np.convolve(e, np.ones(4) / 4, "same")))
        if len(d) and d.max() > 0:
            i = int(np.argmax(d)) if name in ("stamp_hit", "projector", "cine_hit", "crt_switch_off") else int(np.argmax(d > 0.6 * d.max()))   # a slam has a soft front: its sharpest moment is the one to place
            x = x[max(0, i * hop - int(0.002 * SR)):].copy()
            n = min(len(x), int(0.001 * SR))
            x[:n] *= np.linspace(0, 1, n)
    m = np.abs(x).max()
    x = x * (peak / m) if m > 0 else x
    n = min(len(x) // 3, 480)
    if n:
        x[-n:] *= np.linspace(1, 0, n)
    return x


def bed(name, frames, level_db, fade=6):
    """An ambience stretched over a span by looping with crossfades, at a given RMS level."""
    x = V.decode(takes(name)[0])
    rms = np.sqrt((x ** 2).mean()) + 1e-9
    x = x * (10 ** (level_db / 20) / rms)
    need = fr(frames)
    xf = int(0.25 * SR)
    out = x.copy()
    while len(out) < need:
        tail, head = out[-xf:], x[:xf]
        out = np.concatenate([out[:-xf], tail * np.linspace(1, 0, xf) + head * np.linspace(0, 1, xf), x[xf:]])
    out = out[:need]
    out = limit(np.stack([out, out], axis=1), 10 ** ((level_db + 14) / 20), look=0.003, release=0.04)[0][:, 0]     # a bed is a bed: no snap in it stands more than 14 dB over it
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


def impact(peak, tail, k=0):
    """The low part of a hit: a generated cinematic impact (all of it is below 150 Hz), cut to the length the moment
    wants. On a large speaker it is the weight of the hit; on a small one the slam over it carries alone."""
    x = one_shot("cine_hit", k, peak)
    return x * np.exp(-np.arange(len(x)) / (tail * SR))


def stamp(peak, k=0):
    """A stamp landing on the picture: the slap of it, and a short boom under it. Both are generated sounds."""
    a, b = one_shot("stamp_hit", k, peak), impact(peak * 0.6, 0.09, k)
    out = np.zeros(max(len(a), len(b)))
    out[:len(a)] += a
    out[:len(b)] += b
    return out


def heart(peak):
    """One heartbeat, lub-dub: a generated one, which is nearly all below 150 Hz as a real one is, with the knock in
    its middle (140 to 900 Hz) brought up three times so that a laptop plays something too."""
    x = V.decode(V.J("audio", "sfx2", "heart_1.mp3"))
    a, b = V.speech_span(x)
    x = x[a:b] if b > a else x
    x = band(x, None, 140) + 3.0 * band(x, 140, 900)
    n = min(len(x) // 4, 960)
    x[:240] *= np.linspace(0, 1, 240)
    x[-n:] *= np.linspace(1, 0, n)
    return x / np.abs(x).max() * peak


def faster(x, factor):
    """A sound played faster and higher (or slower and lower) by resampling: a tape sped up."""
    return np.interp(np.arange(0, len(x) - 1, factor), np.arange(len(x)), x)


def limit(x, ceiling, look=0.005, release=0.09):
    """A look-ahead limiter: where the sum would pass the ceiling the level is eased down five milliseconds early and
    let back up slowly. Both channels move together. Returns the limited sound and the gain it applied."""
    from scipy.ndimage import minimum_filter1d, uniform_filter1d
    pk = np.abs(x).max(axis=1)
    need = np.minimum(1.0, ceiling / np.maximum(pk, 1e-9))
    w = int(look * SR)
    need = minimum_filter1d(need, size=2 * w + 1, mode="nearest")
    g = need.copy()
    a = np.exp(-1.0 / (release * SR))
    cur = 1.0
    for i in range(len(g)):                                 # down at once, back up slowly
        cur = min(need[i], a * cur + (1 - a))
        g[i] = cur
    g = uniform_filter1d(minimum_filter1d(g, size=w + 1, mode="nearest"), size=w + 1, mode="nearest")
    y = x * g[:, None]
    return np.clip(y, -ceiling, ceiling), g


def tame(x, thr_db=-18.0, ratio=2.5, top_db=-5.0):
    """A voice evened out, as a dialogue mixer would do it: what is louder than the threshold is brought nearer to it
    (2.5 to 1, over 20 ms, looking both ways so that nothing is shaved off the front of a word), and no sample passes
    top_db. The line is put back at the level it came in at: as loud as before, with peaks eleven decibels over its
    level and not sixteen. Until the eighth pass the voices in the flood touched full scale, and the ceiling bent them."""
    from scipy.ndimage import uniform_filter1d
    act = np.abs(x) > 0.02
    before = np.sqrt((x[act] ** 2).mean()) if act.any() else 0.0
    env = np.sqrt(uniform_filter1d(x ** 2, int(0.020 * SR), mode="nearest") + 1e-12)
    over = np.maximum(0.0, 20 * np.log10(env) - thr_db)
    gr = uniform_filter1d(over * (1 - 1 / ratio), int(0.040 * SR), mode="nearest")
    y = x * 10 ** (-gr / 20)
    after = np.sqrt((y[act] ** 2).mean()) if act.any() else 0.0
    if after > 0:
        y = y * before / after
    y, _ = limit(np.stack([y, y], axis=1), 10 ** (top_db / 20), look=0.003, release=0.05)
    return y[:, 0]


def ping(peak):
    """The ring a click sends out, as sound: two generated glass chimes, tuned by a few cents to notes of the film's
    key (their own strongest notes measured as an A a quarter-tone flat and a D sharp: they are played 1.4 percent
    faster and 6.5 percent slower, which makes them A5 and D7). It sits far under the click itself, which stays dry."""
    a = faster(one_shot("ring_ping", 2, 1.0), 880.0 / 868.0)
    b = faster(one_shot("ring_ping", 0, 1.0), 2349.32 / 2513.0)
    out = np.zeros(max(len(a), len(b)))
    out[:len(a)] += a
    out[:len(b)] += 0.4 * b
    return out / np.abs(out).max() * peak


# effects that are not in timing/sound.json: frame, sound, variant, peak, pan
CUES = [
    (155, "paper_snap", 0, 0.30, -0.5), (165, "paper_snap", 1, 0.25, 0.6), (185, "paper_snap", 2, 0.30, 0.4), (195, "paper_snap", 1, 0.25, -0.6),     # on the off-beats
    (205, "paper_slap", 0, 0.45, 0.0), (238, "paper_slap", 1, 0.48, 0.0),          # on her cheek as the shot opens; flat on the lens at frame 238
    (243, "pencil_squeak", 0, 0.28, -0.2), (249, "pencil_squeak", 1, 0.26, 0.2), (268, "pencil_squeak", 2, 0.25, 0.0),     # the three strokes under the 1903 line
    (312.0, "telegraph", 0, 0.22, 0.3), (313.7, "telegraph", 0, 0.20, 0.3), (315.4, "telegraph", 0, 0.20, 0.3), (314.5, "pencil_squeak", 1, 0.25, -0.1),
    (427, "cap_pop", 0, 0.40, 0.0), (487, "pencil_squeak", 1, 0.35, 0.0), (500, "paper_rip", 0, 0.50, 0.0), (604, "send_whoosh", 0, 0.30, 0.2),
    (945, "inhale", 0, 0.35, 0.0), (981, "pencil_squeak", 0, 0.16, 0.2), (985, "pencil_squeak", 1, 0.16, 0.3), (1000, "pencil_write", 0, 0.26, 0.0),
    (95, "whoosh", 2, 0.22, 0.3),                                                   # the blade of light that wipes the wall
    (1230, "whoosh", 1, 0.13, -0.5), (1235, "whoosh", 3, 0.13, -0.25), (1240, "whoosh", 1, 0.13, 0.0), (1245, "whoosh", 3, 0.13, 0.25), (1250, "whoosh", 1, 0.14, 0.5),   # the baton, hand to hand
    (1256, "whoosh", 2, 0.30, 0.0),                                                 # the whip tilt up into the blue
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=V.J("audio", "mix.wav"))
    ap.add_argument("--score", default=V.J("audio", "music", "score_cut2.wav"))    # the theme cut to the picture, film frame 0 at its start: tools/score_build.py
    a = ap.parse_args()
    lines = json.load(open(V.J("timing", "lines.json")))["lines"]
    cues = json.load(open(V.J("timing", "sound.json")))
    shots = {s["id"]: s for s in json.load(open(V.J("shotlist.json")))["shots"]}

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
                x = tame(band(x * (0.15 / (np.sqrt((act ** 2).mean()) if len(act) else 1.0)), lo=85))
                many = len(voices) > 1
                gain = (0.45 if many else 1.0) * ln.get("gain", 1.0) * (0.8 if ln.get("soft") else 1.0)
                pan = (vi - (len(voices) - 1) / 2) * 0.35 if many else ln.get("pan", 0.0)
                dx.add(part["at"] + vi * 0.4, x, gain, pan)
                if ln["id"] in ("mara3", "mara5", "osei4"):       # spoken in the hall
                    hall_send.add(part["at"], x, gain, pan)
    room = convolve(dx.x, reverb_ir(0.35)) * 10 ** (-21 / 20)
    hall = convolve(hall_send.x, reverb_ir(1.4, hi=3500)) * 10 ** (-13 / 20)
    dialogue = limit(dx.x + room + hall + prod_bus.x, 10 ** (-3.5 / 20), look=0.003, release=0.06)[0]      # five voices at once can still add up: the bus has a ceiling of its own

    # ---------------- effects
    fx = Bus()
    send = Bus()                                   # what goes to the long room: stamps, the key, the title
    for f, lvl in cues["clicks"]:
        if lvl <= 0.35:
            fx.add(f, one_shot("key_tap", peak=0.22 * lvl / 0.3), pan=float(RNG.uniform(-0.2, 0.2)))
        else:                                      # the relay: the body of the armature, and the tick of its contact on top
            fx.add(f, one_shot("relay_click", 1 + int(f) % 2, peak=0.50 * lvl))
            fx.add(f, one_shot("relay_click", 0, peak=0.20 * lvl))
    b0, b1 = cues["bleep"]
    buzz = np.tile(one_shot("relay_buzz", 1, peak=0.32), 3)[: fr(b1 - b0)]
    buzz[-240:] *= np.linspace(1, 0, 240)
    fx.add(b0, buzz)
    for n, f in enumerate(cues["keys"]):           # Rosa's finger, one key at a time: three in the macro, four as the last letters arrive on her screen
        fx.add(f, one_shot("key_tap", n, peak=0.30))
    for f, name, k, peak, pan in CUES:
        s_ = one_shot(name, k, peak)
        if name in SWELL:                          # a whoosh is placed by its loudest moment
            e_ = envelope(s_, 10)
            f = f - int(np.argmax(e_)) / SR * FPS
        fx.add(f, s_, pan=pan)

    # the open: ink arriving on the wall, a stroke for each swap; the gasp after "...a prediction.", cut off by two frames of nothing
    for n, f in enumerate((41, 46, 51, 56, 61, 66, 71, 76, 81)):
        fx.add(f, one_shot("ink_scratch", n, 0.13), pan=float(RNG.uniform(-0.7, 0.7)))
    fx.add(0, bed("hall_tone", 120, -46))
    gasp = one_shot("inhale", 0, 0.22)             # the one inhale that is real breath noise (the model's "soft breath" takes came back as rumble)
    cut = fr(118) - fr(112.5)
    gasp = gasp[:cut].copy()
    gasp[-240:] *= np.linspace(1, 0, 240)
    fx.add(112.5, gasp)

    # the hall of wind (120 to 240): the theme comes in without a kick drum, so the cut itself is given a hit; the
    # tube lights strike on pair after pair (measured from the shot: frames 123, 126, 129); wind, and paper in it
    fx.add(120, impact(0.34, 0.25))
    fx.add(120, one_shot("stamp_hit", 0, 0.16))
    for n, f in enumerate((123, 126, 129)):
        fx.add(f, one_shot("tube_on", n, 0.32), pan=(-0.5, 0.5, 0.0)[n])
    fx.add(120, bed("fan_wind", 118, -25))
    fx.add(145, bed("paper_flurry", 90, -27))
    fx.add(215, bed("paper_flutter", 10, -21, fade=2))

    # 1903 (240 to 320): the thin old wind, the stamp, and the set switching off
    fx.add(295, band(bed("fan_wind", 25, -30), 500, 2400))
    fx.add(318, one_shot("crt_switch_off", 0, 0.24))               # the set's switch, and its tube dying: a generated motor running down, played twice as fast and an octave up
    dying = faster(one_shot("power_down", 2, 0.15), 2.2)
    dying[-480:] *= np.linspace(1, 0, 480)
    fx.add(318, dying)

    # the talk (320 to 640): the hall's own tone, a metal room for the bronze, the laptop and the email typing
    fx.add(320, bed("hall_tone", 300, -46))
    fx.add(620, bed("hall_tone", 260, -50, fade=12))              # under the quiet middle of the film: no dead air
    fx.add(440, bed("bronze_tone", 25, -41))                        # the bronze: a metal room
    for f in range(541, 559, 2):
        fx.add(f, one_shot("key_tap", peak=0.11))
    for f in range(563, 588, 3):
        fx.add(f, one_shot("key_tap", peak=0.08))
    for f, pk, k in ((290, 0.22, 0), (472, 0.20, 1), (520, 0.20, 0), (545, 0.20, 1)):       # 69 DAYS LATER. / SUGGESTED. / 10 YEARS. / 2 DAYS.
        s_ = stamp(pk, k)
        fx.add(f, s_)
        send.add(f, s_, 0.5)

    # Casey Harrell (620 to 750): the electrodes are a faint crackle that grows busy while his sentence is written
    # from them; each pair of letters is a soft tick; the two stamps land quietly; one slow breath ends on the cut
    crackle = bed("neural_static", 104, -40, fade=10)
    crackle *= 10 ** (np.interp(np.arange(len(crackle)) / SR * FPS + 646, [646, 692, 698, 711, 716, 750], [-6, -4, 6, 7, -3, -8]) / 20)
    fx.add(646, crackle, pan=-0.15)
    chatter = one_shot("data_chatter", 0, 0.085)[: fr(16)]
    chatter[-fr(3):] *= np.linspace(1, 0, fr(3))
    fx.add(696, chatter, pan=0.2)
    for n in range(14):
        fx.add(696 + n * 1.05, one_shot("key_tap", n, 0.07), pan=-0.1)
    for f, pk in ((714, 0.10), (722, 0.12)):       # DECODED. / THEN SPOKEN, IN HIS OWN VOICE. (quiet: Mara is still speaking)
        s_ = stamp(pk, 2)
        fx.add(f, s_)
        send.add(f, s_, 0.7)
    slow = one_shot("inhale", 0, 0.055)            # near silence, one breath: it ends on the cut to Ray, who then speaks
    slow = np.interp(np.arange(0, len(slow), 1 / 1.6), np.arange(len(slow)), slow)
    fx.add(750 - len(slow) / SR * FPS, band(slow, hi=1800))

    # the turn (750 to 880): a pulse, and the tube beside Osei going out
    h0, h1 = cues["heartbeat"]
    for f in range(h0, h1, 20):
        fx.add(f, heart(0.30))
    fx.add(878, one_shot("tube_off", 0, 0.36))

    # the kitchen (880 to 960): the room, a riser that ends a frame and a half before the key, and the key itself.
    # The key is three things at once: its own click, a slam, and a boom under it.
    fx.add(880, bed("kitchen_tone", 80, -34))
    riser = one_shot("riser", 1, 0.42)
    riser[-int(0.004 * SR):] *= np.linspace(1, 0, int(0.004 * SR))
    fx.add(958.5 - len(riser) / SR * FPS, riser)
    boom = impact(0.26, 0.55)
    hit = one_shot("stamp_hit", 0, 0.30)
    fx.add(960, boom)
    fx.add(960, hit)
    send.add(960, hit, 0.8)
    fx.add(959.4, one_shot("key_tap", 0, 0.30))

    # the flood (960 to 1260): a slide projector advances on every specimen; then the first word on the network
    for n, sid in enumerate("G%02d" % k for k in range(17, 30)):
        fx.add(shots[sid]["start"], one_shot("projector", n, 0.15), pan=0.35 if n % 2 else -0.35)
    modem = one_shot("modem", 0, 0.22)[: fr(6)]
    modem[-fr(1):] *= np.linspace(1, 0, fr(1))
    fx.add(1186, modem)
    for n, f in enumerate((1190, 1193)):           # L, then O: a teleprinter's key for each letter that arrives
        fx.add(f, one_shot("teletype_key", n, 0.34))
    crash = one_shot("glitch_crash", 0, 0.42)[: fr(14)]
    crash[-fr(3):] *= np.linspace(1, 0, fr(3))
    fx.add(1196, crash)
    s_ = stamp(0.22, 0)                            # IT CRASHED.
    fx.add(1201, s_)
    send.add(1201, s_, 0.5)
    fx.add(1209.5, one_shot("power_up", 1, 0.20))  # ...and an hour later it is up again: G, I, N
    for n, f in enumerate((1210, 1212, 1214)):
        fx.add(f, one_shot("teletype_key", n + 1, 0.32))
    s_ = stamp(0.18, 1)                            # FIXED AN HOUR LATER.
    fx.add(1210, s_)
    send.add(1210, s_, 0.5)
    # the two control rooms (1220 to 1225): the real room, 18 February 2021 (the clip the picture comes from, where nobody is speaking)
    real = V.J("audio", "sfx_real_jpl_cheer.wav")
    if os.path.exists(real):
        st = stereo(real)
        st = st * (10 ** (-17 / 20) / (np.sqrt((st ** 2).mean()) + 1e-9))
        n_in, n_out = fr(2), fr(8)
        st[:n_in] *= np.linspace(0, 1, n_in)[:, None]
        st[-n_out:] *= np.linspace(1, 0, n_out)[:, None]
        fx.add_stereo(1218, st)

    # the whale (1260 to 1380): the engine stops, and what is left is water
    fx.add(1260, bed("underwater", 120, -30))
    fx.add(1260, one_shot("sub_drop", 0, 0.14))
    fx.add(1259.6, one_shot("power_down", 1, 0.17))                 # the engine running down: what a small speaker hears of it

    # the end card (1380 to 1440): the baton's light falls into the cursor; the answer types itself; a question lands on the last three clicks
    fx.add(1380, one_shot("bar_zip", 1, 0.26))
    for n in range(6):
        fx.add(1390 + n * 1.5, one_shot("key_tap", n, 0.09), pan=0.1)
    for f, pk, k_, wet in ((1400, 0.12, 1, 0.6), (1405, 0.14, 2, 0.6), (1410, 0.19, 0, 1.0)):       # WHAT / WILL YOU / START?: one part of the question on each of the last three clicks
        s_ = stamp(pk, k_)
        fx.add(f, s_)
        send.add(f, s_, wet)
    fx.add(1410, impact(0.20, 0.7))                 # the last word has weight under it, and the room keeps it
    swell = one_shot("riser", 1, 0.13)[-fr(9):].copy()          # the last third of a second of the riser, into the last word
    swell[: fr(3)] *= np.linspace(0, 1, fr(3))
    fx.add(1410 - len(swell) / SR * FPS, swell)

    # every click of the cursor sends a ring out: two high notes of the film's key, far under the click
    ring_bus = Bus()
    for f in (0, 10, 20, 25, 30, 1380, 1390, 1400, 1405, 1410):
        ring_bus.add(f, ping(0.05), pan=0.0)
    fx.x += ring_bus.x + convolve(ring_bus.x, reverb_ir(1.3, 600, 6000)) * 0.6
    fx.x += convolve(send.x, reverb_ir(1.6, 250, 4500)) * 10 ** (-15 / 20)     # the long room behind the stamps and the key

    # the riser and the kitchen step back for Pip's whisper, then come up into the Enter key
    # ... and three decibels for the lines at the top of the flood (START IT WRONG. / WE'LL FIX IT.)
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

    # ---------------- score: cut to the picture by tools/score_build.py (film frame 0 at its start); here it is only ridden
    sc = Bus()
    sc.add_stereo(0, stereo(a.score))
    t_f = np.arange(N) / SR * FPS
    no_kick = np.interp(t_f, [1239, 1240, 1259.6, 1260], [0, 1, 1, 0])[:, None]       # the kick leaves on the last two beats before the whale
    music = sc.x * (1 - no_kick) + band(sc.x, 190, None) * no_kick
    # the file is written five decibels down so that its peaks are whole; the lines at the top of the flood get room
    music = music * 10 ** (SCORE_DB / 20) * automation([(0, 0), (1186, 0), (1190, -3.5), (1246, -3.5), (1250, 0), (1440, 0)])[:, None]
    a0, a1, cell = fr(1200), fr(1210), fr(2.5)                   # IT CRASHED.: the music stutters for one beat, and is whole again on FIXED
    grain = music[a0:a0 + cell].copy()
    grain[:240] *= np.linspace(0, 1, 240)[:, None]
    grain[-240:] *= np.linspace(1, 0, 240)[:, None]
    music[a0:a1] = np.tile(grain, (int(np.ceil((a1 - a0) / cell)), 1))[: a1 - a0]
    # The voices do not push the whole score down any more. They open its middle, where speech lives, by seven
    # decibels, take three off its top, and leave its bass almost alone: the music stays up and the words stay clear.
    said = np.clip(envelope(dialogue, 120) / 0.02, 0, 1)[:, None]
    low, high = band(music, None, 220), band(music, 5200, None)
    mid = music - low - high
    music = low * (1 - 0.15 * said) + mid * (1 - 0.55 * said) + high * (1 - 0.30 * said)

    # ---------------- sum and master
    stems = dict(dialogue=dialogue, effects=fx.x, score=music, whale=whale)
    os.makedirs(V.J("audio", "stems"), exist_ok=True)

    def write(path, x):
        """24-bit: the quiet tails (the whale's pad, the last fade) keep their bottom instead of being cut to 16 bits."""
        with wave.open(path, "wb") as w:
            w.setnchannels(2)
            w.setsampwidth(3)
            w.setframerate(SR)
            v = np.round(np.clip(x, -1, 1) * 8388607).astype("<i4")
            w.writeframes(np.ascontiguousarray(v).view(np.uint8).reshape(-1, 4)[:, :3].tobytes())

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
    ceiling = 10 ** (-2.6 / 20)                                    # in samples; between samples the peak then measures about a decibel higher
    gain = 1.0
    for _ in range(4):                                             # the limiter takes a little loudness off, so the gain is found in a few steps
        mix, g = limit(raw * gain, ceiling)
        write(pre, mix)
        lufs, peak = loudness(pre)
        if abs(lufs + 14.0) < 0.1:
            break
        gain *= 10 ** ((-14.0 - lufs) / 20)
    os.replace(pre, a.out)
    gr = -20 * np.log10(np.maximum(g, 1e-6))
    print("master: one gain of %+.1f dB and a limiter at %.1f dBFS. The limiter works for %.1f percent of the film; the most it takes off is %.1f dB (at frame %d); more than 3 dB for %.2f percent." % (
        20 * np.log10(gain), 20 * np.log10(ceiling), 100 * (gr > 0.1).mean(), gr.max(), int(np.argmax(gr) / SR * FPS), 100 * (gr > 3).mean()))

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
