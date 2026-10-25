// Platforms (views, followers, per-platform settings and briefs), Leads (THE PROTOCOL signups to DM, /api/leads)
// and Grow (automations and money, each one tap away from Claude's idea inbox). Uses app.js helpers
// ($, esc, n, ago, F, PLAT, calm, act, toast, render, go, D, sent, VIEWS) like studio.js.
"use strict";
const PL = ["instagram", "facebook", "youtube", "threads"];
const PL_SHORT = { instagram: "IG", facebook: "FB", youtube: "YT", threads: "TH" };
let psub = (() => { try { return localStorage.getItem("psub") || "overview"; } catch { return "overview"; } })();
let lsub = "leads"; // Leads tab: leads | grow
let lfilter = "todo";
let LEADS = null, leadsErr = "", leadsAt = 0;

// ---------------------------------------------------------------- numbers per platform
const median = (a) => {
  const s = a.filter((x) => x != null).sort((x, y) => x - y);
  return s.length ? (s.length % 2 ? s[(s.length - 1) / 2] : (s[s.length / 2 - 1] + s[s.length / 2]) / 2) : null;
};
// views per post on every platform, from the Platform stats workflow (production/control/platforms.json, ~10 days)
function platStats() {
  const posts = D.platforms?.posts || {}, P = D.platforms?.platforms || {};
  const when = Object.fromEntries((D.reels || []).map((r) => [r.id, r.posted_at || r.time]));
  const out = {};
  for (const k of PL) {
    const list = Object.entries(posts).filter(([, v]) => v[k] && v[k].views != null)
      .map(([id, v]) => ({ id, views: v[k].views, url: v[k].url, at: when[id] || "" }))
      .sort((a, b) => (a.at > b.at ? 1 : -1));
    const views = list.reduce((a, p) => a + p.views, 0);
    out[k] = { k, list, views, posts: list.length, med: median(list.map((p) => p.views)), best: list.slice().sort((a, b) => b.views - a.views)[0],
      followers: P[k]?.followers ?? null, cfg: D.crosspost?.platforms?.[k] || null, live: P[k] || {} };
  }
  const total = PL.reduce((a, k) => a + out[k].views, 0);
  PL.forEach((k) => (out[k].share = total ? out[k].views / total : 0));
  return { by: out, total, followers: PL.reduce((a, k) => a + (out[k].followers || 0), 0) };
}

// one honest verdict per platform, from its own numbers (never invented)
function verdict(s) {
  const live = s.live, ig = platStats.ig;
  if (s.cfg && s.cfg.enabled === false) return { cls: "off", txt: "Paused", why: s.cfg.paused_note || "Turned off." };
  if (live.warn || live.errors?.length) return { cls: "red", txt: "Issue", why: live.warn || live.errors[0] };
  const plan = (live.plan_per_day || 0) * 7;
  if (plan && live.last_post && live.posted_7d < plan * 0.7) return { cls: "red", txt: "Under plan", why: `${live.posted_7d} of ${plan} posts in 7 days.` };
  if (!s.posts) return { cls: "", txt: "No data", why: "No numbers in the last 10 days yet." };
  if (s.k !== "instagram" && ig?.med && s.med < ig.med * 0.05) return { cls: "red", txt: "Low reach", why: `Median ${n(s.med)} views a post, under 5% of Instagram's ${n(ig.med)}.` };
  return { cls: "ok", txt: "Healthy", why: `Median ${n(s.med)} views a post over ${s.posts} posts.` };
}

// what each platform rewards: research in tools/crosspost/README.md + our own numbers (STATUS, LEDGER)
const PLAYBOOK = {
  instagram: { role: "Source and growth engine", what: ["Identity and contrast hooks (\"6 signs you were born to be a fighter\").", "Trial reels first, share the 72 h winner to the grid and pin it.", "Answer every comment in the first hour; keyword comments trigger DMs."], fix: "Below normal: test a new opening type in the 15:30 hook test, not a new topic." },
  facebook: { role: "Older, broader reach", what: ["Only proven Instagram winners, 1 a day.", "List on screen + music: Facebook plays muted and skims.", "Short story caption, a question last, max 3 hashtags."], fix: "Low reach: check Page quality and recommendation eligibility in the Professional dashboard first." },
  youtube: { role: "Search and long tail", what: ["Keyword title a fighter would type (\"how to stop gassing out\").", "Loops: the last line flows into the first.", "1 long-form a week later on builds subscribers for the Partner Program."], fix: "Low reach: retitle the 3 best Shorts as search questions." },
  threads: { role: "Voice and conversation", what: ["Written takes and questions beat reposted reels.", "Reply to every reply: replies are the reach.", "One topic tag (Fight Psychology), no hashtags."], fix: "Low reach: more questions, fewer lists, reply within the hour." },
};

