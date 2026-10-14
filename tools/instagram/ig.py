"""Post @matteofights trial reels through our own Meta app (Instagram API with Instagram Login).

Nothing goes out without --confirm. Without it, `trial` only prints the preview.

    python -P tools/instagram/ig.py whoami
    python -P tools/instagram/ig.py refresh                     # extend the 60-day token
    python -P tools/instagram/ig.py trial --video media/x/x-A.mp4 --caption-file production/reels/<slug>/caption-A.txt
    python -P tools/instagram/ig.py trial ... --confirm         # only after Matteo said yes to the preview
    python -P tools/instagram/ig.py status <container_id>
    python -P tools/instagram/ig.py insights                    # per-reel metrics -> analytics/snapshots/<date>-graph.json

Token: secrets/meta.env (IG_ACCESS_TOKEN=..., IG_USER_ID=...), or the same names as env vars
(GitHub Actions secrets). Upload is resumable straight to Meta, so the video needs no public URL.
"""
import argparse, json, os, sys, time, urllib.error, urllib.parse, urllib.request
from datetime import datetime, timezone
from pathlib import Path

API = "v23.0"
GRAPH = f"https://graph.instagram.com/{API}"
RUPLOAD = f"https://rupload.facebook.com/ig-api-upload/{API}"
ROOT = Path(__file__).resolve().parents[2]
ENV_FILE = ROOT / "secrets" / "meta.env"
# Reel insights (Instagram Login, needs instagram_business_manage_insights). Skip rate is newer; asked separately.
REEL_METRICS = "reach,views,likes,comments,shares,saved,total_interactions,ig_reels_avg_watch_time,ig_reels_video_view_total_time"


def load_env():
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())
    if not os.environ.get("IG_ACCESS_TOKEN"):
        sys.exit(f"No IG_ACCESS_TOKEN (put it in {ENV_FILE} or the environment).")


def call(method, url, params=None, data=None, headers=None, fatal=True):
    params = dict(params or {})
    if "graph.instagram.com" in url:
        params["access_token"] = os.environ["IG_ACCESS_TOKEN"]
    if params:
        url += ("&" if "?" in url else "?") + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, data=data, method=method, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=600) as r:
            return json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        if not fatal:
            return {"error": e.read().decode(errors="replace")}
        sys.exit(f"{method} {url.split('?')[0]} -> {e.code}: {e.read().decode(errors='replace')}")


def whoami():
    me = call("GET", f"{GRAPH}/me", {"fields": "user_id,username,account_type,followers_count,media_count"})
    print(json.dumps(me, indent=1))
    return me


