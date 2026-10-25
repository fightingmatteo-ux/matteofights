// Reel player: watch any reel start to finish, stop on any frame, draw on it, say what should change, and send the
// notes as one revision (/api/studio "revision" -> edit worker, tools/edit/WORKER.md). Plus "Your edit taste" on
// Studio: the rules Claude learned from those notes (data.json "taste") and whether revisions fall over time
// (/api/taste). Uses app.js helpers ($, esc, D, toast, calm, LABEL, stateOf, fmtName, n, xTxt, ago) and studio.js (L, api).
"use strict";
const FPS = 30;
const TAGS = [["hook", "Hook"], ["text", "Text"], ["cut", "Cut"], ["pacing", "Pacing"], ["framing", "Framing"], ["color", "Color"], ["audio", "Audio"], ["broll", "B-roll"], ["captions", "Captions"], ["other", "Other"]];
const TAGNAME = Object.fromEntries(TAGS);
const INK = "#E43A33";
const drafts = {}; // reel id -> {notes, text}: unsent notes survive closing the player
let PV = null; // open player: {r, v, mode, tool, strokes, cur, tags, rate}
let TASTE = null, tasteAt = 0;
const reduce = () => matchMedia("(prefers-reduced-motion: reduce)").matches;
const clockT = (s) => { s = Math.max(0, s || 0); return `${Math.floor(s / 60)}:${(s % 60).toFixed(1).padStart(4, "0")}`; };
const ICON = {
  play: `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M8 5.5v13l10.5-6.5z" fill="currentColor" stroke="none"/></svg>`,
  pause: `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M8 5h3v14H8zM13 5h3v14h-3z" fill="currentColor" stroke="none"/></svg>`,
  back: `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M15 6l-6 6 6 6"/></svg>`,
  fwd: `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M9 6l6 6-6 6"/></svg>`,
  close: `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 6l12 12M18 6L6 18"/></svg>`,
  pen: `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 20l1-4L16.5 4.5a2.1 2.1 0 0 1 3 3L8 19z"/></svg>`,
  box: `<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="4.5" y="6.5" width="15" height="11" rx="1"/></svg>`,
  arrow: `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 19L19 5M10 5h9v9"/></svg>`,
  undo: `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M9 7L4 12l5 5M4 12h11a5 5 0 0 1 0 10h-2"/></svg>`,
  mark: `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 20l1-4L16.5 4.5a2.1 2.1 0 0 1 3 3L8 19z"/></svg>`,
};

function srcOf(r) {
  if (r.asset) return `api/media?asset=${encodeURIComponent(r.asset)}`;
  return r.video || null;
}

