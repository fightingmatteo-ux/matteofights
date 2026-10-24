"""Knockout draw (2026-10-24, v2 after Matteo's notes): python -P build.py A

Each variant = hook take -> the whole body take (no cuts inside it) -> loop line. Every hook opens on the
knockout tape with its own motion graphic (A: the result plate flips K.O. -> DRAW, B: his 6 fights stack
against my 1 and get knocked over, C: 16 / fight #6 / fight #1). Motion follows Emil Kowalski's rules
(git b0beee3 .claude/skills/animate): strong ease-out entrances, nothing from scale(0), 30-80 ms staggers.
Renders on Modal: the "Submit render" workflow runs `bash make.sh <V>` there.
"""
import html
import json
import os
import re
import shutil
import sys

sys.path.insert(0, "../../editing/reel-kit/editorial")
import cutout  # noqa: E402
import plan  # noqa: E402

REEL = {
    # the spoken hook as on-screen lines: (line text, [EDL words it covers]); words build in as they are said
    "hooks": {
        "A": [["I knocked him out."], ["They called it a draw."]],
        "B": [["My first fight,"], ["stacked against me."], ["I still knocked him out."]],
        "C": [["I was 16."], ["His sixth fight."], ["My first."]],
    },
    # the word the right hand lands on in the hook tape (make_broll.py PUNCH_WORD, +0.05 s)
    "ko_word": {"A": "KNOCKED", "B": "KNOCKED", "C": "FIRST"},
    # big + red over the face, one every few seconds, none over the tape
    "keys": ["REFEREE", "POINTS", "LEGAL", "VIOLENCE", "JUDGES"],
    "fx": {"POINTS": "decode", "LEGAL": "focus", "JUDGES": "focus"},
    # white cards: (first word, card ends before this word, KEYWORD); refs are inside the body segment
    "cards": [
        (("THEY", 1), ("COACHES", 1), "DRAW"),
        (("IT'S", 2), ("YOU", 3), "CHESS"),
    ],
    "slam": ["DRAW"],
    "bed": "../../listicles/music/epic-bold-drums-alex-morgan.mp3",   # the track from the approved Saenchai editorial cut
}

V = sys.argv[1] if len(sys.argv) > 1 else "A"
d = json.load(open(f"work/edl_{V}.json", encoding="utf-8"))
WORDS = d["words"]
FG = f"assets/media/fg_{V}_full.webm"
HOOK, BODY = d["segments"][0], d["segments"][1]
hook_end = HOOK["end"]


def W(word, k=1, seg=None):
    seg = BODY if seg is None else seg
    return [w for w in WORDS if w["w"] == word and w["seg"] == seg["i"]][k - 1]["s"]


# ---- hook graphic: spoken lines (word spans timed to the EDL) + the per-variant figure
hw = [w for w in WORDS if w["seg"] == HOOK["i"]]
spoken = []  # what the lines show, word by word, matched in order to the EDL words
lines_html, plan_words, wi = [], [], 0
norm = lambda s: re.sub(r"[^A-Z0-9']", "", s.upper())  # noqa: E731
for li, (line,) in enumerate(REEL["hooks"][V]):
    spans = []
    for tok in line.split():
        while wi < len(hw) and norm(hw[wi]["w"]) != norm(tok):
            wi += 1
        s = hw[wi]["s"] if wi < len(hw) else hook_end - 0.3
        wid = f"hw{li}_{len(spans)}"
        cls = " red" if norm(tok) in {"DRAW", "OUT", "FIRST", "16"} else ""
        spans.append(f'<span id="{wid}" class="hk-w{cls}">{html.escape(tok)}</span>')
        plan_words.append({"id": wid, "s": round(s, 3)})
        wi += 1
    lines_html.append('<span class="ln">' + " ".join(spans) + "</span>")
lead = '<div class="hk-lead">' + "".join(lines_html) + "</div>"

t = {k.lower().replace("16", "sixteen"): W(k, 1, HOOK) for k in {w["w"] for w in hw}}
ko = W(REEL["ko_word"][V], 1, HOOK) + 0.05
if V == "A":
    chars = lambda s: "".join(f'<span class="ch">{c}</span>' for c in s)  # noqa: E731
    fig = (f'<div class="plate" id="plate"><div class="lbl mono">OFFICIAL RESULT</div><div class="slot">'
           f'<div class="word" id="koW">{chars("K.O.")}</div><div class="word red" id="drawW">{chars("DRAW")}</div>'
           f'<div class="strike"></div></div></div>')
