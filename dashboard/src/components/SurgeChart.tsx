import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { Snapshot } from "../types";
import { fmtCompact, fmtDay, fmtInt } from "../lib/format";
import { Eyebrow, Reveal } from "./primitives";

function ChartTooltip({ active, payload, label }: any) {
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

export function SurgeChart({ data }: { data: Snapshot }) {
  const series = data.daily_last_30d;

  return (
    <section className="mx-auto max-w-[1320px] px-5 sm:px-8 mt-5">
      <Reveal i={0} className="frame relative overflow-hidden">
        {/* scan-line accent */}
        <div className="pointer-events-none absolute inset-x-0 top-0 h-px bg-red/40 animate-scan" />

        <div className="flex items-baseline justify-between gap-4 px-5 sm:px-7 pt-6">
          <div>
            <Eyebrow>Reach &amp; Views · last 30 days</Eyebrow>
            <h2 className="font-display text-5xl sm:text-6xl text-ink leading-none mt-2">
              THE SPIKE
            </h2>
          </div>
          <div className="text-right hidden sm:block">
            <div className="telemetry text-2xl text-red leading-none">
              {fmtCompact(Math.max(...series.map((d) => d.views)))}
            </div>
            <div className="eyebrow mt-1">peak views / day</div>
          </div>
        </div>

        <div className="h-[280px] sm:h-[340px] mt-4 px-1 pb-3">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={series} margin={{ top: 8, right: 18, left: 8, bottom: 4 }}>
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
                tick={{ fill: "#6C6C73", fontSize: 10, fontFamily: "JetBrains Mono" }}
                axisLine={{ stroke: "#26262C" }}
                tickLine={false}
                minTickGap={24}
              />
              <YAxis
                tickFormatter={(v) => fmtCompact(v as number)}
                tick={{ fill: "#6C6C73", fontSize: 10, fontFamily: "JetBrains Mono" }}
                axisLine={false}
                tickLine={false}
                width={42}
              />
              <Tooltip content={<ChartTooltip />} cursor={{ stroke: "#3A3A42" }} />
              <Area
                type="monotone"
                dataKey="reach"
                stroke="#C49040"
                strokeWidth={1.5}
                fill="url(#rFill)"
                animationDuration={1100}
                animationEasing="ease-out"
              />
              <Area
                type="monotone"
                dataKey="views"
                stroke="#E03030"
                strokeWidth={2}
                fill="url(#vFill)"
                animationDuration={1300}
                animationEasing="ease-out"
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </Reveal>
    </section>
  );
}
