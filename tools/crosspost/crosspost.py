"""Cross-post reels that went out on Instagram to YouTube Shorts, Facebook Reels and Threads.

    python -P tools/crosspost/crosspost.py run              # post every due item (the "Cross-post" workflow runs this)
    python -P tools/crosspost/crosspost.py run --dry        # show what would be posted, post nothing
    python -P tools/crosspost/crosspost.py youtube-auth     # one time, local: click "Allow", saves YT_REFRESH_TOKEN
    python -P tools/crosspost/crosspost.py threads-check    # local: token works? prints the Threads user (+ makes it long-lived)
    python -P tools/crosspost/crosspost.py threads-refresh  # local, monthly: extends the 60-day Threads token
    python -P tools/crosspost/crosspost.py facebook-setup   # local: Page token (never expires) from FB_USER_TOKEN in meta.env

State: production/schedule/crosspost.json
  platforms.<name>.enabled  only Matteo turns a platform on (his yes to posting there)
  platforms.<name>.since    only reels posted on Instagram at/after this time are cross-posted (no surprise backfill)
  platforms.youtube.privacy "private" until Google's API audit passes (unaudited apps can only upload private)
  platforms.facebook.winners  only reels the daily Facebook pick chose (queue item fb_pick, set by
                            tools/listicle/factory.py --fb-pick from the Instagram numbers at 72 h) go to Facebook,
                            as their Facebook version (video_asset_fb: list on screen, music in the file)
  posts.<queue id>.<name>   {status: posted|failed, id, url, at, error, tries}
The same video file and caption as Instagram (production/schedule/queue.json -> media release + caption_file), except:
a listicle whose Instagram sound is attached in the app has a silent-ish file, so YouTube and Threads take its music
copy (video_asset_music) and Facebook its Facebook version (video_asset_fb).
Secrets (env, or secrets/crosspost.env locally): YT_CLIENT_ID, YT_CLIENT_SECRET, YT_REFRESH_TOKEN,
FB_PAGE_TOKEN, THREADS_ACCESS_TOKEN, THREADS_USER_ID (+ THREADS_APP_SECRET locally, only to make a token long-lived), GH_TOKEN.
"""
import argparse, datetime as dt, json, os, re, secrets as rnd, sys, time, urllib.error, urllib.parse
import urllib.request, uuid, webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parent))
import captions  # noqa: E402
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import state as store  # noqa: E402  (live state: queue + crosspost results)

ROOT = Path(__file__).resolve().parents[2]
NOTES = ROOT / "production" / "control" / "notes.json"
THREADS_POSTS = ROOT / "production" / "threads" / "posts.json"
NY = ZoneInfo("America/New_York")
ENVF = ROOT / "secrets" / "crosspost.env"
REPO = "fightingmatteo-ux/matteofights"
MAX_TRIES = 3
LOOKBACK_DAYS = 3  # don't cross-post anything older than this, even if enabled late


def now():
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_env():
    if ENVF.exists():
        for line in ENVF.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())


def set_env(key, value):
    """Write/replace KEY=value in secrets/crosspost.env without printing it."""
    ENVF.parent.mkdir(exist_ok=True)
    lines = [l for l in (ENVF.read_text(encoding="utf-8").splitlines() if ENVF.exists() else []) if not l.startswith(key + "=")]
    ENVF.write_text("\n".join(lines + [f"{key}={value}"]) + "\n", encoding="utf-8")
    os.environ[key] = value


def http(method, url, data=None, headers=None, raw=None):
    body = raw if raw is not None else (urllib.parse.urlencode(data).encode() if isinstance(data, dict) else data)
    req = urllib.request.Request(url, body, headers or {}, method=method)
    try:
        with urllib.request.urlopen(req, timeout=300) as r:
            text = r.read().decode() or "{}"
            return r.status, dict(r.headers), json.loads(text) if text.strip().startswith(("{", "[")) else text
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"{method} {url.split('?')[0]} -> {e.code}: {e.read().decode()[:400]}") from None


