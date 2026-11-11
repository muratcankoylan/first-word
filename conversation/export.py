#!/usr/bin/env python3
"""The conversation behind FIRST WORD, as readable Markdown, made from Claude Code's own session records.

    python3 conversation/export.py SESSION.jsonl [SESSION.jsonl ...] --out conversation/

What it keeps: every message the user typed, every reply Claude wrote for the user to read, and, between them,
one plain line for each thing Claude did (the description it gave of each command at the time, the files it
wrote, the skills it loaded, the work it handed to another agent).

What it leaves out, and why:
  - Claude's private reasoning, tool outputs and the commands themselves: not written for a reader, and tool
    outputs hold other people's web pages and documents.
  - System and harness messages, reminders, and the summaries the session wrote for itself when its context was
    compacted (a marker shows where each compaction happened).
  - Messages from other sessions that happened to share the project folder.

  - Other people's text pasted into a message (listed in `omissions.json`, each with a note in its place).

What it changes: home-directory paths become `~`, the session's temporary folders become `<scratch>`, the
account name and any email address are removed, and attached files are named by kind, not by path. The script
refuses to write if a value from the project's `.env` appears anywhere in the output.
"""
import argparse
import json
import os
import re
import sys

SKIP_USER = ("<system-reminder", "Base directory for this skill", "<task-notification", "<local-command", "<command-name", "[SYSTEM",
             "Another Claude session", "<bash-input", "<side-sessions", "<ci-monitor", "Caveat:", "<command-message")
COMPACT = ("This session is being continued", "<artifact-content-authored-by-others/>\nThe summarized", "<artifact-content-authored-by-others/> The summarized")
REMINDER = re.compile(r"<system-reminder>.*?</system-reminder>", re.S)
QUIET = {"mcp__ccd_turn__update_plan", "mcp__ccd_turn__wrap_up", "ToolSearch", "Read", "ListAgents", "mcp__ccd_session__mark_chapter"}


