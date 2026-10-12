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

/**
 * "12s" / "4m" / "3h" / "6d". Used for both "pulled 12s ago" and "next pull in 4m", so it
 * stays unit-only — the surrounding copy supplies the direction.
 */
export const fmtDuration = (ms: number | null): string => {
  if (ms === null || !Number.isFinite(ms)) return "—";
  const s = Math.max(0, Math.round(ms / 1000));
  if (s < 60) return `${s}s`;
  const m = Math.round(s / 60);
  if (m < 60) return `${m}m`;
  const h = Math.round(m / 60);
  if (h < 48) return `${h}h`;
  return `${Math.round(h / 24)}d`;
};

/** Engagement as a share of followers — the only rate this token can actually compute. */
export const engagementRate = (engagement: number, followers: number): string =>
  followers > 0 ? `${((engagement / followers) * 100).toFixed(1)}%` : "—";

/** REELS -> Reel, FEED -> Post, CAROUSEL_ALBUM -> Carousel. */
export const fmtMediaType = (type: string): string => {
  switch (type) {
    case "REELS":
    case "VIDEO":
      return "Reel";
    case "FEED":
    case "IMAGE":
      return "Post";
    case "CAROUSEL_ALBUM":
      return "Carousel";
    case "STORY":
      return "Story";
    default:
      return type.toLowerCase();
  }
};
