# Production state

> This is the project's `STATE.md` as it stood when v015 was delivered, unchanged: the agent's running record of
> what was done, decided and left open, newest first. It names files under `clips/`, `audio/`, `out/` and
> `research/`, which are not in this repository.

Last updated 11 November 2026, 15:30 UTC, after the reel (the film for Instagram) and the process figures. Before that, the 1080p production pass (v015): every draft finished at 1080p, every made shot rebuilt at that size, the whole film reviewed at full size, and masters written.

## Where it stands

- **The film is v015, at 1920 by 1080.** Three masters, all with `audio/mix_v015.wav` (the vertical version for Instagram is in the next section):
  - `out/first_word_v015_1080.mp4`: the standard master. H.264 High, 12 Mbit/s, BT.709 and tagged so, AAC 256k.
  - `out/first_word_v015_1080_prores.mov`: the same frames as ProRes 422 HQ (10-bit), with the sound uncompressed (24-bit). For an editor, a colourist or a platform that wants a mezzanine file.
  - `out/first_word_v015_1080_hdr.mp4`: the HDR master (10-bit HEVC, HLG, BT.2020). Only the film's own lights are above white.
  - `out/animatic_v015.mp4`: a 720p copy with shot names and frame numbers burnt in, for notes.
  - Sound alone: `audio/mix_v015.wav` (24-bit, 48 kHz, -14.1 LUFS, true peak -2.1 dBFS) and the four stems in `audio/stems/` (dialogue, effects, score, whale; 24-bit).
- The cut is 98 shots, not the plan's 100 (see the eighth pass). Every shot has its picture; nothing in the film is a draft any more.
- Standing instructions from the user: follow the plan and do not game it, use real archive. The cast the reels produced is accepted. On 11 November 2026 the user topped up Runway and asked for the film to be made production-ready, which released the 1080p pass.
- Runway: 199.85 USD spent of its 500, 15 credits left. ElevenLabs: 21,001 of 131,000 plan credits used (nothing new on this pass). `GEMINI_API_KEY=` in `.env` is still empty.

## The reel: the film for Instagram (v015), 11 November 2026

The user: "Let's create the social media version of this as well, so I can share on Instagram Reels."

- **Files** (all 60.000 s, the v015 mix, -14.1 LUFS, true peak -2.1 dBFS):
  - `out/first_word_v015_reel.mp4`: 1080 by 1920, H.264, 24 fps, BT.709 tagged. The film's own frame rate.
  - `out/first_word_v015_reel_30fps.mp4`: the same at 30 fps (every fourth frame shown twice). Instagram's help page asks for at least 30 fps; 24 is accepted in practice. This copy is for when it is not.
  - `out/first_word_v015_reel_hdr.mp4`: 10-bit HEVC, HLG. Only the film's own lights above white, as in the 16:9 HDR master.
  - `out/first_word_v015_reel_cover.jpg`: a cover, the title on the glass (frame 141).
- **The shape.** The picture is the middle 4:5 of the 9:16 frame (y 285 to 1635). That is exactly what the feed shows of a reel and is inside what the profile grid shows; Instagram's own buttons sit over the black bands. It takes 45 percent of the film's width (a full 9:16 crop would take 32 and enlarge it 1.8 times; this enlarges 1.25).
- **Every shot is re-framed by hand, not cropped blind** (`timing/reel.json`, `tools/reel.py`): the generated shots get a window placed on the subject (some move with it); the archive shots get a tube of the new shape; the three frames that held two pictures side by side are stacked; code and type shots have their type set again in the film's own frame so that it fills the vertical width (the Casey Harrell text, the stamps, the 1969 card and the last screen are laid out again, some lines broken in two); the paper-strip shots are rendered again with the strips stacked above and below her (`timing/wind_reel.json`).
- **Captions** are taken off the picture and set again on the vertical frame by the conform's own code, at y 1380, never wider than 820 px.
- **Safe zone.** Meta publishes one only for Reels ads (top 14 percent, bottom 35, sides 6; looked up 11 November 2026). The film's own type is inside it, and the years on the paper strips are kept above the buttons at the lower right. The captions are lower than the ad zone allows (they are clear of an ordinary reel's buttons): `CAP_Y_PX` in `tools/reel.py` moves them if the reel runs as an ad.
- **Checked:** every shot looked at in the finished file (first, middle and last frame, with the safe box drawn), two frames at full size, and the changed shots after each of three rounds of fixes. Frame count, length, colour tags and loudness measured. **Not checked:** how it looks inside the Instagram app, on a phone; the sound by ear; the HDR file on an HDR screen.

## The 1080p production pass (v015), 11 November 2026

The user: "I have topped up the runway credits, so you can make the entire movie production-ready. Also, review the entire scene, everything, and improve, optimize, and make it ready for production."

**What was made**

