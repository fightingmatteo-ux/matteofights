"""Find carousels that already proved themselves, so every @matteofights carousel starts from a proven hook.

    python3 -P tools/carousel/scout.py [--posts 60] [user ...]
    python3 -P tools/carousel/scout.py --survey user1 user2 ...   # rank candidate accounts by carousel performance

Weekly (Carousel workflow, Mondays). Pulls the recent posts of every account in production/carousels/accounts.json
(plus the Instagram competitors in production/competitors/accounts.json) through Business Discovery, keeps the
carousels, and marks an outlier when its likes + 3x comments is at least 2x that account's median carousel and
above a floor. Each new outlier gets slides 1-2 saved to production/carousels/proven/<code>/ and an entry in
production/carousels/proven.json with status "unread". Claude then reads slide 1 (the hook as written on the slide),
fills `hook` and `pattern` and sets status "read". Only "read" entries can be used: tools/carousel/lint.py refuses a
carousel without a `hook_ref` to one, or to one of our own proven reel hooks (the "own" list in proven.json).
Business Discovery shows no views or saves for other accounts' posts, so likes and comments are the signal.
Needs FB_USER_TOKEN.
"""
import argparse, datetime as dt, json, os, statistics, sys, urllib.error, urllib.parse, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DIR = ROOT / "production" / "carousels"
PROVEN = DIR / "proven.json"
IG_ID = "17841465098113052"
FIELDS = "timestamp,caption,like_count,comments_count,media_type,permalink,children{media_type,media_url}"
MIN_X, FLOOR, SAVE_SLIDES = 2.0, 300, 2


def get(**params):
    url = f"https://graph.facebook.com/v23.0/{IG_ID}?" + urllib.parse.urlencode({**params, "access_token": os.environ["FB_USER_TOKEN"]})
    try:
        return json.load(urllib.request.urlopen(url, timeout=60))
    except urllib.error.HTTPError as e:
        raise RuntimeError(json.loads(e.read()).get("error", {}).get("message", str(e)))


def posts_of(user, n):
    posts, after, followers = [], None, None
    while len(posts) < n:
        page = f".after({after})" if after else ""
        bd = get(fields=f"business_discovery.username({user}){{followers_count,media{page}.limit({min(50, n - len(posts))}){{{FIELDS}}}}}")["business_discovery"]
        followers = followers or bd.get("followers_count")
        media = bd.get("media", {})
        posts += media.get("data", [])
        after = media.get("paging", {}).get("cursors", {}).get("after")
        if not after or not media.get("data"):
            break
    return followers, posts


def score(p):
    return (p.get("like_count") or 0) + 3 * (p.get("comments_count") or 0)


def code_of(permalink):
    return permalink.rstrip("/").rsplit("/", 1)[-1]


def accounts():
    users = json.loads((DIR / "accounts.json").read_text(encoding="utf-8"))["accounts"]
    comp = json.loads((ROOT / "production/competitors/accounts.json").read_text(encoding="utf-8"))["accounts"]
    users += [a["handle"] for a in comp if a.get("platform") == "instagram"]
    return list(dict.fromkeys(u.lstrip("@") for u in users))


