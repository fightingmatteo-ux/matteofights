#!/usr/bin/env python3
"""Turn a video into something Claude can "watch": frames, a contact sheet, metadata, transcript.

    python3 tools/video/watch.py VIDEO OUTDIR [--every 1.0] [--width 480] [--no-transcript]

Writes to OUTDIR:
  meta.json        duration, resolution, fps, audio
  frames/          one frame every --every seconds (t0000.0.jpg ...)
  scenes/          one frame per hard cut (shows the edit rhythm)
  contact.jpg      grid of the timed frames, numbered, for a one-glance read
  cuts.txt         timestamps of every hard cut
  transcript.txt   speech with timestamps (needs faster-whisper + model download)
  words.json       word-level timestamps (for edits and subtitle timing)
"""
import argparse, json, math, re, shutil, subprocess, sys
from pathlib import Path


# Windows ffmpeg has no fontconfig default, so drawtext needs an explicit font file there.
_WINFONT = Path("C:/Windows/Fonts/arial.ttf")
FONT = f"fontfile='{_WINFONT.as_posix().replace(':', chr(92) + ':')}':" if _WINFONT.exists() else ""


def run(cmd, **kw):
    return subprocess.run(cmd, check=True, capture_output=True, text=True, **kw)


def run_bytes(cmd):
    return subprocess.run(cmd, check=True, capture_output=True).stdout


def probe(video):
    out = run(["ffprobe", "-v", "error", "-print_format", "json", "-show_format", "-show_streams", str(video)]).stdout
    data = json.loads(out)
    v = next((s for s in data["streams"] if s["codec_type"] == "video"), {})
    a = next((s for s in data["streams"] if s["codec_type"] == "audio"), None)
    num, den = (v.get("avg_frame_rate") or "0/1").split("/")
    return {
        "file": Path(video).name,
        "duration_sec": round(float(data["format"].get("duration", 0)), 2),
        "width": v.get("width"),
        "height": v.get("height"),
        "fps": round(float(num) / float(den), 2) if float(den) else None,
        "has_audio": a is not None,
    }


def timed_frames(video, outdir, every, width):
    d = outdir / "frames"
    shutil.rmtree(d, ignore_errors=True)
    d.mkdir(parents=True)
    run(["ffmpeg", "-v", "error", "-i", str(video), "-vf", f"fps=1/{every},scale={width}:-2",
         "-q:v", "4", str(d / "f%04d.jpg")])
    frames = sorted(d.glob("f*.jpg"))
    for i, f in enumerate(frames):
        f.rename(d / f"t{i * every:06.1f}.jpg")
    return sorted(d.glob("t*.jpg"))


def scene_cuts(video, outdir, width, threshold=0.3):
    d = outdir / "scenes"
    shutil.rmtree(d, ignore_errors=True)
    d.mkdir(parents=True)
    res = subprocess.run(
        ["ffmpeg", "-v", "info", "-i", str(video), "-vf",
         f"select='gt(scene,{threshold})',showinfo,scale={width}:-2", "-vsync", "vfr", "-q:v", "4",
         str(d / "s%04d.jpg")],
        capture_output=True, text=True)
    times = [float(t) for t in re.findall(r"pts_time:([\d.]+)", res.stderr)]
    for f, t in zip(sorted(d.glob("s*.jpg")), times):
        f.rename(d / f"cut_{t:07.2f}.jpg")
    return times


def contact_sheet(frames, outdir, every):
    if not frames:
        return
    cols = 6 if len(frames) > 12 else 4
    rows = math.ceil(len(frames) / cols)
    # Number each frame with its timestamp, then tile.
    tmp = outdir / "_labeled"
    shutil.rmtree(tmp, ignore_errors=True)
    tmp.mkdir()
    for i, f in enumerate(frames):
        label = f"{i * every:.0f}s"
        run(["ffmpeg", "-v", "error", "-i", str(f), "-vf",
             f"scale=240:-2,drawtext={FONT}text='{label}':x=8:y=8:fontsize=28:fontcolor=white:box=1:boxcolor=black@0.7",
             str(tmp / f"l{i:04d}.jpg")])
    run(["ffmpeg", "-v", "error", "-y", "-i", str(tmp / "l%04d.jpg"), "-vf",
         f"tile={cols}x{rows}:padding=4:color=black", "-frames:v", "1", "-q:v", "3", str(outdir / "contact.jpg")])
    shutil.rmtree(tmp)


def transcribe(video, outdir):
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        return "skipped: pip install faster-whisper"
    try:
        model = WhisperModel("small", device="cpu", compute_type="int8")
        # decode with ffmpeg (PyAV is broken on some Windows Pythons); 16 kHz mono float
        import numpy as np
        pcm = run_bytes(["ffmpeg", "-v", "error", "-i", str(video), "-f", "s16le", "-ac", "1", "-ar", "16000", "-"])
        audio = np.frombuffer(pcm, np.int16).astype(np.float32) / 32768
        segments, info = model.transcribe(audio, vad_filter=True, word_timestamps=True)
        segments = list(segments)
        (outdir / "words.json").write_text(json.dumps(
            [{"w": w.word.strip(), "s": round(w.start, 2), "e": round(w.end, 2)} for s in segments for w in s.words]))
        lines = [f"[{s.start:6.1f}-{s.end:6.1f}] {s.text.strip()}" for s in segments]
    except Exception as e:  # model download blocked, no audio, etc.
        return f"skipped: {type(e).__name__}: {e}"
    (outdir / "transcript.txt").write_text(encoding="utf-8", data=f"language: {info.language}\n" + "\n".join(lines) + "\n")
    return f"ok ({len(lines)} segments, {info.language})"


def main():
    p = argparse.ArgumentParser()
    p.add_argument("video")
    p.add_argument("outdir")
    p.add_argument("--every", type=float, default=1.0, help="seconds between timed frames")
    p.add_argument("--width", type=int, default=480)
    p.add_argument("--no-transcript", action="store_true")
    a = p.parse_args()
    out = Path(a.outdir)
    out.mkdir(parents=True, exist_ok=True)

    meta = probe(a.video)
    frames = timed_frames(a.video, out, a.every, a.width)
    cuts = scene_cuts(a.video, out, a.width)
    contact_sheet(frames, out, a.every)
    (out / "cuts.txt").write_text("\n".join(f"{t:.2f}" for t in cuts) + "\n")
    meta["hard_cuts"] = len(cuts)
    if cuts and meta["duration_sec"]:
        meta["avg_shot_sec"] = round(meta["duration_sec"] / (len(cuts) + 1), 2)
    meta["transcript"] = "skipped" if a.no_transcript or not meta["has_audio"] else transcribe(a.video, out)
    (out / "meta.json").write_text(json.dumps(meta, indent=2) + "\n")
    print(json.dumps(meta, indent=2))


if __name__ == "__main__":
    sys.exit(main())
