"""Build "Some people train for fun" (THEM vs YOU scorecard reel).

Authored in SOURCE time (Whisper timestamps of raw/IMG_7186.MOV). Cuts come from
work/cuts.json (reel-kit/scripts/cutlist.py); out() maps source -> output time.

  python -P build.py      -> b-roll prep (assets/cut), index.html, music carve
"""
import json
import os
import re
import subprocess

ROOT = os.path.dirname(os.path.abspath(__file__))
A = lambda *p: os.path.join(ROOT, *p)
FPS = 30

SEGMENTS = [tuple(s) for s in json.load(open(A("work", "cuts.json")))["segments"]]
_starts, _acc = [], 0.0
for a, b in SEGMENTS:
    _starts.append(_acc)
    _acc += b - a
TOTAL = round(_acc, 4)


def out(src):
    for (a, b), o in zip(SEGMENTS, _starts):
        if src < a:
            return round(o, 3)
        if src <= b:
            return round(o + src - a, 3)
    return TOTAL


# ---------------------------------------------------------------- events (source seconds)
E = dict(
    fun=1.02, you0=2.38, coming=3.46, spot=4.04,
    they1=5.24, rains=6.60, you1=7.34,
    they2=11.52, reps=12.36, you2=12.98, fight=14.26,
    they3=18.70, story=20.64, you3=22.42, lights=23.88, off=24.28,
    they4=29.56, dropped=30.34, disappear=31.58, week=32.54, you4=33.10, partner=35.42,
    they5=39.58, motivation=40.32, you5=41.40, schedule=42.02, verdict=42.25,
    problem=49.88, nobody=51.80, stance=54.54,
    r1=56.24, r2=57.30, r3=58.30, r4=59.96,
    cta=64.73, cta_type=65.02, waitlist=66.82,
    send=75.14, partner2=76.72, knows=77.40,
)
T = {k: out(v) for k, v in E.items()}
T["total"] = TOTAL
# punch-in per segment: alternate, harder on YOU lines
YOU_KEYS = ("you0", "you1", "you2", "you3", "you4", "you5")
seg_scale = []
for i, (a, b) in enumerate(SEGMENTS):
    you = any(a - 0.1 <= E[k] <= b for k in YOU_KEYS)
    base = 1.12 if you else (1.0 if i % 2 == 0 else 1.06)
    seg_scale.append([round(_starts[i], 4), round(_starts[i] + b - a, 4), base, round(base + 0.035, 3)])
T["seg"] = seg_scale
# THEM / YOU phases for the grade + scorecard
T["phases"] = [[T["they1"], "them"], [T["you1"], "you"], [T["they2"], "them"], [T["you2"], "you"],
               [T["they3"], "them"], [T["you3"], "you"], [T["they4"], "them"], [T["you4"], "you"],
               [T["they5"], "them"], [T["you5"], "you"], [T["verdict"] + 0.4, "end"]]

# ---------------------------------------------------------------- b-roll
# id, file, clip-in, src start, src end, grade
COOL_RAIN = ("eq=contrast=1.15:saturation=0.75:brightness=-0.14:gamma=0.9,"
             "colorbalance=rs=-0.04:bs=0.06:rm=-0.03:bm=0.05,vignette=PI/3.5")
WARM = ("eq=contrast=1.08:saturation=0.92:brightness=-0.03,"
        "colorbalance=rm=0.03:bm=-0.03:rs=0.01:bs=-0.02,vignette=PI/4.5")
BROLL = [
    ("b-rain", "mk2846", 3.0, E["they1"] - 0.05, E["you1"], WARM, "crop=608:1080:656:0,scale=1080:1920"),
    ("b-run", "mk32809", 5.4, E["you1"], 8.633, COOL_RAIN, None),
    ("b-punch", "mk40971", 2.70, E["coming"], 4.40, WARM, None),
    ("b-bag", "mk40276", 1.0, E["you3"] + 0.25, 24.833, WARM, None),
    ("b-drop", "mk40974", 4.70, E["dropped"], E["disappear"] - 0.1, WARM, None),
    ("b-spar", "mk40970", 0.80, E["partner"] - 0.35, 35.967, WARM, None),
    ("b-feat1", "mk40276", 4.5, E["r1"] - 0.15, E["r3"], WARM, None),
    ("b-feat2", "mk41001", 2.0, E["r3"], 62.267, WARM, None),
    ("b-phone", "mk41173", 8.0, E["cta"], 67.933, WARM, None),
]


