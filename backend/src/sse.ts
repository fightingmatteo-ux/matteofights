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
