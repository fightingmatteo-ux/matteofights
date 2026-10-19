"""Instagram Audio API: find a sound from Instagram's library and post a trial reel WITH it, no app needed.

Meta's Audio API (June 2026) lets an app search Instagram music / original sounds that are cleared for
third-party use and attach one to a Reel when the container is created. It only works with Facebook Login
(graph.facebook.com), NOT with the Instagram Login token ig.py uses. So this file uses FB_USER_TOKEN
(the same Facebook Login token Business Discovery / competitors use) and never touches IG_ACCESS_TOKEN.

    python -P tools/instagram/audio.py check                               # does FB_USER_TOKEN have the scopes?
    python -P tools/instagram/audio.py search "echo sax end"               # music (default)
    python -P tools/instagram/audio.py search "gym motivation" --type original_sound
    python -P tools/instagram/audio.py search                              # no query = trending music
    python -P tools/instagram/audio.py info <audio_id>
    python -P tools/instagram/audio.py trial --asset lst-...mp4 --caption-file ... --audio "Echo Sax End"
    python -P tools/instagram/audio.py trial ... --audio-id 587784541076604 --confirm   # only after Matteo's yes

Needs (Facebook Login token, Graph API Explorer on app matteofights-poster): instagram_basic and
instagram_content_publish, plus pages_show_list / pages_read_engagement so the IG account is reachable through
the Page. `check` says what is missing. Limits from Meta: only tracks cleared for third parties (some songs in the
app are missing), no preview of reels with attached audio, and trial_params + audio together is undocumented:
if Meta refuses the pair the error is printed and nothing is posted.
"""
import argparse, json, os, re, sys, time, unicodedata, urllib.error, urllib.parse, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
GRAPH = "https://graph.facebook.com/v23.0"
IG_ID = os.environ.get("IG_FB_USER_ID", "17841465098113052")  # @matteofights as seen through Facebook Login
NEEDED = {"instagram_basic", "instagram_content_publish"}
DEFAULT_AUDIO_VOL, DEFAULT_VIDEO_VOL = 100, 20  # library sound on top, clip's own sound (bag, breathing) underneath


class ApiError(Exception):
    pass


def token():
    if not os.environ.get("FB_USER_TOKEN"):
        meta = ROOT / "secrets" / "meta.env"
        if meta.exists():
            for l in meta.read_text(encoding="utf-8").splitlines():
                if l.startswith("FB_USER_TOKEN="):
                    os.environ["FB_USER_TOKEN"] = l.split("=", 1)[1].strip()
    if not os.environ.get("FB_USER_TOKEN"):
        raise ApiError("No FB_USER_TOKEN (secrets/meta.env or the environment / Actions secret).")
    return os.environ["FB_USER_TOKEN"]


def call(method, path, params=None):
    params = {**(params or {}), "access_token": token()}
    url = path if path.startswith("http") else f"{GRAPH}/{path}"
    body = urllib.parse.urlencode(params).encode() if method == "POST" else None
    if method == "GET":
        url += "?" + urllib.parse.urlencode(params)
    try:
        with urllib.request.urlopen(urllib.request.Request(url, data=body, method=method), timeout=120) as r:
            return json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        raw = e.read().decode(errors="replace")
        try:
            msg = json.loads(raw).get("error", {}).get("message", raw)
        except ValueError:
            msg = raw
        raise ApiError(f"{method} {url.split('?')[0]} -> {e.code}: {msg}")


# ---------------------------------------------------------------- checks + search
def check():
    perms = call("GET", "me/permissions")["data"]
    granted = {p["permission"] for p in perms if p["status"] == "granted"}
    missing = NEEDED - granted
    print("granted:", ", ".join(sorted(granted)) or "(none)")
    if missing:
        print(f"MISSING: {', '.join(sorted(missing))}. Regenerate FB_USER_TOKEN with these added (README, 'Audio API').")
        return False
    acct = call("GET", IG_ID, {"fields": "username"})
    print(f"OK: FB_USER_TOKEN can publish reels with library audio as @{acct.get('username')}")
    return True


def search(query="", kind="music"):
    params = {"audio_type": kind, "user_id": IG_ID}
    if query:
        params["search_query"] = query
    return call("GET", "ig_audio", params).get("audio", [])


def info(audio_id):
    return call("GET", audio_id, {"user_id": IG_ID})


def _norm(s):
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


def resolve(name, kind="music"):
    """audio_id for a sound named in the queue (e.g. 'Echo Sax End - Caleb Arredondo (add in the Instagram app)'),
    or None. Only an exact title match counts: posting the wrong song is worse than posting it by hand."""
    name = re.sub(r"\(.*?\)", "", name or "").strip()
    parts = re.split(r"\s+[-–|]\s+|\s+by\s+", name, maxsplit=1)
    title, artist = parts[0].strip(), (parts[1].strip() if len(parts) > 1 else "")
    if not title:
        return None
    for a in search(title, kind):
        if _norm(a.get("title")) != _norm(title):
            continue
        if artist and _norm(artist) not in _norm(a.get("display_artist") or a.get("ig_username") or ""):
            continue
        return a
    return None


