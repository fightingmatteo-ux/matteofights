// Fast comment replies (Matteo 2026-11-01, "option 1"): any other new comment starts the "Comment replies" workflow
// (Claude Code on Matteo's subscription), so a reply lands in about a minute. Needs Pages secret GH_DISPATCH_TOKEN
// (fine-grained PAT, this repo only, Actions read/write); without it the workflow's 3-hourly run still answers.
// Cost guards: at most one start per 90 s (later comments set "pending" and the running job starts one more), at
// most 48 starts per UTC day (D1 kind "reply_dispatch"), kill switch Pages secret AUTO_REPLY=off.
// Comment-to-DM for "comment PROTOCOL": Meta's Instagram webhook (field "comments") calls this on every new comment
// on @matteofights. A comment containing the keyword gets one private reply (a DM to the commenter, Instagram's
// private-replies API) with the PROTOCOL link, plus a short public reply under the comment. One DM per comment,
// remembered in D1 (kind "protocol_dm"). Own comments and anything older than 7 days are skipped.
// Setup (Matteo, Meta app dashboard): tools/instagram/README.md "Comment PROTOCOL auto-DM".
// Secrets on the Pages project: IG_ACCESS_TOKEN (needs instagram_business_manage_comments + _manage_messages),
// optional IG_APP_SECRET (checks Meta's signature). Without the secret every comment is re-read from the API
// before anything is sent, so a forged call can't make us DM anyone.

const IG = "https://graph.instagram.com/v21.0";
const VERIFY_TOKEN = "matteofights-protocol";
const KEYWORD = /\b(protocol|plan)\b/i;
const OWN = "matteofights";
const LINK = "https://matteofights.me/protocol";
const DM_TEXT = `Here it is 🥊 THE PROTOCOL, free: ${LINK}\n\nTake the 2 minute test first. It builds your workout around what you need most, no gym needed.`;
// "comment PLAN" (plan reels, 2026-11-02): same free PROTOCOL link, worded as the plan they asked for. Shows in the
// control center Leads tab like PROTOCOL commenters (kind protocol_dm, with keyword "plan").
const PLAN_DM_TEXT = `Here's your plan 🥊 Free: ${LINK}\n\nTake the 2 minute test first. It builds the plan around what you need most, no gym needed.`;
// Per-reel plans (docs/plans/plans.json): the first plan whose `match` phrase is in the reel's caption.
const PLANS_URL = "https://matteofights.me/plans/plans.json";
async function planFor(caption) {
  if (!caption) return null;
  try {
    const r = await fetch(PLANS_URL, { cf: { cacheTtl: 300, cacheEverything: true } });
    const { plans } = await r.json();
    const low = caption.toLowerCase();
    return plans.find((p) => p.match && low.includes(p.match.toLowerCase())) || null;
  } catch {
    return null;
  }
}
const reelPlanText = (p) => `Here's your ${p.title} 🥊 Free: https://matteofights.me/plans/?p=${p.slug}\n\nScreenshot it or save the link. Run it for 4 weeks.`;
const keywordOf = (text) => (/\bprotocol\b/i.test(text || "") ? "protocol" : "plan");
const PUBLIC_REPLIES = ["Sent it to your DMs 🥊", "Check your DMs 🥊", "In your DMs now 🥊"];
const NOW_SQL = "strftime('%Y-%m-%dT%H:%M:%SZ','now')";

async function signatureOk(request, raw, secret) {
  const sig = (request.headers.get("x-hub-signature-256") || "").replace(/^sha256=/, "");
  const key = await crypto.subtle.importKey("raw", new TextEncoder().encode(secret), { name: "HMAC", hash: "SHA-256" }, false, ["sign"]);
  const mac = await crypto.subtle.sign("HMAC", key, new TextEncoder().encode(raw));
  const hex = [...new Uint8Array(mac)].map((b) => b.toString(16).padStart(2, "0")).join("");
  return sig.length === hex.length && sig === hex;
}

async function ig(env, method, path, params = {}) {
  const qs = new URLSearchParams({ ...params, access_token: env.IG_ACCESS_TOKEN });
  const r = await fetch(`${IG}/${path}${method === "GET" ? "?" + qs : ""}`, method === "GET" ? {} : {
    method, headers: { "content-type": "application/x-www-form-urlencoded" }, body: qs,
  });
  const d = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(`${path}: ${r.status} ${JSON.stringify(d.error || d).slice(0, 300)}`);
  return d;
}

async function handled(env, id) {
  return !!(await env.DB.prepare("SELECT 1 FROM docs WHERE kind = 'protocol_dm' AND id = ?").bind(id).first());
}

async function remember(env, id, data) {
  await env.DB.prepare(
    `INSERT INTO docs (kind, id, data) VALUES ('protocol_dm', ?, ?) ON CONFLICT (kind, id) DO UPDATE SET data = excluded.data, updated_at = ${NOW_SQL}`,
  ).bind(id, JSON.stringify(data)).run();
}

// Every call Meta makes, so a failed test shows where it stopped (kind "ig_hit", counts on GET /api/signup).
async function logHit(env, data) {
  const id = new Date().toISOString() + "-" + crypto.randomUUID().slice(0, 4);
  await env.DB.prepare("INSERT INTO docs (kind, id, data) VALUES ('ig_hit', ?, ?)").bind(id, JSON.stringify(data)).run();
}

