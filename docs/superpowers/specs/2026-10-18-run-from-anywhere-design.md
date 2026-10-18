# Run from anywhere: design

_2026-10-18. Projects 1 to 3 of 4 (the Samui B-roll shoot + B-roll reel engine is project 4, designed later)._

## Why

Matteo is in Koh Samui with a phone and no reliable laptop. Today the system breaks in exactly that situation:
talking-head renders need his PC (and die when it lags), GitHub cron posts late, bots fight over commits to
`queue.json`, the dashboard is not something he wants to open, and every expiring token or failed job needs a
Claude session to babysit it. He wants to feed the machine from his phone, approve from his phone, see results
that make him want to come back, and never do maintenance.

## Goals

1. **Phone in, posts out.** Upload a talking head or B-roll from the dashboard, add an optional note/tags,
   get 3 rendered hook variants back, approve, done. Laptop can be off or gone.
2. **One dashboard** (`control-site/`, control.matteofights.me), phone-first, that he *wants* to open.
3. **Self-maintenance.** A daily Claude agent on his subscription checks, fixes what is safe, and reports.
4. **Lean Claude setup**, so every session spends tokens on the work, not on unused plugins.

## Anti-goals

- Anything that posts or approves without Matteo. `approved` is only ever set by his hold-to-approve.
- Notification spam. Telegram is a quiet backup, not the main channel.
- A rebuild that stops what works today. Every piece runs beside the old one until it has proven itself.
- New paid services or new accounts beyond what is listed under Cost.

## Hard constraints (Matteo's)

- **Free to test. Fully automatic for under $10/month.**
- GitHub keeps the code and the brain. Cloudflare on the **free plan** (no Workers Paid, no Containers). Nothing renders on GitHub runners (Actions terms risk).
- Storage is Cloudflare R2.

## Cost

| Item | Cost |
|---|---|
| Cloudflare Pages, Workers, cron, D1, Access (Matteo + 1 uploader) | free plan |
| R2 storage | free to 10 GB, then $0.015/GB/month (100 GB ≈ $1.35, 300 GB ≈ $4.35). No egress fees |
| Modal (renders, transcription, B-roll prep) | Starter plan, $30/month free credits; estimated use ≈ $10 of it, so $0 |
| GitHub private repo | free 2,000 min/month; target after this work ≈ 400-600 (no renders run on GitHub) |
| Claude | existing subscription (shares its usage limits with Matteo's own sessions) |

The maintenance agent alerts at R2 > 250 GB and Modal > $20 of the $30 credit, so the bill stays under $10 without Matteo watching it.

## Architecture

```
phone (dashboard PWA) ──upload──► R2 (direct, presigned URL)          Cloudflare free
        │  approve / tweak / notes                                     ├─ Pages: dashboard + /api functions
        ▼                                                              ├─ Worker "ticker": cron every 5 min
   /api (Pages Functions) ──► D1 (queue, jobs, crosspost, stats, bank) ├─ D1: all live state
        │                                                              └─ R2: footage, renders, B-roll bank
        ├─ HTTPS ───► Modal "matteofights-render" (render + transcribe + B-roll fit, reads/writes R2)
        └─ dispatch ─► PRIVATE repo "matteofights" (post, cross-post, Claude planning, stats)
Claude cloud routine (daily, subscription) ─► health check, safe fixes as PRs, report to digest
```

### Where state lives

- **Git (private repo):** code, `context/`, skills, reel folders (plans, EDLs, compositions), LEDGER.md. Things a
  human or Claude edits and wants history for.
- **D1:** everything bots write: queue items (incl. `approved`, `not_before`, `crosspost_to`), crosspost records,
  render jobs and their status, uploads and their notes/tags, B-roll bank index (stars, blocks, usage count),
  stats snapshots, token expiry dates. This ends commit fights. `tools/state.py` is the one Python
  wrapper (D1 HTTP API) that every script uses; no script talks to D1 any other way.
- **R2 bucket `matteofights-media`:** `inbox/` (raw uploads), `broll/` (bank), `jobs/<id>/` (render bundles),
  `renders/` (finished phone versions), `covers/`. Replaces the `media` GitHub release and Drive for new work.
  Existing Drive clips used by the listicle factory are copied once into `broll/`.

### Rendering (Modal, free credits)

- Modal app `matteofights-render`, source in the private repo under `tools/render/modal_app.py` (deployed with
  `modal deploy` from a GitHub workflow when that folder changes). Container image: Debian + Chrome deps,
  ffmpeg, Node, HyperFrames pinned version, faster-whisper, plus the repo's `make_broll`, `score_takes.py`,
  `verify_cut.py`.
- Functions: `prep(job_id)` (transcribe, score takes, B-roll proxies/thumbnails) and `render(job_id, variant)`.
  Started by the Cloudflare `/api` or ticker via a Modal web endpoint protected by a shared secret. The job spec
  and bundle are read from R2 with a bucket-scoped R2 token stored as a Modal secret. Result goes to
  `renders/`; status is reported back to `/api/job` (signed). 4 cores, 120 min timeout, one variant per call so
  the 3 variants render in parallel without touching Matteo's PC.
- Switching backend is one setting, `RENDER_TARGET` = `modal` | `cloudrun` | `github-private`. Fallback order if
  Modal ever drops free credits: Google Cloud Run Jobs (same container, ≈ $0.50/month at current volume), then
  private-repo runners.

### The upload-to-post flow

1. **Upload** in the dashboard: pick file(s), type (talking head / B-roll), optional note and tags. The browser
   gets a presigned multipart URL from `/api/upload` and sends straight to R2 (large 4K files OK, resumable).
2. **Prep job** (Modal): transcribe, score takes by disfluency (never transcript alone), make B-roll
   thumbnails/proxies and tag them into the bank.
3. **Plan job** (private repo, `anthropics/claude-code-action` with `CLAUDE_CODE_OAUTH_TOKEN` from Matteo's
   subscription): reads the transcript, take scores, Matteo's note, the brain (`context/`, platform-captions
   skill, LEDGER), and writes the reel folder: talking points chosen, EDL, 3 hooks, captions, B-roll picks
   (starred clips first, blocked clips never). Commits that folder. Builds the render bundle to R2.
