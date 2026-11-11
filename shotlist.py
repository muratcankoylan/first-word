"""FIRST WORD: frame-accurate shot list.

Source of truth for the cut. 24 fps, 144 BPM: 1 beat = 10 frames, 1 bar = 40 frames,
36 bars = 1,440 frames = 60 s. Run this file to validate the frame maths and to write
shotlist.json and shotlist.md next to it.

Source codes: GEN = generated video, MACRO = a generated macro insert or still (nothing is filmed),
ARCHIVE = real public-domain footage or document (always takes the scanline pass),
CODE = rendered from code (type, 3D, shaders), INK = hand-drawn 2D animation.

This file fixes the picture. Exact start frames of every spoken line are in timing/lines.json, on-screen
type in timing/type.json, sound cues in timing/sound.json.
"""
import json
import os
import statistics

FPS = 24
BEAT = 10
BAR = 40
TOTAL = 1440

PASSAGES = [
    # key, name, start frame, end frame (exclusive), lead dials, kick
    ("A", "Cold open", 0, 120, "Defiance, Velocity", "none: clicks and voices only"),
    ("B", "The wind", 120, 240, "Defiance, Physicality", "in"),
    ("C", "A million years", 240, 320, "Defiance, Velocity", "in, through a TV speaker"),
    ("D0", "The question", 320, 440, "Defiance, Physicality", "half: bass and clicks"),
    ("D1", "The bronze", 440, 500, "Physicality, Wonder", "half"),
    ("D2", "The email", 500, 620, "Defiance, Physicality", "half"),
    ("D3", "The voice", 620, 750, "Wonder, Physicality", "out from 0:26.7"),
    ("E", "The turn", 750, 880, "Defiance, Wonder", "out: pulse and breath"),
    ("F", "The kitchen table", 880, 960, "Physicality, Wonder", "out: room tone"),
    ("G", "The flood", 960, 1260, "Velocity, Euphoria", "in, double time"),
    ("H", "The whale", 1260, 1380, "Wonder, Euphoria", "out: choir and clicks"),
    ("I", "The mark", 1380, 1440, "Wonder, Defiance", "out: five clicks, silence"),
]

S = []  # shots


def shot(sid, passage, start, dur, source, picture, line="", sound="", transition="cut"):
    S.append(dict(id=sid, passage=passage, start=start, dur=dur, source=source,
                  picture=picture, line=line, sound=sound, transition=transition))


# ---------------------------------------------------------------- A. COLD OPEN
shot("A01", "A", 0, 40, "CODE",
     "Black. White type left of centre: The future is, then the cursor, a small tube of cyan light. Every click sends a ring out from it. Doubts type on after the cursor in serif italic inside quotation marks and stack into a list, one per click.",
     "FOUR DESIGNED VOICES, overlapping, each finishing the sentence: \"not for "
     "people like me.\" \"coming for my job.\" \"all hype.\" \"already decided.\"",
     "Relay clicks on frames 0, 10, 20, 25, 30: the 1+1+3 motif. Room tone. No music.",
     "loop point: this frame follows the last frame")
people = [
    ("A02", "Ray, 50s, arms crossed, head bowed. First ink mouths appear on the wall."),
    ("A03", "Amara, a nurse, scrubs under the jacket, head bowed."),
    ("A04", "Dev, a farmer, soil on his cuffs, head bowed."),
    ("A05", "Jun, 19, headphones round the neck, jacket too big, head bowed."),
    ("A06", "Osei, 60s, glasses pushed up into grey hair, head bowed."),
    ("A07", "Pip, 9. The frame was set for adults, so only the top of her hair shows."),
    ("A08", "Rosa, late 60s, apron under the jacket, flour on one sleeve, head bowed."),
    ("A09", "Mara, 40s, a solder burn on one knuckle, head bowed."),
]
for i, (sid, pic) in enumerate(people):
    shot(sid, "A", 40 + 5 * i, 5, "GEN + INK",
         "Line-up frame, locked. " + pic + (" The ink layer grows across all eight swaps." if i == 0 else ""),
         "RAY (voice only, from frame 47) gives the fifth completion: \"Just [bleep] autocomplete.\" The bleep is on frames 55 to 59, and a block of lit cells lands on one drawn mouth, white-hot, and keeps changing. Caption docks at the bottom: THE FUTURE IS, then his words in serif, the bleep a smaller block of the same." if i == 0 else "",
         "One click per swap. The bleep is a relay buzz." if i == 0 else "", "match-cut swap")
