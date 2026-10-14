---
slug: 2026-10-14-freeze-in-sparring
status: edited
pillar: psychology
format: talking-head listicle (3 numbered fixes), loops into the hook
credibility: own experience
cta: on-screen "COMMENT 1, 2 OR 3?" + caption (no spoken CTA: last reel lost viewers before it)
test_variable: hook
---

# Why you freeze in sparring (3 fixes)

Talking points: `TALKING-POINTS.md`. Talking-head take on the two proven listicles (6 signs = 331k, 8 ways = 161k):
number promised up front, beginner-vs-fighter identity, usable payoff. ~22–25 s, no personal story.

## Variants
| V | Hook (spoken) | On-screen hook text | Length | Render |
|---|---|---|---|---|
| A | If you freeze when you spar, it's not your technique, it's your head. And there are three things you can do to fix it. | FREEZE / IN SPARRING? / IT'S YOUR HEAD. | 24.6 s | media/2026-10-14-freeze-in-sparring/freeze-A.mp4 |
| B | Fighters and beginners think completely differently in sparring. Here's the difference. | FIGHTERS / & BEGINNERS / THINK / DIFFERENTLY | 23.3 s | freeze-B.mp4 |
| C | Beginners try to win every exchange. Fighters don't. Here's what they do instead. | BEGINNERS TRY / TO WIN EVERY / EXCHANGE. / FIGHTERS DON'T. | 22.1 s | freeze-C.mp4 |

## Edit (2026-10-14)
One 3-min Edits-app recording (Drive `1qCY0cgJ_W7AhY34gKJu5602sveTPPzSu`), no slates; takes picked by order in
`work/takes.json`. Each variant ends on "...and reset. Because" and replays into its hook ("Because if you freeze..."),
so the loop is one sentence. Fix cards SHOCK / OVERLOAD / SPIRAL; captions moved up to y800 (face fills the frame).
No music bed (none in the cloud session): add a trending track at low volume in the IG app.
Words from the Fetch-video workflow transcript (cloud can't download Whisper models). GSAP bundled locally in
`assets/lib/` (render browser can't reach the CDN).

## Motion graphics (v2, 2026-10-14)
All entrances use a closed-form damped spring (`spring()` in the template), no CSS easing.
- Red skewed slash wipe into every fix (replaces white flashes).
- 01 SHOCK: impact rings + rays + camera hit on "punched"; FAILURE struck through -> "= INFORMATION".
- 02 OVERLOAD: 13 fight words flood the card on "everything", fall away on "jab", JAB springs to hero size.
- 03 SPIRAL: card springs back on "step back", breathing ring grows over "deep breath", snaps on "reset";
  label SPIRAL -> RESET.

## Motion graphics v3 (2026-10-14): full-screen animated cutaways
Matteo: v2 "too basic". v3 cuts from the face to six illustrated scenes (voice continues, captions drop to y1440,
cards hidden while a scene is up). Scenes slide up on a spring, exit with a zoom-fade; dark red radial bg + drifting grid.
- T (turn line): 01 SHOCK / 02 OVERLOAD / 03 SPIRAL tiles spring in from alternating sides, then 01 is focused.
- S1a: a glove flies at the lens and lands on "punched": flash, crack lines draw, shake, SHOCK slams.
- S1b: FAILURE struck through -> INFORMATION, scan line + a fight log types (hit / from / why / fix).
- S2: mental-load meter fills to 100% while 13 skill pills flood and jitter; on "pick" they blow out, JAB locks
  in a bracket reticle, meter drops to 12%, "ONE JOB · ONE ROUND".
- S3a: a red spiral draws inward with GET CAUGHT -> GET MAD -> CHASE IT -> CAUGHT AGAIN; "step back" recedes it,
  STEP BACK arrow springs in.
- S3b: breathing rings grow with INHALE while a clock arc fills; RESET snaps, shockwave, BACK TO ZERO.

## Caption
Your freeze isn't a technique problem.

1. Shock: expect to get hit. It's information, not failure.
2. Overload: one job per round. Just the jab.
3. Spiral: got caught? Step back, breathe out, reset.

Comment the number you struggle with. Follow for the mental side of fighting.

#sparring #boxing #muaythai #fightermindset

## Results (fill at 72 h)
| V | Views | Follows | Shares | Saves | Comments | Avg watch |
|---|---|---|---|---|---|---|
