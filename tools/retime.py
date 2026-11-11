#!/usr/bin/env python3
"""FIRST WORD: lengthen a pause inside a finished voice line so it matches the mouth in a generated shot.

    python3 tools/retime.py          apply timing/retime.json

A generated close-up performs the line at its own pace. Where the words agree but a pause between them is
longer on screen, the finished line gets the same pause: a stretch of its own quiet is repeated inside the
gap, so no word is touched. The original is kept in audio/lines/before_retime/. The line's start and its
word times (timing/lines.json, timing/words.json) are moved to match. Run again after tools/dialogue.py
has recut the line; an entry already applied to the current file is skipped.
"""
import hashlib
import json
import os
import shutil
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import voices as V  # noqa: E402

SR, FPS = V.SR, V.FPS


def main():
    spec = json.load(open(V.J("timing", "retime.json")))
    lp = V.J("timing", "lines.json")
    data = json.load(open(lp))
    by_id = {l["id"]: l for l in data["lines"]}
    wp = V.J("timing", "words.json")
    words = json.load(open(wp))
    chosen = {r["line"]: r for r in json.load(open(V.J("audio", "scenes", "chosen.json")))}
    for lid, e in spec["lines"].items():
        path = V.J("audio", "lines", "%s_0_0.wav" % lid)
        digest = hashlib.sha1(open(path, "rb").read()).hexdigest()
        if e.get("applied_to") == digest:
            print("%s: already applied" % lid)
            continue
        scene = chosen[lid]["scene"]
        stt = json.load(open(V.J("audio", "scenes", scene, "cut_%s_0.wav.stt.json" % lid)))
        ws = [w for w in stt["words"] if w.get("type", "word") == "word"]
        k = e["after_word"]
        a, b = ws[k]["end"], ws[k + 1]["start"]
        if b - a < 0.08:
            sys.exit("%s: no pause to lengthen after word %d" % (lid, k))
        x = V.decode(path).astype(np.float32)
        add = int(round(e["add_frames"] / FPS * SR))
        # the quietest stretch of the gap, repeated at its own centre
        ga, gb = int(a * SR), int(b * SR)
        win = min(gb - ga, max(int(0.04 * SR), min(add, gb - ga)))
        best, best_at = None, ga
        for s0 in range(ga, gb - win + 1, max(1, win // 8)):
            r = float(np.sqrt(np.mean(x[s0:s0 + win] ** 2)))
            if best is None or r < best:
                best, best_at = r, s0
        quiet = x[best_at:best_at + win]
        fill = np.tile(quiet, int(np.ceil(add / len(quiet))) + 1)[:add].copy()
        cut = best_at + win // 2
        f = min(int(0.008 * SR), add // 4, cut, len(x) - cut)
        head, tail = x[:cut].copy(), x[cut:].copy()
        ramp = np.linspace(0, 1, f, dtype=np.float32)
        fill[:f] = fill[:f] * ramp + head[-f:] * (1 - ramp)
        head = head[:-f]
        fill[-f:] = fill[-f:] * (1 - ramp) + tail[:f] * ramp
        tail = tail[f:]
        y = np.concatenate([head, fill, tail])
        keep = V.J("audio", "lines", "before_retime")
        os.makedirs(keep, exist_ok=True)
        shutil.copy(path, os.path.join(keep, os.path.basename(path)))
        V.write_wav(path, y)
        ln = by_id[lid]
        ln["start"] += e.get("start_shift", 0)
        gained = (len(y) - len(x)) / SR * FPS
        words[lid] = [[w[0], round(w[1] + (gained if i > k else 0), 1)] for i, w in enumerate(words[lid])]
        e["applied_to"] = hashlib.sha1(open(path, "rb").read()).hexdigest()
        print("%s: pause after '%s' longer by %.1f frames (quiet at %.1f dB), line now starts at frame %d, %.1f frames long" % (
            lid, ws[k]["text"], gained, 20 * np.log10(best + 1e-9), ln["start"], len(y) / SR * FPS))
    json.dump(words, open(wp, "w"), indent=1)
    head = '{\n "about": %s,\n "guess_lead": %d,\n "lines": [\n' % (json.dumps(data["about"]), data["guess_lead"])
    open(lp, "w").write(head + ",\n".join("  " + json.dumps(l, ensure_ascii=False) for l in data["lines"]) + "\n ]\n}\n")
    json.dump(spec, open(V.J("timing", "retime.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
