# The picture the film is built from

| Path | What it is |
| --- | --- |
| `final/` | The sixteen generated takes in the film, finished at 1080p by the video model. A take named `<person>_reel` is one generation job holding all of that person's shots, which is how a face holds without a face reference. The prompt that made each one is in `timing/generations.json` under the same name. |
| `stills/` | Stills the film moves across or draws over: ink drawings and specimen pictures generated as still images, and three cards drawn in code. |
| `*.mp4` | Shots made by the tools: the real archive through its scanline treatment (`tools/archive_shots.py`), shots drawn in code (`tools/codeshots.py`), the paper strips (`tools/wind.py`), and composites. Named by shot. |
| `drafts/` | Two 480p drafts whose own sound is used in the mix (`timing/production_audio.json`), and the records that say each 1080p take finished. The other drafts are not kept here. |
| `manifest.json` | Which file and which moment of it each shot uses. Written by `tools/cutin.py`, read by `tools/conform.py`. |

`tools/conform.py` reads this folder as it is. Remove it and the conform builds the animatic instead: the same
cut, with a card for each shot.
