# Jarvis Voice Layer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A local Node/TypeScript backend wrapping the Claude Agent SDK that answers from the @matteofights brain, reasons over analytics, and saves reel drafts — plus a Conversation tab in the dashboard you talk to (Wispr Flow dictates in; browser TTS optionally speaks out).

**Architecture:** One Express process exposes `POST /api/chat` (SSE). It runs the Claude Agent SDK (`query()`) scoped to the repo with read-only file tools (`Read`/`Grep`/`Glob`) + one in-process MCP tool (`save_reel_draft`). The repo's `CLAUDE.md` loads automatically via `settingSources: ['project']`, so the agent reads `context/`, `analytics/`, and `CAPTION-ENGINE.md` on demand exactly as Claude does in this repo. The dashboard gains a Conversation panel that streams the SSE response and can read it aloud. No Write/Bash/posting tools exist for the agent — drafting only, per the OPERATING RULES.

**Tech Stack:** Node 20+, TypeScript, Express, `@anthropic-ai/claude-agent-sdk`, `zod`, `dotenv`; Vitest for backend unit tests. Frontend: existing Vite + React + TS dashboard.

**Spec:** [2026-06-05-jarvis-voice-layer-design.md](../specs/2026-06-05-jarvis-voice-layer-design.md)

**Testing note (reconciling TDD with the project's token discipline):** Pure, deterministic logic (draft builder, validation, SSE framing, the route handler with a mocked agent) is built test-first with Vitest. The **live agent loop** and **UI** are verified with documented manual smoke tests rather than automated API-calling tests — running the real model in CI would burn tokens for little signal. This is a deliberate scope choice, not an omission.

---

## File structure

```
backend/                         # NEW — the Jarvis process
  package.json
  tsconfig.json
  .env.example                   # ANTHROPIC_API_KEY, PORT
  src/
    config.ts                    # repo root resolution, model, persona, port
    reelDraft.ts                 # pure: validate + render reel.md markdown + slug
    saveReelDraft.ts             # fs writer (uses reelDraft.ts)
    captionTool.ts               # save_reel_draft MCP tool + createSdkMcpServer
    sse.ts                       # SSE write helpers
    agent.ts                     # runJarvisTurn(): query() -> normalized JarvisEvent stream
    chatHandler.ts               # POST /api/chat handler (agent stream -> SSE)
    server.ts                    # Express wiring + listen
  test/
    reelDraft.test.ts
    sse.test.ts
    chatHandler.test.ts

dashboard/                       # EXTEND
  vite.config.ts                 # add /api dev proxy        (modify)
  src/
    lib/useChat.ts               # NEW — transcript + SSE consumption + session id
    components/Conversation.tsx  # NEW — chat panel + speak-replies toggle
    App.tsx                      # add Dashboard|Jarvis tab nav (modify)
```

---

## Task 1: Backend scaffold

**Files:**
- Create: `backend/package.json`, `backend/tsconfig.json`, `backend/.env.example`
- Modify: `.gitignore` (root)

- [ ] **Step 1: Create `backend/package.json`**

```json
{
  "name": "matteofights-backend",
  "private": true,
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "tsx watch src/server.ts",
    "start": "tsx src/server.ts",
    "test": "vitest run",
    "typecheck": "tsc --noEmit"
  },
  "dependencies": {
    "@anthropic-ai/claude-agent-sdk": "^0.1.0",
    "dotenv": "^16.4.5",
    "express": "^4.21.2",
    "zod": "^3.23.8"
  },
  "devDependencies": {
    "@types/express": "^5.0.0",
    "@types/node": "^22.10.0",
    "tsx": "^4.19.2",
    "typescript": "^5.6.3",
    "vitest": "^2.1.8"
  }
}
```

- [ ] **Step 2: Create `backend/tsconfig.json`**

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "ES2022",
    "moduleResolution": "bundler",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "resolveJsonModule": true,
    "noEmit": true,
    "types": ["node"]
  },
  "include": ["src", "test"]
}
```

- [ ] **Step 3: Create `backend/.env.example`**

```
# Anthropic API key the Claude Agent SDK uses for inference
ANTHROPIC_API_KEY=
# Port the Jarvis backend listens on
PORT=8787
```

- [ ] **Step 4: Add backend artifacts to root `.gitignore`**

Append these lines to the existing root `.gitignore` (do not remove existing entries):

```
# backend
backend/node_modules/
backend/.env
```

- [ ] **Step 5: Install dependencies**

Run: `cd backend && npm install`
Expected: completes without error; `backend/node_modules/` and `backend/package-lock.json` created. If `@anthropic-ai/claude-agent-sdk` resolves to a newer minor than `^0.1.0`, that is fine — record the resolved version in the commit.

- [ ] **Step 6: Commit**

```bash
git add backend/package.json backend/tsconfig.json backend/.env.example backend/package-lock.json .gitignore
git commit -m "Phase 3: backend scaffold (Express + Claude Agent SDK)"
```

---

## Task 2: Reel-draft builder (pure logic, TDD)

The deterministic core of the `save_reel_draft` tool: validate the fields the agent composed (enforcing the brain's non-negotiables — `HELP` trigger, 2–4 hashtags, known archetype, number-pointer subhook) and render the exact `reel.md` format the manual flow uses.

**Files:**
- Create: `backend/src/reelDraft.ts`
- Test: `backend/test/reelDraft.test.ts`

- [ ] **Step 1: Write the failing test**

```typescript
// backend/test/reelDraft.test.ts
import { describe, it, expect } from "vitest";
import { slugify, validateReelInput, renderReelMarkdown, type ReelInput } from "../src/reelDraft";

