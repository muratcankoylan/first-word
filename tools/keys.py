"""Reads .env without ever printing a value. Import env() from here in every tool that calls a paid service."""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def env():
    out = {}
    for ln in open(os.path.join(ROOT, ".env"), encoding="utf-8-sig"):
        ln = ln.strip()
        if not ln or ln.startswith("#") or "=" not in ln:
            continue
        k, v = ln.split("=", 1)
        out[k.strip()] = v.strip().strip("\"'“”‘’").strip()
    return out
