// Comment auto-replies (Matteo 2026-11-01: "fully automate comments, don't sound robotic, under 8 words, nice + value,
// stand your ground with dickheads"): every other comment on a recent reel gets one short reply written by Claude in
// Matteo's voice (REPLY_RULES below), posted under the comment and copied to Matteo's Telegram so he can delete a bad one.
// Needs the ANTHROPIC_API_KEY secret on the Pages project (signup-deploy.yml copies it from the GitHub secret); without
// it nothing is sent. Kill switch: Pages secret AUTO_REPLY=off. One reply per comment (D1 kind "ig_reply"), max 2 per
// person per reel, nothing on reels older than 14 days, never on our own comments, threats/slurs/spam get no reply.
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

const REPLY_MODEL = "claude-haiku-5-5";
const REPLY_RULES = `You reply to Instagram comments as Matteo (@matteofights), 19, Swiss-Brazilian, trains Muay Thai in Bangkok.
You ARE Matteo typing on his phone. Never say or hint you are an AI, a bot, a team or an automation.

Facts you can use (never invent others): first Muay Thai fight at 16, his sixth fight, my first. Someone told me knock him out
or you lose. In the clinch I elbowed the top of his head, the ref stepped in to separate us and I threw the right hand anyway.
He went down. Official result: a draw. I think it should have been a DQ and I own that. Lesson: fighting is about control,
not hurting people. I still train. I am NOT an active pro fighter and have no upcoming fights: never promise a fight.
Free training plan: comment PROTOCOL (only mention it if someone asks for a plan or program).

Style:
- Under 8 words for most replies. Hard max 15 words.
- Casual, lowercase is fine, like a real 19 year old. No hashtags. At most one emoji, usually none.
- Never use em dashes. No corporate words ("great question", "thanks for sharing", "appreciate the support").
- Don't repeat the comment back. Don't start every reply the same way. Vary it.
- Nice people: warm and short. Add value when you can: a real tip, an honest answer, a quick question back.
- Agree with "DQ" takes. Never defend the late punch.
- Questions: answer straight in one line.
- Rude, mocking or dickhead comments: don't be nice and don't grovel. Short, calm, stand your ground, no insults back,
  no swearing. Example: "yeah, that's why I said it." / "didn't count. that's the point."
- Skip (no reply) for: spam, bots, links, promo, "check my page", threats, slurs, sexual stuff, and comments that are
  only tags of friends (unless there's text).

Reply with JSON only: {"reply": "<text>", "skip": false} or {"reply": "", "skip": true, "why": "<few words>"}.

Examples:
"DQ easy" -> {"reply": "agreed, should've been", "skip": false}
"bro still a KO 🔥" -> {"reply": "didn't count though. rightly", "skip": false}
"how long have you been training?" -> {"reply": "since I was a kid, on and off", "skip": false}
"ref was slow ngl" -> {"reply": "maybe. still my job to stop", "skip": false}
"cheater lol" -> {"reply": "yep, owned it in the video", "skip": false}
"first fight next month any tips?" -> {"reply": "breathe, win rounds, don't hunt the KO", "skip": false}
"🔥🔥" -> {"reply": "🙏", "skip": false}
"@jake" -> {"reply": "", "skip": true, "why": "only a tag"}`;

async function replied(env, id) {
  return !!(await env.DB.prepare("SELECT 1 FROM docs WHERE kind = 'ig_reply' AND id = ?").bind(id).first());
}

async function repliesTo(env, media, user) {
  const r = await env.DB.prepare("SELECT COUNT(*) AS n FROM docs WHERE kind = 'ig_reply' AND json_extract(data, '$.media') = ? AND json_extract(data, '$.user') = ? AND json_extract(data, '$.reply') IS NOT NULL")
    .bind(media, user).first();
  return (r && r.n) || 0;
}