# ---------------------------------------------------------------- media release
class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k):
        return None


def signed_url(asset):
    """Download link for a render: presigned R2 (6 h) when it's in R2, else the media release's signed link."""
    import r2
    return r2.video_url(asset, release_url)


def release_url(asset):
    """Signed public download link (valid a few minutes) for a file on the 'media' release."""
    tok = os.environ["GH_TOKEN"]
    _, _, rel = http("GET", f"https://api.github.com/repos/{REPO}/releases/tags/media",
                     headers={"Authorization": f"Bearer {tok}", "Accept": "application/vnd.github+json"})
    a = next((x for x in rel["assets"] if x["name"] == asset), None)
    if not a:
        raise RuntimeError(f"{asset} is not on the media release")
    req = urllib.request.Request(f"https://api.github.com/repos/{REPO}/releases/assets/{a['id']}",
                                 headers={"Authorization": f"Bearer {tok}", "Accept": "application/octet-stream"})
    try:
        urllib.request.build_opener(_NoRedirect).open(req, timeout=60)
    except urllib.error.HTTPError as e:
        if e.code in (301, 302, 307) and e.headers.get("Location"):
            return e.headers["Location"]
        raise
    raise RuntimeError("GitHub did not return a download link")


def offsite_asset(item):
    """The file for other platforms: the music copy when the Instagram file relies on an in-app sound."""
    return item.get("video_asset_music") or item["video_asset"]


def download(asset):
    with urllib.request.urlopen(signed_url(asset), timeout=300) as r:
        return r.read()


# ---------------------------------------------------------------- captions
def caption(item):
    p = ROOT / item.get("caption_file", "")
    return p.read_text(encoding="utf-8").strip() if p.is_file() else (item.get("hook") or "")


def without_hashtags(text):
    lines = [l for l in text.splitlines() if not re.fullmatch(r"\s*(#\S+\s*)+", l)]
    return re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip()


