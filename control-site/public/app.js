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
  short: fmt({ weekday: "short", month: "short", day: "numeric" }),
  key: new Intl.DateTimeFormat("en-CA", { timeZone: TZ, year: "numeric", month: "2-digit", day: "2-digit" }), // YYYY-MM-DD, sortable
  full: fmt({ weekday: "short", month: "short", day: "numeric", hour: "numeric", minute: "2-digit" }),
};
const t12 = (iso) => F.time.format(new Date(iso)).replace(" AM", "am").replace(" PM", "pm");
const dayKey = (d) => F.key.format(d);
const n = (x) => (x == null ? "n/a" : x >= 10000 ? (x / 1000).toFixed(x >= 100000 ? 0 : 1) + "k" : Math.round(x).toLocaleString("en-US"));
const ago = (iso) => {
  if (!iso) return "never";
  const m = Math.round((Date.now() - new Date(iso)) / 60000);
  return m < 1 ? "just now" : m < 60 ? `${m} min ago` : m < 1440 ? `${Math.round(m / 60)} h ago` : `${Math.round(m / 1440)} d ago`;
};
const minsUntil = (iso) => Math.max(0, Math.round((new Date(iso) - Date.now()) / 60000));
const until = (iso) => {
  const m = minsUntil(iso);
  if (m <= 0) return "posting now";
  const h = Math.floor(m / 60), d = Math.floor(h / 24);
  return d >= 1 ? `in ${d} d ${h % 24} h` : h ? `in ${h} h ${m % 60} min` : `in ${m} min`;
};
const hourNY = fmt({ hour: "numeric", hourCycle: "h23" });
const dayWord = (iso) => {
  const d = new Date(iso), k = dayKey(d), today = dayKey(new Date()), tmr = dayKey(new Date(Date.now() + 864e5));
  return k === today ? (+hourNY.format(d) >= 17 ? "Tonight" : "Today") : k === tmr ? "Tomorrow" : F.wday.format(d);
};
// listicle hooks are written in caps for the video; read them in sentence case here
const calm = (h) => {
  h = String(h ?? "");
  if (h !== h.toUpperCase()) return h;
  return h.toLowerCase().replace(/^\w/, (c) => c.toUpperCase()).replace(/\bi\b/g, "I").replace(/\bi'/g, "I'").replace(/\b(\d+)x\b/g, "$1×");
};
const LABEL = { needs_yes: "Needs yes", scheduled: "Set", posted: "Posted", failed: "Failed", win: "Winner" };
const FORMAT = { listicle: "Listicle", statement: "Statement", iykyk: "IYKYK", builder: "Builder", lifestyle: "Lifestyle", "talking head": "Talking head" };
const fmtName = (f) => FORMAT[f] || esc(f);

let D = null;
let tab = (() => { try { return localStorage.getItem("tab") || "home"; } catch { return "home"; } })();
let filter = "all";
let by = "views"; // results ranking: views per reel or follows per 1k
const sent = new Set(); // decisions sent this session (the repo catches up within a minute)
let pa = null; // pending answer, waiting out its undo window: {id, k, choice, left, timer}

const isWin = (r) => (r.metrics?.vs_median_x || 0) >= 2;
const stateOf = (r) => (isWin(r) ? "win" : r.state);
const cover = (r, cls = "") => `<span class="ph" aria-hidden="true">${esc((FORMAT[r.format] || r.format || "?")[0])}</span>` + (r.cover ? `<img class="${cls}" src="${esc(r.cover)}" alt="" loading="lazy" decoding="async">` : "");
// covers fade in over their placeholder once loaded
const markLoaded = (root = document) => root.querySelectorAll("img:not(.ld)").forEach((i) => (i.complete && i.naturalWidth ? i.classList.add("ld") : i.addEventListener("load", () => i.classList.add("ld"), { once: true })));
document.addEventListener("load", (e) => { if (e.target.tagName === "IMG") e.target.classList.add("ld"); }, true);
const xClass = (x) => (x == null ? "down" : x >= 2 ? "win" : x >= 1 ? "up" : "down");
const xTxt = (x) => (x == null ? "" : `${x.toFixed(1)}×`);
const byTime = (a, b) => (a.time > b.time ? 1 : -1);

function toast(msg) {
  const t = $("#toast");
  t.textContent = msg; t.hidden = false;
  clearTimeout(toast.t); toast.t = setTimeout(() => (t.hidden = true), 4000);
}

async function act(body, key, okMsg) {
  try {
    const r = await fetch("api/act", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify(body), keepalive: true });
    if (!r.ok) throw Object.assign(new Error((await r.json().catch(() => ({}))).error || `error ${r.status}`), { server: true });
    sent.add(key);
    toast(okMsg);
    render();
    return true;
  } catch (e) {
    toast(e.server ? `Not sent (${e.message}). Try again in a minute, or send it on Telegram.` : "Not sent: no connection. Try again when you're back online.");
    render();
    return false;
  }
}