// ---------------------------------------------------------------- open / close
function openPlayer(id) {
  const r = D.reels.find((x) => x.id === id);
  if (!r || !srcOf(r)) return false;
  const dlg = $("#player");
  const d = (drafts[id] ||= { notes: [], text: "" });
  PV = { r, mode: "watch", tool: "pen", strokes: [], cur: null, tags: new Set(), rate: 1 };
  const s = stateOf(r), m = r.metrics || {};
  const when = r.state === "posted" && r.posted_at ? `Posted ${ago(r.posted_at)}` : r.time ? F.full.format(new Date(r.time)).replace(" AM", "am").replace(" PM", "pm") + " NY" : "";
  const past = (typeof L !== "undefined" && L?.requests || []).filter((q) => q.target === r.id || (r.reel && q.target === r.reel)).sort((a, b) => (a.at > b.at ? -1 : 1));
  dlg.innerHTML = `<div class="pv">
    <header class="pv-top">
      <button class="pv-icon" data-pclose aria-label="Close player">${ICON.close}</button>
      <div class="pv-title"><p class="cap"><span class="st ${s}">${LABEL[s]}</span> · ${fmtName(r.format)}${when ? ` · ${esc(when)}` : ""}</p><h2 id="pv-h">${esc(calm(r.hook))}</h2></div>
    </header>
    <div class="pv-stage">
      <div class="pv-frame" id="pv-frame">
        <video id="pv-v" src="${esc(srcOf(r))}" ${r.cover ? `poster="${esc(r.cover)}"` : ""} playsinline preload="auto"></video>
        <canvas id="pv-ink" class="pv-ink" aria-label="Draw on this frame"></canvas>
        <button class="pv-tap" data-pplay aria-label="Play or pause"></button>
        <p class="pv-load" id="pv-load">Loading video…</p>
      </div>
    </div>
    <div class="pv-side">
      <div class="pv-bar">
        <div class="pv-scrub" id="pv-scrub" role="slider" tabindex="0" aria-label="Position in the reel" aria-valuemin="0" aria-valuemax="0" aria-valuenow="0">
          <div class="pv-track"><i class="pv-prog" id="pv-prog"></i></div><div class="pv-marks" id="pv-marks"></div><i class="pv-knob" id="pv-knob"></i>
        </div>
        <div class="pv-ctl">
          <span class="pv-time num" id="pv-time">0:00.0</span>
          <button class="pv-icon" data-pstep="-1" aria-label="Back one frame" title="Back one frame (←)">${ICON.back}</button>
          <button class="pv-icon pv-play" data-pplay id="pv-play" aria-label="Play" title="Play or pause (space)">${ICON.play}</button>
          <button class="pv-icon" data-pstep="1" aria-label="Forward one frame" title="Forward one frame (→)">${ICON.fwd}</button>
          <button class="pv-rate" data-prate aria-label="Playback speed">1×</button>
          <button class="btn pv-markbtn" data-pmark title="Mark this frame (M)">${ICON.mark}<span>Note this frame</span></button>
        </div>
      </div>
      <section class="pv-compose" id="pv-compose" hidden aria-label="New note">
        <div class="pv-tools" role="group" aria-label="Drawing tool">
          ${["pen", "box", "arrow"].map((t) => `<button class="pv-tool" data-ptool="${t}" aria-pressed="${t === "pen"}" aria-label="${t === "pen" ? "Pen" : t === "box" ? "Box" : "Arrow"}">${ICON[t]}</button>`).join("")}
          <button class="pv-tool" data-pundo aria-label="Undo last mark">${ICON.undo}</button>
          <span class="pv-at num" id="pv-at"></span>
        </div>
        <label class="sr" for="pv-note">What should change at this moment?</label>
        <textarea id="pv-note" rows="2" placeholder="What should change here? Text over his face, cut earlier, punch in…"></textarea>
        <div class="pv-tags" role="group" aria-label="What kind of change">${TAGS.map(([k, l]) => `<button class="pv-tag" data-ptag="${k}" aria-pressed="false">${l}</button>`).join("")}</div>
        <div class="pv-row"><button class="btn line sm" data-pcancel>Cancel</button><button class="btn sm" data-padd>Add note</button></div>
      </section>
      <section class="pv-notes" aria-labelledby="pv-nh">
        <div class="head"><h3 class="h3" id="pv-nh">Notes</h3><span class="label" id="pv-count"></span></div>
        <ol class="pv-list" id="pv-list"></ol>
        <label class="sr" for="pv-general">Anything else about this reel</label>
        <textarea id="pv-general" rows="2" placeholder="Anything about the whole reel (optional)">${esc(d.text)}</textarea>
        <button class="btn pv-send" data-psend id="pv-send">Send revision</button>
        <p class="hint">Claude re-edits it, re-renders the variants it touches, and learns a rule from every note.${s === "posted" ? " This one is already posted: the change goes into the next version." : ""}</p>
        ${m.views != null ? `<p class="pv-stats"><span><small>Views</small><b class="num">${n(m.views)}</b></span><span><small>vs normal</small><b class="num">${xTxt(m.vs_median_x) || "n/a"}</b></span><span><small>Shares</small><b class="num">${n(m.shares)}</b></span><span><small>Saves</small><b class="num">${n(m.saves)}</b></span></p>` : ""}
        ${past.length ? `<details class="pv-past"><summary>${past.length} earlier revision${past.length === 1 ? "" : "s"}</summary><ul>${past.map((q) => `<li><span class="pill ${esc(q.status)}">${esc(q.status)}</span> ${ago(q.at)}${q.round ? `, round ${q.round}` : ""}<br><small>${esc((q.result || q.text || "").slice(0, 200))}</small></li>`).join("")}</ul></details>` : ""}
        <div class="pv-links">${r.permalink ? `<a class="link" href="${esc(r.permalink)}" target="_blank" rel="noopener">Instagram</a>` : ""}${Object.entries(r.links || {}).map(([k, u]) => `<a class="link" href="${esc(u)}" target="_blank" rel="noopener">${PLAT[k] || esc(k)}</a>`).join("")}<a class="link" href="${esc(srcOf(r))}" download>Download</a></div>
      </section>
    </div>
  </div>`;
  dlg.showModal();
  wire(dlg);
  renderNotes();
  return true;
}

