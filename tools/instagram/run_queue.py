"""Post the next due, APPROVED trial reel from production/schedule/queue.json. One post per run.

Run by the "Post queue" workflow every 30 min (or by hand). An item posts only when:
  approved == true  (set by Matteo, or by Claude after Matteo's explicit yes to that exact preview)
  status == "queued", now >= not_before, and the account's latest post is >= min_gap_hours old.
Items with app_audio get that Instagram library sound attached through the Audio API (audio.py, FB_USER_TOKEN).
Guard against double posts: if a post from the last 24 h already starts with the item's caption, it is
marked posted instead of posting again. An item is set to "posting" before the API call, and "posting" items are
never picked again, so a failed state write after a successful post can't cause a second post.
All reads and writes go through tools/state.py.
"""
import datetime as dt, json, os, re, subprocess, sys, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import state  # noqa: E402

AUDIO_FIELDS = ("audio_id", "audio_title", "audio_artist", "audio_status", "audio_note")
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
    items = state.all("queue")
    # app_audio items carry a sound from Instagram's library. The Audio API (tools/instagram/audio.py, FB_USER_TOKEN)
    # attaches it; a sound it can't find exactly is marked audio_status "manual" and Matteo posts that one in the app.
    due = [i for i in items if i.get("approved") is True and i.get("status") == "queued"
           and i.get("audio_status") != "manual"
           and not i.get("sound_pending")  # still has baked-in music: wait for the factory's --sounds-only re-render
           and dt.datetime.fromisoformat(i["not_before"].replace("Z", "+00:00")) <= now()]
    item = None
    for cand in sorted(due, key=lambda i: i["not_before"]):
        if not cand.get("app_audio") or cand.get("audio_id"):
            item = cand; break
        ok = resolve_audio(cand)
        state.patch("queue", cand["id"], {k: cand[k] for k in AUDIO_FIELDS if k in cand})
        if not ok:
            continue
        item = cand; break
    if not item:
        print("nothing due"); return
    caption = (ROOT / item["caption_file"]).read_text(encoding="utf-8").strip()
    posts = recent_posts()

    first_line = caption.splitlines()[0].strip()
    for p in posts:
        if now() - p["at"] < dt.timedelta(hours=24) and (p.get("caption") or "").strip().startswith(first_line):
            state.patch("queue", item["id"], dict(status="posted", media_id=p["id"], posted_at=p["timestamp"],
                                                  permalink=p.get("permalink"), note="found already on Instagram, not re-posted"))
            print(f"{item['id']}: already posted ({p['id']})"); return

    gap = dt.timedelta(hours=item.get("min_gap_hours", DEFAULT_GAP_H))
    if posts and now() - posts[0]["at"] < gap:
        print(f"{item['id']}: waiting, latest post {posts[0]['timestamp']} is under {gap} old"); return

    if item.get("audio_id"):  # Facebook Login route, library sound attached
        cmd = [sys.executable, "-P", "tools/instagram/audio.py", "trial", "--asset", item["video_asset"],
               "--caption-file", item["caption_file"], "--strategy", item.get("strategy", "MANUAL"),
               "--audio-id", str(item["audio_id"]), "--confirm"]
        for k, flag in (("audio_volume", "--audio-volume"), ("video_volume", "--video-volume")):
            if item.get(k) is not None:
                cmd += [flag, str(item[k])]
    else:
        cmd = [sys.executable, "-P", "tools/instagram/ig.py", "trial", "--asset", item["video_asset"],
               "--caption-file", item["caption_file"], "--strategy", item.get("strategy", "MANUAL"), "--confirm"]
    if item.get("thumb_offset_ms") is not None:
        cmd += ["--thumb-offset", str(item["thumb_offset_ms"])]
    state.patch("queue", item["id"], {"status": "posting", "posting_since": now().strftime("%Y-%m-%dT%H:%M:%SZ")})
    r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, encoding="utf-8")
    out = r.stdout + r.stderr
    print(out[-3000:])
    m = re.search(r"media id (\d+)\s+(\S+)", out)
    if r.returncode == 0 and m:
        result = dict(status="posted", media_id=m.group(1), permalink=m.group(2),
                      posted_at=now().strftime("%Y-%m-%dT%H:%M:%SZ"))
    else:
        result = dict(status="failed", error=out.strip().splitlines()[-1][:500] if out.strip() else f"exit {r.returncode}")
    state.patch("queue", item["id"], result)
    sys.exit(0 if result["status"] == "posted" else 1)


def resolve_audio(item):
    """Find the item's app_audio sound in Instagram's licensed library and store its audio_id. False = post by hand."""
    sys.path.insert(0, str(ROOT / "tools" / "instagram"))
    import audio
    # "id:A|B name": pinned sound(s), tried in order (e.g. the official track first, a fan upload of it second)
    pinned = re.match(r"\s*id:([\d|]{6,})\s*(.*)", item["app_audio"])
    try:
        if pinned:
            track = None
            for sid in [x for x in pinned.group(1).split("|") if x]:
                try:
                    a = audio.info(sid)
                except audio.ApiError as e:  # not in the API library / deleted: try the next one
                    if re.search(r"access token|oauth|session has expired|permission", str(e), re.I) and \
                            "does not exist" not in str(e):
                        raise  # token problem, not the sound: retry next run
                    print(f"{item['id']}: pinned sound {sid} unavailable ({str(e)[:120]})")
                    continue
                track = {"audio_id": sid, "title": a.get("title") or pinned.group(2),
                         "display_artist": a.get("display_artist"), "ig_username": a.get("ig_username")}
                break
            if not track:
                item.update(audio_status="manual", audio_note="no pinned sound available through the API")
                print(f"{item['id']}: no pinned sound available; left for the app")
                return False
        else:
            track = audio.resolve(item["app_audio"])
    except audio.ApiError as e:  # token missing/expired/scope: not the song's fault, so retry next run
        print(f"{item['id']}: Audio API unavailable ({e}); skipped this run")
        item["audio_note"] = str(e)[:300]
        return False
    if not track:
        print(f"{item['id']}: {item['app_audio']!r} not in the API's licensed library; left for the app")
        item.update(audio_status="manual", audio_note="no exact match in the Audio API library")
        return False
    item.update(audio_id=str(track["audio_id"]), audio_title=track.get("title"),
                audio_artist=track.get("display_artist") or track.get("ig_username"))
    print(f"{item['id']}: audio {track.get('title')} -> {track['audio_id']}")
    return True


if __name__ == "__main__":
    main()
