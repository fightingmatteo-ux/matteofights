import { useState } from "react";
import { useSnapshot } from "./lib/useSnapshot";
import { useLiveStatus } from "./lib/useLiveStatus";
import { Grain } from "./components/primitives";
import { StatusRail } from "./components/StatusRail";
import { Header } from "./components/Header";
import { Telemetry } from "./components/Telemetry";
import { SurgeChart } from "./components/SurgeChart";
import { Leaderboard } from "./components/Leaderboard";
import { Conversation } from "./components/Conversation";
import { PublishQueue } from "./components/PublishQueue";
import { EmptyState, ErrorState, LoadingState } from "./components/States";

type Tab = "dashboard" | "jarvis" | "queue";

export default function App() {
  const { state, refresh } = useSnapshot();
  // A manual pull finishes on the backend; `refresh` is what pulls the new file into view
  // immediately instead of waiting out the 30s poll.
  const live = useLiveStatus(refresh);
  const [tab, setTab] = useState<Tab>("dashboard");

  const source = state.status === "ready" ? state.data.source : "instagram graph api";
  // A queued reel is waiting on a decision only Matteo can make, so the tab carries the
  // count rather than making him go and look.
  const queued = live.status?.pendingPublishes ?? 0;

  return (
    <>
      <Grain />

      {/* The rail sits above the tabs on purpose: freshness applies to the whole app, and
          it is the first thing to check before trusting anything below it. */}
      <StatusRail live={live} source={source} />

      <nav className="mx-auto max-w-[1320px] px-5 sm:px-8 pt-6 flex gap-7 border-b border-line">
        {(["dashboard", "jarvis", "queue"] as Tab[]).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`-mb-px pb-3 font-mono text-[13px] uppercase tracking-[0.22em] border-b-2 transition-colors focus-visible:outline-none focus-visible:text-gold ${
              tab === t ? "text-gold border-gold" : "text-muted border-transparent hover:text-ink"
            }`}
          >
            {t === "jarvis" ? "◆ Jarvis" : t}
            {t === "queue" && queued > 0 && (
              <span className="ml-2 px-1.5 py-0.5 bg-red text-white text-[10px] tracking-normal">
                {queued}
              </span>
            )}
          </button>
        ))}
      </nav>

      {tab === "jarvis" && <Conversation />}
      {tab === "queue" && <PublishQueue />}

      {tab === "dashboard" && (
        <>
          {state.status === "loading" && <LoadingState />}
          {state.status === "error" && <ErrorState message={state.message} />}
          {state.status === "empty" && <EmptyState />}
          {state.status === "ready" && (
            <main>
              <Header data={state.data} />
              <Telemetry data={state.data} />
              <SurgeChart data={state.data} />
              <Leaderboard data={state.data} />
              <footer className="border-t border-line">
                <div className="mx-auto max-w-[1320px] px-5 sm:px-8 py-6 flex items-center justify-between font-mono text-[11px] text-muted flex-wrap gap-2">
                  <span>@{state.data.account.username} · id {state.data.account.id}</span>
                  <span>
                    DM trigger:{" "}
                    <span className="text-gold">{state.data.profile.dm_trigger_current}</span> · north
                    star: grow the fighter brand
                  </span>
                </div>
              </footer>
            </main>
          )}
        </>
      )}
    </>
  );
}
