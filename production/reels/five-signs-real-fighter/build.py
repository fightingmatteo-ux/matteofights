"""Build the HyperFrames composition for this reel.

Everything is authored in SOURCE time (seconds in raw/raw.mp4, i.e. the Whisper
timestamps). `out()` maps a source time onto the cut timeline, so changing the cut
list re-times captions, overlays, b-roll and SFX automatically.

Usage:  python -P build.py      (writes index.html + preprocesses b-roll into assets/cut/)
"""
import json
import os
import re
import subprocess

ROOT = os.path.dirname(os.path.abspath(__file__))
A = lambda *p: os.path.join(ROOT, *p)

# ---------------------------------------------------------------- cut list
# Kept source ranges, in order. Cuts sit inside measured silences.
SEGMENTS = [
    (0.00, 9.60), (9.98, 14.98), (15.30, 17.33), (17.75, 21.40), (21.90, 32.00),
    (32.78, 33.47), (33.70, 34.27), (34.45, 42.18), (42.56, 48.40),
]
FPS = 30
# Snap cuts to the frame grid so adjacent clips butt exactly (no 1-frame gaps).
SEGMENTS = [(round(a * FPS) / FPS, round(b * FPS) / FPS) for a, b in SEGMENTS]
# Punch-in scale per segment (start, end) - alternating hides the jump cuts.
SEG_SCALE = [(1.0, 1.045), (1.11, 1.13), (1.0, 1.02), (1.1, 1.12), (1.0, 1.05),
             (1.24, 1.26), (1.34, 1.36), (1.0, 1.03), (1.1, 1.14)]

_starts = []
_acc = 0.0
for a, b in SEGMENTS:
    _starts.append(_acc)
    _acc += b - a
TOTAL = round(_acc, 3)


def out(src):
    """Source time -> output time (snaps times inside a removed gap to the next cut)."""
    for (a, b), o in zip(SEGMENTS, _starts):
        if src < a:
            return round(o, 3)
        if src <= b:
            return round(o + src - a, 3)
    return TOTAL


def seg_end_out(i):
    a, b = SEGMENTS[i]
    return round(_starts[i] + b - a, 3)


# ---------------------------------------------------------------- events (source time)
E = dict(
    hook_whip=1.10, pips_in=2.15,
    n1=4.24, n1_off=7.80, n2=9.98, n2_off=12.90, n3=15.30, n3_off=18.60,
    n4=20.78, n4_off=24.10, n5=26.86, n5_off=30.20,
    light=5.94, smoked_in=7.78, smoked_hit=8.70,
    gcard_in=11.85, blurry=13.18, google=14.48,
    text_in=16.30, chat_in=17.75, read=19.32,
    receipt_in=22.70, paid=23.38, burpee_in=25.40, burpee_cut=26.20,
    graph_in=27.95, graph_q=29.64, tired_in=30.30,
    metoo=32.78, stance=35.82, st_bg=36.25,
    f1=37.14, f2=38.00, f3=39.16, f4=40.60, st_broll2=39.10,
    lockup=42.56, cta=44.30, cta_type=44.92, early=45.86, chips=46.30, end=48.40,
)
T = {k: out(v) for k, v in E.items()}
T["total"] = TOTAL
T["seg"] = [[round(_starts[i], 3), seg_end_out(i), SEG_SCALE[i][0], SEG_SCALE[i][1]]
            for i in range(len(SEGMENTS))]
# Badge windows: from the spoken number until the burned-in number leaves (+0.1s).
T["badges"] = [[out(E[f"n{i}"]), out(E[f"n{i}_off"])] for i in range(1, 6)]

# ---------------------------------------------------------------- b-roll
# id, mixkit file, clip-in (s), output start (src event), output end (src event), whip-out
BROLL = [
    ("b-hook", "mk40971", 2.55, 0.0, None, True),          # ends at hook_whip
    ("b-smoked", "mk40974", 4.40, E["smoked_in"], 9.60, False),
    ("b-gym", "mk40972", 1.00, 11.10, 12.36, True),
    ("b-text", "mk41173", 4.00, E["text_in"], 17.33, False),
    ("b-burpee", "mk40246", 3.20, E["burpee_in"], E["burpee_cut"], False),
    ("b-ropes", "mk52079", 1.40, E["burpee_cut"], E["n5"], True),
    ("b-tired", "mk40275", 0.40, E["tired_in"], 32.00, False),
    ("b-bag", "mk40276", 1.00, E["st_bg"], E["st_broll2"], False),
    ("b-prep", "mk41001", 2.00, E["st_broll2"], 42.18, False),
    ("b-phone", "mk41173", 8.00, E["cta"], E["chips"], True),
]
WHIP_OUT = 0.26
BROLL_GRADE = ("eq=contrast=1.08:saturation=0.92:brightness=-0.03,"
               "colorbalance=rm=0.03:bm=-0.03:rs=0.01:bs=-0.02,vignette=PI/4.5")


