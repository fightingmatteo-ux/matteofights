# Fighter Breakdown: Lomachenko (footwork), re-edit with 3 openings that look different

Matteo 2026-11-19: the old cut (`../2026-11-16-loma-breakdown/`, 5 hooks A-E) never posted. All 5 were the same shot
with only the first line changed, 78-80 s long, CTA at ~76 s (Saenchai Ep. 1, same build: nobody reached the end,
0 PLAN comments). This version tests 3 variants that differ in the first frame, not just the words, and cuts to ~44 s.

Source: the same raw take (Drive `lomachenko.MP4`, now on the media release as `loma-breakdown-src.mp4`), same
word timings (`work/words.json`). Takes and reasons in `work/takes.json`.

## Variants (only the opening differs)

| V | Opening | Frame 0 | Hook (take) |
|---|---|---|---|
| F | result | Matteo's face, title over it, hook word behind his head | "Four opponents in a row quit on their stools against Lomachenko. Here's what he did to them." (old C) |
| G | contrast | Matteo's own pad work (punches), then Loma's feet on "Lomachenko drilled his feet" | "Most people drill punches. Lomachenko drilled his feet." (old A) |
| H | question | overhead fight footage, Loma moving around Pedraza; Matteo appears on "against Lomachenko?" | "Why do good boxers look completely lost against Lomachenko?" (old D) |

G and H are "cold" opens (`"cold": True` in build.py): footage from frame 0, the whole hook line in the title with
the hook word in red, no word behind his head (he isn't on screen).

## Shared body (same in all 3)
One (side step) -> Two (feet never stop) -> "the third one is why people actually quit" -> Three (pivot) -> CTA.
Out: the intro, the dance-origin line, the takeaway, the 5 plan cards.
CTA, one ask: "Comment the fighter you want to see next. The most asked for fighter gets the next episode."
The top pill turns from FIGHTER BREAKDOWN into COMMENT THE NEXT FIGHTER at "Two". No episode number anywhere.

## B-roll (`work/precut.sh` cuts it, `work/make_broll_json.py` places it on source words)
The old clips came from 3 YouTube videos that aren't on the media release, and YouTube blocks runners, so these are
re-picked from what is there (checked frame by frame 2026-11-19): pads = Matteo's own `broll-pads-chaiya.mp4`;
feet, inout = `yt-loma-highlights.mp4`; side1, side2 = `yt-loma-skillr.mp4` (Loma vs Pedraza broadcast);
lost, pivot = `yt-loma-angles-footwork.mp4` (overhead, Loma vs Pedraza). No stool footage available, so the
"quit on their stools" lines stay on his face.

## Render
Submit render (GitHub Actions), variants `F G H`, media = the raw + the 4 sources above, include
`tools/planreel production/listicles/music/epic-bold-drums-alex-morgan.mp3`. precut.sh builds the b-roll and the
a-rolls on the runner; Modal runs `make.sh` (cut-out, build, render, glitch check: black-frame mode for G and H).

No CapCut Eye Contact on these renders (the old A-E had it, done by Matteo on the phone after rendering).

## Queue
Trial set `loma-3open`, ids `2026-11-20-loma-3open-F/G/H`, `approved:false`. Matteo approves after watching.
