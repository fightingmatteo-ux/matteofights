"""Listicle carousel slides (1080x1350 JPEG) for Facebook photo posts (and TikTok photo mode later).

Slide 1: the hook over the reel's darkened cover. Then one slide per item ("1/6" + the sign). Last: the question.
Fonts come from tools/listicle/fonts (Bebas Neue for headlines, Liberation Serif Bold for body).
"""
import io
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[2]
FONTS = ROOT / "tools" / "listicle" / "fonts"
W, H = 1080, 1350
RED = (200, 32, 32)
INK = (11, 11, 13)
TEXT = (240, 240, 240)
MID = (170, 170, 170)


def _font(name, size):
    return ImageFont.truetype(str(FONTS / name), size)


def _wrap(draw, text, font, width):
    lines, cur = [], ""
    for w in text.split():
        t = f"{cur} {w}".strip()
        if draw.textlength(t, font=font) <= width or not cur:
            cur = t
        else:
            lines.append(cur)
            cur = w
    return lines + ([cur] if cur else [])


def _fit(draw, text, name, width, max_h, start, low):
    for size in range(start, low - 1, -4):
        f = _font(name, size)
        lines = _wrap(draw, text, f, width)
        if len(lines) * size * 1.08 <= max_h:
            return f, lines
    f = _font(name, low)
    return f, _wrap(draw, text, f, width)


def _background(cover):
    if cover and Path(cover).exists():
        im = Image.open(cover).convert("RGB")
        im = im.crop((0, int(im.height * 0.38), im.width, im.height))  # skip the burned-in hook text at the top
        s = max(W / im.width, H / im.height)
        im = im.resize((int(im.width * s) + 1, int(im.height * s) + 1))
        im = im.crop(((im.width - W) // 2, (im.height - H) // 2, (im.width - W) // 2 + W, (im.height - H) // 2 + H))
        im = ImageEnhance.Brightness(im.filter(ImageFilter.GaussianBlur(6))).enhance(0.3)
        return im
    return Image.new("RGB", (W, H), INK)


def _jpeg(im):
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=88)
    return buf.getvalue()


def _brand(d):
    d.text((80, H - 110), "@MATTEOFIGHTS", font=_font("BebasNeue-Regular.ttf", 44), fill=MID)


def render(hook, items, cta, cover=None):
    out = []
    bg = _background(cover)

    im = bg.copy()
    d = ImageDraw.Draw(im)
    d.rectangle((80, 380, 200, 392), fill=RED)
    f, lines = _fit(d, hook.upper(), "BebasNeue-Regular.ttf", W - 160, 620, 150, 80)
    y = 430
    for l in lines:
        d.text((80, y), l, font=f, fill=TEXT)
        y += int(f.size * 1.02)
    d.text((80, y + 40), f"SWIPE FOR ALL {len(items)}", font=_font("BebasNeue-Regular.ttf", 54), fill=RED)
    _brand(d)
    out.append(_jpeg(im))

    for k, item in enumerate(items, 1):
        im = Image.new("RGB", (W, H), INK)
        d = ImageDraw.Draw(im)
        d.text((80, 150), f"{k}", font=_font("BebasNeue-Regular.ttf", 300), fill=RED)
        d.text((80 + d.textlength(f"{k}", font=_font("BebasNeue-Regular.ttf", 300)) + 24, 330),
               f"/ {len(items)}", font=_font("BebasNeue-Regular.ttf", 80), fill=MID)
        f, lines = _fit(d, item, "LiberationSerif-Bold.ttf", W - 160, 640, 96, 52)
        y = 560
        for l in lines:
            d.text((80, y), l, font=f, fill=TEXT)
            y += int(f.size * 1.18)
        _brand(d)
        out.append(_jpeg(im))

    im = bg.copy()
    d = ImageDraw.Draw(im)
    f, lines = _fit(d, cta.upper(), "BebasNeue-Regular.ttf", W - 160, 500, 140, 80)
    y = 500
    for l in lines:
        d.text((80, y), l, font=f, fill=TEXT)
        y += int(f.size * 1.02)
    d.rectangle((80, y + 30, 200, y + 42), fill=RED)
    _brand(d)
    out.append(_jpeg(im))
    return out
