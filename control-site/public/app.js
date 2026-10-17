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
const n = (x) => (x == null ? "n/a" : x >= 1e6 ? (x / 1e6).toFixed(x >= 1e7 ? 0 : 1).replace(/\.0$/, "") + "M" : x >= 10000 ? (x / 1000).toFixed(x >= 100000 ? 0 : 1) + "k" : Math.round(x).toLocaleString("en-US"));
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
const PLAT = { instagram: "Instagram", facebook: "Facebook", facebook_slides: "Facebook slides", youtube: "YouTube", threads: "Threads", tiktok: "TikTok" };
const hidden = (() => { try { return new Set(JSON.parse(localStorage.getItem("inboxDone") || "[]")); } catch { return new Set(); } })();
const saveHidden = () => { try { localStorage.setItem("inboxDone", JSON.stringify([...hidden].slice(-400))); } catch {} };

let D = null;
let tab = (() => { try { return localStorage.getItem("tab") || "home"; } catch { return "home"; } })();
let filter = "all";
let by = "views"; // results ranking: views per reel or follows per 1k
let rview = (() => { try { return localStorage.getItem("rview") || "you"; } catch { return "you"; } })(); // Results: you | rivals
let rplat = "all"; // Rivals platform filter
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

// ---------------------------------------------------------------- next up: the few things worth doing now, most valuable first
const prettySlug = (s) => String(s || "").replace(/^\d{4}-\d{2}-\d{2}-/, "").replace(/-/g, " ").replace(/^\w/, (c) => c.toUpperCase());
function nextUp() {
  const items = [];
  const open = (D.platforms?.inbox || []).filter((c) => !c.answered && !hidden.has(c.platform + ":" + c.id));
  const fresh = open.filter((c) => Date.now() - new Date(c.at) < 36e5).length;
  if (open.length) items.push({ dot: fresh ? "red" : "", go: "decide", t: `Answer ${open.length} comment${open.length > 1 ? "s" : ""}`,
    s: fresh ? `${fresh} in the last hour. Replying now lifts the reel most.` : "Early replies lift a reel's reach." });
  for (const t of D.tests || []) {
    const d = t.decision;
    if (d && Date.now() - new Date(d.decided_at) < 7 * 864e5)
      items.push({ dot: "gold", go: "results", t: `Share ${d.winner} of ${prettySlug(t.reel)} to your grid`, s: `${d.why[0].toUpperCase() + d.why.slice(1)}. In the Instagram app: the trial reel, then Share to profile.` });
  }
  const failed = D.reels.filter((r) => r.state === "failed" && r.time && Date.now() - new Date(r.time) < 3 * 864e5).length;
  if (failed) items.push({ dot: "red", go: "reels", f: "failed", t: `${failed} post${failed > 1 ? "s" : ""} failed`, s: "Open it to see why." });
  if (D.health.hooks_ready < 14) items.push({ dot: "", go: "decide", t: `${D.health.hooks_ready} listicle hooks left`, s: "Under two weeks. Send hook ideas, or ask Claude for a batch." });
  if (!items.length) return "";
  return `<section class="nextup" aria-label="Next up">${items.slice(0, 4).map((i) => `<button data-goto="${i.go}" ${i.f ? `data-filter="${i.f}"` : ""}>
    <span class="dot ${i.dot}" aria-hidden="true"></span><span><b>${esc(i.t)}</b><small>${esc(i.s)}</small></span></button>`).join("")}</section>`;
}

