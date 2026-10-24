"""Cut the first-fight tape so each clip fills its slot exactly (real speed, no clip ever runs out and freezes).

    python -P make_broll.py A     # reads work/edl_A.json, writes assets/media/b_<name>.mp4 + work/broll.json

Source: media/first-fight/first-fight-1.mp4 (Drive "Muay Thai fight matteo .MOV", 480x852, filmed from the corner).
Moments (checked frame by frame 2026-10-24): clinch 45.4-47.5 s, ref steps in ~50.3, right hand ~50.5, he drops ~50.9.
Each slot is [from-anchor, to-anchor] in the cut; the source starts at `src_at` and runs as long as the slot needs.
`sync` = (source second, anchor) to line a moment up with a spoken word instead of the slot start.
Frame: 4:5 crop of the ring (1080x1350 at y=285) over a dark blurred copy, like 2026-10-21-saenchai-editorial.
"""
import json
import subprocess
import sys
from pathlib import Path

V = sys.argv[1]
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SRC = ROOT / "media/first-fight/first-fight-1.mp4"
# name: (crop x, y, w, h in source px, slot from, slot to, sync)   anchors: (seg, word|None|"END", k, offset)
SLOTS = {
    # "I was 16 and it was my first fight" over the arena (variants that say it in the body, not C)
    "ring":   ((0, 60, 480, 600), ("setup", None, 1, -0.12), ("setup", "IT", 2, -0.05), (3.0, ("setup", None, 1, -0.12))),
    "clinch": ((30, 130, 400, 500), ("fight", "WE", 1, -0.12), ("fight", "THE", 2, -0.05), (45.4, ("fight", "WE", 1, -0.12))),
    # the right hand lands on "throw", he drops under "right hand / he's out"
    "ko":     ((30, 130, 400, 500), ("fight", "THE", 2, -0.05), ("fight", "END", 1, 0), (50.45, ("fight", "THROW", 1, 0))),
    # replay on "some people say the right hand was too late"
    "replay": ((60, 170, 260, 325), ("debate", "SOME", 1, -0.1), ("debate", "YOU", 1, -0.06), (50.45, ("debate", "RIGHT", 1, 0))),
}

d = json.load(open(HERE / f"work/edl_{V}.json", encoding="utf-8"))
segs = {s["name"]: s for s in d["segments"]}
(HERE / "assets/media").mkdir(parents=True, exist_ok=True)


def at(a):
    seg, word, k, off = a
    s = segs[seg]
    if word is None:
        return s["start"] + off
    if word == "END":
        return s["end"] + off
    hits = [w for w in d["words"] if w["seg"] == s["i"] and w["w"] == word]
    return hits[k - 1]["s"] + off


out = {}
for name, (crop, fa, fb, (src_t, anchor)) in SLOTS.items():
    if fa[0] not in segs:
        continue
    t0, t1 = at(fa), at(fb)
    a = src_t - (at(anchor) - t0)          # source second shown at the slot start
    dur = t1 - t0 + 0.15
    x, y, w, h = crop
    fc = (f"[0:v]fps=30,split[a][b];"
          f"[a]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=30:2,eq=brightness=-0.3:saturation=0.6[bg];"
          f"[b]crop={w}:{h}:{x}:{y},scale=1080:1350:force_original_aspect_ratio=increase:flags=lanczos,crop=1080:1350,"
          f"unsharp=5:5:0.8,eq=contrast=1.07:saturation=1.08[fg];"
          f"[bg][fg]overlay=0:285,noise=alls=6:allf=t,format=yuv420p")
    dst = HERE / f"assets/media/b_{name}.mp4"
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-ss", f"{a:.3f}", "-t", f"{dur:.3f}", "-i", str(SRC),
                    "-filter_complex", fc, "-an", "-c:v", "libx264", "-crf", "19", "-preset", "fast",
                    "-g", "30", "-keyint_min", "30", "-movflags", "+faststart", str(dst)], check=True)
    out[name] = {"start": round(t0, 3), "dur": round(t1 - t0, 3), "src": [round(a, 2), round(a + dur, 2)]}
    print(f"{name:7} slot {t0:6.2f}-{t1:6.2f} ({t1 - t0:4.2f}s)  src {a:.2f}-{a + dur:.2f}")
json.dump(out, open(HERE / "work/broll.json", "w"), indent=1)
