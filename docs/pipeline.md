# FIRST WORD

> This is the project's own README as it stood when v015 was delivered. It was written for the working
> folder, so it names paths that are not in this repository: `.env`, `clips/`, `audio/`, `out/`, `archive/src/`,
> `research/`. See the top-level README for what is and is not here. In this repository `STATE.md` is
> `docs/production-log.md`.

A 60-second film: 24 fps, 1,440 frames, 144 BPM (one beat is 10 frames), 100 shots.
The plan the team reads is the doc "First Word: film plan" (https://claude.ai/artifact/1fdqzNz2dYF53g73AMa2at).
This folder is where the film is made. STATE.md says where production stands.

## What is where

| Path | What it is |
| --- | --- |
| `.env` | The API keys. Never committed, never pasted anywhere. |
| `budget.json`, `ledger.csv` | The spending cap (600 USD) and every paid call, logged when it is submitted. |
| `shotlist.py` | The cut. Source of truth for every shot's frames. Run it to rewrite `shotlist.json` and `shotlist.md`. |
| `timing/lines.json` | Every spoken line: start frame, the frame it must end by, caption, and the grey guess. |
| `timing/type.json` | On-screen type that is part of the picture, frame by frame: what it says, when it lands (stamps land large and settle), which clicks send a ring out from the cursor, where the sentence is still being decoded. Also `screen` (a page of type warped onto a drawn screen's four corners), `ghost` (a word standing in grey whose letters turn white as they arrive) and `spikes` (the row of electrodes). |
| `timing/sound.json` | Clicks, kick, cues. |
| `tools/conform.py` | Builds the film from the shot list. A shot comes from `clips/manifest.json`, or from `clips/<ID>.mp4` (or .mov, .png, .jpg) when that file exists, and is a placeholder card otherwise. With no clips it is the animatic. A draft named in `timing/cutin.json` is read at its best: when `clips/final/<name>.mp4` exists (the same take, finished at 1080p) that file is used. It writes HD colour by the HD rule (BT.709) and tags the file so; `--master FILE.mov` also writes ProRes 422 HQ with the sound uncompressed. Captions look at the picture under them: a box on a white frame, a soft shade over a bright thing in a dark one. |
| `tools/tempaudio.py` | Measures every line's length for the captions and writes `out/fit_report.md`. |
| `timing/scenes.json` | The spoken lines grouped into scenes, with spoken directions. |
| `tools/dialogue.py` | Performs each scene as one conversation (ElevenLabs Text to Dialogue, Eleven v4, library voices) and cuts it into lines. |
| `audio/voices/library_cast.json` | The cast: real people's licensed voices from the ElevenLabs Voice Library. |
| `timing/retime.json`, `tools/retime.py` | Pauses lengthened inside a finished line so it matches the mouth in a generated shot. |
| `tools/voices.py` | Helpers the other sound tools share (API calls, transcription, measuring). Its voice-design stages and `timing/voices.json` are retired. |
| `timing/sfx.json` | Prompts for every sound effect (`sfx`, and `sfx2`: the same sounds made again with the newer effects model), and for the music: the cues the score is cut from (`cues`), the whale's pad (`pad`), and two plans that were measured and not used (`score`, `score2`). |
| `tools/sound.py` | Generates the sound effects, the cues of the score and the pad under the whale, and measures each file as it arrives (how long the sound is, where its energy sits, whether it is only rumble). |
| `timing/score.json`, `tools/score_build.py` | The score, cut to the picture from one theme: which bars play where, at what level, and where the theme's bar lines were measured to be. Writes `audio/music/score_cut2.wav`, 60 seconds long with film frame 0 at its start, which the mix plays. `--map FILE` prints any piece of music bar by bar and finds its drop. |
| `audio/music/LYRIA_PROMPT.md`, `tools/lyria.py` | The same theme briefed for Google's Lyria: a prompt to paste into Runway's app, how to cut the result into the film, and a tool that sends it through the Gemini API once `GEMINI_API_KEY` is in `.env` (never run: there is no key). |
| `tools/score_edit.py` | Retired with v010. It cut the first score (`score_cut1.wav`), which measured as sub bass and little else. Kept, with `tools/retired/mix_v010.py`, so that v010 can be rebuilt. |
| `tools/mix.py` | The mix: dialogue, effects, score and whale stems, mastered to -14 LUFS by one gain and a look-ahead limiter. Places every hit by its sharpest moment, evens each voice out before mixing, and opens the middle of the score where a voice is speaking. Writes 24-bit files (the mix and the four stems in `audio/stems/`). |
| `timing/production_audio.json` | Sound taken from a generated shot: both of Pip's lines, her breath and laugh over her eye, and Mara's snort. |
| `tools/audition.py` | Writes `out/voices_audition.html`, a page that plays the newest animatic, the stems, every take of the theme and its alternates, every effect, the cast and every scene take. |
| `tools/keys.py` | Reads `.env` for the other tools without printing a value. |
| `timing/characters.json` | One fixed description per person, pasted word for word into every prompt that shows them. |
| `timing/generations.json` | Every paid picture job, with the prompt that ran. |
| `tools/runway.py` | Runs a job on Runway (Seedance 2.5 video, image models), downloads the result and logs the cost. Refuses a job that would pass the spending limit. |
| `tools/checkclip.py` | Looks at a generated clip without playing it: a timed contact sheet, the cuts, and every word heard. Writes to `out/check/`. |
| `timing/cutin.json`, `tools/cutin.py` | Which clip each shot comes from, and how it is framed and finished: a punch-in, a person moved to stand level in the line-up, the cursor patch tracked onto a jacket, a dark shot lifted, a slow push, a cut inside the shot, a whip tilt, an impact, a stray red turned cyan, a ring across the water for each click, a blink on the baton. The tool sets each in-point so the mouth lands on the finished voice line, reports the slip in frames, and writes `clips/manifest.json`. |
| `tools/light.py` | The cursor and its family, drawn as light: the cursor is a small tube with a glow, every click sends a ring out from it, the block over a word is a slab of lit cells that keeps changing, the wipe is a blade of light that passes behind people, and the baton's light draws itself in to the cursor at the end. Also the whole-frame looks: an impact, a picture slipping, a tube switching off, a glow on the film's own lights. Nothing cyan in the film is a flat rectangle any more. Since the eighth pass also a row of slits of light, one for each electrode, that fires as a sentence is read from it. |
| `timing/fx.json` | What a shot's whole frame gets once its picture and type are down: a punch on the cut, a slow push so that no shot is a still, an impact, a tube switching off, a glow on generated shots. Never anything on archive except its own tube switching off. |
| `clips/mark.png` | Not there yet: the maker's mark. When this file exists it lands on the end card with the fifth click. Until then its place is empty. |
| `tools/scanlines.py` | The scanline pass: turns a real archive still or film clip into a shot. `--marks` adds the red wax pencil over it (an underline, a ring). |
| `tools/archive_shots.py` | Every real archive shot made again at any size, from recipes that run: the crops are in each source's own pixels, so the scanlines are drawn at the size asked for, not enlarged. `--check` rebuilds each at 720p and compares it with the shot in `clips/`. It holds the two recipes that were never written down (the Flyer and the bronze), recovered by matching the finished shots against their sources. |
| `tools/codeshots.py` | Draws the shots that are code: the radial tree, the protein ribbon, the spectrogram of the real whale clicks, the first web page from its own text, the white specimen plates. |
| `timing/wind.json`, `tools/wind.py` | The wind: about two hundred paper strips and wind-tunnel smoke flown through the hall in 3D over the plates for B04 and B06, behind and in front of her, a few strips close enough to read; and the type laid on the card in her fingers (B08), tracked to its four corners. Every printed text is in the plan's source table. The shutter is half open, as a film camera's is, so the words and the year on a turning strip stay readable. |
| `tools/printshot.py` | D10: the Met's own photograph of the bronze, with the four restored lines in grey, laid on the card the hand ticks. Writes `clips/D10.mp4`. |
| `tools/eyeshot.py` | H02: a sperm whale drawn in code crosses the sky reflected in Pip's eye. Writes `clips/H02.mp4`. |
| `tools/laptopshot.py` | F03: the words "dumb question:" on the kitchen laptop. They are in the generated video itself (`clips/drafts/macro_screen.mp4`); the tool punches in, gives the cursor's block the film's cyan, and types the last four letters by covering the untyped ones with the frame's own page. The block is drawn as light (cyan at its edge, nearly white at its heart, a glow on the page). Writes `clips/F03.mp4`. Reads the draft at its best, so it works from the 1080p version; `--size` sets the output. |
| `tools/diptych.py` | G32 and G33: two pictures in one frame. The two control rooms (1969 and 2021) side by side, each through the scanline pass at its own size and each on a tube of its own; Rosa beside Ray. Writes `clips/G32.mp4` and `clips/G33.mp4`. Reads drafts at their best; `--size` sets the output. |
| `tools/hdr.py` | An HDR version of the cut (10-bit HEVC, HLG) in which only the film's own lights are brighter than white: the cursor, its rings, the tube lights, the baton, a word that lands hot. Everything else sits where a standard picture sits inside HDR. Archive footage and the ink drawings are never lifted. `--sheet` shows which pixels it picks. Nobody on the making side has seen its output on an HDR screen. |
| `fonts/` | The film's typefaces, all under the SIL Open Font Licence, each with its licence text: Barlow Condensed (captions, stamps), Libre Baskerville (the sentence, quotes), Courier Prime, IBM Plex Mono, Kalam (handwriting), Kaushan Script (the title), Cinzel (the Roman restoration). |
| `timing/ink.json`, `tools/inklayer.py` | The ink on the line-up wall: every mouth, the skull and the four doubts, where each sits and the frames it is there. The conform multiplies it onto the picture. |
| `tools/social_clip.py` | Makes a short clip of the cut for a social post from a frozen recipe folder, so the clip stays the same while the film changes. Writes only under `out/social/`. |
| `tools/process_figures.py` | Four figures of how the film was made, set as a research paper sets its figures (`out/process/figure_1.png` to `figure_4.png`): the brief, the persona and the plan; generation; the edit as code; the checking loop. Built only from the project's own material. |
| `timing/reel.json`, `tools/reel.py` | The film for Instagram Reels: 1080 by 1920, the picture in the middle 4:5 (what the feed shows of a reel), every shot re-framed by hand (a window on the subject, type set again where it was too wide, archive on a tube of the new shape, two-picture frames stacked), and the captions set again on the vertical frame, clear of the app's buttons. `base` renders each shot without captions to `clips/reel/base/`; `sheet` shows every shot with the safe zone drawn; `render` writes the reel (`--hdr` for the HDR one). |
| `timing/wind_reel.json` | The paper-strip shots for the reel: the lettered strips brought into the middle of the frame and stacked above and below her. `tools/wind.py --spec timing/wind_reel.json --outdir clips/reel B04 B06` makes them. |
| `persona/` | The persona prompt the film was written from (3,801 words) and its tuning notes, written on 10 November 2026 from the director's brief for the filmmaker. |
| `out/social/` | Clips for posts. `teaser_v1.mp4` is the opening line-up and the whale ending; `teaser_v1_src/` is its recipe, with its own copies of the clips it plays. |
| `refs/` | Reference images for places and props, with no words and no faces, and padded voice references. |
| `clips/` | Picture. `clips/<ID>.mp4` is a finished shot; `clips/drafts/` holds generations (480p) and `clips/final/` the same takes finished at 1080p; `clips/stills/` holds generated stills; `clips/replaced/` keeps the archive shots that a better source took over, and in `clips/replaced/720p/` the made shots as they were before the 1080p pass; `clips/manifest.json` is written by `tools/cutin.py`. |
| `archive/` | Real public-domain sources with a rights record for each. `archive/manifest.json` is the index. `src/` and `rights/` hold what the cut uses or has used; `selects/` holds the few frames chosen from a film; `src_new/` and `rights_new/` hold what was found and is not in the cut. |
| `out/` | Renders and reports: the animatic, its contact sheet, `fit_report.md`, `read_report.md`, `check/`. |
| `research/` | Captured pages behind the tool rules (Seedance 2.5 on Runway, the provider's rule on faces, voices) and the fact-check. |

The reference studies (Passion Never Sleeps, the four reference films, the persona notes) are not in this folder. They
were made earlier in the same session and stayed in that session's own folder. Both studies are also published pages:
https://claude.ai/artifact/Mc9ocqCtWWfJmTq7jPjGzX and https://claude.ai/artifact/FPT51pCMxJSEG1TAECA11a.

## Rebuild

```bash
python3 shotlist.py
python3 tools/retime.py             # only after tools/dialogue.py has recut a line it names
python3 tools/cutin.py              # in-points and lip sync; writes clips/manifest.json
python3 tools/tempaudio.py          # measures line lengths for the captions and the fit report
python3 tools/archive_shots.py --size 1920x1080   # only when an archive shot changes
python3 tools/codeshots.py --size 1920x1080        # only when a code shot changes; writes clips/G02.mp4 and the rest
python3 tools/wind.py --size 1920x1080             # only when the strips or their plates change; writes clips/B04.mp4, B06.mp4, B08.mp4
python3 tools/printshot.py --size 1920x1080        # only when D10 changes
python3 tools/eyeshot.py --size 1920x1080          # only when H02 changes
python3 tools/laptopshot.py --size 1920x1080       # only when F03 or its draft changes
python3 tools/diptych.py --size 1920x1080          # only when G32, G33 or their sources change
python3 tools/score_build.py        # only when the theme, a pad or timing/score.json changes; writes audio/music/score_cut2.wav
python3 tools/mix.py --out audio/mix_v015.wav
# the film: the standard master, and the same frames as ProRes
python3 tools/conform.py --out out/first_word_v015_1080.mp4 --master out/first_word_v015_1080_prores.mov --size 1920x1080 --audio audio/mix_v015.wav --clean --crf 14 --preset slow
# the HDR master
python3 tools/hdr.py --size 1920x1080 --out out/first_word_v015_1080_hdr.mp4 --audio audio/mix_v015.wav
# a small copy with shot names and frame numbers burnt in, for notes
python3 tools/conform.py --out out/animatic_v015.mp4 --audio audio/mix_v015.wav
# the reel (Instagram): base clips, then the vertical film; --hdr for the HDR one
python3 tools/wind.py --size 1920x1080 --spec timing/wind_reel.json --outdir clips/reel B04 B06
python3 tools/reel.py base
python3 tools/reel.py render --out out/first_word_v015_reel.mp4
```

The archive shots are made by `tools/archive_shots.py`, which calls `tools/scanlines.py` once for each part of a shot. The command that first made each one is in `archive/scanline_recipes.md`, including the two that hold a cut inside them (C02, C04) and the two that play a few chosen frames of a film (G12, G18).

Needs Python 3 with Pillow, numpy, scipy and OpenCV, and ffmpeg. `--clean` drops the burn-in. `--size 1920x1080` renders larger.

A new generation: add the job to `timing/generations.json`, run `python3 tools/runway.py run <job>`, then
`python3 tools/checkclip.py clips/drafts/<job>.mp4`, look at the sheet, and add its shots to `timing/cutin.json`.
It is a 480p draft. To finish it at 1080p add a job `<name>_1080` whose body is `{"model": "seedance2_5", "draftTaskId": <the draft's task id>}` and whose `out` is `clips/final/<name>.mp4` (68 credits a second of the whole draft, and only within 7 days of the draft being made); the conform then uses it by itself.

## Rules that do not bend

- Nothing is filmed and nothing is licensed. Picture is generated, drawn in code, or real public-domain archive.
- Everything real takes the scanline pass, and nothing else does. Real events are never re-staged with generated people.
- Real people only say what they are on record as saying. Their words carry a source line.
- No paid call may take `ledger.csv` past the cap in `budget.json`.
- No face goes into the video model as a reference, still or clip, even one the model made. The provider refuses it,
  and the refusal is not worked around. A face is held by generating all of a person's shots in one job (that
  person's reel) from the fixed description in `timing/characters.json`.
- Every typeface in the film is open-licence and lives in `fonts/` with its licence. Only the burn-in on the animatic uses a system font. Names take their proper accents (José Penadés, Erdős).

## Disk

About 42 GB free on 10 November 2026. Renders are piped straight into ffmpeg; nothing writes image sequences.
Drafts are deleted once a take is chosen, except those a clip under `out/social/` keeps its own copy of.
