# Carousels (swipe posts): the middle-of-funnel layer

Why (2026-10-24, from the jayhiette/Dane reference): reels grow the account, belief-shifting carousels build the
trust that turns followers into DMs. Judged on saves, shares, follows and profile visits per 1k reached, not views.
Cadence agreed with Matteo: 1 a day, a new 6th slot at 11:00 New York. Platforms: Instagram, Facebook (album),
Threads (carousel); TikTok photo mode after its app review. YouTube has no image-post API.

## Rules
- **Every carousel starts from a proven hook.** `hook_ref` in `production/carousels/posts.json` must point to an
  `own` hook in `proven.json` (our reels that already won) or a `read` outlier carousel the scout found. Adapt the
  pattern to fighter psychology; never copy another creator's slides. `lint.py` refuses anything else.
- **Slide 1 is animated** on Instagram and Threads (4.5 s silent loop: push-in, two peeks at slide 2, pulsing arrow).
  Text is complete from frame 0 because the first frame is the thumbnail. Facebook gets the still.
- Voice rules apply (context/voice.md): no em dashes, short lines, one CTA on the close slide.
- Automation never approves. Matteo approves like the listicles.

## Pieces
| File | Does |
|---|---|
| `frames.py` | Still frames from the Drive training clips (Carousel workflow, `frames` input) to `production/carousels/frames/` |
| `render.py` | Slides 1080x1350 in `editorial` or `poster` look, `--animate` for the MP4 cover |
| `scout.py` | Monday: other creators' outlier carousels (likes + 3x comments >= 2x their carousel median) to `proven.json`, slides 1-2 saved |
| `lint.py` | The gate (proven hook, 5-10 slides, photos exist, no em dashes, caption, CTA) |
| `report.py` | Monday: every carousel of ours, insights, `results.json` + `analytics/reports/<date>-carousels.md` |

## Weekly loop (Monday)
1. 06:20 UTC Carousel workflow: `scout.py` then `report.py`.
2. Claude: read slide 1 of every `unread` entry in `proven.json` (fill `hook`, `pattern`, status `read`), read the
   report, write what changes in `production/carousels/LEARNINGS.md`, then write the week's 7 carousels from the
   proven hooks that fit.

## Skip rate
Instagram does not expose skip rate or per-slide swipes for carousels (only reels). The report uses
**views per account reached** as the swipe-through proxy: Instagram re-serves an unswiped carousel at slide 2 and
counts that as another view, so a higher ratio means more people saw past the cover.

## Not built yet (after Matteo picks the look)
Posting: Instagram carousel containers (children from R2 URLs, video cover), Threads carousel, Facebook album,
queue items in the 11:00 NY slot through `tools/state.py`, approval on the dashboard.
