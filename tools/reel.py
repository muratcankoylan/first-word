#!/usr/bin/env python3
"""FIRST WORD for Instagram Reels: the film re-framed for a vertical screen, shot by shot.

    python3 tools/reel.py base [SHOT ...]        the film's frames without captions, one clip a shot -> clips/reel/base/
    python3 tools/reel.py sheet OUT.jpg [SHOT ...]   one frame of every shot as it will look, on sheets, with the safe zone drawn
    python3 tools/reel.py render --out FILE [--hdr] [--audio WAV]

The reel is 1080 by 1920. The picture sits in the middle 4:5 of it (1080 by 1350, from y 285 to 1635): that is
exactly what Instagram's feed shows of a reel, it is inside what the profile grid shows (the middle 3:4), and
Instagram's own buttons sit over the bands above and below it. A 4:5 window takes 45 percent of the film's width
where a full 9:16 would take 32 and enlarge it 1.8 times; here the enlargement is 1.25.

Nothing is cropped blind. Each shot has one of these treatments (timing/reel.json; the defaults follow how the
shot was made):
  fill    a 4:5 window of the 16:9 frame, placed on the subject (x, y, z; x may be [from, to] for a move)
  tube    the same for real archive, with the television's rounded glass drawn again at the new shape
  card    type or a drawing on a plain ground: the part that matters, enlarged to the width, the ground carried on
  stack   a frame that holds two pictures side by side becomes two pictures one above the other
A shot whose words or strips were too wide for the window is first made again for it (timing/reel.json, "events"
and "clips"), still at 1920 by 1080, so that everything the conform does to a shot is still done.

Captions are not enlarged with the picture: they are taken off the frames (base) and set again on the vertical
frame by the conform's own caption code, lower-middle, clear of the app's buttons. Type that belongs to a shot
stays in the shot.

Safe zone: Meta publishes one only for Reels ads (top 14 percent, bottom 35, sides 6: on this frame y 269 to
1248, x 65 to 1015; looked up 11 November 2026). The film's own type is kept inside it. Captions sit at y 1380,
which is clear of an ordinary reel's buttons but inside the ad zone: move CAP_Y_PX up if this runs as an ad.
"""
import argparse
import json
import os
import subprocess
import sys

import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import conform as C  # noqa: E402

ROOT = C.ROOT
J = lambda *p: os.path.join(ROOT, *p)
BW, BH = 1920, 1080                 # the film's own frame
CW, CH = 1080, 1920                 # the reel
WX, WY, WW, WH = 0, 285, 1080, 1350  # the picture's window
SAFE = (65, 269, 1015, 1248)        # Meta's zone for text
CAP_Y_PX = 1380                     # the caption's baseline
CAP_K = 1.3                         # the caption's size (the 1080p film uses 1.5 on a frame 1.8 times as wide)
CAP_MAXW = 820                      # a line longer than this is set a little smaller, so it stays clear of the buttons on the right
CARD_CY = 790                       # where a card's middle sits: where faces sit in the window
BASE = J("clips", "reel", "base")
FPS = 24


def spec_file():
    p = J("timing", "reel.json")
    return json.load(open(p)) if os.path.exists(p) else {"shots": {}, "events": [], "clips": {}}


def kind(src):
    if "ARCHIVE" in src:
        return "archive"
    if src.startswith("MACRO"):
        return "macro"
    if src.startswith("INK"):
        return "ink"
    if src.startswith("CODE") and "GEN" not in src:
        return "code"
    return "gen"


def treatment(s, spec):
    t = dict(spec.get("shots", {}).get(s["id"], {}))
    if "mode" not in t:
        t["mode"] = "tube" if kind(s["source"]) == "archive" else "fill"     # type on black fills too: its type is set again to fit (timing/reel.json)
    return t


