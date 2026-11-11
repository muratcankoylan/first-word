# Prompts

Six generations cover every generated shot. Each is written in the shape Runway's own Seedance 2.5 guide asks for, and two are written out in full below. The ten set-ups after them are the beat descriptions that go inside the other timelines.

## Rules for every generation

- **Four parts, in this order.** An asset-binding list, a one-sentence summary, a timeline in continuous whole-second beats with no gaps, and closing consistency notes.
- **No face references.** The model does not reliably accept them. People are described in words: give each person two or three fixed traits and repeat them at every beat they appear in.
- **One person, one generation.** Every shot of a given person is made in the same generation, so the face holds.
- **No words anywhere.** Reference images carry no text or logos, and prompts ask for no readable type. Every word on screen is added in code.
- **Voices go in as audio.** Bind each finished line as @Audio and state that it is the only voice. Write the line as plain labelled dialogue. Close every prompt with: No subtitles. No music.
- **Whole seconds in, frames out.** Timestamps guide pacing and are not frame-exact. The cut takes its frames from the shot list.
- **Draft first.** Generate at 480p in draft mode and enhance only the take we keep.
- **Paste the colour rule into every prompt:** ultramarine, navy and cyan carry the frame. White is the only highlight. Skin stays natural. Everything looks used: scuffs, tape, dust.

## People, in words

These traits are typed into the prompt at every beat. No image of a face is uploaded.

| Person | Fixed traits to repeat |
| --- | --- |
| Mara | A woman in her mid-forties, dark hair tied back, a solder burn on her right knuckle |
| Osei | A man in his mid-sixties, short grey hair, wire glasses pushed up on his head |
| Jun | A young man of nineteen, headphones round the neck, the jacket two sizes too big |
| Ray | A man in his early fifties, heavy forearms, reading glasses in his breast pocket |
| Rosa | A woman in her late sixties, grey hair pinned up, reading glasses, flour on her hands |
| Pip | A girl of nine, gap-toothed, pyjamas under an adult's jacket with the sleeves rolled |
| Amara | A woman in her thirties, nurse's scrubs under the jacket, hair wrapped |
| Dev | A man in his fifties, weathered, soil on his cuffs |

## Reference images to make first

None of these contains a person or a word.

| Reference | What it shows | Used for |
| --- | --- | --- |
| The wall | The empty line-up frame: a light-grey plaster wall with faint pencil height marks, soft top light | Scene and composition for generation 1 |
| The jacket | A navy cotton chore jacket on a hanger, three buttons, a plain white vertical rectangle on the left chest | Wardrobe in every generation |
| The baton | A 30 cm tube of cyan light with metal end caps | Generations 5 and 6 |
| The hall | A long dark workshop: scuffed concrete, benches, a fan the size of the far wall, haze | Generation 2 |
| The kitchen | A table under one warm lamp, an old laptop, a dismantled sewing machine on newspaper | Generation 3 |
| The rooftop | Planters, a washing line, a hydrophone on a tripod, a milk crate, glass towers all round, a parapet | Generation 6 |
| The cyan band | A black frame with one centred vertical band of cyan | The last frame of generation 6, set in Keyframe mode |
| Two grey previz clips | Textureless three.js renders of the walk into the wind and of the handoff | Bound as @Video to fix camera path and blocking |

## The six generations

109 seconds of footage in six requests. Each person's shots sit inside one generation.

| Generation | Seconds | Beats, with their shots | Voice lines bound as audio | Mode |
| --- | --- | --- | --- | --- |
| 1. The line-up | 26 | Eight bowed heads at one second each. Mara looks up and speaks. Jun's question. Ray's objection. Mara's one word. Ray concedes. Mara smiles. Shots A02 to A13, D01, D04, D05, E01, E03 | Six | Reference |
| 2. The hall | 27 | Wide. From behind. From the front. The strip on her cheek. The snort. The bench. The pencil cap. Osei. Shots B01, B04, B06, B07, B09, D03, D07, E05 | Two | Reference, with the wind previz as @Video |
| 3. The kitchen | 10 | Wide. Pip's whisper. Rosa laughing. Shots F01, F04, G33 | One | Reference |
| 4. The blue reel | 19 | Amara, Dev, Jun and Ray at four seconds each, then Ray laughing. Shots G13 to G16, G35 | Four | Reference |
| 5. The handoff | 15 | Five passes at three seconds each. Shots G36 to G40 | None | Reference, with the handoff previz as @Video |
| 6. The whale | 12 | The tilt up, the rooftop hold, the eye, the baton into the lens. Shots G41, H01, H02, H03 | One | Keyframe, last frame set to the cyan band |

