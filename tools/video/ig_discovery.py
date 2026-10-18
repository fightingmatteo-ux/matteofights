"""Download someone else's Instagram reel through Business Discovery (Meta API), no cookies needed.

    python3 -P tools/video/ig_discovery.py URL OUTDIR [--user USERNAME]

Fallback for the Fetch video workflow when yt-dlp is blocked. Finds the reel in the creator's media by
its shortcode, downloads media_url to OUTDIR/video.mp4 and writes OUTDIR/video.info.json in yt-dlp's
field names so the workflow's source.json step works unchanged. Without --user the username comes from
oEmbed. Needs FB_USER_TOKEN; only creator/business accounts are visible.
"""
import argparse, json, os, re, sys, urllib.error, urllib.parse, urllib.request
from pathlib import Path

GRAPH = "https://graph.facebook.com/v23.0"
IG_ID = "17841465098113052"
FIELDS = "timestamp,caption,like_count,comments_count,media_product_type,permalink,view_count,media_url"


def get(path, **params):
    url = f"{GRAPH}/{path}?" + urllib.parse.urlencode({**params, "access_token": os.environ["FB_USER_TOKEN"]})
    try:
        return json.load(urllib.request.urlopen(url, timeout=60))
    except urllib.error.HTTPError as e:
        sys.exit(f"Meta API: {json.loads(e.read()).get('error', {}).get('message', e)}")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("url")
    p.add_argument("outdir")
    p.add_argument("--user", default="")
    p.add_argument("--max-posts", type=int, default=600)
    a = p.parse_args()

    m = re.search(r"/(?:reel|reels|p|tv)/([A-Za-z0-9_-]+)", a.url)
    if not m:
        sys.exit("not an Instagram post link")
    code = m.group(1)
    user = a.user.lstrip("@") or get("instagram_oembed", url=f"https://www.instagram.com/reel/{code}/").get("author_name", "")
    if not user:
        sys.exit("couldn't find the creator's username; pass --user")

    after, seen, prof = None, 0, None
    while seen < a.max_posts:
        page = f".after({after})" if after else ""
        f = f"business_discovery.username({user}){{username,followers_count,media{page}.limit(50){{{FIELDS}}}}}"
        bd = get(IG_ID, fields=f)["business_discovery"]
        prof = prof or bd
        media = bd.get("media", {})
        for post in media.get("data", []):
            if f"/{code}/" in (post.get("permalink") or ""):
                return save(post, prof, a.outdir)
        seen += len(media.get("data", []))
        after = media.get("paging", {}).get("cursors", {}).get("after")
        if not after or not media.get("data"):
            break
    sys.exit(f"{code} not found in @{user}'s last {seen} posts")


def save(post, prof, outdir):
    if not post.get("media_url"):
        sys.exit("Meta API returned no media_url for this reel (copyrighted audio or restricted)")
    out = Path(outdir)
    out.mkdir(parents=True, exist_ok=True)
    urllib.request.urlretrieve(post["media_url"], out / "video.mp4")
    info = {"uploader": prof.get("username"), "uploader_id": prof.get("username"), "channel": prof.get("username"),
            "followers": prof.get("followers_count"), "description": post.get("caption"),
            "timestamp": post.get("timestamp"), "view_count": post.get("view_count"),
            "like_count": post.get("like_count"), "comment_count": post.get("comments_count"),
            "webpage_url": post.get("permalink")}
    (out / "video.info.json").write_text(json.dumps(info, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"@{prof.get('username')}: {post.get('view_count')} views -> {out / 'video.mp4'}")


if __name__ == "__main__":
    main()
