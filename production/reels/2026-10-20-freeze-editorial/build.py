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
import cutout  # noqa: E402
import plan  # noqa: E402

# ---------------------------------------------------------------- fill this in per reel
REEL = {
    # per variant: the hook title. lead = small lines on frame 0; word = the big word that starts behind his
    # head and flies to the front when he SAYS `on`; the title clears just before `until` is said.
    "hooks": {
        "A": {"lead": ["If you freeze when you spar,", "it's your"], "word": "head.", "on": ("HEAD", 1), "until": ("AND", 1)},
        "C": {"lead": ["Beginners try to win", "every exchange. Fighters"], "word": "don't.", "on": ("DON'T", 1), "until": ("HERE'S", 1)},
    },
    # words that go big + red over the face; their effect comes from the word (plan.FX), override in "fx"
    "keys": ["THREE", "ONE", "TWO", "JAB", "RELAX", "CAUGHT"],
    "fx": {},
    # the 2-3 lines that carry the reel, cut to a white card: (first word, card ends before this word, KEYWORD)
    "cards": [
        (("GETTING", 1), ("NUMBER", 2), "INFORMATION"),
        (("PICK", 1), ("JUST", 2), "ONE"),
        (("TAKE", 1), ("BECAUSE", 1), "RESET"),
    ],
    "slam": ["RESET"],          # max one card keyword: over-scaled + sub hit
    "bed": None,                # music under the voice: an mp3/wav path, or None for the synthesised piano placeholder
}
# ----------------------------------------------------------------

V = sys.argv[1] if len(sys.argv) > 1 else "A"
d = json.load(open(f"work/edl_{V}.json", encoding="utf-8"))
WORDS = d["words"]
FG = f"assets/media/fg_{V}_full.webm"


def W(ref):
    word, k = ref
    return [w for w in WORDS if w["w"] == word][k - 1]["s"]


hook = REEL["hooks"][V]
title_end = W(hook["until"]) - 0.06
swap = W(hook["on"]) - 0.02
cards = [(W(a) - 0.06, W(b) - (0.12 if i == len(REEL["cards"]) - 1 else 0.08), kw) for i, (a, b, kw) in enumerate(REEL["cards"])]
head = lambda t: cutout.head_top(FG, t) or 660  # noqa: E731
# hook word: sized to fit, placed so his head hides ~40% of it until it flies forward
hook_size = min(360, int(960 / (0.45 * len(hook["word"]))))  # "head." is ~790 px wide at 360 px
behind_top = min(head(t) for t in (0.0, swap / 2, swap)) - int(127 * hook_size / 360)

# cutaways: make_broll.py-style work/broll.json ({name: {start, dur}}, files assets/media/b_<name>.mp4), if the reel has any
broll = json.load(open("work/broll.json", encoding="utf-8")) if os.path.exists("work/broll.json") else {}
broll_html, broll_spans = plan.broll_html(broll)
ed = plan.build(d, keys=set(REEL["keys"]), cards=cards, slam=set(REEL["slam"]), fx=REEL["fx"],
                hide=[(0, title_end)], title_end=title_end, back_top=lambda t: head(t) - 235, broll=broll_spans,
                **({"bed": "assets/media/bed" + os.path.splitext(REEL["bed"])[1]} if REEL.get("bed") else {}))
css, js = plan.install(".", bed_seconds=None if REEL.get("bed") else d["duration"] + 1)
if REEL.get("bed"):
    os.makedirs("assets/media", exist_ok=True)
    shutil.copy(REEL["bed"], "assets/media/bed" + os.path.splitext(REEL["bed"])[1])

fill = {"ED_CSS": css, "ED_JS": js, "ED_HTML_CAPS": ed["caps"], "ED_HTML_CAPS_BACK": ed["caps_back"],
        "ED_HTML_CARDS": ed["cards"], "ED_AUDIO": ed["audio"], "ED_PLAN": ed["plan"], "ED_BROLL": broll_html,
        "AROLL": f"assets/media/aroll_{V}.mp4", "FG": FG, "DUR": f"{d['duration']:.3f}",
        "HOOK_LEAD": "".join(f'<span class="lead">{x}</span>' for x in hook["lead"]), "HOOK_WORD": hook["word"],
        "HOOK_SIZE": str(hook_size), "BEHIND_TOP": str(behind_top), "TITLE_END": f"{title_end:.3f}",
        "HEAD_SWAP": f"{swap:.3f}", "FRONT_DUR": f"{title_end - swap:.3f}", "HEAD_SFX": f"{swap - 0.09:.3f}",
        "CAP_TOP": "330", "BACK_TOP": "0"}
src = open("work/template.html", encoding="utf-8").read()
open("index.html", "w", encoding="utf-8").write(re.sub(r"\{\{(\w+)\}\}", lambda m: fill[m.group(1)], src))
print(f"{V}: index.html built, {d['duration']:.1f}s, {len(json.loads(ed['plan'])['phrases'])} phrases, {len(cards)} cards")
