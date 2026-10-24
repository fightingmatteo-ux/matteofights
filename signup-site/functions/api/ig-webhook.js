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
const KEYWORD = /\bprotocol\b/i;
const OWN = "matteofights";
const LINK = "https://matteofights.me/protocol";
const DM_TEXT = `Here it is 🥊 THE PROTOCOL, free: ${LINK}\n\nTake the 2 minute test first. It builds your workout around what you need most, no gym needed.`;
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

async function handleComment(env, v) {
  const id = v.id;
  if (!id || !KEYWORD.test(v.text || "") || (v.from && v.from.username === OWN) || await handled(env, id)) return;
  // Re-read the comment from Instagram: proves it is real, on our media and still says the keyword.
  const c = await ig(env, "GET", id, { fields: "id,text,username,timestamp,media{id}" });
  if (!KEYWORD.test(c.text || "") || c.username === OWN) return;
  if (Date.now() - Date.parse(c.timestamp) > 7 * 864e5) return;
  const out = { comment: id, media: c.media && c.media.id, user: c.username, at: new Date().toISOString() };
  try {
    await ig(env, "POST", "me/messages", { recipient: JSON.stringify({ comment_id: id }), message: JSON.stringify({ text: DM_TEXT }) });
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
    waitUntil(Promise.all(comments.map((v) => handleComment(env, v).catch((err) => console.log("comment", v.id, String(err))))));
  }
  return new Response("ok", { status: 200 });
}
