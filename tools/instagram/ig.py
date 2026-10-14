"""Post @matteofights trial reels through our own Meta app (Instagram API with Instagram Login).

Nothing goes out without --confirm. Without it, `trial` only prints the preview.

    python -P tools/instagram/ig.py whoami
    python -P tools/instagram/ig.py refresh                     # extend the 60-day token
    python -P tools/instagram/ig.py trial --video media/x/x-A.mp4 --caption-file production/reels/<slug>/caption-A.txt
    python -P tools/instagram/ig.py trial ... --confirm         # only after Matteo said yes to the preview
    python -P tools/instagram/ig.py status <container_id>

Token: secrets/meta.env (IG_ACCESS_TOKEN=..., IG_USER_ID=...), or the same names as env vars
(GitHub Actions secrets). Upload is resumable straight to Meta, so the video needs no public URL.
"""
import argparse, json, os, sys, time, urllib.error, urllib.parse, urllib.request
from pathlib import Path

API = "v23.0"
GRAPH = f"https://graph.instagram.com/{API}"
RUPLOAD = f"https://rupload.facebook.com/ig-api-upload/{API}"
ENV_FILE = Path(__file__).resolve().parents[2] / "secrets" / "meta.env"


def load_env():
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())
    if not os.environ.get("IG_ACCESS_TOKEN"):
        sys.exit(f"No IG_ACCESS_TOKEN (put it in {ENV_FILE} or the environment).")


def call(method, url, params=None, data=None, headers=None):
    params = dict(params or {})
    if "graph.instagram.com" in url:
        params["access_token"] = os.environ["IG_ACCESS_TOKEN"]
    if params:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, data=data, method=method, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=600) as r:
            return json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
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


def main():
    sys.stdout.reconfigure(encoding="utf-8")  # captions carry emoji; Windows consoles default to cp1252
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
    a = p.parse_args()
    load_env()
    if a.cmd == "whoami": whoami()
    elif a.cmd == "refresh": refresh()
    elif a.cmd == "status": print(status(a.container_id))
    else: trial(a)


if __name__ == "__main__":
    main()