// ---------------------------------------------------------------- seven-segment readout (drawn from data, unlit segments ghosted)
const SEGS = { 0: "abcdef", 1: "bc", 2: "abged", 3: "abgcd", 4: "fgbc", 5: "afgcd", 6: "afgedc", 7: "abc", 8: "abcdefg", 9: "abcdfg", "-": "g", " ": "" };
const RECT = { a: [10, 0, 36, 9], b: [47, 9, 9, 37], c: [47, 54, 9, 37], d: [10, 91, 36, 9], e: [0, 54, 9, 37], f: [0, 9, 9, 37], g: [10, 45.5, 36, 9] };
function seg(str, label) {
  let x = 8, out = "";
  for (const ch of str) {
    if (ch === ":") {
      out += `<g class="colon"><rect class="on" x="${x + 2}" y="26" width="9" height="9" rx="2"/><rect class="on" x="${x - 4}" y="66" width="9" height="9" rx="2"/></g>`;
      x += 24; continue;
    }
    const lit = SEGS[ch] ?? "";
    for (const [s, [rx, ry, w, h]] of Object.entries(RECT)) {
      out += `<rect class="${lit.includes(s) ? "on" : "off"}" x="${x + rx}" y="${ry}" width="${w}" height="${h}" rx="3"/>`;
    }
    x += 70;
  }
  return `<svg class="seg" viewBox="0 0 ${x - 6} 100" role="img" aria-label="${esc(label)}"><g transform="skewX(-6) translate(6 0)">${out}</g></svg>`;
}
const countdown = (iso) => {
  const m = minsUntil(iso);
  return seg(`${Math.floor(m / 60)}:${String(m % 60).padStart(2, "0")}`, `Posts ${until(iso)}`);
};

// ---------------------------------------------------------------- home
function pending() {
  return D.reels.filter((r) => r.state === "needs_yes" && r.id.startsWith("lst-")).sort(byTime);
}
function nextPost() {
  return D.reels.filter((r) => r.state === "scheduled" && r.time && new Date(r.time) > Date.now() - 6e5).sort(byTime)[0];
}
function weekWindow() {
  const keys = [...Array(7)].map((_, i) => dayKey(new Date(Date.now() + i * 864e5)));
  return keys.map((k) => ({ k, reels: D.reels.filter((r) => r.time && dayKey(new Date(r.time)) === k).sort(byTime) }));
}

function phase() {
  const P = pending().length && !sent.has("approve_week");
  const recentFail = D.reels.some((r) => r.state === "failed" && r.time && Date.now() - new Date(r.time) < 3 * 864e5);
  const recentWin = D.reels.some((r) => isWin(r) && Date.now() - new Date(r.posted_at || r.time) < 7 * 864e5);
  if (P) return { cls: "red", txt: "Yes waiting" };
  if (recentFail) return { cls: "red", txt: "A post failed" };
  if (recentWin) return { cls: "gold", txt: "Winner this week" };
  return { cls: "", txt: "All clear" };
}

function holdBtn(count, hint) {
  const done = sent.has("approve_week");
  return `<button class="btn hold ${done ? "done" : ""}" data-hold ${done ? "disabled" : ""} aria-describedby="${hint}"><span class="fill"></span><span class="lbl">${done ? "Approved" : `Hold to approve ${count}`}</span><span class="prog"></span></button>`;
}