- **All 16 drafts finished at 1080p.** Jobs `<name>_1080` in `timing/generations.json` (body: the model and the draft's task id, nothing else), results in `clips/final/<name>.mp4`: 1920 by 1080, 10-bit HEVC, the same frame count as the draft. 190 seconds, 12,920 credits, 129.20 USD. Each was compared with its draft frame for frame before it went into the cut: same length, same cuts at the same frames, no slip in time, the same faces and the same words on the laptop's screen. They are the same takes finished, not new takes.
- **`tools/conform.py` reads a draft at its best** (`best()`): when the 1080p version exists it is used, so `timing/cutin.json` did not change and every in-point, punch-in and lip-sync figure stands (worst slip still 1.2 frames).
- **Every made shot rebuilt at 1920 by 1080**, each by its own tool at that size, not enlarged: the 12 archive shots (`tools/archive_shots.py`, new: the recipes in a form that runs, checked against the existing shots before use), the code shots and stills, the wind shots, D10, H02, the two diptychs, and the laptop's screen (`tools/laptopshot.py`, whose measures were all in draft pixels and now scale to the source). The 720p versions are in `clips/replaced/720p/`.
- **The sound is the v013 mix, unchanged**, written again as 24-bit (`audio/mix_v015.wav`; the largest difference from `mix_v013.wav` is 85 dB below full scale, which is the 16-bit rounding that is now gone).

**The review.** The whole film was rendered at 1920 by 1080 and looked at three ways: every one of the 98 shots on sheets (first, middle and last frame); 32 windows at full size, one film pixel to one screen pixel (every face, the line-up, the hall, each made shot, each kind of archive, the type); and the caption line of every shot. It was also measured against v014 shot by shot: every shot is in the same place and every shot carries more detail (1.1 to 1.9 times). No frozen frames, no stray black frame (the one black frame is the television switching off at 319, as planned).

**What the review found, and what was done**

| Found at full size | Done |
| --- | --- |
| The colours in every file so far were slightly wrong on a player. ffmpeg turns RGB into video by the old SD rule (BT.601) unless told otherwise and wrote no tag; a player reads an HD file by the HD rule. Measured: in coloured areas red 4 to 5 levels low and blue 2 high on Mara and in the hall, red 4 high in the kitchen. | The conform converts by BT.709 and tags the file. Read back by its tags, the master matches the frames the film was made from to within 0.1 of a level on average. |
| The words on the paper strips were striped, and the year at a strip's end could not be read: the shutter was open for the whole frame, so a turning strip smeared 16 pixels, in 14 visible steps. | A half-open shutter, as a film camera's is, and finer steps. Words and years are sharp. Timing unchanged. |
| The type on the card ("FLYING CARS BY 2000.") was softer than the card it lies on, now that the card is sharp. | Its softness is matched to a 1080-line plate (`soft_hd` in `timing/wind.json`). |
| A pale box round the laptop's cursor, and the cursor itself a flat cyan patch. | The box is gone (only the block's own pixels are touched). The block is drawn as light: cyan at its edge, nearly white at its heart, the screen's grain in it, a slow pulse, a glow on the page. |
| White captions over bright pictures had only a shadow: "NOBODY PREDICTS THE FUTURE." on the daisies, "SOMEBODY STARTS IT." on the baton, "START THE PROOF." and "START THE BAND." on white studio shots. | Captions look at the picture under them. A white frame gets paper's box, as the white cards always had. A bright thing in a darker frame gets a soft dark shade under the line, deeper the more of it is bright, and nothing where it is dark. |
| On the blackboard the chalk stroke ran through "I didn't know what the problem was." like a strike-through. | The quote sits just above the stroke, which now underlines it. |
| Under the spectrogram of the whale's clicks, the caption ran over the third line of small print. | The small print sits higher. |

**Looked at and left alone.** The cursor patch on the jackets is plain at full size: it is a blank label by design. The reflection of the sky in Pip's eye is a hard-edged shape: that is the generated shot's own reflection; only the whale in it is drawn. Punch-ins on the reels (the two close-ups of Mara) are softer than the wide shots, as a punch-in is. Faults inside reels are as before (Mara reads younger than her forties; Pip reads about six in the kitchen).

**The masters, measured**

| File | Picture | Sound |
| --- | --- | --- |
| `out/first_word_v015_1080.mp4` | H.264 High, 1920x1080, 24 fps, 1,440 frames, 12 Mbit/s; BT.709, limited range, tagged | AAC 256k, 48 kHz; -14.1 LUFS, range 6.8 LU, true peak -2.1 dBFS |
| `out/first_word_v015_1080_prores.mov` | ProRes 422 HQ, 10-bit, 150 Mbit/s; BT.709, tagged | PCM 24-bit, 48 kHz; the same levels |
| `out/first_word_v015_1080_hdr.mp4` | HEVC Main 10, HLG (ARIB STD-B67), BT.2020; white at 203 nits, brightest pixel 784 nits, 453 of 1,440 frames carry light above white | AAC 256k; the same levels |

