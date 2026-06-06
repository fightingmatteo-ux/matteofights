import { useState } from "react";
import { useSnapshot } from "./lib/useSnapshot";
import { Grain } from "./components/primitives";
import { Header } from "./components/Header";
import { Telemetry } from "./components/Telemetry";
import { SurgeChart } from "./components/SurgeChart";
import { Leaderboard } from "./components/Leaderboard";
import { Conversation } from "./components/Conversation";
import { EmptyState, ErrorState, LoadingState } from "./components/States";

type Tab = "dashboard" | "jarvis";

export default function App() {
  const state = useSnapshot();
  const [tab, setTab] = useState<Tab>("dashboard");

  return (
    <>
      <Grain />
      <nav className="mx-auto max-w-[1320px] px-5 sm:px-8 pt-5 flex gap-4 font-mono text-[11px] uppercase tracking-[0.18em]">
        {(["dashboard", "jarvis"] as Tab[]).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={tab === t ? "text-gold" : "text-muted hover:text-fg"}
          >
            {t}
          </button>
        ))}
      </nav>

      {tab === "jarvis" && <Conversation />}

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
