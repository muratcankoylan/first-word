#!/usr/bin/env python3
"""FIRST WORD: temp guide track for the animatic.

Builds audio/temp_mix.wav from timing/sound.json (relay clicks, kick, cues) and timing/lines.json
(scratch voices made with the macOS `say` command). Nothing here is final sound. The scratch voices exist
to answer one question before any money is spent: does every line fit the slot the cut gives it?

Writes timing/scratch_durations.json (measured length of every line, in frames) and out/fit_report.md.
"""
import hashlib
import json
import os
import re
import subprocess
import sys
import wave

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SR = 48000
FPS = 24
SPF = SR // FPS
TOTAL = 1440
RNG = np.random.default_rng(1903)


def fr(frame):
    return int(round(frame * SPF))


def tc(frame):
    s = frame / FPS
    return "%d:%05.2f" % (int(s // 60), s % 60)


def decay(n, tau):
    return np.exp(-np.arange(n) / (tau * SR))


def click(level=1.0):
    n = int(0.07 * SR)
    t = np.arange(n) / SR
    x = (0.7 * RNG.standard_normal(n) * decay(n, 0.0015)
         + 0.8 * np.sin(2 * np.pi * 2300 * t) * decay(n, 0.005)
         + 0.5 * np.sin(2 * np.pi * 190 * t) * decay(n, 0.014))
    return level * 0.55 * x


def whale_click(level=1.0):
    n = int(0.9 * SR)
    t = np.arange(n) / SR
    x = np.sin(2 * np.pi * 900 * t) * decay(n, 0.004) + 0.5 * RNG.standard_normal(n) * decay(n, 0.001)
    out = np.zeros(n)
    for k, g in enumerate([1.0, 0.45, 0.25, 0.14, 0.08, 0.05]):
        d = int(k * 0.11 * SR)
        out[d:] += g * x[:n - d]
    return level * 0.5 * out


def kick(level=1.0, thin=False):
    n = int(0.24 * SR)
    t = np.arange(n) / SR
    f = 44 + 120 * np.exp(-t / 0.028)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * decay(n, 0.075)
    x[:200] += 0.4 * RNG.standard_normal(200) * decay(200, 0.0008)
    if thin:
        x = np.diff(x, prepend=0.0) * 14
        x = np.diff(x, prepend=0.0) * 6
    return level * 0.8 * x


def hat(level=1.0):
    n = int(0.03 * SR)
    x = np.diff(RNG.standard_normal(n), prepend=0.0) * decay(n, 0.006)
    return level * 0.12 * x


def buzz(frames):
    n = fr(frames)
    t = np.arange(n) / SR
    x = np.sign(np.sin(2 * np.pi * 120 * t)) * 0.5 + 0.5 * np.sin(2 * np.pi * 1000 * t)
    x[:240] *= np.linspace(0, 1, 240)
    x[-240:] *= np.linspace(1, 0, 240)
    return 0.35 * x


def riser(frames):
    n = fr(frames)
    t = np.linspace(0, 1, n)
    f = 200 * (2 ** (t * 4.5))
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.4 + 0.3 * RNG.standard_normal(n) * t
    return 0.4 * x * t ** 2


def thump(level=1.0):
    n = int(0.3 * SR)
    t = np.arange(n) / SR
    return level * 0.7 * np.sin(2 * np.pi * 52 * t) * decay(n, 0.06)


def noise_burst(seconds, level=0.5):
    n = int(seconds * SR)
    return level * RNG.standard_normal(n) * decay(n, seconds / 4)


class Mix:
    def __init__(self):
        self.l = np.zeros(fr(TOTAL))
        self.r = np.zeros(fr(TOTAL))

    def add(self, frame, x, gain=1.0, pan=0.0):
        a = fr(frame)
        if a >= len(self.l):
            return
        x = x[:len(self.l) - a]
        self.l[a:a + len(x)] += x * gain * (1 - max(0.0, pan))
        self.r[a:a + len(x)] += x * gain * (1 + min(0.0, pan))


# ---------------------------------------------------------------- scratch voices
def installed_voices():
    out = subprocess.run(["say", "-v", "?"], capture_output=True, text=True).stdout
    names = []
    for ln in out.splitlines():
        m = re.match(r"^(.*?)\s{2,}([a-z]{2}_[A-Z]{2})\s+#", ln)
        if m:
            names.append((m.group(1).strip(), m.group(2)))
    return names


def pick(voices, want):
    prefix, locale = want
    for name, loc in voices:
        if name.startswith(prefix) and loc == locale:
            return name
    for name, loc in voices:
        if name.startswith(prefix):
            return name
    return "Samantha"


def speak(voice, text, path, rate=None):
    if not os.path.exists(path):
        cmd = ["say", "-v", voice, "-o", path, "--data-format=LEI16@48000"]
        if rate:
            cmd += ["-r", str(rate)]
        subprocess.run(cmd + [text], check=True)
    with wave.open(path) as w:
        x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float64) / 32768
        if w.getnchannels() == 2:
            x = x.reshape(-1, 2).mean(axis=1)
    if not len(x) or np.abs(x).max() == 0:
        return np.zeros(1)
    # trim the silence `say` leaves at both ends, so the length is the length of the speech
    env = np.abs(x) > 0.02 * np.abs(x).max()
    idx = np.nonzero(env)[0]
    x = x[max(0, idx[0] - 200): idx[-1] + 600]
    return 0.7 * x / np.abs(x).max()


def load_final(path):
    """A chosen take of a designed voice, levelled so the lines sit together."""
    with wave.open(path) as w:
        x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float64) / 32768
    act = x[np.abs(x) > 0.02]
    rms = np.sqrt((act ** 2).mean()) if len(act) else 1.0
    x = x * (0.16 / rms)
    pk = np.abs(x).max() if len(x) else 0
    return x * (0.85 / pk) if pk > 0.85 else x


