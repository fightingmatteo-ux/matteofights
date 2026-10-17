# Cloud production: every reel made, sourced, stored and rendered without the laptop

_Spec, 2026-10-17. Builds on Reel studio (`.github/workflows/reel-studio.yml`, `tools/video/README.md`)._

## Goal
Matteo films on his phone, drops footage in Drive (or sends just an idea), and gets back three finished hook
variants on Telegram to approve. Nothing is ever done on the laptop or by hand after one setup session.
Publishing still waits for his explicit yes (operating rule; unchanged).

## How it works
```
Trigger                     Brain (GitHub Actions)                         Out
───────                     ──────────────────────                         ───
Telegram "/reel <idea>"  ─┐  Claude Code (claude-code-action, this repo,    3 phone cuts on Telegram
Dashboard idea           ─┼► CLAUDE.md + PIPELINE.md + skills):              full renders in Drive output
New file in Drive input  ─┘   1 ingest footage (reel_ingest.sh)              REEL.md + LEDGER rows committed
(polled every 30 min)         2 pick takes, write takes.json                 queue.json entries, approved:false
                              3 source b-roll + music (below) into the bank
                              4 write the template, build, check, snapshot,
                                review its own contact sheets, fix
                              5 render A/B/C (reel_render.sh), deliver
Telegram reply "B: bigger counter" ─► same job, revision mode, re-renders only B
```
- **Agent runner:** `anthropics/claude-code-action` in a new `reel-agent.yml`, run on `workflow_dispatch` from the
  control system (new `reel` / `revise` actions in `tools/control/control.py`) and on a Drive-poll schedule. It
  gets the repo, the skills in `.claude/skills/`, and Bash for ffmpeg/node/rclone/yt-dlp. It does the work a
  cloud session does today, but nobody has to open a session.
- **Auth: Matteo's Claude account only, no API key (his call, 2026-10-17).** `CLAUDE_CODE_OAUTH_TOKEN`, made once
  with `claude setup-token`, passed to claude-code-action as `claude_code_oauth_token`. Runs draw on his plan's
  usage limits (shared with his own chats and sessions); if a run hits the limit it stops and says so on Telegram,
  and the job is re-run after the reset. No `ANTHROPIC_API_KEY` fallback. The listicle footage agent moves off the
  API too: it calls `claude -p` (Claude Code CLI, same token) instead of the Python SDK, and the
  `ANTHROPIC_API_KEY` secret gets deleted once nothing reads it.
- **Guardrails:** the agent can commit to `production/reels/<slug>/`, the bank index and queue.json (unapproved
  only), upload to the media release and Drive. It can't post, approve, or touch secrets. Every run ends with
  a Telegram message: the phone cuts, or exactly what blocked it.

## Sourcing (all from Actions runners, which reach the open internet)
| Need | Source | How | Setup |
|---|---|---|---|
| Fight footage of legends (Saenchai etc.) | YouTube | `yt-dlp` with cookies, cut to the needed seconds only (`--download-sections`) | `YT_COOKIES` secret (burner account) |
| Instagram references | Instagram | existing Fetch video path | `IG_COOKIES` (exists) |
| Lifestyle / training / city b-roll | Pexels, Pixabay video APIs (free, commercial use) | search by keyword, download 9:16 or crop | `PEXELS_API_KEY`, `PIXABAY_API_KEY` |
| Music beds, SFX | Pixabay audio, Mixkit (`reel-kit/scripts/mixkit.py`) | not Content ID registered only | `PIXABAY_API_KEY` |
| Matteo's own training clips | Drive input / training folder | rclone (listicle factory already does this) | exists |

Every sourced clip gets a provenance line (URL, timestamps, licence) in the bank index. Fight footage is used
as short commentary clips under Matteo's voice (current house rule: <= 3.5 s each, transformed).

## Storage: the content bank lives in Drive
```
Drive: matteofights-bank/
  footage/<slug>/        raw phone clips (originals, never edited)
  broll/<topic>/         every sourced or own b-roll clip, reused across reels
  music/  sfx/
  renders/<slug>/        finals (Drive output keeps working as Matteo's inbox)
Git: content-bank/broll/library.json + library.md + sheets/<id>.jpg   searchable index, small
GitHub media release:  <slug>-work.tar + phone cuts                       fast cache for runners and cloud sessions
```
The agent searches `library.md` before sourcing anything new, so b-roll is downloaded once and reused.
Tagging: each new clip gets a 3x2 contact sheet and a Haiku-written description (cheap), as in the `broll` skill.

## Rendering
GitHub-hosted `ubuntu-latest` (4 vCPU). The repo is private, so minutes count against the plan (Free 2,000/month,
Pro 3,000/month); beyond that Linux minutes cost ~$0.008/min. A 45 s reel × 3 variants ≈ 30-60 min, so ~10 talking-head
reels a month fit the free tier alongside the listicles; more = a few dollars, or a larger runner if speed matters.

## One-time laptop session (Matteo)
1. Merge `claude/reel-studio` into master.
2. Move the laptop's working media to the cloud: `bash tools/video/reel_work.sh push <slug>` for any reel in
   progress, then `rclone copy media gdrive:matteofights-bank --progress` (or the per-folder layout above).
3. `claude setup-token` → GitHub repo secret `CLAUDE_CODE_OAUTH_TOKEN`.
4. YouTube cookies from a logged-in burner account (same export as `IG_COOKIES`) → secret `YT_COOKIES`.
5. Free Pexels + Pixabay API keys → secrets `PEXELS_API_KEY`, `PIXABAY_API_KEY` (can also be done from the phone).
6. Check Drive storage headroom (Google One plan) for the bank.

## Build order
1. Reel studio ingest/render (done, untested end to end).
2. Sourcing tools: `tools/broll/source.py` (YouTube sections, Pexels, Pixabay) + bank index + Drive layout.
3. `reel-agent.yml` (claude-code-action) + control `reel`/`revise` actions + Telegram delivery.
4. Drive-poll trigger. Then retire laptop-only paths in PIPELINE.md.

## Open risks
- YouTube can still refuse datacenter IPs even with cookies; fallback is a paid residential proxy, or the agent
  asks on Telegram for a Drive upload of that one clip.
- The agent's taste: first reels go to Telegram as drafts; Matteo's notes become rules in PIPELINE.md as now.
- Licensing of fight footage stays commentary-style short clips; stock is the default where a legend isn't named.
