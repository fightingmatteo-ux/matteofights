"""List another creator's recent videos through Business Discovery (Meta API), to find footage to fetch.

    python3 -P tools/video/ig_browse.py USERNAME [--grep WORD] [--pages 2]

Prints permalink, views, likes, date and the first caption line for each video, newest first. Read-only. Pass a
permalink to the Fetch video workflow to download it. Only creator/business accounts are visible. Needs FB_USER_TOKEN.
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ig_discovery import IG_ID, ApiError, get  # noqa: E402

FIELDS = "timestamp,caption,like_count,media_type,media_product_type,permalink,view_count"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("user")
    ap.add_argument("--grep", default="")
    ap.add_argument("--pages", type=int, default=2)
    a = ap.parse_args()
    after, rows, name = "", [], a.user
    for _ in range(a.pages):
        page = f".after({after})" if after else ""
        f = f"business_discovery.username({a.user}){{username,followers_count,media{page}.limit(50){{{FIELDS}}}}}"
        try:
            bd = get(IG_ID, fields=f)["business_discovery"]
        except ApiError as e:
            sys.exit(f"{a.user}: {e}")
        name = f"@{bd['username']} ({bd.get('followers_count')} followers)"
        media = bd.get("media", {})
        rows += [m for m in media.get("data", []) if m.get("media_type") == "VIDEO"]
        after = media.get("paging", {}).get("cursors", {}).get("after")
        if not after:
            break
    print(name)
    for m in rows:
        cap = (m.get("caption") or "").replace("\n", " ")
        if a.grep and a.grep.lower() not in cap.lower():
            continue
        print(f"{m.get('timestamp', '')[:10]}  {m.get('view_count') or '-':>9}v {m.get('like_count') or 0:>7}l  "
              f"{m['permalink']}  {cap[:90]}")


if __name__ == "__main__":
    main()