shot("A10", "A", 80, 10, "GEN + INK",
     "Mara, same frame, head still bowed. Ink at full density: shouting mouths, quoted doubts, a skull.",
     "MARA (voice only, from frame 78): \"Everybody's got...\"", "", "match-cut swap")
shot("A11", "A", 90, 5, "INK + CODE",
     "Extreme close-up of the drawn mouth under its block of lit cells. The picture slips for a frame as it lands.",
     "", "One click.", "cut on the click")
shot("A12", "A", 95, 5, "CODE over GEN",
     "Backspace. A blade of light the height of the frame runs right to left and takes the ink with it in five steps, passing behind Mara. Her head comes up.",
     "", "Five fast clicks.", "backspace wipe")
shot("A13", "A", 100, 20, "GEN",
     "Extreme close-up, Mara. Eyes up into the lens. Clean wall. Dry.",
     "MARA: \"...a prediction.\" Caption: EVERYBODY'S GOT A PREDICTION.",
     "One inhale, then nothing for two frames.", "cut")

# ---------------------------------------------------------------- B. THE WIND
shot("B01", "B", 120, 10, "GEN",
     "Black for three frames on the downbeat. Then the hall's tube lights come on pair by pair down both "
     "sides, and at the far end the fan shows, backlit cyan through haze. Low, wide, a slow push.",
     "", "DROP 1: kick, sub, the fan chopping the pad on eighths.", "hard cut to black on the downbeat")
shot("B02", "B", 130, 5, "MACRO",
     "Macro: a fan blade's edge slices the beam.", "", "", "cut")
shot("B03", "B", 135, 10, "GEN + CODE",
     "Title on glass. A partition in the foreground catches the beam: FIRST WORD in brush lettering. "
     "Mara's silhouette crosses behind it.", "", "", "cut")
shot("B04", "B", 145, 30, "GEN + CODE (3D)",
     "Behind Mara, tracking forward, low, as she walks into the wind toward the fan. Paper strips and "
     "smoke streamlines stream past the camera. Two strips carry a dated prediction each: each arrives in three "
     "frames and then hangs near the lens for about a second, drifting, so it can be read, and the two overlap. "
     "Half-way it cuts in close behind her: the fan is the size of the end wall. The strips ride across the cut.",
     "TYPE ON STRIPS: \"FROM ONE MILLION TO TEN MILLION YEARS.\" 1903. \"THE INTERNET? BAH!\" 1995.",
     "Wind. Paper snaps on the off-beats.", "cut")
shot("B05", "B", 175, 5, "MACRO",
     "Macro: the relay's armature snaps shut. A pinpoint cyan spark.", "", "Click, dry and loud.", "relay cut")
shot("B06", "B", 180, 25, "GEN + CODE (3D)",
     "From the front, low, wide lens tracking backward. She leans into the wind, jacket snapping. "
     "Strips whip past both sides of the lens. Three carry a prediction each and hang near the lens, each in its own part of the frame, for two thirds of a second to a second.",
     "TYPE ON STRIPS: \"NO GREATER THAN THE FAX MACHINE'S.\" 1998. \"HITTING A WALL.\" 2022. IT CAN'T EVEN DRAW HANDS. 2023.",
     "", "cut")
shot("B07", "B", 205, 10, "GEN", "A card of paper plasters itself across her cheek. She peels it off.", "", "Slap of paper.", "cut")
shot("B08", "B", 215, 10, "MACRO",
     "Macro: the card between her fingers. Printed: FLYING CARS BY 2000. Under it, handwritten: us.", "", "", "cut on action")