function clock() {
  const next = nextPost(), ph = phase(), W = weekWindow();
  const all = W.flatMap((d) => d.reels), round = next ? all.indexOf(next) + 1 : 0;
  const today = dayKey(new Date());
  const program = `<div class="program" aria-label="This week: ${all.length} reels, ${all.filter((r) => r.state === "posted").length} posted, ${all.filter((r) => r.state === "needs_yes").length} need your yes">
      <p class="row1"><span>This week</span>${round ? `<span>Round <b>${round}</b> of <b>${all.length}</b></span>` : `<span><b>${all.length}</b> reels</span>`}</p>
      <ol class="rounds" aria-hidden="true">${W.map((d) => `<li><span class="cells">${(d.reels.length ? d.reels : [null, null]).map((r) => `<span class="c ${r ? stateOf(r) : ""} ${r && r === next ? "next" : ""}"></span>`).join("")}</span>
        <span class="d ${d.k === today ? "today" : ""}">${F.wday.format(new Date(d.k + "T12:00:00")).slice(0, 2)}</span></li>`).join("")}</ol>
    </div>`;
  if (!next) {
    return `<article class="clock main ${ph.cls === "red" ? "yes" : ""}" aria-label="Next post"><div class="face">
      <div class="phase"><span class="lamp ${ph.cls}"><i></i>${ph.txt}</span></div>
      <div class="readout">${seg("  :  ", "Nothing scheduled")}<p class="when">Nothing scheduled</p>
        <p class="meta">${pending().length ? "Approve the week and the next reel shows up here." : "The factory makes next week's reels on Sunday morning."}</p></div>
      ${program}</div></article>`;
  }
  return `<article class="clock main ${ph.cls === "red" ? "yes" : ""}" aria-label="Next post">
    <div class="face">
      <div class="phase"><span class="lamp ${ph.cls}"><i></i>${ph.txt}</span></div>
      <div class="readout">
        <span data-until="${esc(next.time)}">${countdown(next.time)}</span>
        <p class="units" aria-hidden="true"><span>HRS</span><span>MIN</span><span>UNTIL NEXT POST</span></p>
        <p class="when">${dayWord(next.time)} ${t12(next.time)}</p>
        <p class="hookline">${esc(calm(next.hook))}</p>
        <p class="meta">${fmtName(next.format)}, New York time</p>
      </div>
      <button class="shot" data-open="${esc(next.id)}" aria-label="Open the next reel">${cover(next)}</button>
      ${program}
    </div>
  </article>`;
}

function waiting() {
  const P = pending();
  if (!P.length) return "";
  const done = sent.has("approve_week");
  return `<section class="waiting" aria-labelledby="w-h">
    <div class="top"><h2 class="h2" id="w-h">${P.length} reels need your yes</h2></div>
    <p class="range">${F.short.format(new Date(P[0].time))} to ${F.short.format(new Date(P[P.length - 1].time))}, New York time</p>
    <div class="row">${holdBtn(P.length, "hold-hint")}<button class="btn line" data-review>Review</button></div>
    <p class="hint" id="hold-hint">${done ? "Sent. This page updates in about a minute." : "Hold for a second. Nothing goes out by accident."}</p>
  </section>`;
}

function splits() {
  const last = D.reels.filter((r) => r.state === "posted").sort((a, b) => ((a.posted_at || a.time) < (b.posted_at || b.time) ? 1 : -1)).slice(0, 3);
  if (!last.length) return "";
  const med = D.baseline.median_views;
  return `<section class="splits" aria-labelledby="s-h">
    <div class="head"><h2 class="h2" id="s-h">Last reels</h2><span class="label">${med ? `vs your normal <span class="num">${n(med)}</span>` : "normal not measured yet"}</span></div>
    <ol>${last.map((r) => {
      const m = r.metrics || {}, t = r.posted_at || r.time;
      return `<li><button data-open="${esc(r.id)}" aria-label="${esc(calm(r.hook))}: ${m.views != null ? `${n(m.views)} views, ${xTxt(m.vs_median_x)} normal` : "numbers after 72 hours"}">
        <span class="views">${m.views != null ? n(m.views) : "72 h"}</span>
        <span class="x ${xClass(m.vs_median_x)}">${m.views != null ? `${xTxt(m.vs_median_x)} normal` : "until numbers"}</span>
        <span class="when2">${F.wday.format(new Date(t))} ${t12(t)}</span></button></li>`;
    }).join("")}</ol>
  </section>`;
}

function bout(r) {
  const s = stateOf(r), m = r.metrics || {};
  let line = `<span class="tm">${r.time ? t12(r.time) + ", " : ""}</span>${fmtName(r.format)}`;
  if (m.views != null) line += `, <span class="num">${n(m.views)}</span> views, <span class="x ${xClass(m.vs_median_x)}">${xTxt(m.vs_median_x)}</span>`;
  else if (r.state === "posted") line += `, numbers after 72 h`;
  return `<li class="bout"><button data-open="${esc(r.id)}">
    <span class="thumb">${cover(r)}</span>
    <time datetime="${esc(r.time)}">${r.time ? t12(r.time) : ""}</time>
    <span class="what"><p>${esc(calm(r.hook))}</p><p>${line}</p></span>
    <span class="st ${s}">${LABEL[s]}</span>
  </button></li>`;
}

function weekList() {
  const today = dayKey(new Date());
  const R = D.reels.filter((r) => r.time && dayKey(new Date(r.time)) >= today && +new Date(r.time) < Date.now() + 8 * 864e5).sort(byTime);
  if (!R.length) return `<h2 class="h2">Schedule</h2><p class="empty-note">No reels this week yet. The factory makes them every Sunday, and you approve them here.</p>`;
  let h = `<div class="head"><h2 class="h2" id="fc-h">Schedule</h2><span class="label">New York time</span></div>`, cur = "";
  for (const r of R) {
    const k = dayKey(new Date(r.time));
    if (k !== cur) {
      if (cur) h += `</ul>`;
      h += `<p class="day ${k === today ? "today" : ""}"><span>${k === today ? "Today, " : ""}${F.day.format(new Date(r.time))}</span></p><ul class="bouts">`;
      cur = k;
    }
    h += bout(r);
  }
  return h + `</ul>`;
}

