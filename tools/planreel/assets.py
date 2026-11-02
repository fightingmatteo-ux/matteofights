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


def lock_icon(d, x, y, s, color):
    """Drawn padlock (body + shackle), s = body width."""
    d.rounded_rectangle([x, y + s * 0.45, x + s, y + s * 1.25], int(s * 0.12), fill=color)
    d.arc([x + s * 0.18, y, x + s * 0.82, y + s * 0.9], 180, 360, fill=color, width=max(3, int(s * 0.13)))
    d.line([x + s * 0.18 + 1, y + s * 0.45, x + s * 0.18 + 1, y + s * 0.62], fill=color, width=max(3, int(s * 0.13)))


def big_card(day, keyword, title, n, total, path):
    """Full-frame 1080x1920 day card (impeccable craft floor: no eyebrow, no boxed rows, one accent, drawn icon).
    Heading = the day's focus, big; day position as large tabular numerals beside it; a hairline list of moves with
    doses; on 3+ moves the last one is blurred behind a lock + "comment WORD"; plan name + levels at the foot."""
    W, H = 1080, 1920
    img = Image.new("RGB", (W, H), (10, 10, 12))
    d = ImageDraw.Draw(img)
    F = lambda f, s: ImageFont.truetype(f, s)  # noqa: E731
    weekday = day["d"].split("·")[0].strip()
    head = day["d"].split("·")[-1].strip().upper()
    pos = weekday.upper() if weekday.lower().startswith(("mon", "tue", "wed", "thu", "fri")) else f"{n}/{total}"
    hf = F(BEBAS, 230 if len(head) <= 8 else 170)
    d.text((80, 300), head, font=hf, fill=(246, 246, 246))
    pf = F(BEBAS, 92 if "/" in pos else 64)
    pw = d.textlength(pos, font=pf)
    d.text((W - 80 - pw, 300 + (hf.size - pf.size) - 18), pos, font=pf, fill=RED)
    y = 300 + hf.size + 70
    items = day["items"]
    lock = len(items) >= 3
    nf, df, idf = F(INTER, 50), F(INTER, 40), F(BEBAS, 64)
    for k, (name, dose, *_) in enumerate(items):
        row = Image.new("RGBA", (W - 160, 150), (0, 0, 0, 0))
        r = ImageDraw.Draw(row)
        r.text((0, 30), f"{k + 1:02d}"[-1] if False else str(k + 1), font=idf, fill=(110, 110, 116, 255))
        nm = name if len(name) <= 24 else name[:23] + "…"
        r.text((80, 22), nm, font=nf, fill=(242, 242, 242, 255))
        r.text((80, 86), dose, font=df, fill=GOLD + (255,))
        if lock and k == len(items) - 1:
            row = row.filter(ImageFilter.GaussianBlur(18))
            img.paste(row, (80, y), row)
            tag = f"Comment {keyword} for this one"
            tf = F(INTER, 40)
            tl = d.textlength(tag, font=tf)
            bw = tl + 150
            x0 = (W - bw) / 2
            d.rounded_rectangle([x0, y + 30, x0 + bw, y + 118], 44, fill=RED)
            lock_icon(d, x0 + 44, y + 50, 34, (255, 255, 255))
            d.text((x0 + 104, y + 52), tag, font=tf, fill=(255, 255, 255))
        else:
            img.paste(row, (80, y), row)
        y += 150
        if k < len(items) - 1:
            d.line([80, y - 6, W - 80, y - 6], fill=(38, 38, 44), width=2)
    fy = H - 330
    d.line([80, fy, W - 80, fy], fill=(38, 38, 44), width=2)
    d.text((80, fy + 40), title, font=F(INTER, 38), fill=(200, 200, 205))
    lf = F(INTER, 34)
    x = 80
    for c in ["Beginner", "Amateur", "Advanced"]:
        on = c == "Amateur"
        w = d.textlength(c, font=lf) + 52
        d.rounded_rectangle([x, fy + 110, x + w, fy + 176], 33, fill=(246, 246, 246) if on else None,
                            outline=None if on else (70, 70, 76), width=2)
        d.text((x + 26, fy + 124), c, font=lf, fill=(10, 10, 12) if on else (170, 170, 176))
        x += w + 14
    img.save(path)


def card_clip(png, out, secs=2.2, fps=30):
    """One authored moment (Emil Kowalski): 0.3 s exponential ease-out from 1.04x and 10 px blur to rest, then hold."""
    base = Image.open(png).convert("RGB")
    fr = Path("assets/media/frames")
    fr.mkdir(parents=True, exist_ok=True)
    n_in = 9
    for i in range(n_in):
        t = 1 - 2 ** (-10 * (i + 1) / n_in)  # easeOutExpo
        sc = 1.04 - 0.04 * t
        im = base.resize((int(1080 * sc), int(1920 * sc)))
        im = im.crop(((im.width - 1080) // 2, (im.height - 1920) // 2, (im.width - 1080) // 2 + 1080, (im.height - 1920) // 2 + 1920))
        im = im.filter(ImageFilter.GaussianBlur(10 * (1 - t)))
        im = Image.blend(Image.new("RGB", (1080, 1920), (10, 10, 12)), im, min(1, 0.35 + t))
        im.save(fr / f"f{i:03d}.png")
    for i in range(n_in, int(secs * fps)):
        base.save(fr / f"f{i:03d}.png") if i == n_in else None
    hold = int(secs * fps) - n_in
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-framerate", str(fps), "-i", str(fr / "f%03d.png"),
                    "-loop", "1", "-t", f"{hold / fps:.3f}", "-i", str(fr / f"f{n_in:03d}.png"),
                    "-filter_complex", f"[0:v]trim=end_frame={n_in}[a];[1:v]fps={fps}[b];[a][b]concat=n=2:v=1[v]", "-map", "[v]",
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "16", out], check=True)
    for f in fr.glob("*.png"):
        f.unlink()


cfg = json.loads(Path(sys.argv[1]).read_text())
Path("assets/media").mkdir(parents=True, exist_ok=True)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(cfg["t_lo"]), "-to", str(cfg["t_hi"]), "-i", cfg["raw"],
                "-vf", "scale=1080:1920", "-c:v", "libx264", "-crf", "17", "-preset", "medium", "-pix_fmt", "yuv420p",
                "-c:a", "aac", "-b:a", "192k", "assets/raw.mp4"], check=True)
plan = next(p for p in json.loads(Path(cfg["plans"]).read_text())["plans"] if p["slug"] == cfg["plan"])
for c in cfg.get("clips", []):  # b-roll cutaways: cut, fill 9:16, mute
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(c["in"]), "-t", str(c["dur"] + 0.3), "-i", c["src"], "-an",
                    "-vf", "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1", "-r", "30",
                    "-c:v", "libx264", "-crf", "17", "-pix_fmt", "yuv420p", f"assets/media/b_{c['name']}.mp4"], check=True)
print("assets ready")