# ------------------------------------------------------------------ base: the film's frames without captions
def state(spec):
    """The conform's state for the reel: no captions, and the type that was too wide for the window set again."""
    st = C.load_state(True, "reel")
    st["all_caps"], st["caps"] = st["caps"], []
    events = []
    for e in st["events"]:
        if e["style"] in ("caption", "docked"):
            continue
        e = dict(e)
        for o in spec.get("events", []):
            if "match" not in o:
                continue
            m = o["match"]
            if all(str(e.get(k, "")).startswith(str(v)) if k in ("text", "word") else e.get(k) == v for k, v in m.items()):
                if o.get("drop"):
                    e = None
                    break
                e.update(o.get("set", {}))
        if e is not None:
            events.append(e)
    for o in spec.get("events", []):                                  # a line too long for the window is set as two: a copy of the event, changed
        if o.get("copy"):
            m = o["copy"]
            src = next(e for e in st["events"] if all(str(e.get(k, "")).startswith(str(v)) if k in ("text", "word") else e.get(k) == v for k, v in m.items()))
            events.append(dict(src, **o["set"]))
    st["events"] = events
    for sid, path in spec.get("clips", {}).items():                   # a shot made again for the window
        st["manifest"][sid] = dict(st["manifest"].get(sid, {}), file=path) if isinstance(st["manifest"].get(sid), dict) else {"file": path}
    return st


def base(shots, spec):
    C.W, C.H, C.K = BW, BH, BH / 720.0
    st = state(spec)
    os.makedirs(BASE, exist_ok=True)
    mp = os.path.join(BASE, "meta.json")
    meta = json.load(open(mp)) if os.path.exists(mp) else {}
    want = set(shots) if shots else None
    for index, s in enumerate(st["shots"]):
        need = want is None or s["id"] in want
        carry = want is not None and "I01" in want and s["id"] == "H03"      # the end card needs the baton's last frame
        if not need and not carry:
            continue
        frames, bs, bg, opts = C.load_shot(st, s)
        enc = None
        if need:
            enc = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "%dx%d" % (BW, BH), "-r", str(FPS), "-i", "-",
                                    "-vf", "scale=in_range=full:out_range=limited:out_color_matrix=bt709:flags=accurate_rnd+full_chroma_int,format=yuv444p,setparams=color_primaries=bt709:color_trc=bt709:colorspace=bt709:range=tv",
                                    "-c:v", "libx264", "-preset", "fast", "-crf", "8", os.path.join(BASE, s["id"] + ".mp4")], stdin=subprocess.PIPE)
        for k in range(s["dur"]):
            if not need and k < s["dur"] - 1:
                continue
            img = C.compose(st, s, index, k, frames, bs, bg, opts)
            if enc:
                enc.stdin.write(img.tobytes())
        if enc:
            enc.stdin.close()
            enc.wait()
            meta[s["id"]] = {"bg": list(bg), "plain": "ARCHIVE" in s["source"] or s["source"].startswith("INK")}
            print("base", s["id"], s["dur"], "frames", flush=True)
    json.dump(meta, open(mp, "w"), indent=0)


