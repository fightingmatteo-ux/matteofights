"""Render a carousel (swipe post) to 1080x1350 JPEG slides in one of the two brand looks.

    python3 -P tools/carousel/render.py production/carousels/posts.json POST_ID OUTDIR [--look editorial|poster]

A post in posts.json:
    {"id": "car-choose-your-hard", "look": "editorial",
     "slides": [{"kind": "cover", "title": "...", "sub": "...", "photo": "path or null"},
                {"kind": "point", "n": 1, "title": "...", "body": "...", "photo": "..."},
                {"kind": "close", "title": "...", "body": "...", "cta": "..."}],
     "caption": "..."}
Photos: a frame from production/carousels/frames/ (tools/carousel/frames.py) or any photo Matteo provides.
Looks:
  editorial  white display serif on black, the photo in a thin white frame, clean sans body (the jayhiette/Dane style)
  poster     full-bleed darkened photo, Bebas Neue caps, red headline, gold numbers (the listicle-cover brand)
"""
import argparse, json
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parents[2]
FONTS = Path(__file__).resolve().parent / "fonts"
W, H = 1080, 1350
INK = (11, 11, 13)
WHITE = (245, 245, 242)
GREY = (150, 150, 150)
RED = (200, 32, 32)
GOLD = (196, 144, 64)
HANDLE = "@matteofights"


def font(name, size, weight=None):
    f = ImageFont.truetype(str(FONTS / name), size)
    if weight:
        f.set_variation_by_axes([weight])
    return f


def serif(size):
    return font("DMSerifDisplay-Regular.ttf", size)


def sans(size, weight=420):
    return font("Geist.ttf", size, weight)


def bebas(size):
    return font("BebasNeue-Regular.ttf", size)


def wrap(d, text, f, width):
    lines = []
    for para in text.split("\n"):
        cur = ""
        for w in para.split():
            t = f"{cur} {w}".strip()
            if d.textlength(t, font=f) <= width or not cur:
                cur = t
            else:
                lines.append(cur)
                cur = w
        lines.append(cur)
    return lines


def fit(d, text, make, width, max_h, start, low, lead):
    """Largest size from start down to low whose wrapped text fits width x max_h."""
    for size in range(start, low - 1, -2):
        f = make(size)
        lines = wrap(d, text, f, width)
        if len(lines) * size * lead <= max_h:
            return f, lines, size
    return f, lines, size


def block(d, xy, lines, f, size, lead, fill, align="left", width=None):
    x, y = xy
    for line in lines:
        lx = x + (width - d.textlength(line, font=f)) / 2 if align == "center" else x
        d.text((lx, y), line, font=f, fill=fill)
        y += size * lead
    return y


def photo(path, size):
    im = ImageOps.exif_transpose(Image.open(ROOT / path if not Path(path).is_absolute() else path)).convert("RGB")
    return ImageOps.fit(im, size, Image.LANCZOS, centering=(0.5, 0.4))


def framed(img, im, box):
    x, y, w, h = box
    img.paste(photo(im, (w, h)), (x, y))
    ImageDraw.Draw(img).rectangle([x - 2, y - 2, x + w + 1, y + h + 1], outline=WHITE, width=2)


def footer(d, n, total, color=GREY):
    f = sans(26, 450)
    d.text((80, H - 78), HANDLE, font=f, fill=color)
    pg = f"{n}/{total}"
    d.text((W - 80 - d.textlength(pg, font=f), H - 78), pg, font=f, fill=color)


# ---------- editorial ----------