def shorten(text, limit):
    if len(text) <= limit:
        return text
    cut = text[: limit - 1]
    cut = cut[: cut.rfind("\n")] if "\n" in cut[limit // 2:] else cut[: cut.rfind(" ")]
    return cut.rstrip() + "…"


def title(item, cap):
    t = item.get("hook") or (cap.splitlines()[0] if cap else item["id"])
    t = t.strip().rstrip(".")
    if t.isupper():
        t = t.capitalize()
    return shorten(t, 90) + " #shorts"


# ---------------------------------------------------------------- YouTube
GOOGLE_TOKEN = "https://oauth2.googleapis.com/token"
YT_SCOPE = "https://www.googleapis.com/auth/youtube.upload https://www.googleapis.com/auth/youtube.readonly"  # readonly: stats.py reads views


def yt_access():
    _, _, t = http("POST", GOOGLE_TOKEN, {"client_id": os.environ["YT_CLIENT_ID"], "client_secret": os.environ["YT_CLIENT_SECRET"],
                                         "refresh_token": os.environ["YT_REFRESH_TOKEN"], "grant_type": "refresh_token"})
    return t["access_token"]


def post_youtube(item, cfg):
    cap, hook = caption(item), item.get("hook", "")
    meta = {"snippet": {"title": captions.youtube_title(cap, hook),
                        "description": shorten(captions.youtube_description(cap, hook), 4900), "categoryId": "17",
                        "tags": ["fighter", "mma", "boxing", "muay thai", "fight mindset"]},
            "status": {"privacyStatus": cfg.get("privacy", "private"), "selfDeclaredMadeForKids": False}}
    video = download(offsite_asset(item))
    tok = yt_access()
    _, h, _ = http("POST", "https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status",
                   raw=json.dumps(meta).encode(),
                   headers={"Authorization": f"Bearer {tok}", "Content-Type": "application/json; charset=UTF-8",
                            "X-Upload-Content-Type": "video/mp4", "X-Upload-Content-Length": str(len(video))})
    loc = {k.lower(): v for k, v in h.items()}["location"]
    _, _, v = http("PUT", loc, raw=video, headers={"Authorization": f"Bearer {tok}", "Content-Type": "video/mp4"})
    return {"id": v["id"], "url": f"https://youtube.com/shorts/{v['id']}", "privacy": v["status"]["privacyStatus"]}


def youtube_auth():
    """Installed-app OAuth with a localhost redirect: opens the browser, Matteo clicks Allow, refresh token is saved."""
    load_env()
    for k in ("YT_CLIENT_ID", "YT_CLIENT_SECRET"):
        if not os.environ.get(k):
            sys.exit(f"{k} missing in secrets/crosspost.env")
    got = {}

    class H(BaseHTTPRequestHandler):
        def do_GET(self):
            q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            got.update({k: v[0] for k, v in q.items()})
            self.send_response(200)
            self.send_header("content-type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write("<h2>Done. You can close this tab.</h2>".encode())

        def log_message(self, *a):
            pass

    srv = HTTPServer(("127.0.0.1", 0), H)
    redirect = f"http://127.0.0.1:{srv.server_port}"
    state = rnd.token_urlsafe(16)
    url = "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode({
        "client_id": os.environ["YT_CLIENT_ID"], "redirect_uri": redirect, "response_type": "code", "scope": YT_SCOPE,
        "access_type": "offline", "prompt": "consent", "state": state})
    print("Opening Google sign-in. Pick the YouTube channel for @matteofights and click Allow.")
    webbrowser.open(url)
    while "code" not in got and "error" not in got:
        srv.handle_request()
    if got.get("state") != state or "code" not in got:
        sys.exit(f"sign-in failed: {got.get('error', 'state mismatch')}")
    _, _, t = http("POST", GOOGLE_TOKEN, {"code": got["code"], "client_id": os.environ["YT_CLIENT_ID"],
                                         "client_secret": os.environ["YT_CLIENT_SECRET"], "redirect_uri": redirect,
                                         "grant_type": "authorization_code"})
    if not t.get("refresh_token"):
        sys.exit("Google returned no refresh token; remove the app's access at myaccount.google.com/permissions and retry")
    set_env("YT_REFRESH_TOKEN", t["refresh_token"])
    print("Saved YT_REFRESH_TOKEN to secrets/crosspost.env")


# ---------------------------------------------------------------- Threads
TH = "https://graph.threads.net/v1.0"


def th_publish(params, wait=False):
    """Create a Threads container (text, video or reply) and publish it. Returns (post id, permalink)."""
    uid, tok = os.environ["THREADS_USER_ID"], os.environ["THREADS_ACCESS_TOKEN"]
    params = {**params, "access_token": tok}
    try:
        _, _, c = http("POST", f"{TH}/{uid}/threads", params)
    except RuntimeError as e:
        if "topic_tag" not in params:
            raise
        print(f"topic tag rejected, retrying without: {str(e)[:120]}")
        params.pop("topic_tag")
        _, _, c = http("POST", f"{TH}/{uid}/threads", params)
    if wait:  # video: Threads processes it before it can be published
        for _ in range(60):
            time.sleep(10)
            _, _, st = http("GET", f"{TH}/{c['id']}?fields=status,error_message&access_token={tok}")
            if st.get("status") == "FINISHED":
                break
            if st.get("status") in ("ERROR", "EXPIRED"):
                raise RuntimeError(f"Threads processing {st.get('status')}: {st.get('error_message')}")
        else:
            raise RuntimeError("Threads processing timed out")
    else:
        time.sleep(3)
    _, _, p = http("POST", f"{TH}/{uid}/threads_publish", {"creation_id": c["id"], "access_token": tok})
    _, _, m = http("GET", f"{TH}/{p['id']}?fields=permalink&access_token={tok}")
    return p["id"], m.get("permalink")


