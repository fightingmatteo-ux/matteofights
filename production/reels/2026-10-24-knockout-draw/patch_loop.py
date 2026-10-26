"""Seamless loop without a re-render (Matteo 2026-10-26: "you can see the video ended").

The hook opens on the KO tape; the video ended on the talking head, so the restart read as a new video. This puts the
loop line (the last segment, voice untouched) over the SAME tape, the seconds just before the hook's first frame, framed
and graded like that first frame, so the last frame runs straight into frame 0. Captions are lifted from the render
(white text) and laid back on the tape with their shadow.

    python patch_loop.py A          # ../../../media/<slug>/<slug>-A.mp4 in place, then rebuilds -phone.mp4
    python patch_loop.py A IN OUT   # one file (local test)
"""
import json
import subprocess
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
SLUG = HERE.name
ROOT = HERE.parents[2]
SRC = ROOT / "media/first-fight/first-fight-2.mp4"
KO = 48.33
PUNCH_WORD = {"A": "KNOCKED", "B": "KNOCKED", "C": "FIRST"}
W, H, FPS = 1080, 1920, 30
TAPE = "crop=360:640:110:0,scale=1080:1920:flags=lanczos,unsharp=5:5:0.7,eq=contrast=1.06:saturation=1.08"  # make_broll "hook"


def raw(args, n=None):
    b = subprocess.run(["ffmpeg", "-v", "error", *args, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(b, np.uint8).reshape(-1, H, W, 3)


def soften(a, r):
    k = np.ones(2 * r + 1) / (2 * r + 1)
    a = np.apply_along_axis(lambda x: np.convolve(x, k, "same"), 0, a)
    return np.apply_along_axis(lambda x: np.convolve(x, k, "same"), 1, a)


def fit(frame0, tape0):
    """Camera scale/offset and per-channel gain that turn the tape frame into the render's frame 0 (plates excluded)."""
    g0 = frame0[::4, ::4].mean(-1)
    keep = np.zeros(g0.shape, bool)
    keep[:110], keep[340:] = True, True  # top and bottom of the frame: no hook plate or caption there
    best = (1e18, None)
    t = tape0.astype(np.float32)
    for s in np.arange(1.0, 1.26, 0.01):
        sw, sh = int(round(W * s)), int(round(H * s))
        big = np.frombuffer(subprocess.run(["ffmpeg", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-i", "-",
                                       "-vf", f"scale={sw}:{sh}", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                                      input=tape0.tobytes(), capture_output=True, check=True).stdout, np.uint8).reshape(sh, sw, 3)
        for oy in range(0, sh - H + 1, 8):
            for ox in range(0, sw - W + 1, 8):
                c = big[oy:oy + H:4, ox:ox + W:4].mean(-1)
                gain = (g0[keep] * c[keep]).sum() / max((c[keep] ** 2).sum(), 1)
                e = ((g0[keep] - gain * c[keep]) ** 2).mean()
                if e < best[0]:
                    best = (e, (s, ox, oy))
    s, ox, oy = best[1]
    return s, ox, oy


def patch(v, src, dst):
    d = json.load(open(HERE / f"work/edl_{v}.json", encoding="utf-8"))
    hook, loop = d["segments"][0], d["segments"][-1]
    punch = [w for w in d["words"] if w["seg"] == hook["i"] and w["w"] == PUNCH_WORD[v]][0]["s"]
    src0 = KO - (punch - hook["start"])  # tape second on screen at frame 0
    n_total = int(subprocess.run(["ffprobe", "-v", "error", "-count_packets", "-select_streams", "v:0", "-show_entries",
                                  "stream=nb_read_packets", "-of", "csv=p=0", str(src)], capture_output=True, text=True, check=True).stdout)
    first = round(loop["start"] * FPS)
    n = n_total - first
    frame0 = raw(["-i", str(src), "-frames:v", "1"])[0].astype(np.float32)
    tape0 = raw(["-ss", f"{src0:.3f}", "-i", str(SRC), "-frames:v", "1", "-vf", TAPE])[0]
    s, ox, oy = fit(frame0, tape0)
    sw, sh = int(round(W * s)), int(round(H * s))
    vf = f"fps={FPS},{TAPE},scale={sw}:{sh},crop={W}:{H}:{ox}:{oy}"
    # the clinch starts at the left edge of the hook crop: open framed on it, ease over to the hook's framing by the end
    dur = n / FPS
    pan = f"'110*(1-cos(PI*min(1,max(0,(t-{dur - 1.4:.3f})/1.2))))/2'"
    loop_vf = vf.replace("crop=360:640:110:0", f"crop=360:640:{pan}:0")
    # tape for the loop: ends one frame before src0, so the next frame (frame 0) continues it
    tape = raw(["-ss", f"{src0 - n / FPS:.3f}", "-i", str(SRC), "-frames:v", str(n), "-vf", loop_vf]).astype(np.float32)
    ref = raw(["-ss", f"{src0:.3f}", "-i", str(SRC), "-frames:v", "1", "-vf", vf])[0].astype(np.float32)
    keep = np.zeros((H, W), bool)
    keep[:440], keep[1360:] = True, True
    gain = np.array([(frame0[..., c][keep] * ref[..., c][keep]).sum() / (ref[..., c][keep] ** 2).sum() for c in range(3)])
    tape = tape * gain
    orig = raw(["-i", str(src), "-vf", f"select=gte(n\\,{first})", "-vsync", "0"]).astype(np.float32)
    fixed = {}
    for k in range(min(n, len(tape), len(orig))):
        o = orig[k]
        white = (o.min(-1) > 214) & (o.max(-1) - o.min(-1) < 22)
        white[:150], white[700:] = False, False  # the caption band
        a = soften(white.astype(np.float32), 1)
        shadow = soften(white.astype(np.float32), 10) * 0.5
        base = tape[k] * (1 - shadow[..., None])
        fixed[first + k] = np.clip(base * (1 - a[..., None]) + o * a[..., None], 0, 255).astype(np.uint8)
    print(f"{v}: loop frames {first}-{first + len(fixed) - 1} over tape {src0 - n / FPS:.2f}-{src0:.2f} s, camera {s:.2f}x +{ox},{oy}, gain {np.round(gain, 2)}")
    tmp = Path(str(dst) + ".tmp.mp4")
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                          "-i", "-", "-i", str(src), "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-crf", "16", "-preset", "medium",
                          "-pix_fmt", "yuv420p", "-c:a", "copy", "-movflags", "+faststart", str(tmp)], stdin=subprocess.PIPE)
    r = subprocess.Popen(["ffmpeg", "-v", "error", "-i", str(src), "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    i = 0
    while len(b := r.stdout.read(W * H * 3)) == W * H * 3:
        p.stdin.write(fixed[i].tobytes() if i in fixed else b)
        i += 1
    r.wait()
    p.stdin.close()
    assert p.wait() == 0
    tmp.replace(dst)


if __name__ == "__main__":
    v = sys.argv[1]
    if len(sys.argv) > 3:
        patch(v, sys.argv[2], sys.argv[3])
    else:
        full = HERE / f"../../../media/{SLUG}/{SLUG}-{v}.mp4"
        patch(v, full, full)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(full), "-c:v", "libx264", "-crf", "23", "-preset", "slow", "-c:a", "copy",
                        "-movflags", "+faststart", str(full).replace(".mp4", "-phone.mp4")], check=True)
