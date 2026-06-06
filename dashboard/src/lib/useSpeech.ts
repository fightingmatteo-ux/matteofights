import { useCallback, useEffect, useRef, useState } from "react";

/**
 * Browser TTS with a synthetic amplitude envelope. speechSynthesis exposes no audio
 * stream, so `levelRef` is driven by word-boundary events (bump) + a decay interval —
 * it reads as "talking" without being literal waveform data.
 */
export function useSpeech(): {
  speak: (text: string) => void;
  speaking: boolean;
  levelRef: React.MutableRefObject<number>;
} {
  const [speaking, setSpeaking] = useState(false);
  const levelRef = useRef(0);
  const decay = useRef<number | undefined>(undefined);

  const stopDecay = () => {
    if (decay.current) {
      window.clearInterval(decay.current);
      decay.current = undefined;
    }
  };

  const speak = useCallback((text: string) => {
    if (typeof window === "undefined" || !window.speechSynthesis || !text.trim()) return;
    window.speechSynthesis.cancel();
    const u = new SpeechSynthesisUtterance(text);
    u.onstart = () => {
      setSpeaking(true);
      levelRef.current = 0.6;
      stopDecay();
      decay.current = window.setInterval(() => {
        levelRef.current *= 0.85;
      }, 50);
    };
    u.onboundary = () => {
      levelRef.current = 0.55 + Math.random() * 0.45;
    };
    const finish = () => {
      setSpeaking(false);
      levelRef.current = 0;
      stopDecay();
    };
    u.onend = finish;
    u.onerror = finish;
    window.speechSynthesis.speak(u);
  }, []);

  useEffect(() => stopDecay, []);

  return { speak, speaking, levelRef };
}
