import type { Snapshot } from "../types";
import { fmtCompact, fmtDay, fmtInt } from "../lib/format";
import { Reveal } from "./primitives";

function Stat({
  label,
  value,
  sub,
  accent,
  i,
}: {
  label: string;
  value: string;
  sub?: string;
  accent?: string;
  i: number;
}) {
  return (
    <Reveal i={i} className="px-5 sm:px-7 py-6">
      <div className="eyebrow">{label}</div>
      <div
        className="telemetry mt-3 text-4xl sm:text-5xl leading-none"
        style={{ color: accent ?? "#F0EFED" }}
      >
        {value}
      </div>
      {sub && <div className="telemetry mt-2 text-[12px] text-muted">{sub}</div>}
    </Reveal>
  );
}

export function Telemetry({ data }: { data: Snapshot }) {
  const daily = data.daily_last_30d;
  const gained = daily.reduce((s, d) => s + d.new_followers, 0);
  const views = daily.reduce((s, d) => s + d.views, 0);
  const reach = daily.reduce((s, d) => s + d.reach, 0);
  const peak = daily.reduce((a, b) => (b.views > a.views ? b : a), daily[0]);

  return (
    <section className="mx-auto max-w-[1320px] px-5 sm:px-8 -mt-2">
      <div className="frame grid grid-cols-2 lg:grid-cols-4 divide-x divide-y lg:divide-y-0 divide-line">
        <Stat
          i={0}
          label="Followers"
          value={fmtInt(data.profile.followers_count)}
          sub={`+${gained} in window`}
          accent="#F0EFED"
        />
        <Stat
          i={1}
          label="Views · 30d"
          value={fmtCompact(views)}
          sub={`${fmtCompact(reach)} reach`}
          accent="#C82020"
        />
        <Stat
          i={2}
          label="Peak day"
          value={fmtCompact(peak.views)}
          sub={`${fmtDay(peak.date)} · views`}
          accent="#C49040"
        />
        <Stat
          i={3}
          label="Posts"
          value={fmtInt(data.profile.media_count)}
          sub={`following ${fmtInt(data.profile.follows_count)}`}
        />
      </div>
    </section>
  );
}
