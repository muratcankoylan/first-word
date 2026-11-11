# Skills, tools and services the agent used

Nothing here is copied from anyone else. Each entry says what the thing did in this production and where to get
it. Their licences and terms are their own.

## Skills

A skill is a set of instructions (and sometimes a small program) that the agent loads for one kind of task.

| Skill | What it did here | Where it is |
| --- | --- | --- |
| **rea-video** | Took five films apart shot by shot: the team's earlier 60-second film and four references. It measures frame rate, cuts, text, tempo and sound, guesses how each shot was made, and asks the agent to review every shot by eye and merge its answers. The agent overrode its first guess on the team's film after looking at the frames. | https://github.com/JuneYaooo/rea-video (third-party; the agent read its code before installing it) |
| **Deep research** (Parallel) | One research run on the canon behind the persona: the books, the techno-optimist essays, the music. Its report came back with sources and per-section confidence; the persona notes say which parts it did not cover. | https://parallel.ai (its CLI and Claude Code plugin) |
| **Web search and page extraction** (Parallel) | Reading the vendors' own documentation (the video model's prompt guide and its rule on faces, the voice vendor's model guidance), and checking the film's factual claims against sources. | same |
| **Docs** (Claude's document connector) | The plan: one shared document with three tabs (treatment, shot list, prompts), kept in step with the cut for two days. Exported here as [docs/plan/](../docs/plan/). | part of Claude |
| **Artifacts** | The two studies as private pages for the team. Their text is in [docs/reports/](../docs/reports/). | part of Claude |
| **Data visualisation** | The rules behind the charts in the four process figures: a validated palette, thin marks, one axis, text never in a data colour. | bundled with Claude Code |

## What is not a skill, but did the same job

| Thing | What it did here |
| --- | --- |
| **Subagents** | Side work with its own written brief: reading a vendor's documentation, verifying historical facts, finding public-domain archive, exporting documents. The main agent checked what each one saved, not just its summary (one early report said "could not verify" about pages it had in fact captured). |
| **Learned rules** | Corrections from review, written down once and loaded into every later context window. See [docs/learned-rules.md](../docs/learned-rules.md). |
| **The project's own files** | `STATE.md`, the pipeline README and the timing data did more to keep the work coherent than any skill. See "State across context resets" in [docs/method.md](../docs/method.md#state-across-context-resets). |
| **The persona prompt** | Written by the agent from the director's brief, then adopted as its working role for the film. See [persona/](../persona/). |

## Services (paid, with the director's keys)

| Service | Used for | Called from |
| --- | --- | --- |
| **Runway** (Seedance 2.5) | Every generated shot: 480p drafts, then the chosen takes finished at 1080p. | [tools/runway.py](../tools/runway.py) |
| **ElevenLabs** | Voices from the Voice Library, scenes performed with Text to Dialogue, sound effects, the theme the score is cut from, and transcription for checking words and lip sync. | [tools/dialogue.py](../tools/dialogue.py), [tools/sound.py](../tools/sound.py), [tools/voices.py](../tools/voices.py) |

## Local tools

ffmpeg, and Python 3 with Pillow, numpy, scipy and OpenCV. Everything in [tools/](../tools/) was written during
the production for this film.

## What the agent could not do

- Hear. Every statement about sound in this repository rests on measurement, and on a person listening.
- See an HDR screen, or the film inside a phone app. The HDR master was checked by its levels only.
- Use a face as a reference for the video model. The provider refuses it, and that was not worked around.