def build_broll():
    os.makedirs(A("assets", "cut"), exist_ok=True)
    clips = []
    for cid, src, cin, s_in, s_out, grade, pre in BROLL:
        o_in, o_out = out(s_in), out(s_out)
        dur = round(o_out - o_in, 3)
        dst = A("assets", "cut", f"{cid}.mp4")
        if not os.path.exists(dst):
            vf = (pre + "," if pre else "") + grade + ",scale=1080:1920,fps=30,format=yuv420p"
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(cin), "-t", str(dur + 0.2),
                            "-i", A("assets", "broll", src + ".mp4"), "-an", "-vf", vf,
                            "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-g", "15", dst], check=True)
        clips.append(dict(id=cid, start=o_in, dur=dur, end=o_out))
    return clips


# ---------------------------------------------------------------- captions
FIX = {"stands": "Stance", "and_sparring": "in"}
EMPHASIS = {"spot", "off", "schedule", "stance"}
NO_CAPTION = [(0.0, out(5.20)), (out(54.40), out(62.30))]  # logo + feature rows carry these words


def load_words():
    words = json.load(open(A("work", "words.json"), encoding="utf-8"))
    res = []
    for i, w in enumerate(words):
        t = w["text"].strip()
        bare = re.sub(r"[^\w']", "", t).lower()
        if bare == "stands":
            t = "Stance."
        if bare == "and" and i > 0 and words[i - 1]["text"].lower().startswith("dropped"):
            t = "in"
        res.append(dict(text=t, start=w["start"], end=w["end"]))
    return res


def kept(t):
    return any(a - 0.02 <= t <= b for a, b in SEGMENTS)


def build_captions():
    words = [w for w in load_words() if kept(w["start"] + 0.03)]
    groups, cur = [], []

    def flush():
        if cur:
            groups.append(list(cur))
            cur.clear()

    seg = lambda t: next((i for i, (a, b) in enumerate(SEGMENTS) if a - 0.05 <= t <= b + 0.05), -1)
    for w in words:
        bare = re.sub(r"[^\w']", "", w["text"]).lower()
        if bare in EMPHASIS:
            flush(); cur.append(w); flush()
            continue
        if cur:
            prev = cur[-1]
            chars = sum(len(x["text"]) + 1 for x in cur) + len(w["text"])
            if (len(cur) >= 3 or chars > 15 or seg(prev["start"]) != seg(w["start"])
                    or re.search(r"[.,?!]$", prev["text"]) or bare in ("they", "you", "you're", "you've")):
                flush()
        cur.append(w)
    flush()
    caps = []
    for gi, g in enumerate(groups):
        s = out(g[0]["start"])
        nxt = out(groups[gi + 1][0]["start"]) if gi + 1 < len(groups) else TOTAL
        e = min(nxt, out(g[-1]["end"]) + 0.35, TOTAL)
        if any(a - 0.05 <= s < b for a, b in NO_CAPTION) or e - s < 0.12:
            continue
        big = len(g) == 1 and re.sub(r"[^\w']", "", g[0]["text"]).lower() in EMPHASIS
        ws = []
        for x in g:
            t = re.sub(r"[.,?!]", "", x["text"]).upper()
            kind = "them" if t == "THEY" else ("you" if t in ("YOU", "YOU'RE", "YOU'VE") else "")
            ws.append(dict(t=t, s=max(s, out(x["start"])), e=out(x["end"]), k=kind))
        caps.append(dict(start=s, end=round(e, 3), big=big, words=ws))
    return caps


# ---------------------------------------------------------------- audio
def sfx(name, src_t=None, out_t=None, vol=0.6, dur=None, ms=0.0):
    t = out_t if out_t is not None else out(src_t)
    return dict(name=name, t=round(max(0.0, t), 3), vol=vol, dur=dur, ms=ms)


