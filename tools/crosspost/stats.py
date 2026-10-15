"""Platform status, per-platform results and a comment inbox for the control center.

    python -P tools/crosspost/stats.py      # the "Platform stats" workflow runs this every 2 hours

Writes production/control/platforms.json (shown on the dashboard by tools/control/build_data.py):
  platforms.<name>  followers, last_post, next_slot, failed (recent), token_expires, warn
  posts.<queue id>.<name>  views/likes/replies/... for every cross-posted reel (Instagram from queue media ids)
  inbox  recent comments from other people on Instagram, Facebook and Threads, newest first, with "answered"
         when @matteofights already replied under it. Replying stays manual (the biggest growth lever).
Read-only: never posts or replies. Secrets: IG_ACCESS_TOKEN, FB_PAGE_TOKEN, THREADS_ACCESS_TOKEN, THREADS_USER_ID.
"""
import datetime as dt, json, os, sys, urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import crosspost as xp  # noqa: E402

OUT = xp.ROOT / "production" / "control" / "platforms.json"
IG = "https://graph.instagram.com/v21.0"
INBOX_DAYS = 4
# Instagram login tokens can't be inspected through the API; set when refreshed (see tools/instagram/README.md)
KNOWN_EXPIRY = {"instagram": "2026-12-13", "threads": None, "facebook": None, "youtube": None}


def get(url, **params):
    _, _, d = xp.http("GET", url + ("&" if "?" in url else "?") + urllib.parse.urlencode(params))
    return d


def safe(fn, default=None):
    try:
        return fn()
    except Exception as e:  # one platform failing must not hide the others
        print(f"  ! {fn.__name__ if hasattr(fn, '__name__') else 'call'}: {str(e)[:160]}")
        return default


def days_left(date):
    if not date:
        return None
    d = dt.date.fromisoformat(date[:10])
    return (d - dt.date.today()).days


def recent_iso(days):
    return xp.iso(dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=days))


