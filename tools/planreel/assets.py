"""Run inside a plan reel folder (by its make.sh, on Modal): python3 ../../../tools/planreel/assets.py work/assets.json
Trims the raw recording to the takes (neutral colour, 1080x1920) -> assets/raw.mp4 and draws the day cards ->
assets/media/b_day<N>.mp4 (full-screen cutaways). Settings come from tools/planreel/editorial.py."""
import json, subprocess, sys
from pathlib import Path
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from PIL import ImageDraw, ImageFilter, ImageFont  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
BEBAS, INTER = str(ROOT / "tools/listicle/fonts/BebasNeue-Regular.ttf"), str(ROOT / "tools/listicle/fonts/Inter-Bold.otf")
RED, GOLD = (200, 32, 32), (196, 144, 64)


def big_card(day, keyword, title, n, total, path):
    """Full-frame 1080x1920 day card: plan title, big day header, numbered rows with doses, last row blurred behind a
    comment tag (3+ rows), level chips at the bottom (the DM plan has Beginner / Amateur / Advanced)."""
    img = Image.new("RGB", (1080, 1920), (11, 11, 13))
    d = ImageDraw.Draw(img)
    for y in range(0, 1920, 4):  # subtle red glow from the top
        a = max(0, 60 - y // 14)
        d.rectangle([0, y, 1080, y + 4], fill=(11 + a // 2, 11, 13))
    F = lambda f, s: ImageFont.truetype(f, s)  # noqa: E731
    d.text((80, 300), title.upper(), font=F(INTER, 40), fill=GOLD)
    d.text((80, 360), f"DAY {n} OF {total}" if not day["d"].lower().startswith(("mon", "tue", "wed", "thu", "fri")) else day["d"].split("·")[0].strip().upper(),
           font=F(BEBAS, 72), fill=(150, 150, 155))
    head = day["d"].split("·")[-1].strip().upper()
    d.text((76, 430), head, font=F(BEBAS, 190), fill=(245, 245, 245))
    d.rectangle([80, 640, 240, 650], fill=RED)
    items = day["items"]
    y = 720
    lock = len(items) >= 3
    for k, (name, dose, *_) in enumerate(items):
        row = Image.new("RGBA", (920, 150), (0, 0, 0, 0))
        r = ImageDraw.Draw(row)
        r.rounded_rectangle([0, 0, 919, 138], 28, fill=(24, 24, 28, 255))
        r.ellipse([28, 37, 92, 101], fill=RED + (255,))
        num = str(k + 1)
        r.text((60 - r.textlength(num, font=F(BEBAS, 54)) / 2, 41), num, font=F(BEBAS, 54), fill=(255, 255, 255, 255))
        nm = name if len(name) <= 26 else name[:25] + "…"
        r.text((120, 26), nm, font=F(INTER, 44), fill=(240, 240, 240, 255))
        r.text((120, 84), dose, font=F(INTER, 34), fill=GOLD + (255,))
        if lock and k == len(items) - 1:
            row = row.filter(ImageFilter.GaussianBlur(16))
            img.paste(row, (80, y), row)
            tag = f"COMMENT {keyword} FOR THIS"
            tf = F(INTER, 40)
            tl = d.textlength(tag, font=tf)
            x0 = (1080 - tl) / 2 - 40
            d.rounded_rectangle([x0, y + 30, x0 + tl + 80, y + 110], 40, fill=RED)
            d.text((x0 + 40, y + 48), tag, font=tf, fill=(255, 255, 255))
        else:
            img.paste(row, (80, y), row)
        y += 162
    cy = max(y + 40, 1560)
    chips = ["BEGINNER", "AMATEUR", "ADVANCED"]
    cf = F(INTER, 34)
    x = 80
    for c in chips:
        w = d.textlength(c, font=cf) + 56
        d.rounded_rectangle([x, cy, x + w, cy + 70], 35, outline=(90, 90, 96), width=3, fill=(40, 12, 12) if c == "AMATEUR" else None)
        d.text((x + 28, cy + 15), c, font=cf, fill=(255, 255, 255) if c == "AMATEUR" else (150, 150, 155))
        x += w + 18
    d.text((80, cy + 100), "All 3 levels in the full plan", font=F(INTER, 34), fill=(150, 150, 155))
    img.save(path)

cfg = json.loads(Path(sys.argv[1]).read_text())
Path("assets/media").mkdir(parents=True, exist_ok=True)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(cfg["t_lo"]), "-to", str(cfg["t_hi"]), "-i", cfg["raw"],
                "-vf", "scale=1080:1920", "-c:v", "libx264", "-crf", "17", "-preset", "medium", "-pix_fmt", "yuv420p",
                "-c:a", "aac", "-b:a", "192k", "assets/raw.mp4"], check=True)
plan = next(p for p in json.loads(Path(cfg["plans"]).read_text())["plans"] if p["slug"] == cfg["plan"])
for k, day in enumerate(plan["days"]):
    big_card(day, cfg["keyword"], plan["title"], k + 1, len(plan["days"]), "assets/media/card_full.png")
    # gentle push-in so the card feels alive
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-loop", "1", "-i", "assets/media/card_full.png", "-t", "2.2", "-r", "30",
                    "-vf", "scale=1188:2112,zoompan=z='min(1+on*0.0012,1.06)':x='iw/2-iw/zoom/2':y='ih/2-ih/zoom/2':d=66:s=1080x1920:fps=30,fade=t=in:st=0:d=0.12",
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "16", f"assets/media/b_day{k + 1}.mp4"], check=True)
for c in cfg.get("clips", []):  # b-roll cutaways: cut, fill 9:16, mute
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(c["in"]), "-t", str(c["dur"] + 0.3), "-i", c["src"], "-an",
                    "-vf", "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1", "-r", "30",
                    "-c:v", "libx264", "-crf", "17", "-pix_fmt", "yuv420p", f"assets/media/b_{c['name']}.mp4"], check=True)
print("assets ready")
