"""Render a carousel (swipe post) to 1080x1350 JPEG slides in one of the two brand looks.

    python3 -P tools/carousel/render.py production/carousels/posts.json POST_ID OUTDIR [--look editorial|poster] [--animate]

--animate also writes <id>-01.mp4: the cover as a 4.5 s silent loop (Instagram and Threads take a video as slide 1;
Facebook albums keep the still). Text is complete from frame 0 because the first frame is the thumbnail. Motion:
slow push-in on the photo, then twice a "peek" (the slide eases left and shows the edge of slide 2) with a pulsing
arrow, the cue that makes people swipe.

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
import argparse, json, math, subprocess
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


ZOOM = [1.0]  # set by animate(): push-in on every photo of the frame being drawn


def photo(path, size):
    im = ImageOps.exif_transpose(Image.open(ROOT / path if not Path(path).is_absolute() else path)).convert("RGB")
    z = ZOOM[0]
    big = (round(size[0] * z), round(size[1] * z))
    im = ImageOps.fit(im, big, Image.LANCZOS, centering=(0.5, 0.4))
    x, y = (big[0] - size[0]) // 2, int((big[1] - size[1]) * 0.4)
    return im.crop((x, y, x + size[0], y + size[1]))


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

FPS, SECONDS, PEEKS, PEEK_PX = 30, 4.5, (1.4, 3.0), 120


def ease(t):
    return 0.5 - 0.5 * math.cos(math.pi * max(0.0, min(1.0, t)))


def peek(t):
    """0..1..0 over 1.1 s for each peek start."""
    return max((math.sin(math.pi * ease((t - p) / 1.1)) if p <= t <= p + 1.1 else 0.0) for p in PEEKS)


def arrow(d, x, y, alpha, color):
    c = tuple(round(v * alpha + 11 * (1 - alpha)) for v in color)
    for k in range(2):
        ox = x + k * 26
        d.line([(ox, y - 26), (ox + 22, y), (ox, y + 26)], fill=c, width=6, joint="curve")


def animate(post, draw, out_mp4, total):
    """Cover slide as a silent looping MP4 with a push-in and two swipe peeks at slide 2."""
    nxt = draw(post["slides"][1], 2, total) if len(post["slides"]) > 1 else None
    ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18",
                           "-movflags", "+faststart", str(out_mp4)], stdin=subprocess.PIPE)
    n = int(FPS * SECONDS)
    for i in range(n):
        t = i / FPS
        ZOOM[0] = 1.0 + 0.05 * math.sin(math.pi * i / n)  # in and back out: seamless loop
        cover = draw(post["slides"][0], 1, total)
        ZOOM[0] = 1.0
        dx = round(PEEK_PX * peek(t))
        frame = Image.new("RGB", (W, H), INK)
        frame.paste(cover, (-dx, 0))
        if nxt is not None and dx:
            frame.paste(nxt.crop((0, 0, dx, H)), (W - dx, 0))
            ImageDraw.Draw(frame).line([(W - dx, 0), (W - dx, H)], fill=INK, width=4)
        pulse = 0.55 + 0.45 * math.sin(2 * math.pi * t / 1.5) ** 2
        arrow(ImageDraw.Draw(frame), W - dx - 110, H // 2, pulse, WHITE)
        ff.stdin.write(frame.tobytes())
    ff.stdin.close()
    if ff.wait():
        raise RuntimeError("ffmpeg failed on the animated cover")
    return out_mp4


def render(post, outdir, look=None, animated=False):
    out = Path(outdir)
    out.mkdir(parents=True, exist_ok=True)
    draw = LOOKS[look or post.get("look", "editorial")]
    paths = []
    for i, s in enumerate(post["slides"], 1):
        p = out / f"{post['id']}-{i:02d}.jpg"
        draw(s, i, len(post["slides"])).save(p, quality=92)
        paths.append(p)
    if animated:
        paths.insert(0, animate(post, draw, out / f"{post['id']}-01.mp4", len(post["slides"])))
    return paths


def main():
    p = argparse.ArgumentParser()
    p.add_argument("posts")
    p.add_argument("post_id")
    p.add_argument("outdir")
    p.add_argument("--look", choices=list(LOOKS))
    p.add_argument("--animate", action="store_true")
    a = p.parse_args()
    posts = json.loads(Path(a.posts).read_text(encoding="utf-8"))["posts"]
    post = next(x for x in posts if x["id"] == a.post_id)
    for path in render(post, a.outdir, a.look, a.animate):
        print(path)


if __name__ == "__main__":
    main()
