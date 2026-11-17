"""Gane b-roll: cut each clip from its source, frame it over a dark blurred copy, and write work/broll_<V>.json.

    python -P work/broll.py          (from the reel folder, after assemble.py has written work/edl_<V>.json)

Clip = (source, source start, duration, crop aspect w/h, crop centre x as a fraction of the width).
Placement = an EDL word ("WORD", k, segment) the cutaway starts 0.12 s before (J-cut).
Gane = white/red flag shorts (VENUM), Pereira = blue shorts.
"""
import json
import os
import subprocess

M = "../../../media/"
GP, MT = M + "yt-gane-pereira-full.mp4", M + "yt-gane-muaythai.mp4"
CLIPS = {
    "kmiss": (GP, 384.6, 2.3, 1.0, 0.48),   # R2 4:38, close: Pereira's high kick, Gane leans out of it (hooks A, B)
    "fin": (GP, 446.3, 3.3, 1.0, 0.50),     # R2 3:36-3:33: Gane's last punches at the cage, the referee stops it (hook C)
    "jab": (GP, 92.6, 2.8, 1.0, 0.50),      # R1 4:12-4:11, close: Gane measures, then the long jab from range (hook D)
    "mt": (MT, 75.0, 2.6, 1.0, 0.47),       # Gane's Muay Thai fight, the kick (hook E)
    "lw": (GP, 104.0, 3.4, 1.0, 0.45),      # R1 4:01-3:57: bouncing, long lunge in, straight back out
    "miss": (GP, 71.8, 4.0, 1.0, 0.47),     # R1 4:33-4:30: Pereira lunges with the right, Gane is already off the line
    "two": (GP, 156.9, 3.0, 1.0, 0.50),     # R1 3:08-3:06, close: jab paw, then the kick from the edge of range
    "ko": (GP, 398.85, 3.4, 1.0, 0.42),     # R2 4:24-4:22: Pereira steps in, Gane's counter drops him
}
HOOK_CLIP = {"A": "kmiss", "B": "kmiss", "C": "fin", "D": "jab", "E": "mt"}
HOOK_AT = {"A": ("GANE", 1), "B": ("FIGHTER", 1), "C": ("AND", 1), "D": ("FIGHTER", 1), "E": ("AND", 1)}
BODY = [("lw", ("MOVES", 1, "body")), ("miss", ("SMALL", 1, "one")), ("two", ("LONG", 1, "two")),
        ("ko", ("HE", 2, "three"))]
DAYS, DAY, GAP = 5, 0.62, 0.7

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
