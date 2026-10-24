"""Catch the HyperFrames cold-start glitch: black or out-of-step frames in a render's first second.

  python3 -I check_render.py <render.mp4> <aroll.mp4> [seconds=1.5]

Seen 2026-10-20 on the first cloud render of a session: frames 0 and 2 black, frames 1-5 at the wrong zoom, audio
fine. The same composition re-rendered clean. Frame 0 is the thumbnail, so always run this; on FAIL just render again.
Compares frame-to-frame motion of the render against the A-roll: overlays barely change it, a glitch spikes it.
"""
import subprocess
import sys

import numpy as np


def frames(path, secs):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-t", str(secs), "-i", path, "-vf", "scale=108:192,format=gray",
                          "-f", "rawvideo", "-"], capture_output=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(-1, 192, 108).astype(float)


render, aroll = sys.argv[1], sys.argv[2]
secs = float(sys.argv[3]) if len(sys.argv) > 3 else 1.5
r, a = frames(render, secs), frames(aroll, secs)
n = min(len(r), len(a))
black = [i for i in range(n) if r[i].mean() < 12]
dr = np.abs(np.diff(r[:n], axis=0)).mean((1, 2))
da = np.abs(np.diff(a[:n], axis=0)).mean((1, 2))
jumps = [i + 1 for i in range(n - 1) if dr[i] > da[i] + 4]
if len(sys.argv) > 4 and sys.argv[4] == "black":  # the reel opens on b-roll/graphics, not the A-roll: only black frames count
    jumps = []
if black or jumps:
    print(f"FAIL {render}: black frames {black}, jumps at frames {jumps}. Render again.")
    sys.exit(1)
print(f"OK {render}: first {n} frames clean")