def build_broll():
    os.makedirs(A("assets", "cut"), exist_ok=True)
    clips = []
    for cid, src, cin, s_in, s_out, whip in BROLL:
        o_in = out(s_in)
        o_out = T["hook_whip"] if s_out is None else out(s_out)
        dur = round(o_out - o_in + (WHIP_OUT if whip else 0), 3)
        dst = A("assets", "cut", f"{cid}.mp4")
        if not os.path.exists(dst):
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(cin), "-t", str(dur + 0.1),
                            "-i", A("assets", "broll", src + ".mp4"), "-an",
                            "-vf", BROLL_GRADE + ",scale=1080:1920,fps=30,format=yuv420p",
                            "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-g", "15",
                            dst], check=True)
        clips.append(dict(id=cid, start=o_in, dur=dur, whip=whip, end=o_out))
    return clips


# ---------------------------------------------------------------- captions
FIX = {"stands": "Stance", "red": "read"}
EMPHASIS = {"smoked", "google", "read", "burpees", "better", "stance", "fighters"}
NO_CAPTION = (out(35.70), out(42.18))   # feature rows carry the words here


def load_words():
    words = json.load(open(A("work", "words.json"), encoding="utf-8"))
    res = []
    for i, w in enumerate(words):
        t = w["text"].strip()
        if t.startswith("-") and res:            # "drop" + "-in" -> "drop-in"
            res[-1]["text"] += t
            res[-1]["end"] = w["end"]
            continue
        bare = re.sub(r"[^\w']", "", t).lower()
        if bare == "of" and i + 1 < len(words) and words[i + 1]["text"].strip().lower() == "one":
            t = "off"                           # "a new gym off one blurry photo"
        t = FIX.get(bare, t) if bare in FIX else t
        res.append(dict(text=t, start=w["start"], end=w["end"]))
    return res


def seg_index(src):
    for i, (a, b) in enumerate(SEGMENTS):
        if a - 0.05 <= src <= b + 0.05:
            return i
    return -1


def build_captions():
    words = [w for w in load_words() if seg_index(w["start"]) >= 0]
    groups, cur = [], []

    def flush():
        if cur:
            groups.append(list(cur))
            cur.clear()

    for w in words:
        bare = re.sub(r"[^\w']", "", w["text"]).lower()
        if bare in EMPHASIS:
            flush()
            cur.append(w)
            flush()
            continue
        if cur:
            chars = sum(len(x["text"]) + 1 for x in cur) + len(w["text"])
            prev = cur[-1]
            if (len(cur) >= 3 or chars > 15 or w["start"] - prev["end"] > 0.3
                    or bare == "number" or seg_index(prev["start"]) != seg_index(w["start"])
                    or re.search(r"[.,?!]$", prev["text"])):
                flush()
        cur.append(w)
    flush()

    caps = []
    for gi, g in enumerate(groups):
        s = out(g[0]["start"])
        nxt = out(groups[gi + 1][0]["start"]) if gi + 1 < len(groups) else TOTAL
        e = min(nxt, out(g[-1]["end"]) + 0.35, TOTAL)
        if s >= NO_CAPTION[0] - 0.05 and s < NO_CAPTION[1]:
            continue
        if e - s < 0.12:
            continue
        big = len(g) == 1 and re.sub(r"[^\w']", "", g[0]["text"]).lower() in EMPHASIS
        caps.append(dict(start=s, end=round(e, 3), big=big,
                         words=[dict(t=re.sub(r"[.,?!]", "", x["text"]).upper(),
                                     s=max(s, out(x["start"])), e=out(x["end"])) for x in g]))
    return caps


# ---------------------------------------------------------------- audio
def sfx(name, src_t=None, out_t=None, vol=0.7, dur=None, media_start=0.0):
    t = out_t if out_t is not None else out(src_t)
    return dict(name=name, t=round(max(0.0, t), 3), vol=vol, dur=dur, ms=media_start)


