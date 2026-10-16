"""Render index.html for one hook variant: python -P build_variant.py A|B|C

Takes work/edl_<V>.json (assemble.py), names its first segment 'hook' and last 'loop' so one template serves all
three variants, fills {{expr}} placeholders from the cut, then carves the music bed under the voice.
"""
import json, re, shutil, subprocess, sys

V = sys.argv[1]
HOOKS = {
    "A": '<span class="t">SAENCHAI FOUGHT</span><span class="t red">BIGGER MEN</span><span class="t">HIS WHOLE CAREER</span>',
    "B": '<span class="t">ALWAYS SPARRING</span><span class="t red">SOMEONE BIGGER?</span>',
    "C": '<span class="t">BIGGER GUYS WIN THE TRADE.</span><span class="t red">SAENCHAI NEVER TRADED.</span>',
}
d = json.load(open(f"work/edl_{V}.json", encoding="utf-8"))
d["segments"][0]["name"] = "hook"
d["segments"][-1]["name"] = "loop"
json.dump(d, open("work/edl.json", "w", encoding="utf-8"), indent=1)
SEG = {s["name"]: s for s in d["segments"]}
def S(n): return SEG[n]["start"]
def E(n): return SEG[n]["end"]
def W(n, word, k=1):
    hits = [w for w in d["words"] if w["seg"] == SEG[n]["i"] and w["w"] == word]
    return hits[k - 1]["s"]
def D(a, b): return b - a

src = open("work/template.html", encoding="utf-8").read().replace("{{HOOK_HTML}}", HOOKS[V])
def ev(m):
    v = eval(m.group(1))
    return str(round(v, 3)) if isinstance(v, (int, float)) else json.dumps(v, separators=(",", ":"))
out = re.sub(r"\{\{(.+?)\}\}", ev, src).replace("assets/media/aroll.mp4", f"assets/media/aroll_{V}.mp4")
open("index.html", "w", encoding="utf-8").write(out)
import os
subprocess.run(["node", os.path.expanduser("~/.claude/skills/hyperframes-audio/scripts/carve.mjs"), "--comp", "index.html", "--bed", "music-bed", "--voice", "vo", "--core", "../worst-decision"], check=True, stdout=subprocess.DEVNULL)
print(f"{V}: index.html built, {d['duration']:.1f}s")
