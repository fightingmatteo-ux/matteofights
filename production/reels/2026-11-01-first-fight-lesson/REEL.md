---
slug: 2026-11-01-first-fight-lesson
status: rendered locally 2026-11-01 (A-E, v2 visual hooks), sent to Matteo, not queued, not approved
pillar: story (pin candidate, replaces knockout-draw A/B/C)
format: talking head, editorial look, one-take loop per hook, hook test round 1 (5 openings)
test_variable: hook (opening type)
---

# First fight, the lesson

Raw: Drive 1f-4HVz4VmlbMkj-AgzVdlPdeB9odWGbX -> media release `first-fight-lesson-raw.mp4` (268.9 s, 1440x2560 HEVC,
13 slated takes + share x3 + follow x3). Tape: `first-fight-2.mp4` (KO 48.33 s).

## Takes (work/takes.json, built by work/make_takes.py: cuts only inside measured silence)
| Segment | Source | Note |
|---|---|---|
| open<V> / end<V> | Loop A2, B1, C3, D1, E2 | open = hook -> "his sixth", end = "It's about control" -> bridge; same take = seamless loop |
| body1 | Body 3, "Someone told me" -> "disqualified me" | one pause > 0.5 s tightened ("so I hunted / the ref") |
| share | Share 3 | |
| body2 | Body 3, "I thought fighting was about hurting people" | "'cause" and "But in reality" dropped |

C3 is the only C take that says "Should a knockout count" (C1/C2: "Shouldn't knockout"). A2 says "I'd know" (A1: "I would").

## Edit
Hook: knockout tape full-bleed behind every variant, hook lines build word by word, plus a visual hook per variant
(Matteo 2026-11-01): A WHAT HAPPENED: K.O. -> OFFICIAL RESULT: DRAW; B ENDED IN: K.O. -> SHOULD HAVE BEEN: L;
C DOES IT COUNT? poll (YES / NO, vote in the comments); D PROUD OF IT meter 100% -> 3%; E stopwatch AFTER THE REF
STEPPED IN +0.0s -> +0.4s (tape: ref 47.9 s, punch 48.33 s). Test note: each opening = line + its own graphic, so a
win credits the package, not the opening type alone (learnings.md tallies read accordingly). Never "official K.O.":
the official result was a draw. Body: tape under "the ref steps in ... he's out" (KO on "right"),
"DQ or draw?" tag over it, DRAW slam card, freeze on the late punch with LATE / "the ref was already in", SEND key,
CONTROL card. Face scrim (light wall). Music: drill-london-echoes, cut silent from just before "draw" to "they should have".

## Sound (skill reel-sound-design, first reel on it)
hit on the hook punch + on "right" (tape), whoosh on strike / hook out / tape in / each jump cut, thud on DRAW plate,
heartbeat under "someone told me", bell on "my first fight", riser into "draw" (ends where the music cuts), boom on
DRAW, shutter on the freeze, tape crowd audio under both tape clips. Attention rule: no 3 s stretch without a change
(`sd.fill_gaps` added one punch-in at ~27.9 s on A). Render: -15.9 LUFS, -1.5 dBTP; voice sections match the a-roll.

## Renders
| V | Opening | Hook | Length | File |
|---|---|---|---|---|
| A | result | I knocked him out in my first fight and it shouldn't have counted. | 30.0 s | media/2026-11-01-first-fight-lesson/2026-11-01-first-fight-lesson-A(-phone).mp4 |
| B | contrast | My first fight ended in a knockout and I'm the one who should have lost. | 30.8 s | ...-B |
| C | question | Should a knockout count if the refs are already in between? | 29.0 s | ...-C |
| D | reframe | My first knockout is the one I'm least proud of. | 29.2 s | ...-D |
| E | number | One punch. Half a second too late. | 29.2 s | ...-E |