function home() {
  return `<div class="home"><div class="left">${clock()}${waiting()}${splits()}</div><section class="right" aria-labelledby="fc-h">${weekList()}</section></div>`;
}

// ---------------------------------------------------------------- reels
function tile(r) {
  const s = stateOf(r), m = r.metrics || {};
  const left = m.views != null ? n(m.views) : r.time ? `${F.wday.format(new Date(r.time))} ${t12(r.time)}` : "";
  const right = m.vs_median_x != null ? `<span class="${s === "win" ? "win" : ""}">${xTxt(m.vs_median_x)}</span>` : "";
  const flag = s === "needs_yes" || s === "failed" || s === "win" ? `<span class="flag ${s}">${LABEL[s]}</span>` : "";
  return `<button class="tile" data-open="${esc(r.id)}" aria-label="${esc(calm(r.hook))}, ${LABEL[s]}${m.views != null ? `, ${n(m.views)} views` : ""}">
    ${r.cover ? cover(r) : `<span class="fallback">${esc(calm(r.hook))}</span>`}
    ${flag}<span class="over"><span>${left}</span>${right}</span>
  </button>`;
}

function reels() {
  const counts = { all: D.reels.length };
  D.reels.forEach((r) => { counts[r.state] = (counts[r.state] || 0) + 1; });
  const list = D.reels.filter((r) => filter === "all" || r.state === filter);
  const b = (k, l) => (k === "all" || counts[k] ? `<button data-filter="${k}" aria-pressed="${filter === k}">${l}<span class="n">${counts[k]}</span></button>` : "");
  return `<div class="page-head"><h1 class="h1">Reels</h1></div>
    <div class="filters" role="group" aria-label="Filter reels">${b("all", "All")}${b("needs_yes", "Needs yes")}${b("scheduled", "Set")}${b("posted", "Posted")}${b("failed", "Failed")}</div>
    ${list.length ? `<div class="grid">${list.map(tile).join("")}</div>` : `<p class="empty-note">No reels with this status.</p>`}`;
}