shot("B09", "B", 225, 10, "GEN", "She snorts, lets the wind take it, keeps walking.", "", "Her snort, close: the short laugh her own shot carries.", "cut")
shot("B10", "B", 235, 5, "CODE", "A strip of newsprint slaps flat against the lens. White-out.", "", "Slap. The music drops into a small speaker.", "paper slap")

# ---------------------------------------------------------------- C. A MILLION YEARS
shot("C01", "C", 240, 35, "ARCHIVE",
     "Scanlines. Macro crawl along a newspaper column: The New York Times, 9 October 1903, page 6. A red wax "
     "pencil underlines the words \"from one million to ten million years\".",
     "OSEI (reading; his voice starts over the wind, from frame 228): \"'From one million to ten million years.'\"",
     "Pencil squeak. Music band-passed, as if from the television.", "scanline roll-in")
shot("C02", "C", 275, 15, "ARCHIVE", "Wider: the page's running head and its date, circled in red. On the word \"years\" (frame 283) it cuts once, inside the shot, to what the paper was laughing at: Langley's Aerodrome lying in the Potomac, 7 October 1903 (Smithsonian, Langley Memoir on Mechanical Flight, plate 100).", "", "", "cut")
shot("C03", "C", 290, 5, "CODE", "Black. Stamp: 69 DAYS LATER.",
     "", "One click.", "cut")
shot("C04", "C", 295, 25, "ARCHIVE",
     "Scanlines. 17 December 1903, Kitty Hawk: the Flyer a few feet off its rail, a man running "
     "alongside (Library of Congress). Slow push in. At frame 312 it cuts once, inside the shot, to the "
     "telegram Orville Wright sent home that afternoon (Library of Congress): its first word, Success, "
     "underlined in red.",
     "MARA (from frame 300, dry, as the Flyer is in the air): \"Close.\"", "Wind, thin and old. A telegraph key, then the pencil. The tube switches off on the last two frames.", "cut")

# ---------------------------------------------------------------- D0. THE QUESTION
shot("D01", "D0", 320, 25, "GEN",
     "Line-up frame, clean wall. Jun looks straight down the lens.",
     "JUN: \"So what does it actually do?\"", "Music back to full range, bass and clicks only.", "match-cut swap")
shot("D02", "D0", 345, 15, "CODE",
     "Black card, while Jun is still finishing his question. The captions predict the answer in grey italic: IT CHANGES EVERYTHING. It holds for ten frames, then the cursor backspaces it.",
     "", "Five fast clicks.", "cut")
shot("D03", "D0", 360, 25, "GEN",
     "The hall. Mara at her bench leans into a wide lens, cyan flare over her shoulder.",
     "MARA: \"It finishes things.\" Caption types in white: IT FINISHES THINGS.", "", "cut")
shot("D04", "D0", 385, 25, "GEN", "Line-up frame. Ray, arms crossed, flat.",
     "RAY: \"It makes things up.\"", "", "match-cut swap")
shot("D05", "D0", 410, 10, "GEN", "Extreme close-up, Mara. She does not blink.",
     "MARA: \"Constantly.\" Grey caption NO, IT DOESN'T. is backspaced first.", "", "cut")
shot("D06", "D0", 420, 5, "MACRO", "Macro: relay click, spark.", "", "Click.", "relay cut")
shot("D07", "D0", 425, 15, "GEN", "Mara pulls the cap off a red wax pencil with her teeth, at a bench in front of the fan, and holds the pencil up.",
     "MARA: \"So we check.\"", "Cap pop.", "cut")

# ---------------------------------------------------------------- D1. THE BRONZE
shot("D08", "D1", 440, 25, "ARCHIVE",
     "Scanlines. Raking light across a broken Roman bronze: a fragment of a military diploma from Sardinia, "
     "113/114 CE (The Metropolitan Museum of Art, public domain image). Slow crawl along the engraved letters to the broken edge. Small tag: ROMAN MILITARY DIPLOMA, 113/114 CE.",
     "OSEI: \"A Roman sentence, broken in bronze.\"", "Metal room tone.", "spark-to-light match")
