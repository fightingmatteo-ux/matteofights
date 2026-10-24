// Public signup endpoint for THE PROTOCOL (matteofights.me/protocol) and the STANCE waitlist, on its own Pages
// project (matteo-signup) because control.matteofights.me sits behind Cloudflare Access. Replaces posting straight
// to Make.com: every field the page sends is kept in D1 (kind "signup", one doc per email, same docs table as
// tools/state.py), the payload is still forwarded to the Make.com webhook so the Notion table keeps filling, and
// Matteo gets a Telegram line per new lead (Instagram handle first: he follows up there).
// GET returns counts only (no emails). Deploy: .github/workflows/signup-deploy.yml.

const MAKE_WEBHOOK = "https://hook.eu1.make.com/7tieu19hys3tpolvxvj6ti1jn6t7x0ra";
const ORIGINS = ["https://matteofights.me", "https://www.matteofights.me"];
const FIELDS = ["primaryFocus", "secondaryFocus", "trainingFrequency", "equipmentAccess", "instagram", "whatsapp",
  "experience", "goal", "source"];
const NOW_SQL = "strftime('%Y-%m-%dT%H:%M:%SZ','now')";
const now = () => new Date().toISOString().replace(/\.\d+Z$/, "Z");

function cors(request) {
  const o = request.headers.get("origin") || "";
  return {
    "access-control-allow-origin": ORIGINS.includes(o) ? o : ORIGINS[0],
    "access-control-allow-methods": "GET, POST, OPTIONS",
    "access-control-allow-headers": "content-type",
    "vary": "origin",
  };
}

const reply = (request, body, status = 200) =>
  new Response(JSON.stringify(body), { status, headers: { "content-type": "application/json", ...cors(request) } });

const clean = (v, n = 120) => (typeof v === "string" ? v.trim().slice(0, n) : null);

async function getDoc(env, id) {
  const r = await env.DB.prepare("SELECT data FROM docs WHERE kind = 'signup' AND id = ?").bind(id).first();
  return r ? JSON.parse(r.data) : null;
}

async function patchDoc(env, id, fields) {
  const f = JSON.stringify(fields);
  await env.DB.prepare(
    `INSERT INTO docs (kind, id, data) VALUES ('signup', ?, json_patch('{}', ?)) ON CONFLICT (kind, id) DO UPDATE SET data = json_patch(docs.data, ?), updated_at = ${NOW_SQL}`,
  ).bind(id, f, f).run();
}

function telegram(env, text) {
  if (!env.TELEGRAM_BOT_TOKEN || !env.TELEGRAM_CHAT_ID) return Promise.resolve();
  return fetch(`https://api.telegram.org/bot${env.TELEGRAM_BOT_TOKEN}/sendMessage`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ chat_id: env.TELEGRAM_CHAT_ID, text }),
  }).catch(() => {});
}

export async function onRequestOptions({ request }) {
  return new Response(null, { status: 204, headers: cors(request) });
}

export async function onRequestGet({ request, env }) {
  const r = await env.DB.prepare(
    `SELECT count(*) AS people,
            sum(json_extract(data, '$.protocol_at') IS NOT NULL) AS protocol,
            sum(json_extract(data, '$.stance_at') IS NOT NULL) AS stance,
            sum(json_extract(data, '$.instagram') IS NOT NULL) AS with_instagram,
            max(json_extract(data, '$.last_at')) AS latest
     FROM docs WHERE kind = 'signup'`,
  ).first();
  const dm = await env.DB.prepare(
    `SELECT count(*) AS comments, sum(json_extract(data, '$.dm') = 'sent') AS dms_sent FROM docs WHERE kind = 'protocol_dm'`,
  ).first();
  return reply(request, { ...r, protocol_comments: dm.comments, protocol_dms_sent: dm.dms_sent });
}

export async function onRequestPost({ request, env, waitUntil }) {
  let body;
  try {
    body = await request.json();
  } catch {
    return reply(request, { error: "bad json" }, 400);
  }
  const email = clean(body.email, 200)?.toLowerCase();
  if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) return reply(request, { error: "bad email" }, 400);

  // Forward first, untouched, so Notion keeps working even if D1 has a bad moment.
  waitUntil(fetch(MAKE_WEBHOOK, { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify(body) })
    .catch(() => {}));

  const event = body.list === "stance_waitlist" ? "stance" : body.kind === "optional_profile" ? "profile" : "protocol";
  const before = (await getDoc(env, email)) || {};
  const fields = { email, last_at: now(), events: { [event]: ((before.events || {})[event] || 0) + 1 } };
  if (!before.first_at) fields.first_at = now();
  if (event === "stance" && !before.stance_at) fields.stance_at = now();
  if (event === "protocol" && !before.protocol_at) fields.protocol_at = now();
  for (const k of FIELDS) {
    const v = clean(body[k]);
    if (v) fields[k] = k === "instagram" ? "@" + v.replace(/^@+/, "").replace(/\s/g, "") : v;
  }
  await patchDoc(env, email, fields);

  // One Telegram line per thing Matteo can act on: a new person, a new Instagram handle, a STANCE join.
  const focus = fields.primaryFocus || before.primaryFocus;
  const ig = fields.instagram && fields.instagram !== before.instagram ? fields.instagram : null;
  const lines = [];
  if (event === "protocol" && !before.protocol_at) {
    lines.push(`🥊 New PROTOCOL signup${focus ? `: wants ${focus}` : ""}` +
      `${fields.trainingFrequency ? `, trains ${fields.trainingFrequency}` : ""}${fields.equipmentAccess ? `, ${fields.equipmentAccess}` : ""}.`);
  }
  if (event === "stance" && !before.stance_at) lines.push(`📱 New STANCE waitlist signup${before.instagram ? ` (${before.instagram})` : ""}.`);
  if (ig) lines.push(`Instagram: ${ig}\nDM them: "Hey, you grabbed THE PROTOCOL. What's the one thing you're stuck on right now?"`);
  if (lines.length) waitUntil(telegram(env, lines.join("\n")));
  return reply(request, { ok: true });
}
