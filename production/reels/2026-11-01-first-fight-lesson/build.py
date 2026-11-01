"""First fight, the lesson (2026-11-01): python -P build.py A

Each variant = open<V> (its loop take: hook + "I was sixteen. My first fight. His sixth.") -> body1 -> share ->
body2 -> end<V> (the same loop take: "It's about control ... <bridge>"), so the replay lands on the hook as one
unbroken sentence. Hook = the knockout tape full-bleed, the hook lines, a WHAT HAPPENED: K.O. plate that gets
struck through and rolls to DRAW. Sound: the editorial kit's quiet caption SFX + the audible retention layer from
sound_design.py (skill reel-sound-design) + the fight tape's own crowd audio.
"""
import html
import json
import os
import re
import shutil
import sys

sys.path.insert(0, "../../editing/reel-kit/editorial")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cutout  # noqa: E402
import plan  # noqa: E402
import sound_design as sd  # noqa: E402
from make_broll import hook_end as _hook_end  # noqa: E402  (also cuts nothing on import)
from reel import REEL  # noqa: E402

V = sys.argv[1] if len(sys.argv) > 1 else "A"
d = json.load(open(f"work/edl_{V}.json", encoding="utf-8"))
WORDS = d["words"]
FG = f"assets/media/fg_{V}_full.webm"
SEG = {("open" if s["name"].startswith("open") else "end" if s["name"].startswith("end") else s["name"]): s
       for s in d["segments"]}
DUR = d["duration"]
norm = lambda s: re.sub(r"[^A-Z0-9']", "", s.upper())  # noqa: E731


def W(seg, word, k=1, end=False):
    hits = [w for w in WORDS if w["seg"] == SEG[seg]["i"] and w["w"] == word]
    return hits[k - 1]["e" if end else "s"]


hook_end = _hook_end(d, V)

# ---- hook: lines that build word by word + the result plate
hw = [w for w in WORDS if w["seg"] == SEG["open"]["i"] and w["s"] < hook_end]
lines_html, plan_words, wi = [], [], 0
for li, line in enumerate(REEL["hooks"][V]):
    spans = []
    for tok in line.split():
        while wi < len(hw) and norm(hw[wi]["w"]) != norm(tok):
            wi += 1
        s = hw[wi]["s"] if wi < len(hw) else hook_end - 0.3
        wid = f"hw{li}_{len(spans)}"
        cls = " red" if norm(tok) in REEL["red"][V] else ""
        spans.append(f'<span id="{wid}" class="hk-w{cls}">{html.escape(tok)}</span>')
        plan_words.append({"id": wid, "s": round(s, 3)})
        wi += 1
        if wi >= len(hw):
            wi = len(hw)
    lines_html.append('<span class="ln">' + " ".join(spans) + "</span>")
lead = '<div class="hk-lead">' + "".join(lines_html) + "</div>"
chars = lambda s: "".join(f'<span class="ch">{c}</span>' for c in s)  # noqa: E731
ko = W("open", REEL["ko_word"][V]) + 0.05
strike = W("open", REEL["strike"][V])
draw_t = max(W("open", REEL["draw"][V]), strike + 0.4)
# per-hook graphic (Matteo 2026-11-01: a different visual hook for every variant, the fight stays behind)
if V == "A":    # result: what happened vs the official result
    fig = (f'<div class="plate" id="plate"><div class="lbl mono" id="koL">WHAT HAPPENED</div><div class="lbl mono red" id="drawL">OFFICIAL RESULT</div><div class="slot">'
           f'<div class="word" id="koW">{chars("K.O.")}</div><div class="word red" id="drawW">{chars("DRAW")}</div>'
           f'<div class="strike"></div></div></div>')
elif V == "B":  # contrast: ended in a K.O. -> should have been an L
    fig = ('<div class="flipcard" id="flip"><div class="lbl mono" id="fL1">ENDED IN</div><div class="lbl mono red" id="fL2">SHOULD HAVE BEEN</div>'
           '<div class="tile"><div class="fc" id="fKO">K.O.</div><div class="fc red" id="fL" style="font-size:330px">L</div></div></div>')
elif V == "C":  # question: a poll that asks for the comment
    fig = ('<div class="poll" id="poll"><div class="q" id="pQ">DOES IT COUNT?</div>'
           '<div class="opt" id="pY"><span>YES</span></div><div class="opt no" id="pN"><span>NO</span></div>'
           '<div class="hint mono" id="pH">VOTE IN THE COMMENTS</div></div>')
elif V == "D":  # reframe: pride meter drains
    fig = ('<div class="meter" id="meter"><div class="lbl mono">PROUD OF IT</div>'
           '<div class="track"><div class="fill" id="mFill"></div></div>'
           '<div class="pct"><span id="m100">100%</span><span class="red" id="m3">3%</span></div></div>')
