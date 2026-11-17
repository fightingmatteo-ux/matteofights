"""Build the loop-format take sheet and film sheet from scripts-loop.json.

    python3 -P production/reels/2026-11-17-loop-shoot/build_loop.py

Writes prompter.html (published as the reading page) and production/reels/FILM-2026-11-17-loop-shoot.md.
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
data = json.loads((HERE / "scripts-loop.json").read_text(encoding="utf-8"))
SRC = (HERE.parent / "2026-11-16-month-shoot" / "prompter.tpl.html").read_text(encoding="utf-8")


def patch(s, old, new):
    assert old in s, old[:50]
    return s.replace(old, new, 1)


# derive the loop template from the month-shoot prompter
t = SRC
t = patch(t, "<title>Matteo Take Sheet</title>", "<title>Loop Take Sheet</title>")
t = patch(t, "<h1>Take Sheet</h1>", "<h1>Loop Take Sheet</h1>")
t = patch(t, "15 reels for the month. Each one is 5 hook takes, then the body once, then the ending once. Tap a take to read it.",
          "Each reel is ONE recording: press record once, read the whole page top to bottom, press stop. Gold lines tell you what to say aloud so the edit can find each part.")
t = patch(t, '[["breakdown","Fighter breakdown series"],["talk","Talking heads and rants"]]', '[["loop","Fighter breakdown, loop format"]]')
t = patch(t, 'b.textContent = NAMES[t.k] || t.k;', 'b.textContent = t.name || NAMES[t.k] || t.k;')
t = patch(t, 'function label(t){ return NAMES[t.k] || ("Hook " + t.k); }', 'function label(t){ return t.name || NAMES[t.k] || ("Hook " + t.k); }')
t = patch(t, '''  $("ps").append("Say first: ");
  const b = document.createElement("b"); b.textContent = r.slate + ", " + (NAMES[t.k] ? NAMES[t.k].toUpperCase() : "TAKE " + t.k);
  $("ps").append(b, ", then wait two seconds");''',
          '''  $("ps").append("Press record, then say: ");
  const b = document.createElement("b"); b.textContent = t.say;
  $("ps").append(b);''')
t = patch(t, 'if (/^\\(.*\\)$/.test(par)) { p.className = "cue"; p.textContent = par; }',
          'if (par.startsWith(">> ")) { p.className = "slate"; p.textContent = par.slice(3); }\n    else if (/^\\(.*\\)$/.test(par)) { p.className = "cue"; p.textContent = par; }')
t = patch(t, 'par.split(/(\\[[^\\]]+\\])/).forEach(bit => {\n      if (/^\\[/.test(bit)) { const s = document.createElement("span"); s.className = "fill"; s.textContent = bit; p.appendChild(s); }',
          'par.split(/(\\[[^\\]]+\\]|\\{[^}]+\\})/).forEach(bit => {\n      if (/^\\{/.test(bit)) { const s = document.createElement("span"); s.className = "br"; s.textContent = bit.slice(1, -1) + " "; p.appendChild(s); }\n      else if (/^\\[/.test(bit)) { const s = document.createElement("span"); s.className = "fill"; s.textContent = bit; p.appendChild(s); }')
t = patch(t, ".txt .fill{color:var(--go)}",
          ".txt .fill{color:var(--go)}\n.txt p.slate{color:var(--go);font-size:.55em;font-weight:800;letter-spacing:.03em;line-height:1.35}\n.txt .br{color:#9fb0ff}")


# card mode: one segment at a time, tap anywhere or the big button for the next one (default on)
t = patch(t, '<div class="cd" id="cd" hidden></div>',
          '<div class="cd" id="cd" hidden></div>\n    <div class="card" id="card" hidden><div class="cs" id="cs"></div><div class="cb" id="cb"></div></div>')
t = patch(t, '<button id="mir">Mirror</button>', '<button id="mir">Mirror</button>\n    <button id="cards">Cards</button>')
t = patch(t, ".txt .br{color:#9fb0ff}",
          ".txt .br{color:#9fb0ff}\n.card{position:absolute;inset:0;overflow-y:auto;display:flex;flex-direction:column;justify-content:flex-start;gap:18px;padding-block:16px;padding-left:max(20px,env(safe-area-inset-left,0px));padding-right:max(20px,env(safe-area-inset-right,0px));cursor:pointer}\n.cs{color:var(--go);font-weight:800;font-size:18px;line-height:1.35;max-width:22em;margin:auto auto 0;width:100%}\n.cb{font-family:var(--read);font-weight:600;line-height:1.28;max-width:22em;margin:0 auto auto;width:100%}\n.cb p{margin:0 0 .7em}\n.cb .br{color:#9fb0ff}")
t = patch(t, 'let cur = 0, playing = false, raf = 0, last = 0, pos = 0, cdTimer = 0, lock = null;',
          'let cur = 0, playing = false, raf = 0, last = 0, pos = 0, cdTimer = 0, lock = null;\nlet cardMode = store.get("ts.cards", true), segs = [], si = 0;')
t = patch(t, 'function tick(ts){', r'''function buildSegs(t){
  segs = [];
  t.text.split(/\n\n+/).forEach(par => {
    if (par.startsWith(">> ")) segs.push({s: par.slice(3), body: []});
    else { if (!segs.length) segs.push({s: "", body: []}); segs[segs.length - 1].body.push(par); }
  });
  const out = [];
  segs.forEach(sg => {
    if (sg.body.length <= 2) { out.push(sg); return; }
    for (let i = 0; i < sg.body.length; i += 2) out.push({s: i ? "Keep going, same take" : sg.s, body: sg.body.slice(i, i + 2)});
  });
  segs = out;
}
function paintCard(){
  const sg = segs[si]; $("cs").textContent = sg.s;
  const cb = $("cb"); cb.textContent = ""; cb.style.fontSize = size + "px";
  sg.body.forEach(par => {
    const p = document.createElement("p");
    par.split(/(\{[^}]+\})/).forEach(bit => {
      if (/^\{/.test(bit)) { const s = document.createElement("span"); s.className = "br"; s.textContent = bit.slice(1, -1) + " "; p.appendChild(s); }
      else p.append(bit);
    });
    cb.appendChild(p);
  });
  $("card").scrollTop = 0;
}
function seg(d){ const n = si + d; if (n >= 0 && n < segs.length) { si = n; paint(); } }
function tick(ts){''')
t = patch(t, '$("scroll").scrollTop = 0; pos = 0;\n  paint();', '$("scroll").scrollTop = 0; pos = 0; buildSegs(t); si = 0;\n  paint();')
t = patch(t, '  $("play").textContent = playing ? "Stop" : "Start";\n  $("play").classList.toggle("on", playing);',
          '''  $("card").hidden = !cardMode; $("scroll").hidden = cardMode; document.querySelector(".mark").hidden = cardMode;
  $("cards").textContent = cardMode ? "Scroll" : "Cards";
  $("play").textContent = cardMode ? (si < segs.length - 1 ? "Next " + (si + 1) + "/" + segs.length : "Done") : (playing ? "Stop" : "Start");
  $("play").classList.toggle("on", playing && !cardMode);
  if (cardMode && segs.length) paintCard();''')
t = patch(t, 'function toggle(){ playing ? stop() : start(); }', 'function toggle(){ if (cardMode) { seg(1); return; } playing ? stop() : start(); }')
t = patch(t, '$("prev").onclick = () => go(-1);', '$("prev").onclick = () => cardMode ? seg(-1) : go(-1);')
t = patch(t, '$("next").onclick = () => go(1);', '$("next").onclick = () => cardMode ? seg(1) : go(1);\n$("card").onclick = toggle;\n$("cards").onclick = () => { stop(); cardMode = !cardMode; store.set("ts.cards", cardMode); paint(); };')


def words(s):
    return len(s.replace("{", "").replace("}", "").split())


reels = []
md = [
    f"# Filming sheet: loop format, Episodes 4 to 7 ({data['updated']})",
    "",
    "Built from `2026-11-17-loop-shoot/scripts-loop.json` (edit there, run `build_loop.py`). Reading page: the Loop Take Sheet.",
    "",
    "## How it works (Matteo 2026-11-17)",
    "- **One recording per reel.** Press record once, read the whole page, press stop. Spoken slates (gold lines) mark each part.",
    "- **Loop:** each LOOP line is a bridge plus the hook, said in one breath. The edit starts the reel at the HOOK and ends it",
    "  on the BRIDGE (last frame = the frame just before the hook word), so the replay is one unbroken sentence.",
    "- Same spot, shirt, distance and light for the whole file, and end each loop line in the posture the hook starts in.",
    "- Flubbed a line: say \"again\", wait 1 s, redo it from its start. The edit picks the repeat with the most eye contact, then the most energy.",
    "- Shorter than the first batch: about 35 to 40 s per reel. Episode numbers 1 to 3 are Saenchai, Lomachenko and Floyd; these are 4 to 7.",
    "- Edit rules: keep word tails (never trim on word ends), no speed changes, plan day cards over the PLAN line, b-roll shows what the words say.",
    "",
]
for r in data["reels"]:
    intro = data["intro"].format(ep=r["ep"])
    body = [intro] + r["body"] + [data["cta"]]
    paras = [
        ">> PRESS RECORD ONCE. Same spot, distance and light for the whole file. Look at the lens, not the screen. Flubbed a line? Say \"again\", wait 1 s, redo it from its start."
    ]
    for lp in r["loops"]:
        paras.append(f'>> SAY "{r["slate"]}, LOOP {lp["k"]}" then wait 2 s. Next line is ONE breath, no pause at the join.')
        paras.append("{" + lp["bridge"] + "} " + lp["hook"])
    paras.append(f'>> SAY "{r["slate"]}, BODY" then wait 2 s. Read the rest once, no stops.')
    paras += body
    paras.append(">> STOP RECORDING. That's the whole reel.")
    text = "\n\n".join(paras)
    assert "—" not in text
    est = (words(" ".join(body)) + words(r["loops"][0]["hook"]) + words(r["loops"][0]["bridge"])) / 3.8
    reels.append({
        "id": r["id"], "group": "loop", "slate": r["slate"], "title": r["title"], "tag": r["tag"],
        "why": r["why"], "note": r["note"],
        "takes": [{"k": "FULL", "name": "Record this reel", "type": "", "say": f'"{r["slate"]}, LOOP A"', "text": text}],
    })
    md += [f"## {r['slate']}: {r['title']} ({r['tag']}), about {est:.0f} s", "", f"Why: {r['why']}", f"Before filming: {r['note']}", "",
           "| Loop | Type | Bridge (end of reel) | Hook (start of reel) |", "|---|---|---|---|"]
    md += [f"| {lp['k']} | {lp['type']} | {lp['bridge']} | {lp['hook']} |" for lp in r["loops"]]
    md += ["", "**BODY (said once)**", ""] + [f"> {p}" for p in body] + [""]

blob = json.dumps({"reels": reels}, ensure_ascii=False).replace("</", "<\\/")
(HERE / "prompter.html").write_text(t.replace("/*DATA*/", blob), encoding="utf-8")
(HERE.parent / "FILM-2026-11-17-loop-shoot.md").write_text("\n".join(md), encoding="utf-8")
print("built", len(reels), "reels")
for r in reels:
    print(r["slate"], len(r["takes"][0]["text"].split()), "words on the page")