def scrub(s, secrets=()):
    for v in secrets:
        if v and v in s:
            sys.exit("a secret from .env appears in the conversation: refusing to write anything")
    s = re.sub(r"/Users/[^/\s\"']+/Library/Application Support/Claude/scratch-workspaces/[^\s\"'`)]*", "<scratch>", s)
    s = re.sub(r"/private/tmp/claude-\d+/[^\s\"'`)]*", "<scratch>", s)
    s = re.sub(r"/Users/[^/\s\"']+/\.claude/projects/[^\s\"'`)]*", "<session records>", s)
    s = re.sub(r"/Users/[^/\s\"']+/Downloads/[^\s\"'`)]*", "[attached file]", s)
    s = re.sub(r"/Users/[^/\s\"']+", "~", s)
    s = re.sub(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[a-z]{2,}", "[email]", s)
    return s


def user_text(content):
    """What the user typed, and how many pictures came with it. None if the entry is not a typed message."""
    images = 0
    if isinstance(content, list):
        if any(isinstance(b, dict) and b.get("type") == "tool_result" for b in content):
            return None, 0
        images = sum(1 for b in content if isinstance(b, dict) and b.get("type") == "image")
        content = "\n".join(b.get("text", "") for b in content if isinstance(b, dict) and b.get("type") == "text")
    if not isinstance(content, str):
        return None, 0
    t = re.sub(r"<artifact-view-context.*?</artifact-view-context>", "", content, flags=re.S)
    t = re.sub(r"<system-reminder>.*?</system-reminder>", "", t, flags=re.S)
    t = re.sub(r"</?pasted_content[^>]*>", "", t)
    t = re.sub(r"\[Image:[^\]]*\]", "", t)
    t = re.sub(r"<artifact-content-authored-by-others/>", "", t)
    t = t.strip()
    if not t and not images:
        return None, 0
    return t, images


def step(b):
    """One plain line for a thing Claude did, or None."""
    name, inp = b.get("name", ""), b.get("input", {}) or {}
    if name in QUIET:
        return None
    if name == "Bash":
        return inp.get("description") or "ran a command"
    if name in ("Write", "Edit"):
        return ("wrote " if name == "Write" else "edited ") + os.path.basename(inp.get("file_path", "a file"))
    if name == "Agent":
        return "handed to another agent: " + (inp.get("description") or "a task")
    if name == "Skill":
        return "loaded the skill " + str(inp.get("skill", ""))
    if name == "SendUserFile":
        return "sent: " + ", ".join(os.path.basename(f) for f in inp.get("files", []))
    if name == "Artifact":
        return "artifact: " + str(inp.get("action", "publish"))
    if name == "WebFetch" or name == "WebSearch":
        return "looked on the web"
    if "Claude_Browser" in name or "claude-in-chrome" in name:
        return "used the browser"
    if name.startswith("mcp__") and name.rsplit("__", 1)[-1] in ("update", "batch", "create", "read", "guide", "export", "query"):
        return "plan document: " + name.rsplit("__", 1)[-1]
    if name.startswith("mcp__"):
        return name.rsplit("__", 1)[-1].replace("_", " ")
    return name


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("sessions", nargs="+")
    ap.add_argument("--out", default="conversation")
    ap.add_argument("--env", default="", help="a .env file whose values must not appear in the output")
    ap.add_argument("--until", default="", help="leave out anything after this time (ISO, UTC)")
    ap.add_argument("--omit", default="", help="a JSON list of {at, keep_paragraphs, note}: a user message that carries other people's text is cut after its first paragraphs and the note says what was there")
    a = ap.parse_args()
    secrets = []
    if a.env and os.path.exists(a.env):
        for line in open(a.env):
            m = re.match(r"\s*[A-Z0-9_]+\s*=\s*(.+)", line)
            if m and len(m.group(1).strip().strip("\"'")) >= 8:
                secrets.append(m.group(1).strip().strip("\"'"))
    omit = json.load(open(a.omit)) if a.omit and os.path.exists(a.omit) else []
    entries, seen = [], set()
    for path in a.sessions:
        for line in open(path):
            try:
                o = json.loads(line)
            except ValueError:
                continue
            if o.get("isSidechain") or o.get("type") not in ("user", "assistant"):
                continue
            ts = o.get("timestamp", "")
            if a.until and ts > a.until:
                continue
            c = (o.get("message") or {}).get("content")
            if o["type"] == "user":
                raw = c if isinstance(c, str) else "\n".join(b.get("text", "") for b in c if isinstance(b, dict) and b.get("type") == "text") if isinstance(c, list) else ""
                raw = REMINDER.sub("", raw)                     # a harness note can sit in front of what the user typed
                if raw.lstrip().startswith(COMPACT):
                    key = ("compact", ts[:16])
                    if key not in seen:
                        seen.add(key)
                        entries.append((ts, "compact", None))
                    continue
                if raw.lstrip().startswith(SKIP_USER):
                    continue
                t, images = user_text(c)
                if t is None:
                    continue
                if t.startswith("[Request interrupted"):
                    t = "*(the user stopped Claude here)*"
                for o2 in omit:                                 # other people's words pasted into a message are not ours to publish
                    if ts.startswith(o2["at"]):
                        t = "\n\n".join(re.split(r"\n\s*\n", t)[:o2.get("keep_paragraphs", 1)]) + "\n\n*(" + o2["note"] + ")*"
                key = ("u", t[:200])
                if key in seen:
                    continue
                seen.add(key)
                entries.append((ts, "user", (t, images)))
            elif isinstance(c, list):
                for b in c:
                    if not isinstance(b, dict):
                        continue
                    if b.get("type") == "text" and b.get("text", "").strip():
                        key = ("a", b["text"][:200], ts[:13])
                        if key in seen:
                            continue
                        seen.add(key)
                        entries.append((ts, "text", b["text"].strip()))
                    elif b.get("type") == "tool_use":
                        s = step(b)
                        if s:
                            key = ("s", b.get("id") or (s, ts))
                            if key in seen:
                                continue
                            seen.add(key)
                            entries.append((ts, "step", s))
    entries.sort(key=lambda e: e[0])
    days = {}
    for e in entries:
        days.setdefault(e[0][:10], []).append(e)
    os.makedirs(a.out, exist_ok=True)
    total = {"user": 0, "text": 0, "step": 0}
    for day, es in sorted(days.items()):
        out = ["# The conversation, %s (times are UTC)" % day, "",
               "Made by `conversation/export.py` from the session's own records. See that file for what is kept, left out and changed.", ""]
        steps = []

        def flush():
            if steps:
                merged, last, n = [], None, 0
                for s in steps:
                    if s == last:
                        n += 1
                    else:
                        if last is not None:
                            merged.append(last + (" (x%d)" % n if n > 1 else ""))
                        last, n = s, 1
                merged.append(last + (" (x%d)" % n if n > 1 else ""))
                out.append("<details><summary>%d step%s</summary>\n" % (len(steps), "" if len(steps) == 1 else "s"))
                out.extend("- " + m for m in merged)
                out.append("\n</details>\n")
                steps.clear()
        for ts, kind, body in es:
            if kind == "step":
                steps.append(scrub(body, secrets)[:200])
                total["step"] += 1
                continue
            flush()
            if kind == "compact":
                out.append("---\n\n*Context compacted here: the session carried on from a summary it wrote for itself, the project's own state file and its saved notes.*\n\n---\n")
            elif kind == "user":
                t, images = body
                out.append("## User, %s\n" % ts[11:16])
                if images:
                    out.append("*(with %d image%s)*\n" % (images, "" if images == 1 else "s"))
                if t:
                    out.append("\n".join("> " + l for l in scrub(t, secrets).split("\n")) + "\n")
                total["user"] += 1
            else:
                out.append("**Claude:**\n\n" + scrub(body, secrets) + "\n")
                total["text"] += 1
        flush()
        path = os.path.join(a.out, day + ".md")
        open(path, "w").write("\n".join(out))
        print("wrote %s: %d lines, %.0f KB" % (path, len(out), os.path.getsize(path) / 1024.0))
    print("%d messages from the user, %d replies, %d steps" % (total["user"], total["text"], total["step"]))


if __name__ == "__main__":
    main()
