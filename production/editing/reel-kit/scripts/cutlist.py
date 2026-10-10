"""Tighten a talking-head take: turn Whisper words into a frame-snapped cut list.

Every gap between kept words longer than --max-gap is removed. Cut points are
refined against the audio envelope (Whisper pads word edges), then padded and
snapped to the frame grid.

Usage:
  python -P cutlist.py <media> <words.json> <out.json>
         [--drop "phrase to remove" ...] [--end-after "word or phrase"] [--max-gap 0.28]

Writes {"segments": [[in, out], ...], "duration": total} in source seconds.
"""
import argparse
import json
import re
import subprocess

import numpy as np

ap = argparse.ArgumentParser()
ap.add_argument("media")
ap.add_argument("words")
ap.add_argument("out")
ap.add_argument("--drop", action="append", default=[], help="phrase to remove (first match)")
ap.add_argument("--end-after", default=None, help="last kept phrase (last match)")
ap.add_argument("--max-gap", type=float, default=0.28)
ap.add_argument("--pre", type=float, default=0.06, help="pad before speech onset")
ap.add_argument("--post", type=float, default=0.12, help="pad after speech offset")
ap.add_argument("--fps", type=int, default=30)
a = ap.parse_args()

words = json.load(open(a.words, encoding="utf-8"))
norm = lambda t: re.sub(r"[^\w']", "", t).lower()
toks = [norm(w["text"]) for w in words]


def find(phrase, last=False):
    p = [norm(x) for x in phrase.split()]
    hits = [i for i in range(len(toks) - len(p) + 1) if toks[i:i + len(p)] == p]
    if not hits:
        raise SystemExit(f"phrase not found: {phrase!r}")
    i = hits[-1] if last else hits[0]
    return i, i + len(p)


keep = [True] * len(words)
for ph in a.drop:
    s, e = find(ph)
    for i in range(s, e):
        keep[i] = False
if a.end_after:
    _, e = find(a.end_after, last=True)
    for i in range(e, len(words)):
        keep[i] = False

# audio envelope (10 ms hop)
sr, hop = 16000, 160
pcm = subprocess.run(["ffmpeg", "-v", "error", "-i", a.media, "-ac", "1", "-ar", str(sr), "-f", "f32le", "-"],
                     capture_output=True, check=True).stdout
x = np.frombuffer(pcm, np.float32)
n = len(x) // hop
env = 20 * np.log10(np.sqrt(np.mean(x[: n * hop].reshape(n, hop) ** 2, axis=1)) + 1e-9)
floor = np.percentile(env, 10)
thr = floor + 15  # speech = 15 dB over the room floor
fr = lambda t: min(n - 1, max(0, int(t * 100)))


def speech_end(t, limit):
    """Last loud frame at/after word end t, searching up to limit."""
    i, j = fr(t - 0.15), fr(limit)
    loud = np.where(env[i:j] > thr)[0]
    if not len(loud):
        return t
    # walk forward while speech continues without a 120 ms hole
    k, last = 0, loud[0]
    for v in loud:
        if v - last > 12:
            break
        last = v
    return (i + last) / 100 + 0.01


def speech_start(t, limit):
    """First loud frame of the run ending near word start t, searching back to limit."""
    i, j = fr(limit), fr(t + 0.25)
    loud = np.where(env[i:j] > thr)[0]
    if not len(loud):
        return t
    first = loud[-1]
    for v in reversed(loud):
        if first - v > 12:
            break
        first = v
    return (i + first) / 100


segs = []
cur = None
prev = None
for i, w in enumerate(words):
    if not keep[i]:
        continue
    if cur is None:
        cur = [w["start"], w["end"]]
    elif w["start"] - prev["end"] > a.max_gap or not keep[i - 1]:
        end = speech_end(prev["end"], min(w["start"], prev["end"] + 0.6))
        start = speech_start(w["start"], max(end, w["start"] - 0.8))
        if start - end > a.max_gap or not keep[i - 1]:
            cur[1] = end
            segs.append(cur)
            cur = [start, w["end"]]
        else:
            cur[1] = w["end"]
    else:
        cur[1] = w["end"]
    prev = w
cur[1] = speech_end(prev["end"], prev["end"] + 0.5)
segs.append(cur)

snap = lambda t: round(t * a.fps) / a.fps
out = []
for s, e in segs:
    s, e = snap(max(0, s - a.pre)), snap(e + a.post)
    if out and s <= out[-1][1]:
        out[-1][1] = e
    else:
        out.append([round(s, 4), round(e, 4)])
total = sum(e - s for s, e in out)
json.dump({"segments": out, "duration": round(total, 3)}, open(a.out, "w"), indent=1)
src = words[-1]["end"]
print(f"{len(out)} segments, {total:.2f}s kept (source speech span {src:.2f}s)")
for s, e in out:
    print(f"  {s:7.3f} -> {e:7.3f}  ({e - s:.2f}s)")
