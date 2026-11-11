#!/usr/bin/env python3
"""FIRST WORD: the theme, asked of Google's Lyria.

    python3 tools/lyria.py [takes]        audio/music/LYRIA_PROMPT.md -> audio/music/lyria_theme_take<n>.mp3

Needs GEMINI_API_KEY in .env. NOT YET RUN: when this was written (11 November 2026) the key was empty. The request
follows Google's page "Generate music with Lyria 3.5" as it read that day: one POST to the Interactions endpoint
with a model and an input, and the audio comes back base64-encoded inside the response. Because the response's
exact shape could not be tried, the tool keeps the whole response beside the audio (with the audio taken out) and
finds the audio by walking it, wherever it is.

The prompt is the first fenced block of audio/music/LYRIA_PROMPT.md, so the file a person pastes into Runway and
the text this tool sends are the same text. Nothing about the director or the project is sent: only the prompt.
"""
import base64
import json
import os
import re
import subprocess
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import voices as V  # noqa: E402

URL = "https://generativelanguage.googleapis.com/v1beta/interactions"
MODEL = "lyria-3.5"


def key():
    for line in open(V.J(".env")):
        m = re.match(r"\s*GEMINI_API_KEY\s*=\s*(.*)", line)
        if m:
            return m.group(1).strip().strip("\"'")
    return ""


def prompt():
    text = open(V.J("audio", "music", "LYRIA_PROMPT.md")).read()
    return re.search(r"```text\n(.*?)```", text, re.S).group(1).strip()


def find_audio(node, found):
    """Every base64 audio block in a response, wherever it sits."""
    if isinstance(node, dict):
        data = node.get("data")
        kind = str(node.get("mime_type") or node.get("mimeType") or node.get("type") or "")
        if isinstance(data, str) and len(data) > 10000 and ("audio" in kind or not kind):
            found.append((kind, data))
            node["data"] = "<%d base64 characters, saved as audio>" % len(data)
        for v in node.values():
            find_audio(v, found)
    elif isinstance(node, list):
        for v in node:
            find_audio(v, found)


def main():
    k = key()
    if not k:
        sys.exit("GEMINI_API_KEY is empty in .env. Add it there (not in the chat) and run this again.")
    takes = int(sys.argv[1]) if len(sys.argv) > 1 else 2
    text = prompt()
    for n in range(1, takes + 1):
        out = V.J("audio", "music", "lyria_theme_take%d.mp3" % n)
        if os.path.exists(out):
            print("kept", os.path.relpath(out, V.ROOT))
            continue
        req = urllib.request.Request(URL, data=json.dumps({"model": MODEL, "input": text}).encode(), method="POST",
                                     headers={"Content-Type": "application/json", "x-goog-api-key": k})
        try:
            with urllib.request.urlopen(req, timeout=600) as r:
                res = json.loads(r.read())
        except urllib.error.HTTPError as ex:
            sys.exit("Lyria refused the request: %s %s" % (ex.code, ex.read().decode("utf-8", "replace")[:600]))
        found = []
        find_audio(res, found)
        json.dump(res, open(out.replace(".mp3", ".response.json"), "w"), indent=1)
        if not found:
            sys.exit("No audio in the response. It is saved beside where the audio would be; read it and fix find_audio().")
        raw = base64.b64decode(found[-1][1])
        ext = ".wav" if raw[:4] == b"RIFF" else ".mp3"
        path = out.replace(".mp3", ext)
        open(path, "wb").write(raw)
        print("wrote", os.path.relpath(path, V.ROOT))
        subprocess.run([sys.executable, V.J("tools", "score_build.py"), "--map", path])


if __name__ == "__main__":
    main()
