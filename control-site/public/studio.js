// Studio: upload footage (edited in the cloud into 3 variants), talking points to film, revision notes, live
// status of edits and renders. Live data from /api/live (D1), refreshed every 30 s and laid over data.json so
// Home shows approvals and posts as they happen. Uses app.js helpers ($, esc, ago, toast, render, D, VIEWS).
let L = null; // live data
let tpPick = null; // talking point chosen for the next upload
let up = null; // upload in progress {name, done, total}
const PART = 50 * 1024 * 1024;
const ST = { uploaded: "Waiting", open: "Waiting", working: "Editing", done: "Done", failed: "Failed",
             queued: "Queued", rendering: "Rendering" };

async function api(path, body, method = "POST") {
  const r = await fetch(path, { method, headers: { "content-type": "application/json" }, body: JSON.stringify(body) });
  const j = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(j.error || `error ${r.status}`);
  return j;
}

async function loadLive() {
  try {
    const r = await fetch("api/live", { cache: "no-store" });
    if (!r.ok) return;
    L = await r.json();
    if (D) overlay();
    if (D && !$("#sheet").open && !document.body.classList.contains("holding") && !(tab === "studio" && busyTyping())) render();
  } catch { /* offline: keep the last data */ }
}
const busyTyping = () => ["note", "rev"].includes(document.activeElement?.id);

// live queue state over the rebuilt data.json reels
function overlay() {
  const q = Object.fromEntries((L.queue || []).map((i) => [i.id, i]));
  for (const r of D.reels || []) {
    const i = q[r.id];
    if (!i) continue;
    if (i.status === "posted") r.state = "posted";
    else if (i.status === "failed") r.state = "failed";
    else if (i.approved && r.state === "needs_yes") r.state = "scheduled";
  }
}

function pill(s) {
  return `<span class="pill ${esc(s)}">${esc(ST[s] || s)}</span>`;
}

function studio() {
  if (!L) return `<div class="page-head"><h1 class="h1">Studio</h1></div><p class="empty-note">Loading live data…</p>`;
  const tps = L.talking_points || [];
  const tp = tps.find((t) => t.id === tpPick);
  const probs = L.health?.problems || [];
  let h = `<div class="page-head"><h1 class="h1">Studio</h1><p class="lede">Upload footage and it comes back as 3 edited variants to approve. Notes on any reel go to the edit worker.</p></div>`;
  if (probs.length) {
    h += `<section class="section alert" aria-labelledby="hp-h"><div class="head"><h2 class="h2" id="hp-h">Needs a look</h2></div>
      <ul class="cmts">${probs.map((p) => `<li><p class="t">${esc(p.text)}</p></li>`).join("")}</ul></section>`;
  }
  // upload
  h += `<section class="section" aria-labelledby="up-h"><div class="head"><h2 class="h2" id="up-h">Upload footage</h2></div>
    ${tp ? `<p class="lede">For: <b>${esc(tp.title)}</b> <button class="link" data-tppick="">change</button></p>` : `<p class="lede">Talking head, B-roll, anything. Pick a talking point below if you filmed one.</p>`}
    <label class="field" for="file">Video</label><input id="file" type="file" accept="video/*" ${up ? "disabled" : ""}>
    <label class="field" for="note">Note for the edit (optional)</label>
    <textarea id="note" placeholder="Take 2 is the good one, use the sparring clip from Tuesday, this is B-roll for the bank"></textarea>
    <div class="row-actions"><button class="btn" data-act="upload" ${up ? "disabled" : ""}>${up ? "Uploading…" : "Upload"}</button>
    ${up ? `<span class="hint">${esc(up.name)}: ${Math.round((100 * up.done) / up.total)}%</span>` : `<span class="hint">Keep this page open until it says done.</span>`}</div>
    ${up ? `<div class="bar-prog"><span style="width:${(100 * up.done) / up.total}%"></span></div>` : ""}</section>`;
  // in progress
  const work = [...(L.uploads || []).map((u) => ({ ...u, kind: "upload", label: u.name })),
                ...(L.requests || []).map((r) => ({ ...r, kind: "request", label: r.text }))].sort((a, b) => (a.at < b.at ? 1 : -1)).slice(0, 12);
  h += `<section class="section" aria-labelledby="wk-h"><div class="head"><h2 class="h2" id="wk-h">Edits</h2></div>
    ${work.length ? `<ul class="cmts">${work.map((w) => `<li><div><p class="t">${pill(w.status)} ${esc(String(w.label).slice(0, 140))}</p>
      <p class="m">${w.kind === "upload" ? "Upload" : "Note"}${w.target ? ` on ${esc(w.target)}` : ""}, <time datetime="${esc(w.at)}">${ago(w.at)}</time>${w.result ? ` · ${esc(w.result)}` : ""}</p></div>
      ${w.status === "failed" ? `<span class="iacts"><button class="btn line" data-retry="${esc(w.kind + ":" + w.id)}">Retry</button></span>` : ""}</li>`).join("")}</ul>`
      : `<p class="empty-note">No edits yet. Upload a video above.</p>`}</section>`;
  // renders
  const jobs = (L.jobs || []).slice().reverse().slice(0, 8);
  if (jobs.length) {
    h += `<section class="section" aria-labelledby="rj-h"><div class="head"><h2 class="h2" id="rj-h">Cloud renders</h2></div>
      <ul class="cmts">${jobs.map((j) => `<li><div><p class="t">${pill(j.status)} ${esc(j.reel)} ${esc(j.variant)}</p>
      <p class="m">${j.seconds ? `${Math.round(j.seconds / 60)} min` : ""}${j.error ? ` · ${esc(j.error.slice(-140))}` : ""}</p></div></li>`).join("")}</ul></section>`;
  }
  // revision note
  const targets = (L.queue || []).filter((i) => i.status === "queued").map((i) => i.id);
  h += `<section class="section" aria-labelledby="rv-h"><div class="head"><h2 class="h2" id="rv-h">Revision or note</h2></div>
    <label class="field" for="target">Which reel</label>
    <select id="target"><option value="">General note</option>${targets.map((t) => `<option>${esc(t)}</option>`).join("")}</select>
    <label class="field" for="rev">What should change</label>
    <textarea id="rev" placeholder="Hook B: say 'bigger guys' not 'bigger men'. Music too loud after 0:20."></textarea>
    <div class="row-actions"><button class="btn" data-act="revise">Send</button><span class="hint">The edit worker applies it and re-renders. Changed reels come back for a yes.</span></div></section>`;
  // talking points
  h += `<section class="section" aria-labelledby="tp-h"><div class="head"><h2 class="h2" id="tp-h">Talking points to film</h2></div>
    <p class="lede">From competitor outliers, written in your voice every Monday. Film one, then upload it with "Film this".</p>
    ${tps.length ? tps.map((t) => `<div class="idea"><p class="t"><b>${esc(t.title)}</b></p>
      ${t.why ? `<p class="m">${esc(t.why)}</p>` : ""}
      <ol class="hooks">${(t.hooks || []).map((x) => `<li>${esc(x)}</li>`).join("")}</ol>
      ${(t.points || []).length ? `<ul class="pts">${t.points.map((x) => `<li>${esc(x)}</li>`).join("")}</ul>` : ""}
      <div class="row-actions"><button class="btn line" data-tppick="${esc(t.id)}">Film this</button><button class="link" data-tpskip="${esc(t.id)}">Skip</button>
      ${t.source ? `<a class="link" href="${esc(t.source)}" target="_blank" rel="noopener">Original</a>` : ""}</div></div>`).join("")
      : `<p class="empty-note">None waiting. New ones arrive Monday.</p>`}</section>`;
  return h;
}

