import type { CSSProperties, ReactNode } from "react";

/** Fixed film-grain overlay. Pointer-events none, never on scrolling content. */
export function Grain() {
  return <div className="grain" aria-hidden />;
}

/** Staggered load-in wrapper. `i` drives a cascade via animation-delay. */
export function Reveal({
  i = 0,
  className = "",
  children,
}: {
  i?: number;
  className?: string;
  children: ReactNode;
}) {
  const style = { "--d": `${i * 90}ms` } as CSSProperties;
  return (
    <div className={`rise ${className}`} style={style}>
      {children}
    </div>
  );
}

export function Eyebrow({ children }: { children: ReactNode }) {
  return <span className="eyebrow">{children}</span>;
}

/** Breathing live indicator. */
export function PulseDot({ color = "#5E9E72" }: { color?: string }) {
  return (
    <span className="relative inline-flex h-2 w-2">
      <span
        className="absolute inline-flex h-full w-full animate-pulseDot rounded-full"
        style={{ background: color }}
      />
    </span>
  );
}

/** Archetype tag — TACTICAL (saves) vs IDENTITY (shares). */
export function ArchetypeTag({ archetype }: { archetype: string }) {
  const isIdentity = archetype === "identity";
  return (
    <span
      className="font-mono text-[9px] uppercase tracking-[0.18em] px-1.5 py-0.5 border"
      style={{
        color: isIdentity ? "#C49040" : "#A8A7A3",
        borderColor: isIdentity ? "rgba(196,144,64,0.4)" : "#26262C",
      }}
    >
      {isIdentity ? "Identity" : "Tactical"}
    </span>
  );
}

/**
 * Where a number came from. This is the one piece of chrome the dashboard genuinely
 * needed: for 74 days it displayed June's figures under a "LIVE" banner, which is worse
 * than displaying nothing. Every number now carries its own provenance.
 *
 *   live    — fetched on the last pull
 *   carried — real, but from an older snapshot; the date is part of the label
 *   locked  — this token cannot see it at all
 */
export type Provenance = "live" | "carried" | "locked";

const PROVENANCE_STYLE: Record<Provenance, { color: string; border: string; label: string }> = {
  live: { color: "#C82020", border: "rgba(200,32,32,0.45)", label: "Live" },
  carried: { color: "#C49040", border: "rgba(196,144,64,0.4)", label: "Carried" },
  locked: { color: "#6C6C73", border: "#26262C", label: "Locked" },
};

export function ProvenanceTag({ kind, detail }: { kind: Provenance; detail?: string }) {
  const s = PROVENANCE_STYLE[kind];
  return (
    <span
      className="inline-flex items-center gap-1.5 font-mono text-[9px] uppercase tracking-[0.16em] px-1.5 py-0.5 border"
      style={{ color: s.color, borderColor: s.border }}
      title={detail}
    >
      {kind === "live" && <PulseDot color={s.color} />}
      {s.label}
      {detail && <span className="text-muted normal-case tracking-normal">{detail}</span>}
    </span>
  );
}

/**
 * Countdown to the next automatic pull, drawn as a draining arc.
 * `fraction` is 1 just after a pull and 0 the moment the next one is due.
 */
export function CountdownRing({
  fraction,
  active,
  size = 16,
}: {
  fraction: number;
  active: boolean;
  size?: number;
}) {
  const r = (size - 3) / 2;
  const c = 2 * Math.PI * r;
  const clamped = Math.max(0, Math.min(1, fraction));
  return (
    <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} aria-hidden className="shrink-0">
      <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="#26262C" strokeWidth="1.5" />
      <circle
        cx={size / 2}
        cy={size / 2}
        r={r}
        fill="none"
        stroke={active ? "#C82020" : "#3A3A42"}
        strokeWidth="1.5"
        strokeDasharray={c}
        strokeDashoffset={c * (1 - clamped)}
        strokeLinecap="butt"
        transform={`rotate(-90 ${size / 2} ${size / 2})`}
        style={{ transition: "stroke-dashoffset 1s linear" }}
      />
    </svg>
  );
}