shot("D09", "D1", 465, 20, "ARCHIVE + CODE",
     "The break. Grey letters carry the line on past the broken edge, exactly as the published restoration has them. "
     "Two alternatives list beneath, each with a percentage.",
     "", "Soft clicks as letters land.", "cut")
shot("D10", "D1", 485, 15, "MACRO",
     "A hand ticks the restoration with the red pencil on a print of the bronze: the museum's own photograph, with the four restored lines in grey. The stamp arrives in two parts: SUGGESTED. over the grey letters of the shot before, THEN CHECKED. on the tick.",
     "", "Pencil squeak.", "cut")

# ---------------------------------------------------------------- D2. THE EMAIL
shot("D11", "D2", 500, 5, "INK", "The bronze's broken edge becomes a torn paper edge. The paper rips across frame.",
     "", "Rip.", "torn-edge match")
shot("D12", "D2", 505, 35, "INK",
     "Navy ink on white, halftone. A lab whiteboard buried under years of marker. Stamp, top left: 10 YEARS.",
     "MARA: \"One lab. Ten years. Unpublished.\" The stamp lands on \"ten\".", "A stamp: a slap with a thump under it.", "cut")
shot("D13", "D2", 540, 20, "INK",
     "An ink laptop. On its screen, set in the drawn screen's own perspective, a label (top-ranked hypothesis:) and then the hypothesis typed out "
     "in the words of the paper that reported it: cf-PICIs hijack diverse phage tails to expand their host range. Stamp, top left, in the place 10 YEARS. just held: 2 DAYS.",
     "JUN: \"Same idea. Two days.\"", "Keys, one for each two letters. The stamp.", "cut")
shot("D14", "D2", 560, 60, "INK + CODE",
     "An ink email window. The real quote types itself in serif inside quotation marks: \"you have access to my "
     "computer, is that right?\" Source line: JOSÉ PENADÉS, IMPERIAL COLLEGE LONDON, TO THE BBC, 2025. Hold.",
     "OSEI (deadpan): \"He asked if they'd been in his computer.\"", "Send whoosh, small.", "cut")

# ---------------------------------------------------------------- D3. THE VOICE
shot("D15", "D3", 620, 40, "CODE",
     "Black. The cursor, a small tube of cyan light, waits at the left of frame. One column builds above and below it and stays to the end of the passage. "
     "First, typed in white capitals: CASEY HARRELL HAS ALS. Under it a row of 256 slits of cyan light flickers into life, one for each electrode, "
     "with a small label: 256 ELECTRODES IN HIS BRAIN. (The row is a drawing of a signal being read, not data.)",
     "MARA (soft): \"And a sentence a man could no longer say.\"",
     "The music stops on the click at 0:26.7. A held pad. A faint electrical crackle.", "cut to black")
shot("D16", "D3", 660, 45, "CODE",
     "Black. As Mara's line ends, a second line types: HIS FOUR-YEAR-OLD WALKS IN DRESSED AS A CHEETAH. Small, at the foot of the column: UC DAVIS. NEW ENGLAND JOURNAL OF MEDICINE, 14 AUGUST 2024.",
     "MARA (soft, carrying on, from 0:28.9): \"Read straight from his brain.\"", "Pad and crackle.", "cut")
shot("D17", "D3", 705, 30, "CODE",
     "From 0:29.0 the cursor types his sentence, letter by letter, the next three letters still noise until each settles, in serif inside quotation marks: \"I'm looking for a cheetah.\" "
     "The row of electrodes is at its busiest while it is being written, a wave of firing running along it toward the sentence.",
     "The words are his, as reported by the researchers.", "A soft tick for every two letters, and a stream of tiny blips: the decoder.", "cut")
shot("D18", "D3", 735, 15, "CODE",
     "The column holds. The electrodes go quiet. The stamp, in two parts, from 0:29.75: DECODED. THEN SPOKEN, IN HIS OWN VOICE.",
     "", "Two quiet stamps. One breath, ending on the cut.", "cut")