**Not judged.** I cannot hear and cannot see an HDR screen. The sound is the mix measured for v013 and nothing in it changed; the HDR file is checked by its levels and by which pixels it lifts (the same lights as in the v014 test, plus the laptop's cursor). Both still want a person: ears for the music and the mix, an HDR phone for the HDR file.

**A new draft from here on.** It is still a 480p draft first. Finishing it at 1080p is 68 credits a second of the whole draft and is only possible within 7 days of the draft being made (`research/runway_api/type_text_to_video_create_params.py.txt`). Until it is finished it will be soft beside everything else.

## The rule that reshaped the plan

Seedance refuses any reference image or clip that contains a realistic face, including a face it generated itself
(`research/faces/`). It is not worked around. One job per person (that person's reel), one fixed description per person
(`timing/characters.json`), references only for places and things. Changing one shot of a person means regenerating
that person's whole reel, which changes their face, so faults inside a reel are left unless the user asks.

## The eighth pass: six scenes that did not read, and the sound

The user, after watching v010, with six screenshots: "The dumb question needs to be written on the screen, so it needs
to come from the video. Also, the last view doesn't make sense. The writing needs to be a better message. With the
whale scene, I don't understand the messaging as well. We need to improve that. With the two-day scene, the writings
need to be done better. I think we can do a better job explaining this decoded casey harrell section. It crashed. The
third letter needs to be done better as well. It's hard to understand. And also, you can do a better sound design at
the sound level with better effects, but also with the background music." They offered a Google key, ElevenLabs, or to
make the music themselves in Runway from a prompt.

What was done, scene by scene. Every picture below was looked at as rendered frames through the film's own compositor.

- **"dumb question:" (F03, 0:38).** It was type laid over a video of a laptop. It is now in the video: a draft was
  generated with the words on the laptop's screen (`macro_screen`, 1 USD) and they came back spelled right, in the
  screen's perspective, with a block cursor. `tools/laptopshot.py` punches in, gives the cursor's block the film's
  cyan, and types the words: the shot opens on "dumb quest" and i, o, n and the colon arrive two frames apart, the
  block moving along. No letter is drawn. An untyped letter is covered with the same frame's own page.
- **The two-day scene (D12, D13, 0:21 to 0:23).** The hypothesis is set in the drawn laptop screen's own perspective
  (a new `screen` type style that warps a flat page onto four corners), under a small label, and typed. "10 YEARS."
  and "2 DAYS." land in the same place, top left, one after the other.
- **Casey Harrell (D15 to D18, 0:26 to 0:31).** One column that builds and stays: CASEY HARRELL HAS ALS. / a row of
  256 slits of light, one for each electrode, labelled 256 ELECTRODES IN HIS BRAIN / HIS FOUR-YEAR-OLD WALKS IN
  DRESSED AS A CHEETAH. / his sentence, decoded letter by letter while the row is at its busiest / DECODED. THEN
  SPOKEN, IN HIS OWN VOICE. (now on screen for 28 frames, not 7) / the source in fine print. Mara has a second line over the decoding, carrying on her
  sentence: "Read straight from his brain." The row of slits is a drawing of a signal, not data, and its note says so.
- **The 1969 crash (G30, G31, 0:49.6 to 0:50.8).** It had 20 frames and said IT CRASHED ON THE THIRD LETTER. It now
  has 30 and tells the whole thing on one card that does not move: 1969. THE INTERNET'S FIRST WORD. / the word LOGIN
  in grey, L and O turning white as they arrive / the crash / IT CRASHED. / then G, I and N turn white and the stamp
  becomes FIXED., with ABOUT AN HOUR LATER. small beneath it, two frames before the chorus says "We'll fix it." (The
  day and month, and "an hour later" in the stamp itself, were on the card at first; the reading-load report said
  neither could be read in the time, so the card was cut to what can.) Two things were wrong in
  the old card and are corrected: it called this "the first message between two computers" (computers had been linked
  before; this was the first message on the ARPANET, the network the internet grew from, and Kleinrock's own account
  calls it the first message on the Internet), and it never said the login went through about an hour later
  (Kleinrock; Bill Duvall in BBC Future, 28 October 2024).
- **Where the ten frames came from.** The four cuts after the crash (a control room in 1969, Rosa laughing, a control
  room in 2021, Ray laughing, five frames each) are now two frames of five, each a pair: the two rooms side by side on
  two tubes, and Rosa beside Ray (`tools/diptych.py`). That is a change to the approved plan: 98 shots where it has
  100, though nothing the plan shows is gone. The real pictures are only cropped; each half is put through the
  scanline pass at its own size.
- **The whale (H01, 0:52.5 to 0:55).** Two lines type at the left: A SPERM WHALE IS SPEAKING. Then: NOBODY KNOWS
  WHAT IT SAYS. YET. (v011 had A SPERM WHALE'S CALL: FIVE CLICKS. NOBODY KNOWS WHAT IT MEANS. YET. The user watched
  it and asked what the scene meant: the line never said the whale was saying something, which is the link to the
  film's title. Reworded in v012 with the user's yes.) The dots by the whale's head are larger and spaced as the clicks are (one, one, three).
  The tag they replace (NOT YET. LISTENING SINCE 2005.) explained nothing to someone who did not know the story.
- **The end card (I01, 0:57.5 to 1:00).** The film now answers its own opening prompt: "The future is" becomes
  "The future is yours to start.", typed on the second click. FIRST WORD lands under it on the third. The disclosure
  is fine print at the foot and, since v012, says it plainly: THE ARCHIVE FOOTAGE IS REAL. THE PEOPLE ARE
  AI-GENERATED. ("Scanlines" was a production word a viewer does not have.) The sentence holds to the last frame, so the last frame no longer matches the
  first exactly: on a loop the prompt and the cursor are in the same place and the sentence clears.

### After v012: the paper strips, and the end card (v013)

The user, on the hall of wind at 0:07: "These writings are great, but they are passing so fast. I think we need to
slow it down a bit there so we can read those writings." And on the end card: "I believe we can remove the first word
here. It's not adding anything. Make the end a bit more dynamic and create buzz."

- **The lettered strips (B04, B06).** Each of the five was in reach of the eye for 7 to 9 frames, one after another.
  Each now arrives in two or three frames and then hangs near the lens, drifting slowly, so it is sharp: about 24 and
  20 frames in B04, and 21, 18 and 16 in B06 (`timing/wind.json`). They overlap, each in its own part of the frame,
  and in B04 they ride across the cut inside the shot. The limit, said plainly: the five lines hold 126 letters and
  digits and the two shots are 55 frames long, so one viewing reads one or two lines a shot, not all five. Reading
  all five at a comfortable speed would need the hall to be about two seconds longer, taken from somewhere else in
  the minute. That was not done.
- **The end card (I01).** The title FIRST WORD is gone from it. The quick three of the last five clicks (1400, 1405,
  1410) each land one part of a question under the sentence: WHAT / WILL YOU / START? Each part arrives large and
  cyan-hot and cools to white, the frame punches in on each, and the last flashes and sends three rings out. The
  sentence and the question hold to the last frame, with the disclosure at the foot. The title still appears once, on
  the glass at 0:05.6 (B03). Sound: a stamp for each part, a short swell into the last, weight under it and the room's
  ring after it; the last second is near silence. Mix v013 measures the same as v011 (-14.1 LUFS, peak -2.1 dBFS).
  My reading of "create buzz": end on a question the viewer can answer. That is mine, not the user's words.

### After v013: the last screen's type, and the disclosure line (v014)

The user, with a crop of the end card: "Make these fonts better on the last screen and also remove the
'AI-generated line.'"

- **Type.** The card had two voices: the sentence in the film's serif and the question in heavy condensed capitals.
  It now has one. The sentence is as it was (the serif, the size and place of the opening prompt). The question is
  set in the film's serif italic, the face the film already keeps for questions, larger than the sentence: What will
  you start? Its three parts still land on the last three clicks, cyan-hot, cooling to white. Then the cursor leaves
  the sentence and comes to rest after the question mark, with a flare and three rings, and blinks there to the last
  frame: it is the viewer's turn. Six treatments were drawn with the faces already in `fonts/` and this one chosen by
  looking; the sheet is `out/end_card_type_options.jpg`. No new typeface was brought in: that needs a download, which
  the user has not been asked about.
- **The disclosure line is gone**, as asked. The film itself now says nowhere that its people are generated. The
  plan's own table (What the tools require, Disclosure) records, from Runway's commercial-use guide, that New York
  has required a conspicuous disclosure in advertisements featuring AI-generated human likenesses since 9 June 2026.
  So if the film runs as an ad, the disclosure has to be made some other way: the platform's AI label at upload, the
  caption, or the line put back (one event in `timing/type.json`). Whether that is enough is a lawyer's question. The
  user was told this when v014 was delivered.

### An HDR test (after v013)

The user: "What do you think if we push HDR on this so it highlights? It gets really bright on social media
screens." I recommended it as a second master, restrained, and they said to build a test.

`tools/hdr.py` builds every frame as the conform does and writes `out/first_word_v013_hdr_test.mp4` (made again for v014 as `out/first_word_v014_hdr_test.mp4`): 10-bit HEVC in
HLG (BT.2020), 1280 by 720, the whole minute. The picture sits where a standard picture sits inside HDR (white at
203 nits). Only the film's own lights are raised, by up to four times: the cursor, its rings, the tube lights, the
baton, the cyan block on the laptop, a word that lands hot. A pixel counts as that light when it is bright and cyan,
or is the near-white heart of such a light. Archive shots and the ink drawings on white paper are never lifted, and
the lift is turned down when light fills much of the frame (the baton held to the lens gets about three quarters).

Checked: which pixels the key picks, on 22 frames across the film (it took two corrections: a large light was
getting a bright rim round a dimmer heart, and the flash on the notebook page was being read as light); and the
levels and colour tags in the finished file. Decoded back to light, the file measures: white type 207 nits (75.4
percent signal, where the standard puts it); the cursor on the end card 627; the tube lights 575 to 686; a word
landing hot 684; the baton held to the lens 522, with an eighth of that frame above 250 nits (the one place it
might glare); a paper strip 128; the archive shots, the notebook page and the white-out all at white or within a
tenth of it; the brightest pixel in the film 784. 448 of the 1,440 frames have some light above white. The file is
HEVC Main 10, tagged BT.2020 and HLG, 1,440 frames, with the v013 mix. **Not checked, and not checkable by me: how it looks.** It has to be
watched on an HDR phone. It is a test of the idea on the 480p drafts; the real version belongs after the 1080p pass.

Posting notes, from what the vendors' pages said on 11 November 2026: HLG is the form Instagram plays as HDR (the
other common form reportedly plays flat there); YouTube takes it and makes its own standard version; a fresh upload
can play as standard for a day before the HDR version appears. A platform or screen without HDR falls back to a
standard picture that the platform makes itself, so where that matters the standard file should be the one posted.

### The sound, rebuilt

What measurement found, before anything was changed:

- **The music was sub bass.** A bar-by-bar map of the score the film had until v010 shows 33 seconds of the same
  groove with its energy below 100 Hz and almost nothing above 4 kHz (28 dB down) before the drop. On a laptop that
  is a dull throb. The same map of three new takes of a six-section plan showed the same fault and showed that the
  model played one groove throughout, whatever each section asked for.
- **The voices in the flood touched full scale** and the master's ceiling was a soft clip, so the loudest passage was
  being bent.
- **Most effects landed about two thirds of a frame late**: the generated files have a little air before the hit.

What was done:

- ElevenLabs' own guides were read first (`research/` holds none of them; the notes are in `timing/sfx.json`). Two
  things followed: there is a newer effects model than the one the film used, and the music model does what a plain
  prompt asks when the piece is one idea.
- **Score.** One theme, composed to be bright: eight bars of arpeggio, hi-hats and choir with no kick drum, then
  sixteen bars of drop. Three takes; take 1 is used (its drop is exactly on bar 9, 144.016 BPM, the most energy above
  400 Hz). `tools/score_build.py` cuts it to the film: the opening for the hall of wind and, through a television's
  speaker, for 1903; the opening again, softened, under the talk; the theme's own two bars before its drop for the
  kitchen, opening up from far away; the drop on the Enter key (measured: 1 ms from frame 960); a dead stop for the
  whale. A held pad was composed for Casey Harrell's passage. The whale's pads are the ones from the sixth pass, now
  held under the end card and gone before the film loops.
- **Effects.** 95 files made with the newer model (`audio/sfx2/`), each measured on arrival; six are skipped (rumble,
  or the weaker of two). No sound in the film is drawn in arithmetic any more. I drew three on this pass (a heartbeat,
  a television switching off, the engine stopping) and took them out again, with the four older ones (the thump under
  the Enter key and the stamps, the pings under the clicks, the bronze's room): the user rejected synthetic sound on
  10 November. Each was asked of the model again, and what came back is shaped, not replaced: a generated heartbeat
  with its middle brought up so a laptop plays it, a generated motor running down played twice as fast for the
  television's tube, two generated glass chimes tuned by a few cents to an A and a D for the pings. New sounds for the new picture: a
  teleprinter key for each letter of LOGIN, the crash, the power coming back, a slide projector on each of the
  thirteen specimens, a crackle and a stream of blips for the electrodes and the decoder, keys under the typing, a
  whoosh for each hand the baton passes through. Every hit is now placed by its sharpest moment: the clicks, stamps
  and keys measure within a twentieth of a frame of their cues.
- **Mix.** Each voice is evened out before it is mixed (peaks 11 dB over its level, not 16). The voices no longer push
  the whole score down: they open its middle by 7 dB and leave the bass. The ceiling is a look-ahead limiter. Every
  line stands at least 6.5 dB over the bed in the speech band, except the four murmured doubts at the open (3 to 4 dB,
  by design: they are also on screen).
- Mix v011: -14.1 LUFS, loudness range 6.8 LU, peak -2.2 dBFS as measured in the finished file. The limiter takes
  off more than 3 dB for 0.36 percent of the film; the most is 5.7 dB, on the Enter key.

**None of this was heard.** I cannot hear. The music was chosen by maps of level in four bands, by where its beats
fall, and by nothing else; a take that measures well can still be the wrong music. `out/voices_audition.html` plays
the three takes of the theme, the alternates, every effect and the old score for comparison.

**Lyria.** Runway's API has no Lyria model (checked again on this pass), so the Google version cannot be made from
here through Runway. `audio/music/LYRIA_PROMPT.md` is the same brief written to Google's prompt guide, for the user
to paste into Runway's app, with the three commands that cut a returned file into the film. `tools/lyria.py` sends
the same prompt through the Gemini API when `GEMINI_API_KEY` is in `.env`; it has never been run.

## The seventh pass: light, motion, and two lines

The user, after watching v009: "I really don't like the blue square or the blue continued graphic. I think we need to
improve that and make it more futuristic and more dynamic. Also, I want you to review the entire movie again and
improve some of the scripts, some of the transcripts, and some of the transitions, and increase the dynamism and
futuristicism." They did not say which graphic. My reading: every flat cyan rectangle the film drew itself. All of
them are replaced, and the same care went over the whole film.

| Was | Now |
| --- | --- |
| The cursor: a flat cyan block that switched on and off | A small tube of light, the same light as the hall's tubes and the baton: a hot core, a glow, an overshoot as it strikes and an afterglow as it goes. It brightens on each letter it sets down. |
| Clicks with nothing to see | Every click of the cursor sends a ring out from it, at the open and on the end card. The whale's rings in the sky are now the same thing coming back. |
| The block over the bleeped word, on the wall, on the big mouth and in the caption: a flat rectangle | A slab of lit cells that keeps changing, with a band of scan travelling down it, a bright rim and its glow on the wall. It lands large and white-hot. Now and then a slice of it slips. |
| The square that wiped the wall's ink | A blade of light the height of the frame, with its trail and sparks. It passes behind Mara. |
| The bar that shrank into the cursor at the end: a flat rectangle | The baton's own light, white-hot, drawing itself in over six frames with the last frame of the shot fading under it and a ring going out from where it is headed. The cursor comes on with a flare. |
| A cyan square on the end card where the maker's mark goes | Gone. The fifth click still sends its ring. When `clips/mark.png` exists it lands there like a stamp. |
| Stamps and cards that simply appeared | They land: large, then true, in four frames, never past the frame's edge. A second part (THEN CHECKED.) is pressed on from above. The grey guesses have a light passing along them. |
| The sentence decoded from a man's brain typed like any other | The next three letters are still noise, a different guess every frame, until each one settles. |
| The opening's four doubts popped on | They type on. |
| The title on the glass sat still | A glint travels along the lettering, and the shot pushes in. |
| Cuts that just cut | The line-up swaps, the relay inserts and the flood's specimens land a few percent large and settle (not the shots in the round lens: that frame has to stay one size). The Enter key is an impact: a flash and the colours pulled apart for four frames. The 1903 passage ends with its tube switching off. The crash card arrives torn for a frame. |
| Stills that were still | The ink drawings, the card in her fingers, the print and Pip's eye push in slowly. |
| The film's own lights as the lens gave them | The cyan lights of generated shots glow a little further. Never on archive. |

All of it is in `tools/light.py`, and which shot gets what is in `timing/fx.json`.

Two lines are rewritten. Only voice-over and on-screen text can change: lines spoken on camera are locked to mouths.

| Was | Now | Why |
| --- | --- | --- |
| MARA, over the card 69 DAYS LATER.: "Sixty-nine days." | "Close." It is said as the Flyer is in the air. | The voice was reading the card out. |
| MARA, over the whiteboard: "One lab's unpublished result." | "One lab. Ten years. Unpublished." The stamp 10 YEARS. now lands on the word "ten". | Three beats, to set up Jun's "Same idea. Two days." |

Sound added for the new picture: a faint two-note ping under each of the ten cursor clicks (the clicks themselves stay dry), a thump under four stamps, a whoosh under the blade, and the tube switching off at the end of 1903. None of it was heard.

Looked at and left: every other voice-over line. The script was already tight, and the on-camera lines cannot move.

## The sixth pass: the plan, audited again, picture and sound

The shot list the user approved was recovered from this session's own record (the file as it stood nine minutes after
approval) and compared with the cut, shot by shot, on rendered frames. The sound column and the transition column
were checked the same way against the mix and the cut. Four things had been quietly changed since approval and were
put back; the rest of the list below was missing or thin and is now built.

Put back as approved:

| Plan item | Now |
| --- | --- |
| D18: the stamp DECODED. THEN SPOKEN, IN HIS OWN VOICE. | It had become fine print. It is the stamp again, in two parts. |
| G07: a voice says "Vague but exciting." | The line had been dropped. It is performed again, and the four first words now pass from side to side. |
| E05 into F01: the tube blinks out, and the kitchen comes out of black | The tube goes out in the shot's last two frames (the reel's own moment), and F01 opens on three frames of black. |
| D13: text types out a hypothesis | It typed only a label. It now types the hypothesis in the words of the paper that reported it. |