def read_base(sid, n, only=None):
    """A shot's base frames (or only some of them) as arrays."""
    path = os.path.join(BASE, sid + ".mp4")
    vf = []
    if only is not None:
        vf = ["-vf", "select='%s'" % "+".join("eq(n\\,%d)" % k for k in sorted(set(only))), "-vsync", "0"]
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path] + vf + ["-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
    a = np.frombuffer(raw, np.uint8).reshape(-1, BH, BW, 3)
    return a


# ------------------------------------------------------------------ the treatments
_tube = {}


def tube_matte(w, h):
    if (w, h) not in _tube:
        m = Image.new("L", (w * 2, h * 2), 0)
        ImageDraw.Draw(m).rounded_rectangle([8, 8, w * 2 - 9, h * 2 - 9], radius=120, fill=255)
        _tube[(w, h)] = np.asarray(m.resize((w, h), Image.LANCZOS).filter(ImageFilter.GaussianBlur(1.6)), np.float32)[..., None] / 255.0
    return _tube[(w, h)]


def at(v, t, k=0):
    """A value; or a move [from, to] over the shot (t: 0 at its first frame, 1 at its last); or keys [[frame, value], ...]
    counted from the shot's first frame, held until one frame before the next key (so a cut inside a shot stays a cut)."""
    if isinstance(v, (list, tuple)) and v and isinstance(v[0], (list, tuple)):
        cur = v[0][1]
        for i, (kf, val) in enumerate(v):
            if k >= kf:
                cur = val
        return cur
    if isinstance(v, (list, tuple)):
        u = t * t * (3 - 2 * t)
        return v[0] + (v[1] - v[0]) * u
    return v


def window(a, x, y, z, w=WW, h=WH):
    """A part of the frame with the window's shape, centred on x, y (shares of the frame), z times closer, at w by h."""
    ch = BH / float(z)
    cw = ch * w / float(h)
    if cw > BW:
        cw, ch = BW, BW * h / float(w)
    x0 = min(BW - cw, max(0.0, x * BW - cw / 2))
    y0 = min(BH - ch, max(0.0, y * BH - ch / 2))
    s = w / cw
    M = np.float32([[s, 0, -x0 * s], [0, s, -y0 * s]])
    return cv2.warpAffine(a, M, (w, h), flags=cv2.INTER_LANCZOS4 if s > 1 else cv2.INTER_AREA, borderMode=cv2.BORDER_REPLICATE)


def ground(a):
    """The plain colour a card stands on: what its edge is."""
    edge = np.concatenate([a[:6].reshape(-1, 3), a[-6:].reshape(-1, 3), a[:, :6].reshape(-1, 3), a[:, -6:].reshape(-1, 3)])
    return np.median(edge, axis=0)


def treat(a, t, u, k=0):
    """One base frame as the reel's frame. t: the shot's treatment; u: where in the shot this frame is, 0 to 1."""
    out = np.zeros((CH, CW, 3), np.uint8)
    mode = t["mode"]
    for hx0, hy0, hx1, hy1 in t.get("hide", ()):                      # small print that the window would cut in half: taken out, the ground round it carried across
        m = np.zeros((BH, BW), np.uint8)
        m[int(hy0 * BH):int(hy1 * BH), int(hx0 * BW):int(hx1 * BW)] = 255
        a = cv2.inpaint(np.ascontiguousarray(a), m, 5, cv2.INPAINT_TELEA)
    if mode in ("fill", "tube"):
        pic = window(a, at(t.get("x", 0.5), u, k), at(t.get("y", 0.5), u, k), at(t.get("z", 1.0), u, k))
        if mode == "tube":
            pic = (pic.astype(np.float32) * tube_matte(WW, WH)).astype(np.uint8)
        out[WY:WY + WH] = pic
    elif mode == "card":
        # The whole frame made smaller about the part that matters, so that nothing is cut off at the part's edge: a
        # ring that ran off the film's frame fades out where that frame ended instead of stopping on a line.
        x0, y0, x1, y1 = t.get("box", (0.0, 0.0, 1.0, 1.0))
        maxw, maxh = t.get("maxw", SAFE[2] - SAFE[0]), t.get("maxh", SAFE[3] - SAFE[1])
        s = min(maxw / ((x1 - x0) * BW), maxh / ((y1 - y0) * BH), t.get("smax", 1.6))
        g = ground(a)
        paper = g.mean() > 40
        cx, cy = CW / 2.0, t.get("cy", CARD_CY if not paper else WY + WH / 2.0)
        tx, ty = cx - s * (x0 + x1) / 2 * BW, cy - s * (y0 + y1) / 2 * BH
        pic = cv2.warpAffine(a, np.float32([[s, 0, tx], [0, s, ty]]), (CW, CH), flags=cv2.INTER_LANCZOS4 if s > 1 else cv2.INTER_AREA,
                             borderMode=cv2.BORDER_CONSTANT, borderValue=tuple(float(v) for v in g)).astype(np.float32)
        yy = np.arange(CH, dtype=np.float32)
        fy = np.clip((yy - ty) / 90.0, 0, 1) * np.clip((ty + s * BH - yy) / 90.0, 0, 1)
        xx = np.arange(CW, dtype=np.float32)
        fx = np.clip((xx - tx) / 90.0, 0, 1) * np.clip((tx + s * BW - xx) / 90.0, 0, 1)
        f = (fy[:, None] * fx[None, :])[..., None]
        pic = g[None, None, :] * (1 - f) + pic * f
        if paper:                                                     # paper is the window; the bands stay black
            out[WY:WY + WH] = np.clip(pic[WY:WY + WH], 0, 255).astype(np.uint8)
        else:
            out[:] = np.clip(pic, 0, 255).astype(np.uint8)
    elif mode == "stack":
        gut = 8
        th = (WH - gut) // 2
        for i, (x, y, z) in enumerate(t["parts"]):
            ch = BH / float(z)
            cw = ch * WW / float(th)
            xx = min(BW - cw, max(0.0, x * BW - cw / 2))
            yy = min(BH - ch, max(0.0, y * BH - ch / 2))
            s = WW / cw
            pic = cv2.warpAffine(a, np.float32([[s, 0, -xx * s], [0, s, -yy * s]]), (WW, th), flags=cv2.INTER_LANCZOS4 if s > 1 else cv2.INTER_AREA)
            if t.get("tube"):
                pic = (pic.astype(np.float32) * tube_matte(WW, th)).astype(np.uint8)
            out[WY + i * (th + gut):WY + i * (th + gut) + th] = pic
    return out


# ------------------------------------------------------------------ captions, set on the vertical frame
def line_k(c):
    """The size a caption is set at: CAP_K, or less when the whole line would be wider than CAP_MAXW."""
    serif = c.style in ("serif", "docked")
    path, px = (C.F_SERIF_I, C.SERIF_CAP_PX) if serif else (C.F_DIN, C.CAP_PX)
    toks = C.cap_reserve(c) or [t for t, _ in C.cap_segments(c, c.until - 1)]
    C.K = CAP_K
    w = sum(px * C.K * 2.2 if t.strip("“”") == "[BLOCK]" else C.width(t, path, px) for t in toks) + C.width(" ", path, px) * (len(toks) - 1)
    if c.style == "docked":
        w += C.width("THE FUTURE IS", C.F_DIN, C.CAP_PX) + C.width(" ", path, px)
    return CAP_K * min(1.0, CAP_MAXW / max(1.0, w))


def captions(img, st, f, bg):
    """The line being spoken, drawn by the conform's own code at the reel's size and place."""
    keep = (C.W, C.H, C.K, C.CAP_Y)
    C.W, C.H, C.K, C.CAP_Y = CW, CH, CAP_K, CAP_Y_PX / float(CH)
    try:
        d = ImageDraw.Draw(img, "RGBA")
        if 40 <= f < 42:                                              # the one caption that is a type event
            C.draw_cap_line(img, d, [("“already decided.”", "w")], "docked", bg, cursor=False, prefix="THE FUTURE IS")
        else:
            for c in st["all_caps"]:
                if c.show_from <= f < c.until:
                    C.K = line_k(c)
                    C.draw_cap_line(img, d, C.cap_segments(c, f), c.style, bg, cursor=f <= c.end + 2,
                                    prefix="THE FUTURE IS" if c.style == "docked" else None, reserve=C.cap_reserve(c))
                    break
        C.flush_lights(img, f)
    finally:
        C.W, C.H, C.K, C.CAP_Y = keep
    return img


def frames_of(st, spec, shots=None, pick=None):
    """Every frame of the reel (or pick(s) -> the frames of a shot to make), with its shot."""
    meta = json.load(open(os.path.join(BASE, "meta.json")))
    for s in st["shots"]:
        if shots and s["id"] not in shots:
            continue
        ks = list(range(s["dur"])) if pick is None else pick(s)
        a = read_base(s["id"], s["dur"], None if pick is None else ks)
        t = treatment(s, spec)
        for i, k in enumerate(sorted(set(ks))):
            u = k / float(max(1, s["dur"] - 1))
            img = Image.fromarray(treat(a[i], t, u, k))
            img = captions(img, st, s["start"] + k, tuple(meta[s["id"]]["bg"]))
            yield s, s["start"] + k, img, meta[s["id"]]["plain"]


def sheet(out, shots, spec):
    st = state(spec)
    tiles = []
    for s, f, img, _ in frames_of(st, spec, shots, pick=lambda s: [(s["dur"] * 2) // 3]):
        d = ImageDraw.Draw(img)
        d.rectangle([SAFE[0], SAFE[1], SAFE[2], SAFE[3]], outline=(255, 210, 0), width=3)        # Meta's zone for text
        d.line([0, 1536, CW, 1536], fill=(255, 80, 80), width=3)                                 # about where an ordinary reel's own caption starts
        t = img.resize((270, 480), Image.LANCZOS)
        ImageDraw.Draw(t).rectangle([0, 0, 110, 14], fill=(0, 0, 0))
        ImageDraw.Draw(t).text((3, 1), "%s f%d %s" % (s["id"], f, treatment(s, spec)["mode"]), fill=(255, 255, 0))
        tiles.append(t)
    cols = 9
    per = cols * 3
    base, ext = os.path.splitext(out)
    for p in range(0, len(tiles), per):
        chunk = tiles[p:p + per]
        sh = Image.new("RGB", (cols * 274, ((len(chunk) + cols - 1) // cols) * 484), (40, 40, 40))
        for i, t in enumerate(chunk):
            sh.paste(t, ((i % cols) * 274 + 2, (i // cols) * 484 + 2))
        path = "%s_%d%s" % (base, p // per + 1, ext) if len(tiles) > per else out
        sh.save(path, quality=88)
        print("wrote", path, sh.size)


def render(out, audio, spec, hdr=False):
    st = state(spec)
    cmd = ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb48le" if hdr else "rgb24", "-s", "%dx%d" % (CW, CH), "-r", str(FPS), "-i", "-"]
    if audio:
        cmd += ["-i", audio, "-c:a", "aac", "-b:a", "256k"]
    if hdr:
        import hdr as Hd
        cmd += ["-vf", "scale=in_range=full:out_range=limited:out_color_matrix=bt2020:flags=accurate_rnd+full_chroma_int,format=yuv420p10le",
                "-c:v", "libx265", "-preset", "medium", "-crf", "15", "-tag:v", "hvc1",
                "-x265-params", "colorprim=bt2020:transfer=arib-std-b67:colormatrix=bt2020nc:range=limited:log-level=error",
                "-color_primaries", "bt2020", "-color_trc", "arib-std-b67", "-colorspace", "bt2020nc", "-color_range", "tv"]
    else:
        cmd += ["-vf", "scale=in_range=full:out_range=limited:out_color_matrix=bt709:flags=accurate_rnd+full_chroma_int,format=yuv420p,setparams=color_primaries=bt709:color_trc=bt709:colorspace=bt709:range=tv",
                "-c:v", "libx264", "-preset", "slow", "-crf", "15", "-profile:v", "high",
                "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709", "-color_range", "tv"]
    cmd += ["-r", str(FPS), "-t", "%.6f" % (st["total"] / float(FPS)), "-movflags", "+faststart", out]
    enc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    n, ease, last, peak = 0, 1.0, None, 0.0
    for s, f, img, plain in frames_of(st, spec):
        if hdr:
            arr = np.asarray(img).astype(np.float32)
            key = np.zeros((CH, CW), np.float32) if plain else Hd.light_key(arr, 1.875)
            scale = max(Hd.FLOOR, min(1.0, (Hd.AREA / max(float(key.mean()), 1e-6)) ** 0.5))
            ease = scale if s["id"] != last else 0.5 * ease + 0.5 * scale
            last = s["id"]
            o, nits = Hd.to_hlg(arr, key, 1.0 + (Hd.PEAK - 1.0) * ease)
            peak = max(peak, float(nits.max()))
            enc.stdin.write(o.tobytes())
        else:
            enc.stdin.write(img.tobytes())
        n += 1
    enc.stdin.close()
    if enc.wait() != 0:
        sys.exit("ffmpeg failed")
    print("wrote %s: %d frames%s" % (out, n, (", brightest pixel %.0f nits" % peak) if hdr else ""))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["base", "sheet", "render"])
    ap.add_argument("args", nargs="*")
    ap.add_argument("--out", default=J("out", "first_word_reel.mp4"))
    ap.add_argument("--audio", default=J("audio", "mix_v015.wav"))
    ap.add_argument("--hdr", action="store_true")
    a = ap.parse_args()
    spec = spec_file()
    if a.cmd == "base":
        base(a.args, spec)
    elif a.cmd == "sheet":
        sheet(a.args[0], a.args[1:], spec)
    else:
        render(a.out, a.audio, spec, a.hdr)


if __name__ == "__main__":
    main()
