export const fmtInt = (n: number): string => n.toLocaleString("en-US");

export const fmtCompact = (n: number): string =>
  new Intl.NumberFormat("en-US", { notation: "compact", maximumFractionDigits: 1 }).format(n);

export const msToSec = (ms: number): string => `${(ms / 1000).toFixed(1)}s`;

/** "2026-06-01..." -> "Jun 1" */
export const fmtDay = (iso: string): string => {
  const d = new Date(iso);
  return d.toLocaleDateString("en-US", { month: "short", day: "numeric" });
};

/** Saves as a share of reach — the algorithmic signal that matters here. */
export const saveRate = (saved: number, reach: number): string =>
  reach > 0 ? `${((saved / reach) * 100).toFixed(1)}%` : "—";
