# @liamjohnston.ai "Claude just learned to fix your offer" carousel, 2026-10-24

Source: https://www.instagram.com/p/De2-09Cjnyx/ (@liamjohnston.ai, 107k followers; 137 likes, 384 comments
within a day: comments ~3x likes, driven by "Comment SOLD"). Matteo: "this is the style carousel I want to be
posting, about boxing instead of AI".

Files: `content-bank/references/videos/liamjohnston-carousel-full/slides/NN-contact.jpg` (10 frames, 1 per
second, of each slide) and `slides/NN/` (2 fps frames). The 9 mp4s are on the media release as
`liamjohnston-carousel-full-slideNN.mp4`. Every slide is a **10 s, 1080x1350, silent video**.

## The style in one line
A dark product UI that **builds itself on every slide**. No photos, no stock, no faces. Each slide is one
interface element animating in: a counter, a dot grid, a bar chart, a checklist ticking, text typing into a box.
You swipe to watch the next thing assemble.

## Design system (copy this exactly, change the accent)
- **Ground:** near-black (#151515 ish) with a fine grain/noise texture, never flat black.
- **Headline, top centre, same spot every slide:** line 1 bold geometric sans in white ("400 saw the offer."),
  line 2 italic serif in the accent colour ("Only 1 bought."). A statement, then the twist. 2 lines, max ~6 words each.
  Our fonts already match: Geist 800 + DM Serif Display Italic.
- **Accent:** one colour only (his is a salmon orange). Used on: line 2, one number, ticks, active states. Ours: brand red #c82020.
- **Cards:** dark grey glass panels, 1 px light border, 16-20 px radius, soft inner glow. Small labels in grey
  sans (12-14 px at 1080), values in bold white.
- **Furniture:** slide number "01" top right, a signature mark bottom right. Nothing else. No swipe arrows.
- **Icon:** one recurring brand mark (the Claude burst) used as bullet/avatar everywhere. Ours: a glove or the M mark.
- **Motion:** everything eases in (fade + 8-12 px rise), items arrive one at a time ~0.6-1 s apart, numbers count up,
  bars fill left to right, ticks pop in. The headline is static from frame 0 (frame 0 is the thumbnail). The last
  ~2 s hold the finished state so a fast swiper still reads it.

## The 9 slides, beat by beat (what animates)
| # | Headline (sans / *serif*) | Component | Motion |
|---|---|---|---|
| 1 | Claude just learned / *to fix your offer.* | Wireframe man who IS a scale: $ tag vs empty pan | Blocks PROMISE, PROOF, GUARANTEE drop onto the pan one by one until it tips. The whole thesis, acted out |
| 2 | 400 saw the offer. / *Only 1 bought.* | Card "Sales page, one month": dot grid + big number | Dots fill as the number counts 89, 222, 356, 400. Then rows: "Booked a call 2 or 3", "Bought 1" (accent). Then "WHY THEY LEFT" chips: "No clear promise", "Looks like free info" |
| 3 | The best offer skills, / *made into one.* | Header pill "Offer Master, 0 skills read" + list of GitHub repos | Repos stream up and get absorbed, counter climbs to "from 18 skills", then a 2-col checklist of the 12 rules ticks in |
| 4 | It beat the top skill / *9 times out of 9.* | "BLIND SCORES, OUT OF 10" bar chart (4 rows) + 3x3 grid "9 BLIND ROUNDS" | Bars fill one by one (8.0 in accent, others grey), then grid cells flip to "WON" row by row |
| 5 | How it fixes your offer / *in 4 steps.* | A chat input box | The prompt types itself, then 4 step cards appear and tick one at a time with a one-line finding under each |
| 6 | What buyers say / *vs what they mean.* | Two columns THEY SAY (italic quote chips) / THEY MEAN (card + accent fix) | Left quote appears, line draws, right card answers with the fix. 4 rows |
| 7 | Same price. / *A better offer.* | Spec card NAME / PRICE / FIRST WIN / GUARANTEE / WHY NOW, all "None" | Old name gets struck through, new values type in row by row, labels turn accent as they fill |
| 8 | The install is one step. / *Paste the link.* | GitHub card + clone URL + chat box | Cursor clicks Code, copies, pastes, "Cloned", "Added to your skills" ticks |
| 9 | Want the full / *Offer Master skill?* | Pill button "Comment **SOLD**" + one line + burst icon | Near-static, the icon pulses. CTA only |

## Why it works (the transferable rules)
1. **Story arc, not a list:** promise (1), pain in numbers (2), how it was made (3), proof (4), how it works (5),
   insight (6), before/after (7), how to get it (8), CTA (9). Every slide answers the question the last one raised.
2. **Each slide is one idea + one component.** Never two charts, never a paragraph.
3. **The animation IS the content.** Counting up, ticking, striking through: you watch the argument happen, which
   is why people stay on each slide for 10 s (watch time per slide on video slides).
4. **Headline twist on line 2 in the accent serif.** Same pattern 9 times, so it reads as one system.
5. **Comment keyword gate on the last slide AND in the caption.** Same mechanic as our COMMENT PROTOCOL.
6. **Proof is shown as UI, not claimed in text** (scores, rounds won). We copy the look, never the trick of
   inventing numbers: every number on our slides is ours or obviously illustrative.

## Boxing version: the same machine, our topic
Brand swap: accent orange to red #c82020, the burst to our mark, signature to `@matteofights` handwritten.
Topic stays fighter psychology (CLAUDE.md). Hook adapted from the read outlier "If your first reaction to X is Y,
you're the problem" (contrast + identity) in `production/carousels/proven.json`.

**Carousel A: "I'll spar when I'm ready."** (fear of sparring, our audience's #1 mental block)
| # | Headline | Component and motion |
|---|---|---|
| 1 | "I'll spar when I'm ready." / *You never will.* | Wireframe fighter standing on a scale: FEAR block on one pan; READY, ROUNDS, REPS drop onto the other until it tips |
| 2 | Months of bag work. / *Zero rounds sparred.* | Card "Your last 3 months": a calendar grid of 90 dots fills grey (bag, pads, runs), the "Sparring" row stays at 0 in red |
| 3 | Fear isn't the problem. / *Waiting for it to leave is.* | Checklist of what the brain does, ticking: "Threat spotted", "Freeze", "Wait for a safe moment", "Moment never comes" |
| 4 | Ready comes / *after round one.* | Bar chart "How nervous, 1 to 10": before round 1, after round 1, after round 5, after round 20 (illustrative, labelled as such) |
| 5 | Get in the ring / *in 4 steps.* | Chat box types "/coach I'm scared to spar", then 4 cards tick: "Ask for technical sparring", "50% power, 2 rounds", "One goal: keep your hands up", "Same partner next week" |
| 6 | What fighters say / *vs what they mean.* | THEY SAY: "I'm not fit enough yet", "I'll look stupid", "I'll get hurt", "Next month" / THEY MEAN + fix |
| 7 | Same gym. / *A different fighter.* | Spec card YOU, 3 MONTHS AGO: SPARRING None, GOAL "get ready", then struck and rebuilt: "2 light rounds a week", "keep my hands up" |
| 8 | Your first round / *starts at home.* | THE PROTOCOL page card: quiz ticks, result "Your priority: Conditioning", workout timer starts |
| 9 | Want the full / *protocol?* | Pill "Comment **PROTOCOL**" + "I'll send you the link." |

Other topics that fit the same 9 beats: "Why you gas in round 2 (it's not cardio)", "What your coach says vs
what he means", "You don't lack discipline. You lack this.", "The 3 a.m. thoughts before your first fight".

## How we build it (proposal, not built yet)
Our renderer (`tools/carousel/render.py`) already does HTML/CSS slides in Chromium and an animated cover.
This style needs every slide animated:
- One HTML component per beat (`scale`, `counter-grid`, `checklist`, `bars`, `chat-steps`, `say-mean`,
  `spec-card`, `cta-pill`) driven by CSS keyframes with delays, a 10 s timeline, last 2 s held.
- Capture each slide as a 10 s 1080x1350 mp4 (Playwright frame capture, as `--animate` already does for the cover).
- Instagram and Threads carousels take video children; Facebook gets frame 10 s stills.
- The cover's wireframe figure is the one asset to make per post (Higgsfield/Firefly render of a wireframe boxer,
  or a traced outline of Matteo's own footage via the `cutout.py` matte, which is more ours).
