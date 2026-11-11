# Scanline recipes

The command that made each archive shot, so any of them can be made again at another size (`--size 1920x1080`).
Crops are in the source's own pixels: left, top, width. Marks are the red wax pencil, drawn over the scanlines.

```bash
A=archive/src
python3 tools/scanlines.py $A/C01_nyt-1903-10-09_p6.jp2 clips/C01.mp4 --frames 35 --start 2940,2800,1100 --end 2975,2872,1050 --marks '[{"kind":"line","a":[3250,3153],"b":[3520,3153],"from":3,"to":8},{"kind":"line","a":[3520,3153],"b":[3902,3154],"from":8,"to":26},{"kind":"line","a":[3066,3210],"b":[3184,3209],"from":28,"to":33}]'
python3 tools/scanlines.py $A/C01_nyt-1903-10-09_p6.jp2 clips/C02.mp4 --frames 15 --start 2150,250,2600 --end 2420,250,2330 --marks '[{"kind":"ellipse","c":[4252,560],"r":[415,82],"from":2,"to":12,"width":11}]'
python3 tools/scanlines.py $A/D08_met-23.160.52_DP105609.jpg clips/D09.mp4 --frames 20 --start 1000,400,3000 --end 1060,430,2900 --marks '[{"kind":"text","text":"DIVI·NERVAE·F·NERVA","at":[2455,812],"cap":168,"pitch":176,"from":2,"per_frame":2},{"kind":"text","text":"PTIMVS·AVG·GERM","at":[2505,1092],"cap":172,"pitch":176,"from":6,"per_frame":2},{"kind":"text","text":"TIFEX·MAXIM·TRIBV","at":[2565,1376],"cap":172,"pitch":176,"from":10,"per_frame":2},{"kind":"text","text":"T·  XVIII","at":[2690,1642],"cap":168,"pitch":176,"from":14,"per_frame":2}]'
python3 tools/scanlines.py $A/G04_bell-notebook-1876-03-10_loc-magbell-25300201-0022.tif clips/G04.mp4 --frames 10 --start 2150,180,1900 --end 2480,242,1300
python3 tools/scanlines.py $A/G05_switchboard-operators_nara-1633445_86-WWT-28-3.jpg clips/G05.mp4 --frames 5 --start 250,500,2500 --end 330,560,2360
python3 tools/scanlines.py $A/G11_ingenuity-first-flight_mastcam-z_liftoff.mp4 clips/G11.mp4 --at 8.0 --frames 5 --start 436,470,400 --end 440,462,392
python3 tools/scanlines.py $A/G12_ingenuity-shadow-navcam_PIA24584.tif clips/G12.mp4 --frames 5 --start 0,60,640 --end 16,69,608
python3 tools/scanlines.py $A/G18_ion-engine-deep-space-1_PIA04238.jpg clips/G18.mp4 --frames 5 --start 0,420,1897 --end 60,454,1777
python3 tools/scanlines.py $A/G20_hurricane-matthew-2016-10-04_terra-modis_GSFC_20171208_Archive_e000205.jpg clips/G20.mp4 --frames 5 --start 400,640,3000 --end 520,708,2760
python3 tools/scanlines.py $A/G26_sagittarius-star-cloud_hubble-heritage_stsci-1998-28d_1024.jpg clips/G26.mp4 --frames 5 --start 0,216,1024 --end 24,230,976
python3 tools/scanlines.py $A/G32_apollo11-mocr-celebration_S69-40023.jpg clips/G32.mp4 --frames 5 --start 0,1500,2629 --end 70,1540,2489
python3 tools/scanlines.py $A/G34_perseverance-landing_jpl-control-room.mp4 clips/G34.mp4 --at 6.2 --frames 5 --start 0,0,1280 --end 20,11,1240
```

C04 (the 1903 flight) and D08 (the bronze) were made on the first day; their commands were not kept.

D09's letters are the restoration printed in the Aeneas paper's Fig. 1 (research/aeneas/fig1_restoration.md), set at the
bronze's own letter height (about 170 pixels) and pitch (about 176), each line starting just past the break. The photograph
ends at x 4000, so the frame cuts each line after eight or nine letters.

Where the marks sit: the phrase "from one million to ten million" is on one line of the fourth column, x 3250 to 3900,
with its baseline near y 3142; the masthead date "OCTOBER 9, 1903." is at x 3904 to 4600, y 529 to 587. G11 is taken at
8.0 s, where the helicopter leaves the ground. G34 is taken at 6.2 s, where the room jumps; the first four seconds of
that file are NASA's animation of the landing and are not used.