const spark = (list, cls = "") => {
  const L = list.slice(-14);
  if (!L.length) return `<span class="spark empty" aria-hidden="true"></span>`;
  const max = Math.max(...L.map((p) => p.views), 1);
  return `<svg class="spark ${cls}" viewBox="0 0 ${L.length * 6} 24" preserveAspectRatio="none" aria-hidden="true">${L.map((p, i) =>
    `<rect x="${i * 6}" y="${24 - Math.max(1.5, (22 * p.views) / max)}" width="4" height="${Math.max(1.5, (22 * p.views) / max)}" rx="1"/>`).join("")}</svg>`;
};

// ---------------------------------------------------------------- home: the readout strip
function kpiStrip() {
  const S = platStats(); platStats.ig = S.by.instagram;
  if (!S.total && !S.followers) return "";
  const newLeads = LEADS ? LEADS.filter((l) => l.status === "new" && l.handle).length : null;
  return `<section class="kpis hud" aria-label="Views and reach">
    <div class="kpi main"><span class="cap">Views, last 10 days</span><span class="big num">${n(S.total)}</span>
      <span class="sub">${n(S.followers)} followers across platforms</span></div>
    <ul class="kpi-pl">${PL.map((k) => { const s = S.by[k], v = verdict(s); return `<li><button data-goto="platforms" data-psub="${k}" aria-label="${PLAT[k]}: ${n(s.views)} views, ${v.txt}">
      <span class="pl"><i class="dot ${v.cls}"></i>${PL_SHORT[k]}</span><span class="num">${n(s.views)}</span>
      <span class="pbar"><i style="width:${Math.round(100 * s.share)}%"></i></span></button></li>`; }).join("")}</ul>
    ${newLeads ? `<button class="kpi-lead" data-goto="leads"><span class="num">${newLeads}</span> lead${newLeads === 1 ? "" : "s"} to message <span aria-hidden="true">→</span></button>` : ""}
  </section>`;
}

// ---------------------------------------------------------------- platforms
function platforms() {
  const S = platStats(); platStats.ig = S.by.instagram;
  const subs = [["overview", "Overview"], ...PL.map((k) => [k, PLAT[k]]), ["formats", "Formats"], ["rivals", "Rivals"], ["reels", "Reels"]];
  const nav = `<div class="seg-tabs" role="tablist" aria-label="Platforms">${subs.map(([k, l]) => `<button role="tab" data-psub="${k}" aria-selected="${psub === k}">${l}</button>`).join("")}</div>`;
  let body;
  if (psub === "formats") body = resultsYou("");
  else if (psub === "rivals") body = rivals("");
  else if (psub === "reels") body = reels();
  else if (PL.includes(psub)) body = platformDetail(S.by[psub]);
  else body = overview(S);
  return `<div class="page-head"><h1 class="h1">Platforms</h1></div>${nav}<div class="psub">${body}</div>`;
}

function overview(S) {
  if (!S.total) return `<p class="empty-note">No platform numbers yet. The Platform stats workflow checks every platform every few hours.</p>`;
  return `<div class="ptotal hud"><div><span class="cap">Total views, last 10 days</span><span class="big num">${n(S.total)}</span></div>
      <div class="stack" aria-hidden="true">${PL.map((k) => `<i class="pl-${k}" style="flex:${S.by[k].views || 0.0001}"></i>`).join("")}</div>
      <p class="legend2">${PL.map((k) => `<span><i class="pl-${k}"></i>${PLAT[k]} ${Math.round(100 * S.by[k].share)}%</span>`).join("")}</p></div>
    <div class="pcards">${PL.map((k) => { const s = S.by[k], v = verdict(s); return `<button class="pcard hud" data-psub="${k}">
      <span class="ph2"><b>${PLAT[k]}</b><span class="chip ${v.cls}">${v.txt}</span></span>
      <span class="big num">${n(s.views)}</span><span class="cap">views, ${s.posts} posts</span>
      ${spark(s.list, v.cls)}
      <span class="row3"><span><small>Per post</small><b class="num">${s.med != null ? n(s.med) : "n/a"}</b></span><span><small>Followers</small><b class="num">${s.followers != null ? n(s.followers) : "n/a"}</b></span><span><small>7 days</small><b class="num">${s.live.posted_7d ?? 0}/${(s.live.plan_per_day || 0) * 7}</b></span></span>
      <span class="why">${esc(v.why)}</span></button>`; }).join("")}</div>
    <p class="hint">Per-post median is the fair comparison: Instagram posts 4 to 5 a day, Facebook 1. Checked ${ago(D.platforms?.updated)}.</p>`;
}

