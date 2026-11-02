"""Build editorial-style (Modal) plan reels from one-take recordings: python3 -P tools/planreel/editorial.py P0 [P3 L1 L2]

For each reel code in REELS: makes production/reels/2026-11-02-plan-<code>/ from the editorial template (build.py,
make.sh, work/template.html, gsap, package.json), with
  work/words.json   the transcript re-written to the SCRIPT (names and words spelled as written; words Matteo said
                    that aren't in the script are kept as heard; script words he skipped are dropped)
  work/takes.json   one take per variant A-E (the last clean take of each letter), cut first word to last word
  work/broll_<V>.json  day cards (full-screen cutaways, captions hidden under them) + matched b-roll
and a tar (assets/raw.mp4 trimmed to the takes + assets/media/b_*.mp4) to push to the media release as
plan-<code>-assets.tar. Render: "Submit render" workflow, media "plan-<code>-assets.tar=media/plan/plan-<code>-assets.tar",
include "media/plan/plan-<code>-assets.tar".
"""
import difflib, json, re, shutil, subprocess, sys, tarfile
from pathlib import Path
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))
from compose import take_segment, card_png, norm  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
SCRATCH = Path("/tmp/claude-0/-home-user-matteofights/768d2191-c274-55b5-bdf2-1189e012dd9d/scratchpad")
TPL = ROOT / "production/reels/_TEMPLATE/editorial"
REF = ROOT / "production/reels/2026-10-20-freeze-editorial"
AN = ROOT / "content-bank/real-footage/analysis"
PLANS = {p["slug"]: p for p in json.loads((ROOT / "docs/plans/plans.json").read_text())["plans"]}

P_BODY, L_BODY = "Here's a three day plan. Day one. Day two. Day three.", "Here's the at-home version. Monday to Friday."
CTA = "Comment {k} and I'll send it to you so you can save it."
REELS = {
    "P0": dict(clips={"A": [("POWER", "kick1", "broll-kicking.mp4", 16.4, 1.6)], "B": [("LEGS", "kick2", "broll-kicking.mp4", 0.5, 1.8)],
               "C": [("LEGS", "kick2", "broll-kicking.mp4", 0.5, 1.8)], "D": [("TRAINING", "kick3", "broll-kicking.mp4", 19.5, 1.6)],
               "E": [("HARD", "kick1", "broll-kicking.mp4", 16.4, 1.6)]}, raw="P0.mp4", an="2026-11-02-plan-P0-power", plan="power-at-home", k="POWER", body=P_BODY, hooks={
        "A": ("Want more punching power but don't have a gym?", ["Want more punching power", "but don't have a"], "gym?", ("GYM", 1), ("HERE'S", 1)),
        "B": ("Most people train their arms for power. Your power comes from your legs.", ["Most people train their arms", "for power. Your power comes from your"], "legs.", ("LEGS", 1), ("HERE'S", 1)),
        "C": ("Most of your punching power comes from your legs and hips, not your arms.", ["Most of your punching power comes", "from your legs and hips, not your"], "arms.", ("ARMS", 1), ("HERE'S", 1)),
        "D": ("You're not weak. You're training power the wrong way.", ["You're not weak.", "You're training power the wrong"], "way.", ("WAY", 1), ("HERE'S", 1)),
        "E": ("If you train at home and still want to hit hard, this is for you.", ["If you train at home", "and still want to hit"], "hard.", ("HARD", 1), ("THIS", 1))}),
    # b-roll per variant: (spoken word token, clip name, release file, in, dur)
    "P3": dict(raw="P3.mp4", an="2026-11-02-plan-P3-cardio", plan="fight-cardio", k="CARDIO", body=P_BODY, hooks={
        "A": ("Do you gas out in round two?", ["Do you gas out", "in round"], "two?", ("TWO", 1), ("HERE'S", 1)),
        "B": ("You don't need more running. Fights aren't jogs, they're bursts.", ["You don't need more running.", "Fights aren't jogs, they're"], "bursts.", ("BURSTS", 1), ("HERE'S", 1)),
        "C": ("Runners pace. Fighters burst. Train like a fighter.", ["Runners pace.", "Fighters"], "burst.", ("BURST", 1), ("TRAIN", 1)),
        "D": ("20 minutes a day. That's enough to stop gassing out.", ["20 minutes a day.", "That's enough to stop gassing"], "out.", ("OUT", 1), ("HERE'S", 1)),
        "E": ("If you're dead by round two, this is for you.", ["If you're dead", "by round"], "two,", ("TWO", 1), ("THIS", 1))}),
    "L1": dict(raw="L1.mp4", an="2026-11-02-plan-L1-loma", plan="lomachenko-footwork", k="LOMA", body=L_BODY, hooks={
        "A": ("Lomachenko spent 4 years doing dance instead of boxing.", ["Lomachenko spent 4 years", "doing dance instead of"], "boxing.", ("BOXING", 1), ("HERE'S", 1)),
        "B": ("Ever wonder why Lomachenko's footwork looks like that?", ["Ever wonder why", "Lomachenko's footwork looks like"], "that?", ("THAT", 1), ("HERE'S", 1)),
        "C": ("Lomachenko's footwork isn't talent. It's years of drills nobody films.", ["Lomachenko's footwork isn't talent.", "It's years of drills nobody"], "films.", ("FILMS", 1), ("HERE'S", 1)),
        "D": ("Most people drill punches. Lomachenko drilled his feet.", ["Most people drill punches.", "Lomachenko drilled his"], "feet.", ("FEET", 1), ("HERE'S", 1)),
        "E": ("If your feet ever feel stuck when you shadowbox, this is for you.", ["If your feet ever feel", "stuck when you"], "shadowbox,", ("SHADOWBOX", 1), ("THIS", 1))}),
    "L2": dict(raw="L2.mp4", an="2026-11-02-plan-L2-tyson", plan="tyson-peekaboo", k="TYSON", body=L_BODY, hooks={
        "A": ("Want head movement like prime Tyson?", ["Want head movement", "like prime"], "Tyson?", ("TYSON", 1), ("HERE'S", 1)),
        "B": ("Steal this from Mike Tyson. Your head is never where they're aiming.", ["Steal this from Mike Tyson.", "Your head is never where they're"], "aiming.", ("AIMING", 1), ("HERE'S", 1)),
        "C": ("Most people block punches. Tyson made them miss.", ["Most people block punches.", "Tyson made them"], "miss.", ("MISS", 1), ("HERE'S", 1)),
        "D": ("Tyson's power started with his head movement, not his arms.", ["Tyson's power started with", "his head movement, not his"], "arms.", ("ARMS", 1), ("HERE'S", 1)),
        "E": ("There's a reason Tyson's opponents kept hitting air.", ["There's a reason Tyson's", "opponents kept hitting"], "air.", ("AIR", 1), ("HERE'S", 1))}),
}