elif V == "B":
    him = "".join(f'<div class="blk">FIGHT {i}</div>' for i in range(1, 7))
    fig = (f'<div class="stk"><div class="stkbase"></div><div class="col him" id="him">{him}</div>'
           f'<div class="col me" id="me"><div class="blk mine">FIGHT 1</div></div>'
           f'<div class="cap him mono">HIM</div><div class="cap me mono">ME</div></div>')
else:
    digits = "".join(f"<b>{i}</b>" for i in range(1, 7))
    fig = ('<div class="age" id="age"><div class="lbl mono">AGE</div><div class="odo"><span>16</span></div></div>'
           '<div class="recs">'
           f'<div class="rec" id="recHim"><div class="lbl mono">HIS FIGHT</div><div class="num">#<span class="slot1"><span class="col1">{digits}</span></span></div></div>'
           '<div class="rec" id="recMe"><div class="lbl mono">MY FIGHT</div><div class="num red">#1</div><div class="under"></div></div>'
           '</div>')
hook_plan = {"v": V, "end": round(hook_end, 3), "ko": round(ko, 3), "words": plan_words, "t": {k: round(x, 3) for k, x in t.items()}}

# hook sounds (the kit's SFX, far under the voice): impact on the knockout, plus the figure's own beats
sfx = [("impact", ko - 0.03, 0.55)]
if V == "A":
    sfx += [("key", t["called"] - 0.02, 0.35), ("whoom", t["draw"] - 0.22, 0.4), ("sub", t["draw"] + 0.1, 0.5)]
elif V == "B":
    sfx += [("tick", t["stacked"] - 0.05 + 0.07 * i, 0.25) for i in range(6)] + [("whoom", t["knocked"], 0.45)]
else:
    sfx += [("data", t["sixth"] - 0.15, 0.3), ("key", t["first"] - 0.02, 0.4)]
hook_audio = "\n      ".join(
    f'<audio id="hks{i}" src="assets/sfx/ed/{n}.wav" data-start="{max(0, s):.3f}" data-duration="1.2" data-track-index="{30 + i}" data-volume="{v}"></audio>'
    for i, (n, s, v) in enumerate(sfx))

# ---- body: editorial captions, cards, tape cutaways (make_broll.py writes work/broll.json)
cards = [(W(*a) - 0.06, W(*b) - (0.12 if i == len(REEL["cards"]) - 1 else 0.08), kw) for i, (a, b, kw) in enumerate(REEL["cards"])]
head = lambda t_: cutout.head_top(FG, t_) or 660  # noqa: E731
broll = json.load(open("work/broll.json", encoding="utf-8")) if os.path.exists("work/broll.json") else {}
body_broll = {k: v for k, v in broll.items() if not v.get("full")}
broll_html, broll_spans = plan.broll_html(body_broll)
ed = plan.build(d, keys=set(REEL["keys"]), cards=cards, slam=set(REEL["slam"]), fx=REEL["fx"],
                hide=[(0, hook_end)], title_end=hook_end, back_top=lambda t_: head(t_) - 235, broll=broll_spans,
                bed="assets/media/bed" + os.path.splitext(REEL["bed"])[1])
css, js = plan.install(".", bed_seconds=None)
os.makedirs("assets/media", exist_ok=True)
shutil.copy(REEL["bed"], "assets/media/bed" + os.path.splitext(REEL["bed"])[1])

fill = {"ED_CSS": css, "ED_JS": js, "ED_HTML_CAPS": ed["caps"], "ED_HTML_CAPS_BACK": ed["caps_back"],
        "ED_HTML_CARDS": ed["cards"], "ED_AUDIO": ed["audio"], "ED_PLAN": ed["plan"], "ED_BROLL": broll_html,
        "AROLL": f"assets/media/aroll_{V}.mp4", "FG": FG, "DUR": f"{d['duration']:.3f}", "HOOK_END": f"{hook_end:.3f}",
        "HOOK_HTML": lead + fig, "HOOK_PLAN": json.dumps(hook_plan), "HOOK_AUDIO": hook_audio,
        "CAP_TOP": "330", "BACK_TOP": "0"}
src = open("work/template.html", encoding="utf-8").read()
open("index.html", "w", encoding="utf-8").write(re.sub(r"\{\{(\w+)\}\}", lambda m: fill[m.group(1)], src))
print(f"{V}: index.html built, {d['duration']:.1f}s, hook {hook_end:.2f}s (ko {ko:.2f}), "
      f"{len(json.loads(ed['plan'])['phrases'])} phrases, {len(cards)} cards, tape {sorted(broll)}")
