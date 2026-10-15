// Matteo Fights control center. Reads data.json (rebuilt on every push), sends decisions to /api/act.
"use strict";
const $ = (s, el = document) => el.querySelector(s);
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const NY = new Intl.DateTimeFormat("en-US", { timeZone: "America/New_York", weekday: "short", month: "short", day: "numeric", hour: "numeric", minute: "2-digit" });
const ny = (iso) => (iso ? NY.format(new Date(iso)) + " NY" : "–");
const n = (x) => (x == null ? "–" : x >= 10000 ? (x / 1000).toFixed(1) + "k" : x.toLocaleString("en-US"));
const ago = (iso) => {
  if (!iso) return "–";
  const m = Math.round((Date.now() - new Date(iso)) / 60000);
  return m < 60 ? `${m}m ago` : m < 1440 ? `${Math.round(m / 60)}h ago` : `${Math.round(m / 1440)}d ago`;
};
const STATE = { needs_yes: "needs your yes", scheduled: "scheduled", posted: "posted", failed: "failed" };

let D = null;
let tab = (() => { try { return localStorage.getItem("tab") || "home"; } catch { return "home"; } })();
let reelFilter = "all";
const sent = new Set(); // optimistic: actions sent this session

function toast(msg) {
  const t = $("#toast");
  t.textContent = msg; t.hidden = false;
  clearTimeout(toast.t); toast.t = setTimeout(() => (t.hidden = true), 3200);
}

async function act(body, key, okMsg) {
  try {
    const r = await fetch("api/act", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify(body) });
    if (!r.ok) throw new Error((await r.json().catch(() => ({}))).error || r.status);
    sent.add(key);
    toast(okMsg + " · updates here in about a minute");
    render();
  } catch (e) {
    toast("Didn't go through: " + e.message);
  }
}

// ---------------------------------------------------------------- views
function stat(v, l, cls = "") { return `<div class="card stat"><div class="v ${cls}">${v}</div><div class="l">${l}</div></div>`; }

function home() {
  const R = D.reels, lst = R.filter((r) => r.id.startsWith("lst-"));
  const needs = lst.filter((r) => r.state === "needs_yes").sort((a, b) => (a.time > b.time ? 1 : -1));
  const posted = R.filter((r) => r.state === "posted");
  const wins = posted.filter((r) => (r.metrics.vs_median_x || 0) >= 2);
  const openQ = D.questions.filter((q) => q.status === "open");
  const us = D.baseline.audience && D.baseline.audience.us_reach_pct;
  let h = "";
  if (needs.length) {
    const done = sent.has("approve_week");
    h += `<div class="card cta"><h3>Next week is ready</h3>
      <div class="strip">${needs.map((r) => (r.cover ? `<img src="${esc(r.cover)}" alt="${esc(r.hook)}" loading="lazy">` : "")).join("")}</div>
      <p><b>${needs.length} trial reels</b> from ${ny(needs[0].time)}. Approving is your yes for exactly these; they post automatically.</p>
      <button class="btn block" ${done ? "disabled" : ""} data-act="approve">${done ? "✓ Approval sent" : "✅ Approve the week"}</button>
      <div style="margin-top:8px"><button class="btn ghost block" data-goto="reels" data-filter="needs_yes">Look at them first</button></div></div>`;
  }
  h += `<h2>Right <span class="k">now</span></h2><div class="grid stats">
    ${stat(D.health.next_post ? ny(D.health.next_post).replace(" NY", "") : "–", "next post (New York)", "gold")}
    ${stat(lst.filter((r) => r.state === "scheduled").length, "scheduled")}
    ${stat(posted.length, "posted")}
    ${stat(wins.length, "winners (2x+)", wins.length ? "gold" : "")}
    ${stat(n(D.baseline.median_views), "your normal views")}
    ${stat(us != null ? us + "%" : "–", "US share of reach", "green")}
    ${stat(openQ.length, "questions for you", openQ.length ? "red" : "")}
    ${stat(D.health.failed.length, "failed posts", D.health.failed.length ? "red" : "")}
  </div>`;
  if (wins.length) {
    h += `<h2>Winners <span class="k">→ repost with a trending sound</span></h2><div class="grid reels">${wins.slice(0, 5).map(reel).join("")}</div>`;
  }
  const recent = posted.slice(0, 5);
  if (recent.length) h += `<h2>Latest <span class="k">posts</span></h2><div class="grid reels">${recent.map(reel).join("")}</div>`;
  return h;
}

