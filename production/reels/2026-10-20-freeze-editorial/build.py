"""Build index.html for the editorial re-cut of freeze-in-sparring A: python -P build.py

Same takes as 2026-10-14-freeze-in-sparring (work/takes.json -> assemble.py -> assets/media/aroll_A.mp4 +
work/edl_A.json), new look from production/editing/reel-kit/editorial/.
"""
import json
import re
import sys

sys.path.insert(0, "../../editing/reel-kit/editorial")
import cutout  # noqa: E402
import plan  # noqa: E402

d = json.load(open("work/edl_A.json", encoding="utf-8"))
WORDS = d["words"]


def W(word, k=1):
    return [w for w in WORDS if w["w"] == word][k - 1]["s"]


def E(word, k=1):
    return [w for w in WORDS if w["w"] == word][k - 1]["e"]


TITLE_END = W("AND") - 0.06                      # title clears just before "and there are three things"
CARDS = [
    (W("GETTING") - 0.06, W("NUMBER", 2) - 0.08, "INFORMATION"),   # getting punched isn't a failure. it's just INFORMATION
    (W("PICK") - 0.06, W("JUST", 2) - 0.04, "ONE"),                   # pick ONE job per round
    (W("TAKE") - 0.06, W("BECAUSE") - 0.12, "RESET"),              # take a deep breath and RESET (slam), face back for "because"
]
ed = plan.build(d, keys={"THREE", "ONE", "TWO", "JAB", "RELAX", "CAUGHT"}, cards=CARDS, slam={"RESET"},
                hide=[(0, TITLE_END)], title_end=TITLE_END,
                back_top=lambda t: (cutout.head_top("assets/media/fg_A_full.webm", t) or 660) - 235)
css, js = plan.install(".", bed_seconds=d["duration"] + 1)

src = open("work/template.html", encoding="utf-8").read()
fill = {"ED_CSS": css, "ED_JS": js, "ED_HTML_CAPS": ed["caps"], "ED_HTML_CAPS_BACK": ed["caps_back"], "ED_HTML_CARDS": ed["cards"], "ED_AUDIO": ed["audio"],
        "ED_PLAN": ed["plan"], "DUR": f"{d['duration']:.3f}", "TITLE_END": f"{TITLE_END:.3f}",
        "HEAD_T": f"{W('HEAD') - 0.03:.3f}", "CAP_TOP": "330", "BEHIND_TOP": "480", "BACK_TOP": "0"}
out = re.sub(r"\{\{(\w+)\}\}", lambda m: fill[m.group(1)], src)
open("index.html", "w", encoding="utf-8").write(out)
print(f"index.html built: {d['duration']:.1f}s, {len(json.loads(ed['plan'])['phrases'])} phrases, {len(CARDS)} cards")
