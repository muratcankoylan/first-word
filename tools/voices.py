#!/usr/bin/env python3
"""FIRST WORD: the designed voices and every spoken line.

    python3 tools/voices.py design     three previews per voice, from the descriptions in timing/voices.json
    python3 tools/voices.py pick       measure the previews and choose one per voice
    python3 tools/voices.py create     save the chosen previews as voices in the ElevenLabs account
    python3 tools/voices.py lines      generate every line, hold it to its slot, check the words by transcription

Nothing here can be heard by the tool that wrote it. Previews and takes are chosen by measurement: the words
come back right in a transcription, the pitch and pace sit where the character should, and the line fits its
slot. out/voices_audition.html lets a person listen and overrule.
"""
import base64
import csv
import datetime
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
import uuid
import wave
from concurrent.futures import ThreadPoolExecutor

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from keys import env  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
API = "https://api.elevenlabs.io"
SR, FPS = 48000, 24
TAKES = 3


def J(*p):
    return os.path.join(ROOT, *p)


def key():
    return env()["ELEVENLABS_API_KEY"]


def call(method, path, body=None, raw=False, query="", tries=4):
    url = API + path + (("?" + query) if query else "")
    data = json.dumps(body).encode() if body is not None else None
    headers = {"xi-api-key": key()}
    if data:
        headers["Content-Type"] = "application/json"
    for attempt in range(tries):
        try:
            r = urllib.request.urlopen(urllib.request.Request(url, data=data, headers=headers, method=method), timeout=180)
            blob = r.read()
            return blob if raw else json.loads(blob.decode())
        except urllib.error.HTTPError as ex:
            msg = ex.read().decode(errors="replace")[:500]
            if ex.code in (409, 429, 500, 502, 503) and attempt < tries - 1:
                time.sleep(3 * (attempt + 1))
                continue
            raise RuntimeError("%s %s -> %d %s" % (method, path, ex.code, msg))
        except urllib.error.URLError as ex:
            if attempt < tries - 1:
                time.sleep(3)
                continue
            raise RuntimeError("%s %s -> %r" % (method, path, ex))


def transcribe(path):
    """Words with start and end times, from ElevenLabs Scribe."""
    cache = path + ".stt.json"
    if os.path.exists(cache):
        return json.load(open(cache))
    blob = open(path, "rb").read()
    out = None
    for model in ("scribe_v2", "scribe_v1"):
        b = "----fw" + uuid.uuid4().hex
        parts = []
        for k, v in (("model_id", model), ("language_code", "en"), ("tag_audio_events", "false"), ("timestamps_granularity", "word")):
            parts.append(("--%s\r\nContent-Disposition: form-data; name=\"%s\"\r\n\r\n%s\r\n" % (b, k, v)).encode())
        parts.append(("--%s\r\nContent-Disposition: form-data; name=\"file\"; filename=\"a%s\"\r\nContent-Type: application/octet-stream\r\n\r\n" % (b, os.path.splitext(path)[1])).encode())
        body = b"".join(parts) + blob + ("\r\n--%s--\r\n" % b).encode()
        req = urllib.request.Request(API + "/v1/speech-to-text", data=body, method="POST",
                                     headers={"xi-api-key": key(), "Content-Type": "multipart/form-data; boundary=" + b})
        try:
            out = json.loads(urllib.request.urlopen(req, timeout=180).read().decode())
            break
        except urllib.error.HTTPError as ex:
            err = ex.read().decode(errors="replace")[:300]
            if model == "scribe_v1":
                raise RuntimeError("speech-to-text -> %d %s" % (ex.code, err))
    res = dict(text=out.get("text", ""), words=[dict(text=w["text"], start=w["start"], end=w["end"]) for w in out.get("words", []) if w.get("type") == "word"])
    json.dump(res, open(cache, "w"))
    return res


# ---------------------------------------------------------------- measuring
def decode(path):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-ac", "1", "-ar", str(SR), "-f", "s16le", "-"], capture_output=True).stdout
    return np.frombuffer(raw, dtype=np.int16).astype(np.float64) / 32768


