"""Plan reel composer: one continuous talking-head take + word captions + day cards + matched b-roll, via ffmpeg.

    python3 -P tools/planreel/compose.py SPEC.json VARIANT OUT.mp4

SPEC (one per reel, e.g. production/reels/2026-11-02-plan-reels/P0.json):
  footage    local path of Matteo's recording (all takes, spoken labels "POWER, TAKE A")
  words      words.json from Fetch video (content-bank/real-footage/analysis/<slug>/words.json)
  plan       slug in docs/plans/plans.json (day cards come from there)
  keyword    the comment word, e.g. "POWER"
  title      small top line, e.g. "3-DAY HOME POWER PLAN"
  broll      [{"match": "legs", "clip": path, "in": 12.3, "dur": 2.0, "mode": "full"|"top"}], placed at the
             first spoken word matching `match` (regex) inside the take. Pictures must show exactly what is said.

The take is cut first word to last word (the latest clean take of that letter), never trimmed inside, so it loops.
Cards flash from "Here's" to "Comment"; on days with 3+ items the last one is blurred with a "comment WORD" tag.
"""
import json, re, subprocess, sys, tempfile
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[2]
FONT = ROOT / "tools/listicle/fonts"
BEBAS, INTER = str(FONT / "BebasNeue-Regular.ttf"), str(FONT / "Inter-Bold.otf")
LUT = ROOT / "content-bank/luts/matteofights-v1.cube"
W, H = 1080, 1920
RED, GOLD, BG = (200, 32, 32), (196, 144, 64), (11, 11, 13)
norm = lambda w: re.sub(r"[^a-z0-9]", "", w.lower())


def take_segment(words, letter):
    """(i0, i1) word indexes of the last complete take for this letter: after 'take X', through '... save it'."""
    found = []
    for i in range(len(words) - 1):
        if norm(words[i]["w"]) == "take" and norm(words[i + 1]["w"])[:1] == letter.lower() and len(norm(words[i + 1]["w"])) <= 3:
            start = i + 2
            # take ends at the "it" after the last "save" before the next "take"
            nxt = next((j for j in range(start, len(words) - 1) if norm(words[j]["w"]) == "take"
                        and len(norm(words[j + 1]["w"])) <= 3), len(words))
            ends = [j for j in range(start, nxt) if norm(words[j]["w"]) == "it" and j > 0 and norm(words[j - 1]["w"]) == "save"]
            if ends:
                found.append((start, ends[-1]))
    if not found:
        sys.exit(f"no complete take {letter}")
    return found[-1]


def card_png(day, keyword, path):
    f_head, f_item, f_dose = ImageFont.truetype(BEBAS, 92), ImageFont.truetype(INTER, 40), ImageFont.truetype(INTER, 38)
    items = day["items"]
    h = 170 + 96 * len(items) + 40
    img = Image.new("RGBA", (980, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, 979, h - 1], 36, fill=BG + (238,), outline=(42, 42, 48, 255), width=3)
    d.rectangle([0, 0, 14, h], fill=RED + (255,))
    d.text((60, 44), day["d"].upper(), font=f_head, fill=(240, 240, 240, 255))
    y = 170
    lock = len(items) >= 3
    for k, (name, dose, *_ ) in enumerate(items):
        row = Image.new("RGBA", (900, 90), (0, 0, 0, 0))
        rd = ImageDraw.Draw(row)
        nm = name if len(name) <= 30 else name[:29] + "…"
        rd.text((0, 18), nm, font=f_item, fill=(232, 232, 232, 255))
        tw = rd.textlength(dose, font=f_dose)
        rd.text((900 - tw, 20), dose, font=f_dose, fill=GOLD + (255,))
        if lock and k == len(items) - 1:
            row = row.filter(ImageFilter.GaussianBlur(14))
            img.alpha_composite(row, (60, y))
            tag = f"🔒 comment {keyword}".replace("🔒 ", "")
            tf = ImageFont.truetype(INTER, 36)
            tl = d.textlength(tag, font=tf)
            x0 = (980 - tl) / 2 - 30
            d.rounded_rectangle([x0, y + 10, x0 + tl + 60, y + 78], 34, fill=RED + (255,))
            d.text((x0 + 30, y + 22), tag, font=tf, fill=(255, 255, 255, 255))
        else:
            img.alpha_composite(row, (60, y))
        y += 96
    img.save(path)


def apply_fixes(seg, fixes):
    """Fix misheard words for the captions: [[["loma","chenco"], ["Lomachenko"]], ...] (first match of each)."""
    seg = [dict(w) for w in seg]
    for src, dst in [[["common"], ["comment"]]] + fixes:
        n = len(src)
        for i in range(len(seg) - n + 1):
            if [norm(w["w"]) for w in seg[i:i + n]] == [norm(x) for x in src]:
                s, e = seg[i]["s"], seg[i + n - 1]["e"]
                step = (e - s) / len(dst)
                tail = seg[i + n - 1]["w"][-1] if seg[i + n - 1]["w"][-1] in ".,?!" else ""
                new = [{"w": d + (tail if k == len(dst) - 1 else ""), "s": s + k * step, "e": s + (k + 1) * step}
                       for k, d in enumerate(dst)]
                seg[i:i + n] = new
                break
    return seg


def ass_time(t):
    t = max(t, 0)
    return f"{int(t // 3600)}:{int(t % 3600 // 60):02d}:{t % 60:05.2f}"