function platformDetail(s) {
  const k = s.k, v = verdict(s), pb = PLAYBOOK[k], cfg = s.cfg, brief = D.briefs?.[k]?.brief || "";
  const hook = (id) => calm(D.reels.find((r) => r.id === id)?.hook || id);
  const top = s.list.slice().sort((a, b) => b.views - a.views).slice(0, 5);
  const settings = cfg ? `<div class="set-row"><label class="switch"><input type="checkbox" id="pl-on" ${cfg.enabled ? "checked" : ""}><span></span>Posting on ${PLAT[k]}</label></div>
      <label class="field" for="pl-slots">Time slots, New York (24 h, comma separated)</label>
      <input id="pl-slots" class="input mono" value="${esc((cfg.slots || []).join(", "))}" inputmode="numeric" placeholder="10:00, 15:30">`
    : `<p class="hint">Instagram times come from the listicle factory and hook tests (09:00, 12:30, 15:30, 18:30, 21:30 NY).</p>`;
  return `<section class="pdetail">
    <div class="pd-head hud"><div><span class="cap">${esc(pb.role)}</span><h2 class="h2">${PLAT[k]}</h2></div><span class="chip ${v.cls}">${v.txt}</span></div>
    <div class="pd-figs">${[["Views, 10 days", n(s.views)], ["Per post", s.med != null ? n(s.med) : "n/a"], ["Followers", s.followers != null ? n(s.followers) : "n/a"], ["Posts, 7 days", `${s.live.posted_7d ?? 0}/${(s.live.plan_per_day || 0) * 7}`]].map(([l, x]) => `<div class="hud"><span class="cap">${l}</span><span class="num mid">${x}</span></div>`).join("")}</div>
    <div class="hud chart"><span class="cap">Views per post, oldest to newest</span>${spark(s.list, "tall " + v.cls)}<p class="why">${esc(v.why)}</p></div>
    <div class="two-col">
      <section class="hud"><h3 class="h3">What works here</h3><ul class="ticks">${pb.what.map((w) => `<li>${esc(w)}</li>`).join("")}</ul>
        ${v.cls === "red" ? `<p class="fixit"><b>Fix first</b>${esc(pb.fix)}</p>` : ""}</section>
      <section class="hud"><h3 class="h3">Top posts</h3>${top.length ? `<ol class="toplist">${top.map((p) => `<li><a href="${esc(p.url || "#")}" target="_blank" rel="noopener"><span class="num">${n(p.views)}</span><span>${esc(hook(p.id))}</span></a></li>`).join("")}</ol>` : `<p class="hint">No posts with numbers yet.</p>`}</section>
    </div>
    <section class="hud tailor"><h3 class="h3">Tailor ${PLAT[k]}</h3>
      ${settings}
      <label class="field" for="pl-brief">Your direction for ${PLAT[k]} content</label>
      <textarea id="pl-brief" rows="3" placeholder="${k === "threads" ? "More hot takes about sparring, fewer lists. Ask a question every evening." : k === "facebook" ? "Only fight-psychology winners. Captions that tell a short story." : k === "youtube" ? "Titles as questions fighters search. Put the best Short first each day." : "More identity hooks, fewer tips. Keep the builder lane at 2 a week."}">${esc(brief)}</textarea>
      <p class="hint">Claude reads this before writing any ${PLAT[k]} caption, title or post.${D.briefs?.[k]?.at ? ` Saved ${ago(D.briefs[k].at)}.` : ""}</p>
      <div class="row-actions"><button class="btn" data-plsave="${k}">Save ${PLAT[k]}</button></div>
    </section>
  </section>`;
}