const valid: ReelInput = {
  date: "2026-06-05",
  archetype: "IDENTITY",
  thumbnail: "6 SIGNS YOU'LL MAKE IT AS A FIGHTER",
  subhook: "Most people quit the second it stops being fun.\nAnd almost none of them get past #4.",
  caption: "Most people quit...\n\n6 signs you'll make it:\n\n1. ...",
  hashtags: ["#boxing", "#fightermindset", "#muaythai", "#fightlife"],
};

describe("slugify", () => {
  it("kebab-cases and strips punctuation", () => {
    expect(slugify("6 SIGNS YOU'LL MAKE IT AS A FIGHTER")).toBe("6-signs-youll-make-it-as-a-fighter");
  });
});

describe("validateReelInput", () => {
  it("accepts a valid identity reel", () => {
    expect(validateReelInput(valid)).toEqual([]);
  });
  it("rejects a non-HELP dm trigger implicitly (trigger is fixed to HELP, not an input)", () => {
    // dm_trigger is not caller-supplied; rendered output must always be HELP — see render test
    expect(validateReelInput(valid)).toEqual([]);
  });
  it("rejects fewer than 2 or more than 4 hashtags", () => {
    expect(validateReelInput({ ...valid, hashtags: ["#one"] })).toContain("hashtags must be 2-4 items");
    expect(validateReelInput({ ...valid, hashtags: ["#a", "#b", "#c", "#d", "#e"] })).toContain("hashtags must be 2-4 items");
  });
  it("rejects an unknown archetype", () => {
    expect(validateReelInput({ ...valid, archetype: "STANCE" as unknown as ReelInput["archetype"] }))
      .toContain("archetype must be TACTICAL or IDENTITY");
  });
  it("warns when the subhook does not point at a numbered item", () => {
    expect(validateReelInput({ ...valid, subhook: "Most people quit.\nA few were built for it." }))
      .toContain("subhook should point at a specific number (e.g. #4)");
  });
});

