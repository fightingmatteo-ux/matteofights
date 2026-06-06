import { query } from "@anthropic-ai/claude-agent-sdk";
import { REPO_ROOT, MODEL, JARVIS_PERSONA } from "./config";
import { captionServer } from "./captionTool";
import type { JarvisEvent } from "./sse";

const READ_ONLY_TOOLS = ["Read", "Grep", "Glob"];
const ALLOWED_TOOLS = [...READ_ONLY_TOOLS, "mcp__jarvis__save_reel_draft"];

/** Pull a human/UI-meaningful target from a tool_use input (file path or pattern). */
function toolTarget(input: unknown): string | undefined {
  if (input && typeof input === "object") {
    const o = input as Record<string, unknown>;
    for (const key of ["file_path", "path", "pattern", "query"]) {
      const v = o[key];
      if (typeof v === "string" && v.length > 0) return v;
    }
  }
  return undefined;
}

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
        effort: "medium", // conserves Claude Pro usage limits; raise to "high" on paid API/Max

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
            yield { type: "tool", name: block.name, target: toolTarget(block.input) };
          }
        }
      } else if (message.type === "result") {
        if (message.subtype === "success") {
          yield { type: "done", result: message.result };
        } else {
          yield { type: "error", message: `Run ended: ${message.subtype}` };
        }
      }
    }
  } catch (err) {
    yield { type: "error", message: err instanceof Error ? err.message : "Unknown agent error" };
  }
}
