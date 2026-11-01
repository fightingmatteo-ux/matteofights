// Shared helpers for the paid 4-week plan (functions/api/plan/*). Not a route: Pages only routes files under functions/.
// One D1 doc per buyer: kind "plan", id = the buyer's private token (their personal link matteofights.me/plan/#k=TOKEN).
// data: { session, status: "pending"|"paid", amount, currency, country, src, created, paid_at, email, baseline, retest }

export const SITE = "https://matteofights.me";
export const PRODUCT = "The 4-Week Power Plan";
const ORIGINS = [SITE, "https://www.matteofights.me"];
const NOW_SQL = "strftime('%Y-%m-%dT%H:%M:%SZ','now')";

// Price in US cents by country (Cloudflare's cf-ipcountry). Lower price where $12 is a lot of money.
// Change prices here; Stripe shows local currency on top of this when Adaptive Pricing is on in the dashboard.
export const PRICE_FULL = 1200;
export const PRICE_LOW = 600;
const LOW = new Set(("IN PK BD LK NP PH ID VN NG KE GH EG MA TN DZ ET UG TZ ZW ZM MM KH LA BO PY " +
  "VE CO PE EC AR BR MX TR UA UZ KZ KG TJ IR IQ SY YE AF").split(" "));
export const priceFor = (country) => (LOW.has((country || "").toUpperCase()) ? PRICE_LOW : PRICE_FULL);

export function cors(request) {
  const o = request.headers.get("origin") || "";
  return {
    "access-control-allow-origin": ORIGINS.includes(o) ? o : ORIGINS[0],
    "access-control-allow-methods": "GET, POST, OPTIONS",
    "access-control-allow-headers": "content-type",
    "vary": "origin",
  };
}

export const json = (request, body, status = 200) =>
  new Response(JSON.stringify(body), { status, headers: { "content-type": "application/json", ...cors(request) } });

export function newToken() {
  const b = crypto.getRandomValues(new Uint8Array(18));
  return btoa(String.fromCharCode(...b)).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

export const validToken = (k) => typeof k === "string" && /^[A-Za-z0-9_-]{20,40}$/.test(k);

export async function load(env, token) {
  const r = await env.DB.prepare("SELECT data FROM docs WHERE kind = 'plan' AND id = ?").bind(token).first();
  return r ? JSON.parse(r.data) : null;
}

export async function save(env, token, patch) {
  await env.DB.prepare(
    `INSERT INTO docs (kind, id, data) VALUES ('plan', ?, json_patch('{}', ?)) ON CONFLICT (kind, id) DO UPDATE SET data = json_patch(docs.data, ?), updated_at = ${NOW_SQL}`,
  ).bind(token, JSON.stringify(patch), JSON.stringify(patch)).run();
}

// Stripe REST call with a form-encoded body (no SDK needed in a Worker).
export async function stripe(env, method, path, params) {
  const body = params ? new URLSearchParams(params).toString() : undefined;
  const r = await fetch(`https://api.stripe.com/v1/${path}`, {
    method,
    headers: { authorization: `Bearer ${env.STRIPE_SECRET_KEY}`, "content-type": "application/x-www-form-urlencoded" },
    body: method === "GET" ? undefined : body,
  });
  const d = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(`Stripe ${r.status}: ${(d.error && d.error.message) || "error"}`);
  return d;
}

export function telegram(env, text) {
  if (!env.TELEGRAM_BOT_TOKEN || !env.TELEGRAM_CHAT_ID) return Promise.resolve();
  return fetch(`https://api.telegram.org/bot${env.TELEGRAM_BOT_TOKEN}/sendMessage`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ chat_id: env.TELEGRAM_CHAT_ID, text }),
  }).catch(() => {});
}
