"""Editorial caption + quote-card + SFX planner (the kaixerb "premium minimal" look).

Called from a reel's inject/build script after the EDL is loaded:

    import sys; sys.path.insert(0, "../../editing/reel-kit/editorial")
    import plan
    css, js = plan.install(".", bed_seconds=d["duration"])
    ed = plan.build(d, keys={"HEAD", "INFORMATION"}, cards=[(t0, t1, "INFORMATION")], hide=[(0, 2.4)])
    # fill {{ED_CSS}} {{ED_JS}} {{ED_HTML_CAPS}} {{ED_HTML_CARDS}} {{ED_AUDIO}} {{ED_PLAN}} in the template

The template inlines editorial.css + editorial.js and calls Editorial.animate(tl, PLAN, {cam: "#cam-inner"}).
Worked example: production/reels/2026-10-20-freeze-editorial/ (build.py). Rules, from the reference:
- captions = short phrases (1-4 words) that build word by word; a phrase clears before the next lands
- at most ONE keyword per phrase: it goes on its own line, much bigger, red; the phrase breaks after it
- quote cards = the important line cut to white, black type building on the voice, the keyword huge in red;
  the music bed lifts under the card so the line lands, then a hard cut back to the face
- SFX: a quiet tick ~50 ms before each phrase, a tonal "key" under keywords, a soft whoom into each card,
  a sub on the slam card or the dip to black
"""
import html
import json
import shutil
from pathlib import Path

KIT = Path(__file__).resolve().parent
FONT = KIT / "fonts/Geist-latin.woff2"

BREAK_BEFORE = {"AND", "BUT", "BECAUSE", "SO", "THEN", "IF", "OR", "WHEN"}
KEEP = {"I": "I", "I'M": "I'm", "I'D": "I'd", "I'LL": "I'll", "I'VE": "I've"}
TICK_LEAD, KEY_LEAD = 0.05, 0.04


def install(reel, bed_seconds=None):
    """Copy the SFX + Geist into <reel>/assets and (re)make the piano bed. Returns (css, js) to inline."""
    reel = Path(reel)
    (reel / "assets/sfx/ed").mkdir(parents=True, exist_ok=True)
    (reel / "assets/fonts").mkdir(parents=True, exist_ok=True)
    for f in (KIT / "sfx").glob("*.wav"):
        if f.name != "bed.wav":
            shutil.copy(f, reel / "assets/sfx/ed" / f.name)
    shutil.copy(FONT, reel / "assets/fonts/Geist-latin.woff2")
    if bed_seconds:
        import make_audio
        (reel / "assets/media").mkdir(parents=True, exist_ok=True)
        make_audio.save(reel / "assets/media/bed.wav", make_audio.bed(bed_seconds))
    return (KIT / "editorial.css").read_text(encoding="utf-8"), (KIT / "editorial.js").read_text(encoding="utf-8")


def disp(w, fix=None):
    if fix and w in fix:
        return fix[w]
    return KEEP.get(w, w.lower())


def phrases(words, keys, gap=0.22, maxw=4):
    out, cur = [], []
    for i, w in enumerate(words):
        if cur:
            prev = cur[-1]
            brk = (w["s"] - prev["e"] > gap or len(cur) >= maxw or prev["w"] in keys or prev["seg"] != w["seg"]
                   or (w["w"] in BREAK_BEFORE and len(cur) >= 2))
            if brk:
                out.append(cur); cur = []
        cur.append(w)
    if cur:
        out.append(cur)
    return out


