# Round 2: re-cut 2026-11-01-first-fight-lesson-B 5 ways

Round-1 winner of `first-fight-lesson` (contrast opening): "My first fight ended in a knockout and I'm the one who should have lost."
Numbers at 24 h: skip rate 31.4%, avg watch 13.0 s, 2601 views. Main leak: **middle** (people stay for the hook, then leave around 13.0 s).

Before cutting, check for Matteo's retention note (Studio revision on this reel, or an upload with the note `retention <id>`). If he sent drop-off times, `cut-the-dip` and `faster` work on those exact seconds.

Five cuts, one per variant, everything else unchanged so the test reads clean:

- A: `cut-the-dip`: remove the beat where viewers leave (retention note, or the point at avg watch)
- B: `faster`: tighter: every pause out, jump cuts, b-roll every 2-3 s through the middle
- C: `shorter`: under 20 s: hook, the one point that matters, payoff
- D: `payoff-first`: flash the payoff (the KO, the result) in the first 2 s, then rewind into the story
- E: `trim-open`: start on the first strong word: cut breaths, 'so', the walk-in (skip rate is the leak)

Queue ids `2026-11-01-first-fight-lesson-B-r2-<letter>`, label each with `trials.py label <id> <edit> --parent 2026-11-01-first-fight-lesson-B`, then `trials.py schedule first-fight-lesson-r2 <next free day>`.
