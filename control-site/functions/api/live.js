// GET /api/live: everything on the dashboard that changes during the day, straight from D1.
import { json, isOwner } from "../../lib/shared.js";
import { all, get } from "../../lib/db.js";

export async function onRequestGet({ request, env }) {
  if (!(await isOwner(request, env))) return json({ error: "not allowed" }, 403);
  const [queue, jobs, uploads, requests, tps, health] = await Promise.all([
    all(env, "queue"), all(env, "job"), all(env, "upload"), all(env, "request"), all(env, "talking_point"),
    get(env, "health", "latest"),
  ]);
  const since = new Date(Date.now() - 14 * 864e5).toISOString();
  const recent = (iso) => (iso || "") >= since;
  return json({
    at: new Date().toISOString(),
    queue: queue.filter((i) => i.status !== "posted" || recent(i.posted_at)),
    jobs: jobs.filter((j) => recent(j.submitted_at || j.updated_at)).slice(-30),
    uploads: uploads.filter((u) => u.status !== "done" || recent(u.at)),
    requests: requests.filter((r) => r.status !== "done" || recent(r.at)),
    talking_points: tps.filter((t) => t.status === "new"),
    health,
  });
}
