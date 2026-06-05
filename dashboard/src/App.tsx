import { useSnapshot } from "./lib/useSnapshot";
import { Grain } from "./components/primitives";
import { Header } from "./components/Header";
import { Telemetry } from "./components/Telemetry";
import { SurgeChart } from "./components/SurgeChart";
import { Leaderboard } from "./components/Leaderboard";
import { EmptyState, ErrorState, LoadingState } from "./components/States";

export default function App() {
  const state = useSnapshot();

  return (
    <>
      <Grain />
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
  );
}
