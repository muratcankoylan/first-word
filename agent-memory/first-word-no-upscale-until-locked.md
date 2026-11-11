---
name: first-word-no-upscale-until-locked
description: First Word is now a 1080p film (pass run 11 Nov 2026 on the user's go-ahead); the cast is accepted; a new draft still needs its own go-ahead and has 7 days
metadata:
  type: feedback
---

On the First Word film the user first held the 1080p pass back (10 November 2026: "Let's continue with generations without making them upscale. After finishing the video, we can upscale.") and then released it on 11 November 2026: "I have topped up the runway credits, so you can make the entire movie production-ready." The pass was run that day: all 16 drafts in the cut were finished at 1920 by 1080 (12,920 credits), every made shot was rebuilt at that size, and the film is rendered at 1080p from then on.

In the 10 November message they also accepted the cast that the per-person reels produced ("these generations are great"), so the faces in the cut are not to be rerolled unless they ask.

**Why:** the user gave no reason for holding back. My reading: an upscale costs about 3.4 times a draft per second and locks money into takes that may still be recut. That reason still holds for anything new.

**How to apply:**
- Work at 1920x1080 now. The 1080p version of a draft lives in `clips/final/<name>.mp4` and `tools/conform.py` picks it up by itself (`best()`), so `timing/cutin.json` still names the draft.
- A new generation is still a 480p draft first. Finishing it at 1080p costs money (68 credits a second) and is only possible within 7 days of the draft being made (vendor's notes, `research/runway_api/type_text_to_video_create_params.py.txt` in the project): say so when a new draft joins the cut and ask before spending, as with any money. Until it is finished the shot will be soft beside the rest.
- After any new 1080p clip, run the tools that read drafts again at `--size 1920x1080`: `tools/laptopshot.py`, `tools/diptych.py`, `tools/wind.py`, `tools/printshot.py`, `tools/eyeshot.py`, and `tools/archive_shots.py` for the archive shots.
- Fixing one shot of a person means regenerating that person's whole reel, which changes their face, so leave faults inside a reel alone and list them. See [[first-word-film-project]].