# ---------------------------------------------------------------- E. THE TURN
shot("E01", "E", 750, 45, "GEN + INK",
     "Line-up frame. Ray. His arms uncross. The ink mouths around him un-draw themselves.",
     "RAY (quiet): \"So it is just autocomplete.\"", "Sub pulse like a heartbeat. Breaths.", "match-cut swap")
shot("E02", "E", 795, 5, "CODE",
     "Black card. The grey prediction IT'S SO MUCH MORE THAN THAT., already up as a caption under Ray's last word, is backspaced.",
     "", "Five fast clicks.", "cut")
shot("E03", "E", 800, 40, "GEN", "Extreme close-up, Mara. The first smile in the film, and it is given time.",
     "MARA: \"Yeah.\" Half a beat. \"It is.\"", "", "cut")
shot("E04", "E", 840, 5, "MACRO", "Macro: relay click.", "", "Click.", "relay cut")
shot("E05", "E", 845, 35, "GEN",
     "Osei on camera for the first time. Three-quarter portrait in the hall beside a vertical cyan tube light. "
     "Slow push in. The tube blinks out in the shot's last two frames, mid-sentence, and the cut is to black.",
     "OSEI (on camera from his first word): \"It only finishes what somebody starts.\" His last words fall over the kitchen that follows.", "", "cut on his line")

# ---------------------------------------------------------------- F. THE KITCHEN TABLE
shot("F01", "F", 880, 25, "GEN",
     "Three frames of black, then the night kitchen. One warm desk lamp over the table. Rosa in reading glasses at an old laptop, a "
     "dismantled sewing machine on newspaper beside it. Pip in pyjamas next to her, chin on her arms. 40mm, locked.",
     "OSEI (voice over, finishing): \"...what somebody starts.\"", "Fridge hum. A clock. Two people breathing.", "cut on his line")
shot("F02", "F", 905, 10, "MACRO", "Macro: a flour-dusted fingertip pecks one key at a time.",
     "", "Single key hits. A riser begins under them.", "cut")
shot("F03", "F", 915, 15, "MACRO", "The laptop screen, close: the words are on the screen in the video itself, in the screen's own perspective. It opens on dumb quest and the last four letters arrive two frames apart, i, o, n and the colon, the cursor's cyan block moving along after each: dumb question:", "", "A key for each of the four letters.", "cut")
shot("F04", "F", 930, 15, "GEN", "Extreme close-up, Pip.",
     "PIP (a whisper, right on the mic): \"So start.\"", "", "cut")
shot("F05", "F", 945, 15, "MACRO",
     "Macro: Rosa's finger falls toward Enter in a speed ramp. Contact on the first frame of the next bar.",
     "", "Inhale. The riser peaks.", "speed-ramp impact")

# ---------------------------------------------------------------- G. THE FLOOD
g1 = [
    ("G01", 10, "INK", "A notebook page of about 1837, redrawn in ink: the words \"I think\" above a sketch of a branching tree. No scanlines: it is a redrawing.", "VOICE: \"I think...\""),
    ("G02", 5, "CODE", "A radial tree of life grows outward from one point.", ""),
    ("G03", 5, "CODE", "A protein ribbon, half folded.", ""),
    ("G04", 10, "ARCHIVE", "Scanlines. A lab notebook page, 10 March 1876 (Library of Congress): the first sentence spoken down a wire. The red pencil underlines Mr. Watson and come here in Bell's own hand.", "VOICE: \"Mr. Watson \u2014 come here...\" Captioned with his dashes, as the notebook has it."),
    ("G05", 5, "ARCHIVE", "Scanlines. A wall of switchboard operators, from a public-domain photograph.", ""),
    ("G06", 5, "MACRO", "A phone lighting up in a hand in the dark.", ""),
    ("G07", 10, "INK", "A March 1989 proposal, redrawn in ink, with a boss's pencilled note at the top: \"Vague but exciting ...\" No scanlines: it is a redrawing.", "VOICE: \"Vague but exciting.\" The pencil is heard writing it."),
    ("G08", 5, "INK", "A black cube computer in ink, with its hand-written sticker: \"This machine is a server. DO NOT POWER IT DOWN!!\"", ""),
    ("G09", 5, "CODE", "The first web page, rendered again from its own plain text and blue links.", ""),
    ("G10", 10, "CODE", "A newsgroup post of 25 August 1991, typed out on a terminal by the cursor: \"just a hobby, won't be big and professional\".", "VOICE: \"Just a hobby.\""),
    ("G11", 5, "ARCHIVE", "A small helicopter lifts off the surface of Mars, 19 April 2021. It runs the software that post began.", ""),
    ("G12", 5, "ARCHIVE", "Its own shadow on the Martian ground: the first five frames its camera took on that flight, one to a film frame. The shadow shrinks as it climbs.", ""),
]
f = 960
for sid, dur, src, pic, line in g1:
    shot(sid, "G", f, dur, src, pic, line,
         "DROP 2 on the Enter key: full kit, double time, choir stack." if sid == "G01" else "",
         "speed-ramp impact" if sid == "G01" else "cut")
    f += dur
