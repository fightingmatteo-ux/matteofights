// The timer AND router for every job (Cloudflare cron every 5 min, free). GitHub's own cron runs hours late.
//
// Each tick:
//  1. heartbeat (D1 ops/ticker): the Modal watchdog takes over the posting jobs if this goes quiet
//  2. checks GitHub dispatches that haven't been seen running (D1 ops_pending): a run GitHub refused (billing,
//     outage) is re-sent to the Modal backup at once and GitHub is marked blocked for 6 h (route.js)
//  3. picks the mode (route.js decideMode: GitHub unless it refuses runs or its month's minutes are >= 85%) and, on
//     a switch, turns GitHub's own scheduled backups off/on so the same job never runs on both, + Telegram
//  4. starts what's due: Post queue at listicle slots or when an approved item is due (D1 queue), Cross-post at
//     its slots, and in Modal mode every workflow cron (schedules.json, generated from the workflow files)
//
// Secrets: GH_TOKEN (fine-grained, repo matteofights: Actions read/write), OPS_URL + OPS_TOKEN (Modal
// matteofights-ops), TELEGRAM_BOT_TOKEN + TELEGRAM_CHAT_ID. Deploy: bash tools/ops/deploy.sh.
import { slotDue, queueDue } from "./due.js";
import { decideMode, classifyRun, dueSchedules, pendingAction, BLOCK_RECHECK_MS } from "./route.js";
import schedules from "./schedules.json";

const nyHM = (d) => new Intl.DateTimeFormat("en-GB", { timeZone: "America/New_York", hour: "2-digit", minute: "2-digit", hour12: false }).format(d);
const iso = (ms) => new Date(ms).toISOString().slice(0, 19) + "Z";
// Their GitHub crons are backups for the ticker's own slots: in Modal mode the slots cover them.
const SLOT_DRIVEN = ["post-queue.yml", "crosspost.yml"];

const gh = (env, path, init = {}) => fetch(`https://api.github.com/repos/${env.GITHUB_REPO}${path}`, {
  ...init,
  headers: { authorization: `Bearer ${env.GH_TOKEN}`, accept: "application/vnd.github+json", "user-agent": "matteo-ticker" },
});

async function getDoc(env, kind, id) {
  const r = await env.DB.prepare("SELECT data FROM docs WHERE kind = ? AND id = ?").bind(kind, id).first();
  return r ? JSON.parse(r.data) : {};
}
const putDoc = (env, kind, id, data) => env.DB.prepare(
  "INSERT INTO docs (kind, id, data) VALUES (?, ?, ?) ON CONFLICT (kind, id) DO UPDATE SET data = excluded.data, " +
  "updated_at = strftime('%Y-%m-%dT%H:%M:%SZ','now')").bind(kind, id, JSON.stringify(data)).run();
const delDoc = (env, kind, id) => env.DB.prepare("DELETE FROM docs WHERE kind = ? AND id = ?").bind(kind, id).run();

async function telegram(env, text) {
  if (!env.TELEGRAM_BOT_TOKEN || !env.TELEGRAM_CHAT_ID) return;
  await fetch(`https://api.telegram.org/bot${env.TELEGRAM_BOT_TOKEN}/sendMessage`, {
    method: "POST", headers: { "content-type": "application/json" },
    body: JSON.stringify({ chat_id: env.TELEGRAM_CHAT_ID, text }),
  }).catch(() => {});
}

async function toModal(env, job) {
  if (!env.OPS_URL) return "modal: not configured";
  const r = await fetch(`${env.OPS_URL}/dispatch`, {
    method: "POST", headers: { authorization: `Bearer ${env.OPS_TOKEN}`, "content-type": "application/json" },
    body: JSON.stringify(job),
  }).catch((e) => ({ status: 0, text: async () => String(e) }));
  return r.status === 202 ? "modal: 202" : `modal: ${r.status} ${(await r.text()).slice(0, 120)}`;
}

async function toGithub(env, job, nowMs) {
  const body = { ref: "master" };
  if (job.inputs && Object.keys(job.inputs).length) body.inputs = job.inputs;
  const r = await gh(env, `/actions/workflows/${job.workflow}/dispatches`, { method: "POST", body: JSON.stringify(body) });
  if (r.status !== 204) return `github: ${r.status}`;
  // remember it: if GitHub never actually starts it, the next ticks hand it to Modal
  await putDoc(env, "ops_pending", `${job.workflow}@${nowMs}`, { ...job, at: iso(nowMs) });
  return "github: 204";
}

// The one way anything gets started. Falls over to the other runner when the first one says no.
export async function runJob(env, job, mode, nowMs) {
  if (mode === "github") {
    const g = await toGithub(env, job, nowMs);
    if (g === "github: 204") return g;
    return `${g} -> ${await toModal(env, job)}`;
  }
  const m = await toModal(env, job);
  if (m === "modal: 202") return m;
  // a cron job can't be faked as a manual GitHub run (it would run with the manual defaults): alert instead
  const g = job.event === "schedule" ? "github: not tried (scheduled job)" : await toGithub(env, job, nowMs);
  if (g !== "github: 204") await telegram(env, `⚠️ ${job.workflow} could not start anywhere (${m}; ${g}). Check Modal credits / GitHub billing.`);
  return `${m} -> ${g}`;
}

