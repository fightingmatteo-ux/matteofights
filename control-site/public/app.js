// Matteo Fights control center. Reads data.json (rebuilt on every push), sends decisions to /api/act.
"use strict";
const $ = (s, el = document) => el.querySelector(s);
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const TZ = "America/New_York";
const fmt = (o) => new Intl.DateTimeFormat("en-US", { timeZone: TZ, ...o });
const F = {
  time: fmt({ hour: "numeric", minute: "2-digit" }),
  wday: fmt({ weekday: "short" }),
  day: fmt({ weekday: "long", month: "short", day: "numeric" }),
  key: fmt({ year: "numeric", month: "2-digit", day: "2-digit" }),
  full: fmt({ weekday: "short", month: "short", day: "numeric", hour: "numeric", minute: "2-digit" }),
};
const t12 = (iso) => F.time.format(new Date(iso)).replace(" AM", "am").replace(" PM", "pm");
const dayKey = (d) => F.key.format(d);
const n = (x) => (x == null ? "–" : x >= 10000 ? (x / 1000).toFixed(x >= 100000 ? 0 : 1) + "k" : Math.round(x).toLocaleString("en-US"));
const ago = (iso) => {
  if (!iso) return "never";
  const m = Math.round((Date.now() - new Date(iso)) / 60000);
  return m < 1 ? "just now" : m < 60 ? `${m} min ago` : m < 1440 ? `${Math.round(m / 60)} h ago` : `${Math.round(m / 1440)} d ago`;
};
const until = (iso) => {
  const m = Math.round((new Date(iso) - Date.now()) / 60000);
  if (m <= 0) return "posting now";
  const h = Math.floor(m / 60), d = Math.floor(h / 24);
  return d >= 1 ? `in ${d} d ${h % 24} h` : h ? `in ${h} h ${m % 60} min` : `in ${m} min`;
};
const dayWord = (iso) => {
  const k = dayKey(new Date(iso)), today = dayKey(new Date()), tmr = dayKey(new Date(Date.now() + 864e5));
  return k === today ? "Tonight" : k === tmr ? "Tomorrow" : F.wday.format(new Date(iso));
};
// listicle hooks are written in caps for the video; read them in sentence case here
const calm = (h) => {
  h = String(h ?? "");
  if (h !== h.toUpperCase()) return h;
  return h.toLowerCase().replace(/^\w/, (c) => c.toUpperCase()).replace(/\bi\b/g, "I").replace(/\bi'/g, "I'").replace(/\b(\d+)x\b/g, "$1×");
};
const LABEL = { needs_yes: "Needs your yes", scheduled: "Scheduled", posted: "Posted", failed: "Failed", win: "Winner" };
const FORMAT = { listicle: "Listicle", statement: "Statement", iykyk: "IYKYK", builder: "Builder", lifestyle: "Lifestyle", "talking head": "Talking head" };

let D = null;
let tab = (() => { try { return localStorage.getItem("tab") || "home"; } catch { return "home"; } })();
let filter = "all";
const sent = new Set(); // decisions sent this session (the repo catches up within a minute)

const isWin = (r) => (r.metrics?.vs_median_x || 0) >= 2;
const stateOf = (r) => (isWin(r) ? "win" : r.state);
const cover = (r, cls = "") => (r.cover ? `<img class="${cls}" src="${esc(r.cover)}" alt="" loading="lazy" decoding="async">` : "");

function toast(msg) {
  const t = $("#toast");
  t.textContent = msg; t.hidden = false;
  clearTimeout(toast.t); toast.t = setTimeout(() => (t.hidden = true), 4000);
}

async function act(body, key, okMsg) {
  try {
    const r = await fetch("api/act", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify(body) });
    if (!r.ok) throw Object.assign(new Error((await r.json().catch(() => ({}))).error || `error ${r.status}`), { server: true });
    sent.add(key);
    toast(okMsg);
    render();
    return true;
  } catch (e) {
    toast(e.server ? `Not sent (${e.message}). Try again in a minute, or send it on Telegram.` : "Not sent: no connection. Try again when you're back online.");
    return false;
  }
}