def build_sfx():
    s = [
        sfx("impact-bass-1", out_t=0.0, vol=0.85), sfx("hit-stance", out_t=0.43, vol=0.55),
        sfx("whoosh", src_t=E["hook_whip"] - 0.12, vol=0.55), sfx("pop", src_t=1.30, vol=0.4),
        sfx("digital-click", src_t=E["pips_in"], vol=0.6),
        sfx("whoosh", src_t=E["smoked_in"] - 0.1, vol=0.5),
        sfx("impact-bass-2", src_t=E["smoked_hit"], vol=0.9), sfx("glitch-1", src_t=E["smoked_hit"], vol=0.25, dur=0.6),
        sfx("red-line", src_t=E["light"] + 0.1, vol=0.35, dur=0.6),
        sfx("pop", src_t=E["gcard_in"], vol=0.45), sfx("glitch-1", src_t=E["blurry"], vol=0.22, dur=0.5),
        sfx("ping", src_t=E["google"], vol=0.3),
        sfx("whoosh", src_t=E["text_in"] - 0.1, vol=0.45), sfx("typing", src_t=E["text_in"] + 0.1, vol=0.35, dur=0.9),
        sfx("pop", src_t=E["chat_in"] + 0.1, vol=0.55), sfx("notification", src_t=E["read"], vol=0.3, dur=1.2),
        sfx("error", src_t=E["read"] + 0.5, vol=0.25, dur=0.9),
        sfx("pop", src_t=E["receipt_in"], vol=0.45), sfx("digital-click", src_t=E["paid"], vol=0.6),
        sfx("whoosh", src_t=E["burpee_in"] - 0.1, vol=0.5), sfx("whoosh-short", src_t=E["burpee_cut"] - 0.05, vol=0.45),
        sfx("pop", src_t=E["graph_in"], vol=0.45), sfx("red-line", src_t=E["graph_q"], vol=0.45, dur=0.8),
        sfx("whoosh", src_t=E["tired_in"] - 0.1, vol=0.45),
        sfx("riser", out_t=T["stance"] - 2.4, vol=0.4, dur=2.4, media_start=7.6),
        sfx("impact-bass-1", src_t=E["stance"], vol=1.0), sfx("hit-stance", src_t=E["stance"], vol=0.6),
        sfx("whoosh-short", src_t=E["lockup"] - 0.08, vol=0.45),
        sfx("pop", src_t=E["cta"], vol=0.45), sfx("typing", src_t=E["cta_type"], vol=0.35, dur=0.7),
        sfx("notification", src_t=E["early"], vol=0.35, dur=1.0),
        sfx("whoosh-short", out_t=TOTAL - 0.3, vol=0.4),
    ]
    for i in range(1, 6):
        s.append(sfx("hit-stance", src_t=E[f"n{i}"], vol=0.6))
        s.append(sfx("digital-click", src_t=E[f"n{i}"] + 0.12, vol=0.45))
    s.append(sfx("whoosh", src_t=11.0, vol=0.45))
    for i in range(1, 6):
        s.append(sfx("whoosh-short", out_t=out(E[f"n{i}"]) - 0.34, vol=0.5))
    for k in ("f1", "f2", "f3", "f4"):
        s.append(sfx("click", src_t=E[k], vol=0.5))
    for i in range(5):
        s.append(sfx("click", out_t=T["chips"] + 0.18 * i, vol=0.35))
    return sorted(s, key=lambda x: x["t"])


def sfx_dur(name):
    p = A("assets", "sfx", name + ".mp3")
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p],
                       capture_output=True, text=True)
    return float(r.stdout.strip())


# ---------------------------------------------------------------- html
def html_videos():
    v = []
    for i, (a, b) in enumerate(SEGMENTS):
        v.append(f'<video id="th-{i}" class="clip th" src="assets/talking.mp4" data-start="{_starts[i]:.4f}" '
                 f'data-duration="{b - a:.4f}" data-media-start="{a:.3f}" data-track-index="0" '
                 f'playsinline data-has-audio="true"></video>')
    return "\n        ".join(v)


def html_broll(clips):
    v = []
    for c in clips:
        v.append(f'<div class="brw" id="w-{c["id"]}"><video id="{c["id"]}" class="clip br" src="assets/cut/{c["id"]}.mp4" '
                 f'data-start="{c["start"]:.3f}" data-duration="{c["dur"]:.3f}" data-track-index="1" muted playsinline></video></div>')
    return "\n      ".join(v)


