"""Render a carousel (swipe post) to designed 1080x1350 slides, each in its own layout, plus an animated cover.

    python3 -P tools/carousel/render.py production/carousels/posts.json POST_ID OUTDIR [--animate]

Builds one HTML page (slides.css + fonts/) and screenshots it in Chromium (shoot.cjs, Playwright). Every slide
names its `layout`; neighbours never share one (lint.py checks). Layouts, so a post never looks like one template:
  cover     stacked mixed type (Anton / italic serif / red Anton) over a tilted photo card, spinning SWIPE badge
  numeral   paper ground, giant outlined numeral, round photo in a red ring, handwritten line with a squiggle
  tape      full-bleed photo, title on a tilted black tape strip, gold handwritten line
  split     photo cut on a diagonal, gold number column, short title + one line
  polaroid  red ground, tilted polaroid with a pin and handwriting, title above
  quote     black, giant gold quote marks, italic serif, the photo as a film strip
  close     one CTA with the save icon and a hand-drawn arrow toward Instagram's save button
Every slide but the last carries the swipe tab, and a red thread runs across the slide edges so the carousel reads
as one strip when swiping. Copy rule: title <= 5 words, one short line under it.

Slide fields: layout, title, line (the short line), photo, n (number). Cover: kicker + title as three parts
"a|b|c" (a and c in Anton, b in italic serif). The moving detail: give the cover a `video` (a 4 s seamless loop from frames.py, on the media release as
carousel-loop-<clip>-<t>.webm, pulled to media/) and the photo card plays it. --animate writes <id>-01.mp4: the
card's footage loops, the SWIPE badge turns slowly, everything else stays still. Frame 0 is complete (it is the
thumbnail); without --animate the cover is the still from the same moment.
"""
import argparse, html, json, subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]

CHEVRON = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M9 5l7 7-7 7"/></svg>'
ARROW = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"><path d="M4 12h15M13 6l6 6-6 6"/></svg>'
BOOKMARK = '<svg viewBox="0 0 24 24" fill="none" stroke="#f5f5f2" stroke-width="2" stroke-linejoin="round"><path d="M6 3h12v18l-6-4.5L6 21z"/></svg>'
SQUIGGLE = '<svg class="squiggle" viewBox="0 0 560 40" fill="none" stroke="#c82020" stroke-width="7" stroke-linecap="round"><path d="M4 26 C 60 4, 100 40, 160 20 S 260 6, 320 24 S 440 36, 556 12"/></svg>'
CURVE = ('<svg class="arrow" viewBox="0 0 300 300" fill="none" stroke="#c82020" stroke-width="8" stroke-linecap="round" stroke-linejoin="round">'
         '<path d="M30 20 C 60 160, 150 230, 250 250"/><path d="M200 210 L 252 252 L 190 272"/></svg>')
RING = ('<svg class="ring" viewBox="0 0 230 230"><defs><path id="c" d="M115,115 m-92,0 a92,92 0 1,1 184,0 a92,92 0 1,1 -184,0"/></defs>'
        '<circle cx="115" cy="115" r="113" fill="#c82020"/><text font-family="Mono" font-weight="700" font-size="25" letter-spacing="6" fill="#f5f5f2">'
        '<textPath href="#c" textLength="572" lengthAdjust="spacing">SWIPE · SWIPE · SWIPE · SWIPE ·</textPath></text></svg>')


def esc(s):
    return html.escape(s or "")


def bg(photo):
    if not photo:
        return ""
    p = Path(photo) if Path(photo).is_absolute() else ROOT / photo
    return f"background-image:url('{p.as_uri()}')"


def furniture(i, total, last):
    out = f'<div class="count">{i:02d} / {total:02d}</div><div class="handle">@matteofights</div>'
    out += '<div class="thread" style="left:0;right:0;bottom:36px"></div>' if not last else '<div class="thread" style="left:0;width:700px;bottom:36px"></div>'
    if not last and i > 1:
        out += f'<div class="swipe">{CHEVRON}</div>'
    return out


def media_card(s, cls):
    if s.get("video"):
        v = Path(s["video"]) if Path(s["video"]).is_absolute() else ROOT / s["video"]
        return f'<video class="ph {cls}" src="{v.as_uri()}" muted playsinline preload="auto" style="{bg(s.get("photo"))}"></video>'
    return f'<div class="ph {cls}" style="{bg(s.get("photo"))}"></div>'


def fit(word, width=780, top=210):
    """Anton caps run about 0.47 em a character: shrink long words so they stay left of the photo card."""
    return f"font-size:{min(top, int(width / (0.47 * max(len(word), 1))))}px"


