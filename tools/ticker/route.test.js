import { test } from "node:test";
import assert from "node:assert/strict";
import { decideMode, classifyRun, cronMatches, dueSchedules, pendingAction } from "./route.js";

const t = (iso) => Date.parse(iso);

test("mode: GitHub by default, Modal when it refuses runs or its minutes are low", () => {
  const now = t("2026-10-25T10:00:00Z");
  assert.equal(decideMode(now).mode, "github");
  assert.equal(decideMode(now, { gh_blocked_until: "2026-10-25T12:00:00Z" }).mode, "modal");
  assert.equal(decideMode(now, { gh_blocked_until: "2026-10-25T09:00:00Z" }).mode, "github");   // re-probe GitHub
  assert.equal(decideMode(now, {}, { month: "2026-10", github_pct: 86 }).mode, "modal");
  assert.equal(decideMode(now, {}, { month: "2026-10", github_pct: 40 }).mode, "github");
  assert.equal(decideMode(now, {}, { month: "2026-09", github_pct: 99 }).mode, "github");    // last month's numbers
});

test("a billing-blocked run is told apart from a normal failure", () => {
  const blocked = { status: "completed", conclusion: "failure" };
  assert.equal(classifyRun(blocked, { jobs: [{ steps: [], runner_name: null }] }), "blocked");
  assert.equal(classifyRun(blocked, { jobs: [] }), "blocked");
  assert.equal(classifyRun(blocked, { jobs: [{ steps: [{ name: "x" }], runner_name: "GitHub Actions 3" }] }), "started");
  assert.equal(classifyRun({ status: "in_progress" }, null), "started");
  assert.equal(classifyRun({ status: "completed", conclusion: "success" }, { jobs: [] }), "started");
  assert.equal(classifyRun(undefined), "missing");
});

test("cron matching (UTC) like GitHub", () => {
  assert.equal(cronMatches("10 20 * * *", t("2026-10-25T20:10:00Z")), true);
  assert.equal(cronMatches("10 20 * * *", t("2026-10-25T20:11:00Z")), false);
  assert.equal(cronMatches("5 */3 * * *", t("2026-10-25T09:05:00Z")), true);
  assert.equal(cronMatches("5 */3 * * *", t("2026-10-25T10:05:00Z")), false);
  assert.equal(cronMatches("40 9 * * 0", t("2026-10-25T09:40:00Z")), true);   // 2026-10-25 is a Sunday
  assert.equal(cronMatches("40 9 * * 0", t("2026-10-26T09:40:00Z")), false);
  assert.equal(cronMatches("0 7 * * 6", t("2026-10-31T07:00:00Z")), true);    // Saturday
  assert.equal(cronMatches("20 6 * * 1", t("2026-10-26T06:20:00Z")), true);   // Monday
  assert.equal(cronMatches("0 9-17/4 * * 1-5", t("2026-10-26T13:00:00Z")), true);
});

test("a schedule fires on exactly one 5-minute tick", () => {
  const s = { "state-export.yml": ["17 4 * * *"], "post-queue.yml": ["5 */3 * * *"] };
  const fired = [];
  for (let m = 0; m < 24 * 60; m += 5) {
    const now = t("2026-10-25T00:00:00Z") + m * 60e3;
    for (const d of dueSchedules(s, now, ["post-queue.yml"])) fired.push(d.wf);
  }
  assert.deepEqual(fired, ["state-export.yml"]);    // once a day, and the skipped workflow never
});

test("pending dispatches: wait, then check, then give up to Modal", () => {
  const at = "2026-10-25T10:00:00Z";
  assert.equal(pendingAction(t("2026-10-25T10:02:00Z"), { at }), "wait");
  assert.equal(pendingAction(t("2026-10-25T10:05:00Z"), { at }), "check");
  assert.equal(pendingAction(t("2026-10-25T10:16:00Z"), { at }), "give-up");
});
