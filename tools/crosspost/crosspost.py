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
  posts.<queue id>.<name>   {status: posted|failed, id, url, at, error, tries}
The same video file and caption as Instagram (production/schedule/queue.json -> media release + caption_file).
Secrets (env, or secrets/crosspost.env locally): YT_CLIENT_ID, YT_CLIENT_SECRET, YT_REFRESH_TOKEN,
FB_PAGE_TOKEN, THREADS_ACCESS_TOKEN, THREADS_USER_ID (+ THREADS_APP_SECRET locally, only to make a token long-lived), GH_TOKEN.
"""
import argparse, datetime as dt, json, os, re, secrets as rnd, sys, time, urllib.error, urllib.parse
import urllib.request, uuid, webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
QUEUE = ROOT / "production" / "schedule" / "queue.json"
STATE = ROOT / "production" / "schedule" / "crosspost.json"
NOTES = ROOT / "production" / "control" / "notes.json"
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
YT_SCOPE = "https://www.googleapis.com/auth/youtube.upload"


def yt_access():
    _, _, t = http("POST", GOOGLE_TOKEN, {"client_id": os.environ["YT_CLIENT_ID"], "client_secret": os.environ["YT_CLIENT_SECRET"],
                                         "refresh_token": os.environ["YT_REFRESH_TOKEN"], "grant_type": "refresh_token"})
    return t["access_token"]


def post_youtube(item, cfg):
    cap = caption(item)
    meta = {"snippet": {"title": title(item, cap), "description": shorten(cap, 4900), "categoryId": "17",
                        "tags": ["fighter", "mma", "boxing", "muay thai", "fight mindset"]},
            "status": {"privacyStatus": cfg.get("privacy", "private"), "selfDeclaredMadeForKids": False}}
    video = download(item["video_asset"])
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


def post_threads(item, cfg):
    uid, tok = os.environ["THREADS_USER_ID"], os.environ["THREADS_ACCESS_TOKEN"]
    text = shorten(without_hashtags(caption(item)), 500)
    _, _, c = http("POST", f"{TH}/{uid}/threads", {"media_type": "VIDEO", "video_url": signed_url(item["video_asset"]),
                                                   "text": text, "access_token": tok})
    for _ in range(60):  # Threads processes the video before it can be published
        time.sleep(10)
        _, _, s = http("GET", f"{TH}/{c['id']}?fields=status,error_message&access_token={tok}")
        if s.get("status") == "FINISHED":
            break
        if s.get("status") in ("ERROR", "EXPIRED"):
            raise RuntimeError(f"Threads processing {s.get('status')}: {s.get('error_message')}")
    else:
        raise RuntimeError("Threads processing timed out")
    _, _, p = http("POST", f"{TH}/{uid}/threads_publish", {"creation_id": c["id"], "access_token": tok})
    _, _, m = http("GET", f"{TH}/{p['id']}?fields=permalink&access_token={tok}")
    return {"id": p["id"], "url": m.get("permalink")}


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
          "gh secret set THREADS_ACCESS_TOKEN < (value from secrets/crosspost.env)")


# ---------------------------------------------------------------- Facebook (Page "Matteo Fights" Reels)
FB = "https://graph.facebook.com/v21.0"
FB_PAGE = "1070947222779004"


def post_facebook(item, cfg):
    tok, page = os.environ["FB_PAGE_TOKEN"], os.environ.get("FB_PAGE_ID", FB_PAGE)
    _, _, s = http("POST", f"{FB}/{page}/video_reels", {"upload_phase": "start", "access_token": tok})
    vid = s["video_id"]
    http("POST", f"https://rupload.facebook.com/video-upload/v21.0/{vid}", raw=b"",
         headers={"Authorization": f"OAuth {tok}", "file_url": signed_url(item["video_asset"])})
    http("POST", f"{FB}/{page}/video_reels", {"upload_phase": "finish", "video_id": vid, "video_state": "PUBLISHED",
                                              "description": shorten(caption(item), 2000), "access_token": tok})
    for _ in range(60):
        time.sleep(10)
        _, _, st = http("GET", f"{FB}/{vid}?fields=status&access_token={tok}")
        status = st.get("status", {})
        if status.get("video_status") == "ready" or (status.get("publishing_phase") or {}).get("status") == "complete":
            break
        if status.get("video_status") == "error":
            raise RuntimeError(f"Facebook processing error: {json.dumps(status)[:300]}")
    return {"id": vid, "url": f"https://www.facebook.com/reel/{vid}"}


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
           "facebook": (post_facebook, ("FB_PAGE_TOKEN",))}
LABEL = {"youtube": "YouTube Shorts", "threads": "Threads", "facebook": "Facebook Reels"}


def note(text):
    notes = json.loads(NOTES.read_text(encoding="utf-8")) if NOTES.exists() else []
    notes.append({"id": "xp-" + uuid.uuid4().hex[:8], "text": text})
    NOTES.parent.mkdir(parents=True, exist_ok=True)
    NOTES.write_text(json.dumps(notes[-200:], indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def run(dry=False):
    load_env()
    state = json.loads(STATE.read_text(encoding="utf-8"))
    items = json.loads(QUEUE.read_text(encoding="utf-8"))["items"]
    oldest = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=LOOKBACK_DAYS)).strftime("%Y-%m-%dT%H:%M:%SZ")
    done = []
    for name, cfg in state["platforms"].items():
        poster, keys = POSTERS[name]
        if not cfg.get("enabled"):
            continue
        if missing := [k for k in keys if not os.environ.get(k)]:
            print(f"{name}: enabled but secrets missing ({', '.join(missing)}), skipped")
            continue
        since = max(cfg.get("since") or now(), oldest)
        for it in sorted(items, key=lambda x: x.get("posted_at", "")):
            if it.get("status") != "posted" or (it.get("posted_at") or "") < since or not it.get("video_asset"):
                continue
            rec = state["posts"].setdefault(it["id"], {}).get(name, {})
            if rec.get("status") == "posted" or rec.get("tries", 0) >= MAX_TRIES:
                continue
            if dry:
                print(f"would post {it['id']} to {name}")
                continue
            try:
                out = poster(it, cfg)
                state["posts"][it["id"]][name] = {"status": "posted", "at": now(), **out}
                done.append((name, it, out))
                print(f"{name}: posted {it['id']} -> {out.get('url')}")
            except Exception as e:
                tries = rec.get("tries", 0) + 1
                state["posts"][it["id"]][name] = {"status": "failed", "error": str(e)[:500], "tries": tries, "at": now()}
                print(f"{name}: FAILED {it['id']} ({tries}/{MAX_TRIES}): {e}")
                if tries >= MAX_TRIES:
                    note(f"⚠️ {LABEL[name]} gave up on: {it.get('hook', it['id'])}\n{str(e)[:300]}")
            STATE.write_text(json.dumps(state, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    for name, it, out in done:
        extra = " (private until the YouTube API audit passes: tap to make it public)" if out.get("privacy") == "private" else ""
        note(f"📤 {LABEL[name]}: {it.get('hook', it['id'])}\n{out.get('url') or ''}{extra}")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("cmd", choices=["run", "youtube-auth", "threads-check", "threads-refresh", "facebook-setup"])
    p.add_argument("--dry", action="store_true")
    a = p.parse_args()
    {"run": lambda: run(a.dry), "youtube-auth": youtube_auth, "threads-check": threads_check,
     "threads-refresh": threads_refresh, "facebook-setup": facebook_setup}[a.cmd]()


if __name__ == "__main__":
    main()