### Generation 1 in full: the line-up

```
@Image 1: the wall and the framing (scene and composition). @Image 2: the navy work jacket (wardrobe). @Audio 1 to @Audio 6: the finished voice lines, the only voices. Generate no other voice.

Summary: Eight people in identical navy work jackets take turns standing in one locked-off, waist-up frame against the light-grey plaster wall of @Image 1, heads bowed, in a cool high-key portrait style with no camera movement, and three of them look up and speak.

Every shot: locked camera at eye level, 65mm, subject dead centre, shoulders square, the wall and soft top light of @Image 1, the jacket of @Image 2. Hard cuts between shots.

0-1s: Ray, a man in his early fifties with heavy forearms and reading glasses in his breast pocket, arms crossed, head bowed.
1-2s: Amara, a woman in her thirties in nurse's scrubs under the jacket, hair wrapped, head bowed.
2-3s: Dev, a weathered man in his fifties with soil on his cuffs, head bowed.
3-4s: Jun, a young man of nineteen, headphones round the neck, the jacket two sizes too big, head bowed.
4-5s: Osei, a man in his mid-sixties with short grey hair and wire glasses pushed up on his head, head bowed.
5-6s: Pip, a girl of nine, stands on the floor, so only the top of her hair enters the bottom of the frame.
6-7s: Rosa, a woman in her late sixties with grey hair pinned up and flour on her sleeve, head bowed.
7-9s: Mara, a woman in her mid-forties with dark hair tied back and a solder burn on her right knuckle, head bowed, then raises her eyes to the lens.
9-11s: Close-up at 100mm of the same Mara, dark hair tied back, eyes on the lens. Dialogue (Mara): @Audio 1, "Everybody's got a prediction."
11-14s: The same Jun, headphones round the neck, looks straight down the lens. Dialogue (Jun): @Audio 2, "So what does it actually do?"
14-17s: The same Ray, arms crossed, flat. Dialogue (Ray): @Audio 3, "It makes things up."
17-19s: Close-up of the same Mara, unblinking. Dialogue (Mara): @Audio 4, "Constantly."
19-23s: The same Ray uncrosses his arms and speaks quietly. Dialogue (Ray): @Audio 5, "So it is just autocomplete."
23-26s: Close-up of the same Mara. She smiles for the first time. Dialogue (Mara): @Audio 6, "Yeah. It is."

Consistency: the same frame, wall, light and jacket in every shot. Cool, slightly desaturated high key, the navy rich. Each face stays the same every time that person returns. No subtitles. No music, room tone only.
```

### Generation 6 in full: the whale

```
Last frame: the cyan band. @Image 1: the rooftop (scene). @Image 2: the tube of cyan light (prop). @Audio 1: the finished line, the only voice. Generate no other voice.

Summary: At blue hour on a lived-in rooftop, a nine-year-old girl in pyjamas and an adult's navy work jacket holds a tube of cyan light up to a sperm whale gliding through a sky that is the underside of an ocean, in an ultramarine fisheye style with hard flash on the foreground, then spins and pushes the tube into the lens.

0-1s: Whip tilt up from her raised fist, holding the tube, into deep blue.
1-7s: 8mm fisheye, 25 cm above the edge of a planter. Foreground: white daisies and long grass, hit by hard on-camera flash. Middle: the girl, small in frame, back to camera, pyjamas under the navy jacket with rolled sleeves, holding the tube above her head like a lantern, standing well inside the roof's parapet. Around her the rooftop of @Image 1: a washing line with one navy jacket, a tripod carrying a hydrophone, a cable running to a laptop on a milk crate. Glass towers bend in at the frame edges. Above them the sky is a rippling water surface seen from below, slow caustic light moving over the towers. A sperm whale glides through that water from left to right. Each time the tube blinks, a ring spreads across the surface overhead. The camera rises very slightly.
7-9s: 100mm macro. One eye of the same girl fills the frame, lit blue, one white point of light in it. The whale's shape crosses the reflection from left to right. She breathes in, and the breath becomes a laugh.
9-12s: 8mm fisheye, 30 cm from her. The same gap-toothed girl in the navy jacket spins toward the camera and pushes the tube straight at the lens with both hands, laughing. Dialogue (the girl): @Audio 1, "Somebody starts it." Her fingers become huge and flash-lit, and the tube grows until it is one vertical band of cyan from the top of frame to the bottom, dead centre.

Consistency: ultramarine, navy and cyan carry every frame, with white only on the flowers. The same girl, jacket and tube throughout. No subtitles. No music. Sound: wind, the distant city, and slow clicks under water.
```