// ---------------------------------------------------------------- results
const CELLS = 24;
function meter(value, max, norm, cls) {
  const on = Math.max(value > 0 ? 1 : 0, Math.round((CELLS * value) / max));
  return `<span class="meter ${cls}" aria-hidden="true">${[...Array(CELLS)].map((_, i) => `<i class="${i < on ? "on" : ""}"></i>`).join("")}${norm != null ? `<span class="norm" style="left:${(100 * norm) / max}%"></span>` : ""}</span>`;
}
function results() {
  const med = D.baseline.median_views;
  const rows = Object.entries(D.formats).map(([k, v]) => ({ k, ...v, avg: v.views / v.reels, fpk: v.views ? (1000 * v.follows) / v.views : 0 }))
    .sort((a, b) => b.avg - a.avg);
  if (!rows.length) {
    return `<div class="page-head"><h1 class="h1">Results</h1></div>
      <p class="empty-note">Results show up 72 hours after a reel posts. Claude pulls the numbers from Instagram every morning and compares each reel with your normal${med ? ` ${n(med)}` : ""} views.</p>`;
  }
  const tot = rows.reduce((a, r) => ({ v: a.v + r.views, f: a.f + r.follows }), { v: 0, f: 0 });
  const avgF = tot.v ? (1000 * tot.f) / tot.v : 0;
  const bestV = rows[0], bestF = rows.slice().sort((a, b) => b.fpk - a.fpk)[0];
  const ranked = by === "fpk" ? rows.slice().sort((a, b) => b.fpk - a.fpk) : rows;
  const maxV = Math.max(...rows.map((r) => r.avg), (med || 0) * 1.5) || 1, maxF = Math.max(...rows.map((r) => r.fpk), avgF * 1.5) || 1;
  const thin = (r) => r.reels < 3;
  const small = (r) => `<small class="${thin(r) ? "thin" : ""}">${r.reels} ${r.reels === 1 ? "reel" : "reels"}${thin(r) ? ", small sample" : ""}</small>`;
  const sample = (r) => `${r.reels} ${r.reels === 1 ? "reel" : "reels"}${thin(r) ? ", small sample" : ""}`;
  const figV = (r) => `<p class="fig gold">${n(r.avg)} views per reel${med ? `, ${(r.avg / med).toFixed(1)}× normal` : ""}</p>`;
  const figF = (r) => `<p class="fig gold">${r.fpk.toFixed(1)} follows per 1k views</p>`;
  const verdicts = bestV === bestF
    ? `<div class="verdicts"><article class="verdict"><h2 class="big">${fmtName(bestV.k)} wins both</h2>${figV(bestV)}${figF(bestV)}
        <p class="meta">From ${sample(bestV)}. Your normal is ${n(med)} views; your average is ${avgF.toFixed(1)} follows per 1k.</p></article></div>`
    : `<div class="verdicts split"><article class="verdict"><h2 class="big">${fmtName(bestV.k)} wins views</h2>${figV(bestV)}<p class="meta">From ${sample(bestV)}. Your normal is ${n(med)}.</p></article>
        <article class="verdict"><h2 class="big">${fmtName(bestF.k)} wins follows</h2>${figF(bestF)}<p class="meta">From ${sample(bestF)}. Your average is ${avgF.toFixed(1)}.</p></article></div>`;
  return `<div class="page-head"><h1 class="h1">Results</h1><p class="lede">Which formats earn views, and which turn views into followers.</p></div>
    ${verdicts}
    <section aria-labelledby="l-h"><div class="head"><h2 class="h2" id="l-h">Every format</h2>
        <span class="toggle" role="group" aria-label="Rank formats by"><button data-by="views" aria-pressed="${by === "views"}">Views</button><button data-by="fpk" aria-pressed="${by === "fpk"}">Follows per 1k</button></span></div>
      <div class="ladder" data-by="${by}" role="table" aria-label="Formats by views per reel and follows per 1,000 views">
        <div class="lhead" role="row"><span role="columnheader">Format</span><span role="columnheader">Views per reel</span><span role="columnheader">Follows per 1,000 views</span></div>
        ${ranked.map((r) => `<div class="lrow" role="row">
          <p class="k" role="rowheader">${fmtName(r.k)} ${small(r)}</p>
          <div class="metric views" role="cell"><span class="cap">Views per reel</span>${meter(r.avg, maxV, med, r === bestV ? "best" : thin(r) ? "thin" : "")}
            <span class="v ${r === bestV ? "best" : ""}">${n(r.avg)}<small>${med ? `${(r.avg / med).toFixed(1)}× normal` : ""}</small></span></div>
          <div class="metric fpk" role="cell"><span class="cap">Follows per 1,000 views</span>${meter(r.fpk, maxF, avgF, r === bestF ? "best" : thin(r) ? "thin" : "")}
            <span class="v ${r === bestF ? "best" : ""}">${r.fpk.toFixed(1)}<small>${n(r.follows)} follows</small></span></div>
        </div>`).join("")}
      </div>
      <p class="legend"><span><i></i>Views: your normal ${n(med)}</span><span><i></i>Follows: your average ${avgF.toFixed(1)} per 1k</span></p>
    </section>
    <section class="panel" aria-labelledby="t-h"><div class="head"><h2 class="h2" id="t-h">The numbers</h2></div><div class="scroll"><table>
      <thead><tr><th scope="col">Format</th><th scope="col">Reels</th><th scope="col">Views/reel</th><th scope="col">vs normal</th><th scope="col">Follows/1k</th><th scope="col">Shares</th><th scope="col">Saves</th><th scope="col">Winners</th></tr></thead>
      <tbody>${rows.map((r) => `<tr><td>${fmtName(r.k)}</td><td>${r.reels}</td><td>${n(r.avg)}</td><td>${med ? (r.avg / med).toFixed(1) + "×" : "n/a"}</td><td>${r.fpk.toFixed(1)}</td><td>${n(r.shares)}</td><td>${n(r.saves)}</td><td>${r.winners}</td></tr>`).join("")}</tbody>
    </table></div></section>
    ${D.baseline.updated ? `<p class="hint">From Instagram, updated ${ago(D.baseline.updated)}.</p>` : ""}`;
}

