"""Render one listicle reel in the proven old format: training clip + red ALL-CAPS hook + subhook,
"READ CAPTION" near the end. No talking, no edit decisions: headless, so the daily factory can run it.

    python -P tools/listicle/render.py <clip> <hook id> <out.mp4> [--cover cover.jpg] [--seconds 8]

The hook text comes from production/listicles/hooks.json. Colour handling matches
production/editing/reel-kit/scripts/prep_footage.sh (iPhone HDR -> SDR, full range -> tv range, neutral grade).
"""
import argparse, json, subprocess, tempfile
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
HOOKS = ROOT / "production" / "listicles" / "hooks.json"
BEBAS = Path(__file__).parent / "fonts" / "BebasNeue-Regular.ttf"
EMOJI = Path("/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf")
MUSIC = sorted((ROOT / "production/reels/five-signs-real-fighter/assets/music").glob("*.mp3"))
W, H = 1080, 1920
RED, WHITE, BLACK = (232, 17, 45), (255, 255, 255), (11, 11, 13)
# Instagram's grid crop keeps y 285-1635; the UI covers the bottom ~320 px. Text stays inside both.
TOP, TEXT_W = 300, 960


def probe(clip, entry):
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", entry,
                          "-of", "csv=p=0", str(clip)], capture_output=True, text=True).stdout.strip()
    return out.split(",")[0] if out else ""


def has_audio(clip):
    return bool(subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries",
                                "stream=index", "-of", "csv=p=0", str(clip)], capture_output=True, text=True).stdout.strip())


def wrap(draw, text, font, width):
    lines, cur = [], ""
    for w in text.split():
        t = f"{cur} {w}".strip()
        if draw.textlength(t, font=font) <= width or not cur:
            cur = t
        else:
            lines.append(cur); cur = w
    return lines + [cur]


def fit(draw, text, max_lines, size, width=TEXT_W):
    while True:
        f = ImageFont.truetype(str(BEBAS), size)
        lines = wrap(draw, text, f, width)
        if len(lines) <= max_lines and all(draw.textlength(l, font=f) <= width for l in lines):
            break
        size -= 4
    # Balance: narrow the box while the line count holds, so no word sits alone on the last line.
    w = width
    while w > 300 and len(wrap(draw, text, f, w - 10)) == len(lines):
        w -= 10
    return f, wrap(draw, text, f, w)


def text_block(draw, lines, font, y, fill, plate=True, gap=0.02):
    """Centred lines on a solid black plate (fight-poster look: no gradients, no shadows)."""
    asc, desc = font.getmetrics()
    lh = int((asc + desc) * (0.92 + gap))
    if plate:
        pw = max(draw.textlength(l, font=font) for l in lines) + 56
        draw.rectangle([(W - pw) / 2, y - 18, (W + pw) / 2, y + lh * len(lines) + 6], fill=BLACK)
    for i, l in enumerate(lines):
        draw.text((W / 2, y + i * lh), l, font=font, fill=fill, anchor="ma")
    return y + lh * len(lines)


def hook_layer(hook, subhook):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    f, lines = fit(d, hook.upper(), 4, 150)
    y = text_block(d, lines, f, TOP, RED)
    size = 64  # one sentence per line when it fits at a readable size, else balanced wrap
    while size > 48 and max(d.textlength(s.upper(), font=ImageFont.truetype(str(BEBAS), size)) for s in subhook) > TEXT_W - 40:
        size -= 2
    sub = [l for s in subhook for l in fit(d, s.upper(), 2, size, TEXT_W - 40)[1]]
    fs = ImageFont.truetype(str(BEBAS), size)
    text_block(d, sub, fs, y + 46, WHITE, gap=0.08)
    return img


def cta_layer():
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    f = ImageFont.truetype(str(BEBAS), 96)
    label, y = "READ CAPTION", 1360
    tw = d.textlength(label, font=f)
    em = 96
    x0 = (W - tw - em - 20) / 2
    d.rectangle([x0 - 30, y - 22, x0 + tw + em + 50, y + 112], fill=BLACK)
    d.text((x0, y), label, font=f, fill=WHITE)
    try:  # Noto Color Emoji only renders at its bitmap size (109); scale it down
        e = Image.new("RGBA", (136, 128), (0, 0, 0, 0))
        ImageDraw.Draw(e).text((0, 0), "⬇️", font=ImageFont.truetype(str(EMOJI), 109), embedded_color=True)
        e = e.crop(e.getbbox()).resize((em, em))
        img.alpha_composite(e, (int(x0 + tw + 20), y + 2))
    except OSError:  # no emoji font: plain red arrow
        cx, top = x0 + tw + 20 + em / 2, y + 8
        d.polygon([(cx - 40, top + 40), (cx + 40, top + 40), (cx, top + 90)], fill=RED)
        d.rectangle([cx - 14, top, cx + 14, top + 42], fill=RED)
    return img


