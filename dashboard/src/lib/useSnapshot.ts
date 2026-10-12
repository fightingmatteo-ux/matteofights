import { useCallback, useEffect, useRef, useState } from "react";
import type { Snapshot } from "../types";

/** How often to re-check latest.json while the tab is visible. */
const POLL_MS = 30_000;
/** Older than this and the number on screen stops being presented as current. */
const STALE_AFTER_DAYS = 2;

export interface Freshness {
  /** Whole days between the snapshot's pulled_at and today. */
  ageDays: number | null;
  /** True when the data is too old to be shown as a live figure. */
  stale: boolean;
  /** epoch ms of the last completed check — not of the data itself. */
  lastCheckedAt: number;
  /** A refresh is in flight (the previous good data stays on screen meanwhile). */
  refreshing: boolean;
  /** Set when the most recent check failed or returned unusable data. */
  warning?: string;
}

type State =
  | { status: "loading" }
  | { status: "error"; message: string }
  | { status: "empty" }
  | { status: "ready"; data: Snapshot; meta: Freshness };

export interface SnapshotResult {
  state: State;
  /** Force an immediate re-check. */
  refresh: () => void;
}

/** Whole days between a YYYY-MM-DD snapshot date and today, in UTC. */
export function ageInDays(pulledAt: string | undefined, now = new Date()): number | null {
  if (!pulledAt) return null;
  const then = new Date(`${pulledAt}T00:00:00Z`);
  if (Number.isNaN(then.getTime())) return null;
  const today = Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate());
  return Math.round((today - then.getTime()) / 86_400_000);
}

/**
 * Last line of defence in the browser. The authoritative gate is
 * scripts/snapshot-health.mjs, which stops a bad snapshot from ever becoming
 * latest.json — but if a zeroed payload does get served, showing the last known
 * good number beats rendering "0" as though the account had emptied out.
 */
function isUsable(json: unknown): json is Snapshot {
  if (!json || typeof json !== "object") return false;
  const profile = (json as Snapshot).profile;
  if (!profile || typeof profile !== "object") return false;
  const n = profile.followers_count;
  return typeof n === "number" && Number.isFinite(n) && n > 0;
}

/**
 * Loads the latest snapshot synced into public/data by scripts/sync-data.mjs, then keeps
 * it current: polls while the tab is visible, and re-checks immediately on focus or when
 * the network comes back. Vite re-runs the sync whenever a new snapshot is written, so a
 * fresh pull reaches the screen without a reload.
 */
export function useSnapshot(): SnapshotResult {
  const [state, setState] = useState<State>({ status: "loading" });
  // Read inside the fetch without making it a dependency, so the poll isn't torn
  // down and rebuilt on every successful check.
  const stateRef = useRef(state);
  stateRef.current = state;
  const inFlight = useRef(false);

  const check = useCallback(async (signal?: AbortSignal) => {
    if (inFlight.current) return;
    inFlight.current = true;

    const prev = stateRef.current;
    if (prev.status === "ready") {
      setState({ ...prev, meta: { ...prev.meta, refreshing: true } });
    }

    const settle = (next: State) => {
      if (!signal?.aborted) setState(next);
    };
    /** Keep showing good data; just record why the check didn't help. */
    const keepPrevious = (warning: string) => {
      if (prev.status === "ready") {
        settle({
          ...prev,
          meta: { ...prev.meta, refreshing: false, lastCheckedAt: Date.now(), warning },
        });
        return true;
      }
      return false;
    };

    try {
      const r = await fetch(`data/latest.json?t=${Date.now()}`, { signal, cache: "no-store" });
      if (r.status === 404) {
        if (!keepPrevious("latest.json is missing")) settle({ status: "empty" });
        return;
      }
      if (!r.ok) throw new Error(`HTTP ${r.status}`);

      const json: unknown = await r.json();
      if (!isUsable(json)) {
        if (!keepPrevious("the served snapshot had no usable follower count — ignored")) {
          settle({ status: "empty" });
        }
        return;
      }

      settle({
        status: "ready",
        data: json,
        meta: {
          ageDays: ageInDays(json.pulled_at),
          stale: (ageInDays(json.pulled_at) ?? Infinity) > STALE_AFTER_DAYS,
          lastCheckedAt: Date.now(),
          refreshing: false,
        },
      });
    } catch (e: unknown) {
      if (signal?.aborted) return;
      const message = e instanceof Error ? e.message : "Unknown error";
      if (!keepPrevious(message)) settle({ status: "error", message });
    } finally {
      inFlight.current = false;
    }
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    void check(controller.signal);

    let timer: number | undefined;
    const start = () => {
      stop();
      timer = window.setInterval(() => void check(controller.signal), POLL_MS);
    };
    const stop = () => {
      if (timer !== undefined) window.clearInterval(timer);
      timer = undefined;
    };

    // Don't poll a hidden tab; check once the moment it comes back.
    const onVisibility = () => {
      if (document.hidden) {
        stop();
      } else {
        void check(controller.signal);
        start();
      }
    };
    const onOnline = () => void check(controller.signal);

    if (!document.hidden) start();
    document.addEventListener("visibilitychange", onVisibility);
    window.addEventListener("focus", onOnline);
    window.addEventListener("online", onOnline);

    return () => {
      controller.abort();
      stop();
      document.removeEventListener("visibilitychange", onVisibility);
      window.removeEventListener("focus", onOnline);
      window.removeEventListener("online", onOnline);
    };
  }, [check]);

  const refresh = useCallback(() => void check(), [check]);
  return { state, refresh };
}
