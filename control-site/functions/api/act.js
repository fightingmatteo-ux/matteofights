// POST /api/act from the dashboard.
//   decisions {action: "approve_week" | "answer" | "idea" | ...}  -> Control workflow (commits the decision)
//   studio    {action: "run", job: "...", ...}                    -> starts that job's workflow directly
import { accessEmail, dispatch, dispatchWorkflow, json } from "../../lib/shared.js";

const ACTIONS = new Set(["approve_week", "approve_threads", "threads_skip", "threads_edit", "answer", "idea", "run"]);
const SLUG = /^[a-z0-9][a-z0-9._-]{2,80}$/;
const VARIANTS = /^[A-Z](,[A-Z]){0,5}$/;
const FOOTAGE = /^[^/\\]{1,200}$/;

// job -> [workflow file, inputs from the body], or an error string. Nothing here can post: posting stays behind
// the approve actions and the Post queue workflow.
const JOBS = {
  refresh_stats: () => ["platform-stats.yml", {}],
  make_listicles: (b) => {
    const count = Number(b.count || 7);
    return Number.isInteger(count) && count >= 1 && count <= 14 ? ["listicle-factory.yml", { count: String(count) }] : "count must be 1-14";
  },
  reel_render: (b) =>
    SLUG.test(b.slug || "") && VARIANTS.test(b.variants || "A,B,C")
      ? ["reel-studio.yml", { mode: "render", slug: b.slug, variants: b.variants || "A,B,C" }]
      : "bad slug or variants",
  reel_ingest: (b) =>
    SLUG.test(b.slug || "") && FOOTAGE.test(b.footage || "newest") && !String(b.footage || "").includes("..")
      ? ["reel-studio.yml", { mode: "ingest", slug: b.slug, footage: b.footage || "newest" }]
      : "bad slug or footage name",
};

export async function onRequestPost({ request, env }) {
  const email = await accessEmail(request, env);
  if (!email || email !== (env.OWNER_EMAIL || "").toLowerCase()) return json({ error: "not allowed" }, 403);
  let body;
  try {
    body = await request.json();
  } catch {
    return json({ error: "bad json" }, 400);
  }
  if (!ACTIONS.has(body.action)) return json({ error: "unknown action" }, 400);
  if (body.action === "idea" && !String(body.text || "").trim()) return json({ error: "empty idea" }, 400);
  if (body.action === "run") {
    const job = Object.hasOwn(JOBS, body.job) ? JOBS[body.job](body) : "unknown job";
    if (typeof job === "string") return json({ error: job }, 400);
    await dispatchWorkflow(env, ...job);
    return json({ ok: true });
  }
  await dispatch(env, body, "dashboard");
  return json({ ok: true });
}
