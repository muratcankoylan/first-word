# The persona: who the agent was asked to be

| File | What it is |
| --- | --- |
| [persona-prompt.md](persona-prompt.md) | The prompt, about 3,800 words. Written to be pasted whole as a system prompt. |
| [persona-notes.md](persona-notes.md) | How to tune it: which section to change for which effect, and three behaviours to know about. |

## How it was made

The whole exchange is in [the conversation](../conversation/2026-11-10.md), from 17:21 UTC.

1. **The request (17:21).** One message from the person, after the reference films had been taken apart:

   > I want you to write a persona prompt that will be creating this video. This is basically a creator who reads
   > futuristic books like Anders Game, Asimov, or maybe books like The Beginning of Infinity, believes in futurism,
   > is a techno-optimist, and listens to things like Grimes. etc so i want a detailed persona prompt with high
   > itnensity keywords and deep research done by you so we can tweak the thinking of the model properly

   ("Anders Game" is *Ender's Game*; the message is quoted as typed.)

2. **Research and a draft, at the same time.** The agent started one deep-research run on the canon (the books,
   the techno-optimist essays, the music) and wrote the first full draft from its own knowledge while the run
   worked. When the report came back it checked the draft against it and edited the prompt seven times.

3. **What the research covered, said plainly.** It confirmed the Asimov, techno-optimist and Grimes material and
   added to it. It found one page of book notes for Deutsch and no citable source for *Ender's Game*, so those
   sections rest on the model's own knowledge of the books and paraphrase them. The dates in the prompt's list of
   real events were not checked in that run. Every claim the film itself makes was checked later against a
   source that was opened and read, before anything went on screen (the fact-check is in
   [the plan](../docs/plan/treatment.md), under "True").

4. **The design choices.**
   - **Six dials, 1 to 10, with both ends described**, so the person can move the output without rewriting
     prose: conviction, menace in the beauty, pace, humour, idea density, and how visible the canon is on screen.
   - **Each belief is paired with what it does to the film.** "Problems are soluble" becomes "nothing is shown
     finished". The second half of each line is what moves the output.
   - **A section of doubts**, "What you argue with yourself about", which keeps the work from reading as an
     advertisement for the future.
   - **Intensity lives in the vocabulary, the beliefs and the pace targets.** The instructions themselves are
     written calmly; capital letters and "must" make a model rigid, not energetic.
   - **A keyword bank that is larger than one film needs**, with an instruction to use a few per piece, because
     models over-use any word they are given.
   - **The assignment is one section**, "The film", so the persona carries over to another brief.

5. **The hand-back (18:09).** The person attached both files and wrote: "you are this but this is just a draft,
   you are beyond this", with a further brief in the same register and the instruction to plan every cut, scene,
   animation and transition before creating anything. From that message on, the agent worked as the persona. The
   plan came next.

## What is not here

The notes name two research files, `research-report.md` and `techno-optimist-creator-canon.json`. They were saved
in the session's first working folder and were not carried into the project, so they are not in this repository.
What the research did and did not establish is in step 3 above and in the conversation.

The two files here were rebuilt from the session's own record of what was written, because the originals stayed
in that first folder too. They match the last saved state of each file.