## Added on the fifth pass (10 November 2026)

Two shots now hold a cut inside them (C02, C04), and two are made from a few chosen frames of a film (G12, G18).
The chosen frames are kept in `archive/selects/` so the shot can be made again at another size. Run from the
project folder.

```bash
A=archive/src; S=archive/selects; T=$(mktemp -d)

# C02: eight frames of the masthead with its date ringed, then seven of Langley's Aerodrome in the Potomac
python3 tools/scanlines.py $A/C01_nyt-1903-10-09_p6.jp2 $T/c02a.mp4 --frames 8 --start 2150,250,2600 --end 2300,250,2450 --marks '[{"kind":"ellipse","c":[4252,560],"r":[415,82],"from":1,"to":6,"width":11}]'
python3 tools/scanlines.py $A/C02_langley-aerodrome-1903-10-07_pl100_wreck-in-water_sck27-p0721.jp2 $T/c02b.mp4 --frames 7 --start 330,2190,1640 --end 400,2230,1500 --roll --roll-frames 2
ffmpeg -v error -y -i $T/c02a.mp4 -i $T/c02b.mp4 -filter_complex "[0:v][1:v]concat=n=2:v=1[v]" -map "[v]" -c:v libx264 -crf 12 -pix_fmt yuv420p -r 24 clips/C02.mp4

# C04: seventeen frames of the Flyer (clips/C04_flight_only.mp4, made on the first day), then eight of the telegram
python3 tools/scanlines.py $A/C04_wright-telegram-1903-12-17_loc-wright-papers-02039-0034.tif $T/c04b.mp4 --frames 8 --start 40,800,900 --end 52,838,770 --roll --roll-frames 2 --marks '[{"kind":"line","a":[76,1018],"b":[250,1018],"from":2,"to":6,"width":8}]'
ffmpeg -v error -y -i clips/C04_flight_only.mp4 -frames:v 17 -c:v libx264 -crf 12 -pix_fmt yuv420p $T/c04a.mp4
ffmpeg -v error -y -i $T/c04a.mp4 -i $T/c04b.mp4 -filter_complex "[0:v][1:v]concat=n=2:v=1[v]" -map "[v]" -c:v libx264 -crf 12 -pix_fmt yuv420p -r 24 clips/C04.mp4

# G04: Bell's own hand, "Mr. Watson" and "come here" underlined
python3 tools/scanlines.py $A/G04_bell-notebook-1876-03-10_loc-magbell-25300201-0022.tif clips/G04.mp4 --frames 10 --start 2540,140,1500 --end 2690,230,1350 --marks '[{"kind":"line","a":[3060,613],"b":[3400,611],"from":1,"to":4,"width":10},{"kind":"line","a":[3545,611],"b":[3905,608],"from":5,"to":9,"width":10}]'

# G12: the first five frames the helicopter's own camera took on its first flight, one to a film frame
mkdir -p $T/g12; i=0; for f in $A/G12_ingenuity-flight1-navcam_f0[1-5]_*.png; do i=$((i+1)); cp "$f" $T/g12/$i.png; done
ffmpeg -v error -y -framerate 24 -i $T/g12/%d.png -c:v libx264 -crf 4 -pix_fmt yuv444p $S/G12_navcam-first-flight_5-frames.mp4
python3 tools/scanlines.py $S/G12_navcam-first-flight_5-frames.mp4 clips/G12.mp4 --at 0 --frames 5 --start 0,50,640 --end 8,55,624

# G18: the thruster lighting, five frames taken at 0.90, 1.05, 1.20, 1.40 and 1.60 s (the clock in the corner is cropped off)
mkdir -p $T/g18; i=0; for t in 0.90 1.05 1.20 1.40 1.60; do i=$((i+1)); ffmpeg -v error -y -ss $t -i $A/G18_hall-thruster-ignition_nasa-glenn-aeps_2022_ignition.mp4 -frames:v 1 $T/g18/$i.png; done
ffmpeg -v error -y -framerate 24 -i $T/g18/%d.png -c:v libx264 -crf 6 -pix_fmt yuv420p $S/G18_thruster-ignition_5-frames.mp4
python3 tools/scanlines.py $S/G18_thruster-ignition_5-frames.mp4 clips/G18.mp4 --at 0 --frames 5 --start 778,640,2702 --end 798,652,2662

# G20, G26, G32: film of the hurricane from the Space Station, the sharper star field, the 1969 control room on film
python3 tools/scanlines.py $A/G20_hurricane-dorian-eye_iss_2019-09-01_jsc2019m000805.mp4 clips/G20.mp4 --at 12.0 --frames 5 --start 50,57,1000 --end 60,62,980
python3 tools/scanlines.py $A/G26_hubble-milky-way-bulge_wfc3_STScI-2018-01.tif clips/G26.mp4 --frames 5 --start 200,500,2900 --end 260,534,2780
python3 tools/scanlines.py $A/G32_apollo11-mocr-celebration-film_1969-07-24_nasa-hd-resource-reel-part09.mp4 clips/G32.mp4 --at 24.5 --frames 5 --start 156,70,968 --end 176,82,928
```

