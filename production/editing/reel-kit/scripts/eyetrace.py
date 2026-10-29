"""Eye-trace check: does every cut start where the viewer was already looking?

  python3 -I eyetrace.py VIDEO [OUT.jpg] [--cuts 4.4,7.16,...] [--thr 0.3]

The rule (from the @liveairprod reference, content-bank/references/2026-10-29-liveairprod-eye-trace.md): the new
shot's point of focus must sit where the old shot's point of focus was on its last frame. Then the cut is
"invisible": the eye doesn't have to search, so nobody feels the jump and nobody swipes.

For each hard cut it finds the point of focus on the last frame before and the first frame after:
  - a face -> the point between the eyes (OpenCV Haar, largest face)
  - no face -> the centre of the strongest detail (top 4% edge energy: text, a glove, a hand)
and prints the jump as % of the frame height. <= 15% clean, <= 30% ok, more = the eye has to hunt.
OUT.jpg: before | after pairs with both points drawn (red = before, green = after).
Needs: ffmpeg, numpy, "opencv-python-headless<5" (5.x dropped the Haar face detector).
"""
import argparse
import subprocess
import sys

import cv2
import numpy as np

W, H = 360, 640
CASCADE = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")


def frame(video, t):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{max(0, t):.3f}", "-i", video, "-frames:v", "1",
                          "-vf", f"scale={W}:{H}", "-f", "rawvideo", "-pix_fmt", "bgr24", "-"], capture_output=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(H, W, 3).copy() if len(raw) == W * H * 3 else None


def cuts(video, thr):
    out = subprocess.run(["ffmpeg", "-v", "info", "-i", video, "-vf", f"select='gt(scene,{thr})',showinfo", "-an", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    return [float(l.split("pts_time:")[1].split()[0]) for l in out.splitlines() if "pts_time:" in l]


def focus(img):
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    faces = CASCADE.detectMultiScale(g, 1.1, 6, minSize=(50, 50))
    if len(faces):
        x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
        return (x + w / 2, y + 0.4 * h), "face"
    e = cv2.magnitude(cv2.Sobel(g, cv2.CV_32F, 1, 0), cv2.Sobel(g, cv2.CV_32F, 0, 1))
    e = cv2.GaussianBlur(e, (31, 31), 0)
    m = e >= np.quantile(e, 0.96)
    ys, xs = np.nonzero(m)
    return (float(xs.mean()), float(ys.mean())), "detail"


def first_seen(video, t, wait=0.8):
    """First frame after the cut that shows something: a white quote card is blank until its first word lands,
    and that first word is where the eye goes."""
    for dt in np.arange(0.04, wait, 0.08):
        f = frame(video, t + dt)
        if f is None or cv2.cvtColor(f, cv2.COLOR_BGR2GRAY).std() > 12:
            return f
    return frame(video, t + 0.04)


def crop_x(src, t, crop_w, target_x, src_w=None):
    """Crop for a cutaway (fight tape, b-roll): the x of a crop_w-wide window so the action in `src` at second `t`
    lands on target_x (0-1 of the output width), e.g. Matteo's eyes on the last face frame before the cut.
    Action = centre of motion between t and t+0.2 s (the fighters, not the crowd), clamped to the frame.
    Use in make_broll.py: x = eyetrace.crop_x(SRC, a, w, 0.5)."""
    if src_w is None:
        src_w = int(subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width",
                                    "-of", "csv=p=0", src], capture_output=True, text=True).stdout.split()[0])
    a, b = frame(src, t), frame(src, t + 0.2)
    if a is None or b is None:
        return max(0, (src_w - crop_w) // 2)
    m = cv2.GaussianBlur(cv2.absdiff(cv2.cvtColor(a, cv2.COLOR_BGR2GRAY), cv2.cvtColor(b, cv2.COLOR_BGR2GRAY)).astype(np.float32), (41, 41), 0)
    col = m.sum(0)
    cx = float((col * np.arange(W)).sum() / max(col.sum(), 1e-6)) / W * src_w   # action centre, source px
    return int(np.clip(cx - target_x * crop_w, 0, src_w - crop_w))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video"); ap.add_argument("out", nargs="?")
    ap.add_argument("--cuts", help="comma-separated cut times (default: detect)")
    ap.add_argument("--thr", type=float, default=0.3)
    a = ap.parse_args()
    ts = [float(x) for x in a.cuts.split(",")] if a.cuts else cuts(a.video, a.thr)
    rows, jumps = [], []
    for t in ts:
        b, f = frame(a.video, t - 0.08), first_seen(a.video, t)
        if b is None or f is None:
            continue
        (pb, kb), (pf, kf) = focus(b), focus(f)
        d = np.hypot(pb[0] - pf[0], pb[1] - pf[1]) / H * 100
        jumps.append(d)
        tag = "clean" if d <= 15 else "ok" if d <= 30 else "HUNT"
        print(f"{t:7.2f}s  {kb:6} -> {kf:6}  jump {d:5.1f}%  {tag}")
        for img in (b, f):
            cv2.circle(img, tuple(int(v) for v in pb), 14, (0, 0, 255), 4)
            cv2.circle(img, tuple(int(v) for v in pf), 14, (0, 255, 0), 4)
        cv2.putText(b, f"{t:.2f}s {d:.0f}%", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2)
        rows.append(np.hstack([b, np.full((H, 6, 3), 255, np.uint8), f]))
    if jumps:
        print(f"cuts {len(jumps)}  median jump {np.median(jumps):.1f}%  hunts {sum(j > 30 for j in jumps)}")
    if a.out and rows:
        per = 4
        grid = [np.hstack(rows[i:i + per] + [np.zeros_like(rows[0])] * (per - len(rows[i:i + per]))) for i in range(0, len(rows), per)]
        cv2.imwrite(a.out, np.vstack(grid), [cv2.IMWRITE_JPEG_QUALITY, 80])
    return 0


if __name__ == "__main__":
    sys.exit(main())