def cover(s, i, total):
    a, b, c = (s["title"].split("|") + ["", "", ""])[:3]
    return (f'<div class="slide dark cover grain"><div class="block"></div>{media_card(s, "card")}'
            f'<div class="kicker">{esc(s.get("kicker"))}</div>'
            f'<h1><span class="a" style="{fit(a)}">{esc(a)}</span><span class="b">{esc(b)}</span>'
            f'<span class="c" style="{fit(c)}">{esc(c)}</span></h1>'
            f'<div class="badge">{RING}<div class="core">{ARROW}</div></div>{furniture(i, total, False)}</div>')


def numeral(s, i, total):
    return (f'<div class="slide paper numeral grain"><div class="big outline">{s.get("n", i - 1):02d}</div>'
            f'<div class="ph disc" style="{bg(s.get("photo"))}"></div><h2>{esc(s["title"])}</h2>'
            f'<div class="note">{esc(s.get("line"))}</div>{SQUIGGLE}{furniture(i, total, False)}</div>')


def tape(s, i, total):
    return (f'<div class="slide dark tape"><div class="ph full" style="{bg(s.get("photo"))}"></div><div class="shade"></div>'
            f'<div class="strip"><h2>{esc(s["title"])}</h2></div><div class="note">{esc(s.get("line"))}</div>'
            f'{furniture(i, total, False)}</div>')


def split(s, i, total):
    return (f'<div class="slide dark split grain"><div class="ph top" style="{bg(s.get("photo"))}"></div>'
            f'<div class="num">{s.get("n", i - 1):02d}</div><div class="text"><h2>{esc(s["title"])}</h2><div class="sub">{esc(s.get("line"))}</div></div>'
            f'{furniture(i, total, False)}</div>')


def polaroid(s, i, total):
    t = esc(s["title"])
    if "|" in t:  # "PART|italic part"
        x, y = t.split("|", 1)
        t = f"{x} <em>{y}</em>"
    return (f'<div class="slide blood polaroid grain"><h2>{t}</h2><div class="pin"></div>'
            f'<div class="frame"><div class="ph" style="{bg(s.get("photo"))}"></div><p>{esc(s.get("line"))}</p></div>'
            f'{furniture(i, total, False)}</div>')


def quote(s, i, total):
    return (f'<div class="slide dark quote"><div class="mark">“</div><h2>{esc(s["title"])}</h2><div class="sub">{esc(s.get("line"))}</div>'
            f'<div class="ph film" style="{bg(s.get("photo"))}"></div><div class="holes" style="bottom:410px"></div>'
            f'<div class="holes" style="bottom:150px"></div>{furniture(i, total, False)}</div>')


def close(s, i, total):
    return (f'<div class="slide paper close grain"><h2>{esc(s["title"])}</h2><div class="big">{esc(s.get("big"))}</div>'
            f'<div class="cta"><div class="icon">{BOOKMARK}</div><p>{esc(s.get("cta"))}</p></div>'
            f'<div class="arrow-note">{esc(s.get("line") or "tap save")}</div>{CURVE}{furniture(i, total, True)}</div>')


LAYOUTS = {"cover": cover, "numeral": numeral, "tape": tape, "split": split, "polaroid": polaroid, "quote": quote, "close": close}

PAGE = """<!doctype html><html><head><meta charset="utf-8"><link rel="stylesheet" href="{css}">
<style>#all .slide{{margin-bottom:20px}}</style></head><body><div id="all">{slides}</div></body></html>"""


def build(post):
    total = len(post["slides"])
    return PAGE.format(css=(HERE / "slides.css").as_uri(),
                       slides="".join(LAYOUTS[s["layout"]](s, i, total) for i, s in enumerate(post["slides"], 1)))


def render(post, outdir, animated=False):
    out = Path(outdir)
    out.mkdir(parents=True, exist_ok=True)
    page = out / f"{post['id']}.html"
    page.write_text(build(post), encoding="utf-8")
    cmd = ["node", str(HERE / "shoot.cjs"), str(page), str(out), post["id"]] + (["--animate", "4"] if animated else [])
    subprocess.run(cmd, check=True)
    paths = [out / f"{post['id']}-{i:02d}.jpg" for i in range(1, len(post["slides"]) + 1)]
    return ([out / f"{post['id']}-01.mp4"] if animated else []) + paths


def main():
    p = argparse.ArgumentParser()
    p.add_argument("posts")
    p.add_argument("post_id")
    p.add_argument("outdir")
    p.add_argument("--animate", action="store_true")
    a = p.parse_args()
    posts = json.loads(Path(a.posts).read_text(encoding="utf-8"))["posts"]
    post = next(x for x in posts if x["id"] == a.post_id)
    for path in render(post, a.outdir, a.animate):
        print(path)


if __name__ == "__main__":
    main()
