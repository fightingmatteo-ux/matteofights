# STATUS: open items, one place

_Updated 2026-10-19 07:30 UTC. Every session: read this after CLAUDE.md, update it when you close or add an item._

Legend: **DO** = needs action now, **MATTEO** = only Matteo can do it, **WAIT** = blocked on someone else, **OK** = done, kept for one cycle.

## Urgent

| # | Item | Status | Next step |
|---|---|---|---|
| 1 | Saenchai v3 render A | OK | Rendered, on `media` release (10-18 12:55Z), Drive upload triggered 13:05Z |
| 2 | Saenchai v3 render B | **DO / MATTEO** | Render died ~17:44 local, nothing running. Matteo starts it (command below). Then `media.sh push` + `drive-upload.yml` |
| 3 | Saenchai v3 render C | **DO / MATTEO** | Not started. Run after B finishes, never in parallel |
| 4 | Saenchai trial-reel slots | **DO** | queue.json: A 14:00Z, B 16:30Z, C 19:00Z on 10-18. B and C slots must move later if their renders are not done; until then the OLD 10-16 cut sits on the release under the same name |
| 5 | Saenchai approval | **MATTEO** | `approved:false` on all three. Only Matteo approves (dashboard Home, hold-to-approve) |
| 6 | YouTube cross-post | **DO (verify)** | Secrets YT_* set 10-18 12:57Z. 5 failed records reset in crosspost.json. Check the next Cross-post run: if 401 `youtubeSignupRequired` again, the chosen Google account still has no channel |
| 7 | YouTube API audit | **WAIT** | Unconfirmed. Uploads with `privacy: public` may be forced private until approved |

Render command for Matteo (PowerShell, from the repo root). One variant at a time, minimized, idle priority:

```powershell
$p = Start-Process "C:\Program Files\Git\bin\bash.exe" -ArgumentList "production/reels/2026-10-16-saenchai-bigger-men/render.sh B" -WindowStyle Minimized -PassThru; Start-Sleep 2; $p.PriorityClass = 'Idle'
```

Log: `media/2026-10-16-saenchai-bigger-men/renders/render_bc.log` (ends with `ALLDONE`).

## Open, not urgent

| Item | Status | Next step |
|---|---|---|
| Run from anywhere, phase 1 (`docs/superpowers/plans/2026-10-18-phase1-foundation.md`) | **MATTEO** | Not started. Needs from his phone: a Modal account + token, an R2 API token, both saved as GitHub secrets (names in the plan). Renders go to Modal, never GitHub runners |
| GitHub Actions minutes | DO (verify) | ~1,470 min in 7.5 days (10-11 to 10-19), about 3x the free 2,000/month. Fixed 10-19: dashboard deploy skips no-op runs + path filter. Biggest left: GitHub Pages rebuild on every push (417 min/week), see next row |
| Public site matteofights.me | **MATTEO** | Settings > Pages > Source = "GitHub Actions", then run the "Public site" workflow. Stops the rebuild-on-every-push and stops publishing `docs/superpowers/` (private specs, likely public now at matteofights.me/superpowers/specs/...) |
| Media cleanup | OK | Daily, `tools/video/lifecycle.py`: posted videos deleted after 7 days + all cross-posts, record in `production/archive/reels.json`. First real deletions ~10-21 |
| Telegram | OK | Alerts only, each with a link to the control center. Decisions on the dashboard (old buttons + typed ideas still work) |
| Cloudflare ticker (`tools/ticker`) | Likely not deployed, so posts run on late GitHub cron | MATTEO creates a fine-grained PAT (Actions read/write), then `wrangler deploy` + Worker secret `GH_TOKEN` |
| TikTok | WAIT | App review |
| Meta oEmbed | WAIT | Not approved; `ig_discovery` scans tracked competitors instead |
| IG token | Expires 2026-12-13 | `ig.py refresh` before then |
| Threads token | Expires 2026-12-14 | `crosspost.py threads-refresh` before then |
| IG_COOKIES secret | Expired, no longer blocking: Fetch video now retries yt-dlp without cookies (worked for Ferris 10-19) and falls back to the API, then the embed page | Optional refresh if logged-out downloads start failing |
| FB_USER_TOKEN | Set 2026-10-15, 60-day token, so expires ~2026-12-14. Expiry not tracked | Add tracking |
| Listicle clip sheets | MATTEO | Waiting on his yes (Telegram or dashboard) |
| Next week's 21 listicles (18 to 28 Oct) | **MATTEO** | Reviewed, 6 clips swapped and re-rendered 10-18 15:00Z. Waiting on his yes (dashboard / Telegram / chat). #1 posts 12:30 NY today only if approved |
| control.matteofights.me | OK | Live behind Cloudflare Access (checked 10-18) |

## Rules (short)

Never set `approved:true`. Never commit `secrets/`, `data.json`, `covers/`, `voice.wav`, `snaps/`. Commit only your own paths. Never run renders as session background jobs, and never render variants in parallel.