Built on this pass:

| Plan item | Now |
| --- | --- |
| The cursor patch on every jacket's chest | Tracked onto the cloth in every wall shot, and on the jacket on the washing line in H01 (`patch` in `timing/cutin.json`). |
| B01: the hall's lights come on at the drop | New draft `hall_fan`: three frames of black, then the tubes come on pair by pair and the fan shows at the far end. |
| B04: the fan the size of a wall; smoke streamlines | The shot now cuts half-way to the wide hall where the fan fills the end wall. Wind-tunnel smoke flies with the strips, behind her and in front (`tools/wind.py`). |
| B03: her silhouette crosses behind the title glass | It does. |
| B05, D06, E04: the relay itself, a pinpoint cyan spark, the spark matched to the next light | New draft `macro_relay`, three angles, the spark cooled to the film's cyan. Each shot is framed so its spark lands on the next shot's light: a tube (B06), the cap in her teeth (D07), Osei's tube (E05). The click now sounds on the frame the armature lands, not three frames early. |
| B07 to B09: one piece of paper | Her reel shows a card on her cheek and in her hand, and the macro between showed a strip. New draft `macro_card2`: the macro is now the card, lettered in code. |
| B10: the slap on the lens | The reel's own strip flying flat onto the lens; the slap sounds on the frame it lands. |
| C01: the underline | A third stroke carries it on under "years" on the next line. |
| D07: she pulls the cap with her teeth | Her reel's own moment, cut into the front of the shot. |
| D10: a printed photograph of the bronze | The Met's own photograph with the four restored lines in grey, laid on the card she ticks (`tools/printshot.py`). |
| H01: its clicks answer the baton's blink; each click sends a ring | The baton flares two frames before each click; every click heard in the shot now has its ring. |
| H02: the whale crossing the reflection in her eye | A sperm whale drawn in code crosses the sky in her eye (`tools/eyeshot.py`). |
| Red belongs to the pencil alone | Stray reds turned cyan in G15, G28, H01 and H03. |