async function writeReply(env, comment, caption, parentText) {
  const user = (parentText ? `They are replying to my earlier reply: "${parentText}"\n` : "")
    + `Reel caption: ${String(caption || "").slice(0, 600)}\nComment from @${comment.username}: ${comment.text}`;
  const r = await fetch("https://api.anthropic.com/v1/messages", {
    method: "POST",
    headers: { "content-type": "application/json", "x-api-key": env.ANTHROPIC_API_KEY, "anthropic-version": "2023-06-01" },
    body: JSON.stringify({ model: REPLY_MODEL, max_tokens: 120, system: REPLY_RULES, messages: [{ role: "user", content: user }] }),
  });
  const d = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(`anthropic ${r.status} ${JSON.stringify(d.error || d).slice(0, 200)}`);
  const txt = (d.content || []).map((b) => b.text || "").join("");
  const m = txt.match(/\{[\s\S]*\}/);
  const out = m ? JSON.parse(m[0]) : { skip: true, why: "no json" };
  let reply = String(out.reply || "").replace(/\s*[\u2014\u2013]\s*/g, ", ").replace(/#\w+/g, "").trim();
  // guards: never long, never links, never talk about bots/AI/automation
  if (!reply || out.skip || reply.split(/\s+/).length > 15 || /https?:|www\.|\b(ai|bots?|automat\w*|chatgpt|claude)\b/i.test(reply)) {
    return { skip: true, why: out.why || "guard" };
  }
  return { reply };
}

async function telegram(env, text) {
  if (!env.TELEGRAM_BOT_TOKEN || !env.TELEGRAM_CHAT_ID) return;
  await fetch(`https://api.telegram.org/bot${env.TELEGRAM_BOT_TOKEN}/sendMessage`, {
    method: "POST", headers: { "content-type": "application/json" },
    body: JSON.stringify({ chat_id: env.TELEGRAM_CHAT_ID, text, disable_web_page_preview: true }),
  }).catch(() => {});
}

async function autoReply(env, v) {
  const id = v.id;
  if (!id || !env.ANTHROPIC_API_KEY || String(env.AUTO_REPLY || "").toLowerCase() === "off") return;
  if (KEYWORD.test(v.text || "") || (v.from && v.from.username === OWN) || await replied(env, id)) return;
  const c = await ig(env, "GET", id, { fields: "id,text,username,timestamp,parent_id,media{id,caption,timestamp}" });
  if (!c.text || c.username === OWN || KEYWORD.test(c.text)) return;
  const media = c.media || {};
  if (Date.now() - Date.parse(c.timestamp) > 2 * 864e5) return;                       // old comment (webhook retry)
  if (media.timestamp && Date.now() - Date.parse(media.timestamp) > 14 * 864e5) return; // old reel
  let parentText = "";
  if (c.parent_id) {   // a reply in a thread: only answer when it replies to us, and keep it to 2 per person per reel
    const p = await ig(env, "GET", c.parent_id, { fields: "username,text" }).catch(() => ({}));
    if (p.username !== OWN) return;
    parentText = p.text || "";
  }
  if (await repliesTo(env, media.id, c.username) >= 2) return;
  const out = { comment: id, media: media.id, user: c.username, text: c.text.slice(0, 300), at: new Date().toISOString() };
  const w = await writeReply(env, c, media.caption, parentText);
  if (w.skip) {
    out.skipped = w.why;
  } else {
    await ig(env, "POST", `${id}/replies`, { message: w.reply });
    out.reply = w.reply;
    await telegram(env, `💬 @${c.username}: ${c.text.slice(0, 200)}\n↳ ${w.reply}`);
  }
  await env.DB.prepare(
    `INSERT INTO docs (kind, id, data) VALUES ('ig_reply', ?, ?) ON CONFLICT (kind, id) DO UPDATE SET data = excluded.data, updated_at = ${NOW_SQL}`,
  ).bind(id, JSON.stringify(out)).run();
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
    waitUntil(Promise.all(comments.map((v) => autoReply(env, v).catch((err) =>
      logHit(env, { reply_error: String(err.message || err).slice(0, 300), comment: v.id }).catch(() => {})))));
  }
  waitUntil(logHit(env, { fields: (body.entry || []).flatMap((e) => (e.changes || []).map((c) => c.field).concat(e.messaging ? ["messaging"] : [])),
    comments: comments.map((v) => ({ id: v.id, keyword: KEYWORD.test(v.text || "") })), token: !!env.IG_ACCESS_TOKEN }).catch(() => {}));
  return new Response("ok", { status: 200 });
}