def build_sfx():
    s = [
        sfx("glitch-1", out_t=0.0, vol=0.3, dur=0.5), sfx("impact-bass-1", src_t=E["you0"], vol=0.9),
        sfx("hit-stance", src_t=E["you0"], vol=0.5), sfx("whoosh", src_t=E["coming"] - 0.1, vol=0.5),
        sfx("hit-stance", src_t=E["spot"], vol=0.6),
        sfx("glitch-1", src_t=E["they1"], vol=0.2, dur=0.4), sfx("whoosh", src_t=E["you1"] - 0.1, vol=0.5),
        sfx("glitch-1", src_t=E["they2"], vol=0.2, dur=0.4), sfx("key-press", src_t=E["reps"], vol=0.4),
        sfx("digital-click", src_t=E["fight"], vol=0.5),
        sfx("glitch-1", src_t=E["they3"], vol=0.2, dur=0.4), sfx("click-soft", src_t=E["story"], vol=0.5),
        sfx("whoosh", src_t=E["you3"] + 0.15, vol=0.5), sfx("click", src_t=E["off"], vol=0.9),
        sfx("impact-bass-2", src_t=E["off"], vol=0.6),
        sfx("glitch-1", src_t=E["they4"], vol=0.2, dur=0.4), sfx("impact-bass-2", src_t=E["dropped"] + 0.15, vol=0.8),
        sfx("error", src_t=E["week"], vol=0.25, dur=0.8), sfx("pop", src_t=E["you4"] + 0.4, vol=0.45),
        sfx("whoosh-short", src_t=E["partner"] - 0.4, vol=0.45),
        sfx("glitch-1", src_t=E["they5"], vol=0.2, dur=0.4), sfx("pop", src_t=E["motivation"], vol=0.4),
        sfx("digital-click", src_t=E["schedule"], vol=0.5), sfx("impact-bass-1", src_t=E["verdict"] + 0.4, vol=0.7),
        sfx("pop", src_t=E["problem"], vol=0.4),
        sfx("riser", out_t=T["stance"] - 2.2, vol=0.38, dur=2.2, ms=7.8),
        sfx("impact-bass-1", src_t=E["stance"], vol=1.0), sfx("hit-stance", src_t=E["stance"], vol=0.6),
        sfx("pop", src_t=E["cta"], vol=0.45), sfx("typing", src_t=E["cta_type"], vol=0.35, dur=0.6),
        sfx("notification", src_t=E["waitlist"], vol=0.35, dur=1.0),
        sfx("whoosh-short", src_t=E["send"] - 0.1, vol=0.4), sfx("click", src_t=E["partner2"], vol=0.5),
        sfx("whoosh", out_t=TOTAL - 0.28, vol=0.45),
    ]
    for k in YOU_KEYS[1:]:
        s.append(sfx("hit-stance", src_t=E[k], vol=0.45))
    for k in ("r1", "r2", "r3", "r4"):
        s.append(sfx("click", src_t=E[k], vol=0.5))
    return sorted(s, key=lambda x: x["t"])


def sfx_dur(name):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                        A("assets", "sfx", name + ".mp3")], capture_output=True, text=True)
    return float(r.stdout.strip())


MUSIC = "assets/music/mk357.mp3"
DROP = 29.18  # big drop in the bed


def html_audio(sfx_list):
    lines = []
    ms1 = round(DROP - T["you0"], 3)            # drop lands on "You train..."
    end1 = T["problem"] + 0.2
    lines.append(f'<audio id="bgm-1" src="{MUSIC}" data-start="0" data-duration="{end1:.3f}" data-media-start="{ms1}" '
                 f'data-track-index="20" data-volume="1" data-automation=\'{{"version":1,"lanes":[{{"target":"volume","points":'
                 f'[{{"t":0,"v":0.3}},{{"t":{end1 - 0.5:.3f},"v":0.3}},{{"t":{end1:.3f},"v":0.0}}]}}]}}\'></audio>')
    d2 = round(TOTAL - T["stance"], 3)
    lines.append(f'<audio id="bgm-2" src="{MUSIC}" data-start="{T["stance"]:.3f}" data-duration="{d2:.3f}" data-media-start="{DROP}" '
                 f'data-track-index="21" data-volume="1" data-automation=\'{{"version":1,"lanes":[{{"target":"volume","points":'
                 f'[{{"t":0,"v":0.3}},{{"t":{d2 - 0.4:.3f},"v":0.3}},{{"t":{d2:.3f},"v":0.2}}]}}]}}\'></audio>')
    for i, s in enumerate(sfx_list):
        full = sfx_dur(s["name"]) - s["ms"]
        dur = min(s["dur"] or full, full, TOTAL - s["t"])
        if dur > 0.05:
            lines.append(f'<audio id="sfx-{i}" src="assets/sfx/{s["name"]}.mp3" data-start="{s["t"]:.3f}" data-duration="{dur:.3f}" '
                         f'data-media-start="{s["ms"]:.3f}" data-track-index="{30 + i}" data-volume="{s["vol"]}"></audio>')
    return "\n    ".join(lines)