// ---------------------------------------------------------------- home
function pending() {
  return D.reels.filter((r) => r.state === "needs_yes" && r.id.startsWith("lst-")).sort((a, b) => (a.time > b.time ? 1 : -1));
}

function decision() {
  const P = pending();
  if (!P.length) return "";
  const done = sent.has("approve_week");
  const first = new Date(P[0].time), last = new Date(P[P.length - 1].time);
  return `<section class="decision" aria-labelledby="d-h">
    <h2 class="h2" id="d-h">${P.length} reels need your yes</h2>
    <p class="lede">${F.day.format(first)} to ${F.day.format(last)}, at 6:30pm and 9:30pm New York. Approving is your yes for exactly these; they post on their own.</p>
    <div class="covers" role="list">${P.map((r) => `<button role="listitem" data-open="${esc(r.id)}" aria-label="${esc(calm(r.hook))}">${cover(r)}</button>`).join("")}</div>
    <div class="actions">
      <button class="btn hold wide" data-hold="approve" ${done ? "disabled" : ""} aria-describedby="hold-hint">${done ? "Approved" : `Hold to approve ${P.length} reels`}</button>
      <button class="btn line" data-goto="reels" data-filter="needs_yes">Check them first</button>
    </div>
    <p class="hint" id="hold-hint" style="margin-top:10px">${done ? "Sent. This page updates in about a minute." : "Press and hold for a second, so nothing goes out by accident."}</p>
  </section>`;
}

function poster() {
  const next = D.reels.filter((r) => r.state === "scheduled" && r.time && new Date(r.time) > Date.now() - 6e5)
    .sort((a, b) => (a.time > b.time ? 1 : -1))[0];
  if (!next) {
    return `<article class="poster empty"><div class="copy">
      <p class="label">Next post</p><p class="when">Nothing scheduled</p>
      <p class="quiet">${pending().length ? "Approve the week above and the next reel shows up here." : "The factory makes next week's reels on Sunday morning."}</p></div></article>`;
  }
  return `<article class="poster" aria-label="Next post">
    <div class="copy">
      <p class="label">Next post</p>
      <p class="when">${dayWord(next.time)}<br>${t12(next.time)}</p>
      <p class="count" data-until="${esc(next.time)}">${until(next.time)}</p>
      <p class="hookline">${esc(calm(next.hook))}</p>
      <p class="meta">${FORMAT[next.format] || esc(next.format)}, New York time</p>
    </div>
    <button class="shot" data-open="${esc(next.id)}" aria-label="Open this reel">${cover(next)}</button>
  </article>`;
}

function score() {
  const posted = D.reels.filter((r) => r.state === "posted");
  const wins = posted.filter(isWin).length;
  const us = D.baseline.audience?.us_reach_pct;
  return `<div class="score">
    <div><b>${n(D.baseline.median_views)}</b><span>views on a normal reel</span></div>
    <div><b>${us != null ? Math.round(us) + "%" : "–"}</b><span>of reach from the US</span></div>
    <div><b class="${wins ? "gold" : ""}">${wins}</b><span>${wins === 1 ? "winner" : "winners"} at 2× normal</span></div>
  </div>`;
}

function bout(r) {
  const s = stateOf(r), m = r.metrics || {};
  let line = FORMAT[r.format] || r.format;
  if (m.views != null) line += ` · <span class="x ${s === "win" ? "win" : ""}">${n(m.views)} views</span>${m.vs_median_x != null ? `, ${m.vs_median_x.toFixed(1)}× normal` : ""}`;
  else if (r.state === "posted") line += ` · numbers after 72 h`;
  return `<li class="bout"><button data-open="${esc(r.id)}">
    <span class="thumb">${cover(r)}</span>
    <time datetime="${esc(r.time)}">${r.time ? t12(r.time) : ""}</time>
    <span class="what"><p>${esc(calm(r.hook))}</p><p>${line}</p></span>
    <span class="tag ${s}">${LABEL[s]}</span>
  </button></li>`;
}