else:           # number: the stopwatch from the ref stepping in to the punch (tape: 47.9 s -> 48.33 s)
    steps = "".join(f'<span class="st" id="sw{i}">+0.{i}s</span>' for i in range(5))
    fig = (f'<div class="watch" id="watch"><div class="lbl mono">AFTER THE REF STEPPED IN</div>'
           f'<div class="sw">{steps}</div><div class="bar"><div class="barf" id="swF"></div></div></div>')
hook_t = {}
for w in hw:
    hook_t.setdefault(norm(w["w"]), w["s"])
hook_plan = {"v": V, "plate": V == "A", "end": round(hook_end, 3), "ko": round(ko, 3), "strike": round(strike, 3),
             "draw": round(draw_t, 3), "words": plan_words, "t": {k: round(x, 3) for k, x in hook_t.items()}}

# ---- body: editorial captions, cards, tape cutaways
cards = []
for i, (a, b, kw) in enumerate(REEL["cards"]):
    t0 = W(*a) - 0.06
    t1 = W(*b) - 0.08
    cards.append((t0, t1, kw))
head = lambda t_: cutout.head_top(FG, t_) or 660  # noqa: E731
broll = json.load(open("work/broll.json", encoding="utf-8"))
body_broll = {k: v for k, v in broll.items() if not v.get("full")}
broll_html, broll_spans = plan.broll_html(body_broll)
ed = plan.build(d, keys=set(REEL["keys"]), cards=cards, slam=set(REEL["slam"]), fx=REEL["fx"], fix=REEL["fix"] or None,
                hide=[(0, hook_end)], title_end=hook_end, back_top=lambda t_: head(t_) - 235, broll=broll_spans,
                bed="assets/media/bed" + os.path.splitext(REEL["bed"])[1], bed_base=0.16, bed_card=0.4)
css, js = plan.install(".", bed_seconds=None)
os.makedirs("assets/media", exist_ok=True)
shutil.copy(REEL["bed"], "assets/media/bed" + os.path.splitext(REEL["bed"])[1])

# ---- music: silence before the verdict, never fade to zero at the end (the loop must not dip)
draw_word = W("body1", "DRAW")
fight = broll["fight"]


def bed_fix(m):
    auto = json.loads(m.group(1))
    pts = [p for p in auto["lanes"][0]["points"] if not (p["v"] == 0 and p["t"] >= DUR - 0.01)]
    cut0, cut1 = round(draw_word - 0.12, 3), round(W("body1", "THEY", 2) + 0.05, 3)
    pts = [p for p in pts if not (cut0 - 0.05 <= p["t"] <= cut1 + 0.3)]
    pts += [{"t": round(cut0 - 0.04, 3), "v": 0.16}, {"t": cut0, "v": 0.0}, {"t": cut1, "v": 0.0}, {"t": round(cut1 + 0.25, 3), "v": 0.16},
            {"t": round(DUR, 3), "v": 0.16}]
    auto["lanes"][0]["points"] = sorted(pts, key=lambda p: p["t"])
    return "data-automation='" + json.dumps(auto, separators=(",", ":")) + "'"


audio = re.sub(r"data-automation='([^']*)'", bed_fix, ed["audio"])
# the kit's slam sub doubles with our boom on DRAW: drop it
audio = re.sub(r'\s*<audio id="ed-sfx\d+" src="assets/sfx/ed/sub.wav"[^>]*></audio>', "", audio)

# ---- the audible retention layer (skill reel-sound-design)
sd.make_all("assets/sfx/sd")
first_after = [w for w in WORDS if w["seg"] == SEG["open"]["i"] and w["w"] == "FIRST" and w["s"] > hook_end]
cues = [
    ("hit", ko - 0.03, 0.85),                       # the knockout lands on the hook word
    ("whoosh", strike - 0.2, 0.4),                  # K.O. struck through
    ("thud", draw_t + 0.02, 0.5),                   # DRAW drops in
    ("whoosh", hook_end - 0.2, 0.45),               # tape -> face
    ("heart", W("body1", "SOMEONE") - 0.05, 0.45),  # the pressure line
    ("whoosh", fight["start"] - 0.18, 0.45),        # tape whips in
    ("hit", W("body1", "RIGHT") + 0.0, 0.7),        # the right hand on tape
    ("riser", draw_word - 0.12 - 2.0, 0.4),         # tension into the verdict, ends hard where the music cuts
    ("boom", draw_word - 0.02, 0.7),                # DRAW
    ("shutter", broll["freeze"]["start"] + 0.33, 0.6),   # the freeze on the late punch
    ("whoosh", SEG["share"]["start"] - 0.18, 0.3),  # jump cut into the share line
    ("whoosh", SEG["body2"]["start"] - 0.18, 0.25),
]
if first_after:
    cues.append(("bell", first_after[0]["s"] - 0.02, 0.32))
