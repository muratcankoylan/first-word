#!/usr/bin/env python3
"""FIRST WORD: the spoken lines, performed as scenes.

Each scene in timing/scenes.json is generated as one conversation with ElevenLabs Text to Dialogue on the
Eleven v4 model, using voices from the Voice Library (real people's licensed voices, listed in
audio/voices/library_cast.json). The scene is then cut into its lines.

    python3 tools/dialogue.py            three takes of every scene, choose, cut, write audio/lines/
    python3 tools/dialogue.py s3_question   one scene only

An input marked "context": true is performed with the scene but not cut out of it: it is there so that the line
after it is an answer and not a word said to nobody. The line it stands for keeps the take it already has.

A take is chosen by measurement: the words come back right in a transcription, and the lines overrun their
slots the least. Nothing here was chosen by ear.
"""
import base64
import json
import os
import re
import sys
from concurrent.futures import ThreadPoolExecutor

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import voices as V  # noqa: E402

SR, FPS = V.SR, V.FPS
TAKES = [(1, 0.5), (2, 0.35), (3, 0.25)]   # seed, stability: lower is freer


def plain(text):
    return re.sub(r"\[.*?\]", "", text).strip()


def generate(scene, cast, model, seed, stability):
    d = V.J("audio", "scenes", scene["id"])
    os.makedirs(d, exist_ok=True)
    base = os.path.join(d, "take%d" % seed)
    if not os.path.exists(base + ".json"):
        body = dict(inputs=[dict(text=i["text"], voice_id=cast[i["voice"]]["voice_id"]) for i in scene["inputs"]],
                    model_id=model, seed=seed, settings=dict(stability=stability))
        r = V.call("POST", "/v1/text-to-dialogue/with-timestamps", body=body, query="output_format=mp3_44100_192")
        open(base + ".mp3", "wb").write(base64.b64decode(r["audio_base64"]))
        json.dump(dict(segments=r["voice_segments"], stability=stability, seed=seed), open(base + ".json", "w"))
    meta = json.load(open(base + ".json"))
    x = V.decode(base + ".mp3")
    spans = []
    for k, inp in enumerate(scene["inputs"]):
        segs = [s for s in meta["segments"] if s["dialogue_input_index"] == k]
        a, b = int(min(s["start_time_seconds"] for s in segs) * SR), int(max(s["end_time_seconds"] for s in segs) * SR)
        sa, sb = V.speech_span(x[a:b])
        spans.append((a + sa, a + sb))
    heard = V.transcribe(base + ".mp3")["text"]
    err = V.same_words(" ".join(plain(i["text"]) for i in scene["inputs"]).replace("freaking", "bleep"), re.sub(r"(?i)\bfreaking\b", "bleep", heard))
    return dict(path=base + ".mp3", x=x, spans=spans, word_error=err, heard=heard, seed=seed, stability=stability)