If Keyframe mode will not take reference images in the same request, drop the two images and keep the last frame. The description carries the rooftop.

## Beat descriptions for the other generations

The ten set-ups below were written one shot at a time. Paste each into its generation's timeline as a beat, change its length to whole seconds, and keep the lens, light and action as written.

## 1. The line-up

Shots A02 to A10, A13, D01, D04, D05, E01, E03. One prompt, eight people.

```
Locked-off camera on a tripod at eye level, 65mm lens, 2.5 metres from the subject. Waist-up portrait, subject dead centre, shoulders square to camera, hands at sides. A light-grey hand-trowelled plaster wall one metre behind, with faint pencil height marks at its left edge. One large soft light from above and slightly in front, cool white, low contrast, a soft shadow under the brow. [CHARACTER SHEET] in a navy cotton work jacket with a plain white vertical rectangle stitched on the left chest. The subject stands still with head bowed, breathing, then slowly raises their eyes to the lens. Cool, slightly desaturated high key. The navy stays rich. No camera movement. 4 seconds.
```

- **Close-ups** (A13, D05, E03): the same set at 100mm and 1 metre, eyes on the upper third.
- **Pip** (A07): she stands on the floor in the adults' frame, so only the top of her hair enters at the bottom edge.
- **Must stay identical:** frame, wall, light, jacket. Align all eight takes on the wall's pencil marks before the ink layer goes on.

## 2. The hall, wide

Shot B01.

```
18mm lens on a tripod 40 cm above a scuffed concrete floor. A long dark workshop: benches and tool racks in silhouette on both sides, wet patches on the floor. At the far end a fan the size of the wall turns slowly, lit from behind by two hard cyan lights aimed at the lens, so each blade cuts the beam. Thick haze. Thin white smoke streamlines flow from the fan toward the camera. No front light. Navy and cyan only, blacks crushed, bloom on the lights. Locked camera. 4 seconds.
```

## 3. Into the wind, from behind

Shot B04. The empty aisle is where the paper strips go in compositing.

```
21mm lens, 60 cm above the floor, 1.5 metres behind her, tracking forward at walking pace. [MARA] walks away from camera down the centre aisle of the dark workshop, leaning into a strong headwind toward the giant backlit fan. Her jacket hem snaps and her hair is pulled straight back. She is a silhouette with a hard cyan edge. Smoke streamlines rush past her toward the lens. The aisle on both sides of her stays empty and dark. Navy and cyan only. 5 seconds.
```

## 4. Into the wind, from the front

Shots B06, B07, B09. Three clips from one prompt, with one added action each.

```
18mm lens at chest height, 80 cm in front of her, tracking backward at her pace. [MARA] walks toward camera into a strong headwind, eyes narrowed, jacket snapping. Hard cyan backlight flares over her right shoulder, and a faint soft cyan fill lifts her face. Haze and smoke streamlines stream past the lens. 5 seconds.
```

- **B07 adds:** a blank strip of white paper blows in and plasters itself across her cheek. She peels it off with her left hand and looks at it.
- **B09 adds:** she snorts, opens her fingers, and the wind takes the strip. She keeps walking.

## 5. Mara at the bench

Shot D03.

```
18mm lens resting on a scarred steel workbench. In the foreground a small relay on a breadboard and a coil of solder, grazed by hard cyan light. [MARA] plants both hands on the bench and leans down and in until her face fills the frame, 40 cm from the lens. She says three words and holds the look. Hard cyan backlight flares over her left shoulder. A vertical cyan tube light glows out of focus behind her. Locked camera. 4 seconds.
```

## 6. Osei

Shot E05.

```
50mm lens, 1.8 metres. Chest-up three-quarter portrait, [OSEI] on the right of frame. On the left, at the height of his face, a vertical tube of cyan light stands in the dark workshop. The tube is his only light: hard cyan from the left, the far side of his face falling to navy, haze behind. He looks just past the lens, then into it, and says one sentence slowly. Slow push in, about a tenth closer by the end. On his last word the tube switches off and the frame goes black. 5 seconds.
```

## 7. The kitchen

Shots F01 and F04.

```
40mm lens on a tripod at table height, 2.5 metres back, the back of a chair soft in the foreground. A small lived-in kitchen at night, one dark window, children's drawings on the fridge. One warm desk lamp over the table is the only light, and everything beyond it falls to deep blue. [ROSA] sits at the table in front of an old laptop, flour on her hands, a dismantled sewing machine laid out on newspaper beside it. [PIP] sits next to her in pyjamas, chin on her folded arms, watching the screen. Rosa raises one finger over the keyboard and hesitates. Locked camera. 4 seconds.
```

