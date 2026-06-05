# @matteofights OS — Design Spec

_Date: 2026-06-05 · Status: Design (Phase 0 buildable, Phases 1–4 architected) · Owner: Matteo_

---

## 1. Vision

A personal operating system for the **@matteofights** Instagram brand — a boxing/Muay Thai fighter
account with a proven viral format (160k and 27k-view reels, DM-driven engagement).

The north star is **growing the fighter brand through a polished, voice-capable system** that
eventually feels like "Jarvis for @matteofights": you speak or type an intent — _"make a reel with
this hook, generate a caption and subhook, post it in our viral format"_ — and the system executes
end to end. It must be **modular and expandable**, so when Matteo's focus shifts (coaching funnel,
Stance app, something new), modules are added or swapped without a rewrite.

### North-star architecture (the shape everything builds toward)

A web app wrapping the **Claude Agent SDK**:

| Layer | Role | Backed by |
|---|---|---|
| **Brain** | The agent's knowledge + operating rules | `context/` markdown docs |
| **Tools** | Things the agent can _do_ | Remotion renderer, carousel renderer, caption generator, IG publisher |
| **Data** | What the agent reasons over | `analytics/` snapshots, `content-bank/` |
| **I/O** | How Matteo talks to it | Dashboard UI + voice (STT/TTS) |
| **Workers** | What runs without him | Scheduled / background subagents (24/7) |

Each layer is an independent module with a defined interface, so it can be understood, built, and
tested on its own.

---

## 2. Goals & non-goals

**Goals**
- A markdown "brain" that makes Claude immediately effective on @matteofights work.
- A visual dashboard ("sick UI") to see reel performance and the content bank.
- A repeatable content engine: hook → caption + subhook → rendered reel in the viral format.
- An expandable platform that grows toward a conversational, voice-driven, partly-autonomous agent.
- **Local-first but cloud-ready** — hostable on the GitHub Student Pack with config, not a rewrite.

**Non-goals (now)**
- No auto-posting to Instagram until the Graph API publishing flow is set up (Phase 4).
- No multi-account/multi-brand support in v1 (designed so it _can_ be added).
- No paid infra. Free tiers + Student Pack credits only.

---

## 3. Primary goal & priority rule

The brand-growth goal wins when priorities conflict. Coaching lead-gen and Stance-funnel uses are
supported but secondary. Concretely: when a content or analytics decision is ambiguous, optimize for
**reach, watch-through, and follower growth on @matteofights itself**.

---

## 4. Module architecture

Five units. The brain is always-on; the other four are the four build modules.

