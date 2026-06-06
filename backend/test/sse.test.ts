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