function fightCard() {
  const from = Date.now() - 3 * 864e5, to = Date.now() + 8 * 864e5;
  const R = D.reels.filter((r) => r.time && +new Date(r.time) > from && +new Date(r.time) < to).sort((a, b) => (a.time > b.time ? 1 : -1));
  if (!R.length) return `<p class="empty-note">No reels this week yet. The factory makes them every Sunday, and you approve them here.</p>`;
  const today = dayKey(new Date());
  let h = "", cur = "";
  for (const r of R) {
    const k = dayKey(new Date(r.time));
    if (k !== cur) {
      if (cur) h += `</ul>`;
      h += `<p class="day ${k === today ? "today" : ""}">${k === today ? "Today, " : ""}${F.day.format(new Date(r.time))}</p><ul class="bouts">`;
      cur = k;
    }
    h += bout(r);
  }
  return h + `</ul>`;
}

function home() {
  return `${decision()}<div class="home">
    <div>${poster()}${score()}</div>
    <section aria-labelledby="fc-h"><div class="card-head"><h2 class="h2" id="fc-h">This week</h2><span class="hint">New York time</span></div>${fightCard()}</section>
  </div>`;
}

// ---------------------------------------------------------------- reels
function tile(r) {
  const s = stateOf(r), m = r.metrics || {};
  const left = m.views != null ? `▶ ${n(m.views)}` : r.time ? `${F.wday.format(new Date(r.time))} ${t12(r.time)}` : "";
  const right = m.vs_median_x != null ? `${m.vs_median_x.toFixed(1)}×` : "";
  return `<button class="tile" data-open="${esc(r.id)}" aria-label="${esc(calm(r.hook))}, ${LABEL[s]}">
    ${r.cover ? cover(r) : `<span class="fallback">${esc(calm(r.hook))}</span>`}
    <span class="flag ${s}">${s === "failed" ? "Failed" : ""}</span>
    <span class="over"><span>${left}</span><span>${right}</span></span>
  </button>`;
}

function reels() {
  const counts = { all: D.reels.length };
  D.reels.forEach((r) => { counts[r.state] = (counts[r.state] || 0) + 1; });
  const list = D.reels.filter((r) => filter === "all" || r.state === filter);
  const b = (k, l) => (k === "all" || counts[k] ? `<button data-filter="${k}" aria-pressed="${filter === k}">${l}${k !== "all" ? ` ${counts[k]}` : ""}</button>` : "");
  return `<h1 class="h1" style="margin-bottom:16px">Reels</h1>
    <div class="seg" role="group" aria-label="Filter reels">${b("all", "All")}${b("needs_yes", "Needs your yes")}${b("scheduled", "Scheduled")}${b("posted", "Posted")}${b("failed", "Failed")}</div>
    ${list.length ? `<div class="grid">${list.map(tile).join("")}</div>` : `<p class="empty-note">No reels with this status.</p>`}`;
}

