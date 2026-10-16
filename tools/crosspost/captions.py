"""Per-platform captions from one Instagram caption (production/.../caption.txt).

Instagram captions look like: opener lines / "6 signs ...:" / numbered items / CTA line / hashtags.
Each platform gets its own shape (research 2026-10-16, see tools/crosspost/README.md):
  facebook  short conversational hook + the list + a real question, 0-3 hashtags, no IG-only CTAs
  youtube   keyword-first title (#shorts) + description with the list + 3 hashtags
  threads   hook first, list, question; no hashtags (one topic tag is sent separately)
"""
import re

IG_ONLY = re.compile(r"(link in (my )?bio|repost this|follow @|on instagram|comment help|dm .?help)", re.I)
QUESTION = "Which one is you? Drop the number."
FB_TAGS = "#fightermindset #mma #boxing"
YT_TAGS = "#fightermindset #mma #boxing"
TOPIC = "Fight Psychology"


def parse(text, hook=""):
    lines = [l.rstrip() for l in text.strip().splitlines()]
    tags = [l for l in lines if re.fullmatch(r"\s*(#\S+\s*)+", l)]
    body = [l for l in lines if l not in tags]
    items = [l for l in body if re.match(r"^\s*\d+[.)]\s+", l)]
    title = next((l for l in body if l.rstrip().endswith(":") and not re.match(r"^\s*\d+[.)]\s", l)), "")
    first_item = body.index(items[0]) if items else len(body)
    opener = [l for l in body[:first_item] if l.strip() and l != title]
    after = [l for l in body[first_item:] if l.strip() and l not in items]
    return {"hook": hook.strip(), "opener": opener, "title": title, "items": items, "after": after,
            "tags": " ".join(tags).split()}


def sentence_case(s):
    s = s.strip().rstrip(".:")
    return s[0].upper() + s[1:].lower() if s.isupper() else s


def prose(text):
    """A talking-head caption (no list) keeps its paragraphs: drop hashtags and IG-only lines, nothing else."""
    lines = [l for l in text.strip().splitlines() if not re.fullmatch(r"\s*(#\S+\s*)+", l) and not IG_ONLY.search(l)]
    return re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip()


def facebook(text, hook=""):
    p = parse(text, hook)
    if not p["items"]:
        return prose(text) + "\n\n" + FB_TAGS
    out = p["opener"][:2] + [""] + ([p["title"]] if p["title"] else []) + p["items"] + ["", QUESTION, "", FB_TAGS]
    return "\n".join(out).strip()


def youtube_title(text, hook=""):
    p = parse(text, hook)
    t = sentence_case(hook or p["title"] or (p["opener"] or ["Fighter mindset"])[0])
    t = " ".join(w if w.lower() in {"a", "an", "the", "for", "of", "to", "in", "on", "and", "or"} and i
                 else w[:1].upper() + w[1:] for i, w in enumerate(t.split()))
    return (t[:85].rstrip() + " 🥊 #shorts")


def youtube_description(text, hook=""):
    p = parse(text, hook)
    lines = p["opener"][:2] + [""] + ([p["title"]] if p["title"] else []) + p["items"]
    if not p["items"]:
        lines = [prose(text)]
    return "\n".join(lines + ["", "New fighter mindset Shorts every day. Subscribe.", "", YT_TAGS]).strip()


def threads(text, hook=""):
    p = parse(text, hook)
    if not p["items"]:
        return prose(text)[:500]
    head = sentence_case(hook) if hook else (p["opener"][0] if p["opener"] else p["title"])
    body = [head, ""] + p["items"] + ["", QUESTION]
    out = "\n".join(body)
    return out if len(out) <= 500 else "\n".join([head, ""] + p["items"])[:500]


def slides(text, hook=""):
    """Facebook/TikTok carousel content: (hook, [item texts without numbers], cta) or None if not a list."""
    p = parse(text, hook)
    if len(p["items"]) < 3:
        return None
    items = [re.sub(r"^\s*\d+[.)]\s+", "", i) for i in p["items"]]
    return (hook or p["title"]).strip().rstrip(":"), items, QUESTION