Sound, built on this pass (none of it was in the mix before):

| Plan item | Now |
| --- | --- |
| DROP 2 on the Enter key | The composed score brought its drop in 30 frames late, and ran its drums 46 frames into the whale. Found by measuring the file. `tools/score_edit.py` takes three beats out before the drop, 20 ms off the front (every hit sat half a frame late), and stops the drums on frame 1260. The first drum hit now measures at frame 960.00. |
| H01: engine off, choir pad, a sub swell | A pad made for the passage (two takes, held voices on D and A, no drums) lies under the whale. The same voices are heard once early, under "a sentence a man could no longer say" (the plan's "held pad" at 0:26.7). |
| A13: one inhale, then nothing for two frames | An inhale after "...a prediction.", cut off; frames 118 and 119 are digital silence; then the drop. |
| B09: her snort, close | The short laugh her own shot carries at that moment. |
| H02: a breath that turns into a laugh | The sound the whale shot itself carries just before Pip's line. |
| C04: wind, thin and old | The fan's wind through a small band, under the flight and the telegram. |
| D08: metal room tone | Drawn in code: high partials that beat slowly. (The sound model answers "silent gallery" with silence.) |
| D16 to D18: room tone only; one breath | The middle of the film had stretches of digital silence. There is now room tone under all of it, and one slow breath that ends on the cut to Ray. |
| G40: kick leaves on the last two beats | The low end is taken out of the score for frames 1240 to 1260. |
| The Enter key's hit | The generated impact was a drone below 60 Hz that held for a second and a half: silent on a small speaker, and it buried the drop on a large one. It is now a tail under a hit drawn in code, with the key's own click. |
| The master | One gain for the whole film and a soft ceiling. The loudness filter used until v008 was turning the quiet middle up by 6 dB and making the first heartbeat after it land too loud. |

Built differently from the plan's wording, and why:

- B01 shows the tube lights coming on, with the fan small at the far end; the wall-sized fan is in the second half of B04 and behind Mara in D07. Five hall drafts were made and none gave both in one frame.
- D08's "spark-to-light match" is carried by the relay cut two shots before it (D06's spark lands on the cap in D07). D08 itself arrives by the scanline roll-in every archive shot has.
- D06's spark lands on the cap between her teeth, not on the ring of light behind her: the ring's centre is behind her head.

