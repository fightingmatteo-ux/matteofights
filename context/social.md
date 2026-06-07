# Social Media Status

_Snapshot. Pull live via Windsor (`instagram` connector) before relying on these numbers._

## Windsor connector

| Connector | Account | ID |
|---|---|---|
| `instagram` | Matteo (matteofights) | 17841465098113052 |

Account: joinstance@gmail.com. Rich per-reel insights available (reach, views, avg watch time,
total watch time, saves, shares, engagement) plus captions, permalinks, and follower/views daily
series.

## Baseline (2026-06-05 pull)
- **Followers: 1,651** · Following: 599 · Posts: 40.
- **Mid-viral-surge:** daily reach jumped from ~5/day (pre-May 24) to ~58k/day on Jun 1–2;
  ~165 new followers in 9 days. Driven by one reel (320k views). The window is open — keep posting.
- Latest detail lives in `analytics/snapshots/2026-06-05.json` and `analytics/reports/2026-06-05.md`.

## Top 5 reels by interactions (pulled 2026-06-06)

| Hook (on-screen thumbnail text) | Views | Likes | Shares | Saves | Comments | Interactions |
|---|---|---|---|---|---|---|
| 6 SIGNS YOU WERE BORN TO BE A FIGHTER (IDENTITY) | 331k | 5,221 | 239 | 783 | 76 | 6,543 |
| 8 WAYS TO FIGHT LIKE A KILLER WITHOUT SPARRING 5X/WEEK (TACTICAL) | 161k | 2,744 | 301 | 1,938 | 64 | 5,091 |
| 8 WAYS YOU CAN TRAIN BOXING ANYWHERE (TACTICAL) | 27k | 633 | 148 | 664 | 18 | 1,482 |
| 7 WAYS TO BUILD FIGHT IQ WITHOUT SPARRING EVERYDAY (TACTICAL) | 32k | 713 | 112 | 624 | 15 | 1,480 |
| 7 WAYS I DEVELOPED REAL POWER WITHOUT EVER TOUCHING A WEIGHT (TACTICAL) | 22k | 237 | 26 | 279 | 0 | 544 |

## What drives each metric

**Likes** — agreement/emotional resonance. Like rate is similar across archetypes (~1.5–1.7%). Raw
like count follows view count, not format. Identity wins on total likes because it reaches more people.

**Saves** — 100% tactical, driven by barrier removal. Identity saves at 0.24%; tactical saves at
1.2–2.5%. People save tips to use later; they don't save identity statements. Save rate benchmark:
`train anywhere` = 2.46% (highest), `fight IQ without sparring everyday` = 1.95%, `killer without sparring 5x/week` = 1.20%.

**Shares** — two mechanisms:
- Identity shares: "this is me" expression, amplified by CTA framing ("Repost so born fighters
  find out who they are" = sharing feels like a *gift*, not self-promotion)
- Tactical shares: "my friend needs this" — most shareable hook = `fight like a killer without sparring 5x/week` (301 shares, highest ever)

**Comments** — low unless explicitly invited. `Drop a 🥊 if...` drives emoji engagement. A real
question or contrast at the close gets actual replies.

## Two viral archetypes (the engines)
1. **Tactical listicle** — `"X ways to [outcome] WITHOUT [requirement]"`. Drives **saves** (the
   algorithmic rocket fuel). Always a barrier-removal topic. 8 items > 6. Arrow format proven.
2. **Identity listicle** — `"X signs you [are/aren't a real fighter]"`. Drives **shares + reposts**
   via `Repost this so [specific person] [specific discovery]` CTA. "Born" framing (nature not skill)
   is most flattering and got 331k views.

## Barriers already covered (don't repeat these WITHOUT topics)
- Sparring too often / 5x a week ✓ (hook: "fight like a killer without sparring 5x/week")
- Sparring every day / fight IQ ✓ (hook: "build fight IQ without sparring everyday")
- No gym / train anywhere ✓
- No weights / weightlifting ✓

## Barriers not yet covered (high upside for next tactical reels)
- No training partner (solo training)
- No coach / no access to coaching
- No natural size, reach, or physical gifts
- No years of experience ("too late to start" / "starting from zero")
- No money / cheap training
- No time (busy schedule framing — subhook territory, not done as a hook yet)

## Improved prototype rules (data-derived)
- **Tactical ceiling push:** 8 items, barrier-removal topic not yet covered, explicit `Save this
  before [specific action]` CTA, arrow format `[concept] [emoji] [title] → [elaboration]`
- **Identity ceiling push:** "born" framing or equivalent (nature, not skill), binary subhook
  (`Some people X. / Some people Y.`), list items that feel like psychological X-rays, CTA frames
  sharing as a service not self-promotion
- **Hybrid worth testing:** identity hook + tactical payload — `Some people train. Some people obsess.
  / 7 things obsessive fighters do that normal people think is crazy.`

Watch-time gate: viral reels hold **~10–13s** avg; flops sit at ~5–7s. **Carousels flop** (confirmed,
both album posts <2k views). See [content.md](content.md) and [viral-format.md](viral-format.md).

## Useful Windsor fields (instagram)
- Profile: `followers_count`, `follows_count`, `media_count`, `biography`, `username`.
- Daily series: `reach`/`reach_1d`, `views`, `follower_count_1d` (last 30 days, excl. today).
- Per media: `media_caption`, `media_permalink`, `media_type`, `timestamp`, `media_reach`,
  `media_views`, `media_saved`, `media_shares`, `media_engagement`,
  `media_reel_avg_watch_time` (ms), `media_reel_total_watch_time` (ms),
  `media_reel_total_interactions`, `media_like_count`, `media_comments_count`.
