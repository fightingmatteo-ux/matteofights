// GET /api/taste: every revision Matteo has sent (D1 kind "request"), boiled down to what the edit worker should be
// learning from: which kinds of change he asks for, how many rounds a reel needs, and whether that falls week by week.
// The rules Claude has learned live in production/editing/taste.md (data.json "taste").
import { json, isOwner } from "../../lib/shared.js";
import { all } from "../../lib/db.js";

const week = (iso) => {
  const d = new Date(iso);
  d.setUTCDate(d.getUTCDate() - ((d.getUTCDay() + 6) % 7)); // Monday
  return d.toISOString().slice(0, 10);
};

export async function onRequestGet({ request, env }) {
  if (!(await isOwner(request, env))) return json({ error: "not allowed" }, 403);
  const reqs = (await all(env, "request")).filter((r) => r.at);
  const tags = {}, weeks = {}, reels = {};
  for (const r of reqs) {
    const notes = r.notes?.length ? r.notes : [{ tags: r.tags || [] }];
    for (const n of notes) for (const t of n.tags?.length ? n.tags : ["other"]) tags[t] = (tags[t] || 0) + 1;
    const w = (weeks[week(r.at)] ||= { week: week(r.at), revisions: 0, notes: 0, reels: new Set() });
    w.revisions += 1; w.notes += notes.length; w.reels.add(r.target);
    const x = (reels[r.target] ||= { target: r.target, rounds: 0, notes: 0, last: r.at, status: r.status });
    x.rounds += 1; x.notes += notes.length;
    if (r.at > x.last) { x.last = r.at; x.status = r.status; }
  }
  const W = Object.values(weeks).sort((a, b) => (a.week > b.week ? 1 : -1)).slice(-12)
    .map((w) => ({ week: w.week, revisions: w.revisions, notes: w.notes, reels: w.reels.size, rounds_per_reel: +(w.revisions / w.reels.size).toFixed(2) }));
  return json({
    at: new Date().toISOString(), total: reqs.length,
    notes: reqs.reduce((a, r) => a + (r.notes?.length || 1), 0),
    tags: Object.entries(tags).sort((a, b) => b[1] - a[1]).map(([tag, n]) => ({ tag, n })),
    weeks: W,
    reels: Object.values(reels).sort((a, b) => (a.last < b.last ? 1 : -1)).slice(0, 40),
  });
}
