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
