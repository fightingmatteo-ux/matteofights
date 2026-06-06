# Jarvis backend (Phase 3)

Local Claude Agent SDK process. Talk to the @matteofights brain by voice/text.

## Run

```bash
cp .env.example .env   # set ANTHROPIC_API_KEY
npm install
npm run dev            # http://localhost:8787
```

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
