"""Splice a fight clip into a variant's a-roll picture (voice untouched), before the cut-out runs, so the editorial
hook word sits behind the FIGHTERS and flies in front on the spoken word:
    python3 ../../../tools/planreel/splice.py work/hook_A.json assets/media/aroll_A.mp4
hook json: {"clip": "assets/media/hookcut_A.mp4", "start": 0.4, "dur": 2.3}  (clip already 1080x1920, cut by precut.sh)
"""
import json, os, subprocess, sys

h = json.load(open(sys.argv[1]))
aroll = sys.argv[2]
tmp = aroll.replace(".mp4", ".splice.mp4")
s, d = h["start"], h["dur"]
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", aroll, "-t", f"{d + 0.1:.3f}", "-i", h["clip"], "-filter_complex",
                f"[1:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1,fps=30,setpts=PTS-STARTPTS+{s:.3f}/TB[b];"
                f"[0:v][b]overlay=0:0:eof_action=pass:enable='between(t,{s:.3f},{s + d:.3f})'[v]",
                "-map", "[v]", "-map", "0:a?", "-c:v", "libx264", "-crf", "16", "-preset", "medium", "-pix_fmt", "yuv420p",
                "-c:a", "copy", tmp], check=True)
os.replace(tmp, aroll)
print(f"spliced {h['clip']} into {aroll} at {s:.2f}-{s + d:.2f}s")
