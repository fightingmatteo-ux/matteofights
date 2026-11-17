"""Floyd b-roll: cut each clip from its source, frame it over a dark blurred copy, and write work/broll_<V>.json.

    python -P work/broll.py          (from the reel folder, after assemble.py has written work/edl_<V>.json)

Clip = (source, source start, duration, crop aspect w/h, crop centre x as a fraction of the width).
Placement = an EDL word ("WORD", k, segment) the cutaway starts 0.12 s before (J-cut).
"""
import json
import os
import subprocess

M = "../../../media/"
DEF, PULL = M + "yt-floyd-defense-highlights.mp4", M + "yt-floyd-pull-counter.mp4"
CLIPS = {
    "hA": (DEF, 149.2, 3.0, 0.8, 0.48),      # Canelo's punches land on the raised shoulder
    "hX": (PULL, 36.4, 3.0, 0.8, 0.47),      # Marquez throws, Floyd leans out, right hand back (hooks B-E)
    "ret": (DEF, 468.4, 3.2, 0.8, 0.50),     # Floyd celebrating, arm up
    "roll": (DEF, 107.0, 3.2, 0.8, 0.45),    # shell at the ropes, Canelo throws into it
    "one": (DEF, 115.6, 3.0, 0.8, 0.45),     # Canelo's right hand hits the shoulder
    "two": (DEF, 113.0, 2.0, 1.0, 0.50),     # lead hand low across the stomach
    "pc1": (PULL, 0.6, 3.4, 1.0, 0.42),      # pull counter on Marquez
    "pc2": (DEF, 145.4, 2.8, 1.0, 0.45),     # the right hand comes straight back, then Canelo misses
}
HOOK_CLIP = {"A": "hA", "B": "hX", "C": "hX", "D": "hX", "E": "hX"}
HOOK_AT = {"A": ("BUT", 1), "B": ("FLOYD", 1), "C": ("HE", 1), "D": ("FIGHTER", 1), "E": ("FIGHTER", 1)}
BODY = [("ret", ("FLOYD", 1, "body")), ("roll", ("SHOULDER", 1, "body")), ("one", ("HIS", 2, "one")),
        ("two", ("LEAD", 1, "two")), ("pc1", ("WHEN", 1, "three")), ("pc2", ("HIS", 1, "three"))]
DAYS, DAY = 5, 0.65

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
    end = [s for s in d["segments"] if s["name"] == "end"][0]
    fri = [w for w in d["words"] if w["w"] == "FRIDAY" and w["seg"] == end["i"]][0]["e"]
    for i in range(DAYS):
        plan[f"day{i + 1}"] = {"start": round(fri + 0.1 + i * DAY, 3), "dur": DAY}
    nxt = [w for w in d["words"] if w["w"] == "COMMENT" and w["seg"] == end["i"]][0]["s"]
    assert fri + 0.1 + DAYS * DAY <= nxt + 0.05, f"{V}: day cards run into 'Comment' ({fri + 0.1 + DAYS * DAY:.2f} > {nxt:.2f})"
    json.dump(plan, open(f"work/broll_{V}.json", "w"), indent=1)
    print(V, " ".join(f"{n}@{c['start']:.1f}" for n, c in plan.items() if not n.startswith("day")))
