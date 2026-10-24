"""Still frames for carousels, pulled from the training clips in Drive (runs in GitHub Actions: rclone "gdrive").

    python3 -P tools/carousel/frames.py CLIP_ID [CLIP_ID ...] [--per-clip 4]

For each clip: downloads it by Drive id, looks at candidate moments (the graded good moments in
production/listicles/moments.json first, then evenly spread), keeps the sharpest frames at least 3 s apart,
rotated per clips.json, as production/carousels/frames/<clip id>/<seconds>.jpg (long edge 1440, q88).
production/carousels/frames/index.json lists them per clip with a sharpness score. Claude looks at them to pick
the photo for each slide; render.py takes a frame path or any photo Matteo provides.
"""
import argparse, json, subprocess, sys
from pathlib import Path

from PIL import Image, ImageFilter, ImageStat

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "production" / "carousels" / "frames"
CLIPS = ROOT / "production" / "listicles" / "clips.json"
MOMENTS = ROOT / "production" / "listicles" / "moments.json"
WORK = ROOT / "work" / "carousel-frames"
LONG_EDGE = 1440


def run(*cmd):
    return subprocess.run(cmd, check=True, capture_output=True, text=True).stdout


def duration(path):
    return float(run("ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)))


def grab(path, t, rotate, dest):
    turn = {90: ["-vf", "transpose=1"], 180: ["-vf", "transpose=1,transpose=1"], 270: ["-vf", "transpose=2"]}
    run("ffmpeg", "-v", "error", "-y", "-ss", f"{t:.2f}", "-i", str(path), "-frames:v", "1",
        *turn.get(rotate, []), "-q:v", "2", str(dest))
    im = Image.open(dest).convert("RGB")
    im.thumbnail((LONG_EDGE, LONG_EDGE))
    return im


def sharpness(im):
    small = im.convert("L").resize((480, round(480 * im.height / im.width)))
    return round(ImageStat.Stat(small.filter(ImageFilter.FIND_EDGES)).var[0], 1)


def candidates(clip_id, dur):
    good = json.loads(MOMENTS.read_text(encoding="utf-8")).get(clip_id, {}).get("good", [])
    near = [t + d for t in good for d in (0.5, 2.0, 4.0, 6.0)]
    spread = [dur * i / 13 for i in range(1, 13)]
    return [t for t in near + spread if 1.0 <= t <= dur - 1.0]


def frames_for(clip_id, per_clip, cat):
    WORK.mkdir(parents=True, exist_ok=True)
    local = WORK / clip_id
    if not local.exists():
        run("rclone", "backend", "copyid", "gdrive:", clip_id, str(local))
    rotate = cat.get(clip_id, {}).get("rotate_fix", 0)
    scored = []
    for t in candidates(clip_id, duration(local)):
        im = grab(local, t, rotate, WORK / "probe.jpg")
        scored.append((sharpness(im), round(t, 1), im))
    out_dir = OUT / clip_id
    out_dir.mkdir(parents=True, exist_ok=True)
    kept = []
    for score, t, im in sorted(scored, key=lambda s: -s[0]):
        if all(abs(t - k["t"]) >= 3 for k in kept):
            name = f"{t:06.1f}.jpg"
            im.save(out_dir / name, quality=88)
            kept.append({"t": t, "file": f"production/carousels/frames/{clip_id}/{name}", "sharpness": score,
                         "size": list(im.size)})
        if len(kept) == per_clip:
            break
    local.unlink()
    return {"name": cat.get(clip_id, {}).get("name", ""), "frames": sorted(kept, key=lambda k: k["t"])}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("clips", nargs="+")
    p.add_argument("--per-clip", type=int, default=4)
    a = p.parse_args()
    cat = json.loads(CLIPS.read_text(encoding="utf-8"))
    index_path = OUT / "index.json"
    OUT.mkdir(parents=True, exist_ok=True)
    index = json.loads(index_path.read_text(encoding="utf-8")) if index_path.exists() else {}
    failed = []
    for cid in [c.strip() for raw in a.clips for c in raw.split(",") if c.strip()]:
        try:
            index[cid] = frames_for(cid, a.per_clip, cat)
            print(f"{cid}: {len(index[cid]['frames'])} frames")
        except subprocess.CalledProcessError as e:
            print(f"{cid}: failed: {e.stderr.strip()[-300:]}")
            failed.append(cid)
    index_path.write_text(json.dumps(index, indent=2) + "\n", encoding="utf-8")
    if failed:
        sys.exit(f"failed: {', '.join(failed)}")


if __name__ == "__main__":
    main()
