# Persona prompt: tuning notes

These notes are for the team. They are not part of the prompt.

## Files

- `persona-prompt.md` is the prompt. Paste the whole file as the system prompt.
- `research-report.md` is the deep research output, with its source list.
- `techno-optimist-creator-canon.json` is the raw research result, including per-section confidence and excerpts.

## How to steer the model

Each section of the prompt controls a different part of the model's thinking. Change the section that matches what you want to move.

| To get | Change | Expect |
|---|---|---|
| More hype, fewer brakes | Raise Conviction to 10 and delete "What you argue with yourself about" | Brochure tone. Louder, less credible, weaker on the doubters' beat. |
| Darker and more Grimes | Raise Menace to 7 or more and swap the palette in "Look" | Villain's-eye imagery, heavier sound direction. |
| In-jokes for a tech audience | Raise Canon on screen to 6 or more | Named references (Kardashev, Seldon, the ansible) in lines and signage. |
| Slower and more emotional | Lower Pace to 5 and lengthen the Questions beat in the structure table | Closer to the Keep Thinking reference: black cards, held shots. |
| A different worldview | Edit "What you believe". Each line is a belief followed by what it does to the film. | The second half of each line is what changes the output most. |
| Different wording | Edit the keyword bank and the two "dead" lists | The most direct lever on vocabulary. |
| A different assignment | Replace "The film" section only | The persona carries over to any brief. |

Three behaviours to know about:

- **Models over-use any word you list.** The keyword bank is deliberately larger than one film needs, and the prompt tells the model to use a few per piece. If one word keeps recurring, delete it from the bank.
- **Examples get copied.** The prompt gives few literal example lines for that reason. If you add sample script lines, add several that differ from each other and say they are illustrations.
- **The dials are coarse.** A change of one point does little. Move a dial by three or more to see a difference, or edit the descriptions of its two ends.

## Choices I made that you may want to reverse

1. **Intensity lives in vocabulary, convictions and pace targets.** The instructions themselves are written calmly. Capital letters and "must" make current models rigid and repetitive, and they do not make the output more energetic.
2. **The optimism is Deutsch's, not accelerationism's.** It is conditional: problems are soluble if people solve them. This gives the film excitement with credibility. To go fully accelerationist, edit the accelerationism bullet and the "inevitable" bullet under "What you argue with yourself about".
3. **Canon on screen is set to 2.** The reading shapes choices and is not name-dropped. At higher settings every script starts mentioning Asimov.
4. **The persona has a handle, Wren.** It makes the persona easier to refer to. Rename it freely.
5. **Four lines the persona holds.** Real archive for real events, no words put in real people's mouths, no "in the style of" a living artist in generation prompts, and no real artist's recording or cloned voice without permission. These protect the film from the most likely public criticism of an AI-made film about AI.

## What the research confirmed and added

Confirmed against sources:

- Asimov: psychohistory, the Seldon Plan shortening the interregnum, the Three Laws, the entropy question in "The Last Question".
- Deutsch: the two maxims, good explanations as hard to vary, and optimism as conditional on creating knowledge.
- Ender's Game: the reorientation insight and the moral injury of a victory engineered by adults.
- Dates for Altman's two essays (23 September 2024 and 10 June 2025) and Buterin's d/acc follow-up (5 January 2025).
- Grimes's self-production, her liking for one jarring element in a song, and the *Akira* reference for *Miss Anthropocene*.
- The look of Frutiger Aero, cassette futurism, solarpunk and the NASA Ames paintings.

Added to the prompt because of the research:

- Grimes in 2026: an album teased as made without generative AI, alongside her statement that AI is the most dangerous thing that will ever happen (NME, reporting an *Interview* magazine conversation). This went into the persona's ambivalence.
- The progress-studies point that progress is real and not automatic, which became the persona's distrust of "inevitable".
- The contrast between polished confidence and visible maintenance in optimistic futurism, which became the "lived-in over pristine" rule.
- "Who holds the tools" from d/acc.
- Fever Ray in the listening list.

Limits:

- The research was thin on Deutsch (one book-notes page, low confidence) and found no citable source for Ender's Game. Those sections rest on my own knowledge of the books. Page-level quotations are not verified, which is one reason the prompt paraphrases the books and does not quote them.
- The archive list of real events and dates in the prompt comes from my own knowledge and was not part of the research run. Check each date before it goes on screen.
- I did not verify the Grimes *Visions* production details (about three weeks, GarageBand, blacked-out room) in this run. They are widely reported.

## Inputs the prompt still needs

Fill the bracketed fields in "The film": brand or project, length, what the viewer does next, platform, and who speaks.

## Sources from the research run

- Vitalik Buterin, "d/acc: one year later": https://vitalik.eth.limo/general/2025/01/05/dacc2.html
- Sam Altman, "The Intelligence Age": https://ia.samaltman.com/
- Sam Altman, "The Gentle Singularity": https://blog.samaltman.com/the-gentle-singularity
- "Once promised, forever believed? An essay on the blind spots of AI promises" (AI & Society, 2025): https://link.springer.com/article/10.1007/s00146-025-02765-1
- "Beyond the Binaries: Techno-Optimism and Pessimism as Situated Epistemic-Affective Orientations" (2026): https://link.springer.com/article/10.1007/s11024-026-09651-0
- Britannica, Foundation series: https://www.britannica.com/topic/Foundation-by-Asimov
- Wikiquote, Isaac Asimov: https://en.wikiquote.org/wiki/Isaac_Asimov
- "The Last Question": http://www.thelastquestion.net/
- Book notes on *The Beginning of Infinity*: https://fluidself.org/books/science/the-beginning-of-infinity
- *Abundance*, publisher page: https://www.simonandschuster.com/books/Abundance/Ezra-Klein/9781668023488
- Grimes, NME cover feature (2015): https://kevinegperry.com/2015/12/04/grimes-interview-art-angels-nme-cover-feature-2015
- Grimes, The Guardian (2015): https://www.theguardian.com/music/2015/oct/31/claire-boucher-grimes-art-angels
- Grimes, NPR conversation: https://www.npr.org/transcripts/455769676
- Grimes, The Quietus: https://thequietus.com/interviews/grimes-art-angels-realiti-interview-pop
- Grimes, Pitchfork on the look of *Miss Anthropocene*: https://pitchfork.com/features/interview/grimes-miss-anthropocene-interview
- Grimes, NME on *Psy Opera* (2026): https://www.nme.com/news/music/grimes-teases-new-album-psy-opera-made-without-generative-ai-but-says-ai-is-bigger-than-jesus-and-most-dangerous-thing-thats-ever-going-to-happen-3941577
- "A Solarpunk Manifesto: Turning Imaginary into Reality": https://www.mdpi.com/2409-9287/8/4/73
- Frutiger Aero Archive: https://frutigeraeroarchive.org/
- Cassette futurism, vocab.design: https://vocab.design/cassette-futurism
