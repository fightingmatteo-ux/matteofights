"""Editorial caption + quote-card + SFX planner (the kaixerb "premium minimal" look).

Called from a reel's inject/build script after the EDL is loaded:

    import sys; sys.path.insert(0, "../../editing/reel-kit/editorial")
    import plan
    css, js = plan.install(".", bed_seconds=d["duration"])
    ed = plan.build(d, keys={"HEAD", "INFORMATION"}, cards=[(t0, t1, "INFORMATION")], hide=[(0, 2.4)])
    # fill {{ED_CSS}} {{ED_JS}} {{ED_HTML_CAPS}} {{ED_HTML_CARDS}} {{ED_AUDIO}} {{ED_PLAN}} in the template

The template inlines editorial.css + editorial.js and calls Editorial.animate(tl, PLAN, {cam: "#cam-inner"}).
Worked example: production/reels/2026-10-20-freeze-editorial/ (build.py). Rules, from the reference:
- captions = short phrases (1-4 words) that come into focus word by word (blur -> sharp, ~0.3 s); the phrase
  dissolves into blur (~0.18 s) while the next one is already focusing in (crossfade, never a gap)
- at most ONE keyword per phrase: its own line, much bigger, red, with an effect that MEANS the word (FX below);
  up to 2 small words may follow it on a tail line (lead top-left, keyword, tail bottom-right)
- keyword phrases alternate between IN FRONT of Matteo and BEHIND him (his cut-out covers the keyword's lower
  edge); needs fg_<V>.webm from cutout.py
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

# keyword effect = what the word means. Override per reel with build(fx={"WORD": "effect"}).
FX = {"RESET": "rewind", "RESTART": "rewind", "AGAIN": "rewind", "BACK": "rewind",
      "JAB": "jab", "PUNCH": "jab", "PUNCHED": "jab", "HIT": "jab", "STRIKE": "jab",
      "CAUGHT": "impact", "KNOCKED": "impact", "SLAM": "impact", "HURT": "impact",
      "RELAX": "exhale", "BREATH": "exhale", "BREATHE": "exhale", "CALM": "exhale",
      "INFORMATION": "decode", "DATA": "decode", "THINKING": "decode", "LEARN": "decode",
      "ONE": "count", "TWO": "count", "THREE": "count", "FOUR": "count", "FIVE": "count",
      "FREEZE": "freeze", "FROZE": "freeze", "STUCK": "freeze"}
FX_SFX = {"rewind": ("rewind", -0.5, 0.45), "jab": ("punch", -0.1, 0.5), "impact": ("impact", -0.03, 0.5),
          "exhale": ("exhale", -0.05, 0.4), "decode": ("data", -0.02, 0.3), "count": ("key", -0.04, 0.3),
          "freeze": ("shimmer", -0.02, 0.4), "focus": ("key", -0.04, 0.3)}
NUM = {"ONE": "1", "TWO": "2", "THREE": "3", "FOUR": "4", "FIVE": "5"}


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
            ki = next((j for j, x in enumerate(cur) if x["w"] in keys), None)
            after_key = 0 if ki is None else len(cur) - 1 - ki
            brk = (w["s"] - prev["e"] > gap or len(cur) >= maxw or prev["seg"] != w["seg"]
                   or (w["w"] in BREAK_BEFORE and len(cur) >= 2)
                   or (ki is not None and (w["w"] in keys or after_key >= 2)))
            if brk:
                out.append(cur); cur = []
        cur.append(w)
    if cur:
        out.append(cur)
    return out


def key_html(wid, word, fx, extra_cls=""):
    """A keyword as per-letter spans (effects move letters, never letter-spacing), plus a ghost numeral for count."""
    chars = "".join(f'<span class="ed-c">{html.escape(c)}</span>' for c in word)
    ghost = f'<span class="ed-ghost">{NUM[word.upper()]}</span>' if fx == "count" and word.upper() in NUM else ""
    return f'<span id="{wid}" class="ed-w ed-key{extra_cls}" data-fx="{fx}">{ghost}{chars}</span>'


def build(d, keys=(), cards=(), hide=(), fix=None, slam=(), dip=None, title_end=0.0, fx=None, behind=True, back_top=None,
          bed="assets/media/bed.wav", bed_base=0.20, bed_card=0.45, sfx_dir="assets/sfx/ed"):
    """keys: UPPERCASE words to emphasise. cards: (t0, t1, KEYWORD) spans cut to white. hide: (a, b) spans with no
    captions (the hook title). slam: keywords on cards that scale past the frame edges + sub. dip: (t0, t1) fade to
    black at the end (sub on it). title_end: when the hook title clears (gets a shimmer at 0). fx: {WORD: effect}
    overrides FX. behind: alternate keyword phrases behind Matteo (template needs #ed-caps-back + the fg cut-out).
    back_top(t) -> px: where a behind phrase starts at time t, e.g. from cutout.head_top() so his hair always
    covers the keyword's lower edge (head_top - 235 tucks ~a quarter of the letters into the hair)."""
    keys = set(keys)
    fxmap = {**FX, **(fx or {})}
    fx_of = lambda w: fxmap.get(w, "focus")
    words = d["words"]
    in_span = lambda t, spans: any(a <= t < b for a, b, *_ in spans)
    caps_html, back_html, cards_html, audio, plan = [], [], [], [], {"phrases": [], "cards": [], "faces": [], "dip": dip, "title_end": title_end}
    sfx = []  # (file, t, vol)

    # ---- captions over the face ----
    face_words = [w for w in words if not in_span(w["s"], cards) and not in_span(w["s"], hide)]
    nkey = 0
    for pi, ph in enumerate(phrases(face_words, keys)):
        pid = f"ph{pi}"
        lead, keyh, tail, pw = [], "", [], []
        seen_key = False
        for wi, w in enumerate(ph):
            wid = f"{pid}w{wi}"
            if w["w"] in keys and not seen_key:
                seen_key = True
                f = fx_of(w["w"])
                keyh = key_html(wid, disp(w["w"], fix), f)
                pw.append({"id": wid, "s": w["s"], "key": True, "fx": f})
                sf, off, vol = FX_SFX[f]
                sfx.append((sf, w["s"] + off, vol))
            else:
                (tail if seen_key else lead).append(f'<span id="{wid}" class="ed-w">{html.escape(disp(w["w"], fix))}</span>')
                pw.append({"id": wid, "s": w["s"], "key": False})
        layer = "front"
        if keyh:
            layer = "back" if behind and nkey % 2 == 1 else "front"
            nkey += 1
        cls = "ed-ph" + (" ed-split" if keyh else "")
        inner = (f'<div class="ed-lead">{" ".join(lead)}</div>' + (f'<div class="ed-keyline">{keyh}</div>' if keyh else "")
                 + (f'<div class="ed-tail">{" ".join(tail)}</div>' if tail else ""))
        style = ""
        if layer == "back" and back_top:
            ys = [y for y in (back_top(ph[0]["s"]), back_top((ph[0]["s"] + ph[-1]["e"]) / 2), back_top(ph[-1]["e"] + 0.3))
                  if y is not None]
            y = min(ys) if ys else None   # the highest his head gets while the phrase is up
            if y is not None:
                style = f' style="top:{max(260, int(y))}px;bottom:auto;height:440px"'
        (back_html if layer == "back" else caps_html).append(f'<div id="{pid}" class="{cls}"{style}>{inner}</div>')
        plan["phrases"].append({"id": pid, "t0": ph[0]["s"], "end": ph[-1]["e"], "words": pw, "layer": layer})
        sfx.append(("tick", ph[0]["s"] - TICK_LEAD, 0.22))
    for a, b in zip(plan["phrases"], plan["phrases"][1:] + [None]):
        nxt = b["t0"] if b else d["duration"]
        card_next = min([c[0] for c in cards if c[0] >= a["t0"]] + [9e9])
        if card_next <= nxt:   # a card cuts in: be gone by then
            a["t1"] = min(card_next - 0.02, a["end"] + 0.7)
        else:                  # crossfade: start dissolving as the next phrase starts focusing in
            a["t1"] = min(nxt + 0.03, a["end"] + 0.7)

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
            f = fx_of(kw)
            k_html = f'<div class="ed-cardkey{" ed-slam" if kw in slam else ""}" style="font-size:{size}px">{key_html(f"{cid}w{j}", disp(keyw["w"], fix), f)}</div>'
            cwords.append({"id": f"{cid}w{j}", "s": keyw["s"], "key": True, "slam": kw in slam, "fx": f}); j += 1
            sf, off, vol = FX_SFX[f]
            sfx.append((sf, keyw["s"] + off, vol + 0.1))
            if kw in slam:
                sfx.append(("sub", keyw["s"] + 0.04, 0.5))
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
    dur = {"tick": 0.07, "key": 0.45, "whoom": 0.6, "shimmer": 0.35, "sub": 1.4, "rewind": 0.63, "punch": 0.34,
           "impact": 0.9, "exhale": 1.0, "data": 0.484}
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
    return {"caps": "\n      ".join(caps_html), "caps_back": "\n        ".join(back_html), "cards": "\n      ".join(cards_html), "audio": "\n      ".join(audio),
            "plan": json.dumps(plan, separators=(",", ":"))}