// ---------------------------------------------------------------- leads
async function loadLeads(force) {
  if (!force && Date.now() - leadsAt < 60000) return;
  leadsAt = Date.now();
  try {
    const r = await fetch("api/leads", { cache: "no-store" });
    if (!r.ok) throw new Error(r.status === 403 ? "login needed" : `error ${r.status}`);
    LEADS = (await r.json()).leads || []; leadsErr = "";
  } catch (e) { leadsErr = e.message; }
  if (D && (tab === "leads" || tab === "home") && !$("#sheet").open && !["dm-tpl", "lnote"].includes(document.activeElement?.id)) render();
}

const FOCUS_LINE = {
  cardio: "gassing out in the later rounds", conditioning: "gassing out in the later rounds", power: "hitting harder",
  strength: "getting stronger without getting slow", mobility: "kicking higher and staying loose", speed: "hand speed",
  mindset: "nerves before sparring", core: "taking body shots",
};
const DEFAULT_TPL = "Hey {name}, Matteo here. You grabbed THE PROTOCOL{focus}. What's the one thing you're stuck on right now in training?";
const tpl = () => { try { return localStorage.getItem("dmTpl") || DEFAULT_TPL; } catch { return DEFAULT_TPL; } };
function dmText(l) {
  const f = String(l.focus || "").toLowerCase(), hit = Object.keys(FOCUS_LINE).find((x) => f.includes(x));
  return tpl().replace("{name}", l.handle ? "@" + l.handle : "").replace("{focus}", hit ? ` for ${FOCUS_LINE[hit]}` : l.focus ? ` (${l.focus})` : "")
    .replace(/\s+([.,?!])/g, "$1").replace(/\s{2,}/g, " ").trim();
}
// coaching fit from their own answers: how often they train, whether they want to compete
function fit(l) {
  let s = 0;
  const fq = String(l.freq || "").toLowerCase(), goal = `${l.goal || ""} ${l.experience || ""}`.toLowerCase();
  if (/[4-7]|daily|every day|twice/.test(fq)) s += 2; else if (/3/.test(fq)) s += 1;
  if (/fight|compet|amateur|pro\b|bout|ring|cage/.test(goal)) s += 2;
  if (l.commented) s += 1;
  if (l.whatsapp) s += 1;
  return s >= 4 ? "hot" : s >= 2 ? "warm" : "";
}
const LSTATUS = { new: "To message", messaged: "Messaged", replied: "Replied", client: "Client", skip: "Skipped" };