def build(d, keys=(), cards=(), hide=(), fix=None, slam=(), dip=None, title_end=0.0,
          bed="assets/media/bed.wav", bed_base=0.20, bed_card=0.45, sfx_dir="assets/sfx/ed"):
    """keys: UPPERCASE words to emphasise. cards: (t0, t1, KEYWORD) spans cut to white. hide: (a, b) spans with no
    captions (the hook title). slam: keywords on cards that scale past the frame edges + sub. dip: (t0, t1) fade to
    black at the end (sub on it). title_end: when the hook title clears (gets a shimmer at 0)."""
    keys = set(keys)
    words = d["words"]
    in_span = lambda t, spans: any(a <= t < b for a, b, *_ in spans)
    caps_html, cards_html, audio, plan = [], [], [], {"phrases": [], "cards": [], "faces": [], "dip": dip, "title_end": title_end}
    sfx = []  # (file, t, vol)

    # ---- captions over the face ----
    face_words = [w for w in words if not in_span(w["s"], cards) and not in_span(w["s"], hide)]
    for pi, ph in enumerate(phrases(face_words, keys)):
        pid = f"ph{pi}"
        spans, pw = [], []
        for wi, w in enumerate(ph):
            k = w["w"] in keys
            cls = "ed-w ed-key" if k else "ed-w"
            spans.append(f'<span id="{pid}w{wi}" class="{cls}">{html.escape(disp(w["w"], fix))}</span>')
            pw.append({"id": f"{pid}w{wi}", "s": w["s"], "key": k})
            if k:
                sfx.append(("key", w["s"] - KEY_LEAD, 0.30))
        lead = [s for s, w in zip(spans, ph) if w["w"] not in keys]
        key = [s for s, w in zip(spans, ph) if w["w"] in keys]
        inner = f'<div class="ed-lead">{" ".join(lead)}</div>' + (f'<div class="ed-keyline">{key[0]}</div>' if key else "")
        caps_html.append(f'<div id="{pid}" class="ed-ph">{inner}</div>')
        plan["phrases"].append({"id": pid, "t0": ph[0]["s"], "end": ph[-1]["e"], "words": pw})
        sfx.append(("tick", ph[0]["s"] - TICK_LEAD, 0.22))
    for a, b in zip(plan["phrases"], plan["phrases"][1:] + [None]):
        nxt = b["t0"] if b else d["duration"]
        stop = min([c[0] for c in cards if c[0] >= a["t0"]] + [nxt])  # clear before a card cuts in
        a["t1"] = min(stop - 0.04, a["end"] + 0.5)

    # ---- white quote cards ----
    for ci, (t0, t1, kw) in enumerate(cards):
        cid = f"card{ci}"
        cw = [w for w in words if t0 - 0.02 <= w["s"] < t1]
        before, keyw, after = [], None, []
        for w in cw:
            if keyw is None and w["w"] == kw:
                keyw = w
            elif keyw is None:
                before.append(w)
            else:
                after.append(w)
        sp = lambda w, j: f'<span id="{cid}w{j}" class="ed-w">{html.escape(disp(w["w"], fix))}</span>'
        j = 0; b_html = []; a_html = []; cwords = []
        for w in before:
            b_html.append(sp(w, j)); cwords.append({"id": f"{cid}w{j}", "s": w["s"], "key": False}); j += 1
        k_html = ""
        if keyw:
            size = min(300 if kw in slam else 230, int(920 / (0.56 * len(disp(keyw["w"], fix)))))  # never past the edges
            k_html = f'<div class="ed-cardkey{" ed-slam" if kw in slam else ""}" style="font-size:{size}px"><span id="{cid}w{j}" class="ed-w">{html.escape(disp(keyw["w"], fix))}</span></div>'
            cwords.append({"id": f"{cid}w{j}", "s": keyw["s"], "key": True, "slam": kw in slam}); j += 1
            sfx.append(("sub" if kw in slam else "key", keyw["s"] - KEY_LEAD, 0.55 if kw in slam else 0.34))
        for w in after:
            a_html.append(sp(w, j)); cwords.append({"id": f"{cid}w{j}", "s": w["s"], "key": False}); j += 1
        cards_html.append(
            f'<div id="{cid}" class="clip ed-card" data-start="{t0:.3f}" data-duration="{t1 - t0:.3f}" data-track-index="6">'
            f'<div class="ed-cardbox"><div class="ed-cardlead">{" ".join(b_html)}</div>{k_html}'
            f'<div class="ed-cardtail">{" ".join(a_html)}</div></div></div>')
        plan["cards"].append({"id": cid, "t0": t0, "t1": t1, "words": cwords})
        sfx.append(("whoom", t0 - 0.18, 0.30))

    # ---- face stretches (for the slow push + alternating punch-in) ----
    edges = sorted([0.0, d["duration"]] + [x for c in cards for x in c[:2]])
    for a, b in zip(edges[::2], edges[1::2]):
        if b - a > 0.05:
            plan["faces"].append([a, b])

    if dip:
        sfx.append(("sub", dip[0], 0.6))
    sfx.append(("shimmer", 0.0, 0.25))

    # ---- audio tags (alternate tracks so short SFX never share one) ----
    sfx = sorted((f, max(0.0, t), v) for f, t, v in sfx)
    dur = {"tick": 0.07, "key": 0.45, "whoom": 0.6, "shimmer": 0.35, "sub": 1.4}
    for n, (f, t, v) in enumerate(sorted(sfx, key=lambda x: x[1])):
        audio.append(f'<audio id="ed-sfx{n}" src="{sfx_dir}/{f}.wav" data-start="{t:.3f}" data-duration="{min(dur[f], d["duration"] - t):.3f}" '
                     f'data-track-index="{20 + n % 4}" data-volume="{v}"></audio>')
    # bed: low under the face, lifts under each card so the line lands, out at the dip/end
    pts = [{"t": 0, "v": bed_base}]
    for t0, t1, *_ in cards:
        pts += [{"t": round(t0 - 0.05, 3), "v": bed_base}, {"t": round(t0 + 0.1, 3), "v": bed_card},
                {"t": round(t1, 3), "v": bed_card}, {"t": round(t1 + 0.25, 3), "v": bed_base}]
    end = dip[0] if dip else d["duration"]
    pts += [{"t": round(end - 0.3, 3), "v": bed_base if not dip else bed_card}, {"t": round(d["duration"], 3), "v": 0}]
    auto = json.dumps({"version": 1, "lanes": [{"target": "volume", "points": pts}]}, separators=(",", ":"))
    audio.append(f'<audio id="ed-bed" src="{bed}" data-start="0" data-duration="{d["duration"]:.3f}" data-track-index="11" '
                 f"data-volume=\"1\" data-automation='{auto}'></audio>")
    return {"caps": "\n      ".join(caps_html), "cards": "\n      ".join(cards_html), "audio": "\n      ".join(audio),
            "plan": json.dumps(plan, separators=(",", ":"))}
