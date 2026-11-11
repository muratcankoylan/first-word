#!/usr/bin/env python3
"""FIRST WORD: put the score's drop on the Enter key, and give the whale its own five seconds.

    python3 tools/score_edit.py        audio/music/score_take1.mp3 + whale_pad_take*.mp3 -> audio/music/score_cut1.wav

The composed score keeps strict time (144.0 BPM from end to end; its second take drifts to about 142 in the drop,
which is why take 1 is the one used). Three things about it were wrong for the picture. All three were found by
measuring the file, and none was judged by ear:

  1. Every hit sits 20 ms after the beat, from the first bar on (the file opens with 20 ms of nothing). That is half
     a film frame late on every cut. The 20 ms are taken off the front.
  2. The full kit comes in 36.25 s into the file where the plan has it at 35.0 s, which is frame 960, the Enter key:
     for 30 frames after the key the film had no music. 1.25 s is taken out before the drop. That is three beats
     exactly, so the beat stays where it was, and the stretch that goes is silence and the first whisper of the riser,
     which the mix keeps closed anyway.
  3. The drums ran on for 1.9 s into the whale, and what followed was only their echo. The drums now stop just short
     of the beat at 47.5 s (frame 1260, where the plan says the engine cuts out), the file's own echo follows that
     stop, and over it lie two takes of a pad made for the passage (tools/sound.py pad): held voices on D and A, then
     a second breath 1.75 s later.
"""
import os
import subprocess
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import voices as V  # noqa: E402

SR = V.SR
SRC = V.J("audio", "music", "score_take1.mp3")
PAD = [(V.J("audio", "music", "whale_pad_take2.mp3"), 0.0), (V.J("audio", "music", "whale_pad_take1.mp3"), 1.75)]   # file, seconds after the stop
OUT = V.J("audio", "music", "score_cut1.wav")
LEAD = 0.020                 # the file's hits sit this long after the beat
CUT = (33.0, 34.25)          # taken out, in beat time: three beats before the drop
STOP = 47.5                  # in the cut file: where the drums stop (film frame 1260)
ECHO_FROM = 49.47            # in the source: after its last hit, the echo that is left
PAD_PEAK = -18.0             # the loudest half second of each pad take, in dB; the drop measures about -13
ECHO_GAIN = -3.0


def stereo(path):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-ac", "2", "-ar", str(SR), "-f", "s16le", "-"], capture_output=True).stdout
    return np.frombuffer(raw, dtype=np.int16).astype(np.float64).reshape(-1, 2) / 32768


def s(t):
    return int(round(t * SR))


def rms_db(x):
    return 20 * np.log10(np.sqrt((x ** 2).mean()) + 1e-9)


def main():
    x = stereo(SRC)
    n = s(0.030)
    head = x[s(LEAD): s(CUT[0] + LEAD) + n].copy()
    drop = x[s(CUT[1] + LEAD): s(STOP + (CUT[1] - CUT[0]) + LEAD)].copy()
    r = np.linspace(0, 1, n)[:, None]
    head[-n:] = head[-n:] * (1 - r) + drop[:n] * r                      # a 30 ms join, in a stretch that is all but silent
    y = np.concatenate([head, drop[n:]])
    assert len(y) == s(STOP), (len(y), s(STOP))
    k0, k1 = s(0.060), s(0.015)                                         # the engine stops: a 45 ms fade that ends 15 ms short of the beat
    y[-k0:-k1] *= (np.linspace(1, 0, k0 - k1) ** 2)[:, None]
    y[-k1:] = 0
    out = np.zeros((s(STOP + 8.0), 2))
    out[:len(y)] = y
    echo = x[s(ECHO_FROM):].copy() * 10 ** (ECHO_GAIN / 20)
    echo[:s(0.008)] *= np.linspace(0, 1, s(0.008))[:, None]
    out[s(STOP): s(STOP) + len(echo)] += echo
    for path, after in PAD:
        p = stereo(path)
        half = SR // 2
        loud = max(rms_db(p[i:i + half]) for i in range(0, len(p) - half, half // 2))
        p *= 10 ** ((PAD_PEAK - loud) / 20)
        a = s(STOP + after)
        p = p[: len(out) - a]
        out[a: a + len(p)] += p
    out[-s(0.5):] *= np.linspace(1, 0, s(0.5))[:, None]
    pcm = (np.clip(out, -1, 1) * 32767).astype(np.int16)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "s16le", "-ar", str(SR), "-ac", "2", "-i", "-", OUT], input=pcm.tobytes(), check=True)
    m = out.mean(axis=1)
    film = lambda t: (t + 5.0) * 24
    print("wrote %s, %.2f s" % (os.path.relpath(OUT, V.ROOT), len(out) / SR))
    for name, t0, t1 in (("the half beat before the drop", 34.79, 35.0), ("the first half beat of the drop", 35.0, 35.21), ("the last beat of the drums", STOP - 0.43, STOP - 0.015),
                         ("the first second after they stop", STOP, STOP + 1), ("second 2", STOP + 1, STOP + 2), ("second 3", STOP + 2, STOP + 3), ("second 4", STOP + 3, STOP + 4), ("second 5", STOP + 4, STOP + 5)):
        print("  %-34s %6.2f to %6.2f s (frames %4d to %4d)  %6.1f dB" % (name, t0, t1, round(film(t0)), round(film(t1)), rms_db(m[s(t0):s(t1)])))


if __name__ == "__main__":
    main()