def post_threads(item, cfg):
    text = captions.threads(caption(item), item.get("hook", ""))
    pid, url = th_publish({"media_type": "VIDEO", "video_url": signed_url(offsite_asset(item)), "text": text,
                           "topic_tag": cfg.get("topic", captions.TOPIC)}, wait=True)
    return {"id": pid, "url": url}


def post_threads_text(post):
    """One written post (+ optional chain of replies under it) from production/threads/posts.json."""
    params = {"media_type": "TEXT", "text": post["text"][:500]}
    if post.get("topic"):
        params["topic_tag"] = post["topic"]
    pid, url = th_publish(params)
    parent = pid
    for reply in post.get("chain") or []:
        parent, _ = th_publish({"media_type": "TEXT", "text": reply[:500], "reply_to_id": parent})
    return {"id": pid, "url": url}


def threads_check():
    load_env()
    tok = os.environ.get("THREADS_ACCESS_TOKEN") or sys.exit("THREADS_ACCESS_TOKEN missing in secrets/crosspost.env")
    if os.environ.get("THREADS_APP_SECRET") and not os.environ.get("THREADS_LONG_LIVED"):
        try:
            _, _, t = http("GET", "https://graph.threads.net/access_token?" + urllib.parse.urlencode(
                {"grant_type": "th_exchange_token", "client_secret": os.environ["THREADS_APP_SECRET"], "access_token": tok}))
            set_env("THREADS_ACCESS_TOKEN", t["access_token"])
            tok = t["access_token"]
            print(f"Exchanged for a long-lived token (~{t.get('expires_in', 0) // 86400} days)")
        except RuntimeError as e:
            print(f"(token not exchanged, probably already long-lived: {str(e)[:120]})")
        set_env("THREADS_LONG_LIVED", "1")
    _, _, me = http("GET", f"{TH}/me?fields=id,username&access_token={tok}")
    set_env("THREADS_USER_ID", me["id"])
    print(f"Threads OK: @{me['username']} (user id saved)")


def threads_refresh():
    load_env()
    _, _, t = http("GET", "https://graph.threads.net/refresh_access_token?" + urllib.parse.urlencode(
        {"grant_type": "th_refresh_token", "access_token": os.environ["THREADS_ACCESS_TOKEN"]}))
    set_env("THREADS_ACCESS_TOKEN", t["access_token"])
    print(f"Refreshed (~{t.get('expires_in', 0) // 86400} days). Update the GitHub secret: "
          "bash tools/ops/sync-secrets.sh --github  (GitHub + the Modal backup, values from secrets/*.env)")


# ---------------------------------------------------------------- Facebook (Page "Matteo Fights" Reels)
FB = "https://graph.facebook.com/v21.0"
FB_PAGE = "1070947222779004"


def post_facebook(item, cfg):
    tok, page = os.environ["FB_PAGE_TOKEN"], os.environ.get("FB_PAGE_ID", FB_PAGE)
    _, _, s = http("POST", f"{FB}/{page}/video_reels", {"upload_phase": "start", "access_token": tok})
    vid = s["video_id"]
    http("POST", f"https://rupload.facebook.com/video-upload/v21.0/{vid}", raw=b"",
         headers={"Authorization": f"OAuth {tok}", "file_url": signed_url(item.get("video_asset_fb") or offsite_asset(item))})
    http("POST", f"{FB}/{page}/video_reels", {"upload_phase": "finish", "video_id": vid, "video_state": "PUBLISHED",
                                              "description": shorten(captions.facebook(caption(item), item.get("hook", "")), 2000),
                                              "access_token": tok})
    for _ in range(60):
        time.sleep(10)
        _, _, st = http("GET", f"{FB}/{vid}?fields=status&access_token={tok}")
        status = st.get("status", {})
        if status.get("video_status") == "ready" or (status.get("publishing_phase") or {}).get("status") == "complete":
            break
        if status.get("video_status") == "error":
            raise RuntimeError(f"Facebook processing error: {json.dumps(status)[:300]}")
    return {"id": vid, "url": f"https://www.facebook.com/reel/{vid}"}


