// GET /api/media?asset=<file>.mp4: any reel's video, same-origin so the player can seek it and draw its frames into a
// canvas (annotations). R2 renders/<asset> first (kept 21 days), else the public "media" GitHub release (proxied,
// Range forwarded). Owner only.
import { json, isOwner } from "../../lib/shared.js";

const SAFE = /^[\w.\-]+\.(mp4|mov|webm)$/i;

export async function onRequestGet({ request, env }) {
  if (!(await isOwner(request, env))) return json({ error: "not allowed" }, 403);
  const asset = new URL(request.url).searchParams.get("asset") || "";
  if (!SAFE.test(asset)) return json({ error: "bad asset" }, 400);
  const range = request.headers.get("range");

  const head = await env.MEDIA.head(`renders/${asset}`);
  if (head) {
    const size = head.size;
    let opts = {}, status = 200, headers = { "content-type": "video/mp4", "accept-ranges": "bytes", "cache-control": "private, max-age=3600" };
    const m = range && /bytes=(\d*)-(\d*)/.exec(range);
    if (m) {
      const start = m[1] ? +m[1] : size - +m[2];
      const end = m[1] && m[2] ? Math.min(+m[2], size - 1) : size - 1;
      opts = { range: { offset: start, length: end - start + 1 } };
      status = 206;
      headers["content-range"] = `bytes ${start}-${end}/${size}`;
      headers["content-length"] = String(end - start + 1);
    } else headers["content-length"] = String(size);
    const obj = await env.MEDIA.get(`renders/${asset}`, opts);
    return new Response(obj.body, { status, headers });
  }

  const repo = env.GITHUB_REPO || "fightingmatteo-ux/matteofights";
  const r = await fetch(`https://github.com/${repo}/releases/download/media/${asset}`, { headers: range ? { range } : {}, redirect: "follow" });
  if (!r.ok && r.status !== 206) return json({ error: "video not found" }, 404);
  const h = new Headers({ "content-type": "video/mp4", "accept-ranges": "bytes", "cache-control": "private, max-age=3600" });
  for (const k of ["content-length", "content-range"]) if (r.headers.get(k)) h.set(k, r.headers.get(k));
  return new Response(r.body, { status: r.status, headers: h });
}
