import { useState } from "react";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { Snapshot } from "../types";
import { fmtCompact, fmtDay, fmtInt, fmtMediaType } from "../lib/format";
import { Eyebrow, ProvenanceTag, Reveal } from "./primitives";

/**
 * Two series, and the difference between them is the point.
 *
 * LIVE is engagement per post, built from /media — real, fetched on the last pull, and
 * the only time series this token can produce. ARCHIVE is the old reach/views chart,
 * which is genuine data but frozen on the day the insights scope lapsed. It used to be
 * the default view with no date on it, which is how a June chart spent the summer
 * looking like this week's performance.
 */

type View = "live" | "archive";

function LiveTooltip({ active, payload }: any) {
  if (!active || !payload?.length) return null;
  const row = payload[0]?.payload;
  return (
    <div className="frame !bg-panel2 px-3 py-2 font-mono text-[11px] max-w-[280px]">
      <div className="text-muted mb-1">
        {row.date ? fmtDay(row.date) : "undated"} · {fmtMediaType(row.type)}
      </div>
      <div className="text-ink mb-1.5 whitespace-normal leading-snug">{row.hook}</div>
      <div className="text-red">{fmtInt(row.likes)} likes</div>
      <div className="text-gold">{fmtInt(row.comments)} comments</div>
    </div>
  );
}

function ArchiveTooltip({ active, payload, label }: any) {
  if (!active || !payload?.length) return null;
  const row = payload[0]?.payload;
  return (
    <div className="frame !bg-panel2 px-3 py-2 font-mono text-[11px]">
      <div className="text-ink mb-1">{fmtDay(label)}</div>
      <div className="text-red">views {fmtInt(row.views)}</div>
      <div className="text-gold">reach {fmtInt(row.reach)}</div>
      <div className="text-green">+{row.new_followers} followers</div>
    </div>
  );
}

const axisTick = { fill: "#6C6C73", fontSize: 10, fontFamily: "JetBrains Mono" };