def main():
    xp.load_env()
    meta = xp.ROOT / "secrets" / "meta.env"  # local runs: the Instagram token lives there (GitHub: secret)
    if meta.exists():
        for line in meta.read_text(encoding="utf-8").splitlines():
            if line.startswith("IG_ACCESS_TOKEN="):
                os.environ.setdefault("IG_ACCESS_TOKEN", line.split("=", 1)[1].strip())
    state = json.loads(xp.STATE.read_text(encoding="utf-8"))
    queue = json.loads(xp.QUEUE.read_text(encoding="utf-8"))["items"]
    old = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else {}
    out = {"updated": xp.now(), "platforms": {}, "posts": {}, "inbox": []}
    since_inbox = recent_iso(INBOX_DAYS)
    recent_posts = [i for i in queue if i.get("status") == "posted" and (i.get("posted_at") or "") >= recent_iso(10)]

    # ------------------------------------------------ Instagram
    ig_tok = os.environ.get("IG_ACCESS_TOKEN")
    ig = {"followers": None, "last_post": max((i["posted_at"] for i in queue if i.get("posted_at")), default=None),
          "failed": [i["id"] for i in queue if i.get("status") == "failed" and (i.get("not_before") or "") >= recent_iso(3)]}
    upcoming = sorted(i["not_before"] for i in queue if i.get("status") == "queued" and i.get("approved"))
    ig["next_slot"] = upcoming[0] if upcoming else None
    if ig_tok:
        me = safe(lambda: get(f"{IG}/me", fields="followers_count,username", access_token=ig_tok), {})
        ig["followers"] = me.get("followers_count")
        for it in recent_posts:
            if not it.get("media_id"):
                continue
            ins = safe(lambda: get(f"{IG}/{it['media_id']}/insights", metric="views,likes,comments,shares,saved",
                                   access_token=ig_tok), {"data": []})
            m = {x["name"]: (x.get("values") or [{}])[0].get("value") for x in ins.get("data", [])}
            out["posts"].setdefault(it["id"], {})["instagram"] = {"views": m.get("views"), "likes": m.get("likes"),
                                                                  "comments": m.get("comments"), "shares": m.get("shares"),
                                                                  "saves": m.get("saved"), "url": it.get("permalink")}
            cm = safe(lambda: get(f"{IG}/{it['media_id']}/comments", fields="id,text,username,timestamp,replies{username}",
                                  access_token=ig_tok), {"data": []})
            for c in cm.get("data", []):
                if c.get("timestamp", "") < since_inbox.replace("Z", "+0000") or c.get("username") == me.get("username"):
                    continue
                out["inbox"].append({"platform": "instagram", "id": c["id"], "who": c.get("username"), "text": c.get("text", ""),
                                     "at": c.get("timestamp"), "on": it.get("hook") or it["id"], "url": it.get("permalink"),
                                     "answered": any(r.get("username") == me.get("username") for r in (c.get("replies") or {}).get("data", []))})
    out["platforms"]["instagram"] = ig

    # ------------------------------------------------ Facebook (Page)
    fb_tok = os.environ.get("FB_PAGE_TOKEN")
    if fb_tok:
        page = xp.FB_PAGE
        fb = {"followers": safe(lambda: get(f"{xp.FB}/{page}", fields="followers_count", access_token=fb_tok), {}).get("followers_count")}
        posts = safe(lambda: get(f"{xp.FB}/{page}/posts", limit=25, access_token=fb_tok,
                                 fields="id,created_time,permalink_url,message,comments.limit(25){id,message,from,created_time,comments.limit(5){from}}"),
                     {"data": []})
        reels = safe(lambda: get(f"{xp.FB}/{page}/video_reels", limit=25, fields="id,views,created_time", access_token=fb_tok), {"data": []})
        views = {r["id"]: r.get("views") for r in reels.get("data", [])}
        for p in posts.get("data", []):
            for c in (p.get("comments") or {}).get("data", []):
                if c.get("created_time", "") < since_inbox.replace("Z", "+0000") or (c.get("from") or {}).get("id") == page:
                    continue
                out["inbox"].append({"platform": "facebook", "id": c["id"], "who": (c.get("from") or {}).get("name", "someone"),
                                     "text": c.get("message", ""), "at": c.get("created_time"), "on": (p.get("message") or "")[:80],
                                     "url": p.get("permalink_url"),
                                     "answered": any((r.get("from") or {}).get("id") == page for r in (c.get("comments") or {}).get("data", []))})
        out["platforms"]["facebook"] = fb
        for qid, recs in state["posts"].items():
            for name in ("facebook", "facebook_slides"):
                r = recs.get(name)
                if r and r.get("status") == "posted":
                    out["posts"].setdefault(qid, {})[name] = {"views": views.get(r.get("id")), "url": r.get("url")}

    # ------------------------------------------------ Threads
    th_tok, th_uid = os.environ.get("THREADS_ACCESS_TOKEN"), os.environ.get("THREADS_USER_ID")
    if th_tok and th_uid:
        TH = xp.TH
        ui = safe(lambda: get(f"{TH}/{th_uid}/threads_insights", metric="followers_count", access_token=th_tok), {"data": []})
        th = {"followers": next((x.get("total_value", {}).get("value") for x in ui.get("data", []) if x["name"] == "followers_count"), None)}
        dbg = safe(lambda: get(f"{TH}/debug_token", input_token=th_tok, access_token=th_tok), {})
        exp = (dbg.get("data") or {}).get("expires_at")
        if exp:
            KNOWN_EXPIRY["threads"] = dt.datetime.fromtimestamp(exp, dt.timezone.utc).strftime("%Y-%m-%d")
        me = safe(lambda: get(f"{TH}/me", fields="username", access_token=th_tok), {}).get("username")

        def th_post(pid, link):
            ins = safe(lambda: get(f"{TH}/{pid}/insights", metric="views,likes,replies,reposts,quotes,shares", access_token=th_tok), {"data": []})
            m = {x["name"]: (x.get("values") or [{}])[0].get("value", x.get("total_value", {}).get("value")) for x in ins.get("data", [])}
            rep = safe(lambda: get(f"{TH}/{pid}/replies", fields="id,text,username,timestamp,permalink,has_replies", access_token=th_tok), {"data": []})
            for c in rep.get("data", []):
                if c.get("username") == me or c.get("timestamp", "") < since_inbox.replace("Z", "+0000"):
                    continue
                answered = False
                if c.get("has_replies"):
                    sub = safe(lambda: get(f"{TH}/{c['id']}/replies", fields="username", access_token=th_tok), {"data": []})
                    answered = any(s.get("username") == me for s in sub.get("data", []))
                out["inbox"].append({"platform": "threads", "id": c["id"], "who": c.get("username"), "text": c.get("text", ""),
                                     "at": c.get("timestamp"), "on": link["on"], "url": c.get("permalink") or link["url"],
                                     "answered": answered})
            return {"views": m.get("views"), "likes": m.get("likes"), "replies": m.get("replies"),
                    "reposts": m.get("reposts"), "shares": m.get("shares"), "url": link["url"]}

        for qid, recs in state["posts"].items():
            r = recs.get("threads")
            if r and r.get("status") == "posted" and r.get("at", "") >= recent_iso(10):
                hook = next((i.get("hook") for i in queue if i["id"] == qid), qid)
                out["posts"].setdefault(qid, {})["threads"] = th_post(r["id"], {"on": hook, "url": r.get("url")})
        if xp.THREADS_POSTS.exists():
            tp = json.loads(xp.THREADS_POSTS.read_text(encoding="utf-8"))
            written = {}
            for p in tp["posts"]:
                if p.get("status") == "posted" and p.get("thread_id") and (p.get("posted_at") or "") >= recent_iso(10):
                    written[p["id"]] = th_post(p["thread_id"], {"on": p["text"].splitlines()[0][:80], "url": p.get("url")})
            out["threads_written"] = written
        out["platforms"]["threads"] = th

    # ------------------------------------------------ status per platform (from crosspost state)
    t_now = dt.datetime.now(dt.timezone.utc)
    for name in ("facebook", "youtube", "threads"):
        cfg = state["platforms"].get(name, {})
        p = out["platforms"].setdefault(name, {})
        recs = [(qid, r[name]) for qid, r in state["posts"].items() if name in r]
        p["enabled"] = bool(cfg.get("enabled"))
        p["last_post"] = max((r.get("at") for _, r in recs if r.get("status") == "posted"), default=None)
        p["failed"] = [qid for qid, r in recs if r.get("status") == "failed" and r.get("at", "") >= recent_iso(3)]
        p["errors"] = [r.get("error", "")[:200] for _, r in recs if r.get("status") == "failed" and r.get("at", "") >= recent_iso(3)][:2]
        if cfg.get("slots"):
            p["next_slot"] = xp.iso(xp.next_slot(t_now, cfg["slots"]))
        if name == "youtube":
            p["privacy"] = cfg.get("privacy")
    for name, p in out["platforms"].items():
        p["token_expires"] = KNOWN_EXPIRY.get(name)
        left = days_left(p["token_expires"])
        p["warn"] = (f"Login expires in {left} days" if left is not None and left <= 21 else None) or \
                    (f"{len(p['failed'])} failed in the last 3 days" if p.get("failed") else None) or \
                    ("Uploads are private until the YouTube audit passes" if p.get("privacy") == "private" else None)
    out["inbox"].sort(key=lambda c: c.get("at") or "", reverse=True)
    out["inbox"] = out["inbox"][:80]

    # tell Matteo once when a login gets close to expiring
    warned = set(old.get("warned", []))
    for name, p in out["platforms"].items():
        left = days_left(p.get("token_expires"))
        key = f"{name}:{p.get('token_expires')}"
        if left is not None and left <= 14 and key not in warned:
            xp.note(f"🔑 The {name.capitalize()} login expires in {left} days ({p['token_expires']}). Tell Claude to refresh it.")
            warned.add(key)
    out["warned"] = sorted(warned)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    counts = ", ".join(f"{k}={v.get('followers')}" for k, v in out["platforms"].items())
    print(f"platforms: {counts}; "
          f"{len(out['posts'])} reels with numbers; inbox {len(out['inbox'])} ({sum(not c['answered'] for c in out['inbox'])} open)")


if __name__ == "__main__":
    main()
