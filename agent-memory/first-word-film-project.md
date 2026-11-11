---
name: first-word-film-project
description: "The user's one-minute AI and futurism film \"First Word\": where the project folder and plan live, the approved budget, and the production constraints set on 2026-11-10"
metadata:
  type: project
---

"First Word" is a 60-second film about AI and futurism that the user's startup is making, modelled on their Toronto Maple Leafs film "Passion Never Sleeps" (which they made and I reverse-engineered with the rea-video skill at ~/rea-video).

The project folder is ~/first-word-film (the session moved there on 2026-11-10). Start by reading STATE.md and README.md in it: they hold what is done, what was decided and what is next. The plan the team reads is a Claude Docs artifact, "First Word: film plan" (https://claude.ai/artifact/1fdqzNz2dYF53g73AMa2at), with three tabs: Treatment, Shot list, Prompts.

Constraints the user set on 2026-11-10:
- I am responsible for producing everything: code, image, video and voice generation. Nothing is filmed.
- Tools: Seedance 2.5 on Runway and ElevenLabs voices. The keys go in first-word-film/.env (RUNWAYML_API_SECRET, ELEVENLABS_API_KEY), added by the user. Never print or repeat their values.
- Spending cap of 600 USD approved on 2026-11-10 (about 500 Runway, 100 voices and music). Every paid call is logged in ledger.csv.
- No licences will be obtained. I use public-domain archive only and rebuild restricted items in type, ink or code with short sourced quotes. I told the user I would not lift copyrighted clips.
- Later on 2026-11-10 the user asked for more real archive in the cut ("use more archived images, videos, and clips") and for the plan to be followed and everything in it built. My reading, not their words: real film replaces a still only when its rights record quotes the holder's own statement; a source with a weak record stays out and is flagged to the user, because rights are theirs to decide.

Two limits that shape how I work on it:
- I cannot hear audio. Timing is checked by measurement; a person has to listen. Say so rather than claim the sound works.
- Disk was tight when the project began (about 6 GB free); about 39 GB were free by the evening of 2026-11-10. Still pipe frames into ffmpeg and never write image sequences.

**Why:** the user wants a film that goes viral and gets shared; they have no production crew for this and no rights budget.

**How to apply:** keep shotlist.py, the timing files and the doc in step whenever the cut changes. See [[user-delegates-film-decisions]] and [[read-subagent-raw-outputs]].