def render(clip, hook_id, out, seconds=8.0, cover=None, music_i=0):
    hooks = {h["id"]: h for h in json.loads(HOOKS.read_text(encoding="utf-8"))["hooks"]}
    h = hooks[hook_id]
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                                str(clip)], capture_output=True, text=True).stdout.strip() or 0)
    seconds = min(seconds, dur) if dur else seconds
    start = max(0.0, (dur - seconds) * 0.4)  # skip the walk-to-the-bag start of most phone clips
    cta_at = max(0.0, seconds - 3.2)

    trc, rng = probe(clip, "stream=color_transfer"), probe(clip, "stream=color_range")
    tm = ""
    if trc in ("arib-std-b67", "smpte2084"):
        tm = (f"zscale=t=linear:npl=100:tin={trc}:pin=bt2020:min=bt2020nc,format=gbrpf32le,zscale=p=bt709,"
              "tonemap=hable:desat=0,zscale=t=bt709:m=bt709:r=tv,")
    elif rng == "pc":
        tm = "scale=in_range=pc:out_range=tv,"

    with tempfile.TemporaryDirectory() as tmp:
        hp, cp = Path(tmp, "hook.png"), Path(tmp, "cta.png")
        hook_layer(h["hook"], h["subhook"]).save(hp)
        cta_layer().save(cp)
        music = MUSIC[music_i % len(MUSIC)] if MUSIC else None
        cmd = ["ffmpeg", "-v", "error", "-y", "-ss", f"{start:.2f}", "-t", f"{seconds:.2f}", "-i", str(clip),
               "-loop", "1", "-i", str(hp), "-loop", "1", "-i", str(cp)]
        # Footage darkened a touch so red text reads on it ("red on dark training footage").
        vf = (f"[0:v]{tm}scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps=30,"
              f"eq=brightness=-0.06:saturation=0.9,format=yuv420p[bg];"
              f"[bg][1:v]overlay=0:0:shortest=1[a];"
              f"[a][2:v]overlay=0:0:shortest=1:enable='gte(t,{cta_at:.2f})',format=yuv420p[v]")
        if music:
            cmd += ["-i", str(music)]
            mi = 3
            if has_audio(clip):  # music on top, the gym sound (bag, breathing) underneath
                af = f"[{mi}:a]volume=0.9[m];[0:a]volume=0.35[g];[m][g]amix=inputs=2:duration=first:normalize=0,"
            else:
                af = f"[{mi}:a]"
            af += f"atrim=0:{seconds:.2f},afade=t=out:st={max(0, seconds - 0.6):.2f}:d=0.6,loudnorm=I=-14:TP=-1.5[au]"
            fc, amap = vf + ";" + af, ["-map", "[au]"]
        elif has_audio(clip):
            fc, amap = vf, ["-map", "0:a:0"]
        else:
            fc, amap = vf, []
        cmd += ["-filter_complex", fc, "-map", "[v]", *amap, "-t", f"{seconds:.2f}",
                "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709", "-color_range", "tv",
                "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
                "-movflags", "+faststart", str(out)]
        subprocess.run(cmd, check=True)
    if cover:  # frame 0.5 s = the cover Instagram uses (thumb_offset 500)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", "0.5", "-i", str(out), "-frames:v", "1",
                        "-vf", "scale=540:-2", "-q:v", "4", str(cover)], check=True)
    return out


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("clip"); p.add_argument("hook_id"); p.add_argument("out")
    p.add_argument("--cover"); p.add_argument("--seconds", type=float, default=8.0)
    p.add_argument("--music", type=int, default=0, help="index into the music tracks")
    a = p.parse_args()
    print(render(a.clip, a.hook_id, a.out, a.seconds, a.cover, a.music))
