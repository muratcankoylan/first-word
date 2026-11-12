# The film

| File | What it is |
| --- | --- |
| `first_word_1080.mp4` | The standard master. 1920 by 1080, 24 fps, H.264 High at about 12 Mbit/s, BT.709, AAC sound. |
| `first_word_1080_hdr.mp4` | The HDR master. 10-bit HEVC in HLG (BT.2020). Only the film's own lights are brighter than white; the brightest reaches 784 nits. Checked by its levels only: the agent cannot see an HDR screen. |
| `first_word_vertical.mp4` | The vertical version for phones. 1080 by 1920, re-framed shot by shot (`timing/reel.json`, `tools/reel.py`). |
| `first_word_vertical_hdr.mp4` | The vertical version in HDR. |

All four carry the same mix: -14.1 LUFS, true peak -2.1 dBFS.

`first_word_1080.mp4` rebuilds from this repository, byte for byte on the machine it was made on. The command is
in the top-level README under "Reproducing". The ProRes master (1.1 GB) is not in the repository.

The people in the film are generated. The archive footage is real. See `NOTICE.md` for whose work is in it and
`LICENSE-CONTENT.md` for what you may do with it.