function closePlayer() {
  const dlg = $("#player");
  if (!dlg.open) return;
  if (PV) { if (drafts[PV.r.id]) drafts[PV.r.id].text = $("#pv-general").value; PV.v?.pause(); }
  const done = () => { dlg.close(); dlg.classList.remove("out"); dlg.innerHTML = ""; PV = null; render(); };
  if (reduce()) return done();
  dlg.classList.add("out");
  setTimeout(done, 160);
}

// ---------------------------------------------------------------- video + scrubber
function wire(dlg) {
  const v = (PV.v = $("#pv-v", dlg));
  const frame = $("#pv-frame", dlg), cv = $("#pv-ink", dlg);
  v.addEventListener("loadedmetadata", () => {
    frame.style.aspectRatio = `${v.videoWidth} / ${v.videoHeight}`;
    $("#pv-load").hidden = true;
    $("#pv-scrub").setAttribute("aria-valuemax", v.duration.toFixed(1));
    sizeInk(); renderNotes(); tickTime();
  });
  v.addEventListener("error", () => { $("#pv-load").textContent = "Couldn't load this video. It may be older than 21 days and not on the media release."; });
  v.addEventListener("timeupdate", tickTime);
  v.addEventListener("seeked", tickTime);
  v.addEventListener("play", () => { setPlay(true); if (PV.mode === "draw") cancelNote(); });
  v.addEventListener("pause", () => setPlay(false));
  v.addEventListener("ended", () => setPlay(false));
  new ResizeObserver(() => { sizeInk(); drawInk(); }).observe(frame);

  // scrub: drag anywhere on the bar
  const sc = $("#pv-scrub", dlg);
  const seek = (e) => {
    const b = sc.getBoundingClientRect(), x = Math.min(1, Math.max(0, (e.clientX - b.left) / b.width));
    if (v.duration) v.currentTime = x * v.duration;
  };
  sc.addEventListener("pointerdown", (e) => { sc.setPointerCapture(e.pointerId); sc.classList.add("drag"); v.pause(); seek(e); });
  sc.addEventListener("pointermove", (e) => sc.hasPointerCapture(e.pointerId) && seek(e));
  sc.addEventListener("pointerup", () => sc.classList.remove("drag"));
  sc.addEventListener("keydown", (e) => {
    if (e.key === "ArrowLeft" || e.key === "ArrowRight") { e.preventDefault(); step((e.key === "ArrowLeft" ? -1 : 1) * (e.shiftKey ? FPS : 1)); }
  });

  // drawing: normalized coordinates so the strokes survive a resize and export at full size
  const pt = (e) => { const b = cv.getBoundingClientRect(); return [(e.clientX - b.left) / b.width, (e.clientY - b.top) / b.height]; };
  cv.addEventListener("pointerdown", (e) => {
    if (PV.mode !== "draw") return;
    cv.setPointerCapture(e.pointerId);
    PV.cur = { tool: PV.tool, pts: [pt(e)] };
    PV.strokes.push(PV.cur); drawInk();
  });
  cv.addEventListener("pointermove", (e) => {
    if (!PV.cur || !cv.hasPointerCapture(e.pointerId)) return;
    if (PV.cur.tool === "pen") PV.cur.pts.push(pt(e)); else PV.cur.pts[1] = pt(e);
    drawInk();
  });
  cv.addEventListener("pointerup", () => {
    if (PV.cur && PV.cur.tool !== "pen" && PV.cur.pts.length < 2) PV.strokes.pop();
    PV.cur = null; drawInk();
  });
  dlg.addEventListener("cancel", (e) => { e.preventDefault(); PV?.mode === "draw" ? cancelNote() : closePlayer(); });
}

