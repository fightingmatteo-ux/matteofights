"""Download someone else's Instagram reel through Business Discovery (Meta API), no cookies needed.

    python3 -P tools/video/ig_discovery.py URL OUTDIR [--user USERNAME]

Fallback for the Fetch video workflow when yt-dlp is blocked. Finds the reel in the creator's media by
its shortcode, downloads media_url to OUTDIR/video.mp4 and writes OUTDIR/video.info.json in yt-dlp's
field names so the workflow's source.json step works unchanged. If Meta withholds the video (licensed
audio), only video.info.json is written and the workflow commits the caption and stats alone. Without --user the username comes from
oEmbed (needs Meta app review) or, failing that, from scanning the accounts in
production/competitors/accounts.json. Needs FB_USER_TOKEN; only creator/business accounts are visible.
"""
import argparse, json, os, re, sys, urllib.error, urllib.parse, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GRAPH = "https://graph.facebook.com/v23.0"
IG_ID = "17841465098113052"
FIELDS = "timestamp,caption,like_count,comments_count,media_product_type,permalink,view_count,media_url"


class ApiError(Exception):
    pass


def get(path, **params):
    url = f"{GRAPH}/{path}?" + urllib.parse.urlencode({**params, "access_token": os.environ["FB_USER_TOKEN"]})
    try:
        return json.load(urllib.request.urlopen(url, timeout=60))
    except urllib.error.HTTPError as e:
        raise ApiError(f"Meta API: {json.loads(e.read()).get('error', {}).get('message', e)}")


def find(code, user, max_posts):
    """(post, profile) for this shortcode in @user's media, or None."""
    after, seen, prof = None, 0, None
    while seen < max_posts:
        page = f".after({after})" if after else ""
        f = f"business_discovery.username({user}){{username,followers_count,media{page}.limit(50){{{FIELDS}}}}}"
        bd = get(IG_ID, fields=f)["business_discovery"]
        prof = prof or bd
        media = bd.get("media", {})
        for post in media.get("data", []):
            if f"/{code}/" in (post.get("permalink") or ""):
                return post, prof
        seen += len(media.get("data", []))
        after = media.get("paging", {}).get("cursors", {}).get("after")
        if not after or not media.get("data"):
            break
    print(f"{code} not in @{user}'s last {seen} posts")
    return None


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
    users = [a.user.lstrip("@")] if a.user else []
    if not users:
        try:
            users = [get("instagram_oembed", url=f"https://www.instagram.com/reel/{code}/")["author_name"]]
        except (ApiError, KeyError) as e:
            print(f"oEmbed lookup failed ({e}); scanning tracked competitors")
            accounts = json.loads((ROOT / "production/competitors/accounts.json").read_text(encoding="utf-8"))["accounts"]
            users = [x["handle"] for x in accounts if x.get("platform") == "instagram"]
            a.max_posts = min(a.max_posts, 100)  # stay inside Business Discovery's rate limit across many accounts
    for user in users:
        try:
            hit = find(code, user, a.max_posts)
        except ApiError as e:
            print(f"@{user}: {e}")
            continue
        if hit:
            return save(*hit, a.outdir)
    sys.exit("reel not found; rerun with the creator's username in the 'user' input")


def embed_video_url(permalink):
    """The public embed page often carries the mp4 even when the API withholds media_url."""
    m = re.search(r"/(?:reel|reels|p|tv)/([A-Za-z0-9_-]+)", permalink)
    if not m:
        return None
    req = urllib.request.Request(f"https://www.instagram.com/p/{m.group(1)}/embed/captioned/",
                                 headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/130.0 Safari/537.36"})
    try:
        html = urllib.request.urlopen(req, timeout=60).read().decode("utf-8", "replace")
    except urllib.error.URLError as e:
        print(f"embed page: {e}")
        return None
    # video_url sits in JSON that may be escaped once or twice: strip the backslashes, then decode \u0026
    flat = html.replace("\\", "")
    hit = re.search(r'video_url":"(https:[^"]+)"', flat)
    if not hit:
        print("embed page has no video_url")
        return None
    return hit.group(1).replace("u0026", "&")


def save(post, prof, outdir):
    out = Path(outdir)
    out.mkdir(parents=True, exist_ok=True)
    url = post.get("media_url") or embed_video_url(post.get("permalink") or "")
    if url:
        urllib.request.urlretrieve(url, out / "video.mp4")
    else:
        print("Meta API returned no media_url (licensed audio) and the embed page had none: saving caption and stats only")
    info = {"uploader": prof.get("username"), "uploader_id": prof.get("username"), "channel": prof.get("username"),
            "followers": prof.get("followers_count"), "description": post.get("caption"),
            "timestamp": post.get("timestamp"), "view_count": post.get("view_count"),
            "like_count": post.get("like_count"), "comment_count": post.get("comments_count"),
            "webpage_url": post.get("permalink")}
    (out / "video.info.json").write_text(json.dumps(info, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"@{prof.get('username')}: {post.get('view_count')} views -> {out}")


if __name__ == "__main__":
    main()
