// Where each job runs: GitHub Actions (primary) or the Modal backup (tools/ops/modal_ops.py). Pure functions,
// tested by route.test.js (node --test tools/ticker/). worker.js does the I/O.
//
// D1 docs (table docs, kind "ops"): router {mode, reason, since, gh_blocked_until}, budget (tools/ops/budget.py),
// ticker {at} (heartbeat the Modal watchdog reads). Kind "ops_pending": one doc per GitHub dispatch not yet seen
// running ({wf, inputs, event, schedule, at, via}).

export const GH_BUDGET_SWITCH = 85;          // % of GitHub's monthly minutes: above this, timed jobs go to Modal
export const BLOCK_RECHECK_MS = 6 * 3600e3;  // after GitHub refuses a run, try it again this much later
export const PENDING_CHECK_AFTER_MS = 3 * 60e3;
export const PENDING_GIVE_UP_MS = 15 * 60e3; // no run visible by then: GitHub is down, run it on Modal

const month = (ms) => new Date(ms).toISOString().slice(0, 7);

export function decideMode(nowMs, router = {}, budget = {}) {
  if (router.gh_blocked_until && nowMs < Date.parse(router.gh_blocked_until)) {
    return { mode: "modal", reason: "GitHub refused to start runs (billing or outage)" };
  }
  if (budget.month === month(nowMs) && Number(budget.github_pct) >= GH_BUDGET_SWITCH) {
    return { mode: "modal", reason: `GitHub minutes at ${budget.github_pct}% this month` };
  }
  return { mode: "github", reason: "GitHub has minutes left" };
}

// A GitHub run that never started (spending limit, billing): completed, failure, and its job ran no steps.
export function classifyRun(run, jobs) {
  if (!run) return "missing";
  if (run.status !== "completed") return "started";
  const list = (jobs && jobs.jobs) || [];
  const ranNothing = list.length === 0 || list.every((j) => !(j.steps || []).length && !j.runner_name);
  return run.conclusion === "failure" && ranNothing ? "blocked" : "started";
}

// ---- 5-field cron (UTC), the subset GitHub accepts: numbers, *, */n, a-b, a-b/n, lists.
function fieldMatches(spec, value, min, max) {
  return spec.split(",").some((part) => {
    let [range, step] = part.split("/");
    step = step ? Number(step) : 1;
    let lo = min, hi = max;
    if (range !== "*") {
      const [a, b] = range.split("-").map(Number);
      lo = a; hi = b === undefined ? (step > 1 ? max : a) : b;
    }
    return value >= lo && value <= hi && (value - lo) % step === 0;
  });
}

export function cronMatches(cron, date) {
  const [mi, h, dom, mon, dow] = cron.trim().split(/\s+/);
  const d = new Date(date);
  const domOk = fieldMatches(dom, d.getUTCDate(), 1, 31);
  const dowOk = fieldMatches(dow.replace(/\b7\b/g, "0"), d.getUTCDay(), 0, 6);
  // cron rule: if both day fields are restricted, either may match
  const dayOk = dom !== "*" && dow !== "*" ? domOk || dowOk : domOk && dowOk;
  return fieldMatches(mi, d.getUTCMinutes(), 0, 59) && fieldMatches(h, d.getUTCHours(), 0, 23) &&
    fieldMatches(mon, d.getUTCMonth() + 1, 1, 12) && dayOk;
}

// Every (workflow, cron) that fired in the 5 minutes up to nowMs. schedules = {"file.yml": ["cron", ...]}.
export function dueSchedules(schedules, nowMs, skip = [], windowMin = 5) {
  const out = [];
  const end = Math.floor(nowMs / 60e3) * 60e3;
  for (const [wf, crons] of Object.entries(schedules || {})) {
    if (skip.includes(wf)) continue;
    for (const cron of crons) {
      for (let k = 0; k < windowMin; k++) {
        if (cronMatches(cron, end - k * 60e3)) { out.push({ wf, cron }); break; }
      }
    }
  }
  return out;
}

// Which pending GitHub dispatches to look at this tick, and which to give up on (send to Modal).
export function pendingAction(nowMs, p) {
  const age = nowMs - Date.parse(p.at);
  if (age < PENDING_CHECK_AFTER_MS) return "wait";
  if (age > PENDING_GIVE_UP_MS) return "give-up";
  return "check";
}
