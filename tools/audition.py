#!/usr/bin/env python3
"""Writes out/voices_audition.html: the cast, every scene take and every line in the mix, to be judged by ear.
Nothing on the page was chosen by ear."""
import glob
import html
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def J(*p):
    return os.path.join(ROOT, *p)


def player(src):
    return '<audio controls preload="none" src="%s"></audio>' % html.escape(src)


LATEST = sorted(os.path.basename(p) for p in glob.glob(J("out", "animatic_v*.mp4")))[-1]      # the newest render sits at the top of the page


def main():
    cast = json.load(open(J("audio", "voices", "library_cast.json")))
    scenes = json.load(open(J("timing", "scenes.json")))["scenes"]
    chosen = json.load(open(J("audio", "scenes", "chosen.json")))
    lines = {l["id"]: l for l in json.load(open(J("timing", "lines.json")))["lines"]}
    chosen = [c for c in chosen if c["line"] in lines]
    o = ['<!doctype html><meta charset="utf-8"><title>First Word: sound</title><style>',
         'body{background:#111318;color:#e8e8e4;font:15px/1.5 -apple-system,Helvetica,sans-serif;margin:0 auto;max-width:1100px;padding:24px 16px 80px}',
         'h1{font-size:26px}h2{margin-top:44px;border-top:1px solid #333;padding-top:20px}h3{margin:26px 0 4px}',
         'table{border-collapse:collapse;width:100%}td,th{padding:6px 8px;border-bottom:1px solid #2a2d35;vertical-align:top;text-align:left}',
         'audio{height:30px;width:250px}.dim{color:#9aa0aa}.tag{color:#00e5ff;font-size:12px;letter-spacing:.04em}video{width:100%;max-width:960px}',
         '</style><h1>First Word: voices, sound and score</h1>',
         '<p class="dim">Every choice here was made by measurement, not by ear: the words came back right in a transcription and the levels sit where the meters say they should. Say what is wrong by name and it is redone.</p>',
         '<h2>%s</h2><video controls src="%s"></video>' % (LATEST.replace("_", " ").replace(".mp4", "").capitalize(), LATEST),
         '<h2>The four parts of the mix</h2><table><tr><th>Stem</th><th>Listen</th></tr>']
    for k, label in (("dialogue", "Dialogue"), ("effects", "Sound effects"), ("score", "Score, as placed and ducked"), ("whale", "Whale: real NOAA clicks in the 1+1+3 rhythm")):
        o.append("<tr><td>%s</td><td>%s</td></tr>" % (label, player("../audio/stems/%s.wav" % k)))
    o.append("</table>")
    o.append('<h2>The score</h2><p class="dim">Rebuilt on the eighth pass. Measured bar by bar, the score the film had until v010 was 33 seconds of sub bass with almost nothing above 4 kHz before its drop. The film is now cut from one theme: eight bars of arpeggio, hi-hats and choir with no kick drum, then the full drop. Three takes of the theme were made; take 1 is in the film because it measured brightest and steadiest. If another take sounds better to you, say which and it is cut in.</p><table><tr><th>What</th><th>Listen</th></tr>')
    o.append("<tr><td>The score as cut to the picture <span class='tag'>IN THE MIX</span><br><span class='dim'>60 seconds, film frame 0 at its start</span></td><td>%s</td></tr>" % player("../audio/music/score_cut2.wav"))
    for k, note in ((1, "<span class='tag'>IN THE FILM</span> brightest, 144.0 BPM, drop exactly on bar 9"), (2, "its opening is a slow build, quieter"), (3, "a half-time kick in the drop")):
        o.append("<tr><td>The theme, take %d<br><span class='dim'>%s</span></td><td>%s</td></tr>" % (k, note, player("../audio/music/cue_theme_take%d.mp3" % k)))
    for name, label in (("cue_flood_lift_take1", "An alternate drop: eight bars at full energy, with a lift"), ("cue_flood_lift_take2", "An alternate: eight bars with no kick, then four of drop"),
                        ("cue_flood_take1", "An alternate drop, take 1"), ("cue_flood_take2", "An alternate drop, take 2"),
                        ("cue_still_take2", "The pad under Casey Harrell's sentence <span class='tag'>IN THE FILM</span>"), ("cue_still_take1", "The same pad, the other take"),
                        ("cue_under_take1", "A sparse underscore for the talk (not used: the theme's opening is, turned down)"),
                        ("whale_pad_take2", "The whale's pad, first breath <span class='tag'>IN THE FILM</span>"), ("whale_pad_take1", "The whale's pad, second breath <span class='tag'>IN THE FILM</span>")):
        if os.path.exists(J("audio", "music", name + ".mp3")):
            o.append("<tr><td>%s</td><td>%s</td></tr>" % (label, player("../audio/music/%s.mp3" % name)))
    o.append("<tr><td>The score until v010, as cut<br><span class='dim'>for comparison</span></td><td>%s</td></tr>" % player("../audio/music/score_cut1.wav"))
    o.append("</table>")
    o.append('<p class="dim">To try a theme made with Google\'s Lyria, see audio/music/LYRIA_PROMPT.md.</p>')
    o.append('<h2>The effects</h2><p class="dim">Made again on the eighth pass with the newer effects model. Each row is one sound; where there are several takes the mix uses them in turn.</p><table><tr><th>Sound</th><th>Takes</th></tr>')
    for name in sorted(set(os.path.basename(f).rsplit("_", 1)[0] for f in glob.glob(J("audio", "sfx2", "*.mp3")))):
        o.append("<tr><td>%s</td><td>%s</td></tr>" % (name.replace("_", " "), " ".join(player("../" + os.path.relpath(f, ROOT)) for f in sorted(glob.glob(J("audio", "sfx2", name + "_*.mp3"))))))
    o.append("</table>")
    o.append('<h2>The cast</h2><p class="dim">Voices of real people from the ElevenLabs Voice Library, performed by the Eleven v4 model. The first player is the voice owner\'s own sample. Alternates were shortlisted for the same role and are not in the mix.</p>')
    o.append("<table><tr><th>Role</th><th>Voice</th><th>Its own sample</th><th>Alternates</th></tr>")
    for role, c in cast.items():
        alts = " ".join("<div>%s<br>%s</div>" % (html.escape(a["name"]), player(a["preview_url"])) for a in c.get("alternates", []) if a.get("preview_url"))
        o.append("<tr><td>%s</td><td><b>%s</b><br><span class='dim'>%s</span>%s</td><td>%s</td><td>%s</td></tr>" % (
            role, html.escape(c["name"]), html.escape((c.get("description") or "")[:220]), "<br><span class='tag'>STAND-IN</span>" if c.get("note") else "", player(c["preview_url"]) if c.get("preview_url") else "", alts))
    o.append("</table>")
    o.append('<h2>The scenes</h2><p class="dim">Each scene was generated three times as one conversation. The take in the mix is marked.</p>')
    for sc in scenes:
        use = next((c["take"] for c in chosen if c["scene"] == sc["id"]), None)
        o.append("<h3>%s</h3><p class='dim'>%s</p>" % (sc["id"], html.escape("  /  ".join(i["text"] for i in sc["inputs"]))))
        for p in sorted(glob.glob(J("audio", "scenes", sc["id"], "take*.mp3"))):
            k = int(os.path.basename(p)[4:-4])
            o.append("<div>take %d %s %s</div>" % (k, player("../" + os.path.relpath(p, ROOT)), '<span class="tag">IN THE MIX</span>' if k == use else ""))
    o.append('<h2>Every line as cut</h2><table><tr><th>Line</th><th>Voice</th><th>Words</th><th>Listen</th><th>Frames</th></tr>')
    for c in chosen:
        if c["line"] == "ray1":
            p = player("../audio/lines/ray1_0_0.wav") + "<br>" + player("../audio/lines/ray1_2_0.wav")
        else:
            p = player("../audio/lines/%s_0_%d.wav" % (c["line"], c["vi"]))
        o.append("<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%.0f%s</td></tr>" % (c["line"], html.escape(c["voice"][:30]), html.escape(lines[c["line"]]["text"]), p, c["frames"], " <span class='tag'>squeezed</span>" if c["squeezed"] > 1 else ""))
    o.append("</table>")
    open(J("out", "voices_audition.html"), "w").write("\n".join(o))
    print("wrote out/voices_audition.html")


if __name__ == "__main__":
    main()