function setPlay(on) {
  const b = $("#pv-play");
  if (!b) return;
  b.innerHTML = on ? ICON.pause : ICON.play;
  b.setAttribute("aria-label", on ? "Pause" : "Play");
  $("#pv-frame").classList.toggle("playing", on);
}
function tickTime() {
  const v = PV?.v;
  if (!v) return;
  const d = v.duration || 0, x = d ? v.currentTime / d : 0;
  $("#pv-time").textContent = `${clockT(v.currentTime)} / ${clockT(d)}`;
  $("#pv-prog").style.transform = `scaleX(${x})`;
  $("#pv-knob").style.left = `${100 * x}%`;
  $("#pv-scrub").setAttribute("aria-valuenow", v.currentTime.toFixed(1));
  $("#pv-scrub").setAttribute("aria-valuetext", clockT(v.currentTime));
  if (PV.mode === "draw") $("#pv-at").textContent = `at ${clockT(v.currentTime)}`;
}
function step(frames) {
  const v = PV.v;
  v.pause();
  v.currentTime = Math.min(v.duration || 0, Math.max(0, v.currentTime + frames / FPS));
}
function togglePlay() {
  const v = PV.v;
  if (PV.mode === "draw") return;
  if (v.paused) { if (v.ended) v.currentTime = 0; v.play().catch(() => {}); } else v.pause();
}

// ---------------------------------------------------------------- ink
function sizeInk() {
  const cv = $("#pv-ink"), f = $("#pv-frame");
  if (!cv || !f) return;
  const dpr = Math.min(2, devicePixelRatio || 1);
  cv.width = Math.round(f.clientWidth * dpr); cv.height = Math.round(f.clientHeight * dpr);
}
function paint(ctx, w, h, strokes) {
  ctx.lineCap = "round"; ctx.lineJoin = "round"; ctx.strokeStyle = INK; ctx.fillStyle = INK;
  ctx.lineWidth = Math.max(3, w / 110);
  ctx.shadowColor = "rgba(0,0,0,.55)"; ctx.shadowBlur = ctx.lineWidth;
  for (const s of strokes) {
    const P = s.pts.map(([x, y]) => [x * w, y * h]);
    ctx.beginPath();
    if (s.tool === "pen") {
      P.forEach(([x, y], i) => (i ? ctx.lineTo(x, y) : ctx.moveTo(x, y)));
      if (P.length === 1) ctx.lineTo(P[0][0] + 0.1, P[0][1]);
      ctx.stroke();
    } else if (s.tool === "box" && P[1]) {
      ctx.strokeRect(Math.min(P[0][0], P[1][0]), Math.min(P[0][1], P[1][1]), Math.abs(P[1][0] - P[0][0]), Math.abs(P[1][1] - P[0][1]));
    } else if (s.tool === "arrow" && P[1]) {
      const [[x0, y0], [x1, y1]] = P, a = Math.atan2(y1 - y0, x1 - x0), L2 = ctx.lineWidth * 4.5;
      ctx.moveTo(x0, y0); ctx.lineTo(x1, y1); ctx.stroke();
      ctx.beginPath(); ctx.moveTo(x1, y1);
      ctx.lineTo(x1 - L2 * Math.cos(a - 0.45), y1 - L2 * Math.sin(a - 0.45));
      ctx.lineTo(x1 - L2 * Math.cos(a + 0.45), y1 - L2 * Math.sin(a + 0.45));
      ctx.closePath(); ctx.fill();
    }
  }
}
function drawInk() {
  const cv = $("#pv-ink");
  if (!cv) return;
  const ctx = cv.getContext("2d");
  ctx.clearRect(0, 0, cv.width, cv.height);
  if (PV?.mode === "draw") paint(ctx, cv.width, cv.height, PV.strokes);
}
// the frame as the edit worker will see it: video pixels + Matteo's marks, 720 px wide
function snapshot() {
  const v = PV.v, w = Math.min(720, v.videoWidth || 720), h = Math.round(w * ((v.videoHeight || 1280) / (v.videoWidth || 720)));
  const c = Object.assign(document.createElement("canvas"), { width: w, height: h });
  const ctx = c.getContext("2d");
  try {
    ctx.drawImage(v, 0, 0, w, h);
    paint(ctx, w, h, PV.strokes);
    return c.toDataURL("image/jpeg", 0.82);
  } catch { return null; } // cross-origin fallback copy: the note still goes, without the picture
}

