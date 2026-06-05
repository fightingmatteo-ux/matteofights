import { useEffect, useState } from "react";
import type { Snapshot } from "../types";

type State =
  | { status: "loading" }
  | { status: "error"; message: string }
  | { status: "empty" }
  | { status: "ready"; data: Snapshot };

/** Loads the latest snapshot synced into public/data by scripts/sync-data.mjs. */
export function useSnapshot(): State {
  const [state, setState] = useState<State>({ status: "loading" });

  useEffect(() => {
    let alive = true;
    fetch(`data/latest.json?t=${Date.now()}`)
      .then((r) => {
        if (r.status === 404) return null;
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json();
      })
      .then((json: Snapshot | null) => {
        if (!alive) return;
        if (!json || !json.profile) setState({ status: "empty" });
        else setState({ status: "ready", data: json });
      })
      .catch((e: unknown) => {
        if (!alive) return;
        setState({ status: "error", message: e instanceof Error ? e.message : "Unknown error" });
      });
    return () => {
      alive = false;
    };
  }, []);

  return state;
}
