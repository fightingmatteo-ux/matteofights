import type { Snapshot, TopMedia } from "../types";
import { fmtCompact, fmtDay, fmtInt, msToSec, saveRate } from "../lib/format";
import { ArchetypeTag, Eyebrow, Reveal } from "./primitives";

function Metric({ label, value, accent }: { label: string; value: string; accent?: string }) {
  return (
    <div className="text-right">
      <div className="telemetry text-[15px] sm:text-base leading-none" style={{ color: accent }}>
        {value}
      </div>
      <div className="font-mono text-[9px] uppercase tracking-[0.14em] text-muted mt-1">
        {label}
      </div>
    </div>
  );
}

function Row({ reel, rank, i }: { reel: TopMedia; rank: number; i: number }) {
  const isRecord = rank === 1;
  return (
    <Reveal i={i}>
      <a
        href={reel.permalink}
        target="_blank"
        rel="noreferrer"
        className="group grid grid-cols-[2rem_1fr] sm:grid-cols-[2.5rem_1fr_auto] gap-4 sm:gap-7 items-center px-5 sm:px-7 py-5 transition-colors duration-500 ease-spring hover:bg-panel2"
        style={isRecord ? { boxShadow: "inset 3px 0 0 #C49040" } : undefined}
      >
        {/* rank */}
        <div
          className="font-display text-3xl sm:text-4xl leading-none"
          style={{ color: isRecord ? "#C49040" : "#3A3A42" }}
        >
          {String(rank).padStart(2, "0")}
        </div>

        {/* hook + meta */}
        <div className="min-w-0">
          <div className="flex items-center gap-2 mb-1.5">
            <ArchetypeTag archetype={reel.archetype} />
            {isRecord && (
              <span className="font-mono text-[9px] uppercase tracking-[0.18em] text-gold">
                ★ Record
              </span>
            )}
            <span className="font-mono text-[10px] text-muted">{fmtDay(reel.date)}</span>
          </div>
          <p className="text-ink text-[15px] sm:text-[16px] leading-snug truncate group-hover:text-white transition-colors">
            {reel.hook}
          </p>
          <div className="mt-2 flex items-center gap-4 sm:hidden telemetry text-[12px] text-ink-dim">
            <span className="text-red">{fmtCompact(reel.views)} views</span>
            <span>{fmtCompact(reel.saved)} saves</span>
            <span>{fmtCompact(reel.shares)} shares</span>
          </div>
        </div>

        {/* metrics (desktop) */}
        <div className="hidden sm:flex items-center gap-7">
          <Metric label="Views" value={fmtCompact(reel.views)} accent="#E03030" />
          <Metric label="Reach" value={fmtCompact(reel.reach)} />
          <Metric label="Saves" value={fmtInt(reel.saved)} accent="#C49040" />
          <Metric label="Shares" value={fmtInt(reel.shares)} />
          <Metric label="Watch" value={msToSec(reel.avg_watch_ms)} />
          <Metric label="Save%" value={saveRate(reel.saved, reel.reach)} />
          <span className="w-9 h-9 rounded-full border border-line flex items-center justify-center text-ink-dim transition-transform duration-500 ease-spring group-hover:translate-x-0.5 group-hover:-translate-y-0.5 group-hover:border-red group-hover:text-red">
            <svg width="13" height="13" viewBox="0 0 16 16" fill="none" aria-hidden>
              <path d="M4 12L12 4M12 4H6M12 4V10" stroke="currentColor" strokeWidth="1.5" />
            </svg>
          </span>
        </div>
      </a>
    </Reveal>
  );
}

export function Leaderboard({ data }: { data: Snapshot }) {
  const reels = [...data.top_media_by_views].sort((a, b) => b.views - a.views);

  return (
    <section className="mx-auto max-w-[1320px] px-5 sm:px-8 mt-5 mb-16">
      <Reveal i={0} className="flex items-baseline justify-between px-1 mb-3">
        <div>
          <Eyebrow>Tale of the Tape</Eyebrow>
          <h2 className="font-display text-5xl sm:text-6xl text-ink leading-none mt-2">
            TOP REELS
          </h2>
        </div>
        <span className="eyebrow hidden sm:flex">Tactical = saves · Identity = shares</span>
      </Reveal>

      <div className="frame divide-y divide-line">
        {reels.map((r, idx) => (
          <Row key={r.permalink} reel={r} rank={idx + 1} i={idx} />
        ))}
      </div>
    </section>
  );
}