// ---------------------------------------------------------------- notes
function startNote() {
  const v = PV.v;
  if (!v.duration) return;
  v.pause();
  PV.mode = "draw"; PV.strokes = []; PV.tags = new Set();
  $("#pv-frame").classList.add("drawing");
  const c = $("#pv-compose");
  c.hidden = false;
  $("#pv-note").value = "";
  document.querySelectorAll(".pv-tag").forEach((b) => b.setAttribute("aria-pressed", "false"));
  tickTime(); drawInk();
  $("#pv-note").focus({ preventScroll: true });
  c.scrollIntoView({ block: "nearest", behavior: reduce() ? "auto" : "smooth" });
}
function cancelNote() {
  PV.mode = "watch"; PV.strokes = [];
  $("#pv-frame").classList.remove("drawing");
  $("#pv-compose").hidden = true;
  drawInk();
}
function addNote() {
  const text = $("#pv-note").value.trim();
  if (!text && !PV.strokes.length) { $("#pv-note").focus(); return toast("Draw on the frame or write what should change."); }
  const note = { t: PV.v.currentTime, text, tags: [...PV.tags], image: snapshot() };
  const list = drafts[PV.r.id].notes;
  list.push(note); list.sort((a, b) => a.t - b.t);
  cancelNote(); renderNotes();
  toast(`Note at ${clockT(note.t)} added.`);
}
function renderNotes() {
  if (!PV) return;
  const list = drafts[PV.r.id].notes, d = PV.v?.duration || 0;
  $("#pv-list").innerHTML = list.length ? list.map((nt, i) => `<li class="pv-n">
      <button class="pv-thumb" data-pjump="${nt.t}" aria-label="Go to ${clockT(nt.t)}">${nt.image ? `<img src="${nt.image}" alt="">` : ""}<span class="num">${clockT(nt.t)}</span></button>
      <div><p>${esc(nt.text) || `<span class="quiet">Drawing only</span>`}</p>${nt.tags.length ? `<p class="pv-ntags">${nt.tags.map((t) => `<span class="chip">${esc(TAGNAME[t] || t)}</span>`).join("")}</p>` : ""}</div>
      <button class="pv-icon sm" data-pdel="${i}" aria-label="Delete note at ${clockT(nt.t)}">${ICON.close}</button></li>`).join("")
    : `<li class="pv-empty">Pause anywhere and tap <b>Note this frame</b>. Circle the problem, say what should change.</li>`;
  $("#pv-count").textContent = list.length ? `${list.length} unsent` : "";
  $("#pv-marks").innerHTML = d ? list.map((nt) => `<i style="left:${(100 * nt.t) / d}%"></i>`).join("") : "";
  const b = $("#pv-send");
  b.textContent = list.length ? `Send ${list.length} note${list.length === 1 ? "" : "s"} as a revision` : "Send revision";
}
async function sendRevision(btn) {
  const d = drafts[PV.r.id];
  d.text = $("#pv-general").value.trim();
  if (!d.notes.length && !d.text) return toast("Add a note on a frame first, or write what should change.");
  btn.disabled = true; btn.classList.add("busy"); btn.textContent = "Sending…";
  try {
    await api("api/studio", { action: "revision", target: PV.r.id, asset: PV.r.asset || null, text: d.text,
      notes: d.notes.map((x) => ({ t: x.t, text: x.text, tags: x.tags, image: x.image })) });
    delete drafts[PV.r.id];
    toast("Revision sent. Claude re-edits it and you approve the new version.");
    tasteAt = 0;
    closePlayer();
    if (typeof loadLive === "function") loadLive();
  } catch (e) {
    btn.disabled = false; btn.classList.remove("busy"); renderNotes();
    toast(`Not sent (${e.message}). Your notes are kept.`);
  }
}

