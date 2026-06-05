# Jarvis Voice Layer (Phase 3) — Design Spec

_Date: 2026-06-05 · Status: Design (approved, ready for plan) · Owner: Matteo_

Builds on [2026-06-05-matteofights-os-design.md](2026-06-05-matteofights-os-design.md) §9 (Phase 3).

---

## 1. Goal

Stand up the "Jarvis" layer: a conversational agent you talk to (by voice or text)
that answers from the @matteofights brain, reasons over analytics, and generates
captions/hooks — the complete Phase 3 layer **minus** the unbuilt video renderer.

v1 capability (confirmed): full conversational Jarvis over everything that exists
today — brain Q&A, analytics, and caption/hook generation.

## 2. Key decisions (locked)

- **Agent runtime: Claude Agent SDK** (`@anthropic-ai/claude-agent-sdk`) — the local
  agent-loop SDK. It natively provides filesystem read/grep tools, the agentic loop,
  streaming, subagents, and MCP. **Not** Anthropic Managed Agents (which would host the
  brain in Anthropic's cloud containers — wrong for a local-first app that reads
  `context/` and `analytics/` off disk).
- **Language: Node + TypeScript** — matches the existing dashboard and the `.mjs`
  caption tooling; one language across the stack; the only path that sets up Phase 4
  (24/7 subagents) cleanly.
- **Model: `claude-opus-4-8`**, adaptive thinking (`{type: "adaptive"}`), effort `high`.
  If voice replies feel slow, the chat model can later be switched to Haiku/Sonnet as a
  one-line config change.
- **Voice in: Wispr Flow** (OS-level dictation, already installed) — nothing to build.
  You dictate into the chat input and it types for you.
- **Voice out: browser `speechSynthesis`** — free, zero setup, behind a "🔊 speak
  replies" toggle that is **off by default**. Premium TTS (ElevenLabs) deferred.
- **Analytics freshness:** v1 reads the dated snapshot files in `analytics/`. Live
  Windsor pulls are deferred (added later via MCP).

## 3. Architecture — three units

### 3.1 `backend/` (new)
- **Does:** One Node/TypeScript Express process wrapping the Claude Agent SDK. Its
  system prompt is the `CLAUDE.md` operating rules plus a "you are Jarvis for
  @matteofights" framing. The agent is scoped to the repo with filesystem read/grep
  tools so it reads `context/*.md`, `analytics/snapshots/` + `analytics/reports/`,
  `content-bank/`, and `production/captions/CAPTION-ENGINE.md` **on demand** — mirroring
  how Claude works in this repo today.
- **Interface:** `POST /api/chat` — accepts the conversation history, streams the
  agent's response back over **SSE** (text deltas + lightweight tool-activity events so
  the UI can show "reading social.md…", "writing draft…").
- **Depends on:** Brain (`context/`, `CLAUDE.md`), analytics files, caption engine,
  `ANTHROPIC_API_KEY` (via `.env`).

### 3.2 `dashboard/` (extend)
- **Does:** Adds a **Conversation** tab to the existing Vite+React app: a transcript, a
  text input (dictated into via Wispr Flow), a send action, and a streaming view of the
  agent's reply + tool activity. A **🔊 speak replies** toggle (default off) reads
  responses aloud via `window.speechSynthesis`.
- **Interface:** Calls `POST /api/chat` and renders the SSE stream. Keeps the dark
  fight-poster aesthetic already established (red/black/gold, Bebas + Geist).
- **Depends on:** `backend/` for the chat endpoint.

### 3.3 Existing units, consumed as tools/data
- **Brain** (`context/`, `CLAUDE.md`) — read via the agent's filesystem tools.
- **Analytics** (`analytics/snapshots|reports/`) — read via filesystem tools.
- **Caption engine** — exposed as a `generate_caption` tool wrapping today's
  hook → subhook → caption logic ([CAPTION-ENGINE.md](../../production/captions/CAPTION-ENGINE.md)),
  writing drafts to `content-bank/captions/drafts/<date>-<slug>/reel.md` exactly as the
  manual flow does now.

## 4. Data flow

1. You dictate into the Conversation input (Wispr Flow types it) and send.
2. Dashboard `POST`s the conversation to `/api/chat`.
3. The Agent SDK loop runs: reads brain/analytics as needed, optionally calls
   `generate_caption`.
4. Response streams back over SSE — text deltas plus tool-activity markers.
5. The panel renders it; if "speak replies" is on, `speechSynthesis` reads it aloud.

## 5. Guardrail — publishing stays manual

Per the OPERATING RULES, drafting is free but publishing is not. The agent is given
**no posting/publishing tool** — there is physically nothing to post with, so it can
only draft (and save drafts to `content-bank/captions/drafts/`). This enforces "never
post without confirmation" structurally, not just by instruction. (Instagram Graph API
publishing remains Phase 4.)

## 6. Error handling

- Anthropic 429/529/5xx → SDK auto-retries with exponential backoff.
- SSE stream drop → client reconnects; partial transcript is preserved.
- Tool errors (e.g. a missing snapshot file) → surfaced inline in the transcript rather
  than failing the whole turn.

## 7. Tech stack

| Concern | Choice |
|---|---|
| Backend | Node 20+, TypeScript, Express |
| Agent | `@anthropic-ai/claude-agent-sdk`, `claude-opus-4-8`, adaptive thinking, effort `high` |
| Streaming | Server-Sent Events (`POST /api/chat`) |
| Frontend | Existing Vite + React + TypeScript dashboard (new Conversation tab) |
| Voice in | Wispr Flow (OS dictation) — external, no code |
| Voice out | Browser `speechSynthesis` — free, toggle, default off |
| Secrets | `ANTHROPIC_API_KEY` via `.env` (already `.gitignore`d) |

## 8. Out of scope (v1)

- Video rendering / "make a reel" end to end (needs the deferred Remotion renderer).
- Live Windsor analytics pulls (reads snapshots for now).
- Premium TTS (ElevenLabs).
- Auto-posting / scheduling (Phase 4, needs Graph API).
- 24/7 background subagents (Phase 4).

## 9. Done when

- `backend/` runs locally, exposes `POST /api/chat`, and the agent answers brand/voice/
  analytics questions from the brain + snapshots.
- The agent can generate a hook/subhook/caption via the caption tool and save a draft.
- The dashboard Conversation tab streams replies and the speak-replies toggle works.
- Dictating with Wispr Flow into the input drives the whole loop end to end.
- The agent has no means to post to Instagram.