4. **Render job** (Modal): 3 variants, slot-fitted B-roll (no freezes), `verify_cut.py` must pass.
5. **Ready**: push notification "3 versions ready". Dashboard plays them inline.
6. **Matteo**: hold-to-approve, or edit a hook line / swap a B-roll clip and tap re-render (only step 4 reruns,
   or step 3+4 if he changes the angle in a note).
7. **Post**: ticker posts at the slot, trial-reel spacing as today, cross-post per `crosspost_to`.

Listicle factory moves onto the same render path (Modal) with its existing logic unchanged.

### Timing (the ticker)

`tools/ticker` Worker deploys on the free plan (cron `*/5`, ~10 ms CPU per tick is enough because it only reads
D1 and dispatches). It replaces GitHub schedule triggers for posting and cross-posting. GitHub cron stays as a
slow backup only (every 3 h) for one week, then is removed. The ticker needs a fine-grained PAT (Actions
read/write on the repo): Matteo creates it once, with a step-by-step link.

## The dashboard (`control-site/`)

Phone-first PWA, installable to home screen. One dashboard: `dashboard/` (Vite, unused since 10-12) is deleted.
Data comes live from D1 via `/api`, so the site no longer redeploys on every commit (deploy only when
`control-site/**` changes).

Home, top to bottom:
1. **Momentum strip:** followers this week (+/-), the best live reel's views, and a streak = days in a row he fed
   the machine (an upload or an approval).
2. **Needs you (ranked, short):** approve N reels, film this talking point, a token Matteo must renew. Max 5
   items; empty state says so and shows the momentum instead.
3. **Results reveal:** when a trial-reel set has 48 h of numbers, a card reveals the winning hook and the margin,
   like a fight result. Tapping logs it to LEDGER via the API.
4. **Pipeline:** each job as a card moving uploaded → prepping → planning → rendering → ready → scheduled →
   posted, with live status.

Other screens: **Upload** (big button, note, tags, type), **Reel** (3 variants inline, hooks editable, B-roll swap,
re-render, approve), **Bank** (B-roll grid with thumbnails, star/block, usage count, filter by tag), **Schedule**.

