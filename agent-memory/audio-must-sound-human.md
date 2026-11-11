---
name: audio-must-sound-human
description: The user rejected the first First Word voices as obviously AI and the temp sound as poor; how to make generated audio they accept
metadata:
  type: feedback
---

For generated voices, sound and music, read the vendor's own prompting and model guidance before generating anything, and build for a listener, not for a meter.

**Why:** on 2026-11-10 the user heard the first First Word voices and said "These are real AI voices. You need to write better prompts and use the latest ElevenLabs model", then asked for "much better sound design", better music, and to "use Eleven Labs better". I had picked takes by measurement because I cannot hear, generated lines one at a time, forced the pace and squeezed the audio. ElevenLabs' docs said plainly that text-designed voices are weaker on its newest model.

**How to apply:** cast voices from real recordings (the ElevenLabs Voice Library) rather than designing them from text; generate dialogue as whole scenes with Text to Dialogue so voices answer each other; let the cut follow the performance instead of squeezing audio; never ship numpy beeps as sound design, generate real effects and a score; always give the user a page to listen on and say that nothing was judged by ear. See [[first-word-film-project]] and [[user-delegates-film-decisions]].

A second round, 2026-11-11, after the user heard animatic v010 of First Word: "you can do a better sound design at the sound level with better effects, but also with the background music", with an offer of a Google (Lyria) key, ElevenLabs, or making the music themselves in Runway from a prompt of mine. What measuring then showed (my findings, not their words): the score was 33 seconds of sub bass with almost nothing above 4 kHz; the voices in the loud passage touched full scale into a soft clip; most effects landed two thirds of a frame late.

**How to apply, added:** before any generated music goes into a mix, map it bar by bar in four frequency bands and throw out a take that is only bass; ask for brightness in the prompt and narrate the structure in one plain prompt (a many-section plan with high adherence came back as one groove); place every hit by its sharpest moment and check it against its frame; master with a limiter, not a waveshaper; even out voices before mixing. Do not synthesise a sound, even as a stopgap: I drew three in numpy on that pass and had to take them out, because this user had already rejected that; ask the model again and shape what comes back. When the user names a tool I cannot reach (Lyria is not on Runway's API), write them a prompt file and the commands that cut their result in.
