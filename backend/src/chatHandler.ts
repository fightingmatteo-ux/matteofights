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
