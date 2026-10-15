"""Post the next due, APPROVED trial reel from production/schedule/queue.json. One post per run.

Run by the "Post queue" workflow every 30 min (or by hand). An item posts only when:
  approved == true  (set by Matteo, or by Claude after Matteo's explicit yes to that exact preview)
  status == "queued", now >= not_before, and the account's latest post is >= min_gap_hours old.
Guard against double posts: if a post from the last 24 h already starts with the item's caption, it is
marked posted instead of posting again.
"""
import datetime as dt, json, os, re, subprocess, sys, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
QUEUE = ROOT / "production" / "schedule" / "queue.json"
GRAPH = "https://graph.instagram.com/v23.0"
DEFAULT_GAP_H = 2.5


def now():
    return dt.datetime.now(dt.timezone.utc)


def recent_posts():
    tok = os.environ["IG_ACCESS_TOKEN"]
    url = f"{GRAPH}/me/media?fields=id,timestamp,caption,permalink&limit=10&access_token={tok}"
    data = json.load(urllib.request.urlopen(url, timeout=60))["data"]
    for p in data:
        p["at"] = dt.datetime.strptime(p["timestamp"], "%Y-%m-%dT%H:%M:%S%z")
    return data


def main():
    if not os.environ.get("IG_ACCESS_TOKEN"):
        for line in (ROOT / "secrets" / "meta.env").read_text(encoding="utf-8").splitlines():
            if "=" in line:
                k, v = line.split("=", 1); os.environ.setdefault(k.strip(), v.strip())
    q = json.loads(QUEUE.read_text(encoding="utf-8"))
    # app_audio items need a sound from Instagram's library (the API can't add one): Matteo posts those in the app
    due = [i for i in q["items"] if i.get("approved") is True and i.get("status") == "queued" and not i.get("app_audio")
           and dt.datetime.fromisoformat(i["not_before"].replace("Z", "+00:00")) <= now()]
    if not due:
        print("nothing due"); return
    item = sorted(due, key=lambda i: i["not_before"])[0]
    caption = (ROOT / item["caption_file"]).read_text(encoding="utf-8").strip()
    posts = recent_posts()

    first_line = caption.splitlines()[0].strip()
    for p in posts:
        if now() - p["at"] < dt.timedelta(hours=24) and (p.get("caption") or "").strip().startswith(first_line):
            item.update(status="posted", media_id=p["id"], posted_at=p["timestamp"], permalink=p.get("permalink"),
                        note="found already on Instagram, not re-posted")
            save(q); print(f"{item['id']}: already posted ({p['id']})"); return

    gap = dt.timedelta(hours=item.get("min_gap_hours", DEFAULT_GAP_H))
    if posts and now() - posts[0]["at"] < gap:
        print(f"{item['id']}: waiting, latest post {posts[0]['timestamp']} is under {gap} old"); return

    cmd = [sys.executable, "-P", "tools/instagram/ig.py", "trial", "--asset", item["video_asset"],
           "--caption-file", item["caption_file"], "--strategy", item.get("strategy", "MANUAL"), "--confirm"]
    if item.get("thumb_offset_ms") is not None:
        cmd += ["--thumb-offset", str(item["thumb_offset_ms"])]
    r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, encoding="utf-8")
    out = r.stdout + r.stderr
    print(out[-3000:])
    m = re.search(r"media id (\d+)\s+(\S+)", out)
    if r.returncode == 0 and m:
        item.update(status="posted", media_id=m.group(1), permalink=m.group(2),
                    posted_at=now().strftime("%Y-%m-%dT%H:%M:%SZ"))
    else:
        item.update(status="failed", error=out.strip().splitlines()[-1][:500] if out.strip() else f"exit {r.returncode}")
    save(q)
    sys.exit(0 if item["status"] == "posted" else 1)


def save(q):
    QUEUE.write_text(json.dumps(q, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