export function SurgeChart({ data }: { data: Snapshot }) {
  const recent = data.recent_media ?? [];
  const hasLive = recent.length > 0;
  const archive = data.daily_last_30d ?? [];
  const hasArchive = archive.length > 0;

  const [view, setView] = useState<View>(hasLive ? "live" : "archive");

  // Oldest to newest, capped so the bars stay readable on a laptop.
  const liveSeries = [...recent]
    .filter((m) => m.date)
    .sort((a, b) => (a.date! < b.date! ? -1 : 1))
    .slice(-24);

  const peakLive = liveSeries.reduce((m, r) => Math.max(m, r.engagement), 0);
  const peakArchive = archive.reduce((m, r) => Math.max(m, r.views), 0);

  return (
    <section className="mx-auto max-w-[1320px] px-5 sm:px-8 mt-5">
      <Reveal i={0} className="frame relative overflow-hidden">
        <div className="pointer-events-none absolute inset-x-0 top-0 h-px bg-red/40 animate-scan" />

        <div className="flex items-end justify-between gap-4 px-5 sm:px-7 pt-6 flex-wrap">
          <div>
            <div className="flex items-center gap-3">
              <Eyebrow>
                {view === "live" ? "Engagement per post" : "Reach & views · daily"}
              </Eyebrow>
              {view === "live" ? (
                <ProvenanceTag kind="live" />
              ) : (
                <ProvenanceTag kind="carried" detail={data.carried_from ?? undefined} />
              )}
            </div>
            <h2 className="font-display text-5xl sm:text-6xl text-ink leading-none mt-2">
              {view === "live" ? "THE WORK" : "THE SPIKE"}
            </h2>
          </div>

          <div className="flex items-center gap-5">
            <div className="text-right hidden sm:block">
              <div className="telemetry text-2xl text-red leading-none">
                {fmtCompact(view === "live" ? peakLive : peakArchive)}
              </div>
              <div className="eyebrow mt-1">
                {view === "live" ? "best post" : "peak views / day"}
              </div>
            </div>
            <div className="flex border border-line">
              {(["live", "archive"] as View[]).map((v) => {
                const enabled = v === "live" ? hasLive : hasArchive;
                return (
                  <button
                    key={v}
                    onClick={() => setView(v)}
                    disabled={!enabled}
                    className={`px-3 py-1.5 font-mono text-[10px] uppercase tracking-[0.16em] transition-colors disabled:opacity-30 focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-red ${
                      view === v ? "bg-panel2 text-gold" : "text-muted hover:text-ink"
                    }`}
                  >
                    {v}
                  </button>
                );
              })}
            </div>
          </div>
        </div>

        {view === "archive" && (
          <p className="px-5 sm:px-7 mt-3 font-mono text-[11px] text-gold leading-relaxed max-w-[70ch]">
            Frozen on {data.carried_from ?? "an earlier pull"}. Reach and views need the
            instagram_manage_insights scope, which this token doesn't hold — so this chart stops
            where the scope did. It is not this week.
          </p>
        )}

        <div className="h-[280px] sm:h-[340px] mt-4 px-1 pb-3">
          <ResponsiveContainer width="100%" height="100%">
            {view === "live" ? (
              <BarChart data={liveSeries} margin={{ top: 8, right: 18, left: 8, bottom: 4 }}>
                <CartesianGrid stroke="#1C1C21" vertical={false} />
                <XAxis
                  dataKey="date"
                  tickFormatter={(d) => (d ? fmtDay(d as string) : "")}
                  tick={axisTick}
                  axisLine={{ stroke: "#26262C" }}
                  tickLine={false}
                  minTickGap={20}
                />
                <YAxis
                  tickFormatter={(v) => fmtCompact(v as number)}
                  tick={axisTick}
                  axisLine={false}
                  tickLine={false}
                  width={42}
                />
                <Tooltip content={<LiveTooltip />} cursor={{ fill: "rgba(255,255,255,0.03)" }} />
                <Bar dataKey="engagement" animationDuration={900} animationEasing="ease-out">
                  {liveSeries.map((m) => (
                    // Reels and feed posts behave differently on this account, so the
                    // chart distinguishes them rather than averaging them into one story.
                    <Cell key={m.id} fill={m.type === "REELS" ? "#C82020" : "#3A3A42"} />
                  ))}
                </Bar>
              </BarChart>
            ) : (
              <AreaChart data={archive} margin={{ top: 8, right: 18, left: 8, bottom: 4 }}>
                <defs>
                  <linearGradient id="vFill" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#C82020" stopOpacity={0.55} />
                    <stop offset="100%" stopColor="#C82020" stopOpacity={0.02} />
                  </linearGradient>
                  <linearGradient id="rFill" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#C49040" stopOpacity={0.28} />
                    <stop offset="100%" stopColor="#C49040" stopOpacity={0.02} />
                  </linearGradient>
                </defs>
                <CartesianGrid stroke="#1C1C21" vertical={false} />
                <XAxis
                  dataKey="date"
                  tickFormatter={fmtDay}
                  tick={axisTick}
                  axisLine={{ stroke: "#26262C" }}
                  tickLine={false}
                  minTickGap={24}
                />
                <YAxis
                  tickFormatter={(v) => fmtCompact(v as number)}
                  tick={axisTick}
                  axisLine={false}
                  tickLine={false}
                  width={42}
                />
                <Tooltip content={<ArchiveTooltip />} cursor={{ stroke: "#3A3A42" }} />
                <Area
                  type="monotone"
                  dataKey="reach"
                  stroke="#C49040"
                  strokeWidth={1.5}
                  fill="url(#rFill)"
                  animationDuration={1100}
                />
                <Area
                  type="monotone"
                  dataKey="views"
                  stroke="#E03030"
                  strokeWidth={2}
                  fill="url(#vFill)"
                  animationDuration={1300}
                />
              </AreaChart>
            )}
          </ResponsiveContainer>
        </div>

        {view === "live" && (
          <div className="px-5 sm:px-7 pb-5 flex items-center gap-5 font-mono text-[10px] uppercase tracking-[0.16em] text-muted">
            <span className="flex items-center gap-2">
              <span className="inline-block w-2.5 h-2.5" style={{ background: "#C82020" }} />
              Reel
            </span>
            <span className="flex items-center gap-2">
              <span className="inline-block w-2.5 h-2.5" style={{ background: "#3A3A42" }} />
              Feed post
            </span>
            <span className="normal-case tracking-normal text-[11px]">
              likes + comments · reach and views need the insights scope
            </span>
          </div>
        )}
      </Reveal>
    </section>
  );
}
