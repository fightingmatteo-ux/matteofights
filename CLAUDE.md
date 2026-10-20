# @matteofights: Operating System

Matteo's fighter Instagram (@matteofights): the brain (context/), the content engine (production/, tools/) and the
machine that renders, posts and cross-posts on its own. This file is routing only: read the linked file when the
task needs it. Open items: [STATUS.md](STATUS.md) (read at session start, update when you close or add one).

## Rules

- **Drafting is free; publishing is not.** Write hooks, captions, scripts freely. Never post, schedule or send
  anything outward without Matteo's explicit yes in this conversation. Automation never sets `approved: true`;
  only Matteo does (dashboard hold-to-approve, Telegram, or `tools/instagram/approve.py` after his yes).
- **North star: fighter-brand growth** (reach, watch-through, followers on @matteofights). Coaching and the Stance
  funnel are secondary; no Stance plug in reels unless he asks. Stance (the app) lives in
  `C:\Users\matte\Documents\Claude\Projects\Stance`, never here.
- **Live state only through `tools/state.py`** (queue, cross-posts, jobs). Never edit
  `production/schedule/*.json` by hand in code; see [tools/cloud/README.md](tools/cloud/README.md).
- **Renders run in the cloud** ([tools/render/README.md](tools/render/README.md)), not on the laptop and never on
  GitHub runners.
- **Concurrent writers:** other sessions and bots push to master all day. `git pull --rebase --autostash` before
  push; `git add <your paths>`, never `-a`. Never commit `secrets/`, `media/`, `data.json`, `covers/`, renders.
- Python: `python -P` (scripts) on this PC, `python3 -P` in workflows. Modal CLI on Windows: `PYTHONUTF8=1`.
- Copy: no em dashes in user-facing text. Voice: [context/voice.md](context/voice.md).
- Analytics files are dated snapshots: pull live (Buzzfy first, Windsor `instagram` 17841465098113052 as
  fallback) when current numbers matter, then write a fresh snapshot.

## Content direction (Matteo, standing)

- **Topic:** combat-sport psychology and fighter mindset, not injury stories. Adjacent lifestyle lane (nutrition,
  recovery, routine) always framed for fighters. **Builder lane:** about 2 of 14 reels/week on "fighter who
  builds", format `builder`; judged on follows per 1k views vs fight content.
- **Cadence (2026-10-20): 5 posts a day** (New York): listicles 09:00, 12:30, 18:30, 21:30 with an Instagram
  sound attached, plus 1 talking-head variant 15:30. Listicles run themselves
  ([tools/listicle/README.md](tools/listicle/README.md)).
- **Talking heads:** Matteo films from talking points, not scripts. 3 hook variants per reel, posted as trial
  reels 48 h apart, logged in [production/reels/LEDGER.md](production/reels/LEDGER.md). Look: **editorial**,
  start from `production/reels/_TEMPLATE/editorial/`.
- **What wins:** identity and contrast beat instruction. Best ever: `6 SIGNS YOU WERE BORN TO BE A FIGHTER`
  (331k, caption opens `Some people train for fun.`); #2 `8 WAYS TO FIGHT LIKE A KILLER WITHOUT SPARRING 5X/WEEK`
  (161k). Barrier-removal (`You don't need X`) is spent. Reels win; carousels are unproven, retested only with
  the locked design system.

## Where things run

| Piece | Where | Doc |
|---|---|---|
| Live state (queue, cross-posts, render jobs) | Cloudflare D1 `matteofights`; JSON files in `production/schedule` are the truth until the cutover flag in `tools/cloud/cloud.json` | [tools/cloud/README.md](tools/cloud/README.md) |
| Videos | R2 `matteofights-media` (`renders/`), `media` GitHub release as fallback | [tools/cloud/README.md](tools/cloud/README.md) |
| Renders | Modal app `matteofights-render` (`tools/render/submit.py`) | [tools/render/README.md](tools/render/README.md) |
| Posting timer | Cloudflare Worker `matteo-ticker` (every 5 min: slots + due queue items) | `tools/ticker/worker.js` |
| Posting / cross-posting / listicles | GitHub Actions: Post queue, Cross-post, Listicle factory, Control | `.github/workflows/` |
| Control center | control.matteofights.me (dashboard) + Telegram @matteofights_control_bot | [control-site/SETUP.md](control-site/SETUP.md) |
| Secrets | `secrets/*.env` locally (git-ignored), GitHub/Modal/Worker secrets remotely; `tools/cloud/set-secrets.sh` | [tools/cloud/README.md](tools/cloud/README.md) |
| Roadmap | Phase 1 done (cutover pending); Phase 2 live dashboard, 3 self-maintenance, 4 lean setup + cleanup | [spec](docs/superpowers/specs/2026-10-18-run-from-anywhere-design.md) |

## Read on demand

| Task | Read |
|---|---|
| **Make or edit a reel (watch, plan, edit, test). Read first.** | [production/editing/reel-kit/PIPELINE.md](production/editing/reel-kit/PIPELINE.md) |
| Render a reel | [tools/render/README.md](tools/render/README.md) |
| Any caption, hook, Threads post, carousel copy | [context/creator-voice.md](context/creator-voice.md), skill `platform-captions` |
| Weekly Threads batch | skill `threads-writer` |
| Hook + caption from a hook | [production/captions/CAPTION-ENGINE.md](production/captions/CAPTION-ENGINE.md) |
| The proven viral reel format | [context/viral-format.md](context/viral-format.md) |
| What is working, from our numbers | `python -P tools/threads/report.py` |
| Competitor outliers, next video ideas | skill `competitor-ideas`, data `production/competitors/` |
| Who Matteo is, story, angles | [context/founder.md](context/founder.md) |
| Visual identity | [context/brand.md](context/brand.md) |
| Audience, hook psychology | [context/audience.md](context/audience.md) |
| Strategy, funnel, CTAs | [context/strategy.md](context/strategy.md) |
| Pillars, formats | [context/content.md](context/content.md) |
| Reel results, test history | [production/reels/LEDGER.md](production/reels/LEDGER.md) |
| Reference reels (watched) | [content-bank/references/](content-bank/references/) |
| Watch or download a video from a cloud session | [tools/video/README.md](tools/video/README.md) |
| Instagram API posting, tokens | `tools/instagram/ig.py` docstring |
| Cross-posting (Facebook, YouTube, Threads) | `tools/crosspost/crosspost.py` docstring |
| Analytics snapshots, account IDs | [context/social.md](context/social.md) |
| Connected tools / MCPs | [context/apps.md](context/apps.md) |
