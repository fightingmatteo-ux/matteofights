# Jarvis backend (Phase 3)

Local Claude Agent SDK process. Talk to the @matteofights brain by voice/text.

## Run

The agent runs the Claude Code engine, so it can authenticate **two ways**:

**A. Claude Pro/Max subscription (no per-token cost — default).** Log in once with
the Claude Code CLI and leave `ANTHROPIC_API_KEY` unset:

```bash
npm i -g @anthropic-ai/claude-code   # if you don't already have it
claude                               # log in with your Anthropic account in the browser, then exit
npm install
npm run dev                          # http://localhost:8787  (uses your subscription)
```

Heads-up: Pro's usage limits are modest and reset every few hours; heavy use will
hit them. The default model is **Sonnet** (`src/config.ts`) to stretch the plan —
Opus is heavily limited on Pro.

**B. Paid Anthropic API.** Put a key in `.env` (`cp .env.example .env`, set
`ANTHROPIC_API_KEY`). If the key is set it takes precedence over the subscription.

Then run the dashboard (`cd ../dashboard && npm run dev`) and open the **Jarvis** tab.
The dashboard proxies `/api` to this server.

## Capabilities

- Reads `context/`, `analytics/`, `content-bank/`, `CAPTION-ENGINE.md` on demand.
- Generates hooks/subhooks/captions and saves drafts via `save_reel_draft`.

## Guardrail

The agent is given only read-only file tools plus `save_reel_draft`. There is **no
posting tool** — drafting only, per the OPERATING RULES. Publishing stays manual.

## Adding posting later (Phase 4 seam)

When the Instagram Graph API token is ready, add a `publish_reel` tool in a new
`src/publishTool.ts`, register it on `captionServer`, and **gate it behind explicit
in-chat confirmation** via the SDK `canUseTool` callback in `agent.ts` (return a
permission prompt for `mcp__jarvis__publish_reel` so Jarvis must get a yes before
posting). Until then, publish manually via Meta Business Suite.
