import type { Snapshot } from "../types";
import { engagementRate, fmtCompact, fmtDay, fmtInt } from "../lib/format";
import { ProvenanceTag, Reveal } from "./primitives";
import type { Provenance } from "./primitives";

/**
 * Four tiles, and every one of them is a number this token can actually fetch today.
 *
 * The old set led with "Views · 30d" and "Peak day" — both from insights, both carried
 * from a June snapshot, both presented as current. They now live in the archive section
 * with a date on them. What's left here is live: follower count and movement, and
 * engagement derived from per-post likes and comments, which need no insights scope.
 */

function Stat({
  label,
  value,
  sub,
  accent,
  provenance,
  detail,
  i,
}: {
  label: string;
  value: string;
  sub?: string;
  accent?: string;
  provenance: Provenance;
  detail?: string;
  i: number;
}) {
  return (
    <Reveal i={i} className="px-5 sm:px-7 py-6">
      <div className="flex items-center justify-between gap-3">
        <span className="eyebrow">{label}</span>
        <ProvenanceTag kind={provenance} detail={detail} />
      </div>
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
  const followers = data.profile.followers_count;
  const delta = data.follower_delta ?? null;
  const eng = data.engagement_30d ?? null;
  const recent = data.recent_media ?? [];

  // Posting cadence, straight from the timestamps. Four posts in thirty days is a fact
  // worth putting on the wall next to the follower count.
  const perWeek = eng && eng.posts > 0 ? (eng.posts / 30) * 7 : 0;

  const best = recent.reduce<(typeof recent)[number] | null>(
    (a, b) => (a === null || b.engagement > a.engagement ? b : a),
    null
  );

  return (
    <section className="mx-auto max-w-[1320px] px-5 sm:px-8 mt-5">
      <div className="frame grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 divide-y sm:divide-y-0 sm:divide-x divide-line">
        <Stat
          i={0}
          label="Followers"
          value={fmtInt(followers)}
          sub={
            delta
              ? `${delta.value >= 0 ? "+" : ""}${fmtInt(delta.value)} since ${fmtDay(delta.since)}`
              : `following ${fmtInt(data.profile.follows_count)}`
          }
          provenance="live"
        />
        <Stat
          i={1}
          label="Engagement · 30d"
          value={eng ? fmtCompact(eng.total) : "—"}
          sub={
            eng
              ? `${fmtInt(eng.likes)} likes · ${fmtInt(eng.comments)} comments · ${engagementRate(eng.total, followers)} of audience`
              : "no post data"
          }
          accent="#C82020"
          provenance="live"
        />
        <Stat
          i={2}
          label="Output · 30d"
          value={eng ? String(eng.posts) : "—"}
          sub={eng ? `${perWeek.toFixed(1)} posts / week · ${fmtInt(data.profile.media_count)} all time` : undefined}
          accent="#C49040"
          provenance="live"
        />
        <Stat
          i={3}
          label="Best recent post"
          value={best ? fmtCompact(best.engagement) : "—"}
          sub={best?.date ? `${fmtDay(best.date)} · engagement` : undefined}
          provenance="live"
        />
      </div>
    </section>
  );
}
