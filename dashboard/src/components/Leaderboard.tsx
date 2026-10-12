import { useState } from "react";
import type { RecentMedia, Snapshot, TopMedia } from "../types";
import { fmtCompact, fmtDay, fmtInt, fmtMediaType, msToSec, saveRate } from "../lib/format";
import { ArchetypeTag, Eyebrow, ProvenanceTag, Reveal } from "./primitives";

/**
 * The board ranks posts by what can actually be measured today: likes + comments, pulled
 * live. The old board ranked by views from a June snapshot and never changed, so a reel
 * posted in August could not appear on it at all.
 *
 * The all-time views board still exists — it holds the account's real record holders —
 * but it is labelled with the date it froze on instead of sitting under a live header.
 */

type Board = "recent" | "alltime";

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

function Arrow() {
  return (
    <span className="w-9 h-9 rounded-full border border-line flex items-center justify-center text-ink-dim transition-transform duration-500 ease-spring group-hover:translate-x-0.5 group-hover:-translate-y-0.5 group-hover:border-red group-hover:text-red">
      <svg width="13" height="13" viewBox="0 0 16 16" fill="none" aria-hidden>
        <path d="M4 12L12 4M12 4H6M12 4V10" stroke="currentColor" strokeWidth="1.5" />
      </svg>
    </span>
  );
}

function Rank({ n, highlight }: { n: number; highlight: boolean }) {
  return (
    <div
      className="font-display text-3xl sm:text-4xl leading-none"
      style={{ color: highlight ? "#C49040" : "#3A3A42" }}
    >
      {String(n).padStart(2, "0")}
    </div>
  );
}

/** A live post: thumbnail, hook, likes, comments. Everything here was fetched this pull. */
function LiveRow({ post, rank, i }: { post: RecentMedia; rank: number; i: number }) {
  const isTop = rank === 1;
  return (
    <Reveal i={i}>
      <a
        href={post.permalink ?? "#"}
        target="_blank"
        rel="noreferrer"
        className="group grid grid-cols-[2rem_1fr] sm:grid-cols-[2.5rem_auto_1fr_auto] gap-4 sm:gap-6 items-center px-5 sm:px-7 py-4 transition-colors duration-500 ease-spring hover:bg-panel2 focus-visible:outline-none focus-visible:bg-panel2"
        style={isTop ? { boxShadow: "inset 3px 0 0 #C49040" } : undefined}
      >
        <Rank n={rank} highlight={isTop} />

        {/* The thumbnail is the fastest way to recognise your own post. Reels have one; */}
        {/* feed images don't return thumbnail_url, so that slot stays a typed placeholder. */}
        <div className="hidden sm:block w-12 h-[68px] border border-line bg-panel2 overflow-hidden shrink-0">
          {post.thumbnail ? (
            <img
              src={post.thumbnail}
              alt=""
              loading="lazy"
              className="w-full h-full object-cover opacity-85 group-hover:opacity-100 transition-opacity"
            />
          ) : (
            <span className="w-full h-full flex items-center justify-center font-mono text-[8px] uppercase tracking-[0.12em] text-muted">
              {fmtMediaType(post.type)}
            </span>
          )}
        </div>

        <div className="min-w-0">
          <div className="flex items-center gap-2 mb-1.5 flex-wrap">
            <span
              className="font-mono text-[9px] uppercase tracking-[0.18em] px-1.5 py-0.5 border"
              style={
                post.type === "REELS"
                  ? { color: "#C82020", borderColor: "rgba(200,32,32,0.45)" }
                  : { color: "#A8A7A3", borderColor: "#26262C" }
              }
            >
              {fmtMediaType(post.type)}
            </span>
            {isTop && (
              <span className="font-mono text-[9px] uppercase tracking-[0.18em] text-gold">
                ★ Top
              </span>
            )}
            <span className="font-mono text-[10px] text-muted">
              {post.date ? fmtDay(post.date) : "undated"}
            </span>
          </div>
          <p className="text-ink text-[15px] sm:text-[16px] leading-snug truncate group-hover:text-white transition-colors">
            {post.hook}
          </p>
          <div className="mt-2 flex items-center gap-4 sm:hidden telemetry text-[12px] text-ink-dim">
            <span className="text-red">{fmtInt(post.likes)} likes</span>
            <span>{fmtInt(post.comments)} comments</span>
          </div>
        </div>

        <div className="hidden sm:flex items-center gap-7">
          <Metric label="Likes" value={fmtInt(post.likes)} accent="#E03030" />
          <Metric label="Comments" value={fmtInt(post.comments)} accent="#C49040" />
          <Metric label="Total" value={fmtCompact(post.engagement)} />
          <Arrow />
        </div>
      </a>
    </Reveal>
  );
}

