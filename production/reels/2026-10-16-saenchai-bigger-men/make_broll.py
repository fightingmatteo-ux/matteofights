"""Cut the Saenchai tape clips so each one fills its slot exactly: no clip ever runs out and freezes.

    python -P make_broll.py A     # reads work/edl_A.json, writes assets/media/b_<name>.mp4 + work/broll.json

Each slot is [from-anchor, to-anchor] in the cut (word starts). The source range is stretched with a slow-mo
(motion-interpolated) when the slot is longer than the source, never past MAX_SLOW; if it still doesn't fill,
the source end is extended. Frame: 4:5 crop of the action (1080x1350 at y=285) over a dark blurred copy.
Learned 2026-10-16: 3 s clips under 5 s lines froze on their last frame ("freeze frames that show nothing").
"""
import json, subprocess, sys
from pathlib import Path

V = sys.argv[1]
ROOT = Path(__file__).resolve().parents[3]
SRC = {"T": ROOT / "media/saenchai-broll/aW6ew2j1ZmQ.mp4",          # YOKKAO: Saenchai sparring in Canada
       "B": ROOT / "media/saenchai-broll/EXPvZzeb5cE.mp4",          # Riddick Bowe and Saenchai @ 13 Coins Gym
       "H": ROOT / "media/saenchai-broll/clips/05-harrison-down-1.mp4"}  # Liam Harrison vs Saenchai 2 (2011), 12:55.5-12:58
MAX_SLOW = 2.0
# name: (source, src start, src end, crop centre x in source px, slot from, slot to)   anchors: (seg, word|None, k, offset)
SLOTS = [
    ("size",    "B", 95.6, 98.9, 790, ("heavier", None, 1, -0.12), ("heavier", "OFTEN", 1, 0)),
    ("trade",   "T", 22.0, 25.2, 640, ("heavier", "OFTEN", 1, 0),   ("heavier", "END", 1, 0)),
    ("teep",    "T", 7.4, 10.8, 640,  ("muscle", "NEVER", 1, -0.1), ("muscle", "END", 1, 0)),
    ("step",    "T", 29.3, 30.9, 560, ("step", "STEP", 1, -0.12),   ("step", "CATCH", 1, 0)),
    ("catch",   "T", 30.7, 32.4, 520, ("step", "CATCH", 1, 0),      ("step", "SWEEP", 1, 0)),
    ("sweep",   "B", 98.9, 101.3, 760, ("step", "SWEEP", 1, 0),     ("step", "START", 1, 0)),
    ("over",    "B", 102.6, 105.4, 700, ("step", "START", 1, 0),    ("reset", None, 1, -0.12)),
    ("dump",    "T", 15.9, 18.9, 600, ("reset", None, 1, -0.12),    ("reset", "A", 1, 0)),
    ("stance",  "T", 34.9, 37.6, 640, ("reset", "A", 1, 0),         ("reset", "TEN", 1, -0.08)),
    ("harr",    "H", 0.55, 2.5, 427,   ("reset", "TEN", 1, -0.08),   ("reset", "HE'S", 1, 0)),
    ("frust",   "B", 105.2, 108.2, 720, ("reset", "HE'S", 1, 0),    ("reset", "END", 1, 0)),
]

d = json.load(open(ROOT / f"production/reels/2026-10-16-saenchai-bigger-men/work/edl_{V}.json", encoding="utf-8"))
segs = {s["name"]: s for s in d["segments"]}
segs.update({"hook": d["segments"][0], "loop": d["segments"][-1]})


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
for name, src, a, b, cx, fa, fb in SLOTS:
    t0, t1 = at(fa), at(fb)
    need = t1 - t0 + 0.15
    speed = min(MAX_SLOW, max(1.0, need / (b - a)))
    if (b - a) * speed < need:
        b = a + need / speed
    w = 384 if src == "H" else 576
    hsrc = 480 if src == "H" else 720
    x0 = max(0, min((854 if src == "H" else 1280) - w, int(cx - w / 2)))
    slow = f"setpts={speed:.3f}*PTS,minterpolate=fps=30:mi_mode=mci:mc_mode=aobmc:vsbmc=1," if speed > 1.02 else ""
    fc = (f"[0:v]{slow}fps=30,split[a][b];"
          f"[a]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=30:2,eq=brightness=-0.3:saturation=0.6[bg];"
          f"[b]crop={w}:{hsrc}:{x0}:0,scale=1080:1350:flags=lanczos,unsharp=5:5:0.6,eq=contrast=1.07:saturation=1.1[fg];"
          f"[bg][fg]overlay=0:285,noise=alls=6:allf=t,format=yuv420p")
    dst = ROOT / f"production/reels/2026-10-16-saenchai-bigger-men/assets/media/b_{name}.mp4"
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-ss", f"{a:.3f}", "-to", f"{b:.3f}", "-i", str(SRC[src]),
                    "-filter_complex", fc, "-an", "-c:v", "libx264", "-crf", "19", "-preset", "fast",
                    "-g", "30", "-keyint_min", "30", "-movflags", "+faststart", str(dst)], check=True)
    out[name] = {"start": round(t0, 3), "dur": round(t1 - t0, 3), "speed": round(speed, 2), "src": src, "range": [a, round(b, 2)]}
    print(f"{name:7} slot {t0:6.2f}-{t1:6.2f} ({t1 - t0:4.2f}s)  src {src} {a:.1f}-{b:.1f}  x{speed:.2f}")
json.dump(out, open(ROOT / "production/reels/2026-10-16-saenchai-bigger-men/work/broll.json", "w"), indent=1)