async function uploadFile() {
  const f = $("#file")?.files?.[0];
  if (!f) return toast("Pick a video first.");
  const note = $("#note").value.trim();
  up = { name: f.name, done: 0, total: f.size || 1 };
  render();
  try {
    const { key, uploadId } = await api("api/upload", { op: "create", name: f.name, size: f.size, type: f.type });
    const n = Math.max(1, Math.ceil(f.size / PART)), parts = new Array(n);
    let next = 0;
    const worker = async () => {
      while (next < n) {
        const i = next++;
        const blob = f.slice(i * PART, Math.min(f.size, (i + 1) * PART));
        for (let attempt = 0; ; attempt++) {
          try {
            const r = await fetch(`api/upload?key=${encodeURIComponent(key)}&uploadId=${encodeURIComponent(uploadId)}&part=${i + 1}`, { method: "PUT", body: blob });
            if (!r.ok) throw new Error(`part ${i + 1}: ${r.status}`);
            parts[i] = await r.json();
            break;
          } catch (e) {
            if (attempt >= 2) throw e;
          }
        }
        up.done += blob.size;
        render();
      }
    };
    await Promise.all([worker(), worker(), worker()]);
    const res = await api("api/upload", { op: "complete", key, uploadId, parts, name: f.name, size: f.size, note, talking_point: tpPick });
    toast(res.started ? "Uploaded. The edit starts now; variants show up on Home for your yes." : "Uploaded. The edit starts on the next check.");
    tpPick = null;
  } catch (e) {
    toast(`Upload failed (${e.message}). Try again.`);
  }
  up = null;
  loadLive();
}

document.addEventListener("click", async (ev) => {
  const t = ev.target.closest("button");
  if (!t) return;
  try {
    if (t.dataset.act === "upload") return uploadFile();
    if (t.dataset.act === "revise") {
      const text = $("#rev").value.trim();
      if (!text) return toast("Write what should change.");
      t.disabled = true;
      await api("api/studio", { action: "request", target: $("#target").value, text });
      $("#rev").value = "";
      toast("Sent. The edit worker is on it.");
      return loadLive();
    }
    if ("tppick" in t.dataset) { tpPick = t.dataset.tppick || null; render(); return $("#file")?.scrollIntoView({ behavior: "smooth", block: "center" }); }
    if (t.dataset.tpskip) { await api("api/studio", { action: "tp", id: t.dataset.tpskip, status: "skipped" }); toast("Skipped."); return loadLive(); }
    if (t.dataset.retry) {
      const [kind, id] = t.dataset.retry.split(":");
      await api("api/studio", { action: "retry", kind, id });
      toast("Sent back to the edit worker.");
      return loadLive();
    }
  } catch (e) {
    toast(`Not sent (${e.message}).`);
    t.disabled = false;
  }
});

VIEWS.studio = studio;
loadLive();
setInterval(loadLive, 30000);
document.addEventListener("visibilitychange", () => document.visibilityState === "visible" && loadLive());