// ---------------------------------------------------------------- results
function results() {
  const rows = Object.entries(D.formats).map(([k, v]) => ({ k, ...v, avg: v.views / v.reels, fpk: v.views ? (1000 * v.follows) / v.views : 0 }))
    .sort((a, b) => b.avg - a.avg);
  if (!rows.length) {
    return `<h1 class="h1">Results</h1>
      <p class="empty-note" style="margin-top:24px">Results show up 72 hours after a reel posts. Claude pulls the numbers from Instagram every morning and compares each reel with your normal ${n(D.baseline.median_views)} views.</p>`;
  }
  const max = Math.max(...rows.map((r) => r.avg)) || 1, maxF = Math.max(...rows.map((r) => r.fpk)) || 1;
  const bars = (key, max, cls, val) => rows.slice().sort((a, b) => b[key] - a[key]).map((r, i) =>
    `<div class="row"><span class="k">${esc(FORMAT[r.k] || r.k)}</span><span class="track"><span class="fill ${i === 0 ? cls : ""}" style="width:${Math.max(2, (100 * r[key]) / max)}%"></span></span><span class="v">${val(r)}</span></div>`).join("");
  return `<h1 class="h1">Results</h1>
    <p class="lede" style="margin:12px 0 32px">Which formats earn views, and which turn views into followers. Your normal reel gets ${n(D.baseline.median_views)} views.</p>
    <div class="two">
      <section class="panel"><h2 class="h2">Views per reel</h2><div class="bars">${bars("avg", max, "top", (r) => n(r.avg))}</div></section>
      <section class="panel"><h2 class="h2">Follows per 1,000 views</h2><div class="bars">${bars("fpk", maxF, "gold", (r) => r.fpk.toFixed(1))}</div></section>
    </div>
    <section class="panel"><h2 class="h2">By format</h2><div class="scroll"><table>
      <thead><tr><th scope="col">Format</th><th scope="col">Reels</th><th scope="col">Views per reel</th><th scope="col">Shares</th><th scope="col">Saves</th><th scope="col">Winners</th></tr></thead>
      <tbody>${rows.map((r) => `<tr><td>${esc(FORMAT[r.k] || r.k)}</td><td>${r.reels}</td><td>${n(r.avg)}</td><td>${n(r.shares)}</td><td>${n(r.saves)}</td><td>${r.winners}</td></tr>`).join("")}</tbody>
    </table></div></section>
    ${D.baseline.updated ? `<p class="hint">From Instagram, updated ${ago(D.baseline.updated)}.</p>` : ""}`;
}

// ---------------------------------------------------------------- decide
function decide() {
  const open = D.questions.filter((q) => q.status === "open");
  const done = D.questions.filter((q) => q.status !== "open").slice(-8).reverse();
  let h = `<h1 class="h1">Your calls</h1><p class="lede" style="margin:12px 0 24px">Claude asks here and on Telegram when it needs a decision from you.</p>`;
  h += open.length
    ? open.map((q) => {
        const picked = [...sent].find((k) => k.startsWith(`q:${q.id}:`));
        return `<section class="q" aria-labelledby="q-${esc(q.id)}"><h3 id="q-${esc(q.id)}">${esc(q.question)}</h3>${q.context ? `<p class="ctx">${esc(q.context)}</p>` : ""}
          <div class="opts">${(q.options || []).map((o, k) => `<button class="opt ${picked === `q:${q.id}:${k}` ? "picked" : ""}" data-q="${esc(q.id)}" data-k="${k}" ${picked ? "disabled" : ""}>${esc(o)}</button>`).join("")}</div>
          ${picked ? `<p class="hint" style="margin-top:10px">Answer sent.</p>` : ""}</section>`;
      }).join("")
    : `<p class="empty-note">Nothing to decide right now.</p>`;
  h += `<section class="section" aria-labelledby="i-h"><h2 class="h2" id="i-h">Ideas for Claude</h2>
    <label class="field" for="idea">What should Claude try?</label>
    <textarea id="idea" placeholder="A hook you thought of, a format you saw, more nutrition, stop using a clip…"></textarea>
    <div class="actions" style="margin-top:12px"><button class="btn" data-act="idea">Send idea</button><span class="hint">Claude replies on its next morning check.</span></div>
    <div style="margin-top:16px">${D.ideas.slice().reverse().map((i) => `<div class="idea"><p class="t">${esc(i.text)}</p>
      <p class="m">${ago(i.at)}, from ${esc(i.via)}${i.status === "new" ? ". Waiting for Claude" : ""}</p>
      ${i.reply ? `<div class="reply"><b>Claude</b>${esc(i.reply)}</div>` : ""}</div>`).join("")}</div></section>`;
  if (done.length) {
    h += `<section class="section"><h2 class="h2">Decided</h2>${done.map((q) => `<div class="idea"><p class="t">${esc(q.question)}</p>
      <p class="m"><span class="answered">${esc(q.answer)}</span>, ${ago(q.answered_at)}${q.via ? ` from ${esc(q.via)}` : ""}</p></div>`).join("")}</section>`;
  }
  return h;
}

