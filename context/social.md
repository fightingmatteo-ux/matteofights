# Social Media Status

_Snapshot. Pull live via Windsor (`instagram` connector) before relying on these numbers._

## Windsor connector

| Connector | Account | ID |
|---|---|---|
| `instagram` | Matteo (matteofights) | 17841465098113052 |

Account: joinstance@gmail.com. Rich per-reel insights available (reach, views, avg watch time,
total watch time, saves, shares, engagement) plus captions, permalinks, and follower/views daily
series.

## Baseline
_To be filled by the first Windsor pull (Phase 1). Latest snapshots/reports live in
`analytics/snapshots/` and `analytics/reports/`._

## Known winners
- **160k-view reel** — "8 WAYS TO FIGHT LIKE A KILLER, WITHOUT SPARRING 5x/WEEK" (listicle-rant).
- **27k-view reel** — "8 WAYS TO TRAIN BOXING ANYWHERE".
- Pattern: curiosity-gap listicle hooks + `READ DESCRIPTION ⬇️` overlay. Carousels underperform.

## Useful Windsor fields (instagram)
- Profile: `followers_count`, `follows_count`, `media_count`, `biography`, `username`.
- Daily series: `reach`/`reach_1d`, `views`, `follower_count_1d` (last 30 days, excl. today).
- Per media: `media_caption`, `media_permalink`, `media_type`, `timestamp`, `media_reach`,
  `media_views`, `media_saved`, `media_shares`, `media_engagement`,
  `media_reel_avg_watch_time` (ms), `media_reel_total_watch_time` (ms),
  `media_reel_total_interactions`, `media_like_count`, `media_comments_count`.