// ---------------------------------------------------------------- results > followers + hook tests (tools/analytics/learn.py)
function growthPanel() {
  const G = D.growth || [];
  if (G.length < 2) return "";
  const v = G.map((g) => g[1]), last = v[v.length - 1], min = Math.min(...v), span = Math.max(...v) - min || 1;
  const W = 300, H = 96;
  const pts = v.map((y, i) => `${((i * W) / (v.length - 1)).toFixed(1)},${(H - 4 - ((y - min) * (H - 8)) / span).toFixed(1)}`).join(" ");
  const since = (days) => {
    const k = dayKey(new Date(Date.now() - days * 864e5)), past = G.filter((g) => g[0] <= k).pop();
    if (!past) return "n/a";
    const d = last - past[1];
    return (d > 0 ? "+" : "") + n(d);
  };
  return `<section class="section growth" aria-labelledby="gr-h"><div class="head"><h2 class="h2" id="gr-h">Followers</h2><span class="label">Instagram, daily</span></div>
    <div class="nums"><span>${n(last)}<small>now</small></span><span>${since(7)}<small>7 days</small></span><span>${since(30)}<small>30 days</small></span></div>
    <svg viewBox="0 0 ${W} ${H}" preserveAspectRatio="none" role="img" aria-label="Followers from ${n(v[0])} to ${n(last)} over ${v.length} days">
      <polygon class="area" points="0,${H} ${pts} ${W},${H}"/><polyline class="line" points="${pts}"/></svg></section>`;
}
function hookTests() {
  const T = D.tests || [];
  if (!T.length) return "";
  const hookOf = (t, v) => v.hook || D.reels.find((r) => r.reel === t.reel && r.variant === v.v)?.hook || "";
  return `<section class="section" aria-labelledby="ht-h"><div class="head"><h2 class="h2" id="ht-h">Hook tests</h2><span class="label">same video, different hooks</span></div>
    ${T.map((t) => {
      const d = t.decision;
      return `<article class="htest"><h3>${esc(prettySlug(t.reel))}</h3><p class="hint">${d ? `${esc(d.winner)} won: ${esc(d.why)}` : "Called once every hook is 72 hours old"}</p>
        <ol>${t.variants.map((v) => `<li class="${d && d.winner === v.v ? "win" : ""}"><span class="v">${esc(v.v)}</span><span class="hk">${esc(calm(hookOf(t, v)).replace(/^[A-Z]: /, ""))}</span>
          <span class="n">${v.views != null ? n(v.views) : "–"}<small>${v.shares ?? 0} shares${v.avg_watch_s != null ? `, ${v.avg_watch_s} s watched` : ""}</small></span></li>`).join("")}</ol></article>`;
    }).join("")}
    <p class="hint">Winner: most views at 72 hours, unless another hook has twice the shares. Within 15%, the longer average watch wins.</p></section>`;
}

// ---------------------------------------------------------------- reels > studio (cloud editing: tools/video/README.md)
const STAGE = { idea: "Idea", "talking-points": "Talking points", filmed: "Filmed", edited: "Edited", testing: "Testing", "winner-posted": "Winner posted", archived: "Archived" };
function studioBoard() {
  const S = (D.studio || []).filter((s) => !["archived", "winner-posted"].includes(s.status));
  const rendering = (s) => sent.has("run:reel_render:" + s.slug);
  return `<section class="studio" aria-labelledby="st-h"><div class="head"><h2 class="h2" id="st-h">Studio</h2><span class="label">filmed reels, edited in the cloud</span></div>
    ${S.length ? `<ul>${S.map((s) => `<li><div><p class="t">${esc(s.title)}</p><p class="m">${STAGE[s.status] || esc(s.status)}${s.variants.length ? `, hooks ${s.variants.join(" ")}` : ""}${s.renderable ? "" : ", media not in the cloud yet"}</p></div>
      ${s.renderable ? `<button class="btn line" data-run="reel_render" data-slug="${esc(s.slug)}" data-variants="${esc(s.variants.join(",") || "A,B,C")}" ${rendering(s) ? "disabled" : ""}>${rendering(s) ? "Rendering" : "Render"}</button>` : ""}</li>`).join("")}</ul>` : ""}
    <form data-ingest><label class="field" for="ing-slug">New reel from Drive</label>
      <input class="text" id="ing-slug" name="slug" placeholder="2026-10-20-short-name" autocomplete="off" autocapitalize="off" spellcheck="false" required pattern="[a-z0-9][a-z0-9._\-]{2,80}">
      <input class="text" name="footage" placeholder="newest, or the clip's name in Drive input" autocomplete="off" autocapitalize="off" spellcheck="false" aria-label="Which footage">
      <div class="row-actions"><button class="btn" type="submit">Bring it in</button><span class="hint">Preps the footage and writes the transcript. Then ask Claude for the edit.</span></div></form></section>`;
}

// ---------------------------------------------------------------- home
function pending() {
  return D.reels.filter((r) => r.state === "needs_yes" && r.id.startsWith("lst-")).sort(byTime);
}
// filmed reels (talking-head A/B/C trial variants) waiting for a yes
function pendingTrials() {
  return D.reels.filter((r) => r.state === "needs_yes" && !r.id.startsWith("lst-")).sort(byTime);
}
// written Threads posts (tools/crosspost) waiting for a yes, still in the future
function pendingThreads() {
  return (D.threads_posts || []).filter((p) => p.status === "queued" && !p.approved && !sent.has("skip:" + p.id) && new Date(p.at) > Date.now()).sort((a, b) => (a.at > b.at ? 1 : -1));
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
  if (P || (pendingThreads().length && !sent.has("approve_threads")) || (pendingTrials().length && !sent.has("approve_trials"))) return { cls: "red", txt: "Yes waiting" };
  if (recentFail) return { cls: "red", txt: "A post failed" };
  if (recentWin) return { cls: "gold", txt: "Winner this week" };
  return { cls: "", txt: "All clear" };
}