// ---------------------------------------------------------------- activity
function activity() {
  const H = D.health;
  const row = (k, v, warn) => `<dt>${k}</dt><dd class="${warn ? "warn" : ""}">${v}</dd>`;
  return `<h1 class="h1">Activity</h1>
    <div class="two" style="margin-top:24px">
      <section class="panel"><h2 class="h2">System</h2><dl class="facts">
        ${row("Last post", ago(H.last_post))}
        ${row("Next post", H.next_post ? F.full.format(new Date(H.next_post)) : "Nothing scheduled")}
        ${row("Hooks ready for next week", H.hooks_ready, H.hooks_ready < 14)}
        ${row("Clips in your Drive folder", H.clips_live || "–")}
        ${row("Clips Claude has watched", H.clips_catalogued)}
        ${row("Clips good enough to use", H.clips_usable)}
        ${row("Failed posts", H.failed.length, H.failed.length)}
      </dl></section>
      <section class="panel"><h2 class="h2">Log</h2>
        ${D.log.length ? `<ol class="log" reversed>${D.log.slice().reverse().map((e) => `<li><time datetime="${esc(e.at)}">${ago(e.at)}</time><p><span class="who ${e.who === "Matteo" ? "matteo" : ""}">${esc(e.who === "system" ? "System" : e.who)}</span> ${esc(e.text)}</p></li>`).join("")}</ol>`
          : `<p class="empty-note">Nothing logged yet. Approvals, posts, answers and Claude's changes show up here.</p>`}
      </section>
    </div>`;
}

// ---------------------------------------------------------------- reel sheet
function openSheet(id) {
  const r = D.reels.find((x) => x.id === id);
  if (!r) return;
  const s = stateOf(r), m = r.metrics || {};
  const stat = (l, v) => `<div><dt>${l}</dt><dd>${v}</dd></div>`;
  const when = r.state === "posted" && r.posted_at ? `Posted ${ago(r.posted_at)}` : r.time ? `${F.full.format(new Date(r.time))} New York` : "";
  const dlg = $("#sheet");
  dlg.innerHTML = `<div class="sheet">
    <div class="cover">${cover(r)}</div>
    <div><span class="tag ${s}">${LABEL[s]}</span><h2 id="sheet-title">${esc(calm(r.hook))}</h2>
      <p class="meta">${FORMAT[r.format] || esc(r.format)}${when ? `<br>${when}` : ""}${r.clip ? `<br>Clip: ${esc(r.clip)}` : ""}</p></div>
    ${m.views != null ? `<dl>${stat("Views", n(m.views))}${stat("vs normal", m.vs_median_x != null ? m.vs_median_x.toFixed(1) + "×" : "–")}${stat("Follows", n(m.follows))}${stat("Shares", n(m.shares))}${stat("Saves", n(m.saves))}${stat("Skip rate", m.skip_rate != null ? Math.round(m.skip_rate) + "%" : "–")}</dl>` : ""}
    ${s === "win" ? `<p class="err" style="color:var(--gold)">Winner. Repost it to your grid from the Instagram app with a trending sound; Claude sent suggestions on Telegram.</p>` : ""}
    ${r.error ? `<p class="err">Failed to post: ${esc(r.error).slice(0, 220)}. Claude looks at it on the next morning check.</p>` : ""}
    <div class="foot">${r.permalink ? `<a class="btn" href="${esc(r.permalink)}" target="_blank" rel="noopener">Open on Instagram</a>` : ""}<button class="btn line" data-close>Close</button></div>
  </div>`;
  dlg.showModal();
}
$("#sheet").addEventListener("click", (e) => { if (e.target === e.currentTarget || e.target.closest("[data-close]")) e.currentTarget.close(); });

// ---------------------------------------------------------------- render + events
const VIEWS = { home, reels, results, decide, activity };

function render() {
  if (!D) return;
  $("#view").innerHTML = VIEWS[tab]();
  document.querySelectorAll(".nav button").forEach((b) => (b.dataset.tab === tab ? b.setAttribute("aria-current", "page") : b.removeAttribute("aria-current")));
  const open = D.questions.filter((q) => q.status === "open" && ![...sent].some((k) => k.startsWith(`q:${q.id}:`))).length;
  const badge = $("#badge"); badge.hidden = !open; badge.textContent = open;
  badge.closest("button").setAttribute("aria-label", open ? `Decide, ${open} waiting` : "Decide");
  $("#fresh").textContent = `Updated ${ago(D.generated_at)}`;
}

function go(next, f) {
  tab = next; if (f) filter = f;
  try { localStorage.setItem("tab", tab); } catch {}
  render(); window.scrollTo(0, 0); $("#view").focus({ preventScroll: true });
}

document.addEventListener("click", (ev) => {
  const t = ev.target.closest("button,a");
  if (!t) return;
  if (t.dataset.tab) { ev.preventDefault(); return go(t.dataset.tab); }
  if (t.dataset.goto) return go(t.dataset.goto, t.dataset.filter);
  if (t.dataset.filter && tab === "reels") { filter = t.dataset.filter; return render(); }
  if (t.dataset.open) return openSheet(t.dataset.open);
  if (t.dataset.act === "idea") {
    const el = $("#idea"), text = el.value.trim();
    if (!text) { el.focus(); return toast("Write the idea first, then send it."); }
    t.disabled = true;
    act({ action: "idea", text }, "idea:" + text, "Idea sent. Claude replies on its next morning check.").then((ok) => { if (ok) { const e2 = $("#idea"); if (e2) e2.value = ""; } else t.disabled = false; });
  }
  if (t.dataset.q) {
    const q = D.questions.find((x) => x.id === t.dataset.q), k = +t.dataset.k;
    act({ action: "answer", id: q.id, choice: q.options[k] }, `q:${q.id}:${k}`, `Answer sent: ${q.options[k]}`);
  }
});

// press-and-hold to approve the week (pointer and keyboard)
const HOLD_MS = 1200;
let holdTimer = null;
function holdStart(b) {
  if (b.disabled || holdTimer) return;
  b.classList.add("holding"); b.textContent = "Keep holding…";
  holdTimer = setTimeout(() => {
    holdTimer = null; b.classList.remove("holding"); b.classList.add("done"); b.textContent = "Approving…";
    navigator.vibrate?.(30);
    const ids = pending().map((r) => r.id);
    act({ action: "approve_week", ids }, "approve_week", `Approved ${ids.length} reels. They post on their own.`).then((ok) => { if (!ok) render(); });
  }, HOLD_MS);
}
function holdStop(b) {
  if (!holdTimer) return;
  clearTimeout(holdTimer); holdTimer = null;
  b.classList.remove("holding"); b.textContent = `Hold to approve ${pending().length} reels`;
}
document.addEventListener("pointerdown", (e) => { const b = e.target.closest("[data-hold]"); if (b) { e.preventDefault(); holdStart(b); } });
["pointerup", "pointercancel", "pointerleave"].forEach((ev) => document.addEventListener(ev, (e) => { const b = $("[data-hold]"); if (b) holdStop(b); }, true));
document.addEventListener("keydown", (e) => { const b = e.target.closest?.("[data-hold]"); if (b && (e.key === " " || e.key === "Enter") && !e.repeat) { e.preventDefault(); holdStart(b); } });
document.addEventListener("keyup", (e) => { const b = e.target.closest?.("[data-hold]"); if (b && (e.key === " " || e.key === "Enter")) holdStop(b); });
document.addEventListener("contextmenu", (e) => { if (e.target.closest("[data-hold]")) e.preventDefault(); });

// live countdown on the poster
setInterval(() => document.querySelectorAll("[data-until]").forEach((el) => (el.textContent = until(el.dataset.until))), 30000);

async function load() {
  try {
    const r = await fetch("data.json?" + Date.now(), { cache: "no-store" });
    if (!r.ok) throw new Error(r.status);
    D = await r.json();
    if (!$("#sheet").open) render();
  } catch {
    if (!D) $("#view").innerHTML = `<p class="empty-note">Couldn't load the latest data. Check your connection; this page retries every minute.</p>`;
  }
}
load();
setInterval(load, 60000);
document.addEventListener("visibilitychange", () => document.visibilityState === "visible" && load());