def show(a):
    secs = (a.get("duration_in_ms") or 0) / 1000
    who = a.get("display_artist") or (f"@{a['ig_username']}" if a.get("ig_username") else "")
    link = a.get("on_platform_audio_preview_link") or ""
    print(f"{a.get('audio_id')}  {a.get('title')}  {who}  {secs:.0f}s  {link}")


# ---------------------------------------------------------------- post
def trial(asset, caption, strategy="MANUAL", audio_id=None, audio_name="", audio_volume=DEFAULT_AUDIO_VOL,
          video_volume=DEFAULT_VIDEO_VOL, thumb_offset=None, confirm=False):
    """Trial reel with a library sound. Returns (media_id, permalink) once published, None for a preview."""
    import ig  # tools/instagram/ig.py: only for the signed media-release link, no Instagram token involved
    track = info(audio_id) if audio_id else resolve(audio_name)
    if not track:
        raise ApiError(f"No exact match in Instagram's licensed library for {audio_name!r}. "
                       f"Search it (audio.py search ...) and pass --audio-id, or post that one in the app.")
    audio_id = track.get("audio_id") or audio_id
    size, url = ig.release_asset(asset)
    print("=" * 60)
    print("PREVIEW: trial reel WITH Instagram library audio (nothing is sent without --confirm)")
    print(f"  account   {IG_ID} (Facebook Login)")
    print(f"  video     {asset} on the media release ({size / 1e6:.1f} MB)")
    print(f"  audio     {track.get('title')} | {track.get('display_artist') or track.get('ig_username') or '?'} "
          f"| id {audio_id} | music {audio_volume}% / clip sound {video_volume}%")
    print(f"  trial     {strategy}")
    if thumb_offset is not None:
        print(f"  cover     frame at {thumb_offset} ms")
    print(f"  caption   ({len(caption)} chars)")
    print("  " + "\n  ".join(caption.splitlines() or ["(empty)"]))
    print("  note      Meta can't preview reels with attached audio: it publishes exactly as configured.")
    print("=" * 60)
    if not confirm:
        print("Preview only. Re-run with --confirm after the explicit yes.")
        return None

    params = {"media_type": "REELS", "video_url": url, "caption": caption,
              "trial_params": json.dumps({"graduation_strategy": strategy}),
              "audio_configuration": json.dumps({"audio_id": str(audio_id), "audio_volume": int(audio_volume),
                                                 "video_volume": int(video_volume)})}
    if thumb_offset is not None:
        params["thumb_offset"] = thumb_offset
    cid = call("POST", f"{IG_ID}/media", params)["id"]
    print(f"container {cid}, Meta is fetching the video...")
    for _ in range(60):  # up to ~10 min
        s = call("GET", cid, {"fields": "status_code,status"})
        if s.get("status_code") == "FINISHED":
            break
        if s.get("status_code") in ("ERROR", "EXPIRED"):
            raise ApiError(f"Processing failed: {s}")
        time.sleep(10)
    else:
        raise ApiError(f"Still processing after 10 min (container {cid}).")
    media_id = call("POST", f"{IG_ID}/media_publish", {"creation_id": cid})["id"]
    link = call("GET", media_id, {"fields": "permalink"}).get("permalink")
    print(f"PUBLISHED trial reel with audio: media id {media_id}  {link}")
    return media_id, link


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("check")
    s = sub.add_parser("search"); s.add_argument("query", nargs="?", default="")
    s.add_argument("--type", choices=["music", "original_sound"], default="music")
    i = sub.add_parser("info"); i.add_argument("audio_id")
    t = sub.add_parser("trial")
    t.add_argument("--asset", required=True, help="file name on the media release")
    t.add_argument("--caption-file"); t.add_argument("--caption")
    g = t.add_mutually_exclusive_group(required=True)
    g.add_argument("--audio-id"); g.add_argument("--audio", help="sound title, optionally 'Title - Artist'")
    t.add_argument("--audio-volume", type=int, default=DEFAULT_AUDIO_VOL)
    t.add_argument("--video-volume", type=int, default=DEFAULT_VIDEO_VOL)
    t.add_argument("--strategy", choices=["MANUAL", "SS_PERFORMANCE"], default="MANUAL")
    t.add_argument("--thumb-offset", type=int)
    t.add_argument("--confirm", action="store_true", help="actually publish (only after an explicit yes)")
    a = p.parse_args()
    try:
        if a.cmd == "check":
            sys.exit(0 if check() else 1)
        elif a.cmd == "search":
            res = search(a.query, a.type)
            print(f"{len(res)} result(s){'' if a.query else ' (trending)'}:")
            for x in res:
                show(x)
        elif a.cmd == "info":
            show(info(a.audio_id))
        else:
            cap = Path(a.caption_file).read_text(encoding="utf-8").strip() if a.caption_file else (a.caption or "")
            trial(a.asset, cap, a.strategy, a.audio_id, a.audio or "", a.audio_volume, a.video_volume,
                  a.thumb_offset, a.confirm)
    except ApiError as e:
        sys.exit(str(e))


if __name__ == "__main__":
    main()