def html_audio(sfx_list):
    lines = []
    mus1_end = T["metoo"] + 0.15
    lines.append(f'<audio id="bgm-1" src="assets/music/mk318.mp3" data-start="0" data-duration="{mus1_end:.3f}" '
                 f'data-media-start="20.15" data-track-index="20" data-volume="1" '
                 f'data-automation=\'{{"version":1,"lanes":[{{"target":"volume","points":[{{"t":0,"v":0.34}},{{"t":{mus1_end - 0.35:.3f},"v":0.34}},{{"t":{mus1_end:.3f},"v":0}}]}}]}}\'></audio>')
    d2 = round(TOTAL - T["stance"], 3)
    lines.append(f'<audio id="bgm-2" src="assets/music/mk318.mp3" data-start="{T["stance"]:.3f}" data-duration="{d2:.3f}" '
                 f'data-media-start="20.15" data-track-index="21" data-volume="1" '
                 f'data-automation=\'{{"version":1,"lanes":[{{"target":"volume","points":[{{"t":0,"v":0.34}},{{"t":{d2 - 0.4:.3f},"v":0.34}},{{"t":{d2:.3f},"v":0.22}}]}}]}}\'></audio>')
    for i, s in enumerate(sfx_list):
        full = sfx_dur(s["name"]) - s["ms"]
        dur = min(s["dur"] or full, full, TOTAL - s["t"])
        if dur <= 0.05:
            continue
        lines.append(f'<audio id="sfx-{i}" src="assets/sfx/{s["name"]}.mp3" data-start="{s["t"]:.3f}" '
                     f'data-duration="{dur:.3f}" data-media-start="{s["ms"]:.3f}" data-track-index="{30 + i}" '
                     f'data-volume="{s["vol"]}"></audio>')
    return "\n    ".join(lines)


def html_captions(caps):
    out_html = []
    for i, c in enumerate(caps):
        ws = "".join(f'<span class="w" id="cw-{i}-{j}">{w["t"]}</span>' for j, w in enumerate(c["words"]))
        cls = "cap big" if c["big"] else "cap"
        out_html.append(f'<div class="{cls} clip" id="cap-{i}" data-start="{c["start"]:.3f}" '
                        f'data-duration="{c["end"] - c["start"]:.3f}" data-track-index="9"><div class="cap-in">{ws}</div></div>')
    return "\n    ".join(out_html)


def window(a, b):
    return f'data-start="{a:.3f}" data-duration="{max(0.05, b - a):.3f}"'


def main():
    clips = build_broll()
    caps = build_captions()
    sfx_list = build_sfx()
    tpl = open(A("work", "template.html"), encoding="utf-8").read()
    W = {
        "TOTAL": f"{TOTAL:.3f}",
        "VIDEOS": html_videos(),
        "BROLL": html_broll(clips),
        "AUDIO": html_audio(sfx_list),
        "CAPTIONS": html_captions(caps),
        "BADGES": "\n            ".join(
            f'<div id="bdg-{i + 1}" class="badge clip" {window(s, e)} data-track-index="2">'
            f'<div class="badge-in"><span>0{i + 1}</span></div></div>' for i, (s, e) in enumerate(T["badges"])),
        "T_JSON": json.dumps(T),
        "BROLL_JSON": json.dumps(clips),
        "CAPS_JSON": json.dumps(caps),
        "W_HOOK": window(0, T["n1"]),
        "W_PIPS": window(T["pips_in"], T["n5_off"]),
        "W_S1": window(T["n1"], T["n2"]),
        "W_GCARD": window(T["gcard_in"], T["n3"]),
        "W_CHAT": window(T["text_in"], T["n4"]),
        "W_RECEIPT": window(T["receipt_in"], T["n5"]),
        "W_BURPEE": window(T["burpee_in"], T["n5"]),
        "W_GRAPH": window(T["graph_in"], T["metoo"]),
        "W_METOO": window(T["metoo"], T["stance"]),
        "W_STANCE": window(T["stance"] - 0.12, T["lockup"]),
        "W_LOCKUP": window(T["lockup"], T["cta"]),
        "W_CTA": window(T["cta"], T["chips"]),
        "W_CHIPS": window(T["chips"], TOTAL),
        "W_FLASH": window(0, TOTAL),
    }
    html = re.sub(r"@@(\w+)@@", lambda m: W[m.group(1)], tpl)
    open(A("index.html"), "w", encoding="utf-8").write(html)
    print(f"index.html written: {TOTAL:.2f}s, {len(caps)} caption groups, {len(sfx_list)} sfx, {len(clips)} b-roll")
    # Carve the music beds around the voice (hyperframes-audio). Rerun after every build.
    carve = os.path.expanduser("~/.claude/skills/hyperframes-audio/scripts/carve.mjs")
    voices = [a for i in range(len(SEGMENTS)) for a in ("--voice", f"th-{i}")]
    for bed in ("bgm-1", "bgm-2"):
        subprocess.run(["node", carve, "--comp", A("index.html"), "--bed", bed, *voices],
                       check=True, capture_output=True, shell=False)
    print("music carved under voice")
    print("T:", {k: v for k, v in T.items() if not isinstance(v, list)})


if __name__ == "__main__":
    main()