- **F04:** 100mm at 60 cm. Pip's face, lit warm from the left by the lamp. Her eyes go from the screen to the woman beside her. She whispers two words. 3 seconds.

## 8. The blue reel

Shots G13 to G16. Every clip opens with the same four sentences.

```
10mm fisheye lens, 25 cm from the foreground object. Hard on-camera flash on the foreground, and a blue-hour background two stops darker. The horizon bows. The camera drifts 5 cm toward the subject. 4 seconds.
```

| Shot | Foreground, flash-lit | Behind it | The one action |
| --- | --- | --- | --- |
| G13 | Amara's hand holding a phone and a paper coffee cup with a pencil sketch on its side | Amara in scrubs and the jacket on a hospital roof, helipad lights, glass towers bending in at the frame edges | She types with her thumb and laughs at herself |
| G14 | A blighted leaf held up to the lens between soil-dark fingers, raked by a phone torch | Dev in a field before sunrise, a tractor with one headlight far back | He turns the leaf and speaks to the phone |
| G15 | The tip of a soldering iron and a curl of smoke | Jun at a desk under a bedroom window open on glass towers, a half-built synthesizer of breadboards and loose wire | He touches the iron to a joint and one small white light comes on |
| G16 | An oil drum used as a desk, a laptop, reading glasses on its lid | Ray alone in a garage with the door open on blue night, a half-dismantled motorcycle | He breathes out, cracks his knuckles and types two words |

## 9. The handoff

Shots G36 to G40. Five clips that must match exactly.

```
24mm lens, 40 cm, shallow focus. A hand enters from the left holding a 30 cm tube of cyan light upright. A second hand enters from the right and takes it at the exact centre of frame. The tube stays vertical and centred, and blinks once as the grip changes. The tube lights both hands, and the background is two stops darker. Locked camera. 3 seconds.
```

- **The five passes:** Mara to Osei in the hall. Osei to Jun. Jun to Rosa in the kitchen, flour on her knuckles. Rosa to Pip. Pip's hand closing round it on the rooftop at blue hour.
- **Must stay identical:** the tube's position, size and angle, and its travel from left to right. The cut takes the five frames around the change of grip.

## 10. The whale

Shots H01, H02, H03. This is the image the film is remembered by, so it gets the most attempts.

```
8mm fisheye lens, 25 cm above the edge of a rooftop planter. Foreground: white daisies and long grass, hit by hard on-camera flash. Middle: [PIP], small in frame, back to camera, in pyjamas and an adult's navy work jacket, holding a 30 cm tube of cyan light above her head like a lantern. Around her a lived-in rooftop at blue hour: a washing line with one navy jacket, a tripod carrying a hydrophone, its cable running to a laptop on a milk crate. Glass towers bend in at the frame edges. Above them the sky is the underside of an ocean: a rippling surface seen from below, slow caustic light moving over the towers. A sperm whale glides through that water from left to right. Each time the tube blinks, a ring spreads across the surface overhead. Ultramarine, navy and cyan, with white only on the flowers. The camera rises 2 cm, almost still. 6 seconds.
```

- **H02:** 100mm macro. One eye of a nine-year-old girl fills the frame, lit blue, with one white point of light in it. The shape of a whale crosses the reflection in her eye from left to right. She breathes in. 3 seconds.
- **H03:** 8mm fisheye, 30 cm from her. Pip, on the same rooftop, spins toward the camera and pushes the tube of cyan light straight at the lens with both hands, laughing. Her fingers become huge and flash-lit. The tube grows until it is one vertical band of cyan from the top of frame to the bottom, dead centre. 3 seconds.
- **The last frame of H03 must be a centred vertical cyan band,** because the next frame is the cursor.

## Macro inserts and stills

Nothing is filmed, so these are generated too. Each is one object, one action and a shallow plane of focus. They are the film's physical proof, so they get the same care as the hero shots.

| Shots | What to make | Note |
| --- | --- | --- |
| B05, D06, E04 | A relay on a breadboard closing, with a pinpoint cyan spark | One six-second generation at extreme macro. Pick the five frames around the spark. The same clip serves all three |
| B02 | A fan blade's edge cutting a beam of light through haze |  |
| B08 | A blank paper strip held between thumb and finger in wind | FLYING CARS BY 2000 and the handwritten "us" are added in code |
| D10 | A hand ticks a printed photograph with a red wax pencil | The photograph is the Met's public-domain image, composited in |
| F02, F03, F05 | A flour-dusted fingertip on old laptop keys, the screen over her shoulder, the fall to Enter | The screen text is added in code. Ask for slow motion on the Enter key |
| G06 | A phone lighting up in a hand in the dark | The screen stays blank |
| G21, G22 | A blackboard with chalk dust and one crossed-out line | #1196 and the quote are added in code |
| G23, G27, G28, G29 | A printed hand with its supports, a cello with two strings off, a circuit board with a bodge wire, a crayon drawing beside its print | Stills on seamless white or black, object dead centre, flat light |

