// The buyer's personal link calls this. GET /api/plan/me?k=TOKEN -> { paid, paid_at, baseline, retest }.
// "paid" is set by the Lemon Squeezy webhook (webhook.js), usually a few seconds after checkout; the page retries.
// POST /api/plan/me { k, test: "baseline"|"retest", results: { jump, pushups, burpees } } saves a test.
import { PLAN } from "../../../lib/plan_content.js";
import { cors, json, load, save, telegram, validToken } from "../../../lib/plan.js";

const FIELDS = { jump: [10, 400], pushups: [0, 200], burpees: [0, 200] }; // jump in cm; page converts inches

const view = (d) => ({ paid: d.status === "paid", plan: d.status === "paid" ? PLAN : undefined, paid_at: d.paid_at || null, baseline: d.baseline || null, retest: d.retest || null });

export async function onRequestOptions({ request }) {
  return new Response(null, { status: 204, headers: cors(request) });
}

export async function onRequestGet({ request, env }) {
  const k = new URL(request.url).searchParams.get("k");
  if (!validToken(k)) return json(request, { error: "bad link" }, 400);
  const doc = await load(env, k);
  if (!doc) return json(request, { error: "unknown link" }, 404);
  return json(request, view(doc));
}

export async function onRequestPost({ request, env }) {
  let body;
  try {
    body = await request.json();
  } catch {
    return json(request, { error: "bad json" }, 400);
  }
  const { k, test, results } = body || {};
  if (!validToken(k) || !["baseline", "retest"].includes(test) || !results) return json(request, { error: "bad request" }, 400);
  const doc = await load(env, k);
  if (!doc || doc.status !== "paid") return json(request, { error: "not paid" }, 403);
  if (test === "retest" && !doc.baseline) return json(request, { error: "do the first test first" }, 409);
  const clean = { at: new Date().toISOString() };
  for (const [f, [lo, hi]] of Object.entries(FIELDS)) {
    const n = Number(results[f]);
    if (!Number.isFinite(n) || n < lo || n > hi) return json(request, { error: `check ${f}` }, 400);
    clean[f] = Math.round(n * 10) / 10;
  }
  await save(env, k, { [test]: clean });
  if (test === "retest") {
    const b = doc.baseline;
    await telegram(env, `📈 Plan retest: jump ${b.jump}->${clean.jump} cm, push-ups ${b.pushups}->${clean.pushups}, burpees ${b.burpees}->${clean.burpees}`);
  }
  return json(request, view({ ...doc, [test]: clean }));
}