# ---- attention rule: something visual or audible every <= 3 s (Matteo 2026-11-01)
P = json.loads(ed["plan"])
events = [hook_end] + [x for v in broll.values() for x in (v["start"], v["start"] + v["dur"])]
events += [x for c in cards for x in c[:2]] + list(d.get("joins", []))
events += [w["s"] for ph in P["phrases"] for w in ph["words"] if w.get("key")]
events += [t for n, t, v in cues if n in ("hit", "boom", "whoosh", "bell", "heart", "shutter", "thud")]
phrase_starts = [ph["t0"] for ph in P["phrases"]]
beats = sd.fill_gaps(events, 0.0, DUR - 0.3, phrase_starts, max_gap=3.0)
cues += [("thud" if i % 2 else "whoosh", t - (0 if i % 2 else 0.15), 0.22) for i, t in enumerate(beats)]
punch_js = "".join(f'tl.to("#cam-punch", {{scale:{1.05 if i % 2 == 0 else 1.0}, duration:0.14, ease:"power3.out"}}, {t:.3f});'
                   for i, t in enumerate(beats))
# the face must be back at 1.0 before the loop seam and whenever a card/b-roll ends (fresh framing after cutaways)
punch_js += f'tl.set("#cam-punch", {{scale:1}}, {max(0, DUR - 0.5):.3f});'
for i, (t0, t1, _) in enumerate(cards):
    punch_js += f'tl.set("#cam-punch", {{scale:1}}, {t1:.3f});'
cues = [c for c in cues if c[1] < DUR - 0.45]       # nothing rings across the loop seam
sd_audio = sd.tags(cues, sfx_dir="assets/sfx/sd", track0=40, total=DUR - 0.05)
tape_audio = "\n      ".join(
    f'<audio id="tape_{k}" src="assets/media/b_{k}.wav" data-start="{v["start"]:.3f}" data-duration="{v["dur"]:.3f}" '
    f'data-track-index="{36 + i}" data-volume="{0.5 if k == "hook" else 0.4}"></audio>'
    for i, (k, v) in enumerate(broll.items()) if v.get("audio"))

# ---- overlay labels: the comment driver on the tape, LATE on the freeze
fz = broll["freeze"]
labels = (f'<div id="lbl1" class="clip tag" data-start="{fight["start"]:.3f}" data-duration="{fight["dur"]:.3f}" data-track-index="7">'
          f'<span>DQ or draw?</span></div>'
          f'<div id="lbl2" class="clip tag late" data-start="{fz["start"]:.3f}" data-duration="{fz["dur"]:.3f}" data-track-index="8">'
          f'<span>LATE</span><small>the ref was already in</small></div>')
label_js = (f'tl.fromTo("#lbl1 span", {{opacity:0, y:14, filter:"blur(10px)"}}, {{opacity:1, y:0, filter:"blur(0px)", duration:0.3, ease:"power4.out", immediateRender:true}}, {fight["start"] + 0.25:.3f});'
            f'tl.fromTo("#lbl2 span", {{opacity:0, scale:1.25, filter:"blur(8px)"}}, {{opacity:1, scale:1, filter:"blur(0px)", duration:0.28, ease:"power4.out", immediateRender:true}}, {fz["start"] + 0.33:.3f});'
            f'tl.fromTo("#lbl2 small", {{opacity:0, y:10}}, {{opacity:1, y:0, duration:0.3, ease:"power4.out", immediateRender:true}}, {fz["start"] + 0.55:.3f});')

fill = {"ED_CSS": css, "ED_JS": js, "ED_HTML_CAPS": ed["caps"], "ED_HTML_CAPS_BACK": ed["caps_back"],
        "ED_HTML_CARDS": ed["cards"] + "\n      " + labels, "ED_AUDIO": audio + "\n      " + sd_audio + "\n      " + tape_audio,
        "ED_PLAN": ed["plan"], "ED_BROLL": broll_html,
        "AROLL": f"assets/media/aroll_{V}.mp4", "FG": FG, "DUR": f"{DUR:.3f}", "HOOK_END": f"{hook_end:.3f}",
        "HOOK_HTML": lead + fig, "HOOK_PLAN": json.dumps(hook_plan), "HOOK_AUDIO": "", "EXTRA_JS": label_js + punch_js,
        "CAP_TOP": "330", "BACK_TOP": "0"}
src = open("work/template.html", encoding="utf-8").read()
open("index.html", "w", encoding="utf-8").write(re.sub(r"\{\{(\w+)\}\}", lambda m: fill[m.group(1)], src))
print(f"{V}: index.html built, {DUR:.1f}s, hook {hook_end:.2f}s (ko {ko:.2f}, strike {strike:.2f}), "
      f"{len(json.loads(ed['plan'])['phrases'])} phrases, {len(cards)} cards, tape {sorted(broll)}, {len(cues)} sd cues, "
      f"punch-ins at {beats}")
