// Footage upload from the phone straight into R2 (binding MEDIA), in parts so files of any size work
// (one request body is capped at 100 MB). Flow:
//   POST {op:"create", name, size, type}                    -> {key, uploadId}
//   PUT  /api/upload?key=..&uploadId=..&part=N  <bytes>      -> {partNumber, etag}   (50 MB parts, from 1)
//   POST {op:"complete", key, uploadId, parts, name, size, note, talking_point} -> {id, started}
//   POST {op:"abort", key, uploadId}
import { json, isOwner, startWorkflow } from "../../lib/shared.js";
import { put, now, newId } from "../../lib/db.js";

const safe = (s) => String(s || "clip").replace(/[^\w.\-]+/g, "_").slice(-80);

export async function onRequestPost({ request, env }) {
  if (!(await isOwner(request, env))) return json({ error: "not allowed" }, 403);
  const b = await request.json().catch(() => ({}));
  if (b.op === "create") {
    const key = `uploads/${now().slice(0, 10)}/${crypto.randomUUID().slice(0, 8)}-${safe(b.name)}`;
    const mp = await env.MEDIA.createMultipartUpload(key, { httpMetadata: { contentType: b.type || "video/mp4" } });
    return json({ key, uploadId: mp.uploadId });
  }
  if (!String(b.key || "").startsWith("uploads/") || !b.uploadId) return json({ error: "bad key" }, 400);
  const mp = env.MEDIA.resumeMultipartUpload(b.key, b.uploadId);
  if (b.op === "abort") {
    await mp.abort();
    return json({ ok: true });
  }
  if (b.op === "complete") {
    await mp.complete(b.parts);
    const id = newId();
    await put(env, "upload", id, {
      status: "uploaded", key: b.key, name: safe(b.name), size: b.size || 0,
      note: String(b.note || "").slice(0, 2000), talking_point: b.talking_point || null, at: now(),
    });
    let started = true;
    try {
      await startWorkflow(env, "edit-worker.yml");
    } catch {
      started = false;
    }
    return json({ id, started });
  }
  return json({ error: "unknown op" }, 400);
}

export async function onRequestPut({ request, env }) {
  if (!(await isOwner(request, env))) return json({ error: "not allowed" }, 403);
  const u = new URL(request.url);
  const key = u.searchParams.get("key"), uploadId = u.searchParams.get("uploadId"), part = Number(u.searchParams.get("part"));
  if (!key?.startsWith("uploads/") || !uploadId || !(part >= 1)) return json({ error: "bad part" }, 400);
  const p = await env.MEDIA.resumeMultipartUpload(key, uploadId).uploadPart(part, request.body);
  return json({ partNumber: p.partNumber, etag: p.etag });
}