Not built, and why:

- D09's "two alternatives, each with a percentage". The paper's figure gives none for this bronze, and nothing is invented on a real document. The only honest source is the published model itself, run on this inscription, which means sending text through a public web form. That needs the user's say-so and has not been done.
- Mara's age (she reads about thirty, the plan says forties), her solder burn, Rosa's apron at the wall. These are inside the reels. Changing them means new reels and new faces.
- B07 and B09 show a card, not a strip. The macro was changed to match the reel, not the reel to match the plan.

## Real archive

In the cut, with its rights record in `archive/rights/` and its row in `archive/manifest.json` (21 items):

- C01, C02: The New York Times, 9 October 1903. C02 also: Langley's Aerodrome in the Potomac, 7 October 1903 (Smithsonian, Langley Memoir, plate 100).
- C04: the first flight, 17 December 1903 (Library of Congress), and the telegram of the same day (Library of Congress, Wright Papers).
- D08, D09, D10: the Met's bronze diploma. G04: Bell's notebook. G05: switchboard operators (National Archives photograph).
- G11: the helicopter's first flight on Mars, filmed by the rover. G12: five frames from the helicopter's own camera on that flight.
- G18: a thruster igniting at NASA Glenn, 2022. G20: Hurricane Dorian from the Space Station, 2019. G26: Hubble's Milky Way bulge.
- G32: the control room after Apollo 11's splashdown, on film. G34: the control room at Perseverance's landing, with its real cheer as sound.