def main():
    spec = json.load(open(V.J("timing", "scenes.json")))
    cast = json.load(open(V.J("audio", "voices", "library_cast.json")))
    data = json.load(open(V.J("timing", "lines.json")))
    by_id = {l["id"]: l for l in data["lines"]}
    sound = json.load(open(V.J("timing", "sound.json")))
    wp = V.J("timing", "words.json")
    words_out = json.load(open(wp)) if os.path.exists(wp) else {}
    only = sys.argv[1:]
    scenes = [s for s in spec["scenes"] if not only or s["id"] in only]

    def slot(inp):
        l = by_id[inp["line"]]
        return l["slot_end"] - l["start"]

    def run(scene):
        takes = []
        for seed, stab in TAKES:
            try:
                t = generate(scene, cast, spec["model"], seed, stab)
            except RuntimeError as ex:
                print("%s take %d FAILED %s" % (scene["id"], seed, str(ex)[:200]))
                continue
            t["over"] = sum(max(0.0, (b - a) / SR * FPS - slot(i) - 2) for (a, b), i in zip(t["spans"], scene["inputs"]) if not i.get("context"))
            takes.append(t)
        takes.sort(key=lambda t: (t["word_error"] > 0, round(t["over"]), t["stability"]))
        return scene, takes

    report = []
    with ThreadPoolExecutor(3) as ex:
        results = list(ex.map(run, scenes))
    for scene, takes in results:
        if not takes:
            continue
        best = takes[0]
        print("%-16s chose take %d (stability %.2f)  overrun %.0f frames  words %s   [others: %s]" % (
            scene["id"], best["seed"], best["stability"], best["over"], "right" if best["word_error"] == 0 else "WRONG: " + best["heard"][:80],
            ", ".join("take %d over %.0f%s" % (t["seed"], t["over"], "" if t["word_error"] == 0 else " wrong") for t in takes[1:])))
        for (a, b), inp in zip(best["spans"], scene["inputs"]):
            if inp.get("context"):          # spoken only so that the next line has something to answer; its own take is kept
                continue
            ln, vi = by_id[inp["line"]], inp.get("vi", 0)
            a2, b2 = max(0, a - int(0.05 * SR)), min(len(best["x"]), b + int(0.10 * SR))
            seg = best["x"][a2:b2].copy()
            frames = len(seg) / SR * FPS
            factor = min(1.08, frames / (slot(inp) + 1.0)) if frames > slot(inp) + 2 else 1.0
            if factor > 1.01:
                seg = V.atempo(seg, factor)
            else:
                factor = 1.0
            n = min(len(seg) // 4, int(0.04 * SR))
            seg[:240] *= np.linspace(0, 1, 240)
            seg[-n:] *= np.linspace(1, 0, n)
            tmp = V.J("audio", "scenes", scene["id"], "cut_%s_%d.wav" % (inp["line"], vi))
            V.write_wav(tmp, seg)
            if os.path.exists(tmp + ".stt.json"):
                os.remove(tmp + ".stt.json")
            wt = V.transcribe(tmp)["words"]
            if inp["line"] == "ray1" and len(wt) >= 3:
                # the second word is spoken, then covered by the relay buzz
                ca, cb = max(0.0, wt[1]["start"] - 0.02), wt[1]["end"] + 0.02
                first, last = seg[: int(ca * SR)].copy(), seg[int(cb * SR):].copy()
                m = min(480, len(first), len(last))
                first[-m:] *= np.linspace(1, 0, m)
                last[:m] *= np.linspace(0, 1, m)
                V.write_wav(V.J("audio", "lines", "ray1_0_0.wav"), first)
                V.write_wav(V.J("audio", "lines", "ray1_2_0.wav"), last)
                dur_b = max(4, int(round((cb - ca) * FPS)))
                fb = ln.get("bleep_at", 55)
                start = int(round(fb - ca * FPS))
                p = ln["parts"]
                p[0]["at"], p[1]["at"], p[1]["dur"], p[2]["at"] = start, fb, dur_b, fb + dur_b
                ln["start"] = start
                sound["bleep"] = [fb, fb + dur_b]
            else:
                V.write_wav(V.J("audio", "lines", "%s_0_%d.wav" % (inp["line"], vi)), seg)
                if vi == 0:
                    words_out[inp["line"]] = [[w["text"], round(w["start"] * FPS, 1)] for w in wt]
            report.append(dict(line=inp["line"], vi=vi, voice=cast[inp["voice"]]["name"], scene=scene["id"], take=best["seed"],
                               frames=round(len(seg) / SR * FPS, 1), slot=slot(inp), squeezed=round(factor, 2)))

    json.dump(words_out, open(wp, "w"), indent=1)
    json.dump(sound, open(V.J("timing", "sound.json"), "w"))
    head = '{\n "about": %s,\n "guess_lead": %d,\n "lines": [\n' % (json.dumps(data["about"]), data["guess_lead"])
    open(V.J("timing", "lines.json"), "w").write(head + ",\n".join("  " + json.dumps(l, ensure_ascii=False) for l in data["lines"]) + "\n ]\n}\n")
    rp = V.J("audio", "scenes", "chosen.json")
    old = [r for r in (json.load(open(rp)) if os.path.exists(rp) else []) if r["scene"] not in [s["id"] for s in scenes]]
    json.dump(old + report, open(rp, "w"), indent=1)
    long = [r for r in report if r["frames"] > r["slot"] + 2]
    print("\nlines cut: %d, squeezed (8 percent at most): %d, still longer than their slot: %d" % (len(report), sum(1 for r in report if r["squeezed"] > 1), len(long)))
    for r in long:
        print("   %-7s %-28s %.0f frames in a %d-frame slot" % (r["line"], r["voice"][:28], r["frames"], r["slot"]))


if __name__ == "__main__":
    main()
