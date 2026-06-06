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
