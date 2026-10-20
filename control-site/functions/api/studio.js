// POST /api/studio: revision notes and talking-point decisions, written to D1 directly.
//   {action:"request", target, text}    -> request/<id>, then the edit worker applies it
//   {action:"tp", id, status}           -> talking point skipped / back to new
//   {action:"retry", kind, id}          -> a failed upload/request back to open
import { json, isOwner, startWorkflow } from "../../lib/shared.js";
import { patch, put, now, newId } from "../../lib/db.js";

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
