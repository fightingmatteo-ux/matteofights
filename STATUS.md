# STATUS: open items, one place

_Updated 2026-10-24 11:50 UTC. Every session: read this after CLAUDE.md, update it when you close or add an item._

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
| Listicle sounds | OK (10-20) | Every listicle: original Echo Sax End every other reel, else Caleb Arredondo's Echo Sax Endless / Echo Sax Feeling Blue (pinned ids, Matteo 10-20). Attaching works: round-three posted 10-20 with Echo Sax End (Take 2) via the API (instagram.com/reel/Detl951FIOw); confirm in the app it shows as a trial reel |
| No-filming slate (10-20) | **MATTEO** | `production/competitors/no-filming-2026-10-20.md`. #1 freeze C editorial is rendered (sent in chat): your yes to post it as a trial reel |
| Saenchai editorial re-cut | OK (10-20) | A/B/C rendered in the cloud (Modal, ~10 min each) after Matteo's notes: fewer jump cuts, 7 tape clips instead of 11, no slow-mo. Approved by Matteo; queue posts `2026-10-21-saenchai-editorial-<V>-phone.mp4` (R2) at 19:30Z 20/21/22 Oct. Release copies still v1 (fallback only); new snapshot check not run |
| Fight-breakdown reels (no talking) | **MATTEO** | Footage is on your PC (`media/saenchai-broll/`). Upload it to Drive, or add Actions secret `YT_COOKIES` (cookies.txt, logged-in YouTube burner) so Fetch video can pull YouTube. Plan: `production/competitors/no-filming-2026-10-20.md` round 2 |
| You-be-the-judge reel | **MATTEO** | Film `production/reels/2026-10-20-you-be-the-judge/` (needs the first-fight KO clip from Drive) |
| Audio API (`tools/instagram/audio.py`) | OK (checked 10-20) | FB_USER_TOKEN has instagram_basic + instagram_content_publish: library sounds can be attached. Sound scout (`sound-scout.yml`, Mondays) -> `production/sounds/proven.json`: niche outliers run on original audio, no cleared track yet |
| Phase 1 cloud (D1, R2, Modal, ticker) | Built 2026-10-20. Files are still the truth; every state workflow mirrors to D1 (`state_mirror.py sync`). Ticker reads D1 and starts Post queue when an item is due | **2026-10-23 or later:** if the "Mirror state to D1" steps were clean for 3 days, set `"state_backend": "d1"` in `tools/cloud/cloud.json` and the post-queue cron to `0 */3 * * *` (the cutover; revert = set both back). Plan: docs/superpowers/plans/2026-10-18-phase1-foundation.md |
| Saenchai old-style (v3 film-study) A/B/C | **MATTEO** | Queued 10-21 as `saenchai-v3-A/B/C` at 15:30 NY on 23/24/25 Oct (19:30Z), same hooks and captions as the editorial cut, so each hook runs in both edit styles 3 days apart (editorial A posted 10-20, B 10-21, C 10-22). Files checked: `saenchai-bigger-men-A/B/C.mp4` on the `media` release are the v3 cut (tape + RESETS counter), 42.1/41.0/40.6 s. No cross-posts (the editorial cut covers YT/Threads/FB). `approved:false` until Matteo's yes |
| Saenchai A/B/C | OK | Moved to the 15:30 NY talking-head slot: A 20 Oct, B 21 Oct, C 22 Oct (19:30 UTC). Posts whatever file is on the `media` release as saenchai-bigger-men-A/B/C.mp4 at that time |
| 5 posts a day (10-20) | OK | All listicles through 28 Oct approved by Matteo (dashboard, 10-20). 15:30 talking-head slot: Saenchai v3 A/B/C on 23-25 Oct, empty from 26 Oct (empty day = skipped, Matteo 10-20) |
| Facebook reels (10-22) | **DO (verify)** | Views fell ~100 -> ~0 a reel. Matteo's yes: 1 FB reel/day, only the best IG reel at 72 h (>= median views), as its Facebook version (list on screen + music, `<asset>-fb.mp4`), 19:30 NY; slide albums paused; YT/Threads get music copies (`<asset>-music.mp4`). Daily pick = Listicle factory 20:10 UTC. Check in a week: FB views per reel vs the old ~20. Matteo to check Page quality / recommendation eligibility in Professional dashboard. Doc: tools/crosspost/README.md |
| Effects shots (nvision.media reference, 10-23) | **MATTEO** | Shot guide `production/shooting/effects-shots.md`. Film the first test shoot (cards 1, 2, 5, 7, 10), upload, Claude builds the effects. Gypsy Amazon version needs their colours, font, logo |
| Carousels (10-24) | **MATTEO** | Built: frames from Drive, renderer (editorial + poster, animated cover), proven-hook bank + lint gate, Monday research (scout + report). Matteo picks the look from the sample sent in chat; then build posting (IG carousel, Threads, FB album, 11:00 NY slot). Lead-magnet upgrade (PROTOCOL) after. Doc: tools/carousel/README.md |
| TikTok | WAIT | App review |
| Meta oEmbed | WAIT | Not approved; `ig_discovery` scans tracked competitors instead |
| IG token | Expires 2026-12-13 | `ig.py refresh` before then |
| Threads token | Expires 2026-12-14 | `crosspost.py threads-refresh` before then |
| IG_COOKIES secret | Expired, no longer blocking: Fetch video now retries yt-dlp without cookies (worked for Ferris 10-19) and falls back to the API, then the embed page | Optional refresh if logged-out downloads start failing |
| FB_USER_TOKEN | Set 2026-10-15, 60-day token, so expires ~2026-12-14. Expiry not tracked | Add tracking |
| Listicle clip sheets | MATTEO | Waiting on his yes (Telegram or dashboard) |
| Next week's 21 listicles (18 to 28 Oct) | **MATTEO** | Reviewed, 6 clips swapped and re-rendered 10-18 15:00Z. Waiting on his yes (dashboard / Telegram / chat). #1 posts 12:30 NY today only if approved |
| control.matteofights.me | OK | Live behind Cloudflare Access (checked 10-18) |
| Style lab next aspect (10-24) | OPEN | hook_style is fully tested (native won). Add a new lab aspect before the next Saturday proposal: hook position (lower plate, faces kept clear; the 10-20 review swapped 6 clips for text over the face) or sound. Code in tools/style/lab.py ASPECTS + tools/listicle/render.py |

## Rules (short)

Never set `approved:true`. Never commit `secrets/`, `data.json`, `covers/`, `voice.wav`, `snaps/`. Commit only your own paths. Never run renders as session background jobs, and never render variants in parallel.
