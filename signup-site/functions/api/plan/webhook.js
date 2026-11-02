// POST /api/plan/webhook: Lemon Squeezy calls this (Settings > Webhooks, events order_created + order_refunded,
// signing secret = Pages secret LEMONSQUEEZY_WEBHOOK_SECRET). Checks the X-Signature, then marks the buyer's token
// paid (Telegram "sold" ping) or refunded (plan locks again). The token travels in the checkout's custom data.
import { PRODUCT, hmacHex, load, save, telegram, validToken } from "../../../lib/plan.js";

export async function onRequestPost({ request, env }) {
  const raw = await request.text();
  if (!env.LEMONSQUEEZY_WEBHOOK_SECRET) return new Response("not configured", { status: 503 });
  const sig = request.headers.get("x-signature") || "";
  if (!sig || sig !== (await hmacHex(env.LEMONSQUEEZY_WEBHOOK_SECRET, raw))) return new Response("bad signature", { status: 401 });
  const body = JSON.parse(raw);
  const event = body.meta && body.meta.event_name;
  const k = body.meta && body.meta.custom_data && body.meta.custom_data.token;
  if (!validToken(k)) return new Response("no token, ignored");
  const doc = await load(env, k);
  if (!doc) return new Response("unknown token, ignored");
  const a = (body.data && body.data.attributes) || {};
  if (event === "order_created" && a.status === "paid" && doc.status !== "paid") {
    const patch = {
      status: "paid",
      paid_at: new Date().toISOString(),
      order: String(body.data.id || ""),
      email: a.user_email || "",
      amount: a.total,
      currency: (a.currency || "usd").toLowerCase(),
      test: !!(body.meta && body.meta.test_mode),
    };
    await save(env, k, patch);
    await telegram(env, `💰 ${PRODUCT} sold${patch.test ? " (TEST)" : ""}: ${(patch.amount / 100).toFixed(2)} ${patch.currency.toUpperCase()}` +
      `${doc.country ? ` (${doc.country})` : ""}${doc.src ? `, from ${doc.src}` : ""}`);
  } else if (event === "order_refunded") {
    await save(env, k, { status: "refunded", refunded_at: new Date().toISOString() });
    await telegram(env, `↩️ ${PRODUCT} refunded${doc.email ? `: ${doc.email}` : ""}`);
  }
  return new Response("ok");
}
