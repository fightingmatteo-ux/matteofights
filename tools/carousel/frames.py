"""Still frames for carousels, pulled from the training clips in Drive (runs in GitHub Actions: rclone "gdrive").

    python3 -P tools/carousel/frames.py CLIP_ID [CLIP_ID ...] [--per-clip 4]

For each clip: downloads it by Drive id, looks at candidate moments (the graded good moments in
production/listicles/moments.json first, then evenly spread), keeps the sharpest frames at least 3 s apart,
rotated per clips.json, as production/carousels/frames/<clip id>/<seconds>.jpg (long edge 1440, q88).
production/carousels/frames/index.json lists them per clip with a sharpness score. Claude looks at them to pick
the photo for each slide; render.py takes a frame path or any photo Matteo provides.
Next to every frame it cuts a 4 s seamless loop from that moment (VP9 webm, 720 wide, no sound, the last 0.5 s
crossfades into the first frame) as work/carousel-frames/loops/carousel-loop-<clip id>-<seconds>.webm; the workflow
uploads those to the media release (never git) and the cover slide plays one as its moving detail.
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


def loop(path, t, rotate, dest, seconds=4.0, fade=0.5):
    turn = {90: "transpose=1,", 180: "transpose=1,transpose=1,", 270: "transpose=2,"}.get(rotate, "")
    run("ffmpeg", "-v", "error", "-y", "-ss", f"{t:.2f}", "-t", f"{seconds + fade:.2f}", "-i", str(path), "-filter_complex",
        f"[0:v]{turn}scale=720:-2,fps=30,split[a][b];[a]trim={fade}:{seconds + fade},setpts=PTS-STARTPTS[m];"
        f"[b]trim=0:{fade},setpts=PTS-STARTPTS[h];[m][h]xfade=transition=fade:duration={fade}:offset={seconds - fade},format=yuv420p",
        "-c:v", "libvpx-vp9", "-b:v", "0", "-crf", "36", "-row-mt", "1", "-an", str(dest))


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
    loops = WORK / "loops"
    loops.mkdir(exist_ok=True)
    dur = duration(local)
    kept = []
    for score, t, im in sorted(scored, key=lambda s: -s[0]):
        if all(abs(t - k["t"]) >= 3 for k in kept):
            name = f"{t:06.1f}.jpg"
            im.save(out_dir / name, quality=88)
            lname = f"carousel-loop-{clip_id}-{t:06.1f}.webm"
            loop(local, min(t, max(0.0, dur - 4.6)), rotate, loops / lname)
            kept.append({"t": t, "file": f"production/carousels/frames/{clip_id}/{name}", "sharpness": score,
                         "size": list(im.size), "loop": lname})
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