# ---------------------------------------------------------------- html
def window(a, b):
    return f'data-start="{a:.3f}" data-duration="{max(0.05, b - a):.3f}"'


def main():
    clips = build_broll()
    caps = build_captions()
    sfx_list = build_sfx()
    vids = "\n          ".join(
        f'<video id="th-{i}" class="clip th" src="assets/talking.mp4" data-start="{_starts[i]:.4f}" data-duration="{b - a:.4f}" '
        f'data-media-start="{a:.4f}" data-track-index="0" playsinline data-has-audio="true"></video>'
        for i, (a, b) in enumerate(SEGMENTS))
    broll = "\n        ".join(
        f'<div class="brw" id="w-{c["id"]}"><video id="{c["id"]}" class="clip br" src="assets/cut/{c["id"]}.mp4" '
        f'data-start="{c["start"]:.3f}" data-duration="{c["dur"]:.3f}" data-track-index="1" muted playsinline></video></div>'
        for c in clips)
    capshtml = "\n    ".join(
        f'<div class="cap{" big" if c["big"] else ""} clip" id="cap-{i}" {window(c["start"], c["end"])} data-track-index="9">'
        f'<div class="cap-in">' + "".join(f'<span class="w {w["k"]}" id="cw-{i}-{j}">{w["t"]}</span>' for j, w in enumerate(c["words"]))
        + '</div></div>' for i, c in enumerate(caps))
    W = {
        "TOTAL": f"{TOTAL:.4f}", "VIDEOS": vids, "BROLL": broll, "AUDIO": html_audio(sfx_list), "CAPTIONS": capshtml,
        "T_JSON": json.dumps(T), "BROLL_JSON": json.dumps(clips), "CAPS_JSON": json.dumps(caps),
        "W_ALL": window(0, TOTAL),
        "W_HOOK": window(0, T["they1"]),
        "W_SCORE": window(T["they1"], T["problem"]),
        "W_P1": window(T["they1"], T["they2"]), "W_P2": window(T["they2"], T["they3"]),
        "W_P3": window(T["they3"], T["you3"] + 0.05), "W_P3B": window(T["you3"], T["they4"]),
        "W_P4": window(T["they4"], T["they5"]), "W_P5": window(T["they5"], T["problem"]),
        "W_RAIN": window(T["you1"], out(8.633)),
        "W_PROB": window(T["problem"], T["stance"]),
        "W_STANCE": window(T["stance"] - 0.1, T["cta"]),
        "W_CTA": window(T["cta"], T["send"] - 0.25),
        "W_SHARE": window(T["send"] - 0.25, TOTAL),
    }
    tpl = open(A("work", "template.html"), encoding="utf-8").read()
    open(A("index.html"), "w", encoding="utf-8").write(re.sub(r"@@(\w+)@@", lambda m: W[m.group(1)], tpl))
    print(f"index.html: {TOTAL:.2f}s, {len(caps)} captions, {len(sfx_list)} sfx, {len(clips)} b-roll")
    carve = os.path.expanduser("~/.claude/skills/hyperframes-audio/scripts/carve.mjs")
    voices = [x for i in range(len(SEGMENTS)) for x in ("--voice", f"th-{i}")]
    for bed in ("bgm-1", "bgm-2"):
        subprocess.run(["node", carve, "--comp", A("index.html"), "--bed", bed, *voices], check=True, capture_output=True)
    print("music carved under voice")


if __name__ == "__main__":
    main()