Notifications: Web Push (VAPID, signed in the Pages Function; iOS needs the PWA added to the home screen, iOS
16.4+). Push only for: reels ready, a reveal, something broken that needs him. Telegram becomes a **daily digest**
at 09:00 Samui time plus "broken and I could not fix it". Telegram replies still steer ("use hook 2").

Access: Matteo full. An optional uploader login (his girlfriend, for B-roll) can only upload and see the Bank.

Design execution uses the existing `control-site/DESIGN.md` + `PRODUCT.md` as the starting brand; the builder
uses the impeccable skill for the redesign pass.

## Claude usage budget

Matteo's plan (Pro or Max) is not confirmed. *Builder's call:* design for Pro. The plan job uses one focused
Claude run per upload (context read from a short brief, not the whole brain) and the maintenance routine is one
run per day. A setting `CLAUDE_BUDGET` = `pro` | `max` lets Max add richer passes (e.g. a second hook round).

## Self-maintenance

A **Claude Code cloud routine** (Anthropic cloud, Matteo's subscription, no GitHub minutes) runs daily:

- **Checks:** every token's expiry (IG 12-13, Threads 12-14, FB_USER_TOKEN ~12-14, YouTube, R2, PAT), failed or
  stuck jobs, failed workflow runs, posts that missed their slot, cross-post failures, R2 size, private-repo
  Actions minutes, Cloudflare free-plan limits, and Claude-setup bloat (below).
- **Fixes on its own (PR, auto-merge after checks pass):** refreshable tokens (IG `ig.py refresh`, Threads
  `threads-refresh`) when < 14 days left; retry failed jobs once; reset stuck jobs; small code fixes for a clear
  failing step with a passing test or dry run; docs/STATUS.md updates.
- **Never:** set `approved`, post, change secrets, delete footage, merge anything touching posting logic without
  Matteo. Those become a "needs you" item with exactly what to do and a link.
- **Reports:** one line per action into D1, shown in the dashboard and in the Telegram digest.

STATUS.md becomes generated from D1 by the routine, so it can never drift from reality.

## Lean Claude setup

- Disable unused plugins/MCP connectors at user level (sales, marketing, product-management, Shopify, Make,
  SEO, Canva, Adobe, Windsor if Buzzfy covers it). Matteo approves the list once; the change is in
  `~/.claude/settings.json`, outside the repo.
- Prune `.claude/settings.local.json` one-off permissions; replace with a few broad, safe rules.
- Project skills that are not about this account (`break-ui`, `emil-design-eng`, `mobile-native`) move to user
  level or are removed from the repo.
- CLAUDE.md budget: ≤ 1,200 words, routing only. Nested CLAUDE.md files in old reel folders and
  `media/legacy-stance-folder` are removed or merged.
- The maintenance routine checks these budgets weekly and opens a PR when one drifts.

## Cleanup included

- Public site matteofights.me: moves from GitHub Pages (rebuilds on every push, ~365 min/month) to its own
  free Cloudflare Pages project deploying only when site files change. DNS switch after a preview check.
- `control-deploy.yml`: path filter, no `workflow_run` redeploys.
- `media` GitHub release and Drive upload workflow retire after R2 has every live asset.

## Rollout (each step keeps the old path working until verified)

1. R2 bucket + D1 + `tools/state.py`; mirror queue/crosspost into D1 (read-only at first), compare for a few days.
2. Modal render app; prove it on the Saenchai B and C renders (if Matteo has not rendered them locally first).
3. Ticker deploy; posting reads D1; GitHub schedules become backup, then removed.
4. Dashboard: live data from D1, upload, pipeline, reel screen, push. Then momentum/reveal/bank.
5. Plan job (Claude) for uploads; listicle factory on the new render path.
6. Maintenance routine; lean setup; site move; retire release/Drive.

Success = one full week where Matteo uploads from his phone, approves from his phone, everything posts on time,
nothing needed his laptop, and the bill is under $10.

## Left to the builder

Table schemas, API shapes, file layout of the render repo, exact UI layout and visual design within the
direction above, test strategy per step.
