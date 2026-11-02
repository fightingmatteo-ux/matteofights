// Shared helpers for the paid 4-week plan (functions/api/plan/*). Not a route: Pages only routes files under functions/.
// One D1 doc per buyer: kind "plan", id = the buyer's private token (their personal link matteofights.me/plan/#k=TOKEN).
// data: { status: "pending"|"paid"|"refunded", order, amount, currency, country, src, created, paid_at, email, baseline, retest }

export const SITE = "https://matteofights.me";
export const PRODUCT = "The 4-Week Power Plan";
const ORIGINS = [SITE, "https://www.matteofights.me"];
const NOW_SQL = "strftime('%Y-%m-%dT%H:%M:%SZ','now')";

// Price in US cents by country (Cloudflare's cf-ipcountry). Lower price where $12 is a lot of money.
// Change prices here (sent to Lemon Squeezy as the checkout's custom price).
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

// Lemon Squeezy (merchant of record: handles VAT/sales tax, pays out to PayPal/bank). Store and product variant ids
// are not secret; the API key and webhook signing secret are Pages secrets (signup-deploy.yml).
export const LS_STORE_ID = "";   // Settings > Stores (number)
export const LS_VARIANT_ID = ""; // Products > The 4-Week Power Plan > variant id (number)

export async function lemon(env, method, path, body) {
  const r = await fetch(`https://api.lemonsqueezy.com/v1/${path}`, {
    method,
    headers: {
      accept: "application/vnd.api+json",
      "content-type": "application/vnd.api+json",
      authorization: `Bearer ${env.LEMONSQUEEZY_API_KEY}`,
    },
    body: body ? JSON.stringify(body) : undefined,
  });
  const d = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(`Lemon Squeezy ${r.status}: ${((d.errors || [])[0] || {}).detail || "error"}`);
  return d;
}

export async function hmacHex(secret, raw) {
  const key = await crypto.subtle.importKey("raw", new TextEncoder().encode(secret), { name: "HMAC", hash: "SHA-256" }, false, ["sign"]);
  const mac = await crypto.subtle.sign("HMAC", key, new TextEncoder().encode(raw));
  return [...new Uint8Array(mac)].map((x) => x.toString(16).padStart(2, "0")).join("");
}

export function telegram(env, text) {
  if (!env.TELEGRAM_BOT_TOKEN || !env.TELEGRAM_CHAT_ID) return Promise.resolve();
  return fetch(`https://api.telegram.org/bot${env.TELEGRAM_BOT_TOKEN}/sendMessage`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ chat_id: env.TELEGRAM_CHAT_ID, text }),
  }).catch(() => {});
}