def speech_span(x):
    """First and last sample of speech, by energy."""
    if not len(x) or np.abs(x).max() == 0:
        return 0, 0
    win = SR // 100
    n = len(x) // win
    e = np.sqrt((x[:n * win].reshape(n, win) ** 2).mean(axis=1))
    on = np.nonzero(e > max(0.004, 0.06 * e.max()))[0]
    if not len(on):
        return 0, len(x)
    return max(0, on[0] * win - win), min(len(x), (on[-1] + 1) * win + 4 * win)


def f0_median(x):
    win, hop = int(0.04 * SR), SR // 100
    lo, hi = SR // 450, SR // 65
    n = 1 << (2 * win - 1).bit_length()
    han = np.hanning(win)
    f0 = []
    for i in range(0, len(x) - win, hop):
        seg = x[i:i + win]
        if np.sqrt((seg ** 2).mean()) < 0.02:
            continue
        sp = np.fft.rfft((seg - seg.mean()) * han, n)
        ac = np.fft.irfft(sp * np.conj(sp))[:win]
        ac = ac / (ac[0] + 1e-12)
        k = lo + int(np.argmax(ac[lo:hi]))
        if ac[k] > 0.5:
            f0.append(SR / k)
    return float(np.median(f0)) if f0 else 0.0


def syllables(text):
    n = 0
    for word in re.findall(r"[a-z']+", re.sub(r"\[.*?\]", "", text.lower())):
        word = word.replace("'", "")
        k = len(re.findall(r"[aeiouy]+", word))
        if word.endswith("e") and not word.endswith(("le", "ee")) and k > 1:
            k -= 1
        n += max(1, k)
    return n


def norm(text):
    t = re.sub(r"\[.*?\]", " ", text.lower()).replace("mister", "mr").replace("okay", "ok").replace("o.k.", "ok")
    t = re.sub(r"\bf[\*u][\*c][\*k]\w*", "bleep", t)
    return re.findall(r"[a-z0-9]+", t.replace("'", "").replace("’", ""))


def wer(ref, hyp):
    r, h = norm(ref), norm(hyp)
    d = list(range(len(h) + 1))
    for i in range(1, len(r) + 1):
        prev, d[0] = d[0], i
        for j in range(1, len(h) + 1):
            cur = min(d[j] + 1, d[j - 1] + 1, prev + (r[i - 1] != h[j - 1]))
            prev, d[j] = d[j], cur
    return d[len(h)] / max(1, len(r))


def write_wav(path, x):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((np.clip(x, -1, 1) * 32767).astype(np.int16).tobytes())


def credits():
    s = call("GET", "/v1/user/subscription")
    return s["character_count"], s["character_limit"]


