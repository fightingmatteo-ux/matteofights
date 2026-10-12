---
slug: 2026-10-12-origin-story
status: edited
pillar: story → mindset (pinned profile reel)
format: story, paradox payoff (KO → draw), 5-country montage
credibility: own experience (5 countries, first fight)
cta: follow for the mental side of fighting + comment "Ever had a fight you won taken from you?"
test_variable: hook
---

# Origin story (pin)

Talking points: `TALKING-POINTS.md`. Supersedes the injury-led draft in
`content-bank/captions/drafts/2026-10-12-pinned-origin-story/`.

## Variants
| V | Hook (spoken, verbatim) | On-screen hook text | Cover |
|---|---|---|---|
| A | My first fight, I knocked the guy out. It was still a draw. | KNOCKED HIM OUT. STILL A DRAW. | ring photo |
| B | Before my first fight, someone told me: if you don't knock him out, you lose. | "KNOCK HIM OUT OR YOU LOSE" | ring photo |
| C | People think combat sports is just violence. My first fight is why I know it isn't. | IT'S NOT JUST VIOLENCE | ring photo |

## Footage plan (stock until the b-roll bank is shot)
| Beat | Own footage (Drive) | Stock |
|---|---|---|
| Setup / KO | the KO clip from his fight video: <1 s of the clinch, cut on the right hand, freeze + red circle, slow the half-second after; shown ONCE on "he slept". Pinned reply idea: "Elbows in the clinch are legal in Muay Thai. The right hand during the break wasn't. I was 16." | Mixkit referee 40997/40991 |
| Chess | sparring innov8 | Mixkit chess 49731 (vert), 5339 |
| Zurich | sparring innov8 | Mixkit Zurich 4367 |
| Essaouira | padwork morocco | Mixkit Morocco streets 26822/26817 |
| São Paulo | — | Wikimedia CC0 photo or text card |
| Koh Samui | pads super8 / chaiya | — |
| Rome | boxing rome simba, sunrise skipping rome | Mixkit Colosseum 47981/11039 |
| Appendix | — | Mixkit hospital 4745, heart monitor 46365 |
| Now / close | — | Mixkit Bangkok night 21920 |

## Edit (2026-10-12)
Filmed handheld in Bangkok (Edits app, one long take). Takes picked in `work/takes.json`; A-rolls via
`assemble.py`; one template for all variants (`work/template.html`, `bash build.sh <V>`).
Loop: close + bridge + hook filmed as one continuous take per variant → seamless replay.

| V | Spoken hook | On-screen | Length | Render |
|---|---|---|---|---|
| A | "…my first fight when I knocked the guy out, and there was still a draw." | KNOCKED HIM OUT. / STILL A DRAW. | 59.2 s | `media/2026-10-12-origin-story/renders/origin-A.mp4` |
| B | "Someone told me, if you don't knock him out, you're gonna lose." | "KNOCK HIM OUT / OR YOU LOSE." | 53.7 s | `…/origin-B.mp4` |
| C | "People think combat sports is just about violence. My first fight is how I know that's not true." | COMBAT SPORTS / IS NOT JUST / VIOLENCE. | 54.5 s | `…/origin-C.mp4` |

Footage: own (ring photo, fight clips cleaned + 2x upscaled, KO from "Muay Thai fight matteo" 0:47.9–0:49.5
starting after the elbows, freeze on the right hand; Impact MMA Zurich; Essaouira pads; Super 8 Samui;
Audace Rome; Bangkok = Matteo talking) + stock (Mixkit chess 5339; Wikimedia CC0 São Paulo Sé cathedral).
Music: launch soundtrack bed, cut to silence on "The result? A draw.", back in on the lesson.