def post_facebook_slides(item, cfg):
    """The listicle as a photo album on the Page (title slide, one slide per item, question)."""
    import slides
    content = captions.slides(caption(item), item.get("hook", ""))
    if not content:
        return {"skipped": "not a list"}
    tok, page = os.environ["FB_PAGE_TOKEN"], os.environ.get("FB_PAGE_ID", FB_PAGE)
    cover = ROOT / Path(item.get("caption_file", "x/x")).parent / "cover.jpg"
    ids = []
    for k, jpg in enumerate(slides.render(*content, cover)):
        boundary = uuid.uuid4().hex
        body = (f"--{boundary}\r\nContent-Disposition: form-data; name=\"published\"\r\n\r\nfalse\r\n"
                f"--{boundary}\r\nContent-Disposition: form-data; name=\"source\"; filename=\"s{k}.jpg\"\r\n"
                f"Content-Type: image/jpeg\r\n\r\n").encode() + jpg + f"\r\n--{boundary}--\r\n".encode()
        _, _, ph = http("POST", f"{FB}/{page}/photos?access_token={tok}", raw=body,
                        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
        ids.append(ph["id"])
    hook, items, cta = content
    head = hook[0].upper() + hook[1:].lower() if hook.isupper() else hook
    data = {"message": f"{head}\n\nSwipe through all {len(items)}. {cta}", "access_token": tok}
    data.update({f"attached_media[{i}]": json.dumps({"media_fbid": x}) for i, x in enumerate(ids)})
    _, _, post = http("POST", f"{FB}/{page}/feed", data)
    return {"id": post["id"], "url": f"https://www.facebook.com/{post['id']}"}


def facebook_setup():
    """Page token from the user token in secrets/meta.env (needs pages_manage_posts). From a long-lived user token
    the Page token never expires."""
    load_env()
    meta = ROOT / "secrets" / "meta.env"
    user = next((l.split("=", 1)[1].strip() for l in meta.read_text(encoding="utf-8").splitlines()
                 if l.startswith("FB_USER_TOKEN=")), "")
    _, _, perms = http("GET", f"{FB}/me/permissions?access_token={user}")
    granted = {p["permission"] for p in perms["data"] if p["status"] == "granted"}
    if missing := {"pages_manage_posts", "pages_read_engagement", "pages_show_list"} - granted:
        sys.exit(f"FB_USER_TOKEN lacks {', '.join(sorted(missing))}: regenerate it (see tools/crosspost/README.md)")
    _, _, p = http("GET", f"{FB}/{FB_PAGE}?fields=name,access_token&access_token={user}")
    _, _, dbg = http("GET", f"{FB}/debug_token?input_token={p['access_token']}&access_token={p['access_token']}")
    exp = dbg["data"].get("expires_at", 0)
    set_env("FB_PAGE_TOKEN", p["access_token"])
    print(f"Page token for {p['name']} saved; expires: {'never' if not exp else dt.datetime.fromtimestamp(exp)}")


# ---------------------------------------------------------------- run
POSTERS = {"youtube": (post_youtube, ("YT_CLIENT_ID", "YT_CLIENT_SECRET", "YT_REFRESH_TOKEN")),
           "threads": (post_threads, ("THREADS_ACCESS_TOKEN", "THREADS_USER_ID")),
           "facebook": (post_facebook, ("FB_PAGE_TOKEN",)),
           "facebook_slides": (post_facebook_slides, ("FB_PAGE_TOKEN",))}
LABEL = {"youtube": "YouTube Shorts", "threads": "Threads", "facebook": "Facebook Reels",
         "facebook_slides": "Facebook slides", "threads_text": "Threads post"}


def note(text):
    notes = json.loads(NOTES.read_text(encoding="utf-8")) if NOTES.exists() else []
    notes.append({"id": "xp-" + uuid.uuid4().hex[:8], "text": text})
    NOTES.parent.mkdir(parents=True, exist_ok=True)
    NOTES.write_text(json.dumps(notes[-200:], indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def iso(t):
    return t.astimezone(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_iso(s):
    return dt.datetime.fromisoformat(s.replace("Z", "+00:00"))


def next_slot(after, slots):
    """First New York slot time ("HH:MM") at or after `after` (aware datetime)."""
    t = after.astimezone(NY)
    for day in range(8):
        d = (t + dt.timedelta(days=day)).date()
        for hm in sorted(slots):
            c = dt.datetime(d.year, d.month, d.day, *map(int, hm.split(":")), tzinfo=NY)
            if c >= t:
                return c
    raise ValueError("no slot")


def load_state():
    """{"platforms", "posts"} from tools/state.py, plus a copy save_state() diffs against."""
    st = {"platforms": store.get("crosspost", "platforms") or {}, "posts": store.get("crosspost", "posts") or {}}
    st["_before"] = json.loads(json.dumps(st))
    return st


def save_state(state):
    """Write each changed platform config and per-platform post record whole (a posted record must not keep a
    failed attempt's error), leaving everything this run didn't touch alone."""
    before = state["_before"]
    for doc in ("platforms", "posts"):
        old, new, sets = before[doc], state[doc], {}
        for k, v in new.items():
            if k not in old or not isinstance(v, dict) or not isinstance(old[k], dict):
                if old.get(k) != v:
                    sets[(k,)] = v  # new reel / platform: set whole
                continue
            for name, rec in v.items():
                if old[k].get(name) != rec:
                    sets[(k, name)] = rec
        if sets:
            store.set_paths("crosspost", doc, sets)
    state["_before"] = json.loads(json.dumps({"platforms": state["platforms"], "posts": state["posts"]}))


def run_platform(name, cfg, state, items, done, dry):
    """Post at most one reel to this platform per run, in its own New York time slots, oldest reel first."""
    poster, keys = POSTERS[name]
    if missing := [k for k in keys if not os.environ.get(k)]:
        print(f"{name}: enabled but secrets missing ({', '.join(missing)}), skipped")
        return
    t_now = dt.datetime.now(dt.timezone.utc)
    since = max(cfg.get("since") or now(), iso(t_now - dt.timedelta(days=LOOKBACK_DAYS)))
    last = parse_iso(cfg["last_slot"]) + dt.timedelta(minutes=1) if cfg.get("last_slot") else None
    winners = bool(cfg.get("winners"))  # Facebook: only the daily pick, timed from when it was picked
    ref = (lambda x: (x.get("fb_pick") or {}).get("at") or "") if winners else (lambda x: x.get("posted_at") or "")
    for it in sorted(items, key=ref):
        if it.get("status") != "posted" or ref(it) < since or not it.get("video_asset"):
            continue
        if winners and ((it.get("posted_at") or "") < cfg.get("since", "") or not it.get("video_asset_fb")):
            continue
        rec = state["posts"].setdefault(it["id"], {}).get(name, {})
        if rec.get("status") in ("posted", "skipped") or rec.get("tries", 0) >= MAX_TRIES:
            continue
        if "crosspost_to" in it and name not in it["crosspost_to"]:
            continue  # hook variants of one video: each goes to its own platform, never the same clip twice
        after = parse_iso(ref(it)) + dt.timedelta(minutes=cfg.get("min_delay_min", 0))
        after = max(after, last) if last else after
        slot = next_slot(after, cfg["slots"]) if cfg.get("slots") else after
        if slot > t_now:
            print(f"{name}: next is {it['id']} at {slot.astimezone(NY).strftime('%a %H:%M')} NY")
            return
        if dry:
            print(f"would post {it['id']} to {name} (slot {slot.astimezone(NY).strftime('%a %H:%M')} NY)")
            return
        try:
            out = poster(it, cfg)
        except Exception as e:
            tries = rec.get("tries", 0) + 1
            state["posts"][it["id"]][name] = {"status": "failed", "error": str(e)[:500], "tries": tries, "at": now()}
            print(f"{name}: FAILED {it['id']} ({tries}/{MAX_TRIES}): {e}")
            if tries >= MAX_TRIES:
                note(f"⚠️ {LABEL[name]} gave up on: {it.get('hook', it['id'])}\n{str(e)[:300]}")
            save_state(state)
            return
        if out.get("skipped"):
            state["posts"][it["id"]][name] = {"status": "skipped", "at": now(), **out}
            save_state(state)
            continue  # e.g. a talking-head reel has no list for slides: try the next reel
        state["posts"][it["id"]][name] = {"status": "posted", "at": now(), **out}
        cfg["last_slot"] = iso(slot)
        done.append((name, it.get("hook", it["id"]), out))
        print(f"{name}: posted {it['id']} -> {out.get('url')}")
        save_state(state)
        return


def run_threads_text(cfg, done, dry):
    """Approved written Threads posts whose time has come; one per run, at least min_gap_hours apart."""
    if not THREADS_POSTS.exists() or not os.environ.get("THREADS_ACCESS_TOKEN"):
        return
    data = json.loads(THREADS_POSTS.read_text(encoding="utf-8"))
    t_now = dt.datetime.now(dt.timezone.utc)
    posted = [parse_iso(p["posted_at"]) for p in data["posts"] if p.get("posted_at")]
    if posted and t_now - max(posted) < dt.timedelta(hours=cfg.get("min_gap_hours", 2)):
        return
    changed = False
    for p in sorted(data["posts"], key=lambda x: x["at"]):
        if p.get("status") != "queued" or not p.get("approved") or parse_iso(p["at"]) > t_now:
            continue
        changed = True
        if t_now - parse_iso(p["at"]) > dt.timedelta(hours=cfg.get("max_late_hours", 6)):
            p["status"] = "missed"
            continue
        if dry:
            print(f"would post Threads text {p['id']}")
            return
        try:
            out = post_threads_text(p)
            p.update(status="posted", posted_at=now(), thread_id=out["id"], url=out["url"])
            done.append(("threads_text", p["text"].splitlines()[0][:80], out))
            print(f"threads_text: posted {p['id']} -> {out.get('url')}")
        except Exception as e:
            p["tries"] = p.get("tries", 0) + 1
            p["error"] = str(e)[:500]
            print(f"threads_text: FAILED {p['id']}: {e}")
            if p["tries"] >= MAX_TRIES:
                p["status"] = "failed"
                note(f"⚠️ Threads post failed: {p['text'][:80]}\n{str(e)[:300]}")
        break
    if changed and not dry:
        THREADS_POSTS.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def run(dry=False):
    load_env()
    state = load_state()
    items = store.all("queue")
    done = []
    for name, cfg in state["platforms"].items():
        if not cfg.get("enabled"):
            continue
        if name == "threads_text":
            run_threads_text(cfg, done, dry)
        else:
            run_platform(name, cfg, state, items, done, dry)
    for name, label, out in done:
        if name == "threads_text":
            continue  # written posts were approved as a batch; no ping for each one
        extra = " (private until the YouTube API audit passes: tap to make it public)" if out.get("privacy") == "private" else ""
        note(f"📤 {LABEL[name]}: {label}\n{out.get('url') or ''}{extra}")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("cmd", choices=["run", "youtube-auth", "threads-check", "threads-refresh", "facebook-setup"])
    p.add_argument("--dry", action="store_true")
    a = p.parse_args()
    {"run": lambda: run(a.dry), "youtube-auth": youtube_auth, "threads-check": threads_check,
     "threads-refresh": threads_refresh, "facebook-setup": facebook_setup}[a.cmd]()


if __name__ == "__main__":
    main()
