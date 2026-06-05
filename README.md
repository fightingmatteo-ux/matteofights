# @matteofights OS

A personal operating system for growing the **@matteofights** Instagram brand (boxing / Muay Thai),
built to grow into a voice-capable, partly-autonomous content agent.

## What's here

- **`context/`** — the brand brain (founder story, voice, audience, strategy, content, viral format).
- **`content-bank/`** — best reels, caption swipe file, scraped posts.
- **`analytics/`** — Instagram performance pulled from Windsor.ai → dated snapshots + reports.
- **`production/`** — the content engine (Remotion video + PIL carousels). _Phase 2._
- **`dashboard/`** — the "sick UI" web dashboard. _Phase 1+._
- **`docs/superpowers/specs/`** — the design spec and per-phase plans.

## Data

Instagram analytics come through the **Windsor.ai MCP** (account `joinstance@gmail.com`,
`instagram` connector for `matteofights`, ID `17841465098113052`).

## Hosting

Local-first, cloud-ready. Frontend deploys to Vercel/Netlify; 24/7 agents (Phase 4) run on an
always-on host (DigitalOcean / Azure via GitHub Student Pack). No local-only path assumptions.

## Roadmap

See [docs/superpowers/specs/2026-06-05-matteofights-os-design.md](docs/superpowers/specs/2026-06-05-matteofights-os-design.md).
Build proceeds in phases (0 → 4); each phase below the current one is design-only until reached.
