"""Keep every written Threads post's latest numbers for good (production/threads/results.json).

    python3 -P tools/threads/collect.py     # the Platform stats workflow runs this right after tools/crosspost/stats.py

stats.py puts the numbers in production/control/platforms.json -> threads_written, but only for posts from the last
10 days. This copies them, with the post's kind/topic/text, into a file that is never trimmed, so
tools/threads/report.py (and the threads-writer skill) can learn from the whole history.
"""
import datetime as dt, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
POSTS = ROOT / "production/threads/posts.json"
STATS = ROOT / "production/control/platforms.json"
OUT = ROOT / "production/threads/results.json"


def main():
    if not (POSTS.exists() and STATS.exists()):
        return
    written = json.loads(STATS.read_text(encoding="utf-8")).get("threads_written") or {}
    posts = {p["id"]: p for p in json.loads(POSTS.read_text(encoding="utf-8"))["posts"]}
    res = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else {}
    now = dt.datetime.now(dt.timezone.utc)
    changed = 0
    for pid, m in written.items():
        p = posts.get(pid)
        if not p or m.get("views") is None or not p.get("posted_at"):
            continue
        age = (now - dt.datetime.fromisoformat(p["posted_at"].replace("Z", "+00:00"))).total_seconds() / 3600
        row = {"kind": p.get("kind"), "topic": p.get("topic"), "from": p.get("from"), "posted_at": p["posted_at"],
               "text": p["text"], "chain": len(p.get("chain") or []), "age_h": round(age),
               **{k: m.get(k) for k in ("views", "likes", "replies", "reposts", "shares")}, "url": m.get("url")}
        if res.get(pid) != row:
            res[pid] = row
            changed += 1
    if changed:
        OUT.write_text(json.dumps(res, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"threads results: {len(res)} posts, {changed} updated")


if __name__ == "__main__":
    main()
