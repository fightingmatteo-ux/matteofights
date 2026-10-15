"""Technique score for a stretch of training footage, from body pose (MediaPipe, free, runs on the CPU).

    python -P tools/listicle/technique.py <clip> <start s> [seconds]     # prints the score + parts

Motion alone can't tell skilled boxing from messing around. This measures what a coach looks at, on ~6 frames
per second (rubric: context/boxing-technique.md):
  in_frame   the fighter is detected and big enough (body >= ~40% of the frame height), not cut off
  guard      between strikes both hands are up by the face (wrists above the shoulders' line, near the chin)
  strikes    arms actually reach full extension (elbow > 155 deg) at shoulder height: punches thrown, not pawing
  stance     feet wider than the shoulders and not crossed; head stays between the feet (balanced)
  work       hands and feet keep moving (not resting); no walking up to the camera (body growing fast)
score 0-10 = weighted mix. Used to rank candidate moments on the moment sheets and as the fallback when a clip
has no coach-graded moment yet (render.graded_start).
"""
import math, subprocess, sys, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODEL = ROOT / "media" / "models" / "pose_landmarker_full.task"
MODEL_URL = ("https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_full/float16/latest/"
             "pose_landmarker_full.task")
FPS, W = 6, 360
# MediaPipe pose landmark ids
NOSE, LSH, RSH, LEL, REL, LWR, RWR, LHIP, RHIP, LANK, RANK = 0, 11, 12, 13, 14, 15, 16, 23, 24, 27, 28


def _model():
    if not MODEL.exists():
        MODEL.parent.mkdir(parents=True, exist_ok=True)
        urllib.request.urlretrieve(MODEL_URL, MODEL)
    return MODEL


def _frames(clip, start, seconds):
    """RGB frames at FPS from start, letterboxed into a fixed W x H (9:16) canvas: (list of bytes, w, h)."""
    h = W * 16 // 9
    out = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{start:.2f}", "-t", f"{seconds:.2f}", "-i", str(clip),
                          "-vf", f"fps={FPS},scale={W}:{h}:force_original_aspect_ratio=decrease,pad={W}:{h}:(ow-iw)/2:(oh-ih)/2",
                          "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
    size = W * h * 3
    return [out[i:i + size] for i in range(0, len(out) - size + 1, size)], W, h


def _angle(a, b, c):
    ab, cb = (a.x - b.x, a.y - b.y), (c.x - b.x, c.y - b.y)
    n = math.hypot(*ab) * math.hypot(*cb)
    return math.degrees(math.acos(max(-1, min(1, (ab[0] * cb[0] + ab[1] * cb[1]) / n)))) if n else 0


def score(clip, start, seconds=8.5):
    import mediapipe as mp
    from mediapipe.tasks import python as mpt
    from mediapipe.tasks.python import vision
    frames, w, h = _frames(clip, start, seconds)
    opts = vision.PoseLandmarkerOptions(base_options=mpt.BaseOptions(model_asset_path=str(_model())),
                                        running_mode=vision.RunningMode.VIDEO, num_poses=1,
                                        min_pose_detection_confidence=0.5, min_tracking_confidence=0.5)
    poses = []
    with vision.PoseLandmarker.create_from_options(opts) as lm:
        for k, buf in enumerate(frames):
            img = mp.Image(image_format=mp.ImageFormat.SRGB, data=__import__("numpy").frombuffer(buf, "uint8").reshape(h, w, 3))
            r = lm.detect_for_video(img, int(k * 1000 / FPS))
            poses.append(r.pose_landmarks[0] if r.pose_landmarks else None)
    n = len(poses) or 1
    seen = [p for p in poses if p]
    if len(seen) < n * 0.3:
        return {"score": 0.0, "in_frame": round(len(seen) / n, 2), "why": "fighter not visible"}

    heights, guard_ok, guard_n, ext, stance_ok, balance_ok, moves = [], 0, 0, 0, 0, 0, []
    prev = None
    for p in seen:
        top = min(p[NOSE].y, p[LSH].y)
        foot = max(p[LANK].y, p[RANK].y)
        heights.append(max(0.0, foot - top + 0.08))       # + head above the nose
        sh_y = (p[LSH].y + p[RSH].y) / 2
        sh_w = abs(p[LSH].x - p[RSH].x) or 0.01
        el = (_angle(p[LSH], p[LEL], p[LWR]), _angle(p[RSH], p[REL], p[RWR]))
        striking = [a > 155 and abs(wr.y - sh_y) < 0.12 for a, wr in zip(el, (p[LWR], p[RWR]))]
        ext += any(striking)
        # guard: the non-striking hand(s) up by the face
        for s, wr in zip(striking, (p[LWR], p[RWR])):
            if not s:
                guard_n += 1
                guard_ok += wr.y < sh_y + 0.02 and abs(wr.x - p[NOSE].x) < 2.2 * sh_w
        feet = abs(p[LANK].x - p[RANK].x)
        stance_ok += 1.0 <= feet / sh_w <= 3.2
        lo, hi = sorted((p[LANK].x, p[RANK].x))
        balance_ok += lo - 0.25 * sh_w <= p[NOSE].x <= hi + 0.25 * sh_w
        if prev:
            moves.append(sum(abs(p[i].x - prev[i].x) + abs(p[i].y - prev[i].y) for i in (LWR, RWR, LANK, RANK)))
        prev = p

    m = len(seen)
    body = sorted(heights)[len(heights) // 2]
    size_s = max(0.0, min(1.0, (body - 0.25) / 0.35))            # 0 at 25% of frame height, 1 at 60%+
    in_frame = (m / n) * size_s
    guard = guard_ok / guard_n if guard_n else 0.0
    strikes = min(1.0, (ext / m) / 0.18)                           # ~1 extended strike frame in 6 = busy
    stance = 0.5 * stance_ok / m + 0.5 * balance_ok / m
    act = sorted(moves)[len(moves) // 2] if moves else 0
    work = max(0.0, min(1.0, act / 0.06))
    tail = heights[-max(2, m // 4):]
    approach = max(tail) / max(1e-3, body)                         # body suddenly much bigger at the end
    s = 10 * (0.20 * in_frame + 0.30 * guard + 0.20 * strikes + 0.15 * stance + 0.15 * work)
    # From one phone angle these numbers are too noisy to rank good technique; they VETO the obvious failures
    # and Claude grades the rest against the rubric (context/boxing-technique.md).
    veto = ("not visible enough" if m / n < 0.5 else "fighter too small" if body < 0.33 else
            "walks up to the camera" if approach > 1.3 else "hands down most of the time" if guard < 0.2 else
            "barely moving" if work < 0.25 else None)
    return {"score": round(s, 1), "veto": veto, "in_frame": round(in_frame, 2), "guard": round(guard, 2),
            "strikes": round(strikes, 2), "stance": round(stance, 2), "work": round(work, 2), "body": round(body, 2),
            "approach": round(approach, 2)}


if __name__ == "__main__":
    a = sys.argv[1:]
    print(score(a[0], float(a[1]), float(a[2]) if len(a) > 2 else 8.5))
