// GET /api/plan/buy?src=REEL -> Lemon Squeezy checkout for the 4-week plan, priced by country (lib/plan.js priceFor).
// Makes the buyer's private token first: it is the redirect after paying AND the button on the receipt email
// (lost-link recovery for free). The payment itself is confirmed by the order_created webhook (webhook.js).
import { SITE, PRODUCT, LS_STORE_ID, LS_VARIANT_ID, priceFor, newToken, save, lemon } from "../../../lib/plan.js";

export async function onRequestGet({ request, env }) {
  if (!env.LEMONSQUEEZY_API_KEY || !LS_STORE_ID || !LS_VARIANT_ID) return new Response("Checkout is not switched on yet.", { status: 503 });
  const url = new URL(request.url);
  const src = (url.searchParams.get("src") || "").replace(/[^\w-]/g, "").slice(0, 40);
  const country = request.headers.get("cf-ipcountry") || "";
  const amount = priceFor(country);
  const token = newToken();
  const link = `${SITE}/plan/#k=${token}`;
  let c;
  try {
    c = await lemon(env, "POST", "checkouts", {
      data: {
        type: "checkouts",
        attributes: {
          custom_price: amount,
          product_options: {
            name: PRODUCT,
            redirect_url: link,
            receipt_button_text: "Open your plan",
            receipt_link_url: link,
            receipt_thank_you_note: "Your plan link is the button above. Bookmark it: it's how you come back for the day 28 retest.",
          },
          checkout_data: { custom: { token, src, country } },
          expires_at: new Date(Date.now() + 864e5).toISOString(),
        },
        relationships: {
          store: { data: { type: "stores", id: String(LS_STORE_ID) } },
          variant: { data: { type: "variants", id: String(LS_VARIANT_ID) } },
        },
      },
    });
  } catch (e) {
    return new Response(`Checkout failed, try again in a minute. (${String(e.message || e).slice(0, 120)})`, { status: 502 });
  }
  await save(env, token, { status: "pending", amount, currency: "usd", country, src, created: new Date().toISOString() });
  return Response.redirect(c.data.attributes.url, 303);
}