def syllables(text):
    text = re.sub(r"\[bleep\]", "", text.lower())
    n = 0
    for word in re.findall(r"[a-z']+", text):
        word = word.replace("'", "")
        groups = re.findall(r"[aeiouy]+", word)
        k = len(groups)
        if word.endswith("e") and not word.endswith(("le", "ee")) and k > 1:
            k -= 1
        n += max(1, k)
    return n


def main():
    lines = json.load(open(os.path.join(ROOT, "timing", "lines.json")))["lines"]
    cues = json.load(open(os.path.join(ROOT, "timing", "sound.json")))
    scratch = os.path.join(ROOT, "audio", "scratch")
    os.makedirs(scratch, exist_ok=True)
    os.makedirs(os.path.join(ROOT, "out"), exist_ok=True)
    voices = installed_voices()
    m = Mix()      # the bed: clicks, kick, cues
    vox = Mix()    # the scratch voices

    # ---- the grid
    for f, lvl in cues["clicks"]:
        m.add(f, click(lvl))
    for i, f in enumerate(cues["whale"]):
        m.add(f, whale_click(0.8), pan=-0.3 if i % 2 else 0.3)
    a, b = cues["bleep"]
    m.add(a, buzz(b - a))
    for a, b, mode in cues["kick"]:
        for f in range(a, b, 10):
            beat = (f % 40) // 10
            if mode == "full":
                m.add(f, kick(0.9))
                m.add(f + 5, hat(0.6))
            elif mode == "tv":
                m.add(f, kick(0.5, thin=True))
            elif mode == "half":
                if beat in (0, 2):
                    m.add(f, kick(0.6))
            elif mode == "double":
                m.add(f, kick(1.0))
                m.add(f + 5, kick(0.45))
                m.add(f + 2.5, hat(1.0))
                m.add(f + 7.5, hat(1.0))
    a, b = cues["heartbeat"]
    for f in range(a, b, 20):
        m.add(f, thump(0.9))
        m.add(f + 6, thump(0.55))
    a, b = cues["riser"]
    m.add(a, riser(b - a))
    for f in cues["impact"]:
        m.add(f, noise_burst(0.5, 0.5))
        m.add(f, thump(1.2))
    for f in cues["keys"]:
        m.add(f, click(0.4))
    for f in cues["slap"]:
        m.add(f, noise_burst(0.12, 0.6))

    # ---- the voices
    measured = {}
    rows = []
    spans = []
    designed, scratched = set(), set()
    for ln in lines:
        wants = ln.get("voices") or [ln["voice"]]
        parts = ln.get("parts") or [{"say": ln["text"], "at": ln["start"]}]
        end = ln["start"]
        for pi, part in enumerate(parts):
            if part.get("bleep"):
                continue
            longest = 0
            for vi, want in enumerate(wants):
                final = os.path.join(ROOT, "audio", "lines", "%s_%d_%d.wav" % (ln["id"], pi, vi))
                if os.path.exists(final) and "--scratch" not in sys.argv:
                    x = load_final(final)
                    designed.add(ln["id"])
                else:
                    name = pick(voices, want)
                    said = part.get("tts") or ln.get("tts") or part["say"]
                    key = hashlib.md5((name + said + str(ln.get("rate"))).encode()).hexdigest()[:8]
                    path = os.path.join(scratch, "%s_%d_%d_%s.wav" % (ln["id"], pi, vi, key))
                    x = speak(name, said, path, ln.get("rate"))
                    scratched.add(ln["id"])
                gain = ln.get("gain", 0.9) if len(wants) == 1 else 0.5
                pan = ln.get("pan", 0.0) if len(wants) == 1 else (vi - (len(wants) - 1) / 2) * 0.4
                vox.add(part["at"] + vi * 0.3, x, gain=gain * (0.75 if ln.get("soft") else 1.0), pan=pan)
                longest = max(longest, len(x))
            dur = longest / SPF
            measured["%s#%d" % (ln["id"], pi)] = round(dur, 1)
            end = max(end, part["at"] + dur)
        measured[ln["id"]] = round(end - ln["start"], 1)
        syl = syllables(ln["text"])
        slot = ln["slot_end"] - ln["start"]
        rows.append(dict(id=ln["id"], who=ln["who"], text=ln["text"], start=ln["start"], dur=end - ln["start"],
                         end=end, slot_end=ln["slot_end"], margin=ln["slot_end"] - end, syl=syl,
                         need=syl / (slot / FPS), soft=bool(ln.get("soft"))))
        spans.append((ln["id"], ln["who"], ln["start"], end))

    json.dump(measured, open(os.path.join(ROOT, "timing", "scratch_durations.json"), "w"), indent=1)

    # duck the bed under the voices so the words stay in front
    env = (np.abs(vox.l) + np.abs(vox.r)) / 2
    win = SR // 12
    cs = np.cumsum(np.concatenate([[0.0], env]))
    smooth = (cs[win:] - cs[:-win]) / win
    smooth = np.concatenate([np.full(win // 2, smooth[0]), smooth, np.full(len(env) - len(smooth) - win // 2, smooth[-1])])
    duck = 1 - 0.6 * np.clip(smooth / 0.03, 0, 1)
    left, right = m.l * duck * 0.7 + vox.l, m.r * duck * 0.7 + vox.r
    peak = max(np.abs(left).max(), np.abs(right).max())
    st = np.stack([left, right], axis=1) / peak * 0.89
    for name, a, b in (("A open", 0, 120), ("B drop", 120, 240), ("D talk", 320, 620), ("G flood", 960, 1240)):
        v = np.sqrt((vox.l[fr(a):fr(b)] ** 2).mean()); bed = np.sqrt(((m.l * duck * 0.7)[fr(a):fr(b)] ** 2).mean())
        print("level check %-8s voice rms %.3f  bed rms %.3f" % (name, v, bed), file=sys.stderr)
    with wave.open(os.path.join(ROOT, "audio", "temp_mix.wav"), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((st * 32767).astype(np.int16).tobytes())

    # ---- the report
    out = ["# Fit report: do the words fit the cut?", "",
           "Lengths are measured on the audio in the mix. Pace needed is what the slot demands, in syllables per "
           "second: comfortable speech is 4 to 5.5, and above 6 a line is rushed.", "",
           "VOICES_NOTE", "",
           "| Line | Who | Words | Starts | Scratch length | Ends | Must end by | Spare frames | Pace needed | Verdict |",
           "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    for r in rows:
        limit = 5.2 if r["soft"] else 6.2
        slot = r["slot_end"] - r["start"]
        if r["who"].startswith("DOUBT"):
            verdict = "overlaps by design"
        elif r["need"] > limit:
            verdict = "RUSHED: retime or trim"
        elif r["margin"] < -0.15 * slot:
            verdict = "needs a quick read: %.2f s at most" % (slot / FPS)
        elif r["margin"] < 0.1 * slot:
            verdict = "fits, tight"
        else:
            verdict = "fits"
        out.append("| %s | %s | %s | %s (f%d) | %d f (%.2f s) | f%d | f%d | %d | %.1f | %s |" % (
            r["id"], r["who"], r["text"], tc(r["start"]), r["start"], round(r["dur"]), r["dur"] / FPS,
            round(r["end"]), r["slot_end"], round(r["margin"]), r["need"], verdict))
    out += ["", "## Voices on top of each other", ""]
    hits = []
    for i in range(len(spans)):
        for j in range(i + 1, len(spans)):
            a, b = spans[i], spans[j]
            if a[1].startswith("DOUBT") and b[1].startswith("DOUBT"):
                continue
            ov = min(a[3], b[3]) - max(a[2], b[2])
            if ov > 1:
                hits.append("- %s (%s) and %s (%s) overlap for %d frames, from f%d." % (a[0], a[1], b[0], b[1], round(ov), max(a[2], b[2])))
    out += hits or ["None."]
    words = sum(len(re.findall(r"[A-Za-z']+", re.sub(r"\[bleep\]", "", ln["text"]))) for ln in lines)
    out += ["", "Spoken words: %d. Voiced time, summed: %.1f s of 60." % (words, sum(r["dur"] for r in rows) / FPS)]
    note = "Designed voices: %d lines. " % len(designed) if designed else "All voices are macOS scratch voices. "
    if designed and scratched:
        note += "Still on a scratch voice: %s." % ", ".join(sorted(scratched - designed))
    out[out.index("VOICES_NOTE")] = note
    open(os.path.join(ROOT, "out", "fit_report.md"), "w").write("\n".join(out) + "\n")
    print("\n".join(out))


if __name__ == "__main__":
    sys.exit(main())
