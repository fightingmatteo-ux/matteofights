# STATUS: open items, one place

_Updated 2026-10-19 08:30 UTC. Every session: read this after CLAUDE.md, update it when you close or add an item._

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
| Editorial look (kaixerb reference, 10-20) | OK | Approved by Matteo (v5). Saved as the default: `production/reels/_TEMPLATE/editorial/`. Next talking-head reel uses it. Leave headroom above your head when filming |
| Saenchai A/B/C trial reels | **MATTEO** | Rescheduled to 2026-10-20 9:30 / 12:00 / 15:30 NY. Approve on the control center **Home** tab: "3 trial reels need your yes" -> Hold to approve. Not approved = nothing posts |
| Listicle sounds | OK (10-20) | Factory rotates Echo Sax End / INSONAMIA / Echo Sax End / Memory Reboot from the next Sunday batch (`own_proven.json`). First post with an attached sound + trial is untested: check it |
| No-filming slate (10-20) | **MATTEO** | `production/competitors/no-filming-2026-10-20.md`. #1 freeze C editorial is rendered (sent in chat): your yes to post it as a trial reel |
| Fight-breakdown reels (no talking) | **MATTEO** | Footage is on your PC (`media/saenchai-broll/`). Upload it to Drive, or add Actions secret `YT_COOKIES` (cookies.txt, logged-in YouTube burner) so Fetch video can pull YouTube. Plan: `production/competitors/no-filming-2026-10-20.md` round 2 |
| You-be-the-judge reel | **MATTEO** | Film `production/reels/2026-10-20-you-be-the-judge/` (needs the first-fight KO clip from Drive) |
| Audio API (`tools/instagram/audio.py`) | OK (checked 10-20) | FB_USER_TOKEN has instagram_basic + instagram_content_publish: library sounds can be attached. Sound scout (`sound-scout.yml`, Mondays) -> `production/sounds/proven.json`: niche outliers run on original audio, no cleared track yet |
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