g2 = [
    ("G13", "Amara on a hospital roof on her break, phone flash-lit in her foreground hand, the city behind.", "AMARA: \"Dumb question...\" Caption in serif."),
    ("G14", "Dev in a field before sunrise, holding a blighted leaf up to the lens under his phone torch.", "DEV: \"What if...\" Caption in serif."),
    ("G15", "Jun at a bedroom window open on glass towers, solder smoke curling into the lens, a half-built synth.", "JUN: \"Could I...\" Caption in serif."),
    ("G16", "Ray alone in his garage, laptop on an oil drum. He exhales and types.", "RAY: \"Okay, so...\" Caption in serif."),
]
for sid, pic, line in g2:
    shot(sid, "G", f, 20, "GEN", "Blue world, fisheye, flash-lit foreground. " + pic, line,
         "Beat-locked: one cut every two beats." if sid == "G13" else "", "cut on the beat")
    f += 20
g3 = [
    (5, "CODE", "white", "A protein ribbon, half folded, residues still loose.", "AMARA: \"Start the cure.\""),
    (5, "ARCHIVE", "black", "A thruster lighting in a NASA vacuum chamber, 2022 (film): the ring of plasma comes on with the cut and settles to blue.", ""),
    (5, "CODE", "white", "Six words in serif, read on 2 November 2026 from a scroll burnt in 79 CE: \"that which is in itself desirable\".", ""),
    (5, "ARCHIVE", "black", "A hurricane from orbit, its eye dead centre: film from the Space Station, 1 September 2019.", ""),
    (5, "MACRO", "black", "A blackboard, #1196 chalked in one corner, one line of a proof crossed out.", "OSEI: \"Start the proof.\""),
    (10, "MACRO + CODE", "black", "Macro on the crossed-out line. Serif quote over it: \"I didn't know what the problem was.\" Source line: LIAM PRICE, 23. ERDŐS PROBLEM 1196.", ""),
    (5, "MACRO", "white", "A 3D-printed hand, print supports still attached.", ""),
    (5, "CODE", "black", "A spectrogram of whale clicks.", ""),
    (5, "CODE", "white", "Two words in a typewriter face, circled in red pencil: \"Shock! Shock!\" Source line: DONALD KNUTH, 2026.", ""),
    (5, "ARCHIVE", "black", "A star field: Hubble looking into the hub of the Milky Way.", ""),
    (5, "MACRO", "white", "A cello with two strings off.", "JUN: \"Start the band.\""),
    (5, "MACRO", "black", "A circuit board with one bodge wire.", ""),
    (5, "MACRO", "white", "A child's crayon drawing beside its first clumsy print.", ""),
]
for i, (dur, src, ground, pic, line) in enumerate(g3):
    shot("G%02d" % (17 + i), "G", f, dur, src,
         "Specimen, dead centre on seamless %s. %s" % (ground, pic),
         line, "Thirteen cuts in 2.9 seconds. Rendered frames carry their own source code as grey annotations." if i == 0 else "", "shape-match cut")
    f += dur