function reel(r) {
  const m = r.metrics || {}, x = m.vs_median_x;
  const win = (x || 0) >= 2;
  const nums = m.views != null
    ? `<div class="nums"><span><b>${n(m.views)}</b> views</span>${x != null ? `<span><b>${x.toFixed(1)}x</b> normal</span>` : ""}
       <span><b>${n(m.shares)}</b> shares</span><span><b>${n(m.saves)}</b> saves</span>${m.follows != null ? `<span><b>${n(m.follows)}</b> follows</span>` : ""}</div>`
    : "";
  return `<div class="reel">
    <div class="img" style="${r.cover ? `background-image:url('${esc(r.cover)}')` : ""}">
      <span class="chip ${win ? "win" : r.state}">${win ? "winner" : STATE[r.state] || r.state}</span></div>
    <div class="body"><div class="hook">${esc(r.hook)}</div>
      <div class="meta"><span class="fmt">${esc(r.format)}</span> · ${r.state === "posted" ? "posted " + ago(r.posted_at) : ny(r.time)}</div>
      ${nums}
      ${r.review ? `<div class="meta">footage check ${r.review.score}/10</div>` : ""}
      ${r.error ? `<div class="meta warn">${esc(r.error).slice(0, 140)}</div>` : ""}
      ${r.permalink ? `<a class="meta" href="${esc(r.permalink)}" target="_blank" rel="noopener">open on Instagram ↗</a>` : ""}
    </div></div>`;
}

function reels() {
  const list = D.reels.filter((r) => reelFilter === "all" || r.state === reelFilter);
  const f = (k, l) => `<button data-filter="${k}" class="${reelFilter === k ? "on" : ""}">${l}</button>`;
  return `<h2>All <span class="k">reels</span></h2>
    <div class="filters">${f("all", "All")}${f("needs_yes", "Needs yes")}${f("scheduled", "Scheduled")}${f("posted", "Posted")}${f("failed", "Failed")}</div>
    ${list.length ? `<div class="grid reels">${list.map(reel).join("")}</div>` : `<div class="empty">Nothing here.</div>`}`;
}

function results() {
  const F = Object.entries(D.formats);
  if (!F.length) return `<h2>Results</h2><div class="empty">Numbers appear 72 hours after the first reels post. Claude logs them every morning.</div>`;
  const rows = F.map(([k, v]) => ({ k, ...v, avg: Math.round(v.views / v.reels), fpk: v.views ? (1000 * v.follows) / v.views : 0 }))
    .sort((a, b) => b.avg - a.avg);
  const max = Math.max(...rows.map((r) => r.avg)) || 1;
  const maxF = Math.max(...rows.map((r) => r.fpk)) || 1;
  return `<h2>What's <span class="k">working</span></h2>
    <div class="card"><h3>Average views per reel, by format</h3><div class="bars">
      ${rows.map((r) => `<div class="row"><span>${esc(r.k)}</span><div class="track"><div class="fill" style="width:${(100 * r.avg) / max}%"></div></div><span class="n">${n(r.avg)}</span></div>`).join("")}
    </div></div>
    <div class="card" style="margin-top:10px"><h3>Follows per 1,000 views (what grows the account)</h3><div class="bars">
      ${rows.map((r) => `<div class="row"><span>${esc(r.k)}</span><div class="track"><div class="fill gold" style="width:${(100 * r.fpk) / maxF}%"></div></div><span class="n">${r.fpk.toFixed(1)}</span></div>`).join("")}
    </div></div>
    <div class="card" style="margin-top:10px;overflow-x:auto"><table><tr><th>Format</th><th>Reels</th><th>Avg views</th><th>Shares</th><th>Saves</th><th>Winners</th></tr>
      ${rows.map((r) => `<tr><td class="fmt">${esc(r.k)}</td><td class="num">${r.reels}</td><td class="num">${n(r.avg)}</td><td class="num">${n(r.shares)}</td><td class="num">${n(r.saves)}</td><td class="num">${r.winners}</td></tr>`).join("")}
    </table></div>
    ${D.baseline.updated ? `<p class="meta" style="color:var(--muted);font-size:12px">Numbers from Instagram via Buzzfy, updated ${ago(D.baseline.updated)}.</p>` : ""}`;
}