def refresh():
    r = call("GET", "https://graph.instagram.com/refresh_access_token", {"grant_type": "ig_refresh_token"})
    if ENV_FILE.exists():
        lines = [l for l in ENV_FILE.read_text(encoding="utf-8").splitlines() if not l.startswith("IG_ACCESS_TOKEN=")]
        lines.insert(0, f"IG_ACCESS_TOKEN={r['access_token']}")
        ENV_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Token refreshed, valid for {r.get('expires_in', 0) // 86400} days." + ("" if ENV_FILE.exists() else " Update the IG_ACCESS_TOKEN secret."))


def status(cid):
    return call("GET", f"{GRAPH}/{cid}", {"fields": "status_code,status"})


def trial(a):
    video = Path(a.video)
    if not video.is_file():
        sys.exit(f"Video not found: {video}")
    caption = Path(a.caption_file).read_text(encoding="utf-8").strip() if a.caption_file else (a.caption or "")
    size = video.stat().st_size
    me = call("GET", f"{GRAPH}/me", {"fields": "user_id,username"})
    user_id = os.environ.get("IG_USER_ID") or me["user_id"]

    print("=" * 60)
    print("PREVIEW: trial reel (nothing is sent without --confirm)")
    print(f"  account   @{me['username']} ({user_id})")
    print(f"  video     {video} ({size / 1e6:.1f} MB)")
    print(f"  trial     {a.strategy} ({'you share it to followers in the app' if a.strategy == 'MANUAL' else 'Instagram shares it if it performs'})")
    if a.thumb_offset is not None:
        print(f"  cover     frame at {a.thumb_offset} ms")
    print(f"  caption   ({len(caption)} chars)")
    print("  " + "\n  ".join(caption.splitlines() or ["(empty)"]))
    print("=" * 60)
    if not a.confirm:
        print("Preview only. Re-run with --confirm after the explicit yes.")
        return

    params = {
        "media_type": "REELS",
        "upload_type": "resumable",
        "caption": caption,
        "trial_params": json.dumps({"graduation_strategy": a.strategy}),
    }
    if a.thumb_offset is not None:
        params["thumb_offset"] = a.thumb_offset
    cid = call("POST", f"{GRAPH}/{user_id}/media", params)["id"]
    print(f"container {cid}, uploading...")
    call("POST", f"{RUPLOAD}/{cid}", data=video.read_bytes(), headers={
        "Authorization": f"OAuth {os.environ['IG_ACCESS_TOKEN']}",
        "offset": "0",
        "file_size": str(size),
    })
    for _ in range(60):  # Meta processes the video; up to ~10 min
        s = status(cid)
        if s.get("status_code") == "FINISHED":
            break
        if s.get("status_code") in ("ERROR", "EXPIRED"):
            sys.exit(f"Processing failed: {s}")
        time.sleep(10)
    else:
        sys.exit(f"Still processing after 10 min. Check later: ig.py status {cid}")
    media_id = call("POST", f"{GRAPH}/{user_id}/media_publish", {"creation_id": cid})["id"]
    link = call("GET", f"{GRAPH}/{media_id}", {"fields": "permalink"}).get("permalink")
    print(f"PUBLISHED trial reel: media id {media_id}  {link}")
    if a.slug and a.variant:
        sys.path.insert(0, str(ROOT / "tools" / "analytics"))
        import ledger
        ledger.link(media_id, a.slug, a.variant, None)


def insights(a):
    """Per-reel metrics in the Buzzfy snapshot shape, for tools/analytics/ledger.py."""
    me = call("GET", f"{GRAPH}/me", {"fields": "user_id,username,followers_count"})
    user_id = os.environ.get("IG_USER_ID") or me["user_id"]
    pulled = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    url, params, media = f"{GRAPH}/{user_id}/media", {"fields": "id,caption,media_product_type,timestamp,permalink", "limit": 50}, []
    while url and len(media) < a.limit:
        page = call("GET", url, params)
        media += page.get("data", [])
        nxt = page.get("paging", {}).get("next")
        if nxt:  # keep its cursor, drop its token (call() adds ours)
            u = urllib.parse.urlsplit(nxt)
            url, params = f"{u.scheme}://{u.netloc}{u.path}", {k: v for k, v in urllib.parse.parse_qsl(u.query) if k != "access_token"}
        else:
            url = None
    posts = []
    for m in media[: a.limit]:
        if m.get("media_product_type") != "REELS":
            continue
        r = call("GET", f"{GRAPH}/{m['id']}/insights", {"metric": REEL_METRICS}, fatal=False)
        if "error" in r:
            print(f"  {m['id']}: no insights ({r['error'][:120]})")
            continue
        v = {d["name"]: (d.get("values") or [{}])[0].get("value") for d in r.get("data", [])}
        skip = call("GET", f"{GRAPH}/{m['id']}/insights", {"metric": "reels_skip_rate"}, fatal=False)
        skip = None if "error" in skip else (skip.get("data") or [{}])[0].get("values", [{}])[0].get("value")
        watch, total = v.get("ig_reels_avg_watch_time"), v.get("ig_reels_video_view_total_time")
        posts.append({
            "id": m["id"], "kind": "reel", "posted_at": m["timestamp"].replace("+0000", "Z"),
            "on_grid": None,  # the API doesn't say whether a trial was shared; Buzzfy pulls fill it in
            "permalink": m.get("permalink"),
            "caption_first_line": (m.get("caption") or "").strip().split("\n")[0][:200],
            "reach": v.get("reach"), "views": v.get("views"), "likes": v.get("likes"),
            "comments": v.get("comments"), "shares": v.get("shares"), "saves": v.get("saved"),
            "interactions": v.get("total_interactions"),
            "avg_watch_time_s": round(watch / 1000, 1) if watch is not None else None,
            "total_watch_time_min": round(total / 60000, 1) if total is not None else None,
            "skip_rate_pct": skip,
        })
    out = Path(a.out or ROOT / "analytics" / "snapshots" / f"{pulled[:10]}-graph.json")
    out.write_text(json.dumps({
        "source": "own Meta app (graph.instagram.com)", "pulled_at": pulled,
        "account": {"followers": me.get("followers_count")}, "posts": posts}, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"{len(posts)} reels -> {out}")


def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("whoami")
    sub.add_parser("refresh")
    s = sub.add_parser("status"); s.add_argument("container_id")
    t = sub.add_parser("trial")
    t.add_argument("--video", required=True)
    t.add_argument("--caption-file")
    t.add_argument("--caption")
    t.add_argument("--strategy", choices=["MANUAL", "SS_PERFORMANCE"], default="MANUAL")
    t.add_argument("--thumb-offset", type=int, help="cover frame, ms from start")
    t.add_argument("--confirm", action="store_true", help="actually publish (only after an explicit yes)")
    t.add_argument("--slug", help="reel folder, e.g. 2026-10-14-freeze-in-sparring (links the post in the ledger)")
    t.add_argument("--variant", help="A, B or C")
    i = sub.add_parser("insights")
    i.add_argument("--limit", type=int, default=60, help="newest N posts")
    i.add_argument("--out", help="snapshot path (default analytics/snapshots/<date>-graph.json)")
    a = p.parse_args()
    load_env()
    if a.cmd == "whoami": whoami()
    elif a.cmd == "refresh": refresh()
    elif a.cmd == "status": print(status(a.container_id))
    elif a.cmd == "insights": insights(a)
    else: trial(a)


if __name__ == "__main__":
    main()