// ---------------------------------------------------------------- events
document.addEventListener("click", (ev) => {
  if (!PV) return;
  const t = ev.target.closest("button");
  if (!t || !t.closest("#player")) return;
  if ("pclose" in t.dataset) return closePlayer();
  if ("pplay" in t.dataset) return togglePlay();
  if (t.dataset.pstep) return step(+t.dataset.pstep);
  if ("prate" in t.dataset) { PV.rate = PV.rate === 1 ? 0.5 : PV.rate === 0.5 ? 0.25 : 1; PV.v.playbackRate = PV.rate; t.textContent = `${PV.rate}×`; return; }
  if ("pmark" in t.dataset) return startNote();
  if (t.dataset.ptool) { PV.tool = t.dataset.ptool; document.querySelectorAll(".pv-tool[data-ptool]").forEach((b) => b.setAttribute("aria-pressed", b === t)); return; }
  if ("pundo" in t.dataset) { PV.strokes.pop(); return drawInk(); }
  if (t.dataset.ptag) { const k = t.dataset.ptag, on = !PV.tags.has(k); on ? PV.tags.add(k) : PV.tags.delete(k); return t.setAttribute("aria-pressed", on); }
  if ("pcancel" in t.dataset) return cancelNote();
  if ("padd" in t.dataset) return addNote();
  if (t.dataset.pjump) { if (PV.mode === "draw") cancelNote(); PV.v.pause(); PV.v.currentTime = +t.dataset.pjump; return; }
  if (t.dataset.pdel) { drafts[PV.r.id].notes.splice(+t.dataset.pdel, 1); return renderNotes(); }
  if ("psend" in t.dataset) return sendRevision(t);
}, true);
document.addEventListener("keydown", (e) => {
  if (!PV || !$("#player").open) return;
  if (["TEXTAREA", "INPUT"].includes(e.target.tagName)) {
    if (e.key === "Enter" && (e.metaKey || e.ctrlKey) && e.target.id === "pv-note") { e.preventDefault(); addNote(); }
    return;
  }
  if (e.key === " " && e.target.tagName !== "BUTTON") { e.preventDefault(); togglePlay(); }
  else if ((e.key === "ArrowLeft" || e.key === "ArrowRight") && e.target.id !== "pv-scrub") { e.preventDefault(); step((e.key === "ArrowLeft" ? -1 : 1) * (e.shiftKey ? FPS : 1)); }
  else if (e.key === "m" || e.key === "M") { e.preventDefault(); startNote(); }
});