def survey(users, n):
    """Which accounts' carousels perform: per account, carousels in the last n posts, median carousel score
    (likes + 3x comments) per 1k followers, and how carousels do vs that account's reels. Writes a report."""
    rows = []
    for user in users:
        try:
            followers, posts = posts_of(user, n)
        except RuntimeError as e:
            print(f"@{user}: {e}")
            continue
        cars = [x for x in posts if x.get("media_type") == "CAROUSEL_ALBUM"]
        vids = [x for x in posts if x.get("media_type") == "VIDEO"]
        if not cars or not followers:
            print(f"@{user}: {len(cars)} carousels")
            continue
        med = statistics.median(score(x) for x in cars)
        best = max(cars, key=score)
        rows.append({"user": user, "followers": followers, "carousels": len(cars), "of": len(posts),
                     "median": med, "per_k": round(1000 * med / followers, 2),
                     "vs_reels": round(med / statistics.median(score(x) for x in vids), 2) if vids else None,
                     "best": best["permalink"], "best_score": score(best),
                     "best_line": (best.get("caption") or "").strip().split("\n")[0][:70]})
        print(f"@{user}: {len(cars)}/{len(posts)} carousels, median {med:.0f} ({rows[-1]['per_k']}/1k followers)")
    rows.sort(key=lambda r: (r["carousels"] >= 5, r["per_k"]), reverse=True)
    lines = [f"# Carousel accounts survey, {dt.date.today().isoformat()}", "",
             "Score = likes + 3x comments (Business Discovery shows no views or saves). Ranked by median carousel score per 1k "
             "followers, accounts with 5+ carousels first.", "",
             "| Account | Followers | Carousels | Median score | Per 1k followers | vs their reels | Best carousel |", "|---|---|---|---|---|---|---|"]
    for r in rows:
        lines.append(f"| @{r['user']} | {r['followers']:,} | {r['carousels']}/{r['of']} | {r['median']:.0f} | {r['per_k']} | "
                     f"{r['vs_reels'] if r['vs_reels'] is not None else '-'} | [{r['best_score']:,}]({r['best']}) {r['best_line'].replace('|', '/')} |")
    out = ROOT / "analytics" / "reports" / f"{dt.date.today().isoformat()}-carousel-accounts.md"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"-> {out.relative_to(ROOT)}")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("users", nargs="*")
    p.add_argument("--posts", type=int, default=60)
    p.add_argument("--survey", action="store_true")
    a = p.parse_args()
    if a.survey:
        return survey([u.lstrip("@") for raw in a.users for u in raw.replace(",", " ").split()], a.posts)
    bank = json.loads(PROVEN.read_text(encoding="utf-8"))
    known = {e["code"] for e in bank["carousels"]}
    added, errors = 0, []
    for user in a.users or accounts():
        try:
            followers, posts = posts_of(user, a.posts)
        except RuntimeError as e:
            errors.append(f"@{user}: {e}")
            print(errors[-1])
            continue
        cars = [x for x in posts if x.get("media_type") == "CAROUSEL_ALBUM"]
        if len(cars) < 3:
            print(f"@{user}: {len(cars)} carousels, too few to judge")
            continue
        med = statistics.median(score(x) for x in cars) or 1
        for c in cars:
            x = score(c) / med
            code = code_of(c["permalink"])
            if x < MIN_X or score(c) < FLOOR or code in known:
                continue
            out = DIR / "proven" / code
            out.mkdir(parents=True, exist_ok=True)
            slides = []
            for i, kid in enumerate((c.get("children") or {}).get("data", [])[:SAVE_SLIDES], 1):
                if kid.get("media_type") == "IMAGE" and kid.get("media_url"):
                    urllib.request.urlretrieve(kid["media_url"], out / f"{i:02d}.jpg")
                    slides.append(f"production/carousels/proven/{code}/{i:02d}.jpg")
            bank["carousels"].append({
                "code": code, "user": user, "followers": followers, "permalink": c["permalink"],
                "posted": c.get("timestamp"), "likes": c.get("like_count"), "comments": c.get("comments_count"),
                "x_median": round(x, 2), "caption_first_line": (c.get("caption") or "").strip().split("\n")[0][:160],
                "slides": slides, "status": "unread", "hook": None, "pattern": None, "found": dt.date.today().isoformat()})
            known.add(code)
            added += 1
            print(f"@{user}: {code} {x:.1f}x median ({score(c)})")
    bank["updated"] = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%MZ")
    bank["errors"] = errors
    PROVEN.write_text(json.dumps(bank, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"{added} new proven carousels; {sum(e['status'] == 'unread' for e in bank['carousels'])} waiting for Claude to read")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
