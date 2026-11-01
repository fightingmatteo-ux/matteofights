// The buyer's personal link calls this. GET /api/plan/me?k=TOKEN -> { paid, paid_at, baseline, retest }.
// First visit after paying checks the Stripe session and marks the doc paid (+ Telegram ping). No webhook needed.
// POST /api/plan/me { k, test: "baseline"|"retest", results: { jump, pushups, burpees } } saves a test.
import { PLAN } from "../../../lib/plan_content.js";
import { cors, json, load, save, stripe, telegram, validToken, PRODUCT } from "../../../lib/plan.js";

const FIELDS = { jump: [10, 400], pushups: [0, 200], burpees: [0, 200] }; // jump in cm; page converts inches

async function confirm(env, k, doc) {
  if (doc.status === "paid") return doc;
  const s = await stripe(env, "GET", `checkout/sessions/${doc.session}`);
  if (s.payment_status !== "paid" || (s.metadata && s.metadata.token !== k)) return doc;
  const patch = {
    status: "paid",
    paid_at: new Date().toISOString(),
    email: (s.customer_details && s.customer_details.email) || "",
    amount: s.amount_total,
    currency: s.currency,
  };
  await save(env, k, patch);
  await telegram(env, `💰 ${PRODUCT} sold: ${(patch.amount / 100).toFixed(2)} ${patch.currency.toUpperCase()}` +
    `${doc.country ? ` (${doc.country})` : ""}${doc.src ? `, from ${doc.src}` : ""}`);
  return { ...doc, ...patch };
}

const view = (d) => ({ paid: d.status === "paid", plan: d.status === "paid" ? PLAN : undefined, paid_at: d.paid_at || null, baseline: d.baseline || null, retest: d.retest || null });

export async function onRequestOptions({ request }) {
  return new Response(null, { status: 204, headers: cors(request) });
}

export async function onRequestGet({ request, env }) {
  const k = new URL(request.url).searchParams.get("k");
  if (!validToken(k)) return json(request, { error: "bad link" }, 400);
  let doc = await load(env, k);
  if (!doc) return json(request, { error: "unknown link" }, 404);
  try {
    doc = await confirm(env, k, doc);
  } catch (e) {
    return json(request, { error: "could not check payment, refresh in a minute" }, 502);
  }
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
