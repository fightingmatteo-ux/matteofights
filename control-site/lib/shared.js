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
// and Telegram stay stateless.
export async function dispatch(env, payload, via) {
  const r = await fetch(
    `https://api.github.com/repos/${env.GITHUB_REPO}/actions/workflows/control.yml/dispatches`,
    {
      method: "POST",
      headers: {
        authorization: `Bearer ${env.GITHUB_TOKEN}`,
        accept: "application/vnd.github+json",
        "user-agent": "matteofights-control",
      },
      body: JSON.stringify({ ref: "master", inputs: { payload: JSON.stringify(payload), via } }),
    },
  );
  if (r.status !== 204) throw new Error(`GitHub dispatch ${r.status}: ${await r.text()}`);
}

// Start any workflow without inputs (the edit worker after an upload or a note).
export async function startWorkflow(env, file) {
  const r = await fetch(`https://api.github.com/repos/${env.GITHUB_REPO}/actions/workflows/${file}/dispatches`, {
    method: "POST",
    headers: { authorization: `Bearer ${env.GITHUB_TOKEN}`, accept: "application/vnd.github+json", "user-agent": "matteofights-control" },
    body: JSON.stringify({ ref: "master" }),
  });
  if (r.status !== 204) throw new Error(`GitHub dispatch ${file} ${r.status}: ${await r.text()}`);
}

// Every /api call: the Access login must be Matteo. Bindings: DB = D1 "matteofights", MEDIA = R2 "matteofights-media".
export async function isOwner(request, env) {
  const email = await accessEmail(request, env);
  return !!email && email === (env.OWNER_EMAIL || "").toLowerCase();
}

// Start any workflow without inputs (the edit worker after an upload or a revision note).
export async function startWorkflow(env, file) {
  const r = await fetch(`https://api.github.com/repos/${env.GITHUB_REPO}/actions/workflows/${file}/dispatches`, {
    method: "POST",
    headers: { authorization: `Bearer ${env.GITHUB_TOKEN}`, accept: "application/vnd.github+json", "user-agent": "matteofights-control" },
    body: JSON.stringify({ ref: "master" }),
  });
  if (r.status !== 204) throw new Error(`GitHub dispatch ${file} ${r.status}: ${await r.text()}`);
}

// Every /api call that reads or changes things: the Access login must be Matteo.
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