### 4.1 Brain — `context/`
- **Does:** Holds brand, voice, audience, strategy, content, and the viral format as small topical
  docs read on-demand (Gypsy Amazon's proven pattern). `CLAUDE.md` routes to them.
- **Interface:** Markdown files + a routing table in `CLAUDE.md`. Read-only for the agent at runtime;
  edited deliberately.
- **Depends on:** Nothing. This is the root.

### 4.2 Analytics — `analytics/` _(first module built, Phase 1)_
- **Does:** Pulls Instagram metrics via Windsor MCP (joinstance account), writes dated JSON snapshots,
  generates insight reports.
- **Interface:** `analytics/snapshots/<date>.json` (raw pulls) → `analytics/reports/<date>.md` (digested).
  The dashboard and the agent both read these files.
- **Depends on:** Windsor IG connector authorization. Optional add-ons (deferred): Higgsfield
  `virality_predictor`, sessionid scraper, browser automation.

### 4.3 Content engine — `production/` _(Phase 2)_
- **Does:** Renders vertical reels (Remotion) and carousels/static posts (PIL), and generates captions
  + subhooks from a hook using the viral format. Exposed as callable tools.
- **Interface:** CLI/npm scripts + a thin command layer (`make-reel --hook "..."`). Inputs: hook string,
  footage/assets. Output: finished `.mp4` / `.png` staged in `content-bank/` + a caption file.
- **Depends on:** Brain (`viral-format.md`, `voice.md`, `brand.md`) for copy and styling.

### 4.4 Dashboard UI — `dashboard/` _(Phase 1 read-only, grows through Phase 3)_
- **Does:** Visualizes reel performance, content bank, and (later) the content pipeline; hosts the
  Jarvis conversation + voice in Phase 3.
- **Interface:** Vite + React app reading `analytics/` and `content-bank/` (via a light backend API in
  later phases). Dark fight-poster aesthetic: red/black/gold, Bebas + Geist.
- **Depends on:** Analytics module for data. Agent SDK backend for Phase 3.

### 4.5 Workers — scheduled subagents _(Phase 4)_
- **Does:** Background jobs — nightly analytics pull, trend scanning, comment/DM triage, draft
  generation.
- **Interface:** Cron-scheduled agents on an always-on host, writing into `analytics/` and `content-bank/`.
- **Depends on:** Everything below it; needs an always-on host (not serverless).

---

## 5. Tech stack & hosting

| Concern | Choice | Rationale |
|---|---|---|
| Frontend | Vite + React + TypeScript | Fast, standard, deploys anywhere (Vercel/Netlify in Student Pack) |
| Styling | Tailwind, dark combat theme | Matches established Stance/@matteofights brand |
| Backend (Phase 3+) | Node + Express **or** Python FastAPI | Wraps Claude Agent SDK; pick at Phase 3 |
| Agent | Claude Agent SDK + Claude API | The Jarvis brain (see `claude-api` skill for model IDs/params) |
| Video render | Remotion 4.x (ported from Gypsy) | Vertical 1080×1920; Windows render gotchas already documented |
| Carousel/static | Python + PIL (ported from trainingcampfiles) | Existing `render_carousel.py` + Bebas/Inter fonts |
| Analytics source | Windsor.ai MCP (`instagram_public`) | Already available; free; joinstance account |
| Voice (Phase 3) | Browser Web Speech API first | Free STT/TTS in Chrome; upgrade TTS (e.g. ElevenLabs) later |
| Always-on host (Phase 4) | DigitalOcean droplet or Azure VM | Student Pack credits; serverless can't run 24/7 jobs |

**Hosting principle:** local-first, cloud-ready. Standard build output, all secrets via env vars, no
local-only path assumptions. Frontend → Vercel/Netlify; long-running backend/workers → DO/Azure.

---

## 6. Reusable assets (what we port, from where)

| Asset | Source | Use |
|---|---|---|
| `CLAUDE.md` + `context/` routing pattern | Gypsy Amazon `CLAUDE.md` | Brain backbone |
| Remotion pipeline + Windows render rules | Gypsy `remotion-video/`, `context/remotion.md` | Phase 2 video engine |
| `render_carousel.py` + Bebas/Inter fonts | Stance @trainingcampfiles | Phase 2 carousel engine |
| `VIRAL_FORMAT_TEMPLATE.md` | Stance `@matteofights/captions/` | → `context/viral-format.md` |
| Best reels + frames (160k, 27k, ACL story) | Stance `@matteofights/reels/` | → `content-bank/reels/` |
| `insights/` (currently empty) | Stance `@matteofights/insights/` | → `analytics/` |
| Windsor connector pattern + sessionid scraper | Gypsy `context/social.md`, `.ig_sessionid` | Phase 1 analytics / deferred scraper |

---

## 7. Phase 0 — Foundation (buildable detail)

**Outcome:** A git-tracked, deploy-portable repo with the brain populated and Stance content migrated.
Makes Claude effective on @matteofights work immediately. No code beyond scaffolding.

### 7.1 Target structure

```
@matteofights/
  CLAUDE.md                 # OS entry: operating rules + routing table
  README.md                 # human-facing overview + how to run later phases
  .gitignore                # node, python, env, large media
  .env.example              # Windsor / API keys (no secrets committed)

  context/                  # THE BRAIN
    founder.md              # Matteo: fighter background, story, what's post-worthy
    brand.md                # @matteofights visual + verbal identity
    voice.md                # caption voice; language to use / avoid
    audience.md             # who watches, what they want, where they convert
    strategy.md             # growth plan; north star = fighter-brand growth
    content.md              # pillars, cadence, formats
    viral-format.md         # migrated hook + caption formula
    social.md               # analytics snapshots + Windsor IDs (joinstance)
    apps.md                 # connected MCPs/tools + their account/IDs

  content-bank/
    reels/                  # migrated best reels + frames
    captions/               # swipe file / caption library
    scraped/                # (empty; sessionid scraper output, later)

  analytics/
    snapshots/              # (empty; dated Windsor JSON, Phase 1)
    reports/                # (empty; insight reports, Phase 1)

  production/               # (empty dirs; engine ported Phase 2)
    remotion/
    carousels/

  dashboard/                # (empty; Vite+React app, Phase 1)

  Instagram/Reels/          # existing — fold source footage into content-bank over time

  docs/superpowers/specs/   # this spec + future phase specs
```

### 7.2 `context/` doc contents (what each must contain)
- **founder.md** — pull from Stance `FOUNDER.md`; Matteo's fighter background, handle, story angles,
  what makes content authentic.
- **brand.md** — @matteofights identity distinct from Stance: fight-poster aesthetic, red/black/gold,
  Bebas headline energy. Adapt from Stance `BRAND.md` marketing section.
- **voice.md** — caption voice (raw, personal, story-driven, direct address, "no 'I' preferred"),
  banned/over-used language.
- **audience.md** — fighters and aspiring fighters on a busy schedule; pain points; the curiosity-gap
  hook psychology that already worked.
- **strategy.md** — growth plan; cadence; the "DM me [WORD]" lead mechanism; how @matteofights ladders
  to coaching and to Stance later.
- **content.md** — pillars and formats; reel vs carousel vs story; posting rhythm.
- **viral-format.md** — verbatim migration of `VIRAL_FORMAT_TEMPLATE.md` (hook formula, caption
  structure, ready-to-use hooks, blank template).
- **social.md** — current follower/reach baseline + the Windsor connector IDs for the joinstance
  account (filled once the connector is authorized in Phase 1).
- **apps.md** — Windsor (joinstance@gmail.com), Higgsfield (virality_predictor), and any others; note
  account + what each is used for.

### 7.3 `CLAUDE.md` operating rules (mirrors Gypsy's pattern)
- Read `context/` files on-demand, not all at session start; routing table lists when to read each.
- Drafting/suggesting is free; **publishing or posting requires explicit in-conversation confirmation.**
- Analytics files are dated snapshots — pull live via Windsor when current numbers matter, then update
  the snapshot.
- Brand/voice answers come from `context/` without an API call when the docs already cover it.

### 7.4 Migration steps
1. Copy `VIRAL_FORMAT_TEMPLATE.md` → `context/viral-format.md`.
2. Copy Stance `@matteofights/reels/**` → `content-bank/reels/` (keep the view-count folder names —
   they're labeled training data for what works).
3. Seed `context/founder.md`, `brand.md`, `voice.md`, `audience.md`, `strategy.md`, `content.md` from
   the relevant Stance docs, rewritten for @matteofights (not Stance the app).
4. `git init`, add `.gitignore` (ignore `node_modules/`, `.env`, large media in `content-bank/reels/`),
   first commit.

### 7.5 Phase 0 done when
- Repo initialized and committed; `.gitignore` and `.env.example` present.
- All nine `context/` docs exist with real content (no placeholders).
- Stance @matteofights content migrated and verified.
- `CLAUDE.md` routes correctly and a fresh session can answer brand/voice/format questions from docs alone.

---

## 8. Phase 1 — Analytics + dashboard (next build, moderate detail)

**Outcome:** Authorized IG data flowing into snapshots/reports, and a read-only dashboard that shows it.

- **8.1 Connector:** Authorize Windsor `instagram_public` on joinstance@gmail.com
  (`get_connector_authorization_url` → connect → confirm the @matteofights IG account + ID). Record IDs
  in `context/social.md` and `context/apps.md`.
- **8.2 Pull → snapshot:** A script calls Windsor `get_data` for reach, views, followers, and per-post
  metrics; writes `analytics/snapshots/<date>.json`.
- **8.3 Report:** Digest the snapshot into `analytics/reports/<date>.md` — top reels, watch-through,
  follower delta, what the numbers say about the next post.
- **8.4 Dashboard v1 (read-only):** Vite+React, dark combat theme. Views: reel performance leaderboard,
  follower/reach trend, content-bank browser. Reads the JSON/markdown directly (static build, no backend
  yet → deploys to Vercel/Netlify as-is).
- **Done when:** one real snapshot + report exist and the dashboard renders them locally and builds clean
  for deploy.

---

## 9. Phases 2–4 — Architecture (designed, specced later)

- **Phase 2 — Content engine + "make a reel":** Port Remotion vertical templates (respect the documented
  4.x/Windows render rules) and `render_carousel.py`. Build a command layer:
  `hook → caption + subhook (viral-format) → rendered reel`, output staged in `content-bank/` with its
  caption. Posting stays manual here.
- **Phase 3 — Jarvis layer:** Stand up the backend (Node/Express or Python/FastAPI) wrapping the Claude
  Agent SDK; the brain becomes its knowledge and Phase 2 tools become its callable tools. Dashboard gains
  a conversation panel + voice I/O (Web Speech first). "Make a reel with this hook" works by voice/text.
- **Phase 4 — Autonomy:** Instagram Graph API Content Publishing (Business account + Facebook app + token)
  for real posting/scheduling; 24/7 scheduled subagents on an always-on host (nightly analytics, trend
  scanning, comment/DM triage, draft generation).

**Grounding constraints carried forward:** auto-posting requires the Graph API setup (why it's Phase 4);
24/7 workers require an always-on host, not serverless; voice starts with the free browser API and
upgrades later.

---

## 10. Success criteria (platform level)

- Claude can answer any @matteofights brand/voice/format question from the brain alone.
- Real Instagram performance is visible in a dashboard you'd actually open.
- A single command turns a hook into a finished reel + caption in the viral format.
- The system is conversational and voice-driven.
- It can be deployed to Student-Pack infra without rearchitecting.
- New modules slot in without disturbing existing ones.

---

## 11. Open / deferred decisions
- Backend language (Node vs Python) — decide at Phase 3 based on how the Agent SDK + Remotion/PIL tools
  are orchestrated.
- TTS upgrade path (ElevenLabs vs alternatives) — decide at Phase 3.
- Whether the sessionid scraper is worth the ToS risk vs staying purely on Windsor + Graph API — revisit
  if Windsor's post-level data proves insufficient.
- Multi-brand/account support — out of scope now; module boundaries keep it possible.
