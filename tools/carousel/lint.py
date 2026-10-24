"""Gate for production/carousels/posts.json: a carousel that fails here is not rendered or queued.

    python3 -P tools/carousel/lint.py [POST_ID ...]     # exit 1 on any failure (drafts are skipped)

Rules: hook_ref points to a proven hook (an 'own' id or a 'read' carousel in proven.json), 5-10 slides, a cover
first and a close last, every photo exists, no em dashes anywhere, caption <= 2,200 characters with at most 4
hashtags, and the close has one CTA.
"""
import json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DIR = ROOT / "production" / "carousels"


def problems(post, proven):
    out = []
    refs = {o["id"] for o in proven["own"]} | {c["code"] for c in proven["carousels"] if c["status"] == "read"}
    if post.get("hook_ref") not in refs:
        out.append(f"hook_ref {post.get('hook_ref')!r} is not a proven hook (own id or a 'read' carousel in proven.json)")
    slides = post.get("slides", [])
    if not 5 <= len(slides) <= 10:
        out.append(f"{len(slides)} slides (5-10)")
    if slides and (slides[0].get("kind") != "cover" or slides[-1].get("kind") != "close"):
        out.append("first slide must be the cover and the last the close")
    for i, s in enumerate(slides, 1):
        if s.get("photo") and not (ROOT / s["photo"]).exists():
            out.append(f"slide {i}: photo {s['photo']} not found")
    text = json.dumps(post, ensure_ascii=False)
    if "—" in text:
        out.append("em dash in the copy (use a period)")
    cap = post.get("caption", "")
    if len(cap) > 2200 or len(re.findall(r"#\w+", cap)) > 4:
        out.append("caption over 2,200 characters or more than 4 hashtags")
    if slides and not slides[-1].get("cta"):
        out.append("close slide has no cta")
    return out


def main():
    posts = json.loads((DIR / "posts.json").read_text(encoding="utf-8"))["posts"]
    proven = json.loads((DIR / "proven.json").read_text(encoding="utf-8"))
    ids = set(sys.argv[1:])
    bad = 0
    for p in posts:
        if (ids and p["id"] not in ids) or (not ids and p.get("status") == "draft"):
            continue
        for msg in problems(p, proven):
            print(f"{p['id']}: {msg}")
            bad += 1
    print(f"{bad} problem(s)" if bad else "carousels OK")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