async function checkPending(env, nowMs, router) {
  const { results } = await env.DB.prepare("SELECT id, data FROM docs WHERE kind = 'ops_pending' ORDER BY id LIMIT 6").all();
  const out = [];
  for (const row of results) {
    const p = JSON.parse(row.data);
    const act = pendingAction(nowMs, p);
    if (act === "wait") continue;
    let verdict = "missing";
    if (act === "check") {
      const runs = await (await gh(env, `/actions/workflows/${p.workflow}/runs?per_page=3&event=workflow_dispatch`)).json();
      const run = (runs.workflow_runs || []).find((r) => Date.parse(r.created_at) >= Date.parse(p.at) - 60e3);
      const jobs = run && run.status === "completed" ? await (await gh(env, `/actions/runs/${run.id}/jobs`)).json() : null;
      verdict = classifyRun(run, jobs);
      if (verdict === "missing") continue;   // not visible yet; look again next tick (gives up after 15 min)
    }
    await delDoc(env, "ops_pending", row.id);
    if (verdict === "started") {
      if (router.block_reason) {   // the 6-hourly re-check found GitHub working again
        await telegram(env, "✅ GitHub Actions run again. Jobs are back on GitHub; Modal stays as the backup.");
        delete router.block_reason;
      }
      continue;
    }
    // GitHub refused (or never showed it): block GitHub for a while and run it on Modal now
    router.gh_blocked_until = iso(nowMs + BLOCK_RECHECK_MS);
    if (!router.block_reason) {   // say it once, not on every 6-hourly re-check
      await telegram(env, `⚠️ GitHub refused to run ${p.workflow} (${verdict}). Sent it to the Modal backup; GitHub gets re-checked every 6 h.`);
    }
    router.block_reason = verdict === "blocked" ? "GitHub refused to start the run (billing / minutes)" : "GitHub never started the run";
    const { at, ...job } = p;
    out.push(`${p.workflow} ${verdict} on GitHub -> ${await toModal(env, job)}`);
  }
  return out;
}

async function setGithubSchedules(env, enabled) {
  const verb = enabled ? "enable" : "disable";
  const res = [];
  for (const wf of Object.keys(schedules)) {
    const r = await gh(env, `/actions/workflows/${wf}/${verb}`, { method: "PUT" });
    res.push(r.status === 204 ? 0 : 1);
  }
  return res.reduce((a, b) => a + b, 0); // number that failed
}

export default {
  async scheduled(event, env) {
    const now = event.scheduledTime;
    const out = [];
    await putDoc(env, "ops", "ticker", { at: iso(now) }).catch(() => {});
    let router = {}, budget = {}, qdue = false;
    try {
      router = await getDoc(env, "ops", "router");
      budget = await getDoc(env, "ops", "budget");
      const { results } = await env.DB.prepare("SELECT data FROM docs WHERE kind = 'queue'").all();
      qdue = queueDue(now, results.map((r) => JSON.parse(r.data)));
    } catch (e) {
      console.log("D1 read failed, slots only:", String(e));
    }

    try { out.push(...await checkPending(env, now, router)); } catch (e) { out.push(`pending check failed: ${e}`); }

    const { mode, reason } = decideMode(now, router, budget);
    if (mode !== (router.mode || "github")) {
      const failed = await setGithubSchedules(env, mode === "github");
      // block-driven switches are announced by checkPending (once); budget-driven ones here
      if (!router.block_reason) {
        await telegram(env, mode === "modal"
          ? `🔁 Jobs switched to the Modal backup: ${reason}. Posting continues; GitHub's own timers are paused so nothing runs twice.`
          : `✅ Jobs back on GitHub: ${reason}. Modal stays as the backup.`);
      }
      out.push(`mode ${router.mode || "github"} -> ${mode} (${reason}; ${failed} workflow toggles failed)`);
      router.mode = mode;
      router.since = iso(now);
    }
    router.mode = mode;
    router.reason = reason;
    await putDoc(env, "ops", "router", router).catch((e) => out.push(`router save failed: ${e}`));

    if (slotDue(now, env.POST_SLOTS) || qdue) out.push(await runJob(env, { workflow: "post-queue.yml" }, mode, now));
    if (slotDue(now, env.XPOST_SLOTS)) out.push(await runJob(env, { workflow: "crosspost.yml" }, mode, now));
    if (mode === "modal") {
      for (const { wf, cron } of dueSchedules(schedules, now, SLOT_DRIVEN)) {
        out.push(`${wf} (${cron}): ${await runJob(env, { workflow: wf, event: "schedule", schedule: cron }, mode, now)}`);
      }
    }
    console.log(nyHM(new Date(now)), mode, out.join(" | ") || "nothing due");
  },
};
