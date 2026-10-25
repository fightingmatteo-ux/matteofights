// GET /api/leads: everyone who signed up for THE PROTOCOL / STANCE (D1 kind "signup", written by
// signup-site/functions/api/signup.js) plus people who commented PROTOCOL and got the auto-DM but never signed up
// (kind "protocol_dm", signup-site/functions/api/ig-webhook.js). Owner only (Access login), emails included.
// POST /api/leads {email|handle, status, note}: Matteo's follow-up state, kept on the signup doc
// (lead_status, lead_note, contacted_at) or, for commenters without a signup, on kind "lead" by handle.
import { json, isOwner } from "../../lib/shared.js";
import { all, patch, now } from "../../lib/db.js";

const STATUSES = new Set(["new", "messaged", "replied", "client", "skip"]);
const handleOf = (s) => String(s || "").trim().replace(/^@+/, "").toLowerCase();

export async function onRequestGet({ request, env }) {
  if (!(await isOwner(request, env))) return json({ error: "not allowed" }, 403);
  const [signups, dms, marks] = await Promise.all([all(env, "signup"), all(env, "protocol_dm"), all(env, "lead")]);
  const mark = Object.fromEntries(marks.map((m) => [m.id, m]));
  const known = new Set(signups.map((s) => handleOf(s.instagram)).filter(Boolean));
  const commented = {};
  for (const d of dms) {
    const h = handleOf(d.user);
    if (!h) continue;
    const c = (commented[h] ||= { handle: h, comments: 0, first_at: d.at, dm: d.dm });
    c.comments += 1;
    if ((d.at || "") < (c.first_at || "~")) c.first_at = d.at;
  }
  const leads = signups.map((s) => {
    const h = handleOf(s.instagram);
    return {
      key: s.id, email: s.email || s.id, handle: h || null, kind: s.stance_at && !s.protocol_at ? "stance" : "protocol",
      focus: s.primaryFocus || null, focus2: s.secondaryFocus || null, freq: s.trainingFrequency || null,
      equipment: s.equipmentAccess || null, experience: s.experience || null, goal: s.goal || null,
      source: s.source || null, whatsapp: s.whatsapp || null, stance: !!s.stance_at,
      at: s.first_at || s.updated_at, last_at: s.last_at || null,
      commented: !!(h && commented[h]),
      status: s.lead_status || "new", note: s.lead_note || "", contacted_at: s.contacted_at || null,
    };
  });
  for (const c of Object.values(commented)) {
    if (known.has(c.handle)) continue;
    const m = mark["ig:" + c.handle] || {};
    leads.push({
      key: "ig:" + c.handle, email: null, handle: c.handle, kind: "comment", at: c.first_at, commented: true,
      dm: String(c.dm || "").startsWith("sent") ? "sent" : "failed",
      status: m.status || "new", note: m.note || "", contacted_at: m.contacted_at || null,
    });
  }
  leads.sort((a, b) => ((a.at || "") < (b.at || "") ? 1 : -1));
  return json({ at: now(), leads });
}

export async function onRequestPost({ request, env }) {
  if (!(await isOwner(request, env))) return json({ error: "not allowed" }, 403);
  const b = await request.json().catch(() => ({}));
  const key = String(b.key || "");
  if (!key) return json({ error: "no lead" }, 400);
  const fields = {};
  if (b.status != null) {
    if (!STATUSES.has(b.status)) return json({ error: "bad status" }, 400);
    fields.status = b.status;
    if (b.status === "messaged") fields.contacted_at = now();
  }
  if (b.note != null) fields.note = String(b.note).slice(0, 1000);
  if (!Object.keys(fields).length) return json({ error: "nothing to change" }, 400);
  if (key.startsWith("ig:")) {
    await patch(env, "lead", key, { ...fields, at: now() });
  } else {
    const out = {};
    if (fields.status) out.lead_status = fields.status;
    if (fields.contacted_at) out.contacted_at = fields.contacted_at;
    if (fields.note != null) out.lead_note = fields.note;
    // only ever touch an existing signup: the public form owns creating them
    const r = await env.DB.prepare("SELECT 1 FROM docs WHERE kind = 'signup' AND id = ?").bind(key).first();
    if (!r) return json({ error: "unknown lead" }, 404);
    await patch(env, "signup", key, out);
  }
  return json({ ok: true });
}
