// POST /api/studio: revision notes and talking-point decisions, written to D1 directly.
//   {action:"request", target, text}    -> request/<id>, then the edit worker applies it
//   {action:"tp", id, status}           -> talking point skipped / back to new
//   {action:"retry", kind, id}          -> a failed upload/request back to open
//   {action:"revision", target, asset, text, notes:[{t, text, tags[], image (jpeg data URL)}]}
//                                       -> request/<id> with frame notes; each annotated frame to R2 revisions/<id>/<n>.jpg
//                                          (the edit worker downloads them: requests_cli.py notes <id> <dir>)
import { json, isOwner, startWorkflow } from "../../lib/shared.js";
import { patch, put, now, newId } from "../../lib/db.js";

const TAGS = new Set(["hook", "text", "cut", "pacing", "framing", "color", "audio", "broll", "captions", "other"]);
const MAX_NOTES = 20, MAX_IMG = 2_000_000;

async function revision(env, b) {
  const target = String(b.target || "").slice(0, 120);
  const notes = Array.isArray(b.notes) ? b.notes.slice(0, MAX_NOTES) : [];
  const text = String(b.text || "").trim().slice(0, 4000);
  if (!target || (!notes.length && !text)) return json({ error: "nothing to send" }, 400);
  const id = newId();
  // earlier revisions of this reel: round 2, 3... is the number that should fall as Claude learns
  const { results } = await env.DB.prepare("SELECT count(*) AS n FROM docs WHERE kind = 'request' AND json_extract(data, '$.target') = ?").bind(target).all();
  const out = [];
  for (const [k, nt] of notes.entries()) {
    const note = { t: Math.max(0, Math.round(Number(nt.t || 0) * 100) / 100), text: String(nt.text || "").trim().slice(0, 1000),
      tags: (Array.isArray(nt.tags) ? nt.tags : []).filter((x) => TAGS.has(x)).slice(0, 4) };
    const m = /^data:image\/jpeg;base64,(.+)$/.exec(String(nt.image || ""));
    if (m && m[1].length * 0.75 <= MAX_IMG) {
      const key = `revisions/${id}/${String(k + 1).padStart(2, "0")}-${note.t.toFixed(2)}s.jpg`;
      await env.MEDIA.put(key, Uint8Array.from(atob(m[1]), (c) => c.charCodeAt(0)), { httpMetadata: { contentType: "image/jpeg" } });
      note.image = key;
    }
    out.push(note);
  }
  const summary = text || out.map((n) => `${n.t.toFixed(1)}s: ${n.text}`).join("\n");
  await put(env, "request", id, { status: "open", target, asset: String(b.asset || "").slice(0, 160) || null, text: summary.slice(0, 4000),
    notes: out, tags: [...new Set(out.flatMap((n) => n.tags))], round: (results[0]?.n || 0) + 1, source: "player", at: now() });
  await startWorkflow(env, "edit-worker.yml").catch(() => {});
  return json({ id });
}

export async function onRequestPost({ request, env }) {
  if (!(await isOwner(request, env))) return json({ error: "not allowed" }, 403);
  const b = await request.json().catch(() => ({}));
  if (b.action === "request") {
    const text = String(b.text || "").trim();
    if (!text) return json({ error: "empty note" }, 400);
    const id = newId();
    await put(env, "request", id, { status: "open", target: String(b.target || "").slice(0, 120), text: text.slice(0, 4000), at: now() });
    await startWorkflow(env, "edit-worker.yml").catch(() => {});
    return json({ id });
  }
  if (b.action === "revision") return revision(env, b);
  if (b.action === "tp" && ["skipped", "new"].includes(b.status)) {
    await patch(env, "talking_point", String(b.id), { status: b.status });
    return json({ ok: true });
  }
  if (b.action === "retry" && ["upload", "request"].includes(b.kind)) {
    await patch(env, b.kind, String(b.id), { status: b.kind === "upload" ? "uploaded" : "open", result: null });
    await startWorkflow(env, "edit-worker.yml").catch(() => {});
    return json({ ok: true });
  }
  return json({ error: "unknown action" }, 400);
}
