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

## Two viral archetypes (the engines)
1. **Tactical listicle** — `"X ways to [outcome] WITHOUT [requirement]"`. Drives **saves** (the
   algorithmic rocket fuel). Top: 160k-view "without living in the gym" (1,937 saves), 32k/27k/21k.
2. **Identity listicle** — `"X signs you [are/aren't a real fighter]"`. Drives **shares + reposts**
   via a `Repost this so real fighters find it` CTA. Top: **320k-view** "6 signs you were born to be
   a fighter" (Jun 1) — the single biggest post and the surge's cause.

Watch-time gate: viral reels hold **~10–13s** avg; flops sit at ~5–7s. **Carousels flop** (confirmed,
both album posts <2k views). See [content.md](content.md) and [viral-format.md](viral-format.md).

## Useful Windsor fields (instagram)
- Profile: `followers_count`, `follows_count`, `media_count`, `biography`, `username`.
- Daily series: `reach`/`reach_1d`, `views`, `follower_count_1d` (last 30 days, excl. today).
- Per media: `media_caption`, `media_permalink`, `media_type`, `timestamp`, `media_reach`,
  `media_views`, `media_saved`, `media_shares`, `media_engagement`,
  `media_reel_avg_watch_time` (ms), `media_reel_total_watch_time` (ms),
  `media_reel_total_interactions`, `media_like_count`, `media_comments_count`.