shot("G30", "G", f, 10, "CODE",
     "Black. Small, above: 1969. THE INTERNET'S FIRST WORD. The word LOGIN stands in grey in a teletype face, "
     "and the cursor sends it a letter at a time: L turns white, then O. Then the frame crashes into datamosh.",
     "ROSA: \"Start it wrong.\"", "A modem handshake, five frames.", "cut")
f += 10
shot("G31", "G", f, 20, "CODE",
     "Black, the same card held. LO in white, GIN still grey, no cursor. Stamp: IT CRASHED. On the next beat the cursor "
     "comes back, G, I and N turn white, and the stamp becomes FIXED., with ABOUT AN HOUR LATER. small beneath it. (Twenty frames, where the approved "
     "plan had ten: see the note on G32 and G33.)",
     "", "The music stutters for one beat, and comes back on the fix.", "cut")
f += 20
g4 = [
    ("G32", "ARCHIVE", "Scanlines, two tubes side by side. Left: a mission control room on its feet, flags waving, 24 July 1969, colour film. "
                       "Right: another control room, 18 February 2021, the same jump. (The approved plan had these as two cuts of five frames, "
                       "G32 and G34. They share a frame so the crash before them can be read.)", "ALL: \"We'll fix it.\""),
    ("G33", "GEN", "Two pictures side by side. Left: Rosa laughing at her screen, hand over her mouth. Right: Ray laughing in spite of himself. "
                   "(The approved plan had these as two cuts of five frames, G33 and G35.)", ""),
    ("G36", "GEN", "The baton of cyan light leaves Mara's hand.", ""),
    ("G37", "GEN", "Osei's hand takes it and passes it on.", ""),
    ("G38", "GEN", "Jun's hand.", ""),
    ("G39", "GEN", "Rosa's hand, flour on the knuckles.", ""),
    ("G40", "GEN", "Pip's small hand closes round it.", ""),
    ("G41", "GEN", "Whip tilt up from her raised fist into deep blue.", ""),
]
for sid, src, pic, line in g4:
    shot(sid, "G", f, 5, src, pic, line,
         "Kick leaves on the last two beats." if sid == "G40" else "",
         "whip tilt" if sid == "G41" else ("matched action, left to right" if sid in ("G36", "G37", "G38", "G39", "G40") else "cut"))
    f += 5

# ---------------------------------------------------------------- H. THE WHALE
shot("H01", "H", 1260, 60, "GEN",
     "Blue world, fisheye. A rooftop meadow at blue hour, flash-lit flowers inches from the lens, a washing "
     "line, a hydrophone on a tripod. Pip, small, back to us, holds the baton up like a lantern. Above the "
     "glass towers the sky is the underside of an ocean, and a sperm whale glides through it. The baton "
     "blinks; two frames later the whale's click answers, and each click sends a ring across the surface overhead. A navy work jacket with the cursor patch hangs on the line. "
     "Two lines type at the left, on a soft dark ground: A SPERM WHALE IS SPEAKING. Then: NOBODY KNOWS WHAT IT SAYS. YET. Hold.",
     "OSEI: \"Nobody predicts the future.\" Caption for the whale, by its head: one dot for each click, spaced as the clicks are (one, one, then three quick ones), then a question mark.",
     "Engine off. Choir pad, a sub swell, and the 1+1+3 clicks with a long tail.", "whip tilt")
shot("H02", "H", 1320, 16, "GEN + CODE", "Macro: Pip's eye, the whale crossing its reflection (the whale in the eye is drawn in code).", "", "A breath that turns into a laugh: the sound her own shot carries.", "cut")
shot("H03", "H", 1336, 44, "GEN",
     "She spins and pushes the baton into the lens. Fisheye: her fingers huge and flash-lit, the bar "
     "growing until it is a vertical band of cyan across the frame.",
     "PIP (close, in the voice the video model gave her): \"Somebody starts it.\"", "", "cut on the turn")

