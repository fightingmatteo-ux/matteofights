#!/usr/bin/env python3
"""Cut a branded 9:16 reel from clips with ffmpeg.

    python3 tools/video/reel.py OUT.mp4 --clip a.mp4@0-3.5 --clip b.mov@12-15 \
        --hook "8 WAYS TO FIGHT LIKE A LEGEND WITHOUT A COACH" \
        --sub "You don't need a coach to fight like a legend." \
        [--music track.mp3] [--mute-clips] [--no-lut] [--end-text "READ DESCRIPTION"]

Each --clip is PATH, PATH@START-END or PATH@START (seconds). Clips are cropped to fill 1080x1920,
graded with the brand LUT, joined in order, then the hook (brand red, ALL CAPS) and subhook are
burned in at the top and the end card near the end.
"""
import argparse, shutil, subprocess, sys, tempfile, textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LUT = ROOT / "content-bank/luts/matteofights-v1.cube"
RED = "0xCC2222"
W, H, FPS = 1080, 1920, 30
FONTS = [
    "/usr/share/fonts/truetype/msttcorefonts/Impact.ttf",
    "/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
]


def ff(*args):
    subprocess.run(["ffmpeg", "-v", "error", "-y", *args], check=True)


def has_audio(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries", "stream=index",
                          "-of", "csv=p=0", str(path)], capture_output=True, text=True).stdout
    return bool(out.strip())


def duration(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                          str(path)], capture_output=True, text=True).stdout
    return float(out.strip())


def parse_clip(spec):
    path, _, rng = spec.partition("@")
    start, _, end = rng.partition("-")
    return Path(path), float(start) if start else 0.0, float(end) if end else None


def esc(s):
    # drawtext reads the text from a file, so only the path needs escaping.
    return str(s).replace("\\", "/").replace(":", r"\:").replace("'", r"\'")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("out")
    p.add_argument("--clip", action="append", required=True)
    p.add_argument("--hook")
    p.add_argument("--hook-secs", type=float, default=3.5)
    p.add_argument("--sub")
    p.add_argument("--end-text", default="READ DESCRIPTION")
    p.add_argument("--end-secs", type=float, default=3.0)
    p.add_argument("--music")
    p.add_argument("--music-vol", type=float, default=0.8)
    p.add_argument("--mute-clips", action="store_true")
    p.add_argument("--no-lut", action="store_true")
    p.add_argument("--font", default=next((f for f in FONTS if Path(f).exists()), None))
    a = p.parse_args()

    tmp = Path(tempfile.mkdtemp(prefix="reel_"))
    try:
        # 1) Normalize every clip: trim, fill 9:16, grade, 30fps, stereo audio (silent if none).
        grade = "" if a.no_lut or not LUT.exists() else f",lut3d='{esc(LUT)}'"
        vf = (f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1,fps={FPS}{grade},"
              "format=yuv420p")
        parts = []
        for i, spec in enumerate(a.clip):
            path, start, end = parse_clip(spec)
            seg = tmp / f"p{i:03d}.mp4"
            trim = ["-ss", str(start)] + (["-to", str(end)] if end is not None else [])
            if has_audio(path) and not a.mute_clips:
                ff(*trim, "-i", str(path), "-vf", vf, "-af", "aresample=48000,aformat=channel_layouts=stereo",
                   "-c:v", "libx264", "-crf", "18", "-preset", "veryfast", "-c:a", "aac", "-b:a", "192k", str(seg))
            else:
                ff(*trim, "-i", str(path), "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo", "-vf", vf,
                   "-map", "0:v", "-map", "1:a", "-shortest", "-c:v", "libx264", "-crf", "18",
                   "-preset", "veryfast", "-c:a", "aac", str(seg))
            parts.append(seg)
        lst = tmp / "list.txt"
        lst.write_text("".join(f"file '{s}'\n" for s in parts))
        joined = tmp / "joined.mp4"
        ff("-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(joined))
        total = duration(joined)

        # 2) Text: hook (red, top third) + subhook (white) for the opening, end card at the end.
        font = esc(a.font)
        draws = []
        if a.hook:
            f = tmp / "hook.txt"
            f.write_text("\n".join(textwrap.wrap(a.hook.upper(), 16)))
            draws.append(f"drawtext=fontfile='{font}':textfile='{esc(f)}':fontcolor={RED}:fontsize=96:"
                         f"box=1:boxcolor=black@0.75:boxborderw=28:line_spacing=10:x=(w-text_w)/2:y=h*0.16:enable='lt(t,{a.hook_secs})'")
        if a.sub:
            f = tmp / "sub.txt"
            f.write_text("\n".join(textwrap.wrap(a.sub, 28)))
            draws.append(f"drawtext=fontfile='{font}':textfile='{esc(f)}':fontcolor=white:fontsize=50:"
                         f"box=1:boxcolor=black@0.6:boxborderw=18:line_spacing=8:x=(w-text_w)/2:y=h*0.52:enable='lt(t,{a.hook_secs})'")
        if a.end_text:
            f = tmp / "end.txt"
            f.write_text(a.end_text.upper())
            draws.append(f"drawtext=fontfile='{font}':textfile='{esc(f)}':fontcolor=white:fontsize=64:"
                         f"box=1:boxcolor={RED}:boxborderw=24:x=(w-text_w)/2:y=h*0.80:"
                         f"enable='gte(t,{max(0, total - a.end_secs)})'")
        vchain = ",".join(draws) or "null"

        if a.music:
            mix = ("[1:a]volume=%s[m]" % a.music_vol) + (
                ";[0:a][m]amix=inputs=2:duration=first:dropout_transition=0[a]" if not a.mute_clips
                else ";[m]anull[a]")
            ff("-i", str(joined), "-stream_loop", "-1", "-i", a.music, "-filter_complex",
               f"[0:v]{vchain}[v];{mix}", "-map", "[v]", "-map", "[a]", "-t", str(total),
               "-c:v", "libx264", "-crf", "20", "-preset", "medium", "-c:a", "aac", "-b:a", "192k",
               "-movflags", "+faststart", a.out)
        else:
            ff("-i", str(joined), "-vf", vchain, "-c:v", "libx264", "-crf", "20", "-preset", "medium",
               "-c:a", "copy", "-movflags", "+faststart", a.out)
        print(f"{a.out}  {total:.1f}s  {W}x{H}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