Rights notes that need a person's eye (the records quote every statement):

- G32's film is NASA's and NASA's upload is marked Public Domain, but the reel's description says the high-definition transfer was made by the Discovery Channel. It is kept in the cut on my recommendation; the user has not ruled on it. The same shots from NASA's own server are in `archive/src_new/` (softer by a long way), and the black-and-white still is in `clips/replaced/`.
- G18's record names no photographer. It is in NASA's library with no third-party mark; that NASA shot it is inferred. NASA calls the thruster a Hall-effect thruster for the Gateway station; it is not a gridded ion engine, so the film's words say "thruster".
- G12, G18, G20, G32, G34 and G11 are NASA or JPL: "not subject to copyright in the United States", no endorsement implied, credit asked. G32 and G34 show real, recognisable people at work.
- The telegram in the cut is the Library's black-and-white scan, whose own page carries the public-domain statement. The sharper colour scan's page does not, so it stays out.

In hand, not in the cut (`archive/src_new/`, records in `archive/rights_new/`, summary in `archive/src_new/FOUND.md`): four
more plates of the Aerodrome, the colour telegram, the softer control room film, a JPL ion engine test with words burned
in, the switchboard film, a 1936 film of flow round aerofoils, ten more of the helicopter's frames and a later flight,
a second Hubble field, Bell's telephone patent. Not found anywhere usable: NACA's smoke-tunnel films.

Also heard in the NASA landing clip, and not used: the call "Touchdown confirmed. Perseverance is safely on the surface of Mars..." It would sit on top of "We'll fix it."

## Where each shot comes from

`timing/cutin.json` is the table; `python3 tools/cutin.py` turns it into `clips/manifest.json`.

