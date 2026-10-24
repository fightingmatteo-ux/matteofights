"""Cut the first-fight tape so each clip fills its slot exactly, at real speed, synced to the words.

    python -P make_broll.py A     # reads work/edl_A.json, writes assets/media/b_<name>.mp4 + work/broll.json

Source: media/first-fight/first-fight-2.mp4 (Drive "Muay Thai fight matteo 2.MOV", 480x852). Matteo = blue shorts, red
gloves, back to the camera (confirmed by Matteo 2026-10-24). Frame by frame: clinch 42.4 s, elbows to the top of his
head 43.1-47.8, the ref separates them ~47.9-48.1, the right hand lands 48.33, he drops out of frame 48.6-48.9.
Slots: [from-anchor, to-anchor] in the cut; `sync` = (source second, anchor) puts that moment on that word.
Anchors: (seg, word | None | "END", k, offset); seg "hook" = first segment, "body" = second, "loop" = last.
`hold` = freeze the clip's last frame once the source reaches that second (a deliberate freeze on the punch).
`full` = full-bleed 9:16 crop (the hook); otherwise a 4:5 crop over a dark blurred copy.
"""
import json
import subprocess
import sys
from pathlib import Path

V = sys.argv[1]
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SRC = ROOT / "media/first-fight/first-fight-2.mp4"
KO = 48.33  # the right hand lands
PUNCH_WORD = {"A": "KNOCKED", "B": "KNOCKED", "C": "FIRST"}[V]
SLOTS = {
    # every hook opens on the knockout: the right hand lands on the spoken word
    "hook":   dict(crop=(110, 0, 360, 640), full=True, a=("hook", None, 1, 0), b=("hook", "END", 1, 0),
                   sync=(KO, ("hook", PUNCH_WORD, 1, 0.05))),
    # "so we clinch, I elbow the top of his head, the referee steps in and I throw the right hand. He's out":
    # ONE real-speed clip, the narration lines up with the tape (elbows, ref, punch on "right", he's down by "out")
    "fight":  dict(crop=(0, 0, 480, 600), a=("body", "WE", 1, -0.12), b=("body", "THEY", 1, -0.08),
                   sync=(KO, ("body", "RIGHT", 1, 0))),
    # "some people say the right hand came too early. You be the judge": replay, freezes on the punch
    "replay": dict(crop=(130, 0, 320, 400), a=("body", "SOME", 1, -0.1), b=("body", "TELL", 1, -0.06),
                   sync=(KO, ("body", "RIGHT", 2, 0.1)), hold=KO + 0.04),
}

d = json.load(open(HERE / f"work/edl_{V}.json", encoding="utf-8"))
segs = {"hook": d["segments"][0], "body": d["segments"][1], "loop": d["segments"][-1]}
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
for name, c in SLOTS.items():
    t0, t1 = at(c["a"]), at(c["b"])
    src_t, anchor = c["sync"]
    a = src_t - (at(anchor) - t0)          # source second on screen at the slot start
    dur = t1 - t0 + 0.15
    x, y, w, h = c["crop"]
    hold = ""
    if c.get("hold") and c["hold"] < a + dur:
        keep = c["hold"] - a
        hold = f"trim=duration={keep:.3f},tpad=stop_mode=clone:stop_duration={dur - keep + 0.1:.3f},"
    if c.get("full"):
        fc = (f"[0:v]fps=30,{hold}crop={w}:{h}:{x}:{y},scale=1080:1920:flags=lanczos,unsharp=5:5:0.7,"
              f"eq=contrast=1.06:saturation=1.08,noise=alls=5:allf=t,format=yuv420p")
    else:
        fc = (f"[0:v]fps=30,{hold}split[a][b];"
              f"[a]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=30:2,eq=brightness=-0.3:saturation=0.6[bg];"
              f"[b]crop={w}:{h}:{x}:{y},scale=1080:1350:force_original_aspect_ratio=increase:flags=lanczos,crop=1080:1350,"
              f"unsharp=5:5:0.8,eq=contrast=1.07:saturation=1.08[fg];"
              f"[bg][fg]overlay=0:285,noise=alls=6:allf=t,format=yuv420p")
    dst = HERE / f"assets/media/b_{name}.mp4"
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-ss", f"{max(0, a):.3f}", "-t", f"{dur + 0.2:.3f}", "-i", str(SRC),
                    "-filter_complex", fc, "-an", "-t", f"{dur:.3f}", "-c:v", "libx264", "-crf", "18", "-preset", "fast",
                    "-g", "30", "-keyint_min", "30", "-movflags", "+faststart", str(dst)], check=True)
    out[name] = {"start": round(t0, 3), "dur": round(t1 - t0, 3), "src": [round(a, 2), round(a + dur, 2)],
                 "full": bool(c.get("full"))}
    print(f"{name:7} slot {t0:6.2f}-{t1:6.2f} ({t1 - t0:4.2f}s)  src {a:.2f}-{a + dur:.2f}")
json.dump(out, open(HERE / "work/broll.json", "w"), indent=1)