# ---------------------------------------------------------------- I. THE MARK
shot("I01", "I", 1380, 60, "CODE",
     "The baton's light, white-hot, draws itself in to the cursor's place over six frames, and the cursor comes on with a flare. White type: The future is. "
     "On the second click the film answers its own opening prompt, typed letter by letter: The future is yours to start. Every click sends a ring out from the cursor. "
     "The last three clicks each land one part of a question under the sentence, in the film's serif italic and larger than the sentence, cyan-hot and cooling to white, "
     "the frame punching in on each: What, will you, start? The last one flashes. Then the cursor leaves the sentence, comes to rest after the question mark with a flare "
     "and three rings, and blinks there to the last frame. The maker's mark lands with the last word (when there is one). "
     "(No title and no disclosure line on the card: the user asked for both to go, the title in v013 and the line in v014.)",
     "", "Five clicks, 1+1+3, each with its ring. Keys under the typing. A stamp for each part of the question, a short swell into the last, and weight under it. The whale's pad holds under it all and is gone before the film loops.", "bar-to-cursor match")

def tc(frame):
    s = frame / FPS
    return "%d:%05.2f" % (int(s // 60), s % 60)


def validate():
    S.sort(key=lambda x: x["start"])
    pos = 0
    for s in S:
        assert s["start"] == pos, (s["id"], s["start"], pos)
        pos += s["dur"]
    assert pos == TOTAL, pos
    ids = [s["id"] for s in S]
    assert len(ids) == len(set(ids))
    for key, name, a, b, dials, kick in PASSAGES:
        shots = [s for s in S if s["passage"] == key]
        assert shots[0]["start"] == a and shots[-1]["start"] + shots[-1]["dur"] == b, key


def stats():
    d = [s["dur"] for s in S]
    out = dict(shots=len(S), mean_s=round(statistics.mean(d) / FPS, 2), median_s=round(statistics.median(d) / FPS, 2),
               shortest_f=min(d), longest_f=max(d), under_half_second=sum(1 for x in d if x < 12),
               holds_2s=[(s["id"], round(s["dur"] / FPS, 2)) for s in S if s["dur"] >= 48])
    per = []
    for key, name, a, b, dials, kick in PASSAGES:
        n = sum(1 for s in S if s["passage"] == key)
        per.append(dict(key=key, name=name, start=tc(a), end=tc(b), seconds=round((b - a) / FPS, 2), shots=n,
                        cuts_per_min=round(n / ((b - a) / FPS) * 60), dials=dials, kick=kick))
    src = {}
    for s in S:
        for part in s["source"].replace("(3D)", "").replace("over", "+").split("+"):
            k = part.strip()
            src[k] = src.get(k, 0) + s["dur"] / (s["source"].count("+") + s["source"].count("over") + 1)
    out["passages"] = per
    out["source_seconds"] = {k: round(v / FPS, 1) for k, v in sorted(src.items(), key=lambda kv: -kv[1])}
    return out


def markdown():
    lines = []
    for key, name, a, b, dials, kick in PASSAGES:
        lines.append("## %s. %s (%s to %s)\n" % (key, name, tc(a), tc(b)))
        lines.append("| Shot | In | Frames | Made by | Picture | Voice and type | Sound | Cut in |")
        lines.append("| --- | --- | --- | --- | --- | --- | --- | --- |")
        for s in S:
            if s["passage"] != key:
                continue
            lines.append("| %s | %s | %d | %s | %s | %s | %s | %s |" % (
                s["id"], tc(s["start"]), s["dur"], s["source"], s["picture"], s["line"], s["sound"], s["transition"]))
        lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    validate()
    here = os.path.dirname(os.path.abspath(__file__))
    st = stats()
    json.dump(dict(fps=FPS, bpm=144, frames=TOTAL, passages=st["passages"], shots=S), open(os.path.join(here, "shotlist.json"), "w"), indent=1)
    open(os.path.join(here, "shotlist.md"), "w").write(markdown())
    print(json.dumps(st, indent=1))
