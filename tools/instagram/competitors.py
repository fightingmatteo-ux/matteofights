"""Pull competitors' recent posts via Business Discovery and rank their reels' hooks.

    python -P tools/instagram/competitors.py                 # everyone in context/competitors.md
    python -P tools/instagram/competitors.py someuser other  # just these
    python -P tools/instagram/competitors.py --posts 100

Writes analytics/snapshots/<date>-competitors.json (raw) and analytics/reports/<date>-competitors.md
(top reels by views and by views per follower, with the hook = first caption line).
Needs FB_USER_TOKEN (secrets/meta.env or env). Only creator/business accounts are visible.
"""
import argparse, datetime as dt, json, os, re, sys, urllib.error, urllib.parse, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
IG_ID = "17841465098113052"
FIELDS = "timestamp,caption,like_count,comments_count,media_product_type,permalink,view_count,media_url"


def token():
    if not os.environ.get("FB_USER_TOKEN"):
        for l in (ROOT / "secrets" / "meta.env").read_text(encoding="utf-8").splitlines():
            if l.startswith("FB_USER_TOKEN="):
                os.environ["FB_USER_TOKEN"] = l.split("=", 1)[1].strip()
    return os.environ["FB_USER_TOKEN"]


def discover(user, n):
    posts, after, prof = [], None, None
    while len(posts) < n:
        page = f".after({after})" if after else ""
        f = f"business_discovery.username({user}){{username,name,followers_count,media_count,biography,media{page}.limit({min(50, n - len(posts))}){{{FIELDS}}}}}"
        url = f"https://graph.facebook.com/v23.0/{IG_ID}?" + urllib.parse.urlencode({"fields": f, "access_token": token()})
        try:
            bd = json.load(urllib.request.urlopen(url, timeout=60))["business_discovery"]
        except urllib.error.HTTPError as e:
            msg = json.loads(e.read()).get("error", {}).get("message", "")
            return None, f"{user}: {msg}"
        prof = prof or {k: bd.get(k) for k in ("username", "name", "followers_count", "media_count", "biography")}
        media = bd.get("media", {})
        posts += media.get("data", [])
        after = media.get("paging", {}).get("cursors", {}).get("after")
        if not after or not media.get("data"):
            break
    return {**prof, "posts": posts}, None


def hook(caption):
    line = next((l.strip() for l in (caption or "").splitlines() if l.strip()), "")
    return re.sub(r"\s+", " ", line)[:110]


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser()
    p.add_argument("users", nargs="*")
    p.add_argument("--posts", type=int, default=50)
    a = p.parse_args()
    users = a.users or re.findall(r"^\s*-\s*@?([A-Za-z0-9._]+)", (ROOT / "context" / "competitors.md").read_text(encoding="utf-8"), re.M)
    today = dt.date.today().isoformat()
    accounts, errors = [], []
    for u in users:
        acc, err = discover(u, a.posts)
        (errors.append(err) if err else accounts.append(acc))
        print(err or f"{u}: {acc['followers_count']:,} followers, {len(acc['posts'])} posts")

    (ROOT / "analytics" / "snapshots" / f"{today}-competitors.json").write_text(
        json.dumps({"pulled": today, "accounts": accounts, "errors": errors}, indent=1, ensure_ascii=False), encoding="utf-8")

    reels = []
    for acc in accounts:
        for m in acc["posts"]:
            if m.get("media_product_type") == "REELS" and m.get("view_count"):
                reels.append({**m, "user": acc["username"], "followers": acc["followers_count"] or 1,
                              "vpf": m["view_count"] / (acc["followers_count"] or 1), "hook": hook(m.get("caption"))})

    def table(rows):
        out = ["| Account | Views | Views/follower | Likes | Comments | Hook (first caption line) |", "|---|---|---|---|---|---|"]
        for r in rows:
            out.append(f"| [@{r['user']}]({r['permalink']}) | {r['view_count']:,} | {r['vpf']:.1f}x | {r.get('like_count') or 0:,} "
                       f"| {r.get('comments_count') or 0:,} | {r['hook'].replace('|', '/')} |")
        return "\n".join(out)

    md = [f"# Competitor reels, {today}", "",
          "Business Discovery (Meta API). Views/follower = how far a reel travelled beyond the account's audience: "
          "the best signal for hooks that break out.", "",
          "## Accounts", "| Account | Followers | Reels pulled | Median views |", "|---|---|---|---|"]
    for acc in accounts:
        v = sorted(r["view_count"] for r in reels if r["user"] == acc["username"])
        md.append(f"| @{acc['username']} | {acc['followers_count']:,} | {len(v)} | {v[len(v)//2]:,} |" if v else
                  f"| @{acc['username']} | {acc['followers_count']:,} | 0 | - |")
    md += ["", "## Top 25 by views per follower (broke out of their own audience)", table(sorted(reels, key=lambda r: -r["vpf"])[:25]),
           "", "## Top 25 by raw views", table(sorted(reels, key=lambda r: -r["view_count"])[:25])]
    if errors:
        md += ["", "## Not visible", *[f"- {e}" for e in errors]]
    (ROOT / "analytics" / "reports").mkdir(parents=True, exist_ok=True)
    out = ROOT / "analytics" / "reports" / f"{today}-competitors.md"
    out.write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"report: {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