// ---------------------------------------------------------------- Studio: your edit taste
async function loadTaste() {
  if (Date.now() - tasteAt < 120000) return;
  tasteAt = Date.now();
  try {
    const r = await fetch("api/taste", { cache: "no-store" });
    if (r.ok) TASTE = await r.json();
  } catch {}
  if (tab === "studio" && !$("#sheet").open && !$("#player").open && !["note", "rev"].includes(document.activeElement?.id)) render();
}
function tastePanel() {
  loadTaste();
  const rules = D.taste || [];
  const T = TASTE, W = T?.weeks || [];
  const maxR = Math.max(2, ...W.map((w) => w.rounds_per_reel));
  const tags = T?.tags || [], maxT = Math.max(1, ...tags.map((x) => x.n));
  const first = W[0]?.rounds_per_reel, last = W[W.length - 1]?.rounds_per_reel;
  const trend = W.length >= 3 && first != null ? (last < first ? `down from ${first} to ${last}` : last > first ? `up from ${first} to ${last}` : `flat at ${last}`) : null;
  // revised reels vs the rest, on the same normal (only reels with numbers)
  const revised = new Set((T?.reels || []).map((x) => x.target));
  const withNum = D.reels.filter((r) => r.metrics?.vs_median_x != null);
  const med = (a) => (a.length ? a.map((r) => r.metrics.vs_median_x).sort((x, y) => x - y)[Math.floor(a.length / 2)] : null);
  const rv = withNum.filter((r) => revised.has(r.id) || (r.reel && revised.has(r.reel))), rest = withNum.filter((r) => !rv.includes(r));
  const byTag = {};
  for (const x of rules) (byTag[x.tag] ||= []).push(x);
  return `<section class="section taste" aria-labelledby="ta-h"><div class="head"><h2 class="h2" id="ta-h">Your edit taste</h2><span class="label">${rules.length} rules learned</span></div>
    <p class="lede">Every note you draw on a frame becomes a rule Claude follows next time. The goal: fewer rounds per reel, week after week.</p>
    <div class="taste-grid">
      <div class="hud"><span class="cap">Rounds per reel, by week</span>
        ${W.length ? `<div class="tbars" role="img" aria-label="Revision rounds per reel by week${trend ? `, ${trend}` : ""}">${W.map((w) => `<span title="Week of ${esc(w.week)}: ${w.revisions} revisions on ${w.reels} reels"><i style="height:${Math.max(6, (100 * w.rounds_per_reel) / maxR)}%"></i><small>${esc(w.week.slice(5))}</small></span>`).join("")}</div>
          <p class="why">${trend ? `Rounds per reel ${esc(trend)}.` : "Needs 3 weeks of revisions to show a trend."} ${T.total} revisions, ${T.notes} notes so far.</p>`
          : `<p class="why">${T ? "No revisions yet. Open any reel and draw on a frame." : "Loading…"}</p>`}</div>
      <div class="hud"><span class="cap">What you ask for most</span>
        ${tags.length ? `<ul class="tagbars">${tags.slice(0, 6).map((x) => `<li><span>${esc(TAGNAME[x.tag] || x.tag)}</span><i style="--w:${(100 * x.n) / maxT}%"></i><b class="num">${x.n}</b></li>`).join("")}</ul>` : `<p class="why">Tag your notes (Hook, Cut, Framing…) and the biggest gap shows up here.</p>`}</div>
      <div class="hud"><span class="cap">Revised vs first cut, views vs normal</span>
        ${rv.length ? `<p class="pv-stats"><span><small>Revised (${rv.length})</small><b class="num">${xTxt(med(rv))}</b></span><span><small>First cut (${rest.length})</small><b class="num">${xTxt(med(rest))}</b></span></p><p class="why">${rv.length < 5 ? "Small sample: a hint, not a verdict." : "Median per reel."}</p>` : `<p class="why">Shows once revised reels have 72 h numbers.</p>`}</div>
    </div>
    ${rules.length ? `<div class="rules">${Object.entries(byTag).map(([tag, xs]) => `<div class="rule-group"><p class="cap">${esc(TAGNAME[tag] || tag)}</p><ul>${xs.map((x) => `<li>${esc(x.rule)}${x.source ? `<small>${esc(x.source)}</small>` : ""}</li>`).join("")}</ul></div>`).join("")}</div>` : ""}
  </section>`;
}