/** An all-time record, with the insights metrics that are no longer being refreshed. */
function ArchiveRow({ reel, rank, i }: { reel: TopMedia; rank: number; i: number }) {
  const isRecord = rank === 1;
  return (
    <Reveal i={i}>
      <a
        href={reel.permalink}
        target="_blank"
        rel="noreferrer"
        className="group grid grid-cols-[2rem_1fr] sm:grid-cols-[2.5rem_1fr_auto] gap-4 sm:gap-7 items-center px-5 sm:px-7 py-5 transition-colors duration-500 ease-spring hover:bg-panel2 focus-visible:outline-none focus-visible:bg-panel2"
        style={isRecord ? { boxShadow: "inset 3px 0 0 #C49040" } : undefined}
      >
        <Rank n={rank} highlight={isRecord} />
        <div className="min-w-0">
          <div className="flex items-center gap-2 mb-1.5 flex-wrap">
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
        <div className="hidden sm:flex items-center gap-7">
          <Metric label="Views" value={fmtCompact(reel.views)} accent="#E03030" />
          <Metric label="Reach" value={fmtCompact(reel.reach)} />
          <Metric label="Saves" value={fmtInt(reel.saved)} accent="#C49040" />
          <Metric label="Shares" value={fmtInt(reel.shares)} />
          <Metric label="Watch" value={msToSec(reel.avg_watch_ms)} />
          <Metric label="Save%" value={saveRate(reel.saved, reel.reach)} />
          <Arrow />
        </div>
      </a>
    </Reveal>
  );
}

export function Leaderboard({ data }: { data: Snapshot }) {
  const recent = data.recent_media ?? [];
  const alltime = data.top_media_by_views ?? [];
  const hasRecent = recent.length > 0;

  const [board, setBoard] = useState<Board>(hasRecent ? "recent" : "alltime");
  const [showAll, setShowAll] = useState(false);

  const ranked = [...recent].sort((a, b) => b.engagement - a.engagement);
  const shown = showAll ? ranked : ranked.slice(0, 10);
  const archiveRanked = [...alltime].sort((a, b) => b.views - a.views);

  return (
    <section className="mx-auto max-w-[1320px] px-5 sm:px-8 mt-5 mb-16">
      <Reveal i={0} className="flex items-end justify-between px-1 mb-3 gap-4 flex-wrap">
        <div>
          <div className="flex items-center gap-3">
            <Eyebrow>Tale of the Tape</Eyebrow>
            {board === "recent" ? (
              <ProvenanceTag kind="live" />
            ) : (
              <ProvenanceTag kind="carried" detail={data.carried_from ?? undefined} />
            )}
          </div>
          <h2 className="font-display text-5xl sm:text-6xl text-ink leading-none mt-2">
            {board === "recent" ? "BY ENGAGEMENT" : "ALL-TIME VIEWS"}
          </h2>
        </div>

        <div className="flex border border-line">
          {(
            [
              ["recent", "Recent"],
              ["alltime", "All-time"],
            ] as [Board, string][]
          ).map(([v, label]) => {
            const enabled = v === "recent" ? hasRecent : archiveRanked.length > 0;
            return (
              <button
                key={v}
                onClick={() => setBoard(v)}
                disabled={!enabled}
                className={`px-3 py-1.5 font-mono text-[10px] uppercase tracking-[0.16em] transition-colors disabled:opacity-30 focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-red ${
                  board === v ? "bg-panel2 text-gold" : "text-muted hover:text-ink"
                }`}
              >
                {label}
              </button>
            );
          })}
        </div>
      </Reveal>

      {board === "alltime" && (
        <p className="px-1 mb-3 font-mono text-[11px] text-gold leading-relaxed max-w-[70ch]">
          Record holders as of {data.carried_from ?? "an earlier pull"}. Views, saves, shares and
          watch time stopped updating when the insights scope lapsed — nothing posted since then can
          appear here.
        </p>
      )}

      <div className="frame divide-y divide-line">
        {board === "recent"
          ? shown.map((p, idx) => <LiveRow key={p.id} post={p} rank={idx + 1} i={idx} />)
          : archiveRanked.map((r, idx) => (
              <ArchiveRow key={r.permalink} reel={r} rank={idx + 1} i={idx} />
            ))}
      </div>

      {board === "recent" && ranked.length > 10 && (
        <button
          onClick={() => setShowAll((v) => !v)}
          className="mt-3 w-full border border-line py-2.5 font-mono text-[10px] uppercase tracking-[0.18em] text-muted transition-colors hover:border-red hover:text-red focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-red"
        >
          {showAll ? "Show top 10" : `Show all ${ranked.length} posts`}
        </button>
      )}
    </section>
  );
}
