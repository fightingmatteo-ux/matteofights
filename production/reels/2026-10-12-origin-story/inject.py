# Renders work/template.html -> index.html for one variant.
#   python -P inject.py A
# - {{expr}} placeholders are evaluated against work/edl_<V>.json
# - segment names are aliased: hookA/hookB/hookC -> "hook", closeX -> "close", setup2B -> "setup2", lessonC -> "lesson"
# - <!--@only A,C--> ... <!--@end--> keeps a block only for the listed variants
import json, re, sys

V = sys.argv[1] if len(sys.argv) > 1 else "A"
d = json.load(open(f"work/edl_{V}.json", encoding="utf-8"))
ALIAS = {"hookA": "hook", "hookB": "hook", "hookC": "hook", "closeA": "close", "closeB": "close",
         "closeC": "close", "setup2B": "setup2", "lessonC": "lesson"}
SEG = {}
for s in d["segments"]:
    SEG[s["name"]] = s
    SEG[ALIAS.get(s["name"], s["name"])] = s


def S(n): return SEG[n]["start"]
def E(n): return SEG[n]["end"]
def has(n, word): return any(w["seg"] == SEG[n]["i"] and w["w"] == word for w in d["words"])
def W(n, word, k=1):
    hits = [w for w in d["words"] if w["seg"] == SEG[n]["i"] and w["w"] == word]
    return hits[k - 1]["s"]


src = open("work/template.html", encoding="utf-8").read()
src = re.sub(r"<!--@only ([A-Z,]+)-->(.*?)<!--@end-->",
             lambda m: m.group(2) if V in m.group(1).split(",") else "", src, flags=re.S)


def ev(m):
    v = eval(m.group(1))
    if isinstance(v, str):
        return v
    return str(round(v, 3)) if isinstance(v, (int, float)) else json.dumps(v, separators=(",", ":"), ensure_ascii=False)


open("index.html", "w", encoding="utf-8").write(re.sub(r"\{\{(.+?)\}\}", ev, src))
print(f"index.html <- variant {V} ({d['duration']}s)")
