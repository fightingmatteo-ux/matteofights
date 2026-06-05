import { Eyebrow } from "./primitives";

function Shell({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-[100dvh] flex items-center justify-center px-6">
      <div className="frame max-w-md w-full p-8 text-center">{children}</div>
    </div>
  );
}

function Bar({ w, h = "h-4" }: { w: string; h?: string }) {
  return (
    <div className={`relative overflow-hidden bg-panel2 ${h} ${w}`}>
      <div className="absolute inset-0 -translate-x-full animate-shimmer bg-gradient-to-r from-transparent via-white/5 to-transparent" />
    </div>
  );
}

export function LoadingState() {
  return (
    <div className="min-h-[100dvh]">
      <div className="mx-auto max-w-[1320px] px-5 sm:px-8 pt-12 space-y-4">
        <Bar w="w-40" h="h-3" />
        <Bar w="w-[60%]" h="h-20" />
        <Bar w="w-[40%]" h="h-3" />
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-px frame mt-8">
          {[0, 1, 2, 3].map((k) => (
            <div key={k} className="p-6 space-y-3">
              <Bar w="w-20" h="h-3" />
              <Bar w="w-24" h="h-9" />
            </div>
          ))}
        </div>
        <div className="frame mt-5 p-7">
          <Bar w="w-32" h="h-10" />
          <div className="mt-6">
            <Bar w="w-full" h="h-[260px]" />
          </div>
        </div>
      </div>
    </div>
  );
}

export function ErrorState({ message }: { message: string }) {
  return (
    <Shell>
      <Eyebrow>Signal lost</Eyebrow>
      <h2 className="font-display text-5xl text-red mt-3 leading-none">NO FEED</h2>
      <p className="text-ink-dim text-sm mt-4 font-mono">{message}</p>
      <p className="text-muted text-[13px] mt-4">
        The dashboard reads <span className="font-mono text-ink-dim">public/data/latest.json</span>.
        Run <span className="font-mono text-ink-dim">npm run sync-data</span> after a fresh Windsor pull.
      </p>
    </Shell>
  );
}

export function EmptyState() {
  return (
    <Shell>
      <Eyebrow>Awaiting first pull</Eyebrow>
      <h2 className="font-display text-5xl text-ink mt-3 leading-none">NO DATA YET</h2>
      <p className="text-muted text-[13px] mt-4">
        Drop a snapshot in{" "}
        <span className="font-mono text-ink-dim">analytics/snapshots/</span> and run{" "}
        <span className="font-mono text-ink-dim">npm run sync-data</span>.
      </p>
    </Shell>
  );
}
