import { useCallback, useRef, useState } from "react";
import { useChat } from "../lib/useChat";
import { useMicLevel } from "../lib/useMicLevel";
import { useSpeech } from "../lib/useSpeech";
import { BrainConstellation } from "./BrainConstellation";
import { derivePhase, targetToNode, type NodeId } from "../lib/brainNodes";
import { Eyebrow } from "./primitives";

export function Conversation() {
  const [speakOn, setSpeakOn] = useState(false);
  const [draft, setDraft] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  const { speak, speaking, levelRef: ttsLevelRef } = useSpeech();
  const { levelRef: micLevelRef, status: micStatus } = useMicLevel();

  const [activeNode, setActiveNode] = useState<NodeId | null>(null);
  const [toolKind, setToolKind] = useState<"reading" | "drafting" | null>(null);
  const clearTimer = useRef<number | undefined>(undefined);

  const onTool = useCallback((name: string, target?: string) => {
    setActiveNode(targetToNode(name, target));
    setToolKind(name.includes("save_reel_draft") ? "drafting" : "reading");
    if (clearTimer.current) window.clearTimeout(clearTimer.current);
    clearTimer.current = window.setTimeout(() => {
      setToolKind(null);
      setActiveNode(null);
    }, 1600);
  }, []);

  const onDone = useCallback(
    (text: string) => {
      if (speakOn) speak(text);
    },
    [speakOn, speak],
  );

  const { turns, busy, send } = useChat({ onTool, onDone });

  const phase = derivePhase({
    busy,
    speaking,
    reading: toolKind === "reading",
    drafting: toolKind === "drafting",
    listening: micStatus === "granted",
  });

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    const text = draft;
    setDraft("");
    void send(text);
    inputRef.current?.focus();
  };

  return (
    <section className="mx-auto max-w-[1320px] px-5 sm:px-8 py-6">
      <div className="flex items-center justify-between mb-2">
        <Eyebrow>Jarvis</Eyebrow>
        <label className="font-mono text-[11px] text-muted flex items-center gap-2 cursor-pointer">
          <input type="checkbox" checked={speakOn} onChange={(e) => setSpeakOn(e.target.checked)} />
          🔊 speak replies
        </label>
      </div>

      <BrainConstellation
        phase={phase}
        activeNode={activeNode}
        micLevelRef={micLevelRef}
        ttsLevelRef={ttsLevelRef}
      />

      <div className="space-y-3 min-h-[20vh]">
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
