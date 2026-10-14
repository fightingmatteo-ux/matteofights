# Reel ledger: every variant, what it was, how it did

Generated. After posting, link each variant: `python -P tools/analytics/ledger.py link <media_id> <slug> <V>`
(`ig.py trial --slug --variant` does it for you). Metrics arrive daily from the **Reel ledger** Action
(our Meta app) or from a Buzzfy pull in a session (`ledger.py ingest <snapshot>`), then `ledger.py build`.
All variants of a test go up as trial reels the same day; the call is made at 72 h.
Reels expose no follows, so the winner = most views at ~72 h (Instagram's own verdict on non-followers),
unless one variant clearly out-shares the others. Only the "Patterns so far" section is hand-written.

<!-- ledger:start -->
_Built 2026-10-14 12:50 UTC from `analytics/reel-metrics.jsonl` by `tools/analytics/ledger.py build`. Do not edit between the markers; edit `production/reels/posted.json` and rebuild._

### Status
- Last grid post: 2026-09-24 (19 days ago). **Too long: followers see nothing new. Share a winner today.**
- Baseline: median views of a settled reel = 2,755 (over 85 reels); ×median compares to it.
- `2026-10-12-origin-story`: waiting, youngest variant is 21 h old (call at 72 h).
- 3 recent trial reel(s) not linked to a reel folder: `17940059640367921`, `18382008682224632`, `18660007336005034`

| Posted | Reel | V | Caption opens | Grid | At | Views | ×median | Reach | Watch | Skip | Shares | Saves | Comm. | Verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2026-10-13 | `2026-10-12-origin-story` | A2 | [My first Muay Thai fight: knocked him out, still got a ](https://www.instagram.com/reel/DecCFynzIk9/) | trial | 21h ⏳ | 2,266 | 0.8 | 1,961 | 13.2s | 32% | 1 | 4 | 0 | pending |
| 2026-10-12 | `2026-10-12-origin-story` | A | [My first fight, I knocked the guy out. It was still a d](https://www.instagram.com/reel/DeZ1ClETXec/) | trial | 43h ⏳ | 1,678 | 0.6 | 1,448 | 15.8s | 32% | 3 | 4 | 0 | pending |
| 2026-10-11 | `worst-decision` | v2 | [Worst fighting decision of my life: a BJJ takedown on c](https://www.instagram.com/reel/DeXUBkDzbBG/) | trial | 66h | 2,725 | 1.0 | 2,447 | 17.0s | 32% | 0 | 3 | 0 |  |
| 2026-10-06 |  |  | [I was free](https://www.instagram.com/reel/DeJHPRgKyZ6/) | trial | 199h | 388 | 0.1 | 335 | 5.5s | 61% | 1 | 0 | 0 |  |
| 2026-10-05 |  |  | [If you're starting combat sports as an adult, don't spa](https://www.instagram.com/reel/DeH4_voTskV/) | trial | 210h | 2,114 | 0.8 | 1,925 | 7.6s | 45% | 4 | 25 | 0 |  |
| 2026-10-05 |  |  | [Most adults quit combat sports by week three. Here's wh](https://www.instagram.com/reel/DeHvV-2zPkN/) | trial | 211h | 2,088 | 0.8 | 1,787 | 11.4s | 39% | 24 | 47 | 2 |  |
| 2026-09-24 |  |  | [Which number got you? Be honest](https://www.instagram.com/reel/DdrkdJQTdCY/) | ✅ | 474h | 3,426 | 1.2 | 2,904 | 17.2s | 37% | 10 | 15 | 21 |  |
| 2026-09-24 |  |  | [Yoga has ClassPass. Runners have Strava. Fighters have ](https://www.instagram.com/reel/DdqqI0DyTfp/) | ✅ | 482h | 2,579 | 0.9 | 2,115 | 15.5s | 34% | 7 | 18 | 55 |  |
| 2026-09-23 |  |  | [(hashtags only)](https://www.instagram.com/reel/DdoggH6TDb4/) | trial | 502h | 812 | 0.3 | 605 | 11.0s | 70% | 0 | 2 | 0 |  |
| 2026-09-22 |  |  | [There's no such thing as an ex-fighter.](https://www.instagram.com/reel/DdmVi93zYnO/) | ✅ | 523h | 13,069 | 4.7 | 6,272 | 10.3s | 47% | 9 | 38 | 2 |  |
| 2026-09-22 |  |  | [I'm building an app for fighters. Not gym bros. Not run](https://www.instagram.com/reel/Ddl7jVgzfJV/) | trial | 526h | 2,358 | 0.9 | 1,951 | 10.2s | 39% | 7 | 16 | 53 |  |
| 2026-09-08 |  |  | [Paying for boxing classes won't automatically make you ](https://www.instagram.com/reel/DdBwrd_T7x1/) | ✅ | 864h | 2,249 | 0.8 | 1,960 | 15.3s | 38% | 6 | 57 | 2 |  |
| 2026-09-07 |  |  | [5 things I wish someone told me before my first 5 boxin](https://www.instagram.com/reel/Dc_KvSVTSOm/) | trial | 888h | 3,321 | 1.2 | 2,070 | 8.9s | 47% | 4 | 15 | 0 |  |
| 2026-09-06 |  |  | [Iykyk](https://www.instagram.com/reel/Dc8blmkz5Sr/) | ✅ | 913h | 10,162 | 3.7 | 5,548 | 6.9s | 29% | 77 | 20 | 8 |  |
<!-- ledger:end -->

## Patterns so far
- _Add a line whenever a test is decided. Keep it to what the numbers showed._
