"""Cut the first-fight tape so each clip fills its slot exactly, at real speed, synced to the words.

    python -P make_broll.py A     # reads work/edl_A.json, writes assets/media/b_<name>.mp4 (+ .wav) + work/broll.json

Source: media/first-fight/first-fight-2.mp4 (480x852). Matteo = blue shorts, back to the camera. Clinch 42.4 s,
elbows 43.1-47.8, the ref separates them ~47.9-48.1, the right hand lands 48.33, he drops 48.6-48.9.
Segments (takes.json order): open (hook + "I was sixteen..."), body1, share, body2, end.
Anchors: (seg, word | None | "END", k, offset). `hold` freezes the last frame from that source second.
Each clip also gets its own tape audio (crowd, gloves, ref) as b_<name>.wav, mixed under the voice by build.py.
"""
import json
import subprocess
import sys
from pathlib import Path

V = sys.argv[1]
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SRC = ROOT / "media/first-fight/first-fight-2.mp4"
KO = 48.33
sys.path.insert(0, str(HERE))
from reel import REEL  # noqa: E402

SLOTS = {
    # the hook opens on the knockout: the right hand lands on the hook's punch word
    "hook":   dict(crop=(110, 0, 360, 640), full=True, a=("open", None, 1, 0), b=("open", "HOOKEND", 1, 0),
                   sync=(KO, ("open", REEL["ko_word"][V], 1, 0.05))),
    # "The ref steps in to separate us. And I throw the right hand anyway. He's out." one real-speed clip
    "fight":  dict(crop=(0, 0, 480, 600), a=("body1", "REF", 1, -0.35), b=("body1", "THEY", 1, -0.06),
                   sync=(KO, ("body1", "RIGHT", 1, 0.0))),
    # "They should've disqualified me." the punch, frozen with the ref already in between
    "freeze": dict(crop=(110, 0, 360, 450), a=("body1", "THEY", 2, -0.08), b=("body1", "END", 1, 0),
                   sync=(KO - 0.35, ("body1", "THEY", 2, -0.08)), hold=KO - 0.02),
}

d = json.load(open(HERE / f"work/edl_{V}.json", encoding="utf-8"))
SEG = {("open" if s["name"].startswith("open") else "end" if s["name"].startswith("end") else s["name"]): s
       for s in d["segments"]}
(HERE / "assets/media").mkdir(parents=True, exist_ok=True)


def at(a):
    seg, word, k, off = a
    s = SEG[seg]
    if word is None:
        return s["start"] + off
    if word == "END":
        return s["end"] + off
    if word == "HOOKEND":
        return hook_end(d, V) + off
    hits = [w for w in d["words"] if w["seg"] == s["i"] and w["w"] == word]
    return hits[k - 1]["s"] + off


def hook_end(d, V):
    """The hook ends where "I was sixteen" starts (first 'I' after the last hook word)."""
    s = SEG["open"]
    ws = [w for w in d["words"] if w["seg"] == s["i"]]
    last = REEL["hook_last"][V]
    idx = max(i for i, w in enumerate(ws) if w["w"] == last)
    return round(ws[idx + 1]["s"] - 0.04, 3) if idx + 1 < len(ws) else ws[idx]["e"] + 0.2


if __name__ == "__main__":
    out = {}
    for name, c in SLOTS.items():
        t0, t1 = at(c["a"]), at(c["b"])
        src_t, anchor = c["sync"]
        a = src_t - (at(anchor) - t0)
        dur = t1 - t0 + 0.15
        x, y, w, h = c["crop"]
        hold = ""
        if c.get("hold") and c["hold"] < a + dur:
            keep = max(0.04, c["hold"] - a)
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
        # tape audio for the moving clips only (a freeze has no sound of its own)
        if not c.get("hold"):
            subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-ss", f"{max(0, a):.3f}", "-t", f"{dur:.3f}", "-i", str(SRC),
                            "-vn", "-af", f"highpass=f=120,afade=t=in:d=0.08,afade=t=out:st={max(0, dur - 0.2):.3f}:d=0.2",
                            "-ar", "48000", "-ac", "2", str(dst.with_suffix(".wav"))], check=True)
        out[name] = {"start": round(t0, 3), "dur": round(t1 - t0, 3), "src": [round(a, 2), round(a + dur, 2)],
                     "full": bool(c.get("full")), "audio": not c.get("hold")}
        print(f"{name:7} slot {t0:6.2f}-{t1:6.2f} ({t1 - t0:4.2f}s)  src {a:.2f}-{a + dur:.2f}")
    json.dump(out, open(HERE / "work/broll.json", "w"), indent=1)
