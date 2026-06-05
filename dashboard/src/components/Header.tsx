import type { Snapshot } from "../types";
import { Eyebrow, PulseDot, Reveal } from "./primitives";

export function Header({ data }: { data: Snapshot }) {
  return (
    <header className="border-b border-line">
      {/* top status rail */}
      <div className="mx-auto max-w-[1320px] px-5 sm:px-8 py-3 flex items-center justify-between text-[11px] font-mono text-muted">
        <span className="flex items-center gap-2">
          <PulseDot color="#C82020" />
          FIGHT INTELLIGENCE
        </span>
        <span className="hidden sm:inline tracking-wide">
          SRC: WINDSOR // {data.account.windsor_account}
        </span>
        <span>PULLED {data.pulled_at}</span>
      </div>

      <div className="mx-auto max-w-[1320px] px-5 sm:px-8 pt-8 pb-10">
        <Reveal i={0}>
          <Eyebrow>Instagram Operating System</Eyebrow>
        </Reveal>

        <Reveal i={1} className="mt-3 flex items-end justify-between gap-6 flex-wrap">
          <h1 className="font-display leading-[0.82] text-ink text-[19vw] sm:text-[140px] tracking-[0.01em]">
            @MATTEOFIGHTS
          </h1>
        </Reveal>

        <Reveal i={2}>
          <p className="mt-4 max-w-[60ch] text-ink-dim text-[15px] leading-relaxed whitespace-pre-line">
            {data.profile.biography}
          </p>
        </Reveal>
      </div>
    </header>
  );
}
