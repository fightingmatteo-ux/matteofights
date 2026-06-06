import { useEffect, useRef, useState } from "react";

export type MicStatus = "idle" | "granted" | "denied";

/**
 * Requests the mic once and exposes a live 0–1 amplitude in a ref (read it from a
 * requestAnimationFrame loop, not React state, to avoid re-render churn). On denial
 * the level stays 0 and status is "denied" — callers degrade to a calm visual.
 */
export function useMicLevel(): { levelRef: React.MutableRefObject<number>; status: MicStatus } {
  const levelRef = useRef(0);
  const [status, setStatus] = useState<MicStatus>("idle");

  useEffect(() => {
    let ctx: AudioContext | null = null;
    let stream: MediaStream | null = null;
    let raf = 0;
    let cancelled = false;

    (async () => {
      try {
        stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        if (cancelled) {
          stream.getTracks().forEach((t) => t.stop());
          return;
        }
        ctx = new AudioContext();
        const src = ctx.createMediaStreamSource(stream);
        const analyser = ctx.createAnalyser();
        analyser.fftSize = 512;
        src.connect(analyser);
        const data = new Uint8Array(analyser.frequencyBinCount);
        setStatus("granted");

        const tick = () => {
          analyser.getByteTimeDomainData(data);
          let sum = 0;
          for (let i = 0; i < data.length; i++) {
            const v = (data[i] - 128) / 128;
            sum += v * v;
          }
          const rms = Math.sqrt(sum / data.length);
          levelRef.current = Math.min(1, rms * 3); // amplify quiet speech
          raf = requestAnimationFrame(tick);
        };
        tick();
      } catch {
        if (!cancelled) setStatus("denied");
      }
    })();

    return () => {
      cancelled = true;
      cancelAnimationFrame(raf);
      stream?.getTracks().forEach((t) => t.stop());
      void ctx?.close();
    };
  }, []);

  return { levelRef, status };
}
