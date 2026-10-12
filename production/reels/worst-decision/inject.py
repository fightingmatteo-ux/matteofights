# Renders ../index.src.html -> index.html: {{expr}} placeholders are evaluated against the cut (edl.json).
import json, re
d = json.load(open("work/edl.json"))
SEG = {s["name"]: s for s in d["segments"]}
def S(n): return SEG[n]["start"]
def E(n): return SEG[n]["end"]
def W(n, word, k=1):
    hits = [w for w in d["words"] if w["seg"] == SEG[n]["i"] and w["w"] == word]
    return hits[k-1]["s"]
def D(a, b): return b - a

src = open("work/template.html", encoding="utf-8").read()
def ev(m):
    v = eval(m.group(1))
    return str(round(v, 3)) if isinstance(v, (int, float)) else json.dumps(v, separators=(",", ":"))
out = re.sub(r"\{\{(.+?)\}\}", ev, src)
open("index.html", "w", encoding="utf-8").write(out)
