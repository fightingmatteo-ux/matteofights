"""Editorial talking-head reel (the look since 2026-10-20): python -P build.py A

Copy production/reels/_TEMPLATE/editorial/ (build.py, make.sh, work/template.html) into the new reel, fill REEL
below from the transcript, then `bash make.sh A` (assemble -> cut-out -> build -> render -> glitch check).
Kit + rules: production/editing/reel-kit/editorial/README.md. Worked example: 2026-10-20-freeze-editorial/.

Words are the UPPERCASE tokens in work/edl_<V>.json. ("WORD", k) = the k-th time that word is said.
"""
import json
import os
import re
import shutil
import sys

sys.path.insert(0, "../../editing/reel-kit/editorial")
sys.path.insert(0, "../../../tools/planreel")
import cutout  # noqa: E402
import plan  # noqa: E402

# ---------------------------------------------------------------- fill this in per reel
REEL = {
    # Origin pin (Matteo 2026-11-20): 3 openings that look different on mute, every variant a loop (the bridge at the
    # end runs into the hook at the start, one continuous take). Research: production/competitors/talking-heads-2026-11-20.md
    # A: his face, numbers board (result). B: cold, his beginner pad kick under "School came easy" (contrast).
    # C: cold, the stadium under "The day before my first fight", the hospital photo under "I ended up in the hospital".
    "hooks": {
        # review 11-20: the behind-the-head word never showed (the cut-out misreads his head on the white wall), so frame 0
        # was two small lines. Now the whole board is on frame 0 over his face, the last word big and red (Santino style)
        "A": {"lead": ["One fight at 16.", "Still no"], "word": "second.", "on": ("SECOND", 1), "until": ("STARTED", 1), "cold": True},
        "B": {"lead": ["School came easy.", "Fighting"], "word": "didn't.", "on": ("DIDN'T", 1), "until": ("STARTED", 1), "cold": True},
        "C": {"lead": ["The day before", "my first fight:"], "word": "hospital.", "on": ("HOSPITAL", 1), "until": ("STARTED", 1), "cold": True},
    },
    # one red keyword every ~3-6 s, on the word that carries the line
    "keys": ["JITSU", "STREET", "ANYTHING", "SCARED", "SLEEP", "APPENDICITIS", "STADIUM", "COUNTRIES", "FRACTURE", "ACL",
             "SPAR", "COMEBACK"],
    "fx": {"APPENDICITIS": "impact", "ACL": "impact", "STREET": "jab", "SPAR": "jab"},
    # (first word, card ends before this word, KEYWORD): the 2 lines that carry the reel
    "cards": [
        (("SCARED", 2), ("SO", 2), "FRIENDS"),         # "Scared to get knocked out in front of all my friends"
        (("TAUGHT", 1), ("DISCIPLINE", 1), "WORK"),     # "if you want something you actually have to work your ass off for it"
    ],
    "cta_at": ("FOLLOW", 1),
    "cta": "FOLLOW FOR THE COMEBACK",
    "slam": ["WORK"],
    "bed": "../../listicles/music/epic-bold-drums-alex-morgan.mp3",
}
# ----------------------------------------------------------------

V = sys.argv[1] if len(sys.argv) > 1 else "A"
d = json.load(open(f"work/edl_{V}.json", encoding="utf-8"))
WORDS = d["words"]
FG = f"assets/media/fg_{V}_full.webm"


SEGNAME = {s["i"]: s["name"] for s in d["segments"]}


def W(ref):
    word, k, *seg = ref
    return [w for w in WORDS if w["w"] == word and (not seg or SEGNAME[w["seg"]] == seg[0])][k - 1]["s"]


