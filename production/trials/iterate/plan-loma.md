# Round 2: re-cut 2026-11-02-plan-L1-D 5 ways

Round-1 winner of `plan-loma` (contrast opening): "Most people drill punches. Lomachenko drilled his feet."
Numbers at 24 h: skip rate 44.4%, avg watch 5.8 s, 2303 views. Main leak: **opening** (fewer people than usual stay past 3 s).

Before cutting, check for Matteo's retention note (Studio revision on this reel, or an upload with the note `retention <id>`). If he sent drop-off times, `cut-the-dip` and `faster` work on those exact seconds.

Five cuts, one per variant, everything else unchanged so the test reads clean:

- A: `trim-open`: start on the first strong word: cut breaths, 'so', the walk-in (skip rate is the leak)
- B: `first-frame`: open on the most striking frame (tape, impact, b-roll) with the hook line over it
- C: `text-hook`: same cut, a new on-screen hook text (sharper, shorter, the top opening type)
- D: `cut-the-dip`: remove the beat where viewers leave (retention note, or the point at avg watch)
- E: `shorter`: under 20 s: hook, the one point that matters, payoff

Queue ids `2026-11-02-plan-L1-D-r2-<letter>`, label each with `trials.py label <id> <edit> --parent 2026-11-02-plan-L1-D`, then `trials.py schedule plan-loma-r2 <next free day>`.