describe("renderReelMarkdown", () => {
  it("renders the canonical reel.md with HELP trigger and all sections", () => {
    const md = renderReelMarkdown(valid);
    expect(md).toContain("date: 2026-06-05");
    expect(md).toContain("archetype: IDENTITY");
    expect(md).toContain("dm_trigger: HELP");
    expect(md).toContain("# 6 SIGNS YOU'LL MAKE IT AS A FIGHTER");
    expect(md).toContain("## Thumbnail text (on-screen, ALL CAPS, red-on-black)");
    expect(md).toContain("## Subhook (caption opener, 2 lines)");
    expect(md).toContain("## Caption");
    expect(md).toContain("## Hashtags");
    expect(md).toContain("#boxing #fightermindset #muaythai #fightlife");
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && npx vitest run test/reelDraft.test.ts`
Expected: FAIL — cannot resolve `../src/reelDraft`.

- [ ] **Step 3: Write minimal implementation**

```typescript
// backend/src/reelDraft.ts
export type Archetype = "TACTICAL" | "IDENTITY";

export interface ReelInput {
  date: string;            // YYYY-MM-DD
  archetype: Archetype;
  thumbnail: string;       // on-screen hook, ALL CAPS
  subhook: string;         // 2 lines; line 2 points at a #number
  caption: string;         // full caption body
  hashtags: string[];      // 2-4 niche tags, each starting with #
}

export function slugify(s: string): string {
  return s
    .toLowerCase()
    .replace(/['']/g, "")
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

export function validateReelInput(input: ReelInput): string[] {
  const errors: string[] = [];
  if (input.archetype !== "TACTICAL" && input.archetype !== "IDENTITY") {
    errors.push("archetype must be TACTICAL or IDENTITY");
  }
  if (input.hashtags.length < 2 || input.hashtags.length > 4) {
    errors.push("hashtags must be 2-4 items");
  }
  if (!input.hashtags.every((h) => h.startsWith("#"))) {
    errors.push("each hashtag must start with #");
  }
  if (!/#\d/.test(input.subhook)) {
    errors.push("subhook should point at a specific number (e.g. #4)");
  }
  if (!/^\d{4}-\d{2}-\d{2}$/.test(input.date)) {
    errors.push("date must be YYYY-MM-DD");
  }
  return errors;
}

export function renderReelMarkdown(input: ReelInput): string {
  return `---
date: ${input.date}
status: draft
archetype: ${input.archetype}
dm_trigger: HELP
---

# ${input.thumbnail}

## Thumbnail text (on-screen, ALL CAPS, red-on-black)
${input.thumbnail}

## Subhook (caption opener, 2 lines)
${input.subhook}

## Caption
${input.caption}

## Hashtags
${input.hashtags.join(" ")}
`;
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && npx vitest run test/reelDraft.test.ts`
Expected: PASS (all cases).

- [ ] **Step 5: Commit**

```bash
git add backend/src/reelDraft.ts backend/test/reelDraft.test.ts
git commit -m "Phase 3: reel-draft validator + markdown renderer"
```

---

## Task 3: Draft writer

Writes the rendered markdown to `content-bank/captions/drafts/<date>-<slug>/reel.md`.

**Files:**
- Create: `backend/src/config.ts`, `backend/src/saveReelDraft.ts`
- Test: extend `backend/test/reelDraft.test.ts` (writer test in a temp dir)

- [ ] **Step 1: Create `backend/src/config.ts`**

```typescript
// backend/src/config.ts
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";

const here = dirname(fileURLToPath(import.meta.url));
// backend/src -> repo root is two levels up
export const REPO_ROOT = resolve(here, "..", "..");
export const DRAFTS_DIR = resolve(REPO_ROOT, "content-bank", "captions", "drafts");

export const MODEL = "claude-opus-4-8";
export const PORT = Number(process.env.PORT ?? 8787);

export const JARVIS_PERSONA = [
  "You are Jarvis for @matteofights — Matteo's fighter-brand Instagram operating system.",
  "Your operating rules and the routing table live in CLAUDE.md, which is already loaded.",
  "Read context/*.md, analytics/snapshots and analytics/reports, content-bank/, and",
  "production/captions/CAPTION-ENGINE.md on demand using the Read/Grep/Glob tools — do not guess.",
  "Drafting is free; publishing is not. You have no tool to post anything. When you produce a",
  "finished reel, call save_reel_draft to persist it; never claim anything was posted.",
  "Be concise and direct, in Matteo's voice. The north star is fighter-brand growth.",
].join(" ");
```

- [ ] **Step 2: Write the failing writer test (append to `backend/test/reelDraft.test.ts`)**

```typescript
// append to backend/test/reelDraft.test.ts
import { mkdtempSync, readFileSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { writeReelDraft } from "../src/saveReelDraft";

describe("writeReelDraft", () => {
  it("writes reel.md under <draftsDir>/<date>-<slug>/", () => {
    const dir = mkdtempSync(join(tmpdir(), "drafts-"));
    try {
      const path = writeReelDraft(valid, dir);
      expect(path).toBe(join(dir, "2026-06-05-6-signs-youll-make-it-as-a-fighter", "reel.md"));
      expect(readFileSync(path, "utf8")).toContain("dm_trigger: HELP");
    } finally {
      rmSync(dir, { recursive: true, force: true });
    }
  });
});
```

- [ ] **Step 3: Run test to verify it fails**

Run: `cd backend && npx vitest run test/reelDraft.test.ts`
Expected: FAIL — cannot resolve `../src/saveReelDraft`.

- [ ] **Step 4: Create `backend/src/saveReelDraft.ts`**

```typescript
// backend/src/saveReelDraft.ts
import { mkdirSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { DRAFTS_DIR } from "./config";
import { renderReelMarkdown, slugify, type ReelInput } from "./reelDraft";

/** Writes reel.md and returns its absolute path. `baseDir` overridable for tests. */
export function writeReelDraft(input: ReelInput, baseDir: string = DRAFTS_DIR): string {
  const folder = join(baseDir, `${input.date}-${slugify(input.thumbnail)}`);
  mkdirSync(folder, { recursive: true });
  const path = join(folder, "reel.md");
  writeFileSync(path, renderReelMarkdown(input), "utf8");
  return path;
}
```

- [ ] **Step 5: Run test to verify it passes**

Run: `cd backend && npx vitest run test/reelDraft.test.ts`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add backend/src/config.ts backend/src/saveReelDraft.ts backend/test/reelDraft.test.ts
git commit -m "Phase 3: draft writer + backend config"
```

---

## Task 4: `save_reel_draft` MCP tool

Wraps the writer as an in-process Agent SDK tool. The agent supplies the composed fields; the tool validates and persists.

**Files:**
- Create: `backend/src/captionTool.ts`

- [ ] **Step 1: Create `backend/src/captionTool.ts`**

```typescript
// backend/src/captionTool.ts
import { tool, createSdkMcpServer } from "@anthropic-ai/claude-agent-sdk";
import { z } from "zod";
import { validateReelInput, type ReelInput } from "./reelDraft";
import { writeReelDraft } from "./saveReelDraft";

const saveReelDraft = tool(
  "save_reel_draft",
  "Persist a finished reel (thumbnail hook, subhook, full caption, hashtags) as a draft markdown file. Use only after composing the reel from the brain. dm_trigger is always HELP. This does NOT post anything.",
  {
    date: z.string().describe("YYYY-MM-DD, usually today"),
    archetype: z.enum(["TACTICAL", "IDENTITY"]),
    thumbnail: z.string().describe("On-screen hook, ALL CAPS"),
    subhook: z.string().describe("2-line caption opener; line 2 points at a numbered item, e.g. 'And almost everyone skips #5.'"),
    caption: z.string().describe("Full caption body in Matteo's voice"),
    hashtags: z.array(z.string()).describe("2-4 niche combat hashtags, each starting with #"),
  },
  async (args) => {
    const input = args as ReelInput;
    const errors = validateReelInput(input);
    if (errors.length > 0) {
      return {
        content: [{ type: "text", text: `Draft rejected. Fix and retry:\n- ${errors.join("\n- ")}` }],
        isError: true,
      };
    }
    const path = writeReelDraft(input);
    return { content: [{ type: "text", text: `Draft saved to ${path}` }] };
  },
);

export const captionServer = createSdkMcpServer({
  name: "jarvis",
  version: "0.1.0",
  tools: [saveReelDraft],
});
```

- [ ] **Step 2: Typecheck**

Run: `cd backend && npx tsc --noEmit`
Expected: PASS (no type errors). If the SDK's `tool()` handler return type differs, adjust the returned object shape to match the SDK's exported content-block type — do not change the validation logic.

- [ ] **Step 3: Commit**

```bash
git add backend/src/captionTool.ts
git commit -m "Phase 3: save_reel_draft in-process MCP tool"
```

---

## Task 5: SSE helpers (TDD)

**Files:**
- Create: `backend/src/sse.ts`
- Test: `backend/test/sse.test.ts`

- [ ] **Step 1: Write the failing test**

```typescript
// backend/test/sse.test.ts
import { describe, it, expect } from "vitest";
import { sseFrame } from "../src/sse";

describe("sseFrame", () => {
  it("encodes an event as a single SSE data frame with double newline", () => {
    expect(sseFrame({ type: "text", text: "hi" })).toBe('data: {"type":"text","text":"hi"}\n\n');
  });
  it("escapes newlines inside payloads (stays one frame)", () => {
    const frame = sseFrame({ type: "text", text: "a\nb" });
    expect(frame.endsWith("\n\n")).toBe(true);
    expect(frame.split("\n\n")).toHaveLength(2); // payload + terminator
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && npx vitest run test/sse.test.ts`
Expected: FAIL — cannot resolve `../src/sse`.

- [ ] **Step 3: Write minimal implementation**

```typescript
// backend/src/sse.ts
import type { Response } from "express";

export type JarvisEvent =
  | { type: "session"; sessionId: string }
  | { type: "text"; text: string }
  | { type: "tool"; name: string }
  | { type: "done"; result: string }
  | { type: "error"; message: string };

/** One SSE frame. JSON.stringify escapes newlines, so each event is exactly one frame. */
export function sseFrame(event: JarvisEvent): string {
  return `data: ${JSON.stringify(event)}\n\n`;
}

export function writeSse(res: Response, event: JarvisEvent): void {
  res.write(sseFrame(event));
}

export function openSse(res: Response): void {
  res.writeHead(200, {
    "Content-Type": "text/event-stream",
    "Cache-Control": "no-cache",
    Connection: "keep-alive",
  });
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && npx vitest run test/sse.test.ts`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/src/sse.ts backend/test/sse.test.ts
git commit -m "Phase 3: SSE frame helpers"
```

---

## Task 6: Agent wrapper

Maps the Claude Agent SDK `query()` stream into normalized `JarvisEvent`s. This is the only file that touches the SDK message shapes.

**Files:**
- Create: `backend/src/agent.ts`

- [ ] **Step 1: Create `backend/src/agent.ts`**

```typescript
// backend/src/agent.ts
import { query } from "@anthropic-ai/claude-agent-sdk";
import { REPO_ROOT, MODEL, JARVIS_PERSONA } from "./config";
import { captionServer } from "./captionTool";
import type { JarvisEvent } from "./sse";

const READ_ONLY_TOOLS = ["Read", "Grep", "Glob"];
const ALLOWED_TOOLS = [...READ_ONLY_TOOLS, "mcp__jarvis__save_reel_draft"];

/**
 * Runs one conversational turn. On the first turn omit `sessionId`; capture the
 * emitted session id and pass it back on later turns to keep context.
 *
 * Guardrail: `tools` enables ONLY read-only file tools — no Write/Bash/Edit and
 * no posting tool exist, so the agent can draft but never publish.
 */
export async function* runJarvisTurn(
  userText: string,
  sessionId?: string,
): AsyncGenerator<JarvisEvent> {
  try {
    for await (const message of query({
      prompt: userText,
      options: {
        model: MODEL,
        thinking: { type: "adaptive" },
        effort: "high",
        cwd: REPO_ROOT,
        settingSources: ["project"], // loads CLAUDE.md (the brain's operating rules)
        systemPrompt: JARVIS_PERSONA,
        tools: READ_ONLY_TOOLS,
        allowedTools: ALLOWED_TOOLS,
        permissionMode: "default",
        mcpServers: {
          jarvis: { type: "sdk", name: "jarvis", instance: captionServer.instance },
        },
        ...(sessionId ? { resume: sessionId } : {}),
      },
    })) {
      if (message.type === "system" && "session_id" in message) {
        yield { type: "session", sessionId: message.session_id };
      } else if (message.type === "assistant") {
        for (const block of message.message.content ?? []) {
          if (block.type === "text") {
            yield { type: "text", text: block.text };
          } else if (block.type === "tool_use") {
            yield { type: "tool", name: block.name };
          }
        }
      } else if (message.type === "result") {
        yield { type: "done", result: message.result ?? "" };
      }
    }
  } catch (err) {
    yield { type: "error", message: err instanceof Error ? err.message : "Unknown agent error" };
  }
}
```

- [ ] **Step 2: Typecheck**

Run: `cd backend && npx tsc --noEmit`
Expected: PASS. If a property name differs from the SDK's exported types (e.g. the system message's session field, or the content block discriminant), correct it to match the SDK types — the control flow stays the same.

- [ ] **Step 3: Commit**

```bash
git add backend/src/agent.ts
git commit -m "Phase 3: agent wrapper (query -> JarvisEvent stream)"
```

---

## Task 7: Chat route handler (TDD with a mocked agent)

**Files:**
- Create: `backend/src/chatHandler.ts`
- Test: `backend/test/chatHandler.test.ts`

- [ ] **Step 1: Write the failing test**

```typescript
// backend/test/chatHandler.test.ts
import { describe, it, expect, vi } from "vitest";
import { makeChatHandler } from "../src/chatHandler";
import type { JarvisEvent } from "../src/sse";

function fakeRes() {
  const chunks: string[] = [];
  return {
    chunks,
    headersSent: false,
    writeHead: vi.fn(),
    write: (s: string) => { chunks.push(s); return true; },
    end: vi.fn(),
    status() { return this; },
    json: vi.fn(),
  } as any;
}

async function* fakeTurn(): AsyncGenerator<JarvisEvent> {
  yield { type: "session", sessionId: "sesn_1" };
  yield { type: "text", text: "hello" };
  yield { type: "done", result: "hello" };
}

describe("chat handler", () => {
  it("streams agent events as SSE frames", async () => {
    const handler = makeChatHandler(() => fakeTurn());
    const res = fakeRes();
    await handler({ body: { message: "hi" } } as any, res);
    const body = res.chunks.join("");
    expect(body).toContain('data: {"type":"session","sessionId":"sesn_1"}');
    expect(body).toContain('data: {"type":"text","text":"hello"}');
    expect(body).toContain('data: {"type":"done","result":"hello"}');
    expect(res.end).toHaveBeenCalled();
  });

  it("400s when message is missing", async () => {
    const handler = makeChatHandler(() => fakeTurn());
    const res = fakeRes();
    await handler({ body: {} } as any, res);
    expect(res.json).toHaveBeenCalledWith({ error: "message is required" });
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && npx vitest run test/chatHandler.test.ts`
Expected: FAIL — cannot resolve `../src/chatHandler`.

- [ ] **Step 3: Write minimal implementation**

```typescript
// backend/src/chatHandler.ts
import type { Request, Response } from "express";
import { openSse, writeSse, type JarvisEvent } from "./sse";

type TurnRunner = (message: string, sessionId?: string) => AsyncGenerator<JarvisEvent>;

/** Factory so tests can inject a fake turn runner instead of calling the real agent. */
export function makeChatHandler(runTurn: TurnRunner) {
  return async function chatHandler(req: Request, res: Response): Promise<void> {
    const message = req.body?.message;
    const sessionId = req.body?.sessionId;
    if (typeof message !== "string" || message.trim() === "") {
      res.status(400).json({ error: "message is required" });
      return;
    }
    openSse(res);
    try {
      for await (const event of runTurn(message, sessionId)) {
        writeSse(res, event);
      }
    } catch (err) {
      writeSse(res, { type: "error", message: err instanceof Error ? err.message : "stream failed" });
    } finally {
      res.end();
    }
  };
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && npx vitest run test/chatHandler.test.ts`
Expected: PASS (both cases).

- [ ] **Step 5: Commit**

```bash
git add backend/src/chatHandler.ts backend/test/chatHandler.test.ts
git commit -m "Phase 3: /api/chat handler (SSE stream from agent)"
```

---

## Task 8: Express server

**Files:**
- Create: `backend/src/server.ts`

- [ ] **Step 1: Create `backend/src/server.ts`**

```typescript
// backend/src/server.ts
import "dotenv/config";
import express from "express";
import { PORT } from "./config";
import { makeChatHandler } from "./chatHandler";
import { runJarvisTurn } from "./agent";

const app = express();
app.use(express.json({ limit: "1mb" }));

app.get("/api/health", (_req, res) => {
  res.json({ ok: true, hasKey: Boolean(process.env.ANTHROPIC_API_KEY) });
});

app.post("/api/chat", makeChatHandler(runJarvisTurn));

app.listen(PORT, () => {
  console.log(`Jarvis backend listening on http://localhost:${PORT}`);
});
```

- [ ] **Step 2: Run the full backend test suite + typecheck**

Run: `cd backend && npx vitest run && npx tsc --noEmit`
Expected: all tests PASS, no type errors.

- [ ] **Step 3: Commit**

```bash
git add backend/src/server.ts
git commit -m "Phase 3: Express server with /api/chat and /api/health"
```

---

## Task 9: Backend manual smoke (live agent)

This is the manual gate that exercises the real model — run it once, by hand, not in CI.

**Files:** none (verification only)

- [ ] **Step 1: Provide an API key**

Copy `backend/.env.example` to `backend/.env` and set `ANTHROPIC_API_KEY` to a real key.

- [ ] **Step 2: Start the backend**

Run: `cd backend && npm run dev`
Expected: `Jarvis backend listening on http://localhost:8787`.

- [ ] **Step 3: Health check**

Run (new terminal): `curl http://localhost:8787/api/health`
Expected: `{"ok":true,"hasKey":true}`.

- [ ] **Step 4: Brain question (reads context/ + analytics/)**

Run:
```bash
curl -N -X POST http://localhost:8787/api/chat -H "Content-Type: application/json" \
  -d '{"message":"What are my two viral archetypes and which reel drove the surge?"}'
```
Expected: a stream of `data: {"type":"tool","name":"Read"}` / `Grep` frames (it reads the brain), then `data: {"type":"text",...}` frames whose text references the tactical + identity archetypes and the 320k "born to be a fighter" reel, then a `done` frame. Confirms brain + analytics reading works.

- [ ] **Step 5: Draft generation (exercises save_reel_draft)**

Run:
```bash
curl -N -X POST http://localhost:8787/api/chat -H "Content-Type: application/json" \
  -d '{"message":"Write an identity reel in our viral format about staying disciplined when no one is watching, and save it as a draft."}'
```
Expected: a `data: {"type":"tool","name":"save_reel_draft"}` frame, and a new folder under `content-bank/captions/drafts/` containing a `reel.md` with `dm_trigger: HELP`, a number-pointer subhook, and 2–4 hashtags. Verify the file exists and reads correctly.

- [ ] **Step 6: Guardrail check**

Run:
```bash
curl -N -X POST http://localhost:8787/api/chat -H "Content-Type: application/json" \
  -d '{"message":"Post that last reel to Instagram right now."}'
```
Expected: the agent explains it cannot post / has no posting capability and offers the draft instead. Confirm no posting tool appears in any `tool` frame. This is the load-bearing guardrail — do not proceed if it claims to have posted.

- [ ] **Step 7: No commit** (verification task). If any step fails, fix the relevant earlier task before continuing.

---

## Task 10: Dashboard — chat hook

**Files:**
- Create: `dashboard/src/lib/useChat.ts`

- [ ] **Step 1: Create `dashboard/src/lib/useChat.ts`**

```typescript
// dashboard/src/lib/useChat.ts
import { useRef, useState } from "react";

export type Turn = { role: "user" | "assistant"; text: string };
type ToolName = string;

type ServerEvent =
  | { type: "session"; sessionId: string }
  | { type: "text"; text: string }
  | { type: "tool"; name: ToolName }
  | { type: "done"; result: string }
  | { type: "error"; message: string };

export function useChat(onAssistantDone?: (text: string) => void) {
  const [turns, setTurns] = useState<Turn[]>([]);
  const [activity, setActivity] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const sessionId = useRef<string | undefined>(undefined);

  async function send(message: string) {
    if (busy || !message.trim()) return;
    setBusy(true);
    setTurns((t) => [...t, { role: "user", text: message }, { role: "assistant", text: "" }]);

    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message, sessionId: sessionId.current }),
    });
    if (!res.body) {
      setBusy(false);
      return;
    }

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    let assistantText = "";

    // SSE frames are separated by a blank line.
    // eslint-disable-next-line no-constant-condition
    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const frames = buffer.split("\n\n");
      buffer = frames.pop() ?? "";
      for (const frame of frames) {
        const line = frame.replace(/^data: /, "").trim();
        if (!line) continue;
        const evt = JSON.parse(line) as ServerEvent;
        if (evt.type === "session") {
          sessionId.current = evt.sessionId;
        } else if (evt.type === "tool") {
          setActivity(`${evt.name}…`);
        } else if (evt.type === "text") {
          assistantText += evt.text;
          setTurns((t) => {
            const next = [...t];
            next[next.length - 1] = { role: "assistant", text: assistantText };
            return next;
          });
        } else if (evt.type === "error") {
          assistantText += `\n[error: ${evt.message}]`;
          setTurns((t) => {
            const next = [...t];
            next[next.length - 1] = { role: "assistant", text: assistantText };
            return next;
          });
        }
      }
    }
    setActivity(null);
    setBusy(false);
    if (assistantText) onAssistantDone?.(assistantText);
  }

  return { turns, activity, busy, send };
}
```

- [ ] **Step 2: Typecheck**

Run: `cd dashboard && npx tsc --noEmit`
Expected: PASS.

- [ ] **Step 3: Commit**

```bash
git add dashboard/src/lib/useChat.ts
git commit -m "Phase 3: dashboard useChat hook (SSE consumption + session id)"
```

---

## Task 11: Dashboard — Conversation panel + speak toggle

**Files:**
- Create: `dashboard/src/components/Conversation.tsx`

- [ ] **Step 1: Create `dashboard/src/components/Conversation.tsx`**

```tsx
// dashboard/src/components/Conversation.tsx
import { useRef, useState } from "react";
import { useChat } from "../lib/useChat";
import { Eyebrow } from "./primitives";

export function Conversation() {
  const [speak, setSpeak] = useState(false);
  const [draft, setDraft] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  const speakReply = (text: string) => {
    if (!speak || typeof window === "undefined" || !window.speechSynthesis) return;
    window.speechSynthesis.cancel();
    window.speechSynthesis.speak(new SpeechSynthesisUtterance(text));
  };

  const { turns, activity, busy, send } = useChat(speakReply);

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    const text = draft;
    setDraft("");
    void send(text);
    inputRef.current?.focus();
  };

  return (
    <section className="mx-auto max-w-[1320px] px-5 sm:px-8 py-6">
      <div className="flex items-center justify-between mb-4">
        <Eyebrow>Jarvis</Eyebrow>
        <label className="font-mono text-[11px] text-muted flex items-center gap-2 cursor-pointer">
          <input type="checkbox" checked={speak} onChange={(e) => setSpeak(e.target.checked)} />
          🔊 speak replies
        </label>
      </div>

      <div className="space-y-3 min-h-[40vh]">
        {turns.length === 0 && (
          <p className="font-mono text-[12px] text-muted">
            Dictate or type — ask about your analytics, or have Jarvis draft a reel.
          </p>
        )}
        {turns.map((t, i) => (
          <div
            key={i}
            className={`whitespace-pre-wrap text-[14px] leading-relaxed ${
              t.role === "user" ? "text-gold" : "text-fg"
            }`}
          >
            <span className="font-mono text-[10px] uppercase tracking-[0.18em] text-muted mr-2">
              {t.role === "user" ? "you" : "jarvis"}
            </span>
            {t.text || (busy && i === turns.length - 1 ? "…" : "")}
          </div>
        ))}
        {activity && <div className="font-mono text-[11px] text-muted">{activity}</div>}
      </div>

      <form onSubmit={submit} className="mt-6 flex gap-2">
        <input
          ref={inputRef}
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          placeholder="Talk to Jarvis (Wispr Flow dictates here)…"
          className="flex-1 bg-transparent border border-line px-3 py-2 font-mono text-[13px] text-fg outline-none focus:border-gold"
          disabled={busy}
        />
        <button
          type="submit"
          disabled={busy || !draft.trim()}
          className="border border-line px-4 py-2 font-mono text-[11px] uppercase tracking-[0.18em] text-fg hover:border-gold disabled:opacity-40"
        >
          Send
        </button>
      </form>
    </section>
  );
}
```

- [ ] **Step 2: Typecheck**

Run: `cd dashboard && npx tsc --noEmit`
Expected: PASS. If `text-fg` / `text-muted` / `text-gold` / `border-line` are not all defined in `tailwind.config.js`, use the exact token names already used elsewhere in the dashboard (grep `text-muted` / `text-gold` in `dashboard/src` — they appear in `App.tsx` and `primitives.tsx`, so they exist).

- [ ] **Step 3: Commit**

```bash
git add dashboard/src/components/Conversation.tsx
git commit -m "Phase 3: Conversation panel + speak-replies toggle"
```

---

## Task 12: Dashboard — tab nav + dev proxy

**Files:**
- Modify: `dashboard/src/App.tsx`, `dashboard/vite.config.ts`

- [ ] **Step 1: Add the `/api` dev proxy to `dashboard/vite.config.ts`**

Replace the file with:

```typescript
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// base "./" keeps the build portable — works at any path on Vercel/Netlify/static hosts.
export default defineConfig({
  base: "./",
  plugins: [react()],
  server: {
    proxy: {
      "/api": "http://localhost:8787",
    },
  },
});
```

- [ ] **Step 2: Add tab nav to `dashboard/src/App.tsx`**

Replace the file with:

```tsx
import { useState } from "react";
import { useSnapshot } from "./lib/useSnapshot";
import { Grain } from "./components/primitives";
import { Header } from "./components/Header";
import { Telemetry } from "./components/Telemetry";
import { SurgeChart } from "./components/SurgeChart";
import { Leaderboard } from "./components/Leaderboard";
import { Conversation } from "./components/Conversation";
import { EmptyState, ErrorState, LoadingState } from "./components/States";

type Tab = "dashboard" | "jarvis";

export default function App() {
  const state = useSnapshot();
  const [tab, setTab] = useState<Tab>("dashboard");

  return (
    <>
      <Grain />
      <nav className="mx-auto max-w-[1320px] px-5 sm:px-8 pt-5 flex gap-4 font-mono text-[11px] uppercase tracking-[0.18em]">
        {(["dashboard", "jarvis"] as Tab[]).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={tab === t ? "text-gold" : "text-muted hover:text-fg"}
          >
            {t}
          </button>
        ))}
      </nav>

      {tab === "jarvis" && <Conversation />}

      {tab === "dashboard" && (
        <>
          {state.status === "loading" && <LoadingState />}
          {state.status === "error" && <ErrorState message={state.message} />}
          {state.status === "empty" && <EmptyState />}
          {state.status === "ready" && (
            <main>
              <Header data={state.data} />
              <Telemetry data={state.data} />
              <SurgeChart data={state.data} />
              <Leaderboard data={state.data} />
              <footer className="border-t border-line">
                <div className="mx-auto max-w-[1320px] px-5 sm:px-8 py-6 flex items-center justify-between font-mono text-[11px] text-muted flex-wrap gap-2">
                  <span>@{state.data.account.username} · id {state.data.account.id}</span>
                  <span>
                    DM trigger:{" "}
                    <span className="text-gold">{state.data.profile.dm_trigger_current}</span> · north
                    star: grow the fighter brand
                  </span>
                </div>
              </footer>
            </main>
          )}
        </>
      )}
    </>
  );
}
```

- [ ] **Step 3: Typecheck + build**

Run: `cd dashboard && npx tsc --noEmit && npm run build`
Expected: both PASS (build emits `dist/`).

- [ ] **Step 4: Commit**

```bash
git add dashboard/src/App.tsx dashboard/vite.config.ts
git commit -m "Phase 3: dashboard Dashboard|Jarvis tab nav + /api dev proxy"
```

---

## Task 13: End-to-end manual smoke

**Files:** none (verification only)

- [ ] **Step 1: Run both processes**

Terminal A: `cd backend && npm run dev`
Terminal B: `cd dashboard && npm run dev`

- [ ] **Step 2: Open the dashboard, switch to the Jarvis tab**

Open the Vite URL (e.g. `http://localhost:5173`). Click **JARVIS**.

- [ ] **Step 3: Dictate with Wispr Flow**

Focus the input, dictate: "How did my last reel do and what should I post next?" Confirm the text appears, send, and Jarvis streams a reply that references real brain/analytics content; tool activity ("Read…") shows during the turn.

- [ ] **Step 4: Speak toggle**

Enable **🔊 speak replies**, send another message, confirm the reply is read aloud via the browser voice. Disable it and confirm it stops.

- [ ] **Step 5: Draft round-trip**

Ask Jarvis to write and save an identity reel. Confirm a new `content-bank/captions/drafts/<date>-<slug>/reel.md` appears and follows the format (HELP trigger, number-pointer subhook, 2–4 hashtags).

- [ ] **Step 6: No commit** (verification). Fix earlier tasks if anything fails.

---

## Task 14: README + publish-tool seam note

Document how to run the layer and mark exactly where the future confirmation-gated Graph API publish tool plugs in (Matteo is setting up the Graph API separately).

**Files:**
- Create: `backend/README.md`

- [ ] **Step 1: Create `backend/README.md`**

````markdown
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
````

- [ ] **Step 2: Commit**

```bash
git add backend/README.md
git commit -m "Phase 3: backend README + publish-tool seam note"
```

---

## Self-review (completed by plan author)

- **Spec coverage:** §3.1 backend → Tasks 1,4,6,7,8; §3.2 dashboard panel + speak toggle → Tasks 10,11,12; §3.3 brain/analytics read + caption tool → Tasks 2,3,4,6 (`settingSources`, Read/Grep/Glob, `save_reel_draft`); §4 data flow → Tasks 7,10,13; §5 guardrail → Task 6 (`tools` allowlist) + Task 9 step 6 + Task 14; §6 error handling → Tasks 6 (try/catch), 7 (handler catch), 10 (error event render); §7 tech stack → Task 1; §9 done-when → Tasks 9 + 13. Live Windsor pull / video render / premium TTS / posting are correctly absent (spec §8 out of scope).
- **Placeholder scan:** no TBD/TODO; every code step shows complete code; manual-smoke tasks are explicitly verification-only, not stubs.
- **Type consistency:** `JarvisEvent` defined in `sse.ts` and reused by `agent.ts`, `chatHandler.ts`, and mirrored in `useChat.ts`; `ReelInput` defined in `reelDraft.ts` and consumed by `saveReelDraft.ts` + `captionTool.ts`; tool name `mcp__jarvis__save_reel_draft` consistent between `agent.ts` allowlist and the `jarvis` MCP server name in `captionTool.ts`.
- **Known runtime-verify points (flagged in-task, not guesses):** exact SDK system-message session field, content-block discriminants, and `tool()` return shape are confirmed against the SDK types during the Task 4/6 typecheck steps; if a name differs, correct it without changing control flow.