def script_words(seg, script):
    """Re-spell a take's transcript to the script, keeping Whisper's timings."""
    toks = script.split()
    a, b = [norm(w["w"]) for w in seg], [norm(t) for t in toks]
    out = []
    for op, i0, i1, j0, j1 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
        if op == "equal":
            out += [{"text": toks[j0 + k], "start": seg[i0 + k]["s"], "end": seg[i0 + k]["e"]} for k in range(i1 - i0)]
        elif op == "replace":
            s, e = seg[i0]["s"], seg[i1 - 1]["e"]
            n = j1 - j0
            out += [{"text": toks[j0 + k], "start": s + (e - s) * k / n, "end": s + (e - s) * (k + 1) / n} for k in range(n)]
        elif op == "delete":  # said but not in the script: keep as heard
            out += [{"text": seg[k]["w"], "start": seg[k]["s"], "end": seg[k]["e"]} for k in range(i0, i1)]
    return out


def full_card(day, keyword, path_mp4, tmp):
    card = tmp / "card.png"
    card_png(day, keyword, card)
    c = Image.open(card)
    scale = 1.0
    bg = Image.new("RGB", (1080, 1920), (11, 11, 13))
    d = ImageDraw.Draw(bg)
    d.rectangle([0, 0, 1080, 1920], fill=(11, 11, 13))
    bg.paste(c.resize((int(c.width * scale), int(c.height * scale))), ((1080 - c.width) // 2, (1920 - c.height) // 2), c)
    png = tmp / "full.png"
    bg.save(png)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-loop", "1", "-i", str(png), "-t", "2.2", "-r", "30", "-c:v", "libx264",
                    "-pix_fmt", "yuv420p", "-crf", "16", str(path_mp4)], check=True)