Where things sit. Langley's plate: the upper of its two photographs, the wreck among the boats. The telegram: the word
"Success" runs from x 79 to 246 with its baseline near y 1002, on the Library's black-and-white scan (the colour scan,
`archive/src_new/N02_wright-telegram...mcc061.tif`, is sharper, but its own page carries no rights statement). Bell's
page: "Mr. Watson" is at x 3065 to 3395 and "come here" at x 3550 to 3900, baseline near y 590, on the right-hand
page, where Watson repeats the sentence back. The thruster's ring is centred near x 2128, y 1504 in the 4K frame, low
in the picture, so it sits a little under the middle of the shot. The control room film is 4:3 inside a 16:9 file;
its picture runs from x 156 to 1124. The shots these replace are kept in `clips/replaced/`.

## Added on the eighth pass (11 November 2026)

G32 now holds two real pictures side by side, and G34 is no longer a shot of its own: `tools/diptych.py` makes each
half with this tool at the half's own size (636 by 720), so the scanlines are drawn at full sharpness and never
scaled, and joins them with a black gutter. The conform gives each half a tube of its own. The whole-frame versions
are kept in `clips/replaced/` (`G32_whole_frame.mp4`, `G34_whole_frame.mp4`).

```bash
python3 tools/diptych.py
# which runs, for the two halves:
python3 tools/scanlines.py $A/G32_apollo11-mocr-celebration-film_1969-07-24_nasa-hd-resource-reel-part09.mp4 half0.mp4 --at 24.5 --frames 5 --start 300,0,636 --end 308,5,626 --size 636x720
python3 tools/scanlines.py $A/G34_perseverance-landing_jpl-control-room.mp4 half1.mp4 --at 6.2 --frames 5 --start 330,0,636 --end 338,5,626 --size 636x720
```

The 1969 film is four by three inside a 1280 by 720 file (the picture runs from x 156 to 1124). Its half is taken at one
source pixel to one film pixel; the whole-frame shot it replaces was enlarged by a third.

## The 1080p pass (11 November 2026): every archive shot made again at 1920 by 1080

`tools/archive_shots.py` holds every recipe on this page in a form that runs, and made all of them again at
1920 by 1080 on 11 November 2026. Nothing about a shot changed but its size: the crop and the move are in each
source's own pixels, so the picture inside the tube is the same and the scanlines are drawn at the larger size,
not enlarged.

```bash
python3 tools/archive_shots.py --check             # rebuilds each at 1280x720 and compares it with the shot in clips/
python3 tools/archive_shots.py --size 1920x1080    # all of them
python3 tools/diptych.py --size 1920x1080          # G32 (the two control rooms) and G33
python3 tools/printshot.py --size 1920x1080        # D10 (the museum's photograph on the card)
```

Before the 1080p versions were made, `--check` rebuilt every shot at 720p and compared it with the one in the
film: every one matched (likeness 0.98 or better, frame for frame). Two recipes had never been written down,
the Flyer (C04) and the bronze (D08), made on the first day. Their crops were recovered by matching the
finished shots against their sources, and are now in the tool:

- C04, the Flyer: a push from `500,618,4100` to `1150,980,3000` over 25 frames, of which the first 17 are in the
  shot; then the telegram as recorded above.
- D08, the bronze: a pan from `1100,378,1500` to `1750,1250,1500` over 25 frames, with the picture rolling into
  place for 5 frames.

The 720p shots the film used until v014 are kept in `clips/replaced/720p/`.
