"""Mechanical checks for Threads posts and captions (context/creator-voice.md + voice.md). Exit 1 on any error.

    python3 -P tools/threads/lint.py                    # queued, unapproved posts in production/threads/posts.json
    python3 -P tools/threads/lint.py --all              # every post in posts.json
    python3 -P tools/threads/lint.py --captions         # "ready" hook captions in production/listicles/hooks.json
Errors block (fix the text). Warnings are judgement calls: read them, fix most of them.
"""
import difflib, json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BANNED = [
    "rise and grind", "grind never stops", "no days off", "embrace the suck", "when no one is watching",
    "when nobody is watching", "stay hungry", "level up", "this is your sign", "reminder that", "nobody is coming to save you",
    "hardest worker in the room", "trust the process", "beast mode", "alpha", "sigma", "let that sink in", "read that again",
    "unlock", "elevate", "journey", "transform your", "your best self", "wellness", "holistic", "self-care", "mindfulness",
    "link in bio", "stance app",
]
BAIT = re.compile(r"\b(agree\??$|who'?s with me|comment (yes|below|if)|drop a \S+ if|like if|tag someone who|type \w+ if)", re.I | re.M)
EMOJI = re.compile("[\U0001F300-\U0001FAFF☀-➿]")
FAKE_STAT = re.compile(r"\b\d{2}(\.\d)?% of\b", re.I)


def check(text, prior, mode):
    err, warn = [], []
    t = text.lower()
    if "—" in text or "–" in text:
        err.append("em/en dash")
    for b in BANNED:
        if re.search(r"\b" + re.escape(b) + r"\b", t):
            err.append(f"banned phrase: '{b}'")
    if mode == "threads":
        if len(text) > 500:
            err.append(f"{len(text)} chars > 500")
        if re.search(r"#\w", text):
            err.append("hashtag on Threads")
        if re.search(r"https?://|www\.", text):
            err.append("link")
        if EMOJI.search(text):
            warn.append("emoji (voice.md: none on Threads)")
        if BAIT.search(text):
            err.append("engagement bait line")
    else:
        tags = re.findall(r"#\w+", text)
        if not 2 <= len(tags) <= 4:
            warn.append(f"{len(tags)} hashtags (2-4)")
    if FAKE_STAT.search(text):
        warn.append("percentage stat: only with a named real source")
    if re.search(r"\bit'?s not .{2,40}\. it'?s\b", t):
        warn.append("'It's not X. It's Y.' (max once a week)")
    if t.rstrip().endswith("that's the difference."):
        warn.append("ends on 'That's the difference.'")
    first = text.strip().splitlines()[0] if text.strip() else ""
    if len(first.split()) > 14:
        warn.append(f"first line {len(first.split())} words (feed shows the opener; aim <= 12)")
    for p in prior:
        r = difflib.SequenceMatcher(None, t, p.lower()).ratio()
        if r > 0.8:
            err.append(f"near-duplicate of an earlier post ({r:.2f}): '{p.splitlines()[0][:60]}'")
            break
    return err, warn


def main():
    mode = "captions" if "--captions" in sys.argv else "threads"
    errors = 0
    if mode == "threads":
        posts = json.loads((ROOT / "production/threads/posts.json").read_text(encoding="utf-8"))["posts"]
        todo = posts if "--all" in sys.argv else [p for p in posts if p.get("status") == "queued" and not p.get("approved")]
        openers = {}
        for p in todo:
            prior = [q["text"] for q in posts if q is not p]
            texts = [p["text"]] + list(p.get("chain") or [])
            for i, text in enumerate(texts):
                e, w = check(text, prior if i == 0 else [], "threads")
                for x in e:
                    print(f"ERROR {p['id']}{'' if i == 0 else f' chain {i}'}: {x}")
                for x in w:
                    print(f"warn  {p['id']}{'' if i == 0 else f' chain {i}'}: {x}")
                errors += len(e)
            o = " ".join(p["text"].lower().split()[:2])
            openers.setdefault(o, []).append(p["id"])
        for o, ids in openers.items():
            if len(ids) > 2:
                print(f"warn  {len(ids)} posts open with '{o}': {', '.join(ids)} (vary openers)")
        i_posts = [p["id"] for p in todo if re.search(r"\bI\b|\bI'", p["text"])]
        if len(i_posts) > 3:
            print(f"warn  {len(i_posts)} first-person posts this batch (max ~3, facts from founder.md only)")
        print(f"{len(todo)} posts checked, {errors} errors")
    else:
        hooks = json.loads((ROOT / "production/listicles/hooks.json").read_text(encoding="utf-8"))["hooks"]
        for h in [h for h in hooks if h.get("status") == "ready"]:
            prior = [x.get("caption", "") for x in hooks if x is not h]
            e, w = check(h.get("caption", ""), prior, "captions")
            for x in e:
                print(f"ERROR {h['id']}: {x}")
            for x in w:
                print(f"warn  {h['id']}: {x}")
            errors += len(e)
        print(f"captions checked, {errors} errors")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
