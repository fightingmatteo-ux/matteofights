"""Patch only the "came too early" replay inside a finished render, no full re-render (Matteo 2026-10-24: the
right hand sits out of frame there).

    python patch_replay.py A      # needs numpy; reads/writes ../../../media/<slug>/<slug>-A.mp4 (+ -phone.mp4)

Why it was out of frame: the replay clip sits inside the camera, which is still pushed in (~1.1x, from the bottom)
after the face stretch before it, so its right edge (where the punch is) is cut off. The fix:
1. cut the replay again with the punch further inside the frame (NEW_CROP), as a full 1080x1920 layer;
2. find the camera scale on the old clip, so old clip vs render differ only where the captions are;
3. per frame: captions from the render (difference mask), everything else from the new clip;
4. splice the patched seconds back in (frame exact), audio untouched, then the -phone copy.
"""
import json
import subprocess
import sys
from pathlib import Path

import numpy as np

V = sys.argv[1]
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SLUG = HERE.name
RENDER = ROOT / f"media/{SLUG}/{SLUG}-{V}.mp4"
SRC = ROOT / "media/first-fight/first-fight-2.mp4"
NEW_CROP = (150, 0, 330, 412)   # x, y, w, h in source px (4:5): the punch at ~87% instead of past the edge
W, H, FPS = 1080, 1920, 30

subprocess.run([sys.executable, "-P", str(HERE / "make_broll.py"), V], check=True, cwd=HERE)  # old crop + slots
slot = json.load(open(HERE / "work/broll.json"))["replay"]
f0, n = round(slot["start"] * FPS), round(slot["dur"] * FPS)
a = slot["src"][0]
old = HERE / "assets/media/b_replay.mp4"
new = HERE / "assets/media/b_replay2.mp4"
hold = 48.33 + 0.04 - a  # same freeze as make_broll (KO + 0.04)
x, y, w, h = NEW_CROP
fc = (f"[0:v]fps=30,trim=duration={hold:.3f},tpad=stop_mode=clone:stop_duration={slot['dur'] + 1:.3f},split[a][b];"
      f"[a]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=30:2,eq=brightness=-0.3:saturation=0.6[bg];"
      f"[b]crop={w}:{h}:{x}:{y},scale=1080:1350:force_original_aspect_ratio=increase:flags=lanczos,crop=1080:1350,"
      f"unsharp=5:5:0.8,eq=contrast=1.07:saturation=1.08[fg];[bg][fg]overlay=0:285,noise=alls=6:allf=t,format=yuv420p")
subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-ss", f"{a:.3f}", "-t", f"{slot['dur'] + 1:.3f}", "-i", str(SRC),
                "-filter_complex", fc, "-an", "-t", f"{slot['dur'] + 0.2:.3f}", "-c:v", "libx264", "-crf", "16", str(new)], check=True)


def reader(path, start_frame=0, count=None, ss=None):
    args = ["ffmpeg", "-v", "error"] + (["-ss", f"{ss:.3f}"] if ss is not None else []) + ["-i", str(path)]
    vf = f"select=gte(n\\,{start_frame})," if start_frame else ""
    args += ["-vf", vf + "format=rgb24", "-vsync", "0"] + (["-frames:v", str(count)] if count else []) + ["-f", "rawvideo", "-"]
    p = subprocess.Popen(args, stdout=subprocess.PIPE)
    while True:
        buf = p.stdout.read(W * H * 3)
        if len(buf) < W * H * 3:
            return
        yield np.frombuffer(buf, np.uint8).reshape(H, W, 3)


def cam(img, s):
    """the camera transform: scale s about the bottom centre (transform-origin 50% 100%)"""
    if abs(s - 1) < 1e-3:
        return img
    ys = np.clip(((np.arange(H) - H) / s + H).round().astype(int), 0, H - 1)
    xs = np.clip(((np.arange(W) - W / 2) / s + W / 2).round().astype(int), 0, W - 1)
    return img[ys][:, xs]


R = list(reader(RENDER, f0, n))
O = list(reader(old, 0, n))
N = list(reader(new, 0, n))
n = min(len(R), len(O), len(N))
# camera scale: fit on the middle frames, below the caption band
mid = range(n // 3, n - 2, max(1, n // 8))
err = lambda s: np.mean([np.abs(cam(O[i], s)[800:1500].astype(int) - R[i][800:1500].astype(int)).mean() for i in mid])  # noqa: E731
s = min(np.arange(1.0, 1.2, 0.005), key=err)
print(f"{V}: replay frames {f0}-{f0 + n}, camera scale {s:.3f} (err {err(s):.1f} vs {err(1.0):.1f} at 1.0)")

out = HERE / f"assets/media/patch_{V}.mp4"
enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                        "-i", "-", "-c:v", "libx264", "-crf", "14", "-pix_fmt", "yuv420p", str(out)], stdin=subprocess.PIPE)
k = np.ones(7)
WHIP = 6  # the clip whips in with a blur over the first frames: fade from the render to the new clip there
for i in range(n):
    r, o = R[i].astype(int), cam(O[i], s).astype(int)
    # caption glyphs only: differ from the old clip AND look like caption ink (white, or the red keyword),
    # inside the caption band at the top. Everything else comes from the new clip.
    white = r.min(2) > 175
    red = (r[..., 0] > 170) & (r[..., 1] < 95) & (r[..., 2] < 120)
    g = (np.abs(r - o).max(2) > 46) & (white | red)
    g[:240] = False
    g[820:] = False
    m = g.astype(float)
    for ax in (0, 1):                                                         # cover the glyph edges + a bit of shadow
        m = np.apply_along_axis(lambda row: np.convolve(row, k, "same"), ax, m)
    m = np.clip(m / 2, 0, 1)
    if i < WHIP:
        m = np.maximum(m, 1 - i / WHIP)
    m = m[..., None]
    enc.stdin.write((m * R[i] + (1 - m) * N[i]).astype(np.uint8).tobytes())
enc.stdin.close()
enc.wait()

tmp = RENDER.with_name(RENDER.stem + "-patched.mp4")
f1 = f0 + n
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(RENDER), "-i", str(out), "-filter_complex",
                f"[0:v]trim=start_frame=0:end_frame={f0},setpts=PTS-STARTPTS[a];[1:v]setpts=PTS-STARTPTS[b];"
                f"[0:v]trim=start_frame={f1},setpts=PTS-STARTPTS[c];[a][b][c]concat=n=3:v=1:a=0[v]",
                "-map", "[v]", "-map", "0:a", "-c:v", "libx264", "-crf", "16", "-preset", "medium", "-c:a", "copy",
                "-movflags", "+faststart", str(tmp)], check=True)
tmp.replace(RENDER)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(RENDER), "-c:v", "libx264", "-crf", "23", "-preset", "slow", "-c:a", "copy",
                "-movflags", "+faststart", str(RENDER.with_name(RENDER.stem + "-phone.mp4"))], check=True)
print(f"done: {RENDER} (+ -phone.mp4), frames {f0}-{f1} replaced")