function leads() {
  const seg = `<div class="seg-tabs" role="tablist" aria-label="Leads"><button role="tab" data-lsub="leads" aria-selected="${lsub === "leads"}">Leads</button><button role="tab" data-lsub="grow" aria-selected="${lsub === "grow"}">Grow and earn</button></div>`;
  if (lsub === "grow") return `<div class="page-head"><h1 class="h1">Leads</h1></div>${seg}${grow()}`;
  loadLeads();
  const head = `<div class="page-head"><h1 class="h1">Leads</h1><p class="lede">Everyone who grabbed THE PROTOCOL or commented PROTOCOL. Message them, mark it, and the follow-up never slips.</p></div>${seg}`;
  if (!LEADS) return head + `<p class="empty-note">${leadsErr ? `Couldn't load leads (${esc(leadsErr)}).` : "Loading leads…"}</p>`;
  const cnt = (f) => LEADS.filter(f).length;
  const todo = (l) => l.status === "new" && l.handle;
  const F2 = { todo: ["To message", todo], messaged: ["Messaged", (l) => l.status === "messaged"], replied: ["Replied", (l) => l.status === "replied"], client: ["Clients", (l) => l.status === "client"], all: ["All", () => true] };
  const list = LEADS.filter(F2[lfilter][1]);
  const stats = [["Signups", cnt((l) => l.kind !== "comment")], ["With Instagram", cnt((l) => l.handle)], ["To message", cnt(todo)], ["Replied", cnt((l) => l.status === "replied")], ["Clients", cnt((l) => l.status === "client")]];
  const row = (l) => {
    const f = fit(l), chips = [l.focus, l.freq, l.equipment].filter(Boolean);
    return `<li class="lead hud ${l.status}">
      <div class="who">${l.handle ? `<a class="handle" href="https://instagram.com/${esc(l.handle)}" target="_blank" rel="noopener">@${esc(l.handle)}</a>` : `<span class="handle quiet">No Instagram</span>`}
        ${f ? `<span class="chip ${f === "hot" ? "gold" : ""}" title="Coaching fit from their answers">${f === "hot" ? "Hot fit" : "Warm"}</span>` : ""}
        ${l.kind === "comment" ? `<span class="chip" title="Commented PROTOCOL and got the DM, no signup yet">Commented</span>` : l.commented ? `<span class="chip">Commented too</span>` : ""}
        ${l.stance ? `<span class="chip">STANCE</span>` : ""}</div>
      <p class="meta">${chips.map(esc).join(" · ") || (l.kind === "comment" ? "Got the PROTOCOL link by DM" : "No answers")}${l.goal ? `<br>Goal: ${esc(l.goal)}` : ""}</p>
      <p class="when"><time datetime="${esc(l.at)}">${ago(l.at)}</time>${l.email ? ` · <button class="link" data-copy="${esc(l.email)}">${esc(l.email)}</button>` : ""}${l.contacted_at ? ` · messaged ${ago(l.contacted_at)}` : ""}</p>
      <div class="lacts">
        ${l.handle ? `<button class="btn ${l.status === "new" ? "" : "line"} sm" data-dm="${esc(l.key)}">Message</button>` : ""}
        <select class="lsel" data-lstatus="${esc(l.key)}" aria-label="Status for ${esc(l.handle || l.email)}">${Object.entries(LSTATUS).map(([k, t]) => `<option value="${k}" ${l.status === k ? "selected" : ""}>${t}</option>`).join("")}</select>
      </div></li>`;
  };
  return head + `<div class="lstats">${stats.map(([l, x]) => `<div class="hud"><span class="cap">${l}</span><span class="num mid">${x}</span></div>`).join("")}</div>
    <div class="filters" role="group" aria-label="Show">${Object.entries(F2).map(([k, [l, f]]) => `<button data-lfilter="${k}" aria-pressed="${lfilter === k}">${l}<span class="n">${cnt(f)}</span></button>`).join("")}</div>
    ${list.length ? `<ul class="leads">${list.map(row).join("")}</ul>` : `<p class="empty-note">${lfilter === "todo" ? "Everyone with an Instagram handle has been messaged. 🥊" : "Nobody here yet."}</p>`}
    <details class="hud tplbox"><summary>Message template</summary>
      <label class="field" for="dm-tpl">Opening DM. {name} = their handle, {focus} = what they picked.</label>
      <textarea id="dm-tpl" rows="3">${esc(tpl())}</textarea>
      <div class="row-actions"><button class="btn line sm" data-tplsave>Save template</button><button class="link" data-tplreset>Reset</button></div></details>
    <div class="row-actions"><button class="btn line sm" data-csv>Download CSV</button><span class="hint">Message copies a personal DM and opens their Instagram chat; paste and send. Instagram doesn't let any tool cold-DM someone who hasn't messaged you first.</span></div>`;
}

async function leadPost(body) {
  const r = await fetch("api/leads", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify(body) });
  if (!r.ok) throw new Error((await r.json().catch(() => ({}))).error || `error ${r.status}`);
}
async function setStatus(key, status) {
  const l = LEADS.find((x) => x.key === key);
  const was = l.status;
  l.status = status; if (status === "messaged") l.contacted_at = new Date().toISOString();
  render();
  try { await leadPost({ key, status }); } catch (e) { l.status = was; render(); toast(`Not saved (${e.message}).`); }
}
async function copy(text) {
  try { await navigator.clipboard.writeText(text); return true; } catch { return false; }
}
function csv() {
  const cols = ["handle", "email", "status", "focus", "focus2", "freq", "equipment", "experience", "goal", "source", "whatsapp", "at", "contacted_at"];
  const q = (v) => `"${String(v ?? "").replace(/"/g, '""')}"`;
  const blob = new Blob([[cols.join(","), ...LEADS.map((l) => cols.map((c) => q(l[c])).join(","))].join("\n")], { type: "text/csv" });
  const a = Object.assign(document.createElement("a"), { href: URL.createObjectURL(blob), download: `protocol-leads-${new Date().toISOString().slice(0, 10)}.csv` });
  a.click(); setTimeout(() => URL.revokeObjectURL(a.href), 2000);
}

