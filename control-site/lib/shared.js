// Shared by the Pages Functions. Secrets live in Cloudflare (Settings > Environment variables), never in the repo.
//   GITHUB_TOKEN      fine-grained token, this repo only, "Actions: read and write" (starts the Control workflow)
//   GITHUB_REPO       fightingmatteo-ux/matteofights
//   OWNER_EMAIL       the only email allowed to act on the dashboard
//   ACCESS_TEAM       Cloudflare Access team name (<team>.cloudflareaccess.com)
//   ACCESS_AUD        the Access application's AUD tag
//   TELEGRAM_BOT_TOKEN, TELEGRAM_WEBHOOK_SECRET, TELEGRAM_CHAT_ID
// Bindings (Pages project): DB = D1 "matteofights", MEDIA = R2 "matteofights-media" (tools/cloud/setup.sh).

export function json(body, status = 200) {
  return new Response(JSON.stringify(body), { status, headers: { "content-type": "application/json" } });
}

// Start the Control workflow with one action. GitHub does the work (and commits), so the site
// and Telegram stay stateless. When the ticker has moved jobs to the Modal backup (D1 ops/router mode "modal",
// tools/ticker/route.js) or GitHub says no, the same workflow runs on Modal instead (secrets OPS_URL, OPS_TOKEN).
// A GitHub dispatch is remembered in D1 ops_pending, so the ticker re-sends it to Modal if GitHub never starts it.
async function routerMode(env) {
  try {
    const r = await env.DB.prepare("SELECT data FROM docs WHERE kind = 'ops' AND id = 'router'").first();
    return r ? JSON.parse(r.data).mode || "github" : "github";
  } catch { return "github"; }
}

async function toModal(env, job) {
  if (!env.OPS_URL) return `Modal backup not configured`;
  const r = await fetch(`${env.OPS_URL}/dispatch`, {
    method: "POST", headers: { authorization: `Bearer ${env.OPS_TOKEN}`, "content-type": "application/json" },
    body: JSON.stringify(job),
  });
  return r.status === 202 ? "" : `Modal ${r.status}: ${(await r.text()).slice(0, 200)}`;
}

async function toGithub(env, job) {
  const body = { ref: "master" };
  if (job.inputs) body.inputs = job.inputs;
  const r = await fetch(`https://api.github.com/repos/${env.GITHUB_REPO}/actions/workflows/${job.workflow}/dispatches`, {
    method: "POST",
    headers: { authorization: `Bearer ${env.GITHUB_TOKEN}`, accept: "application/vnd.github+json", "user-agent": "matteofights-control" },
    body: JSON.stringify(body),
  });
  if (r.status !== 204) return `GitHub ${r.status}: ${(await r.text()).slice(0, 200)}`;
  if (["edit-worker.yml", "talking-points.yml"].includes(job.workflow)) return "";  // GitHub-only: no Modal retry
  const at = new Date().toISOString().slice(0, 19) + "Z";
  await env.DB.prepare("INSERT INTO docs (kind, id, data) VALUES ('ops_pending', ?, ?) ON CONFLICT (kind, id) DO NOTHING")
    .bind(`${job.workflow}@${Date.now()}`, JSON.stringify({ ...job, at })).run().catch(() => {});
  return "";
}

async function runJob(env, job) {
  const order = (await routerMode(env)) === "modal" ? [toModal, toGithub] : [toGithub, toModal];
  const first = await order[0](env, job);
  if (!first) return;
  const second = await order[1](env, job);
  if (second) throw new Error(`${first}; ${second}`);
}

export async function dispatch(env, payload, via) {
  await runJob(env, { workflow: "control.yml", inputs: { payload: JSON.stringify(payload), via } });
}

// Start any workflow without inputs (the edit worker after an upload or a note). The edit worker uses
// claude-code-action, which only runs on GitHub: while jobs are on the Modal backup it waits (the upload is kept
// in D1, so nothing is lost; start it from the dashboard once GitHub is back).
export async function startWorkflow(env, file) {
  if (file === "edit-worker.yml" && (await routerMode(env)) === "modal") {
    throw new Error("The edit worker only runs on GitHub, which is paused right now (minutes or billing). Your upload is saved.");
  }
  const err = await toGithub(env, { workflow: file });
  if (err) throw new Error(`dispatch ${file}: ${err}`);
}

// Every /api call: the Access login must be Matteo. Bindings: DB = D1 "matteofights", MEDIA = R2 "matteofights-media".
export async function isOwner(request, env) {
  const email = await accessEmail(request, env);
  return !!email && email === (env.OWNER_EMAIL || "").toLowerCase();
}

// Verify the Cloudflare Access login (RS256 JWT) instead of trusting a header, so the API is safe
// even if the Access rule were ever removed by mistake.
let certs = null;
export async function accessEmail(request, env) {
  const token = request.headers.get("cf-access-jwt-assertion");
  if (!token) return null;
  const [h, p, s] = token.split(".");
  const dec = (x) => JSON.parse(atob(x.replace(/-/g, "+").replace(/_/g, "/")));
  const header = dec(h), claims = dec(p);
  if (!certs) {
    const r = await fetch(`https://${env.ACCESS_TEAM}.cloudflareaccess.com/cdn-cgi/access/certs`);
    certs = (await r.json()).keys;
  }
  const jwk = certs.find((k) => k.kid === header.kid);
  if (!jwk) return null;
  const key = await crypto.subtle.importKey("jwk", jwk, { name: "RSASSA-PKCS1-v1_5", hash: "SHA-256" }, false, ["verify"]);
  const sig = Uint8Array.from(atob(s.replace(/-/g, "+").replace(/_/g, "/")), (c) => c.charCodeAt(0));
  const ok = await crypto.subtle.verify("RSASSA-PKCS1-v1_5", key, sig, new TextEncoder().encode(`${h}.${p}`));
  const aud = Array.isArray(claims.aud) ? claims.aud : [claims.aud];
  if (!ok || !aud.includes(env.ACCESS_AUD) || claims.exp * 1000 < Date.now()) return null;
  return (claims.email || "").toLowerCase();
}

export async function tg(env, method, body) {
  const r = await fetch(`https://api.telegram.org/bot${env.TELEGRAM_BOT_TOKEN}/${method}`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(body),
  });
  return r.json();
}
