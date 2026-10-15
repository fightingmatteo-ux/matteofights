"""Measure the creators in production/competitors/accounts.json and flag their outliers.

    python3 -P tools/competitors/scout.py            # all accounts (the Competitors workflow runs this weekly)
    python3 -P tools/competitors/scout.py --only instagram

An outlier is a post that did >= OUTLIER_X times that creator's own median on that platform: proof the idea
worked, independent of how big the account is. Writes production/competitors/outliers.json
(accounts with followers/median, outliers newest-evidence first). Read-only.
Instagram: Business Discovery (FB_USER_TOKEN, creator/business accounts only). YouTube: public Shorts via yt-dlp.
"""
import datetime as dt, json, re, statistics as st, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "instagram"))
DIR = ROOT / "production" / "competitors"
OUTLIER_X = 3.0
MIN_POSTS = 8        # fewer posts than this and a median means nothing
IG_POSTS, YT_SHORTS = 50, 50


def hook(text):
    line = next((l.strip() for l in (text or "").splitlines() if l.strip()), "")
    return re.sub(r"\s+", " ", line)[:140]


def instagram(acc):
    import competitors as c  # tools/instagram/competitors.py
    prof, err = c.discover(acc["handle"], IG_POSTS)
    if err:
        return None, err
    posts = [{"id": p.get("permalink", "").rstrip("/").split("/")[-1], "url": p.get("permalink"), "views": p.get("view_count"),
              "likes": p.get("like_count"), "comments": p.get("comments_count"), "hook": hook(p.get("caption")),
              "posted_at": (p.get("timestamp") or "")[:19] + "Z" if p.get("timestamp") else None}
             for p in prof["posts"] if p.get("media_product_type") == "REELS" and p.get("view_count")]
    return {"followers": prof.get("followers_count"), "posts": posts}, None


def youtube(acc):
    r = subprocess.run([sys.executable, "-m", "yt_dlp", "--flat-playlist", "-J", "--playlist-end", str(YT_SHORTS),
                        f"https://www.youtube.com/@{acc['handle']}/shorts"], capture_output=True, text=True, timeout=300)
    try:
        d = json.loads(r.stdout)
    except ValueError:
        return None, (r.stderr.strip().splitlines() or ["no output"])[-1][:200]
    posts = [{"id": e["id"], "url": e.get("url") or f"https://www.youtube.com/shorts/{e['id']}", "views": e.get("view_count"),
              "hook": hook(e.get("title")), "rank": i} for i, e in enumerate(d.get("entries") or []) if e.get("view_count")]
    return {"followers": d.get("channel_follower_count"), "posts": posts}, None


FETCH = {"instagram": instagram, "youtube": youtube}


def main():
    only = sys.argv[sys.argv.index("--only") + 1] if "--only" in sys.argv else None
    accounts = json.loads((DIR / "accounts.json").read_text(encoding="utf-8"))["accounts"]
    old = json.loads((DIR / "outliers.json").read_text(encoding="utf-8")) if (DIR / "outliers.json").exists() else {}
    seen = {o["id"]: o.get("first_seen") for o in old.get("outliers", [])}
    today = dt.date.today().isoformat()
    out_acc, outliers, errors = [], [], []
    for acc in accounts:
        if only and acc["platform"] != only or acc["platform"] not in FETCH:
            continue
        try:
            data, err = FETCH[acc["platform"]](acc)
        except Exception as e:  # one account failing must not stop the rest
            data, err = None, str(e)[:200]
        if err:
            errors.append(f"{acc['platform']} @{acc['handle']}: {err}")
            print("  !", errors[-1])
            continue
        views = [p["views"] for p in data["posts"]]
        med = st.median(views) if len(views) >= MIN_POSTS else None
        out_acc.append({**acc, "followers": data["followers"], "posts_n": len(views), "median_views": round(med) if med else None,
                        "max_views": max(views) if views else None})
        if not med:
            continue
        for p in data["posts"]:
            x = p["views"] / med
            if x >= OUTLIER_X:
                outliers.append({**p, "platform": acc["platform"], "handle": acc["handle"], "name": acc["name"],
                                 "x": round(x, 1), "median_views": round(med), "first_seen": seen.get(p["id"]) or today})
        print(f"{acc['platform']:9} @{acc['handle']:22} median {round(med):>8,}  outliers {sum(1 for o in outliers if o['handle'] == acc['handle'])}")
    if only:  # keep the other platforms from the last run
        out_acc += [a for a in old.get("accounts", []) if a["platform"] != only]
        outliers += [o for o in old.get("outliers", []) if o["platform"] != only]
    outliers.sort(key=lambda o: (-o["x"], -o["views"]))
    DIR.mkdir(parents=True, exist_ok=True)
    (DIR / "outliers.json").write_text(json.dumps({
        "updated": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "rule": f">= {OUTLIER_X:g}x the creator's own median",
        "accounts": out_acc, "outliers": outliers, "errors": errors}, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"{len(out_acc)} accounts, {len(outliers)} outliers, {len(errors)} errors")


if __name__ == "__main__":
    main()
