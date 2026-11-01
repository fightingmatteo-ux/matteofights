// GET /api/plan/buy?src=REEL -> Stripe Checkout for the 4-week plan, priced by country (lib/plan.js priceFor).
// Makes the buyer's private token first, so the same personal link is the success page AND sits on the Stripe
// receipt/invoice email (lost-link recovery for free). Payment is confirmed later by /api/plan/me against Stripe.
import { SITE, PRODUCT, priceFor, newToken, save, stripe } from "../../../lib/plan.js";

export async function onRequestGet({ request, env }) {
  if (!env.STRIPE_SECRET_KEY) return new Response("Checkout is not switched on yet.", { status: 503 });
  const url = new URL(request.url);
  const src = (url.searchParams.get("src") || "").replace(/[^\w-]/g, "").slice(0, 40);
  const country = request.headers.get("cf-ipcountry") || "";
  const amount = priceFor(country);
  const token = newToken();
  const link = `${SITE}/plan/#k=${token}`;
  let s;
  try {
    s = await stripe(env, "POST", "checkout/sessions", {
      mode: "payment",
      "line_items[0][quantity]": "1",
      "line_items[0][price_data][currency]": "usd",
      "line_items[0][price_data][unit_amount]": String(amount),
      "line_items[0][price_data][product_data][name]": PRODUCT,
      "line_items[0][price_data][product_data][description]": "4 weeks, 3 sessions a week, no gym. Test on day 1, retest on day 28.",
      client_reference_id: token,
      "metadata[token]": token,
      "metadata[src]": src,
      "metadata[country]": country,
      "invoice_creation[enabled]": "true",
      "invoice_creation[invoice_data][description]": `Your plan (bookmark this link, it is yours): ${link}`,
      allow_promotion_codes: "true",
      success_url: link,
      cancel_url: `${SITE}/plan/?cancelled=1`,
    });
  } catch (e) {
    return new Response(`Checkout failed, try again in a minute. (${String(e.message || e).slice(0, 120)})`, { status: 502 });
  }
  await save(env, token, { session: s.id, status: "pending", amount, currency: "usd", country, src, created: new Date().toISOString() });
  return Response.redirect(s.url, 303);
}