def captions_ass(words, t0, hide, title, keyword, path):
    """Word-group captions (3 words max, keyword in red), hidden while cards show; small title on top."""
    hdr = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,Bebas Neue,118,&H00FFFFFF,&H00FFFFFF,&H00000000,&H64000000,0,0,0,0,100,100,1,0,1,6,0,2,60,60,560,1
Style: Top,Bebas Neue,64,&H00E8E8E8,&H00E8E8E8,&H00000000,&H00000000,0,0,0,0,100,100,4,0,1,3,0,8,60,60,150,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    ev, group = [], []
    end_all = words[-1]["e"] - t0 + 0.3

    def flush():
        if not group:
            return
        s, e = group[0]["s"] - t0, group[-1]["e"] - t0
        if any(a < e and s < b for a, b in hide):
            group.clear()
            return
        txt = " ".join(("{\\c&H2020C8&}" + w["w"].upper() + "{\\c&HFFFFFF&}") if norm(w["w"]) in (norm(keyword), "common")
                       else w["w"].upper() for w in group)
        ev.append(f"Dialogue: 0,{ass_time(s)},{ass_time(e + 0.08)},Cap,,0,0,0,,{txt.rstrip('.,')}")
        group.clear()

    for w in words:
        group.append(w)
        if len(group) == 3 or re.search(r"[.?!,]$", w["w"]):
            flush()
    flush()
    ev.insert(0, f"Dialogue: 0,0:00:00.00,{ass_time(end_all)},Top,,0,0,0,,{title}")
    Path(path).write_text(hdr + "\n".join(ev) + "\n")


def main(spec_path, variant, out):
    spec = json.loads(Path(spec_path).read_text())
    words = json.loads(Path(spec["words"]).read_text())
    i0, i1 = take_segment(words, variant)
    seg = words[i0:i1 + 1]
    t0, t1 = max(seg[0]["s"] - 0.08, 0), seg[-1]["e"] + 0.12
    dur = t1 - t0
    plan = next(p for p in json.loads((ROOT / "docs/plans/plans.json").read_text())["plans"] if p["slug"] == spec["plan"])
    # card window: from "here's" to "comment" (Whisper may hear "common")
    hs = next((w["s"] for w in seg if norm(w["w"]) in ("heres", "here")), seg[len(seg) // 2]["s"])
    cs = next((w["s"] for w in seg if norm(w["w"]) in ("comment", "common") and w["s"] > hs), t1 - 2)
    a, b = hs - t0, cs - t0
    n = len(plan["days"])
    step = max((b - a) / n, 0.75)
    windows = [(a + k * step, a + (k + 1) * step) for k in range(n)]
    tmp = Path(tempfile.mkdtemp())
    for k, day in enumerate(plan["days"]):
        card_png(day, spec["keyword"], tmp / f"card{k}.png")
    captions_ass(apply_fixes(seg, spec.get("fix", [])), t0, windows, spec["title"], spec["keyword"], tmp / "cap.ass")

    inputs = ["-ss", f"{t0:.3f}", "-t", f"{dur:.3f}", "-i", spec["footage"]]
    fc = [f"[0:v]scale={W}:{H},lut3d='{LUT}',eq=contrast=1.04:saturation=1.05,setsar=1[base]"]
    last = "base"
    idx = 1
    for br in spec.get(f"broll_{variant}", spec.get("broll", [])):
        hit = next((w for w in seg if re.search(br["match"], w["w"], re.I)), None)
        if not hit:
            continue
        s = hit["s"] - t0
        e = min(s + br.get("dur", 2.0), dur)
        inputs += ["-ss", str(br["in"]), "-t", f"{e - s + 0.2:.2f}", "-i", br["clip"]]
        if br.get("mode", "full") == "full":
            fc.append(f"[{idx}:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setpts=PTS-STARTPTS+{s:.3f}/TB[b{idx}]")
        else:
            fc.append(f"[{idx}:v]scale={W - 80}:-2,setpts=PTS-STARTPTS+{s:.3f}/TB[b{idx}]")
        x, y = ("0", "0") if br.get("mode", "full") == "full" else ("40", "200")
        fc.append(f"[{last}][b{idx}]overlay={x}:{y}:eof_action=pass:enable='between(t,{s:.3f},{e:.3f})'[v{idx}]")
        last, idx = f"v{idx}", idx + 1
    for k, (s, e) in enumerate(windows):
        inputs += ["-i", str(tmp / f"card{k}.png")]
        fc.append(f"[{last}][{idx}:v]overlay=(W-w)/2:H*0.585:enable='between(t,{s:.3f},{e:.3f})'[c{k}]")
        last, idx = f"c{k}", idx + 1
    fc.append(f"[{last}]subtitles='{tmp / 'cap.ass'}':fontsdir='{FONT}'[out]")
    fc.append("[0:a]loudnorm=I=-14:TP=-1.5:LRA=11[aout]")
    cmd = ["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", ";".join(fc), "-map", "[out]", "-map", "[aout]",
           "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p", "-r", "30",
           "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-t", f"{dur:.3f}", out]
    subprocess.run(cmd, check=True)
    print(f"{out}: take {variant} {t0:.2f}-{t1:.2f}s ({dur:.1f}s), cards {[(round(s,1), round(e,1)) for s, e in windows]}")


if __name__ == "__main__":
    main(*sys.argv[1:4])