async function handleComment(env, v) {
  const id = v.id;
  if (!id || !KEYWORD.test(v.text || "") || (v.from && v.from.username === OWN) || await handled(env, id)) return;
  // Re-read the comment from Instagram: proves it is real, on our media and still says the keyword.
  const c = await ig(env, "GET", id, { fields: "id,text,username,timestamp,media{id}" });
  if (!KEYWORD.test(c.text || "") || c.username === OWN) return;
  if (Date.now() - Date.parse(c.timestamp) > 7 * 864e5) return;
  const out = { comment: id, media: c.media && c.media.id, user: c.username, keyword: keywordOf(c.text), at: new Date().toISOString() };
  let plan = null;
  if (out.keyword === "plan" && out.media) {
    try {
      plan = await planFor((await ig(env, "GET", out.media, { fields: "caption" })).caption);
    } catch {
      plan = null; // caption unreadable: fall back to the PROTOCOL link
    }
  }
  if (plan) out.plan = plan.slug;
  try {
    await ig(env, "POST", "me/messages", { recipient: JSON.stringify({ comment_id: id }), message: JSON.stringify({ text: plan ? reelPlanText(plan) : out.keyword === "plan" ? PLAN_DM_TEXT : DM_TEXT }) });
    out.dm = "sent";
  } catch (e) {
    out.dm = "failed: " + String(e.message || e).slice(0, 300);
  }
  try {
    await ig(env, "POST", `${id}/replies`, { message: PUBLIC_REPLIES[Math.floor(Math.random() * PUBLIC_REPLIES.length)] });
    out.reply = "sent";
  } catch (e) {
    out.reply = "failed: " + String(e.message || e).slice(0, 300);
  }
  await remember(env, id, out);
}

const DISPATCH_GAP_MS = 90e3;
const DISPATCH_MAX_DAY = 48;

async function kickReplies(env, v) {
  if (!env.GH_DISPATCH_TOKEN || String(env.AUTO_REPLY || "").toLowerCase() === "off") return;
  if (!v || !v.id || KEYWORD.test(v.text || "") || (v.from && v.from.username === OWN)) return;
  const day = new Date().toISOString().slice(0, 10);
  const row = await env.DB.prepare("SELECT data FROM docs WHERE kind = 'reply_dispatch' AND id = ?").bind(day).first();
  const d = row ? JSON.parse(row.data) : { n: 0, last: 0 };
  const save = (x) => env.DB.prepare(
    `INSERT INTO docs (kind, id, data) VALUES ('reply_dispatch', ?, ?) ON CONFLICT (kind, id) DO UPDATE SET data = excluded.data, updated_at = ${NOW_SQL}`,
  ).bind(day, JSON.stringify(x)).run();
  if (d.n >= DISPATCH_MAX_DAY) return;                       // daily cap: the 3-hourly run picks the rest up
  if (Date.now() - d.last < DISPATCH_GAP_MS) {               // a run just started: tell it to go once more
    await save({ ...d, pending: Date.now() });
    return;
  }
  const r = await fetch("https://api.github.com/repos/fightingmatteo-ux/matteofights/actions/workflows/comment-replies.yml/dispatches", {
    method: "POST",
    headers: { authorization: `Bearer ${env.GH_DISPATCH_TOKEN}`, accept: "application/vnd.github+json", "user-agent": "matteo-signup",
      "content-type": "application/json" },
    body: JSON.stringify({ ref: "master", inputs: { source: "webhook" } }),
  });
  if (!r.ok) throw new Error(`dispatch ${r.status} ${(await r.text()).slice(0, 200)}`);
  await save({ n: d.n + 1, last: Date.now(), pending: 0 });
}

// Meta's subscription check.
export async function onRequestGet({ request }) {
  const u = new URL(request.url);
  if (u.searchParams.get("hub.mode") === "subscribe" && u.searchParams.get("hub.verify_token") === VERIFY_TOKEN) {
    return new Response(u.searchParams.get("hub.challenge") || "", { status: 200 });
  }
  return new Response("forbidden", { status: 403 });
}

export async function onRequestPost({ request, env, waitUntil }) {
  const raw = await request.text();
  if (env.IG_APP_SECRET && !(await signatureOk(request, raw, env.IG_APP_SECRET))) return new Response("bad signature", { status: 403 });
  let body;
  try {
    body = JSON.parse(raw);
  } catch {
    return new Response("bad json", { status: 400 });
  }
  const comments = [];
  for (const e of body.entry || []) {
    for (const ch of e.changes || []) {
      if (ch.field === "comments" && ch.value) comments.push(ch.value);
    }
  }
  // Answer Meta fast (it retries slow webhooks); do the sending after.
  if (env.IG_ACCESS_TOKEN && comments.length) {
    waitUntil(Promise.all(comments.map((v) => handleComment(env, v).catch((err) =>
      logHit(env, { error: String(err.message || err).slice(0, 300), comment: v.id }).catch(() => {})))));
    waitUntil(Promise.all(comments.map((v) => kickReplies(env, v).catch((err) =>
      logHit(env, { reply_dispatch_error: String(err.message || err).slice(0, 300), comment: v.id }).catch(() => {})))));
  }
  waitUntil(logHit(env, { fields: (body.entry || []).flatMap((e) => (e.changes || []).map((c) => c.field).concat(e.messaging ? ["messaging"] : [])),
    comments: comments.map((v) => ({ id: v.id, keyword: KEYWORD.test(v.text || "") })), token: !!env.IG_ACCESS_TOKEN }).catch(() => {}));
  return new Response("ok", { status: 200 });
}