| Source | Shots |
| --- | --- |
| `mara_reel` (30 s) | A09, A10, A12, A13, D03, D05, D07, E03, B07, B09 |
| `ray_reel` (18 s) | A02, D04, E01, G16, G35 |
| `jun_reel` (12 s) | A05, D01, G15 |
| `osei_reel` (10 s) | A06, E05 |
| `amara_dev_reel` (14 s) | A03, A04, G13, G14 |
| `rosa_pip_reel` (14 s) | A07, A08, F01, F04, G33, and the empty wall used above Ray, Dev and Rosa |
| `hall_fan` (15 s) | B01, and under the wind in the first half of B04 and in B06 |
| `hall_wide` (10 s) | B03, and under the wind in the second half of B04 |
| `macro_relay` (9 s) | B05, D06, E04 |
| `macro_hall` (12 s) | B02 |
| `macro_card2` (5 s) | under the lettering in B08 |
| `macro_hands` (8 s) | under the print in D10 |
| `paper_pickups` (8 s) | B10 |
| `macro_kitchen` (10 s) | F02, F03, F05, G06 |
| `handoff` (10 s) | G36 to G40 |
| `whale_1080` (final, 12 s) | G41, H01, H02, H03 |
| generated stills | G21, G22, G23, G27, G28, G29 |
| navy-ink stills | A11, D12, D13, D14, G01, G07, G08, and `ink_wall` for the wall |
| drawn by code | B04, B06, B08 (`tools/wind.py`); D10 (`tools/printshot.py`); H02 (`tools/eyeshot.py`); D11, G02, G03, G17, G24, G09, G19, G25 (`tools/codeshots.py`) |
| real archive, scanline pass | C01, C02, C04, D08, D09, G04, G05, G11, G12, G18, G20, G26, G32, G34 (`archive/scanline_recipes.md`) |

Drafts not in the cut: `hall_tubes`, `hall_fanwall`, `hall_walk`, `macro_card`, `lineup_t1`, `lineup_fix`, `kitchen_t1`, `whale_t1` to `whale_t3`, and `G21_t1.png`. The archive shots a better source took over are in `clips/replaced/`.
Keep `lineup_t1`, `lineup_fix` and `audio/mix_v004.wav`: the teaser under `out/social/`, made by another session, was built from them. That teaser shows the first draft's faces, not the cast.

## Sound

- Mix v011: -14.1 LUFS, peak -2.2 dBFS in the finished file, loudness range 6.8 LU. One gain of +1.6 dB over the whole film and a look-ahead limiter.
- The score is `audio/music/score_cut2.wav`: the theme (`cue_theme_take1.mp3`) cut to the picture by `tools/score_build.py` from `timing/score.json`. The score until v010 (`score_cut1.wav`) is kept for comparison.
- Effects come from `audio/sfx2/` (the newer model) where a sound is there, and from `audio/sfx/` where it is not (the inhale). Nothing is synthesised. The mix as it was for v010 is kept in `tools/retired/mix_v010.py`.
- Both of Pip's lines, her laugh over her eye and Mara's snort are sound from the generated shots themselves.
- None of the sound was heard. It was measured (levels by stem, by band and by frame, where every hit falls) and transcribed. A person has to listen: `out/voices_audition.html` plays the newest animatic, the four stems, every take of the theme and every effect.

New on the eighth pass and never heard, so the first things to listen for: the whole score (does the theme suit the film; is the opening too busy under the talk at 0:13 to 0:27); the hit on the first music (frame 120); the television switching off (318); the stamps (290, 472, 520, 545); the crackle and the blips under Casey Harrell's sentence (646 to 750) and Mara's new line (694); the heartbeat (750 to 880); the four keys (917 to 923); the riser and the Enter key (919 to 960); the projector on the specimens (1120 to 1185); the teleprinter keys, the crash and the power coming back (1190 to 1214); the title landing (1400).

## Still open

- Nobody has heard the mix or watched the lip sync (measured within 1.2 frames), and nobody has seen the HDR master on an HDR screen.
- The music: whether the theme is right is a judgement for ears. A Lyria version needs the user to make it in Runway from `audio/music/LYRIA_PROMPT.md`, or a Gemini key in `.env`.
- The cut is 98 shots where the approved plan has 100 (the two pairs). If the user wants the four cuts back, the 1969 card goes back to 20 frames.
- D09's alternatives need the user's say-so to query the published model.
- How the film discloses its AI-generated people now that the line is off the end card (see the v014 section).
- The maker's mark for the end card: the user has not said whose it is. Its place is empty until `clips/mark.png` exists.
- The two rights notes (G32's transfer, G18's maker) want a person's decision.
- Faults inside reels, left alone: Mara reads younger than her forties; Pip reads about six in the kitchen.
- G12 plays its five frames faster than they were taken (they were taken at 0, 1, 2, 6 and 11 seconds).
- The first web page is the oldest copy CERN keeps, from 1992.

## Next, in order

1. The user watches `out/first_word_v015_1080.mp4` with sound, and the HDR master on an HDR phone.
2. A decision on how the film discloses its AI-generated people where it runs as an advertisement, on the maker's mark, and on the two rights notes.
3. The user looks at the reel on a phone, inside Instagram, before posting.