## Learned on the first day of generation

These correct the prompts above. The prompts that actually ran are in `timing/generations.json` in the project folder.

- Through the API, references are written `@Image1`, `@Audio1`, with no space.
- Every voice reference must be at least two seconds long. Pad short lines with silence.
- A bound voice sets the voice and the timing. The model performs the line again; it does not copy our recording in.
- First and last frames cannot be combined with reference images in one request. The whale shot uses references, so its last frame is matched to the cursor in the edit.
- Pip's lines carry no voice reference. The model gives her a voice.
- Say what a person looks like, not only who they are. Osei is a Black Ghanaian man in his mid-sixties; without that the model drew someone else. Give two people no prop in common: Ray's reading glasses and Osei's glasses were confused.
- Describe the whale's anatomy and give it a reference picture: an enormous blunt square head, a narrow lower jaw, small paddle flippers.
- Do not describe a child in nightwear. Pip wears a striped top and jeans under the jacket.
- Reference images of empty places must not mention portraits or framing for people.
- A draft is 854 by 480 at 24 frames a second, 20 credits a second.

## Learned on the second day of generation

The prompts that ran are in `timing/generations.json` in the project folder, one per job. The line-up prompt above is no longer how the people are made: each person now has a reel of their own. What the second day taught, in the order it cost us:

- **No face in any reference, ever.** A still or a clip that shows a realistic face is refused, even when the model made it itself. The provider documents this as intended. Do not retry it and do not disguise it.
- **Write a reel, not a scene.** One job holds every shot of one person, in every place. Open with "Mara, in every shot:" and her fixed description, list the beats grouped by place, and close with "the same woman in every shot: the same face, hair and jacket at the wall and in the hall". Thirty seconds and nine beats held.
- **The fixed descriptions** are in `timing/characters.json`. Paste them. A synonym is a new person.
- **Two people who never meet can share a reel** (Amara and Dev, Rosa and Pip) when every beat names one of them.
- **A voice can be bound as a voice.** "@Audio1 is Pip's voice: when she whispers, it is in this girl's voice" gave a line she had never said.
- **A sound direction becomes a prop.** "Right on the microphone" put a microphone in the picture. Closeness belongs in the Sound line only.
- **A close, flash-lit wide lens always comes back with a round lens edge**, whether the prompt says fisheye, ultra-wide or barrel distortion, and whatever it says about borders. The conform now makes that edge the same circle on every such shot.
- **Hide a face with an action, not a rule.** "Her right forearm is raised across her face against the wind" held for the whole shot. "We never see her face" alone produced a caped silhouette.
- **An empty frame has to be the only thing in its job that could fill it.** The top of Pip's hair in an otherwise empty frame failed while Osei was in the same job, and worked once he was not.
- **Text in a still:** ask for one short thing to be readable and say that everything else is smeared. Otherwise the model writes fluent nonsense.
- **Hands default to old and heavy.** Give every hand an age and a build.
- **Spoken words can come back garbled** ("autocomplete" became something like "octavation"). Transcribe every line before trusting the mouth.

## Learned on the third pass

- **The ink style is one paragraph, pasted in front of every drawing:** "Hand-drawn illustration in navy blue ink on bright white paper: confident brush-pen outlines, solid navy for the darkest areas, mid-tones made only of coarse halftone dots, no other colour, no grey wash, a lot of white paper left showing. It is a drawing, not a photograph and not a 3D render." Seven drawings from seven separate requests came back as one hand.
- **Ask for the label blank and letter it in code.** The cube computer's sticker, the email window and the laptop screen were all requested empty. The words on them are set afterwards, so they are exactly the words on record.
- **Ask for a sheet of separate drawings, not a composition.** "About twenty separate small drawings, evenly spaced with clear white gaps between them, like a sheet of stickers" gave nineteen mouths and a skull that could be cut apart and placed one by one on the wall.
- **Name the hand.** "The slim brown hand of a South Asian woman in her forties, with short unpainted nails and a small pale burn scar on the knuckle of the index finger, the cuff of a navy work jacket at the wrist" fixed the heavy old hand of the first take.
- **Check a generated page for words you did not ask for.** The proposal's header bars came back faintly lettered DATE, TO, FROM. They were painted solid.