// ---------------------------------------------------------------- grow: automations + money
const LIVE = [
  ["Comment PROTOCOL, get the DM", "Any comment with \"protocol\" gets the link by DM and a public reply."],
  ["Signup ping", "Telegram line for every new PROTOCOL signup, Instagram handle first."],
  ["Hook tests", "4 openings a day, winner called at 72 h, told to share it."],
  ["Facebook daily pick", "Only the best Instagram reel at 72 h goes to Facebook."],
  ["Health check", "Stuck, failed or missed posts and renders to Telegram every 6 h."],
];
const NEXT = [
  { id: "auto-lead-nudge", t: "Lead follow-up nudge", why: "Every evening Telegram lists leads not messaged after 24 h, with the DM ready to paste. The 74 old handles never got a message.", cost: "Free, no AI", effort: "S" },
  { id: "auto-dm-step2", t: "DM step 2 when they reply", why: "When a PROTOCOL lead answers the DM, Instagram allows replies for 24 h: send their focus workout tip plus one question, so the chat keeps going.", cost: "Free", effort: "M" },
  { id: "auto-keywords", t: "A keyword per reel", why: "Each reel gets its own comment word (CARDIO, NERVES, POWER) with its own freebie. More DMs, and we learn which topic pulls leads.", cost: "Free", effort: "S" },
  { id: "auto-email", t: "5-email welcome series", why: "Signups get 5 short emails over 14 days: the story, one drill each, then the paid program. Email is the list Instagram can't take away.", cost: "Free tier", effort: "M" },
  { id: "auto-weekly-report", t: "Monday platform report", why: "Views per platform vs last week, the weakest platform and the one fix, on Telegram before the week starts.", cost: "Free, no AI", effort: "S" },
  { id: "auto-winner-recycle", t: "Winner recycler", why: "A 2× winner comes back 3 weeks later with a new hook and sound, and goes to every platform in its own shape.", cost: "Free", effort: "M" },
];
const MONEY = [
  { id: "money-paid-protocol", t: "Paid PROTOCOL: 8-week fight conditioning", how: "The free test already says what each fighter lacks. The paid plan is that weakness, 8 weeks, 3 sessions a week. Sold on the result page and in DM step 2.", price: "$29 to $49 one-time (estimate)", stage: "First" },
  { id: "money-coaching", t: "Online coaching, by application", how: "Hot-fit leads (train 4+ times a week, want to compete) get an invite to apply. Few spots, weekly check-in videos.", price: "$150 to $300 a month (estimate)", stage: "After 10 paid buyers" },
  { id: "money-brands", t: "Brand deals with a live media kit", how: "A page that pulls these numbers live: views per platform, audience, best reels. Pitch gloves, wraps, recovery and supplement brands.", price: "Depends on reach", stage: "Now, it's free" },
  { id: "money-affiliate", t: "Gear links that pay", how: "Your real gear on matteofights.me/links with affiliate links; listicles about gear point there.", price: "Commission per sale", stage: "Now, small" },
  { id: "money-payouts", t: "Platform payouts", how: "YouTube Partner (Shorts) and Facebook content monetization open as followers and views grow. Requirements change; check YouTube Studio and the Facebook Professional dashboard.", price: "Ad share", stage: "Later" },
];
function grow() {
  const card = (x, kind) => {
    const k = "grow:" + x.id, done = sent.has(k);
    return `<article class="gcard hud"><div class="gh"><h3 class="h3">${esc(x.t)}</h3><span class="chip">${esc(kind === "money" ? x.stage : `${x.cost} · ${x.effort === "S" ? "small" : "medium"} build`)}</span></div>
      <p>${esc(kind === "money" ? x.how : x.why)}</p>${kind === "money" ? `<p class="price num">${esc(x.price)}</p>` : ""}
      <div class="row-actions"><button class="btn ${done ? "" : "line"} sm" data-grow="${esc(x.id)}" ${done ? "disabled" : ""}>${done ? "Sent to Claude" : kind === "money" ? "Plan this with Claude" : "Build this"}</button></div></article>`;
  };
  return `<section class="section"><div class="head"><h2 class="h2">Running now</h2><span class="label">${LIVE.length} automations</span></div>
      <ul class="livelist">${LIVE.map(([t, d]) => `<li><i class="dot ok"></i><b>${esc(t)}</b><span>${esc(d)}</span></li>`).join("")}</ul></section>
    <section class="section"><div class="head"><h2 class="h2">Next automations</h2><span class="label">to grow</span></div>
      <p class="lede">Tap one and it lands in Claude's idea inbox with the plan; nothing goes live without your yes.</p>
      <div class="gcards">${NEXT.map((x) => card(x, "auto")).join("")}</div></section>
    <section class="section"><div class="head"><h2 class="h2">Start earning</h2><span class="label">in order</span></div>
      <p class="lede">The ladder: free PROTOCOL builds the list, a paid plan proves people buy, coaching and brands scale it. Prices are starting estimates to test, not promises.</p>
      <div class="gcards">${MONEY.map((x) => card(x, "money")).join("")}</div></section>`;
}

