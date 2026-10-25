// End-to-end simulation of the ticker: fake D1, GitHub, Modal, Telegram. node sim.mjs
import assert from "node:assert/strict";
import worker from "./worker.bundle.mjs";

const docs = new Map(); // "kind|id" -> {data, updated_at}
const DB = {
  prepare(sql) {
    let args = [];
    const api = {
      bind(...a) { args = a; return api; },
      async first() { return (await api.all()).results[0] || null; },
      async all() {
        if (/kind = 'queue'/.test(sql)) return { results: [] };
        if (/kind = 'ops_pending'/.test(sql)) return { results: [...docs].filter(([k]) => k.startsWith("ops_pending|")).sort().map(([k, v]) => ({ id: k.split("|")[1], data: v.data })) };
        if (/SELECT data FROM docs WHERE kind = \? AND id = \?/.test(sql)) { const d = docs.get(`${args[0]}|${args[1]}`); return { results: d ? [{ data: d.data }] : [] }; }
        throw new Error("unexpected sql " + sql);
      },
      async run() {
        if (sql.startsWith("INSERT")) docs.set(`${args[0]}|${args[1]}`, { data: args[2] });
        else if (sql.startsWith("DELETE")) docs.delete(`${args[0]}|${args[1]}`);
        return {};
      },
    };
    return api;
  },
};
const doc = (k, i) => JSON.parse((docs.get(`${k}|${i}`) || { data: "{}" }).data);

let ghBlocked = true, modalStatus = 202, runs = [];
const calls = [];
globalThis.fetch = async (url, init = {}) => {
  const m = init.method || "GET";
  calls.push(`${m} ${url.replace("https://api.github.com/repos/o/r", "GH")}`);
  const res = (status, body = {}) => ({ status, json: async () => body, text: async () => JSON.stringify(body) });
  if (url.includes("api.telegram.org")) { tg.push(JSON.parse(init.body).text); return res(200); }
  if (url.startsWith("https://ops.test/dispatch")) { modal.push(JSON.parse(init.body)); return res(modalStatus); }
  if (url.endsWith("/dispatches")) {
    const wf = url.split("/workflows/")[1].split("/")[0];
    runs.unshift({ id: runs.length + 1, wf, created_at: new Date(now).toISOString(), status: "completed", conclusion: ghBlocked ? "failure" : "success" });
    return res(204);
  }
  if (url.includes("/runs?")) { const wf = url.split("/workflows/")[1].split("/")[0]; return res(200, { workflow_runs: runs.filter((r) => r.wf === wf) }); }
  if (url.includes("/jobs")) return res(200, { jobs: ghBlocked ? [{ steps: [], runner_name: null }] : [{ steps: [{ name: "a" }], runner_name: "gh" }] });
  if (/\/(enable|disable)$/.test(url)) { toggles.push(url.split("/").pop()); return res(204); }
  return res(404);
};
let tg = [], modal = [], toggles = [], now = 0;
const env = { DB, GITHUB_REPO: "o/r", GH_TOKEN: "x", OPS_URL: "https://ops.test", OPS_TOKEN: "t", TELEGRAM_BOT_TOKEN: "b", TELEGRAM_CHAT_ID: "c",
  POST_SLOTS: "12:31", XPOST_SLOTS: "" };
const tick = async (isoStr) => { now = Date.parse(isoStr); await worker.scheduled({ scheduledTime: now }, env); };

// 1. 12:31 New York (16:31Z, EDT) slot: GitHub mode, dispatch to GitHub, remembered as pending
await tick("2026-10-25T16:31:00Z");
assert.equal(doc("ops", "router").mode, "github");
assert.ok(calls.some((c) => c.includes("post-queue.yml/dispatches")));
assert.equal([...docs.keys()].filter((k) => k.startsWith("ops_pending")).length, 1);
assert.ok(doc("ops", "ticker").at, "heartbeat written");

// 2. +5 min: GitHub refused it (billing) -> sent to Modal, mode flips, GitHub crons paused, ONE Telegram
await tick("2026-10-25T16:36:00Z");
assert.deepEqual(modal.map((j) => j.workflow), ["post-queue.yml"]);
assert.equal(doc("ops", "router").mode, "modal");
assert.ok(toggles.length > 5 && toggles.every((t) => t === "disable"));
assert.equal(tg.length, 1);
assert.match(tg[0], /refused/);

// 3. Modal mode: the daily 20:10Z listicle cron runs on Modal with its schedule (no GitHub dispatch)
const before = calls.filter((c) => c.includes("/dispatches")).length;
await tick("2026-10-25T20:10:00Z");
assert.deepEqual(modal.at(-1), { workflow: "listicle-factory.yml", event: "schedule", schedule: "10 20 * * *" });
assert.equal(calls.filter((c) => c.includes("/dispatches")).length, before);

// 4. Scheduled job while Modal refuses (credits): alert, and NOT a fake manual GitHub run
modalStatus = 429; tg = [];
const ghBefore = calls.filter((c) => c.includes("/dispatches")).length;
await tick("2026-10-25T18:25:00Z");                 // health.yml "25 */6" fires at 18:25Z
assert.equal(modal.at(-1).workflow, "health.yml");
assert.equal(calls.filter((c) => c.includes("/dispatches")).length, ghBefore, "no fake manual GitHub run");
assert.equal(tg.length, 1);
assert.match(tg[0], /could not start anywhere/);
modalStatus = 202;

// 5. 6 h after the block: re-probe GitHub quietly; it works again -> one "back" message, crons re-enabled
ghBlocked = false; tg = []; toggles = [];
await tick("2026-10-25T22:40:00Z");                 // block expired (16:36 + 6 h): mode github, crons enabled
assert.equal(doc("ops", "router").mode, "github");
assert.ok(toggles.every((t) => t === "enable") && toggles.length > 5);
assert.equal(tg.length, 0, "no message for the quiet re-probe");
env.POST_SLOTS = "18:46";                           // 22:46Z = 18:46 NY: next post slot -> GitHub
await tick("2026-10-25T22:46:00Z");
await tick("2026-10-25T22:51:00Z");                 // pending check: started -> "back on GitHub"
assert.equal(tg.length, 1);
assert.match(tg[0], /run again/);
assert.equal(doc("ops", "router").block_reason, undefined);
console.log("simulation ok:", modal.length, "Modal dispatches,", calls.length, "fetches");
