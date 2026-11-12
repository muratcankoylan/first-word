# The sound

| Path | What it is |
| --- | --- |
| `mix_v015.wav` | The mix. 24-bit, 48 kHz, -14.1 LUFS, range 6.8 LU, true peak -2.1 dBFS. |
| `stems/` | The four stems the mix is the sum of: dialogue, effects, score, whale. |
| `lines/` | Every spoken line as it is cut into the film. The voices are licensed voices from a voice library; each scene was performed as one conversation and cut into lines (`tools/dialogue.py`, `timing/scenes.json`). |
| `sfx2/`, `sfx/` | Every generated sound effect, several takes of each, with what each measured (`sfx2/measured.json`). |
| `music/` | The theme and the pads the score is cut from, and the score cut to the picture (`score_cut2.wav`, written by `tools/score_build.py`). |
| `sfx_real_jpl_cheer.wav` | One real sound: a NASA/JPL control room, 2021. Its rights record is in `archive/`. |

`tools/score_build.py` and `tools/mix.py` rebuild the score, the mix and the stems from this folder, byte for
byte. The whale's clicks are a NOAA recording in `archive/src/`.

Nothing here was judged by ear by the agent that made it. It measured; a person listened.