const HOLD = {
  week: { key: "approve_week", count: () => pending().length },
  threads: { key: "approve_threads", count: () => pendingThreads().length },
  trials: { key: "approve_trials", count: () => pendingTrials().length },
};
function holdBtn(count, hint, kind = "week") {
  const done = sent.has(HOLD[kind].key);
  return `<button class="btn hold ${done ? "done" : ""}" data-hold="${kind}" ${done ? "disabled" : ""} aria-describedby="${hint}"><span class="fill"></span><span class="lbl">${done ? "Approved" : `Hold to approve ${count}`}</span><span class="prog"></span></button>`;
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

function threadsWaiting() {
  const T = pendingThreads();
  if (!T.length || sent.has("approve_threads")) return "";
  return `<section class="waiting" aria-labelledby="tw-h">
    <div class="top"><h2 class="h2" id="tw-h">${T.length} Threads posts need your yes</h2></div>
    <p class="range">${F.short.format(new Date(T[0].at))} to ${F.short.format(new Date(T[T.length - 1].at))}, New York time</p>
    <div class="row"><button class="btn line" data-goto="decide">Read and approve</button></div>
  </section>`;
}

function trialsWaiting() {
  const T = pendingTrials();
  if (!T.length) return "";
  const done = sent.has("approve_trials");
  return `<section class="waiting trials" aria-labelledby="tr-h">
    <div class="top"><h2 class="h2" id="tr-h">${T.length} trial reels need your yes</h2></div>
    <p class="range">One video, ${T.length} hooks. Tap one to watch it.</p>
    <ul class="trial-list">${T.map((r) => `<li><button data-open="${esc(r.id)}"><span class="thumb">${cover(r)}</span>
      <span class="what"><p>${esc(calm(r.hook))}</p><p><span class="num">${r.time ? `${F.wday.format(new Date(r.time))} ${t12(r.time)}` : ""}</span>, ${r.variant ? "version " + esc(r.variant) : "trial reel"}</p></span></button></li>`).join("")}</ul>
    <div class="row">${holdBtn(T.length, "trial-hint", "trials")}</div>
    <p class="hint" id="trial-hint">${done ? "Sent. This page updates in about a minute." : "Hold for a second. They post as trial reels, 2.5 hours apart."}</p>
  </section>`;
}

function home() {
  return `<div class="home"><div class="left">${clock()}${nextUp()}${waiting()}${trialsWaiting()}${threadsWaiting()}${splits()}</div><section class="right" aria-labelledby="fc-h">${weekList()}</section></div>`;
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
    ${studioBoard()}
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
  const sw = `<span class="toggle" role="group" aria-label="Results for"><button data-rview="you" aria-pressed="${rview === "you"}">You</button><button data-rview="rivals" aria-pressed="${rview === "rivals"}">Rivals</button></span>`;
  return rview === "rivals" ? rivals(sw) : resultsYou(sw);
}

// ---------------------------------------------------------------- results > rivals (competitor outliers + idea cards)
const MEASURED = ["instagram", "youtube"];
const ADAPTED = { tiktok: "TikTok", facebook: "Facebook", threads: "Threads" };
function rivals(sw) {
  const C = D.competitors || {};
  const ideas = C.ideas || [], outs = C.outliers || [], accs = C.accounts || [];
  const head = `<div class="page-head"><div class="head"><h1 class="h1">Results</h1>${sw}</div>
    <p class="lede">Posts from creators close to you that did at least 3× their own normal, and what you'd make from them.</p></div>`;
  if (!ideas.length && !outs.length) return head + `<p class="empty-note">No competitor data yet. The Competitors workflow measures the creators in production/competitors/accounts.json every Monday.</p>`;
  const chips = ["all", "instagram", "youtube", "tiktok", "facebook", "threads"].map((k) =>
    `<button data-rplat="${k}" aria-pressed="${rplat === k}">${k === "all" ? "All" : PLAT[k]}</button>`).join("");
  const adapted = ADAPTED[rplat];
  const pv = (c) => (c.platforms || {})[rplat === "all" ? "instagram" : rplat] || "";
  const best = (c) => (c.evidence || []).slice().sort((a, b) => b.x - a.x)[0];
  const card = (c) => {
    const e = best(c), used = sent.has("rival:" + c.id), more = (c.evidence || []).length - 1;
    return `<article class="rcard" aria-labelledby="rc-${esc(c.id)}">
      <h3 id="rc-${esc(c.id)}">${esc(c.title)}</h3>
      ${e ? `<p class="proof"><span class="num xbig">${e.x}×</span><span><a href="${esc(e.url)}" target="_blank" rel="noopener">${n(e.views)} views on @${esc(e.handle)}</a>${more > 0 ? `, ${more} more like it` : ""}<br><small>${esc(c.pattern)}</small></span></p>` : ""}
      <p class="yhook">${esc(c.version?.hook || "")}</p>
      <ol class="beats">${(c.version?.beats || []).map((b) => `<li>${esc(b)}</li>`).join("")}</ol>
      ${pv(c) ? `<p class="pv"><b>${rplat === "all" ? "Instagram" : PLAT[rplat]}</b>${esc(pv(c))}</p>` : ""}
      <details class="why"><summary>Why it worked, what you need</summary><p>${esc(c.why)}${c.version?.needs ? ` <b>Needs:</b> ${esc(c.version.needs)}` : ""}</p></details>
      <div class="row-actions"><button class="btn ${used ? "" : "line"}" data-useidea="${esc(c.id)}" ${used ? "disabled" : ""}>${used ? "Sent to your ideas" : "Use this idea"}</button></div>
    </article>`;
  };
  const skip = new Set(C.skip || []);
  const shown = outs.filter((o) => !skip.has(o.id) && (rplat === "all" || o.platform === rplat)).slice(0, 24);
  const orow = (o) => `<li><a href="${esc(o.url)}" target="_blank" rel="noopener">
      <span class="num ox ${o.x >= 10 ? "hot" : ""}">${o.x}×</span>
      <span class="ot"><b>${esc(o.hook || "(no caption)")}</b><small>@${esc(o.handle)} on ${PLAT[o.platform]}, ${n(o.views)} views (normal ${n(o.median_views)})</small></span></a></li>`;
  const counts = Object.fromEntries(accs.map((a) => [a.platform + a.handle, outs.filter((o) => o.handle === a.handle && o.platform === a.platform).length]));
  const accRows = accs.filter((a) => rplat === "all" || a.platform === rplat || adapted).map((a) =>
    `<tr><td><b>${esc(a.name)}</b><small>${esc(a.why)}</small></td><td>${PLAT[a.platform]}</td><td>${n(a.followers)}</td><td>${a.median_views ? n(a.median_views) : "n/a"}</td><td>${counts[a.platform + a.handle] || 0}</td></tr>`).join("");
  return head + `<div class="filters" role="group" aria-label="Platform">${chips}</div>
    ${adapted ? `<p class="note-adapted">${adapted} doesn't let anyone read other creators' posts, so these ideas come from proven Instagram and YouTube outliers, rewritten for ${adapted}.</p>` : ""}
    <section aria-labelledby="ri-h"><div class="head"><h2 class="h2" id="ri-h">Ideas for you</h2><span class="label">${ideas.length} from real outliers</span></div>
      <div class="rcards">${ideas.map(card).join("")}</div></section>
    ${adapted ? "" : `<section class="section" aria-labelledby="ro-h"><div class="head"><h2 class="h2" id="ro-h">Outliers</h2><span class="label">${C.rule || ""}</span></div>
      ${shown.length ? `<ol class="outliers">${shown.map(orow).join("")}</ol>` : `<p class="empty-note">No outliers on this platform yet.</p>`}</section>`}
    <section class="section" aria-labelledby="ra-h"><div class="head"><h2 class="h2" id="ra-h">Who we watch</h2></div>
      <div class="scroll"><table class="accs"><thead><tr><th scope="col">Creator</th><th scope="col">Platform</th><th scope="col">Followers</th><th scope="col">Normal</th><th scope="col">Outliers</th></tr></thead>
      <tbody>${accRows}</tbody></table></div>
      <p class="hint">Measured every Monday${C.updated ? `, last ${ago(C.updated)}` : ""}. Add creators in production/competitors/accounts.json.</p></section>`;
}

function resultsYou(sw) {
  const med = D.baseline.median_views;
  const rows = Object.entries(D.formats).map(([k, v]) => ({ k, ...v, avg: v.views / v.reels, fpk: v.views ? (1000 * v.follows) / v.views : 0 }))
    .sort((a, b) => b.avg - a.avg);
  if (!rows.length) {
    return `<div class="page-head"><div class="head"><h1 class="h1">Results</h1>${sw}</div></div>
      <p class="empty-note">Results show up 72 hours after a reel posts. The numbers come from Instagram every 2 hours and each reel is compared with your normal${med ? ` ${n(med)}` : ""} views.</p>
      ${growthPanel()}${hookTests()}`;
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
  return `<div class="page-head"><div class="head"><h1 class="h1">Results</h1>${sw}</div><p class="lede">Which formats earn views, and which turn views into followers.</p></div>
    ${verdicts}
    ${growthPanel()}
    ${hookTests()}
    <section class="section" aria-labelledby="l-h"><div class="head"><h2 class="h2" id="l-h">Every format</h2>
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
    ${D.baseline.updated ? `<p class="hint">From Instagram, updated ${ago(D.baseline.updated)}.</p>` : ""}
    ${crossResults()}
    ${styleTests()}`;
}

function styleTests() {
  const ex = (D.lab?.experiments || []).filter((e) => e.status !== "proposed").slice(-6).reverse();
  if (!ex.length) return "";
  const st = { testing: "Testing", decided: "Decided", rejected: "Kept current" };
  return `<section class="section" aria-labelledby="sl-h"><div class="head"><h2 class="h2" id="sl-h">Style tests</h2></div>
    <div class="scroll"><table><thead><tr><th>Test</th><th>A (current)</th><th>B (your pick)</th><th>Reels A / B</th><th>vs normal A / B</th><th>Status</th></tr></thead>
    <tbody>${ex.map((e) => `<tr><td>${esc(e.aspect.replace("_", " "))}</td><td>${esc(e.control)}</td><td>${esc(e.b || "–")}</td>
      <td>${e.n ? `${e.n.a} / ${e.n.b}` : "0 / 0"}</td><td>${e.median_vs_normal ? `${e.median_vs_normal.a ?? "–"} / ${e.median_vs_normal.b ?? "–"}` : "–"}</td>
      <td>${st[e.status] || esc(e.status)}${e.winner ? `: ${esc(e.winner)}` : ""}</td></tr>`).join("")}</tbody></table></div>
    <p class="hint">Every other new reel uses B until both sides have 6 reels with numbers; the winner becomes the default.</p></section>`;
}

function crossResults() {
  const posts = D.platforms?.posts || {};
  const ids = Object.keys(posts);
  if (!ids.length) return "";
  const hook = (id) => calm(D.reels.find((r) => r.id === id)?.hook || id);
  const cols = ["instagram", "facebook", "youtube", "threads"].filter((k) => ids.some((id) => posts[id][k]));
  const tot = Object.fromEntries(cols.map((k) => [k, ids.reduce((a, id) => a + (posts[id][k]?.views || 0), 0)]));
  return `<section class="section" aria-labelledby="xr-h"><div class="head"><h2 class="h2" id="xr-h">Views per platform</h2></div>
    <div class="scroll"><table><thead><tr><th>Reel</th>${cols.map((k) => `<th>${PLAT[k]}</th>`).join("")}</tr></thead>
    <tbody>${ids.map((id) => `<tr><td>${esc(hook(id))}</td>${cols.map((k) => { const m = posts[id][k]; return `<td>${m ? (m.url ? `<a href="${esc(m.url)}" target="_blank" rel="noopener">${n(m.views)}</a>` : n(m.views)) : "–"}</td>`; }).join("")}</tr>`).join("")}
      <tr class="tot"><td>Total</td>${cols.map((k) => `<td>${n(tot[k])}</td>`).join("")}</tr></tbody></table></div>
    <p class="hint">Last 10 days, checked every 2 hours. Followers per platform are on the Activity tab.</p></section>`;
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
        return `<section class="q" aria-labelledby="q-${esc(q.id)}"><h3 id="q-${esc(q.id)}">${esc(q.question)}</h3>${q.image ? `<img class="qimg" src="${esc(q.image)}" alt="The options side by side, numbered" loading="lazy">` : ""}${q.context ? `<p class="ctx">${esc(q.context)}</p>` : ""}
          <div class="opts" role="group" aria-labelledby="q-${esc(q.id)}">${(q.options || []).map((o, k) => `<button class="opt ${pick === k ? "picked" : ""}" data-q="${esc(q.id)}" data-k="${k}" aria-pressed="${pick === k}" ${sentK ? "disabled" : ""}>${esc(o)}</button>`).join("")}</div>
          ${sentK ? `<p class="sent-note">Answer sent.</p>` : ""}</section>`;
      }).join("")
    : pendingThreads().length ? "" : `<p class="empty-note">Nothing to decide right now.</p>`;
  h += threadsSection();
  h += inboxSection();
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

function inboxSection() {
  const all = (D.platforms?.inbox || []).filter((c) => !hidden.has(c.platform + ":" + c.id));
  const open = all.filter((c) => !c.answered), answered = all.filter((c) => c.answered).slice(0, 5);
  const row = (c) => `<li><div><p class="t">${esc(c.text)}</p>
      <p class="m"><b>${esc(c.who || "someone")}</b> on ${PLAT[c.platform] || esc(c.platform)}, <time datetime="${esc(c.at)}">${ago(c.at)}</time>${c.on ? ` · ${esc(calm(c.on)).slice(0, 70)}` : ""}</p></div>
      <span class="iacts">${c.url ? `<a class="btn line" href="${esc(c.url)}" target="_blank" rel="noopener">Reply</a>` : ""}<button class="link" data-done="${esc(c.platform + ":" + c.id)}">Done</button></span></li>`;
  return `<section class="section inbox" aria-labelledby="ib-h"><div class="head"><h2 class="h2" id="ib-h">Comments to answer</h2></div>
    <p class="lede">New comments on Instagram, Facebook and Threads from the last 4 days. Replying in the first hour is the biggest growth lever, and it stays yours: nothing here replies for you.</p>
    ${open.length ? `<ul class="cmts">${open.map(row).join("")}</ul>` : `<p class="empty-note">No open comments. ${D.platforms?.updated ? `Checked ${ago(D.platforms.updated)}.` : ""}</p>`}
    ${answered.length ? `<p class="label" style="margin-top:16px">You already replied</p><ul class="cmts done">${answered.map(row).join("")}</ul>` : ""}</section>`;
}

const KIND = { take: "Hot take", question: "Question", tip: "Tip", story: "Lesson", chain: "Thread" };
function threadsSection() {
  const T = pendingThreads();
  const set = (D.threads_posts || []).filter((p) => p.status === "queued" && p.approved && !sent.has("skip:" + p.id) && new Date(p.at) > Date.now());
  if (!T.length && !set.length) return "";
  const done = sent.has("approve_threads");
  const post = (p, st) => `<li><time datetime="${esc(p.at)}">${t12(p.at)}</time><div><p class="t">${esc(D.edits?.[p.id] ?? p.text)}</p>
      ${(p.chain || []).length ? `<ol class="chain">${p.chain.map((c) => `<li>${esc(c)}</li>`).join("")}</ol>` : ""}
      <p class="m">${KIND[p.kind] || esc(p.kind)}${p.topic ? `, ${esc(p.topic)}` : ""} <span class="st ${st}">${LABEL[st]}</span>
        <span class="tacts"><button class="link" data-tedit="${esc(p.id)}">Edit</button><button class="link" data-tskip="${esc(p.id)}">Skip</button></span></p></div></li>`;
  const byDay = (list, st) => {
    const days = [];
    for (const p of list) {
      const k = dayKey(new Date(p.at));
      if (!days.length || days[days.length - 1].k !== k) days.push({ k, t: p.at, posts: [] });
      days[days.length - 1].posts.push(p);
    }
    return days.map((d) => `<p class="rd">${F.day.format(new Date(d.t))}</p><ul class="tposts">${d.posts.map((p) => post(p, st)).join("")}</ul>`).join("");
  };
  let h = `<section class="section threads" aria-labelledby="th-h"><div class="head"><h2 class="h2" id="th-h">Threads posts</h2></div>`;
  if (T.length) {
    h += `<p class="lede">${T.length} written posts for ${F.short.format(new Date(T[0].at))} to ${F.short.format(new Date(T[T.length - 1].at))}, New York time. Approving is your yes for exactly these; they post on their own at these times. Not happy with one? Send it as an idea below and Claude rewrites it.</p>
      <div class="row-actions">${holdBtn(T.length, "th-hint", "threads")}</div>
      <p class="hint" id="th-hint">${done ? "Sent. This page updates in about a minute." : "Hold for a second. Nothing goes out by accident."}</p>
      ${byDay(T, "needs_yes")}`;
  }
  if (set.length) h += `<p class="label" style="margin-top:20px">Approved, coming up</p>${byDay(set.slice(0, 9), "scheduled")}`;
  return h + `</section>`;
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

// ---------------------------------------------------------------- platforms
function platformsPanel() {
  const P = D.platforms?.platforms;
  if (!P) return "";
  const when = (iso) => (iso ? F.full.format(new Date(iso)).replace(" AM", "am").replace(" PM", "pm") : "n/a");
  const order = ["instagram", "facebook", "youtube", "threads"].filter((k) => P[k]);
  return `<section aria-labelledby="pf-h"><div class="head"><h2 class="h2" id="pf-h">Platforms</h2></div>
    <div class="scroll"><table><thead><tr><th>Platform</th><th>Followers</th><th>Plan / day</th><th>Last 7 days</th><th>Next slot</th><th>Status</th></tr></thead>
    <tbody>${order.map((k) => { const p = P[k]; return `<tr><td>${PLAT[k]}</td><td>${n(p.followers)}</td><td title="${esc(p.plan_mix || "")}">${p.plan_per_day ?? "n/a"}</td><td class="${p.plan_per_day && p.posted_7d < p.plan_per_day * 7 * 0.7 && p.last_post ? "warn" : ""}">${p.posted_7d ?? 0} of ${(p.plan_per_day || 0) * 7}</td><td>${p.enabled === false ? "off" : when(p.next_slot)}</td>
      <td class="${p.warn ? "warn" : ""}">${esc(p.warn || "OK")}${p.errors?.length ? `<br><small>${esc(p.errors[0])}</small>` : ""}</td></tr>`; }).join("")}</tbody></table></div>
    <p class="hint" style="margin-top:12px">Plan per day: ${order.map((k) => `${PLAT[k]} ${esc(P[k].plan_mix || "")}`).join(", ")}. Checked ${ago(D.platforms.updated)}. Logins: ${order.filter((k) => P[k].token_expires).map((k) => `${PLAT[k]} until ${F.short.format(new Date(P[k].token_expires + "T12:00:00"))}`).join(", ") || "no expiry"}.</p></section>`;
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
      </dl><p class="hint" style="margin-top:12px">Times are New York time.</p>
        <div class="runrow"><button class="btn line" data-run="refresh_stats" ${sent.has("run:refresh_stats:") ? "disabled" : ""}>Refresh numbers</button>
          <button class="btn line" data-run="make_listicles" data-count="7" ${sent.has("run:make_listicles:") ? "disabled" : ""}>Make 7 listicles</button></div>
        <p class="hint" style="margin-top:8px">New listicles wait for your yes like every week.</p></section>
      ${platformsPanel()}
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
    <div class="cover">${r.video ? `<video src="${esc(r.video)}" poster="${esc(r.cover || "")}" controls playsinline preload="metadata"></video>` : cover(r)}</div>
    <div><span class="st ${s}">${LABEL[s]}</span><h2 id="sheet-title">${esc(calm(r.hook))}</h2>
      <p class="meta">${fmtName(r.format)}${when ? `<br>${when}` : ""}${r.clip ? `<br>Clip: ${esc(r.clip)}` : ""}</p></div>
    ${m.views != null ? `<dl>${stat("Views", n(m.views))}${stat("vs normal", m.vs_median_x != null ? xTxt(m.vs_median_x) : "n/a", isWin(r) ? "gold" : "")}${stat("Follows", n(m.follows))}${stat("Shares", n(m.shares))}${stat("Saves", n(m.saves))}${stat("Skip rate", m.skip_rate != null ? Math.round(m.skip_rate) + "%" : "n/a")}</dl>` : ""}
    ${s === "win" ? `<p class="note">Winner. Repost it to your grid from the Instagram app with a trending sound; Claude sent suggestions on Telegram.</p>` : ""}
    ${r.error ? `<p class="err">Failed to post: ${esc(r.error).slice(0, 220)}. Claude looks at it on the next morning check.</p>` : ""}
    <div class="foot">${r.permalink ? `<a class="btn" href="${esc(r.permalink)}" target="_blank" rel="noopener">Instagram</a>` : ""}${Object.entries(r.links || {}).map(([k, u]) => `<a class="btn line" href="${esc(u)}" target="_blank" rel="noopener">${PLAT[k] || esc(k)}</a>`).join("")}${r.video ? `<a class="btn line" href="${esc(r.video)}" download>Download</a>` : ""}<button class="btn line" data-close>Close</button></div>
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
function openEdit(id) {
  const p = (D.threads_posts || []).find((x) => x.id === id);
  if (!p) return;
  const dlg = $("#sheet");
  dlg.innerHTML = `<div class="sheet edit"><div><h2 id="sheet-title">Edit Threads post</h2><p class="meta">${F.full.format(new Date(p.at)).replace(" AM", "am").replace(" PM", "pm")} New York${(p.chain || []).length ? ". Saving removes its follow-up replies." : ""}</p></div>
    <label class="field" for="tedit">Text (max 500 characters)</label><textarea id="tedit" maxlength="500" rows="8">${esc(D.edits?.[id] ?? p.text)}</textarea>
    <div class="foot"><button class="btn" data-tsave="${esc(id)}">Save</button><button class="btn line" data-close>Cancel</button></div></div>`;
  dlg.showModal(); $("#tedit").focus();
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
  const open = D.questions.filter((q) => q.status === "open" && ![...sent].some((k) => k.startsWith(`q:${q.id}:`))).length
    + (pendingThreads().length && !sent.has("approve_threads") ? 1 : 0)
    + (pendingTrials().length && !sent.has("approve_trials") ? 1 : 0);
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
  if (t.dataset.rview) { rview = t.dataset.rview; try { localStorage.setItem("rview", rview); } catch {} return render(); }
  if (t.dataset.rplat) { rplat = t.dataset.rplat; return render(); }
  if (t.dataset.useidea) {
    const c = (D.competitors?.ideas || []).find((x) => x.id === t.dataset.useidea);
    if (!c) return;
    const plat = rplat === "all" ? "instagram" : rplat;
    const text = `From Rivals: ${c.title}. Hook: ${c.version?.hook || ""}. Beats: ${(c.version?.beats || []).join(" / ")}. ${PLAT[plat]}: ${(c.platforms || {})[plat] || ""}`.slice(0, 1500);
    t.disabled = true;
    return act({ action: "idea", text }, "rival:" + c.id, "Sent to your ideas. Claude picks it up on the next check.");
  }
  if (t.dataset.run) {
    const { run: job, slug = "", variants, count } = t.dataset;
    const msg = { reel_render: "Render started. The phone cuts land in Drive and here in about 30 to 60 minutes.",
      refresh_stats: "Refreshing. New numbers in a few minutes.", make_listicles: "Making 7 listicles. They show up for your yes when done." }[job];
    t.disabled = true;
    return act({ action: "run", job, slug, variants, count }, `run:${job}:${slug}`, msg);
  }
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
  if (t.dataset.done) { hidden.add(t.dataset.done); saveHidden(); return render(); }
  if (t.dataset.tskip) {
    const id = t.dataset.tskip;
    return act({ action: "threads_skip", id }, "skip:" + id, "Skipped. It won't be posted.");
  }
  if (t.dataset.tedit) return openEdit(t.dataset.tedit);
  if (t.dataset.tsave) {
    const id = t.dataset.tsave, text = $("#tedit").value.trim();
    if (!text) return toast("Write the post first.");
    if (text.length > 500) return toast(`Threads allows 500 characters; this is ${text.length}.`);
    act({ action: "threads_edit", id, text }, "edit:" + id + ":" + text.length, "Saved. The new text posts at the same time.").then((ok) => {
      if (ok) { D.edits = { ...(D.edits || {}), [id]: text }; $("#sheet").close(); render(); }
    });
  }
});
document.addEventListener("submit", (e) => {
  const f = e.target.closest("[data-ingest]");
  if (!f) return;
  e.preventDefault();
  const slug = f.slug.value.trim().toLowerCase(), footage = f.footage.value.trim() || "newest";
  act({ action: "run", job: "reel_ingest", slug, footage }, `run:reel_ingest:${slug}`, "Bringing it in. The transcript is ready in about 10 minutes; then ask Claude for the edit.");
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
    if (b.dataset.hold === "trials") {
      const rids = pendingTrials().map((r) => r.id);
      act({ action: "approve_week", ids: rids }, "approve_trials", `Approved ${rids.length} trial reels. They post on their own.`);
      return;
    }
    if (b.dataset.hold === "threads") {
      const tids = pendingThreads().map((p) => p.id);
      act({ action: "approve_threads", ids: tids }, "approve_threads", `Approved ${tids.length} Threads posts. They post at their times.`);
      return;
    }
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
  if (b) { b.classList.remove("holding"); holdLabel(b, `Hold to approve ${(HOLD[b.dataset.hold] || HOLD.week).count()}`); }
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