function decide() {
  const open = D.questions.filter((q) => q.status === "open");
  const done = D.questions.filter((q) => q.status !== "open").slice(-8).reverse();
  let h = `<h2>Your <span class="k">calls</span></h2>`;
  h += open.length
    ? open.map((q) => `<div class="card q"><div class="text">${esc(q.question)}</div>${q.context ? `<div class="ctx">${esc(q.context)}</div>` : ""}
        ${sent.has("q:" + q.id) ? `<div class="ans">✓ Sent</div>` : `<div class="opts">${(q.options || []).map((o, k) => `<button class="btn" data-q="${esc(q.id)}" data-k="${k}">${esc(o)}</button>`).join("")}</div>`}</div>`).join("")
    : `<div class="card empty">No open questions. Claude asks here (and on Telegram) when it needs a call from you.</div>`;
  h += `<h2>Ideas <span class="k">for Claude</span></h2><div class="card">
    <textarea id="idea" placeholder="Anything: a hook idea, a format you saw, 'more nutrition', 'stop using clip X'…"></textarea>
    <div style="margin-top:10px"><button class="btn gold block" data-act="idea">Send to Claude</button></div>
    ${D.ideas.slice().reverse().map((i) => `<div class="idea"><div class="t">${esc(i.text)}</div><div class="m">${ago(i.at)} · via ${esc(i.via)}${i.status === "new" ? " · not picked up yet" : ""}</div>${i.reply ? `<div class="reply">${esc(i.reply)}</div>` : ""}</div>`).join("")}
  </div>`;
  if (done.length) h += `<h2>Decided</h2><div class="card">${done.map((q) => `<div class="idea"><div class="t">${esc(q.question)}</div><div class="m">→ <span style="color:var(--green)">${esc(q.answer)}</span> · ${ago(q.answered_at)} · ${esc(q.via || "")}</div></div>`).join("")}</div>`;
  return h;
}

function activity() {
  const H = D.health;
  return `<h2>System <span class="k">health</span></h2><div class="card kv">
      <span>Last post</span><span class="val">${ago(H.last_post)}</span>
      <span>Next post</span><span class="val">${ny(H.next_post)}</span>
      <span>Hooks written, waiting</span><span class="val ${H.hooks_ready < 14 ? "warn" : ""}">${H.hooks_ready}</span>
      <span>Clips in Drive</span><span class="val">${H.clips_live || "–"}</span>
      <span>Clips Claude has looked at</span><span class="val">${H.clips_catalogued}</span>
      <span>Usable clips</span><span class="val">${H.clips_usable}</span>
      <span>Failed posts</span><span class="val ${H.failed.length ? "warn" : ""}">${H.failed.length}</span>
    </div>
    <h2>What's <span class="k">happening</span></h2><div class="card log">
      ${D.log.length ? D.log.slice().reverse().map((e) => `<div class="e"><span class="when">${ago(e.at)}</span><span><span class="who">${esc(e.who)}</span> ${esc(e.text)}</span></div>`).join("") : `<div class="empty">Nothing logged yet.</div>`}
    </div>`;
}

const VIEWS = { home, reels, results, decide, activity };

function render() {
  if (!D) return;
  $("#view").innerHTML = VIEWS[tab]();
  document.querySelectorAll("#tabs button").forEach((b) => b.classList.toggle("on", b.dataset.tab === tab));
  const open = D.questions.filter((q) => q.status === "open" && !sent.has("q:" + q.id)).length;
  const badge = $("#badge"); badge.hidden = !open; badge.textContent = open;
  $("#fresh").innerHTML = `updated ${ago(D.generated_at)}`;
}

document.addEventListener("click", (ev) => {
  const t = ev.target.closest("button,a");
  if (!t) return;
  if (t.dataset.tab) { tab = t.dataset.tab; try { localStorage.setItem("tab", tab); } catch {} window.scrollTo(0, 0); return render(); }
  if (t.dataset.goto) { tab = t.dataset.goto; reelFilter = t.dataset.filter || "all"; return render(); }
  if (t.dataset.filter && tab === "reels") { reelFilter = t.dataset.filter; return render(); }
  if (t.dataset.act === "approve") {
    const ids = D.reels.filter((r) => r.state === "needs_yes" && r.id.startsWith("lst-")).map((r) => r.id);
    if (confirm(`Approve ${ids.length} reels? They'll post automatically at the New York times shown.`))
      act({ action: "approve_week", ids }, "approve_week", "✅ Week approved");
  }
  if (t.dataset.act === "idea") {
    const text = $("#idea").value.trim();
    if (!text) return toast("Type an idea first");
    act({ action: "idea", text }, "idea:" + text, "💡 Sent to Claude").then(() => { const el = $("#idea"); if (el) el.value = ""; });
  }
  if (t.dataset.q) {
    const q = D.questions.find((x) => x.id === t.dataset.q);
    act({ action: "answer", id: q.id, choice: q.options[+t.dataset.k] }, "q:" + q.id, "Answer sent");
  }
});

async function load() {
  try {
    const r = await fetch("data.json?" + Date.now(), { cache: "no-store" });
    D = await r.json();
    render();
  } catch {
    $("#view").innerHTML = `<div class="empty">Couldn't load the data. Pull to refresh.</div>`;
  }
}
load();
setInterval(load, 60000);
document.addEventListener("visibilitychange", () => document.visibilityState === "visible" && load());
