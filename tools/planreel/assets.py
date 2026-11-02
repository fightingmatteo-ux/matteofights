"""Run inside a plan reel folder (by its make.sh, on Modal): python3 ../../../tools/planreel/assets.py work/assets.json
Trims the raw recording to the takes (neutral colour, 1080x1920) -> assets/raw.mp4 and draws the day cards ->
assets/media/b_day<N>.mp4 (full-screen cutaways). Settings come from tools/planreel/editorial.py."""
import json, subprocess, sys
from pathlib import Path
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from compose import card_png  # noqa: E402

cfg = json.loads(Path(sys.argv[1]).read_text())
Path("assets/media").mkdir(parents=True, exist_ok=True)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(cfg["t_lo"]), "-to", str(cfg["t_hi"]), "-i", cfg["raw"],
                "-vf", "scale=1080:1920", "-c:v", "libx264", "-crf", "17", "-preset", "medium", "-pix_fmt", "yuv420p",
                "-c:a", "aac", "-b:a", "192k", "assets/raw.mp4"], check=True)
plan = next(p for p in json.loads(Path(cfg["plans"]).read_text())["plans"] if p["slug"] == cfg["plan"])
for k, day in enumerate(plan["days"]):
    card_png(day, cfg["keyword"], "assets/media/card.png")
    c = Image.open("assets/media/card.png")
    bg = Image.new("RGB", (1080, 1920), (11, 11, 13))
    bg.paste(c, ((1080 - c.width) // 2, (1920 - c.height) // 2), c)
    bg.save("assets/media/card_full.png")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-loop", "1", "-i", "assets/media/card_full.png", "-t", "2.2", "-r", "30",
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "16", f"assets/media/b_day{k + 1}.mp4"], check=True)
print("assets ready")
