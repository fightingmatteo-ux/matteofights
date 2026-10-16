---
slug: 2026-10-16-saenchai-bigger-men
status: edited
pillar: psychology
format: legend-credibility
credibility: Saenchai (fought heavier opponents; widely reported)
cta: save + share ("Save this for your next spar. And send it to the smallest guy in your gym."), comment question in caption
test_variable: hook
---

# Saenchai vs bigger men: win the reset

## Talking points
See TALKING-POINTS.md (reading script this time, hooks verbatim).

## Variants
| V | Hook (spoken, verbatim) | On-screen hook text | Length | Render (Drive output + media release) | Queue (NY) |
|---|---|---|---|---|---|
| A | Saenchai fought bigger men his whole career. Here's how he thought about it. | SAENCHAI FOUGHT / BIGGER MEN / HIS WHOLE CAREER | 45.2 s | saenchai-bigger-men-A.mp4 | Oct 16 09:30 |
| B | If you always spar someone bigger than you, steal this from Saenchai. | ALWAYS SPARRING / SOMEONE BIGGER? | 43.2 s | saenchai-bigger-men-B.mp4 | Oct 16 12:00 |
| C | Bigger guys win the trade, but Saenchai never traded. | BIGGER GUYS WIN THE TRADE. / SAENCHAI NEVER TRADED. | 42.3 s | saenchai-bigger-men-C.mp4 | Oct 16 14:30 |

Edit ("late-night film study", 2026-10-16): lamp-lit A-roll; Saenchai clips as game tape (letterboxed over a blurred
copy, grain, TAPE labels); coach marks (STEP OFF arrow, CATCH circle, SWEEP / START OVER labels); a RESETS counter
01 -> 02 -> spins to a gold 10 on "ten times" over the Harrison clinch throw; WIN THE RESET card; save + send icons;
loop line into the hook. Music: epic-bold-drums (Pixabay, not Content ID registered), enters with the first tape, its
break re-enters on "ten". Build: `python -P build_variant.py <V>` then `npx hyperframes@0.8.147 render -q delivery`.
Dropped: Harrison 13:03 clip (it was Saenchai on the canvas, not Harrison).

Shared body: beats 1-6 in TALKING-POINTS.md, then the variant's own loop line (beat 7), hard cut into the hook for a seamless loop. Edit: word-pop subtitles, SAENCHAI name card on beat 1, no fight footage.

## Caption + hashtags (Instagram source; crosspost adapts it for Facebook, YouTube, Threads)
```
Bigger guys win the trade.
Saenchai never traded.

He spent most of his career fighting heavier men.
He didn't out-muscle them. He made them start over.
Step off the line. Catch the kick. Sweep. Reset.

Next time you spar someone bigger, don't win the exchange. Win the reset.

Save this before your next spar. Send it to the smallest guy in your gym.

Who's the fighter whose mind you'd steal?

#muaythai #fightermindset #boxing
```
YouTube Short title: Saenchai vs Bigger Opponents: The Mindset 🥊 #shorts
Threads (written post): Saenchai spent years fighting bigger men. He never tried to out-muscle them. He made them reset, over and over. Most beginners do the opposite. Who's the fighter whose mind you'd steal?

## Posting log (Matteo posts all 3 trial reels the same day, 2-3 h apart; auto-share OFF)
| V | Posted (local time) | Type | IG media id | Notes |
|---|---|---|---|---|
| A | | trial | | |
| B | | trial | | |
| C | | trial | | |

## Saenchai B-roll (Matteo's call 2026-10-16: commentary over short clips; keep each clip <= 3.5 s, always under his voice + subtitles)
Local only (gitignored): `media/saenchai-broll/clips/`. Sources downloaded with yt-dlp:
YOKKAO "Saenchai sparring in Canada" (aW6ew2j1ZmQ), Liam Harrison vs Saenchai 2, April 2011 (_sWmii41j-8);
also on disk for more cuts: Samkor vs Saenchai (XlLvvN4OfaM), Saenchai vs Thongthai (FTYRm8Z_t-k).

| Clip | Source + time | Under the line |
|---|---|---|
| 00-intro-saenchai | YOKKAO 0:00-0:03 | beat 1 + SAENCHAI name card |
| 01-step-off-line | YOKKAO 0:29.5-0:31.8 (bigger guy kicks, Saenchai slides off) | "He'd step off the line" |
| 02-catch-and-sweep | YOKKAO 0:31.5-0:34.8 (catches the kick, dumps him) | "Catch the kick. Sweep them." |
| 03-dumped-to-floor | YOKKAO 0:16.0-0:18.8 | "And make them start over" |
| 04-reset-to-stance | YOKKAO 0:35.0-0:37.5 (both back to stance) | "Every reset costs the bigger guy energy" |
| 05/06-harrison-down | Harrison 12:55.5-12:58, 13:03.5-13:05.5 | "Do that ten times" |
Transform each: 9:16 crop on the fighters, slight zoom or slow-mo on the key frame, subtitles on top.

## Edit v2 (2026-10-16, after "you didn't pick the best takes ... double cut ... freeze frames")
Takes chosen by `reel-kit/scripts/score_takes.py` (re-transcribe each candidate with a disfluency prompt, penalise
hesitations, repeats, fillers, low-confidence words), every cut checked with `verify_cut.py`; voice cut from
`assets/voice.wav` (sample accurate). Final takes in `work/takes.json`. B-roll is cut per line by `make_broll.py`
(slot-fitted, slow-mo up to 2x, never freezes): Riddick Bowe x Saenchai @ 13 Coins Gym (EXPvZzeb5cE) for size,
sweep, start over, frustration; YOKKAO Toronto for trade, teep, step/catch, dump, stance; Harrison 2011 for "ten
times". Look: late-night film study, RESETS counter 01 -> 02 -> 10, Bowe heavyweight callout, WIN THE RESET card.
Cross-post: one hook per platform, never the same clip twice (`crosspost_to` in queue.json): A -> YouTube Shorts,
B -> Threads, C -> Facebook. Talking-head captions keep their full body on every platform (`captions.prose`).
