# Connected Tools & MCPs

_What's wired up and what each is for._

| Tool | Account | Use for | Status |
|---|---|---|---|
| **Windsor.ai** | joinstance@gmail.com | Instagram analytics (`instagram` connector, matteofights, ID 17841465098113052) | Connected |
| **Windsor.ai** | joinstance@gmail.com | Facebook Organic analytics (`facebook_organic` connector, "Matteo Fights" Page, ID 1070947222779004) | Connected (confirmed 2026-06-16 — previously miscategorized as not connected, that was wrong) |
| **Higgsfield** | — | Image/video generation; `virality_predictor` to score reels before posting | Available |
| **Buzzfy** | — | Reel tracking + viral research for @matteofights and boxing/combat accounts (`.mcp.json` → `https://mcp.buzzfy.co/mcp`) | Added 2026-10-14 — sign in on first use; tools not yet verified |

## Windsor field quirk (facebook_organic)
`get_fields` errors on this connector (pydantic validation bug) — field discovery is broken. Use
known-good fields directly with `get_data` instead: `date`, `page_fans` (total, reliable),
`page_impressions`, `page_post_engagements`, `post_created_time`, `post_message`,
`post_impressions`, `permalink_url`. **`page_fan_adds` and `page_fan_adds_unique` always return 0
— broken/unpopulated field, do not use to measure growth.** Use day-over-day delta on `page_fans`
instead. `post_engaged_users` also returns null — broken.

## Notes
- Windsor's older account (linked to Gypsy Amazon) is full; this project uses the **joinstance**
  account. Don't confuse the two.
- Higgsfield `virality_predictor` is a useful pre-post check for reels (Phase 2+).

## Planned (later phases)
- **Claude Agent SDK + Anthropic API** — the Jarvis backend (Phase 3).
- **Instagram Graph API (Content Publishing)** — real posting/scheduling (Phase 4); requires a
  Business account linked to a Facebook app + access token.
- **Optional:** sessionid scraper for grid/caption backfill; browser automation for native
  Professional-Dashboard numbers Windsor doesn't expose (retention curve, audio attribution).
