import type { Snapshot } from "../types";
import { Eyebrow, Reveal } from "./primitives";

/**
 * The masthead. Freshness used to live here as a hard-coded "LIVE" label; it now belongs
 * to StatusRail, which derives it from the backend's actual last pull. What's left is
 * identity and one honest note about what the dashboard currently cannot see.
 */

function InsightsLocked({ data }: { data: Snapshot }) {
  return (
    <div className="border-t border-line-soft bg-panel/30">
      <div className="mx-auto max-w-[1320px] px-5 sm:px-8 py-3 font-mono text-[11px] leading-relaxed text-muted">
        <span className="text-gold uppercase tracking-[0.16em]">Insights locked</span>
        <span className="mx-2 text-line">/</span>
        Reach, views, saves, shares and watch time need the{" "}
        <span className="text-ink-dim">instagram_manage_insights</span> permission. This token has{" "}
        <span className="text-ink-dim">instagram_basic</span>, so followers and per-post likes and
        comments stay live while those metrics show their last known values with a date on them.
        Re-authorise the Meta app with that scope and they refill on the next pull — no plan
        upgrade, no third-party tool.
      </div>
    </div>
  );
}

export function Header({ data }: { data: Snapshot }) {
  const insightsLocked = data.capabilities?.insights === false;

  return (
    <header className="border-b border-line">
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

      {insightsLocked && <InsightsLocked data={data} />}
    </header>
  );
}