def editorial(s, n, total):
    img = Image.new("RGB", (W, H), INK)
    d = ImageDraw.Draw(img)
    M = 110
    if s["kind"] == "cover":
        f, lines, size = fit(d, s["title"], serif, W - 2 * M, 300, 132, 80, 1.0)
        y = 210
        y = block(d, (M, y), lines, f, size, 1.0, WHITE, "center", W - 2 * M)
        if s.get("sub"):
            fs = sans(44, 380)
            y = block(d, (M, y + 26), [s["sub"]], fs, 44, 1.2, WHITE, "center", W - 2 * M)
        if s.get("photo"):
            framed(img, s["photo"], (150, int(y) + 60, W - 300, H - int(y) - 60 - 170))
    elif s["kind"] == "point":
        head = f"{s['n']}. {s['title']}" if s.get("n") else s["title"]
        f, lines, size = fit(d, head, serif, W - 2 * M, 200, 92, 60, 1.02)
        y = block(d, (M, 150), lines, f, size, 1.02, WHITE)
        top = int(y) + 40
        fb, blines, bsize = fit(d, s.get("body", ""), lambda z: sans(z, 400), W - 2 * M, 250, 50, 36, 1.22)
        body_h = len(blines) * bsize * 1.22
        if s.get("photo"):
            ph = int(H - top - body_h - 60 - 150)
            framed(img, s["photo"], (M, top, W - 2 * M, ph))
            top += ph + 50
        block(d, (M, top), blines, fb, bsize, 1.22, WHITE)
    else:  # close
        f, lines, size = fit(d, s["title"], serif, W - 2 * M, 360, 110, 64, 1.02)
        fb, blines, bsize = fit(d, s.get("body", ""), lambda z: sans(z, 400), W - 2 * M, 300, 48, 36, 1.25)
        total_h = len(lines) * size * 1.02 + 40 + len(blines) * bsize * 1.25
        y = (H - total_h) / 2 - 40
        y = block(d, (M, y), lines, f, size, 1.02, WHITE, "center", W - 2 * M)
        y = block(d, (M, y + 40), blines, fb, bsize, 1.25, WHITE, "center", W - 2 * M)
        if s.get("cta"):
            fc = sans(36, 560)
            block(d, (M, y + 50), wrap(d, s["cta"], fc, W - 2 * M), fc, 36, 1.3, WHITE, "center", W - 2 * M)
    footer(d, n, total)
    return img


# ---------- poster ----------

def dark_photo(path, amount=0.42):
    return ImageEnhance.Brightness(photo(path, (W, H))).enhance(amount)


def poster(s, n, total):
    img = dark_photo(s["photo"]) if s.get("photo") else Image.new("RGB", (W, H), INK)
    d = ImageDraw.Draw(img)
    M = 90
    if s["kind"] == "cover":
        f, lines, size = fit(d, s["title"].upper(), bebas, W - 2 * M, 640, 230, 120, 0.92)
        y = H * 0.40 - len(lines) * size * 0.92 / 2
        y = block(d, (M, y), lines, f, size, 0.92, RED)
        if s.get("sub"):
            block(d, (M, y + 10), [s["sub"].upper()], bebas(72), 72, 1.0, WHITE)
        block(d, (M, H - 190), ["SWIPE  >"], bebas(48), 48, 1, GOLD)
    elif s["kind"] == "point":
        block(d, (M, 120), [f"{s['n']:02d}"], bebas(170), 170, 1, GOLD)
        f, lines, size = fit(d, s["title"].upper(), bebas, W - 2 * M, 300, 130, 80, 0.95)
        y = block(d, (M, 320), lines, f, size, 0.95, WHITE)
        fb, blines, bsize = fit(d, s.get("body", ""), lambda z: sans(z, 520), W - 2 * M, 300, 52, 38, 1.22)
        block(d, (M, y + 30), blines, fb, bsize, 1.22, WHITE)
    else:  # close
        f, lines, size = fit(d, s["title"].upper(), bebas, W - 2 * M, 520, 190, 100, 0.95)
        y = block(d, (M, 260), lines, f, size, 0.95, RED)
        fb, blines, bsize = fit(d, s.get("body", ""), lambda z: sans(z, 480), W - 2 * M, 280, 48, 36, 1.25)
        y = block(d, (M, y + 40), blines, fb, bsize, 1.25, WHITE)
        if s.get("cta"):
            fc = bebas(64)
            block(d, (M, y + 50), wrap(d, s["cta"].upper(), fc, W - 2 * M), fc, 64, 1.0, GOLD)
    footer(d, n, total, (200, 200, 200))
    return img


LOOKS = {"editorial": editorial, "poster": poster}


def render(post, outdir, look=None):
    out = Path(outdir)
    out.mkdir(parents=True, exist_ok=True)
    draw = LOOKS[look or post.get("look", "editorial")]
    paths = []
    for i, s in enumerate(post["slides"], 1):
        p = out / f"{post['id']}-{i:02d}.jpg"
        draw(s, i, len(post["slides"])).save(p, quality=92)
        paths.append(p)
    return paths


def main():
    p = argparse.ArgumentParser()
    p.add_argument("posts")
    p.add_argument("post_id")
    p.add_argument("outdir")
    p.add_argument("--look", choices=list(LOOKS))
    a = p.parse_args()
    posts = json.loads(Path(a.posts).read_text(encoding="utf-8"))["posts"]
    post = next(x for x in posts if x["id"] == a.post_id)
    for path in render(post, a.outdir, a.look):
        print(path)


if __name__ == "__main__":
    main()
