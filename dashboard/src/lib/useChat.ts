import { useRef, useState } from "react";

export type Turn = { role: "user" | "assistant"; text: string };

type ServerEvent =
  | { type: "session"; sessionId: string }
  | { type: "text"; text: string }
  | { type: "tool"; name: string; target?: string }
  | { type: "done"; result: string }
  | { type: "error"; message: string };

export interface ChatCallbacks {
  /** Fired for each tool the agent uses (drives the brain constellation). */
  onTool?: (name: string, target?: string) => void;
  /** Fired once the assistant turn finishes, with the full reply text. */
  onDone?: (text: string) => void;
}

export function useChat(cb: ChatCallbacks = {}) {
  const [turns, setTurns] = useState<Turn[]>([]);
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
          cb.onTool?.(evt.name, evt.target);
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
    setBusy(false);
    if (assistantText) cb.onDone?.(assistantText);
  }

  return { turns, busy, send };
}
