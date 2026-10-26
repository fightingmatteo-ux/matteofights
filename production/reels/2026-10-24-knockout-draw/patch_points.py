"""Patch only the POINTS keyword inside a finished render, no re-render (Matteo 2026-10-26: the decode effect faded
out before it locked in, so viewers saw "p30x$/ ... pointf").

    python patch_points.py A          # ../../../media/<slug>/<slug>-A.mp4 in place, then rebuilds -phone.mp4
    python patch_points.py A IN OUT   # one file (local test)

points.png / points-back.png: the keyword rendered from this reel's own CSS (front 176 px, back 220 px, red, same
shadow), transparent 1080x1920. A and B have it in the back layer (behind Matteo), C in front.
Per frame where the scrambled word shows: old glyphs + shadow are replaced by the clean frame just before the word
appeared, then the right word goes on top, aligned on the letters the decode had already locked (p, o, i, n),
kept behind Matteo for the back layer, faded on the last frame with the phrase.
"""
import subprocess
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
SLUG = HERE.name
W, H = 1080, 1920
WINDOW = {"A": 11.0, "B": 13.0, "C": 8.8}  # 2 s search window start (s)
BACK = {"A": True, "B": True, "C": False}


def red(f):
    f = f.astype(np.int16)
    return (f[..., 0] > 150) & (f[..., 1] < 110) & (f[..., 2] < 120) & (f[..., 0] - f[..., 1] > 90)


def grow(m, r):
    out = m.copy()
    for dy in range(-r, r + 1, 2):
        for dx in range(-r, r + 1, 2):
            out |= np.roll(np.roll(m, dy, 0), dx, 1)
    return out


def soften(a, r):
    k = np.ones(2 * r + 1) / (2 * r + 1)
    a = np.apply_along_axis(lambda x: np.convolve(x, k, "same"), 0, a)
    return np.apply_along_axis(lambda x: np.convolve(x, k, "same"), 1, a)


def png_rgba(path):
    b = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-f", "rawvideo", "-pix_fmt", "rgba", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(b, np.uint8).reshape(H, W, 4).astype(np.float32)


def read_window(path, t, d):
    b = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.3f}", "-i", str(path), "-t", f"{d:.3f}", "-f", "rawvideo",
                        "-pix_fmt", "rgb24", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(b, np.uint8).reshape(-1, H, W, 3)


def fps(path):
    n, d = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=r_frame_rate",
                           "-of", "csv=p=0", str(path)], capture_output=True, text=True, check=True).stdout.strip().split("/")
    return float(n) / float(d)


def align(word_m, frame_m):
    """Offset (dy, dx) putting the word's p-o-i-n onto the frame's locked letters."""
    ys, xs = np.nonzero(word_m)
    left = word_m.copy()
    left[:, int(xs.min() + (xs.max() - xs.min()) * 0.6):] = False  # p o i n
    fy, fx = np.nonzero(frame_m)
    best, off = -1, (0, 0)
    for dy in range(fy.min() - ys.min() - 40, fy.min() - ys.min() + 41, 2):
        for dx in range(fx.min() - xs.min() - 40, fx.min() - xs.min() + 41, 2):
            s = (np.roll(np.roll(left, dy, 0), dx, 1) & frame_m).sum()
            if s > best:
                best, off = s, (dy, dx)
    oy, ox = off
    for dy in (oy - 1, oy, oy + 1):  # 1 px refine
        for dx in (ox - 1, ox, ox + 1):
            s = (np.roll(np.roll(left, dy, 0), dx, 1) & frame_m).sum()
            if s > best:
                best, off = s, (dy, dx)
    return off


def patch(v, src, dst):
    rate = fps(src)
    a0 = round(WINDOW[v] * rate)
    F = {a0 + i: f for i, f in enumerate(read_window(src, a0 / rate, 2.0))}
    counts = np.array([red(F[i][300:800]).sum() for i in sorted(F)])
    on = [a0 + i for i, c in enumerate(counts) if c > 800]
    first, last = on[0], on[-1]
    full = np.median([counts[i - a0] for i in on[:-1]])
    word = png_rgba(HERE / ("points-back.png" if BACK[v] else "points.png"))
    dy, dx = align(red(word[..., :3].astype(np.uint8)) & (word[..., 3] > 128), red(F[last - 2]))
    word = np.roll(np.roll(word, dy, 0), dx, 1)
    wa = word[..., 3:] / 255.0
    plate = F[first - 1].astype(np.float32)
    wall = np.median(plate[350:800].reshape(-1, 3), axis=0)
    fg = (np.abs(plate - wall).sum(-1) > 90) if BACK[v] else np.zeros((H, W), bool)  # Matteo in front of the back layer
    fg = soften(fg.astype(np.float32), 3)[..., None]
    zone = grow((wa[..., 0] > 0.05) | grow(red(F[last - 2]), 10), 30)  # the word and its shadow...
    zone[:np.nonzero(red(word[..., :3].astype(np.uint8)) & (wa[..., 0] > 0.5))[0].min() - 6] = False  # ...not the lead line
    post = F[last + 10].astype(np.float32)  # word gone
    energy = lambda f: np.abs(f.astype(np.float32) - post)[zone].mean()
    ref = energy(F[(first + last) // 2])
    run = list(on) + [i for i in range(last + 1, last + 7) if energy(F[i]) / ref > 0.12]
    fixed = {}
    for i in run:
        f = F[i].astype(np.float32)
        old = grow(np.abs(f - plate).sum(-1) > 24, 6) & (zone | grow(red(F[i]), 16))  # + this frame's own scrambled glyphs
        m = soften(old.astype(np.float32), 4)[..., None]
        base = f * (1 - m) + plate * m
        k = min(1.0, energy(F[i]) / ref)  # the phrase dissolves over the last frames
        a = wa * k * (1 - fg)
        out = base * (1 - a) + word[..., :3] * a
        if BACK[v]:
            out = out * (1 - fg) + f * fg  # keep Matteo exactly as rendered
        fixed[i] = np.clip(out, 0, 255).astype(np.uint8)
    last = run[-1]
    print(f"{v}: patched frames {first}-{last} ({(last - first + 1) / rate:.2f} s), word offset {dy},{dx}")
    tmp = Path(str(dst) + ".tmp.mp4")
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(rate),
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