// ---------------------------------------------------------------- events (capture: a Home button that jumps to a
// platform sets the sub-tab before app.js switches tabs and renders)
document.addEventListener("click", async (ev) => {
  const t = ev.target.closest("button,a");
  if (!t) return;
  if (t.dataset.psub && t.dataset.goto) { psub = t.dataset.psub; try { localStorage.setItem("psub", psub); } catch {} return; } // app.js switches the tab
  if (t.dataset.psub) { psub = t.dataset.psub; try { localStorage.setItem("psub", psub); } catch {} render(); return window.scrollTo(0, 0); }
  if (t.dataset.lsub) { lsub = t.dataset.lsub; return render(); }
  if (t.dataset.lfilter) { lfilter = t.dataset.lfilter; return render(); }
  if (t.dataset.dm) {
    const l = LEADS.find((x) => x.key === t.dataset.dm);
    if (!l) return;
    const ok = await copy(dmText(l));
    window.open(`https://ig.me/m/${encodeURIComponent(l.handle)}`, "_blank", "noopener");
    toast(ok ? "DM copied. Paste it in the chat and send." : "Opened the chat. Copy failed, type it there.");
    if (l.status === "new") setStatus(l.key, "messaged");
    return;
  }
  if (t.dataset.copy) { toast((await copy(t.dataset.copy)) ? "Copied." : "Copy failed."); return; }
  if ("tplsave" in t.dataset) { try { localStorage.setItem("dmTpl", $("#dm-tpl").value.trim() || DEFAULT_TPL); } catch {} toast("Template saved on this device."); return render(); }
  if ("tplreset" in t.dataset) { try { localStorage.removeItem("dmTpl"); } catch {} return render(); }
  if ("csv" in t.dataset) return LEADS && csv();
  if (t.dataset.grow) {
    const x = [...NEXT, ...MONEY].find((y) => y.id === t.dataset.grow);
    t.disabled = true;
    return act({ action: "idea", text: `From Grow: ${x.t}. ${x.why || x.how}${x.price ? ` Price: ${x.price}.` : ""} Plan it and ask me before anything goes live.` },
      "grow:" + x.id, "Sent to Claude's ideas. You get the plan on the next check.");
  }
  if (t.dataset.plsave) {
    const k = t.dataset.plsave, body = { action: "platform_set", platform: k, brief: $("#pl-brief").value.trim() };
    if ($("#pl-on")) body.enabled = $("#pl-on").checked;
    if ($("#pl-slots")) {
      const slots = $("#pl-slots").value.split(/[,\s]+/).filter(Boolean).map((s) => s.padStart(5, "0"));
      const bad = slots.filter((s) => !/^([01]\d|2[0-3]):[0-5]\d$/.test(s));
      if (bad.length) return toast(`Times look like 10:00 or 21:30; check ${bad.join(", ")}.`);
      body.slots = slots;
    }
    if (body.enabled === false && D.crosspost?.platforms?.[k]?.enabled && !confirm(`Stop posting on ${PLAT[k]}?`)) return;
    t.disabled = true;
    const ok = await act(body, "plset:" + k + ":" + Date.now(), `${PLAT[k]} saved. Live in about a minute.`);
    if (ok) { D.briefs = { ...(D.briefs || {}), [k]: { brief: body.brief, at: new Date().toISOString() } }; render(); }
  }
}, true);
document.addEventListener("change", (ev) => {
  const s = ev.target.closest("[data-lstatus]");
  if (s) setStatus(s.dataset.lstatus, s.value);
});

VIEWS.platforms = platforms;
VIEWS.leads = leads;
loadLeads(true);
setInterval(() => loadLeads(), 120000);
