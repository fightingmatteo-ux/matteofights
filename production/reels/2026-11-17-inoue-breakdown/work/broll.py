"""Inoue b-roll: cut each clip from its source, frame it over a dark blurred copy, and write work/broll_<V>.json.

    python -P work/broll.py          (from the reel folder, after assemble.py has written work/edl_<V>.json)

Clip = (source, source start, duration, crop aspect w/h, crop centre x as a fraction of the width).
Placement = an EDL word ("WORD", k, segment) the cutaway starts 0.12 s before (J-cut).
Inoue vs Nakatani (Tokyo Dome, 2 May 2026): Inoue = blond, black shorts; Nakatani = dark hair, white/gold JUNCO.
Top Rank reel: McDonnell 2018 (Inoue black/gold, McDonnell pink JAMIE), Moloney 2020 (Inoue blond, gold shorts).
"""
import json
import os
import subprocess

M = "../../../media/"
DZ, TR = M + "yt-inoue-nakatani-dazn.mp4", M + "yt-inoue-toprank-kos.mp4"
CLIPS = {
    "feet": (DZ, 52.8, 3.0, 1.0, 0.45),     # R1 2:47-2:45, wide low angle: both stances, feet in frame (hooks A, E)
    "drop": (TR, 28.8, 3.2, 1.0, 0.50),     # McDonnell R1: Inoue lands, McDonnell drops (hook B)
    "dome": (DZ, 38.8, 2.1, 1.0, 0.50),     # the Tokyo Dome: INOUE vs NAKATANI on the big screen, the full stands (hook C)
    "punch": (DZ, 599.8, 1.6, 1.0, 0.45),   # R12 close: Inoue's right hand lands, whole body behind it (hook D)
    "belt": (DZ, 690.0, 2.4, 1.0, 0.50),    # after the decision: arms up, the belts
    "jab": (TR, 168.6, 2.8, 1.0, 0.50),     # Moloney R4: the jab from range
    "body": (TR, 50.8, 4.0, 1.0, 0.50),     # McDonnell replay: his guard goes up to his head, Inoue digs to the body
    "bal": (DZ, 603.8, 2.8, 1.0, 0.40),     # R12 high angle: feet planted under the punch
}
HOOK_CLIP = {"A": "feet", "B": "drop", "C": "dome", "D": "punch", "E": "feet"}
HOOK_AT = {"A": ("BUT", 1), "B": ("FIGHTER", 1), "C": ("SOLD", 1), "D": ("FIGHTER", 1), "E": ("AND", 1)}
BODY = [("belt", ("CALLED", 1, "body")), ("jab", ("FAST", 1, "one")), ("body", ("DIGS", 1, "two")),
        ("bal", ("WEIGHT", 1, "three"))]
DAYS, DAY, GAP = 5, 0.6, 0.7

os.makedirs("assets/broll", exist_ok=True)
for name, (src, ss, dur, asp, cx) in CLIPS.items():
    out = f"assets/broll/b_{name}.mp4"
    if os.path.exists(out):
        continue
    fg_h = round(1080 / asp)  # 1080 wide, 1350 (4:5) or 1080 (1:1) tall
    vf = (f"[0:v]fps=30,split[a][b];"
          f"[a]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=40:2,eq=brightness=-0.28[bg];"
          f"[b]crop=ih*{asp}:ih:max(0\\,min(iw-ih*{asp}\\,iw*{cx}-ih*{asp}/2)):0,scale=1080:{fg_h}[fg];"
          f"[bg][fg]overlay=0:(H-h)/2,format=yuv420p[v]")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(ss), "-t", str(dur), "-i", src, "-filter_complex", vf,
                    "-map", "[v]", "-an", "-c:v", "libx264", "-crf", "18", "-preset", "slow", "-movflags", "+faststart",
                    out], check=True)
    print("made", out)

for V in "ABCDE":
    d = json.load(open(f"work/edl_{V}.json", encoding="utf-8"))
    seg = {s["i"]: s["name"] for s in d["segments"]}

    def W(word, k, segname=None):
        return [w for w in d["words"] if w["w"] == word and (segname is None or seg[w["seg"]] == segname)][k - 1]["s"]

    h = HOOK_CLIP[V]
    plan = {h: {"start": round(W(*HOOK_AT[V]) - 0.06, 3), "dur": CLIPS[h][2]}}
    for name, ref in BODY:
        plan[name] = {"start": round(W(*ref) - 0.12, 3), "dur": CLIPS[name][2]}
    # the 5 plan day cards play over the room tone after the CTA's last word
    end = [s for s in d["segments"] if s["name"] == "end"][0]
    last = [w for w in d["words"] if w["seg"] == end["i"]][-1]["e"]
    for i in range(DAYS):
        plan[f"day{i + 1}"] = {"start": round(last + GAP + i * DAY, 3), "dur": DAY}
    assert last + GAP + DAYS * DAY <= d["duration"], f"{V}: day cards run past the end"
    json.dump(plan, open(f"work/broll_{V}.json", "w"), indent=1)
    print(V, " ".join(f"{n}@{c['start']:.1f}" for n, c in plan.items() if not n.startswith("day")), f"cards@{last + GAP:.1f}-{last + GAP + DAYS * DAY:.1f}/{d['duration']:.1f}")
