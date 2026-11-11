#!/usr/bin/env python3
"""FIRST WORD: cut generated clips into the film, with mouths on the finished voice lines.

    python3 tools/cutin.py           rewrite clips/manifest.json from timing/cutin.json, and report

timing/cutin.json names, for each shot, the clip it comes from and either a fixed in-point ("in", seconds)
or the spoken line the shot shows ("line"). For a line, the in-point is worked out from two transcriptions:
where each word falls in the clip's own sound (out/check/<clip>.words.json, written by tools/checkclip.py)
and where it falls in the finished line (timing/words.json). The clip is slid so the words that are on
screen agree, and the report gives what is left over, word by word, in frames. Two frames or less reads as
in sync; more than that is flagged.

Everything else in an entry is passed through to the conform, which explains each in its own notes: the framing
("zoom", "dx", "dy", "matte"), the ends of a shot ("fade_in", "whiteout", "blackout", "ramp", "whip"), drawings
("wash", "boil", "pile", "grow"), and "bg", "bar_from", "speed", "lift" (a dark shot's shadows opened), "bump"
(the picture lands large on an impact) and "place" (a person in the locked line-up frame moved down to stand
level with the others, the empty wall of a plate filling in above them). The close blue-hour shots carry
"matte": "lens": the model draws a round lens edge of its own on them, a different size and place each time,
so each is punched in and centred by hand (zoom, dx, dy) until that edge lies outside the one circle the
conform draws, and every such shot has the same round frame. When a performance in a clip runs at
another pace than the finished line, the picture is played up to 18 percent faster or 15 percent slower.
"""
import json
import os
import re
import statistics
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import voices as V  # noqa: E402

FPS = 24


def norm(w):
    return re.sub(r"[^a-z0-9']", "", w.lower())


def find_line(clip_words, said, after=0.0, before=1e9):
    """The clip's words that perform `said`, as (word, start) pairs, searched between two times."""
    want = [norm(w) for w in said.split() if norm(w)]
    have = [(norm(w[0]), w[1]) for w in clip_words if after <= w[1] < before and norm(w[0])]
    best = None
    for i in range(len(have)):
        k, hits = 0, []
        for j in range(i, len(have)):
            if k < len(want) and have[j][0] == want[k]:
                hits.append(have[j])
                k += 1
            if k == len(want):
                break
        if best is None or len(hits) > len(best):
            best = hits
        if len(hits) == len(want):
            return hits, True
    return best or [], False



def main():
    spec = json.load(open(V.J("timing", "cutin.json")))
    shots = {s["id"]: s for s in json.load(open(V.J("shotlist.json")))["shots"]}
    lines = {l["id"]: l for l in json.load(open(V.J("timing", "lines.json")))["lines"]}
    words = json.load(open(V.J("timing", "words.json")))
    mp = V.J("clips", "manifest.json")
    manifest = json.load(open(mp)) if os.path.exists(mp) else {}
    rows = []
    for sid, e in spec["shots"].items():
        s = shots[sid]
        entry = dict(file=e["clip"])
        note = ""
        if "line" in e:
            name = os.path.splitext(os.path.basename(e["clip"]))[0]
            cw = json.load(open(V.J("out", "check", name + ".words.json")))
            ln = lines[e["line"]]
            said = e.get("said") or re.sub(r"\[.*?\]", "", ln.get("text") or ln.get("cap") or "")
            beat = e.get("beat", [0.0, 1e9])
            got, whole = find_line(cw, said, beat[0], beat[1])
            film = [(norm(w[0]), ln["start"] + w[1]) for w in words.get(e["line"], []) if norm(w[0])]
            pairs = []
            k = 0
            for w, t in got:                      # pair each heard word with the same word in the finished line
                while k < len(film) and film[k][0] != w:
                    k += 1
                if k < len(film):
                    pairs.append((w, t, film[k][1]))
                    k += 1
            if not pairs:
                rows.append((sid, e["clip"], "LINE NOT FOUND in the clip: " + said))
                continue
            on = [p for p in pairs if s["start"] - 2 <= p[2] < s["start"] + s["dur"]] or pairs
            t_in = statistics.median(t - (f - s["start"]) / FPS for _, t, f in on) + e.get("nudge", 0) / FPS
            res = [((t - t_in) * FPS - (f - s["start"])) for _, t, f in on]
            worst, speed = max(abs(r) for r in res), 1.0
            if worst > 2 and len(on) >= 3 and e.get("fit", True):
                # the clip's performance runs at another pace: play the picture a little faster or slower
                xs = [(f - s["start"]) / FPS for _, t, f in on]
                ys = [t for _, t, f in on]
                mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
                b = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / max(1e-9, sum((x - mx) ** 2 for x in xs))
                b = min(1.18, max(0.85, b))
                a0 = my - b * mx
                res2 = [((t - a0) / b * FPS - (f - s["start"])) for _, t, f in on]
                if max(abs(r) for r in res2) < worst - 1:
                    t_in, speed, res, worst = a0, b, res2, max(abs(r) for r in res2)
                    entry["speed"] = round(b, 3)
            note = "line %s, %d of %d words on screen, worst slip %.1f frames%s%s%s" % (
                e["line"], len(on), len(pairs), worst, "" if worst <= 2 else "  <-- CHECK", "" if whole else "  (line only partly heard)",
                "" if speed == 1.0 else "  (picture played at %d percent)" % round(speed * 100))
            entry["in"] = round(max(0.0, t_in), 3)
        else:
            entry["in"] = e.get("in", 0.0)
        for k in ("zoom", "dx", "dy", "matte", "fade_in", "whiteout", "blackout", "ramp", "wash", "bg", "boil", "bar_from", "speed", "pile", "grow", "place", "lift", "whip", "bump", "lead", "tail", "black_in", "patch", "tint", "paste", "rings", "chop", "push", "tint_box", "blink", "tubes"):
            if k in e:
                entry[k] = e[k]
        if "speed" in e:
            entry["speed"] = e["speed"]
        used = s["dur"] / FPS * entry.get("speed", 1.0)
        if "beat" in e and entry["in"] + used > e["beat"][1] + 0.001:
            note += "  <-- RUNS PAST ITS BEAT by %.0f frames" % ((entry["in"] + used - e["beat"][1]) * FPS)
        if "beat" in e and entry["in"] < e["beat"][0] - 0.001:
            note += "  <-- STARTS BEFORE ITS BEAT by %.0f frames" % ((e["beat"][0] - entry["in"]) * FPS)
        manifest[sid] = entry
        rows.append((sid, e["clip"], "in %.2f s, %d frames. %s" % (entry["in"], s["dur"], note)))
    for sid in spec.get("drop", []):
        manifest.pop(sid, None)
    json.dump(manifest, open(mp, "w"), indent=1)
    for r in rows:
        print("%-4s %-28s %s" % r)
    print("%d shots in the manifest" % len(manifest))


if __name__ == "__main__":
    main()
