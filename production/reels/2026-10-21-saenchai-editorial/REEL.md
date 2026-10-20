---
slug: 2026-10-21-saenchai-editorial
status: prepared in the cloud, render on Matteo's laptop (the tape footage only exists there)
pillar: psychology
format: legend-credibility, editorial look
test_variable: look (same takes, tape slots and hooks as 2026-10-16-saenchai-bigger-men)
---

# Saenchai vs bigger men, editorial re-cut

Matteo 2026-10-20: re-render the Saenchai reel in the new style on the laptop. The current cut (A/B/C on the media
release) posts first as trial reels to test the hooks; this version tests the look against it.

## On the laptop (Git Bash, repo root), one variant at a time
```bash
cd production/reels/2026-10-21-saenchai-editorial
npm i                 # first time only (@hyperframes/core)
bash make.sh A        # then: bash make.sh B, bash make.sh C
```
`make.sh` does everything: assembles the A-roll from the original folder's `assets/raw.mp4` + `assets/voice.wav`,
cuts the tape with `make_broll.py` (reads `media/saenchai-broll/`), cuts Matteo out (~5 min, downloads the RVM model
once into this folder), builds, renders, runs the glitch check (re-renders once on FAIL) and writes
`media/2026-10-21-saenchai-editorial/2026-10-21-saenchai-editorial-<V>-phone.mp4`. Then upload to Drive output as usual.

## What changed vs the current cut
- Hook word flies from behind his head to the front on the spoken word: A "career." / B "steal" / C "never".
- Phrase captions (focus-in, blur dissolve), keywords with meaning effects: SWEEP = jab, MUSCLE + FRUSTRATED = impact,
  TEN = giant 10 behind the word; behind/in-front alternation only where his face is on screen.
- Tape clips are the same slots as before (make_broll.py), above his cut-out, whip in with a motion blur.
- White slam card: "don't win the exchange, win the **reset**" (rewind effect + sub hit).
- Music: epic-bold-drums (the original cut's Pixabay track) instead of the piano placeholder; caption SFX on top.
- Dropped from v3: RESETS counter, TAPE labels, Bowe callout, gold accents (cleaner, editorial).

## Check before sending
`npx --yes hyperframes@0.8.147 snapshot --at <hook word>,<a tape clip>,<the RESET card>`: the hook word must be
visibly cut by his hair before it flies, captions readable over the tape, card text inside the frame.
Prepared and lint-checked in the cloud with stand-in timings (only error: footage not present there).
