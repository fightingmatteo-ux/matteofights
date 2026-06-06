import { describe, it, expect, vi } from "vitest";
import { makeChatHandler } from "../src/chatHandler";
import type { JarvisEvent } from "../src/sse";

function fakeRes() {
  const chunks: string[] = [];
  return {
    chunks,
    headersSent: false,
    writeHead: vi.fn(),
    write: (s: string) => {
      chunks.push(s);
      return true;
    },
    end: vi.fn(),
    status() {
      return this;
    },
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