def ledger(model, what, units, output, ok=True):
    with open(J("ledger.csv"), "a", newline="") as f:
        csv.writer(f).writerow([datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"), "elevenlabs", model, what, "", units, "plan credit", 0, output, "yes" if ok else "no"])


def load_voices():
    return json.load(open(J("timing", "voices.json")))


# ---------------------------------------------------------------- design
def design():
    v = load_voices()
    before, limit = credits()

    def one(k):
        spec = v["voices"][k]
        d = J("audio", "voices", k)
        os.makedirs(d, exist_ok=True)
        meta = os.path.join(d, "design.json")
        if os.path.exists(meta):
            return k, "kept"
        try:
            out = call("POST", "/v1/text-to-voice/design", query="output_format=mp3_44100_192",
                       body=dict(voice_description=spec["description"], model_id=v["design_model"], text=spec["text"], guidance_scale=4, seed=1903))
        except RuntimeError as ex:
            return k, "FAILED: %s" % str(ex)[:260]
        pre = []
        for i, p in enumerate(out["previews"]):
            fn = "p%d.mp3" % (i + 1)
            open(os.path.join(d, fn), "wb").write(base64.b64decode(p["audio_base_64"]))
            pre.append(dict(file=fn, generated_voice_id=p["generated_voice_id"], seconds=p.get("duration_secs")))
        json.dump(dict(text=out.get("text"), previews=pre, made=datetime.date.today().isoformat()), open(meta, "w"), indent=1)
        return k, "%d previews" % len(pre)

    with ThreadPoolExecutor(3) as ex:
        for k, res in ex.map(one, [k for k in v["voices"] if not v["voices"][k].get("skip")]):
            print("%-6s %s" % (k, res))
    after, _ = credits()
    ledger(v["design_model"], "voice design previews for %d voices" % len(v["voices"]), after - before, "audio/voices/")
    print("credits used: %d (now %d of %d)" % (after - before, after, limit))


# ---------------------------------------------------------------- pick
def measure_preview(path, spec):
    x = decode(path)
    a, b = speech_span(x)
    x = x[a:b]
    stt = transcribe(path)
    words = stt["words"]
    talk = sum(w["end"] - w["start"] for w in words) or (len(x) / SR)
    span = (words[-1]["end"] - words[0]["start"]) if words else len(x) / SR
    f0 = f0_median(x)
    lo, hi = spec["f0"]
    off = 0.0 if lo <= f0 <= hi else 12 * abs(np.log2(f0 / (lo if f0 < lo else hi))) if f0 > 0 else 12.0
    pace = syllables(spec["text"]) / max(0.1, span)
    err = wer(spec["text"], stt["text"])
    noise = float(np.sqrt((np.sort(np.abs(x))[: len(x) // 10] ** 2).mean())) if len(x) else 0
    score = 10 * (1 - err) - off - 0.6 * abs(pace - spec["pace"]) - 200 * noise
    return dict(f0=round(f0), pitch_off_semitones=round(off, 1), pace=round(pace, 2), word_error=round(err, 3),
                seconds=round(len(x) / SR, 2), score=round(score, 2), heard=stt["text"])


def pick():
    v = load_voices()
    cast_path = J("audio", "voices", "cast.json")
    cast = json.load(open(cast_path)) if os.path.exists(cast_path) else {}
    rows = []
    for k, spec in v["voices"].items():
        if spec.get("skip"):
            continue
        d = J("audio", "voices", k)
        meta = json.load(open(os.path.join(d, "design.json")))
        best = None
        for p in meta["previews"]:
            p["measure"] = measure_preview(os.path.join(d, p["file"]), spec)
            if best is None or p["measure"]["score"] > best["measure"]["score"]:
                best = p
        json.dump(meta, open(os.path.join(d, "design.json"), "w"), indent=1)
        cur = cast.get(k, {})
        if not cur.get("voice_id"):  # once a voice is saved, the pick is fixed
            cast[k] = dict(pick=best["file"], generated_voice_id=best["generated_voice_id"], measure=best["measure"])
        for p in meta["previews"]:
            m = p["measure"]
            rows.append((k, p["file"], "PICK" if p["file"] == cast[k]["pick"] else "", m["f0"], "%d-%d" % tuple(spec["f0"]), m["pace"], spec["pace"], m["word_error"], m["score"]))
    json.dump(cast, open(cast_path, "w"), indent=1)
    print("%-6s %-7s %-5s %5s %-9s %5s %5s %6s %6s" % ("voice", "preview", "", "f0", "wanted", "pace", "want", "w.err", "score"))
    for r in rows:
        print("%-6s %-7s %-5s %5d %-9s %5.2f %5.1f %6.3f %6.2f" % r)


# ---------------------------------------------------------------- create
def create():
    v = load_voices()
    cast_path = J("audio", "voices", "cast.json")
    cast = json.load(open(cast_path))
    for k, spec in v["voices"].items():
        if spec.get("skip"):
            continue
        c = cast[k]
        if c.get("voice_id"):
            print("%-6s kept %s" % (k, c["voice_id"][:6] + "..."))
            continue
        out = call("POST", "/v1/text-to-voice", body=dict(voice_name=spec["name"], voice_description=spec["description"][:990], generated_voice_id=c["generated_voice_id"]))
        c["voice_id"] = out["voice_id"]
        json.dump(cast, open(cast_path, "w"), indent=1)
        print("%-6s saved" % k)
    s = call("GET", "/v1/user/subscription")
    print("voice slots: %d of %d" % (s["voice_slots_used"], s["voice_limit"]))


# ---------------------------------------------------------------- lines
QUICK = "[quickly]"   # the v4 model ignores the speed setting; it does follow this tag (33 frames became 25 in a test)
NUMS = {"sixty-nine": "69", "sixty nine": "69", "one million": "1 million", "ten million": "10 million", "two days": "2 days"}


def speak(voice_id, text, model, seed, out_path):
    if os.path.exists(out_path):
        return
    blob = call("POST", "/v1/text-to-speech/" + voice_id, raw=True, query="output_format=mp3_44100_192",
                body=dict(text=text, model_id=model, seed=seed))
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    open(out_path, "wb").write(blob)


def same_words(said, heard):
    a, b = said.lower(), heard.lower()
    for k, v in NUMS.items():
        a, b = a.replace(k, v), b.replace(k, v)
    return wer(a, b)


def take_info(path, said):
    x = decode(path)
    a, b = speech_span(x)
    stt = transcribe(path)
    w = stt["words"]
    if w:  # keep the speech, drop the breath before it and the room after it
        a = max(a, int((w[0]["start"] - 0.08) * SR), 0)
        b = max(a + 1, min(b, int((w[-1]["end"] + 0.22) * SR)))
    return dict(path=path, a=a, b=b, frames=(b - a) / SR * FPS, word_error=same_words(said, stt["text"]), heard=stt["text"], words=w)


def atempo(x, factor):
    """Pitch-preserving speed-up, used sparingly (15 percent at most)."""
    tmp = J("audio", "takes", "_tmp_%s.wav" % uuid.uuid4().hex)
    write_wav(tmp, x)
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", tmp, "-filter:a", "atempo=%.4f" % factor, "-ac", "1", "-ar", str(SR), "-f", "s16le", "-"], capture_output=True).stdout
    os.remove(tmp)
    return np.frombuffer(raw, dtype=np.int16).astype(np.float64) / 32768


def lines():
    v = load_voices()
    cast = json.load(open(J("audio", "voices", "cast.json")))
    data = json.load(open(J("timing", "lines.json")))
    model = v["speech_model"]
    before, limit = credits()
    jobs = []
    for ln in data["lines"]:
        who = v["cast"][ln["who"]]
        keys = who if isinstance(who, list) else [who]
        d = v["direction"].get(ln["id"], {})
        said = d.get("say") or ln["text"]
        for vi, k in enumerate(keys):
            if not v["voices"][k].get("skip"):
                jobs.append((ln, vi, k, said, d.get("tag", "")))

    def run(job):
        ln, vi, k, said, tag = job
        slot = ln["slot_end"] - ln["start"]
        best, tried, log, went_quick = None, 0, [], False
        plans = [(s, tag if s % 2 else "", "_t" if (tag and s % 2) else "") for s in range(1, TAKES + 1)]
        while plans:
            seed, tg, suffix = plans.pop(0)
            name = "%s_v%d_s%d_x100%s.mp3" % (ln["id"], vi, seed, suffix)
            path = J("audio", "takes", ln["id"], name)
            try:
                speak(cast[k]["voice_id"], (tg + " " + said).strip(), model, seed, path)
                info = take_info(path, said)
            except RuntimeError as ex:
                log.append("%s FAILED %s" % (name, str(ex)[:160]))
                continue
            tried += 1
            info.update(seed=seed, tag=tg, fits=info["frames"] <= slot + 2)
            log.append("s%d%s %.0f/%d%s" % (seed, suffix, info["frames"], slot, "" if info["word_error"] == 0 else " WRONG"))
            # right words first, then fitting the slot, then the take that uses the slot without rushing it
            rank = (info["word_error"] > 0, not info["fits"], abs(info["frames"] - 0.9 * slot))
            if best is None or rank < best[0]:
                best = (rank, info)
            if plans or best is None or tried >= 8:
                continue
            if best[0][0]:
                plans = [(30 + tried, "", ""), (40 + tried, "", "")]            # wrong words: plain takes again
            elif best[0][1] and not went_quick and not tag:
                went_quick = True                                                # right words, too long: ask for it quicker
                plans = [(51, QUICK, "_q"), (52, QUICK, "_q"), (53, QUICK, "_q")]
        return job, (best[1] if best else None), log

    results = []
    with ThreadPoolExecutor(4) as ex:
        for job, info, log in ex.map(run, jobs):
            results.append((job, info, log))
            print("%-7s %-5s %s" % (job[0]["id"], job[2], "  ".join(log)[:200]))

    words_out, report = {}, []
    by_id = {l["id"]: l for l in data["lines"]}
    sound = json.load(open(J("timing", "sound.json")))
    for job, info, log in results:
        ln, vi, k, said, tag = job
        slot = ln["slot_end"] - ln["start"]
        if info is None:
            report.append(dict(line=ln["id"], voice=k, take="NO TAKE", frames=0, slot=slot, squeezed=1.0, word_error=1.0, heard=""))
            continue
        x = decode(info["path"])
        t0 = info["a"] / SR
        seg = x[info["a"]:info["b"]].copy()
        factor = min(1.15, info["frames"] / (slot + 1.0)) if info["frames"] > slot + 1 else 1.0
        if factor > 1.01:
            seg = atempo(seg, factor)
        else:
            factor = 1.0
        n = min(len(seg) // 4, int(0.03 * SR))
        if n:
            seg[:240] *= np.linspace(0, 1, 240)
            seg[-n:] *= np.linspace(1, 0, n)
        wt = [(w["text"], (w["start"] - t0) / factor, (w["end"] - t0) / factor) for w in info["words"]]
        if ln["id"] == "ray1" and len(wt) >= 3:
            # the second word is spoken, then covered: cut the take either side of it and time the bleep to it
            a, b = max(0.0, wt[1][1] - 0.02), wt[1][2] + 0.02
            first, last = seg[: int(a * SR)].copy(), seg[int(b * SR):].copy()
            m = min(480, len(first), len(last))
            first[-m:] *= np.linspace(1, 0, m)
            last[:m] *= np.linspace(0, 1, m)
            write_wav(J("audio", "lines", "ray1_0_0.wav"), first)
            write_wav(J("audio", "lines", "ray1_2_0.wav"), last)
            f_bleep = 55
            dur_b = max(4, int(round((b - a) * FPS)))
            start = int(round(f_bleep - a * FPS))
            p = by_id["ray1"]["parts"]
            p[0]["at"], p[1]["at"], p[1]["dur"], p[2]["at"] = start, f_bleep, dur_b, f_bleep + dur_b
            by_id["ray1"]["start"] = start
            sound["bleep"] = [f_bleep, f_bleep + dur_b]
        else:
            write_wav(J("audio", "lines", "%s_0_%d.wav" % (ln["id"], vi)), seg)
            if vi == 0:
                words_out[ln["id"]] = [[t, round(a * FPS, 1)] for t, a, b in wt]
        report.append(dict(line=ln["id"], voice=k, take=os.path.basename(info["path"]), frames=round(len(seg) / SR * FPS, 1), slot=slot,
                           squeezed=round(factor, 2), word_error=info["word_error"], heard=info["heard"]))

    json.dump(words_out, open(J("timing", "words.json"), "w"), indent=1)
    json.dump(sound, open(J("timing", "sound.json"), "w"))
    head = '{\n "about": %s,\n "guess_lead": %d,\n "lines": [\n' % (json.dumps(data["about"]), data["guess_lead"])
    open(J("timing", "lines.json"), "w").write(head + ",\n".join("  " + json.dumps(l, ensure_ascii=False) for l in data["lines"]) + "\n ]\n}\n")
    json.dump(report, open(J("audio", "takes", "chosen.json"), "w"), indent=1)
    after, _ = credits()
    if after > before:
        ledger(model, "spoken lines, takes and transcription checks", after - before, "audio/lines/")
    bad = [r for r in report if r["word_error"] > 0]
    long = [r for r in report if r["frames"] > r["slot"] + 2]
    print("\ncredits used: %d (now %d of %d)" % (after - before, after, limit))
    print("quick takes chosen: %d, squeezed in time: %d" % (sum(1 for r in report if "_q" in r["take"]), sum(1 for r in report if r["squeezed"] > 1)))
    print("lines whose words did not come back exactly: %d" % len(bad))
    for r in bad:
        print("   %-7s %-5s heard: %s" % (r["line"], r["voice"], r["heard"]))
    print("lines still longer than their slot: %d" % len(long))
    for r in long:
        print("   %-7s %-5s %.0f frames in a %d-frame slot (take %s, squeezed x%.2f)" % (r["line"], r["voice"], r["frames"], r["slot"], r["take"], r["squeezed"]))


if __name__ == "__main__":
    {"design": design, "pick": pick, "create": create, "lines": lines}[sys.argv[1]]()