// ---------------------------------------------------------------- decide
function decide() {
  const open = D.questions.filter((q) => q.status === "open");
  const done = D.questions.filter((q) => q.status !== "open").slice(-8).reverse();
  let h = `<div class="page-head"><h1 class="h1">Your calls</h1><p class="lede">Claude asks here and on Telegram when it needs a decision. Tap an answer; you get 4 seconds to undo it.</p></div>`;
  h += open.length
    ? open.map((q) => {
        const sentK = [...sent].find((k) => k.startsWith(`q:${q.id}:`));
        const pick = sentK ? +sentK.split(":").pop() : pa && pa.id === q.id ? pa.k : -1;
        return `<section class="q" aria-labelledby="q-${esc(q.id)}"><h3 id="q-${esc(q.id)}">${esc(q.question)}</h3>${q.context ? `<p class="ctx">${esc(q.context)}</p>` : ""}
          <div class="opts" role="group" aria-labelledby="q-${esc(q.id)}">${(q.options || []).map((o, k) => `<button class="opt ${pick === k ? "picked" : ""}" data-q="${esc(q.id)}" data-k="${k}" aria-pressed="${pick === k}" ${sentK ? "disabled" : ""}>${esc(o)}</button>`).join("")}</div>
          ${sentK ? `<p class="sent-note">Answer sent.</p>` : ""}</section>`;
      }).join("")
    : `<p class="empty-note">Nothing to decide right now.</p>`;
  h += `<section class="section" aria-labelledby="i-h"><div class="head"><h2 class="h2" id="i-h">Ideas for Claude</h2></div>
    <label class="field" for="idea">What should Claude try?</label>
    <textarea id="idea" placeholder="A hook you thought of, a format you saw, more nutrition, stop using a clip"></textarea>
    <div class="row-actions"><button class="btn" data-act="idea">Send idea</button><span class="hint">Claude replies on its next morning check.</span></div>
    <div style="margin-top:16px">${D.ideas.slice().reverse().map((i) => `<div class="idea"><p class="t">${esc(i.text)}</p>
      <p class="m"><time datetime="${esc(i.at)}" title="${i.at ? F.full.format(new Date(i.at)) + " New York" : ""}">${ago(i.at)}</time>, from ${esc(i.via)}${i.status === "new" ? ". Waiting for Claude" : ""}</p>
      ${i.reply ? `<div class="reply"><b>Claude</b>${esc(i.reply)}</div>` : ""}</div>`).join("")}</div></section>`;
  if (done.length) {
    h += `<section class="section" aria-labelledby="dd-h"><div class="head"><h2 class="h2" id="dd-h">Decided</h2></div>${done.map((q) => `<div class="idea"><p class="t">${esc(q.question)}</p>
      <p class="m"><span class="answered">${esc(q.answer)}</span>, ${ago(q.answered_at)}${q.via ? ` from ${esc(q.via)}` : ""}</p></div>`).join("")}</section>`;
  }
  return h;
}