def build(code):
    R = REELS[code]
    slug = f"2026-11-02-plan-{code}"
    out = ROOT / "production/reels" / slug
    (out / "work").mkdir(parents=True, exist_ok=True)
    for f in ["make.sh", "work/template.html"]:
        shutil.copy(TPL / f, out / f)
    for f in ["package.json", "hyperframes.json"]:
        shutil.copy(REF / f, out / f)
    (out / "assets/lib").mkdir(parents=True, exist_ok=True)
    shutil.copy(REF / "assets/lib/gsap.min.js", out / "assets/lib/gsap.min.js")

    raw_words = json.loads((AN / R["an"] / "words.json").read_text())
    segs = {v: take_segment(raw_words, v) for v in "ABCDE"}
    t_lo = min(raw_words[i0]["s"] for i0, _ in segs.values()) - 0.6
    t_hi = max(raw_words[i1]["e"] for _, i1 in segs.values()) + 0.6
    words, takes, variants, hooks, clips = [], {}, {}, {}, {}
    plan = PLANS[R["plan"]]
    for v, (i0, i1) in segs.items():
        hook, lead, word, on, until = R["hooks"][v]
        script = f"{hook} {R['body']} {CTA.format(k=R['k'].capitalize())}"
        sw = script_words(raw_words[i0:i1 + 1], script)
        for w in sw:
            w["start"] -= t_lo
            w["end"] -= t_lo
        words += sw
        s0, e0 = sw[0]["start"] - 0.06, sw[-1]["end"] + 0.12
        takes[v] = [round(s0, 3), round(e0, 3)]
        variants[v] = [v]
        hooks[v] = {"lead": lead, "word": word, "on": on, "until": until}
        # day cards: from "here's" (or the day/monday word) to "comment", in variant time
        up = lambda w: "".join(ch for ch in w["text"].upper() if ch.isalnum() or ch == "'").strip("'")  # noqa: E731
        hs = next(w["start"] for w in sw if up(w) in ("DAY", "MONDAY"))
        cs = next(w["start"] for w in sw if up(w) == "COMMENT")
        n = len(plan["days"])
        step = (cs - hs + 0.25) / n
        broll = {f"day{k + 1}": {"start": round(hs - s0 - 0.1 + k * step, 3), "dur": round(step, 3)} for k in range(n)}
        for tok, name, src, cin, cdur in R.get("clips", {}).get(v, []):
            t = next(w["start"] for w in sw if up(w) == tok)
            broll[name] = {"start": round(t - s0, 3), "dur": cdur}
            clips[name] = {"name": name, "src": f"../../../media/plan/{src}", "in": cin, "dur": cdur}
        (out / f"work/broll_{v}.json").write_text(json.dumps(broll, indent=1))
    (out / "work/assets.json").write_text(json.dumps({"raw": f"../../../media/plan/{R['an']}.mp4", "t_lo": round(t_lo, 3),
        "t_hi": round(t_hi, 3), "plan": R["plan"], "keyword": R["k"], "plans": "../../../docs/plans/plans.json", "clips": list(clips.values())}, indent=1))
    (out / "work/words.json").write_text(json.dumps(words))
    (out / "work/takes.json").write_text(json.dumps({"src": "assets/raw.mp4", "words": "work/words.json", "speed": 1.0,
                                                     "takes": takes, "variants": variants, "fix": {}}, indent=1))
    # build.py: template with REEL filled, per-variant broll, captions hidden under day cards
    b = (TPL / "build.py").read_text()
    reel = {"hooks": hooks, "keys": [R["k"], "COMMENT"], "fx": {}, "cards": [], "slam": [], "bed": None}
    b = re.sub(r"REEL = \{.*?\n\}\n", "REEL = " + repr(reel) + "\n", b, flags=re.S)
    b = b.replace('broll = json.load(open("work/broll.json", encoding="utf-8")) if os.path.exists("work/broll.json") else {}',
                  'broll = json.load(open(f"work/broll_{V}.json", encoding="utf-8")) if os.path.exists(f"work/broll_{V}.json") else {}')
    b = b.replace("hide=[(0, title_end)]", "hide=[(0, title_end)] + [(c['start'], c['start'] + c['dur']) for n, c in broll.items() if n.startswith('day')]")
    (out / "build.py").write_text(b)
    m = (out / "make.sh").read_text().replace('V="${1:-A}"', 'V="${1:-A}"\n[ -f assets/raw.mp4 ] || { "$(command -v python3)" -m pip install -q pillow; python3 ../../../tools/planreel/assets.py work/assets.json; }')
    (out / "make.sh").write_text(m)
    print(f"{code}: {out.relative_to(ROOT)} takes {takes}")

if __name__ == "__main__":
    for c in sys.argv[1:]:
        build(c)
