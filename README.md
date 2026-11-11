# FIRST WORD: how one conversation made a one-minute film

FIRST WORD is a 60-second film about AI and the future: 98 shots, 24 frames a second, cut to a 144 BPM grid.
Nothing in it was filmed. One AI agent (Claude Fable 5.2, running in Claude Code) planned it, wrote it, generated
or found every picture, cast and directed the voices, built the sound, and cut it in Python. One person stayed in
the loop: 40 messages over two days.

This repository is everything behind the film except the media itself: the conversation, the persona prompt, the
plan, the research reports, the code, the timing data, the rights records, the agent's notes to itself, and the
spending ledger.

![Every shot of the film, in order](docs/figures/all_98_shots.jpg)

## Start here

| If you want | Read |
| --- | --- |
| The whole method on one page | [docs/workflow.md](docs/workflow.md) |
| What was actually said, by whom, in order | [conversation/](conversation/) |
| The persona prompt and how to tune it | [persona/](persona/) |
| The plan the film was built from | [docs/plan/](docs/plan/) (treatment, shot list, prompts) |
| The two studies the plan stands on | [docs/reports/](docs/reports/) |
| The code that makes the film | [tools/](tools/), described in [docs/pipeline.md](docs/pipeline.md) |
| The cut as data | [shotlist.py](shotlist.py), [timing/](timing/) |
| What went wrong and how it was fixed, pass by pass | [docs/production-log.md](docs/production-log.md) |
| What each tool or skill did, and where to get it | [skills/README.md](skills/README.md) |
| What the agent wrote down to remember | [agent-memory/](agent-memory/) |
| What it cost | [ledger.csv](ledger.csv), [budget.json](budget.json) |

## The film in numbers

| | |
| --- | --- |
| Length | 60 seconds, 1,440 frames, 98 shots (46 of them last five frames) |
| Where the pictures come from | 41 shots generated video, 16 generated close-ups, 13 real public-domain archive, 20 drawn in code, 8 ink over picture (by each shot's main source) |
| Video model | Seedance 2.5 on Runway: 480p drafts, then the chosen takes finished at 1080p |
| Voices, effects, music | ElevenLabs: real people's licensed voices from the Voice Library, each scene performed as one conversation; generated effects; one generated theme cut to the picture |
| Code | About 8,200 lines of Python in `tools/` and `shotlist.py` |
| Versions | 15, each one rendered, looked at as frames, measured, and corrected |
| Spent | 199.85 USD on Runway against a 600 USD cap; voices and sound on an existing ElevenLabs plan |
| The person's part | 40 messages: a brief, a persona, the keys, the money, and notes after watching and listening |

## How it was made, briefly

![Figure 1](docs/figures/figure_1.png)

1. **Take a film apart.** The agent reverse-engineered a 60-second film the team had made before (88 shots), then
   four reference films, shot by shot, with a video-analysis skill and its own eyes on the frames.
2. **Write a persona.** The person asked for a persona prompt for the film's maker. The agent researched the canon
   behind it and wrote a 3,800-word prompt with six dials. The person handed it back with a brief: you are this,
   and more.
3. **Plan before generating anything.** A treatment, a 100-row shot list and the prompts, in one shared document.
   The person approved it, set a spending cap, and said: you decide everything after that.
4. **Build an animatic first.** The cut exists as code (`shotlist.py`). The conform builds the film from it with a
   placeholder card for any shot that has no picture yet, so there is a watchable film from the first hour.
5. **Fill it in.** Generated shots (one job per person, so a face holds without using a face as a reference),
   real archive with a rights record for each source, shots drawn in code, voices, effects, score.
6. **Look, measure, fix.** Every version was rendered, cut into contact sheets, and read as still frames. The
   agent cannot hear, so sound was checked by measurement and the person listened. Fifteen rounds.
7. **Finish.** A 1080p pass, an HDR master, a vertical version for phones, and figures of the process.

[docs/workflow.md](docs/workflow.md) has each stage with the files it left behind, and the loops in detail.

![Figure 3](docs/figures/figure_3.png)

## What is not here

- **The film files, clips, audio and generated footage.** They are large, and generated media is not something
  another run would reproduce: the video and voice models do not return the same take twice.
- **The archive source files.** Every one is public domain and is listed in
  [archive/manifest.json](archive/manifest.json) with where it came from and the holder's own rights statement.
  Fetch them from the holders.
- **API keys.** Copy [.env.example](.env.example) to `.env` and add your own.
- **Third-party skills and documentation.** They are linked in [skills/README.md](skills/README.md), not copied.
- **The agent's private reasoning and raw tool output.** The conversation record keeps what each side wrote for
  the other, and one plain line for each thing the agent did. [conversation/export.py](conversation/export.py)
  says exactly what is kept, left out and changed, and is the script that made the record.

## Running the code

The tools need Python 3 with Pillow, numpy, scipy and OpenCV, and ffmpeg. They were written and run on macOS.

```bash
python3 shotlist.py
mkdir -p out
python3 tools/conform.py --out out/animatic.mp4
```

With no clips at all, that builds the animatic: the whole 60-second cut at 1280 by 720, silent, with a card for
each of the 98 shots and the captions and on-screen type drawn over it. This was checked from a clean copy of this
repository (about three minutes). The cards and the strip of shot names along the top are set in a macOS system
font; on another system, point `F_UI` at the top of `tools/conform.py` to a font you have. `tools/process_figures.py`
also uses macOS fonts. Nothing else was tested off macOS.

Everything past the animatic needs media you generate or fetch yourself, and paid calls need your own keys.
[docs/pipeline.md](docs/pipeline.md) lists every tool and the full rebuild order.

This is the record of one production, not a framework. The code was written for this film and is published so the
method can be read, checked and borrowed from.

## Rules the production kept

- Nothing filmed, nothing licensed: picture is generated, drawn in code, or real public-domain archive.
- Everything real takes one visual treatment (scanlines) and nothing else does. Real events are never re-staged
  with generated people. Real people only say what they are on record as saying.
- No paid call may take the ledger past the cap. Every paid call is logged when it is submitted.
- No face goes into the video model as a reference. The provider refuses it and the refusal is not worked around.
- The agent says what it could not check. It cannot hear and cannot see an HDR screen: sound and HDR were verified
  by measurement only, and a person had to listen and watch.

## Licence

- Code (`tools/`, `shotlist.py`, `conversation/export.py`): MIT, see [LICENSE](LICENSE).
- Everything written or drawn for the project (documents, persona, plan, conversation, timing data, figures):
  CC BY 4.0, see [LICENSE-CONTENT.md](LICENSE-CONTENT.md).
- Fonts, archive records and anything else from other people: see [NOTICE.md](NOTICE.md).