hook = REEL["hooks"][V]
cold = hook.get("cold", False)
title_end = W(hook["until"]) - 0.06
swap = W(hook["on"]) - 0.02
cards = [(W(a) - 0.06, W(b) - (0.12 if i == len(REEL["cards"]) - 1 else 0.08), kw) for i, (a, b, kw) in enumerate(REEL["cards"])]
# cut-out only covers the opening (FG_TO s, the hook word behind his head): the full-length cut-out took ~1 h per 80 s
# variant on Modal (2026-11-20). After it, "behind" phrases sit in the clean space above his head instead.
FG_TO = 8.0
head = lambda t: (cutout.head_top(FG, t) or 660) if t < FG_TO - 0.3 else 565  # noqa: E731
# hook word: sized to fit, placed so his head hides ~40% of it until it flies forward
hook_size = min(360, int(780 / (0.45 * len(hook["word"]))))  # fits the frame after the 1.26x fly-forward  # "head." is ~790 px wide at 360 px
behind_top = min(head(t) for t in (0.0, swap / 2, swap)) - int(127 * hook_size / 360)

# cutaways: make_broll.py-style work/broll.json ({name: {start, dur}}, files assets/media/b_<name>.mp4), if the reel has any
broll = json.load(open(f"work/broll_{V}.json", encoding="utf-8")) if os.path.exists(f"work/broll_{V}.json") else {}
_cardspans = []
broll_html, broll_spans = plan.broll_html(broll)
broll_html = broll_html.replace("assets/media/b_", "assets/broll/b_")  # submit.py skips assets/media/b_*.mp4
ed = plan.build(d, keys=set(REEL["keys"]), cards=cards, slam=set(REEL["slam"]), fx=REEL["fx"],
                hide=[(0, title_end)] + _cardspans, title_end=title_end, back_top=lambda t: head(t) - 235, broll=broll_spans,
                **({"bed": "assets/media/bed" + os.path.splitext(REEL["bed"])[1]} if REEL.get("bed") else {}))
css, js = plan.install(".", bed_seconds=None if REEL.get("bed") else d["duration"] + 1)
if REEL.get("bed"):
    os.makedirs("assets/media", exist_ok=True)
    shutil.copy(REEL["bed"], "assets/media/bed" + os.path.splitext(REEL["bed"])[1])

fill = {"ED_CSS": css, "ED_JS": js, "ED_HTML_CAPS": ed["caps"], "ED_HTML_CAPS_BACK": ed["caps_back"],
        "ED_HTML_CARDS": ed["cards"], "ED_AUDIO": ed["audio"], "ED_PLAN": ed["plan"], "ED_BROLL": broll_html,
        "AROLL": f"assets/media/aroll_{V}.mp4", "FG": FG, "FG_DUR": f"{min(FG_TO, d['duration']):.3f}", "DUR": f"{d['duration']:.3f}",
        "HOOK_LEAD": "".join(f'<span class="lead">{x}</span>' for x in hook["lead"])
                     + (f'<span class="word">{hook["word"]}</span>' if cold else ""),
        "HOOK_WORD": "" if cold else hook["word"],
        "CTA_TEXT": REEL["cta"], "CTA_START": f"{W(REEL['cta_at']) - 0.1:.3f}",
        "CTA_DUR": f"{d['duration'] - W(REEL['cta_at']) + 0.1:.3f}",
        "HOOK_SIZE": str(hook_size), "BEHIND_TOP": str(behind_top), "TITLE_END": f"{title_end:.3f}",
        "HEAD_SWAP": f"{swap:.3f}", "FRONT_DUR": f"{title_end - swap:.3f}", "HEAD_SFX": f"{swap - 0.09:.3f}",
        "CAP_TOP": "330", "BACK_TOP": "0", "DAYCARDS_HTML": "", "DAYCARDS_JS": ""}
src = open("work/template.html", encoding="utf-8").read()
open("index.html", "w", encoding="utf-8").write(re.sub(r"\{\{(\w+)\}\}", lambda m: fill[m.group(1)], src))
print(f"{V} ({'cold open' if cold else 'face open'}): index.html built, {d['duration']:.1f}s, {len(json.loads(ed['plan'])['phrases'])} phrases, {len(cards)} cards")
