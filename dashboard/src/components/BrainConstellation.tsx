import { useEffect, useRef } from "react";
import { BRAIN_NODES, type NodeId, type Phase } from "../lib/brainNodes";

const PHASE_COLOR: Record<Phase, string> = {
  idle: "#3E6E8C",
  listening: "#5E9E72",
  reading: "#C49040",
  thinking: "#C49040",
  drafting: "#C0392B",
  speaking: "#C0392B",
};

function hexToRgb(hex: string): string {
  const n = parseInt(hex.slice(1), 16);
  return `${(n >> 16) & 255},${(n >> 8) & 255},${n & 255}`;
}

/**
 * The living brain. One Canvas 2D rAF loop draws the node ring, tracer lines, ripples,
 * orbiting particles, and the CORE. Phase/activeNode come from React props (rare
 * changes); per-frame amplitude is read from refs (mic + TTS) to avoid re-render churn.
 */
export function BrainConstellation({
  phase,
  activeNode,
  micLevelRef,
  ttsLevelRef,
}: {
  phase: Phase;
  activeNode: NodeId | null;
  micLevelRef: React.MutableRefObject<number>;
  ttsLevelRef: React.MutableRefObject<number>;
}) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const phaseRef = useRef(phase);
  phaseRef.current = phase;
  const activeRef = useRef(activeNode);
  activeRef.current = activeNode;

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let raf = 0;
    let t = 0;
    const ripples: { r: number; a: number }[] = [];

    const resize = () => {
      const dpr = window.devicePixelRatio || 1;
      canvas.width = canvas.clientWidth * dpr;
      canvas.height = canvas.clientHeight * dpr;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    };
    resize();
    window.addEventListener("resize", resize);

    const draw = () => {
      t += 1;
      const w = canvas.clientWidth;
      const h = canvas.clientHeight;
      const cx = w / 2;
      const cy = h / 2;
      const R = Math.min(w, h) * 0.36;
      const N = BRAIN_NODES.length;
      const color = PHASE_COLOR[phaseRef.current];
      const rgb = hexToRgb(color);

      ctx.clearRect(0, 0, w, h);

      const amp = Math.max(micLevelRef.current, ttsLevelRef.current);
      const breathe = 0.5 + 0.5 * Math.sin(t * 0.05);
      const coreBase = 16 + (phaseRef.current === "thinking" ? breathe * 7 : breathe * 2);
      const coreR = coreBase + amp * 26;

      ctx.font = "10px ui-monospace, monospace";
      ctx.textAlign = "center";

      BRAIN_NODES.forEach((node, i) => {
        const ang = (i / N) * Math.PI * 2 - Math.PI / 2;
        const nx = cx + Math.cos(ang) * R;
        const ny = cy + Math.sin(ang) * R;
        const active = activeRef.current === node.id;

        ctx.strokeStyle = active ? color : "rgba(168,167,163,0.10)";
        ctx.lineWidth = active ? 1.5 : 0.5;
        ctx.beginPath();
        ctx.moveTo(cx, cy);
        ctx.lineTo(nx, ny);
        ctx.stroke();

        ctx.beginPath();
        ctx.arc(nx, ny, active ? 6 : 2.5, 0, Math.PI * 2);
        ctx.fillStyle = active ? "#C0392B" : "rgba(168,167,163,0.5)";
        if (active) {
          ctx.shadowColor = "#C0392B";
          ctx.shadowBlur = 16;
        }
        ctx.fill();
        ctx.shadowBlur = 0;

        ctx.fillStyle = active ? "#EDEBE6" : "rgba(168,167,163,0.55)";
        ctx.fillText(node.label, cx + Math.cos(ang) * (R + 16), cy + Math.sin(ang) * (R + 16) + 3);
      });

      if (amp > 0.25 && t % 6 === 0) ripples.push({ r: coreR, a: 0.5 });
      for (let i = ripples.length - 1; i >= 0; i--) {
        const rp = ripples[i];
        rp.r += 2.5;
        rp.a *= 0.94;
        if (rp.a < 0.02) {
          ripples.splice(i, 1);
          continue;
        }
        ctx.beginPath();
        ctx.arc(cx, cy, rp.r, 0, Math.PI * 2);
        ctx.strokeStyle = `rgba(${rgb},${rp.a})`;
        ctx.lineWidth = 1;
        ctx.stroke();
      }

      if (phaseRef.current === "thinking") {
        for (let i = 0; i < 6; i++) {
          const a = t * 0.03 + (i / 6) * Math.PI * 2;
          const pr = coreR + 14 + Math.sin(t * 0.08 + i) * 4;
          ctx.beginPath();
          ctx.arc(cx + Math.cos(a) * pr, cy + Math.sin(a) * pr, 1.6, 0, Math.PI * 2);
          ctx.fillStyle = color;
          ctx.fill();
        }
      }

      const grad = ctx.createRadialGradient(cx, cy, 0, cx, cy, coreR);
      grad.addColorStop(0, color);
      grad.addColorStop(1, `rgba(${rgb},0.05)`);
      ctx.beginPath();
      ctx.arc(cx, cy, coreR, 0, Math.PI * 2);
      ctx.fillStyle = grad;
      ctx.shadowColor = color;
      ctx.shadowBlur = 24;
      ctx.fill();
      ctx.shadowBlur = 0;

      raf = requestAnimationFrame(draw);
    };
    draw();

    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener("resize", resize);
    };
  }, [micLevelRef, ttsLevelRef]);

  return (
    <div className="relative w-full h-[300px] sm:h-[360px] mb-6">
      <canvas ref={canvasRef} className="w-full h-full" />
      <span className="absolute bottom-2 left-1/2 -translate-x-1/2 font-mono text-[10px] uppercase tracking-[0.2em] text-muted">
        {phase}
      </span>
    </div>
  );
}