// answers wait out a 4 second undo window, then send
const UNDO_S = 4;
function showUndo() {
  const u = $("#undo");
  if (!pa) { u.hidden = true; u.innerHTML = ""; return; }
  u.hidden = false;
  u.innerHTML = `<span class="count" aria-hidden="true">${seg(String(pa.left), "")}</span><p>Sending <b>${esc(pa.choice)}</b></p><button class="btn line" data-undo>Undo</button>`;
}
function commitAnswer() {
  if (!pa) return;
  clearInterval(pa.timer);
  const { id, k, choice } = pa;
  pa = null; showUndo();
  act({ action: "answer", id, choice }, `q:${id}:${k}`, `Answer sent: ${choice}`);
}
function pickAnswer(id, k) {
  const q = D.questions.find((x) => x.id === id);
  if (!q) return;
  if (pa && pa.id !== id) commitAnswer();
  if (pa) clearInterval(pa.timer);
  pa = { id, k, choice: q.options[k], left: UNDO_S };
  pa.timer = setInterval(() => {
    if (!pa) return;
    pa.left -= 1;
    if (pa.left <= 0) commitAnswer(); else $("#undo .count") && ($("#undo .count").innerHTML = seg(String(pa.left), ""));
  }, 1000);
  $("#sr").textContent = `Sending ${pa.choice} in ${UNDO_S} seconds. Press Undo or Escape to cancel.`;
  showUndo(); render();
  // keep the picked answer visible above the undo bar
  document.querySelector(`[data-q="${CSS.escape(id)}"][data-k="${k}"]`)?.scrollIntoView({ block: "center", behavior: matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth" });
}
function undoAnswer() {
  if (!pa) return;
  clearInterval(pa.timer); pa = null; showUndo(); render();
  toast("Not sent. Pick again when you're ready.");
}

// ---------------------------------------------------------------- activity
function activity() {
  const H = D.health;
  const row = (k, v, warn) => `<dt>${k}</dt><dd class="${warn ? "warn" : ""}">${v}</dd>`;
  return `<div class="page-head"><h1 class="h1">Activity</h1></div>
    <div class="two">
      <section aria-labelledby="sy-h"><div class="head"><h2 class="h2" id="sy-h">System</h2></div><dl class="facts">
        ${row("Last post", ago(H.last_post))}
        ${row("Next post", H.next_post ? F.full.format(new Date(H.next_post)).replace(" AM", "am").replace(" PM", "pm") : "Nothing scheduled")}
        ${row("Hooks ready for next week", H.hooks_ready, H.hooks_ready < 14)}
        ${row("Clips in your Drive folder", H.clips_live || "n/a")}
        ${row("Clips Claude has watched", H.clips_catalogued)}
        ${row("Clips good enough to use", H.clips_usable)}
        ${row("Failed posts", H.failed.length, H.failed.length)}
      </dl><p class="hint" style="margin-top:12px">Times are New York time.</p></section>
      <section aria-labelledby="lg-h"><div class="head"><h2 class="h2" id="lg-h">Log</h2></div>
        ${D.log.length ? `<ol class="log" reversed>${D.log.slice().reverse().map((e) => `<li><time datetime="${esc(e.at)}" title="${F.full.format(new Date(e.at))} New York">${ago(e.at)}</time><p><span class="who ${e.who === "Matteo" ? "matteo" : ""}">${esc(e.who === "system" ? "System" : e.who)}</span> ${esc(e.text)}</p></li>`).join("")}</ol>`
          : `<p class="empty-note">Nothing logged yet. Approvals, posts, answers and Claude's changes show up here.</p>`}
      </section>
    </div>`;
}

// ---------------------------------------------------------------- sheets
function openSheet(id) {
  const r = D.reels.find((x) => x.id === id);
  if (!r) return;
  const s = stateOf(r), m = r.metrics || {};
  const stat = (l, v, cls = "") => `<div><dt>${l}</dt><dd class="${cls}">${v}</dd></div>`;
  const when = r.state === "posted" && r.posted_at ? `Posted ${ago(r.posted_at)}` : r.time ? `${F.full.format(new Date(r.time)).replace(" AM", "am").replace(" PM", "pm")} New York` : "";
  const dlg = $("#sheet");
  dlg.innerHTML = `<div class="sheet">
    <div class="cover">${cover(r)}</div>
    <div><span class="st ${s}">${LABEL[s]}</span><h2 id="sheet-title">${esc(calm(r.hook))}</h2>
      <p class="meta">${fmtName(r.format)}${when ? `<br>${when}` : ""}${r.clip ? `<br>Clip: ${esc(r.clip)}` : ""}</p></div>
    ${m.views != null ? `<dl>${stat("Views", n(m.views))}${stat("vs normal", m.vs_median_x != null ? xTxt(m.vs_median_x) : "n/a", isWin(r) ? "gold" : "")}${stat("Follows", n(m.follows))}${stat("Shares", n(m.shares))}${stat("Saves", n(m.saves))}${stat("Skip rate", m.skip_rate != null ? Math.round(m.skip_rate) + "%" : "n/a")}</dl>` : ""}
    ${s === "win" ? `<p class="note">Winner. Repost it to your grid from the Instagram app with a trending sound; Claude sent suggestions on Telegram.</p>` : ""}
    ${r.error ? `<p class="err">Failed to post: ${esc(r.error).slice(0, 220)}. Claude looks at it on the next morning check.</p>` : ""}
    <div class="foot">${r.permalink ? `<a class="btn" href="${esc(r.permalink)}" target="_blank" rel="noopener">Open on Instagram</a>` : ""}<button class="btn line" data-close>Close</button></div>
  </div>`;
  dlg.showModal(); markLoaded(dlg);
}

function openReview() {
  const P = pending();
  if (!P.length) return;
  const days = [];
  for (const r of P) {
    const k = dayKey(new Date(r.time));
    if (!days.length || days[days.length - 1].k !== k) days.push({ k, t: r.time, reels: [] });
    days[days.length - 1].reels.push(r);
  }
  const dlg = $("#sheet");
  dlg.innerHTML = `<div class="review">
    <header><h2 class="h2" id="sheet-title">${P.length} reels need your yes</h2>
      <p class="label">${F.short.format(new Date(P[0].time))} to ${F.short.format(new Date(P[P.length - 1].time))}, New York time. Approving is your yes for exactly these; they post on their own.</p></header>
    <div class="list" tabindex="0" aria-label="Reels waiting">${days.map((d) => `<p class="rd">${F.day.format(new Date(d.t))}</p><ul>${d.reels.map((r) => `<li>
      <span class="thumb">${cover(r)}</span><time datetime="${esc(r.time)}">${t12(r.time)}</time><p>${esc(calm(r.hook))}<small>${fmtName(r.format)}</small><span class="st needs_yes">Needs yes</span></p></li>`).join("")}</ul>`).join("")}</div>
    <footer><div class="row">${holdBtn(P.length, "rv-hint")}<button class="btn line" data-close>Close</button></div>
      <p class="hint" id="rv-hint">Hold for a second. Nothing goes out by accident.</p></footer>
  </div>`;
  dlg.showModal(); markLoaded(dlg);
}
$("#sheet").addEventListener("click", (e) => { if (e.target === e.currentTarget || e.target.closest("[data-close]")) e.currentTarget.close(); });

// ---------------------------------------------------------------- render + events
const VIEWS = { home, reels, results, decide, activity };

function render() {
  if (!D) return;
  const active = document.activeElement, keep = active?.id === "idea" ? active.value : null;
  $("#view").innerHTML = VIEWS[tab]();
  markLoaded();
  if (keep != null && $("#idea")) { $("#idea").value = keep; $("#idea").focus(); }
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
  if (t.dataset.by) { by = t.dataset.by; return render(); }
  if (t.dataset.open) return openSheet(t.dataset.open);
  if ("review" in t.dataset) return openReview();
  if ("undo" in t.dataset) return undoAnswer();
  if (t.dataset.act === "idea") {
    const el = $("#idea"), text = el.value.trim();
    if (!text) { el.focus(); return toast("Write the idea first, then send it."); }
    t.disabled = true;
    act({ action: "idea", text }, "idea:" + text, "Idea sent. Claude replies on its next morning check.").then((ok) => { if (ok) { const e2 = $("#idea"); if (e2) e2.value = ""; } });
  }
  if (t.dataset.q && !t.disabled) pickAnswer(t.dataset.q, +t.dataset.k);
});
document.addEventListener("keydown", (e) => { if (e.key === "Escape" && pa && !$("#sheet").open) undoAnswer(); });
document.addEventListener("visibilitychange", () => { if (document.visibilityState === "hidden") commitAnswer(); });

// press-and-hold to approve the week (pointer and keyboard)
const HOLD_MS = 1200;
let holdTimer = null, holdEl = null;
const holdLabel = (b, txt) => { const l = b.querySelector(".lbl"); if (l) l.textContent = txt; };
function holdStart(b) {
  if (b.disabled || holdTimer) return;
  holdEl = b;
  document.body.classList.add("holding");
  b.classList.add("holding"); holdLabel(b, "Keep holding");
  navigator.vibrate?.(10);
  holdTimer = setTimeout(() => {
    holdTimer = null; holdEl = null; b.classList.remove("holding"); b.classList.add("done"); holdLabel(b, "Approving");
    document.body.classList.remove("holding"); document.body.classList.add("rung"); setTimeout(() => document.body.classList.remove("rung"), 900);
    navigator.vibrate?.([30, 60, 30]);
    const ids = pending().map((r) => r.id);
    act({ action: "approve_week", ids }, "approve_week", `Approved ${ids.length} reels. They post on their own.`).then((ok) => {
      const dlg = $("#sheet");
      if (ok && dlg.open && dlg.querySelector(".review")) setTimeout(() => dlg.close(), 500);
      if (!ok && dlg.open && dlg.querySelector(".review")) openReview();
    });
  }, HOLD_MS);
}
function holdStop() {
  if (!holdTimer) return;
  clearTimeout(holdTimer); holdTimer = null;
  document.body.classList.remove("holding");
  const b = holdEl; holdEl = null;
  if (b) { b.classList.remove("holding"); holdLabel(b, `Hold to approve ${pending().length}`); }
}
document.addEventListener("pointerdown", (e) => { const b = e.target.closest("[data-hold]"); if (b) { e.preventDefault(); holdStart(b); } });
["pointerup", "pointercancel"].forEach((ev) => document.addEventListener(ev, holdStop, true));
document.addEventListener("pointerleave", (e) => { if (e.target === holdEl) holdStop(); }, true);
document.addEventListener("keydown", (e) => { const b = e.target.closest?.("[data-hold]"); if (b && (e.key === " " || e.key === "Enter") && !e.repeat) { e.preventDefault(); holdStart(b); } });
document.addEventListener("keyup", (e) => { const b = e.target.closest?.("[data-hold]"); if (b && (e.key === " " || e.key === "Enter")) holdStop(); });
document.addEventListener("contextmenu", (e) => { if (e.target.closest("[data-hold]")) e.preventDefault(); });

// live clock: New York time in the bar, countdown on the clock face
function tick() {
  $("#nyclock").textContent = `NY ${t12(new Date().toISOString())}`;
  document.querySelectorAll("[data-until]").forEach((el) => (el.innerHTML = countdown(el.dataset.until)));
}
tick();
setInterval(tick, 15000);

async function load() {
  try {
    const r = await fetch("data.json?" + Date.now(), { cache: "no-store" });
    if (!r.ok) throw new Error(r.status);
    D = await r.json();
    if (!$("#sheet").open && !holdTimer) render();
  } catch {
    if (!D) $("#view").innerHTML = `<p class="empty-note">Couldn't load the latest data. Check your connection; this page retries every minute.</p>`;
  }
}
load();
setInterval(load, 60000);
document.addEventListener("visibilitychange", () => document.visibilityState === "visible" && load());
