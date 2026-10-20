"""Sound scout: which Instagram sounds are carrying outlier reels in Matteo's niche, and which of them the Audio
API can attach to his reels.

    python -P tools/instagram/sound_scout.py            # runs in the "Sound scout" Action (Instagram + FB_USER_TOKEN)

1. Reels to read: every Instagram outlier in production/competitors/outliers.json, plus the hand-picked niche hits
   in production/sounds/watch.json ({"reels": [{"url", "views", "note"}]}, e.g. viral fighter reels from Buzzfy).
2. For each reel, yt-dlp reads the metadata only (no download) and gives the sound: `track` + `artist`, or nothing
   for original audio. Logged-out first, IG_COOKIES if set; a blocked reel is skipped, not fatal.
3. Sounds are grouped and ranked by the views they carried (count, total, best multiple of the creator's median).
4. Each named sound is looked up with audio.resolve() (exact title, artist if known) against the licensed library
   through FB_USER_TOKEN. A hit gets `audio_id`: queue items can use it (`audio_id` / `app_audio`) and
   `audio.py trial --audio-id` attaches it. No hit = the sound isn't cleared for third-party apps; add it in the app.

Writes production/sounds/proven.json (newest run wins; `history` keeps first-seen dates).
"""
import json
import os
import re
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
import audio  # noqa: E402

OUT = ROOT / "production/sounds/proven.json"
WATCH = ROOT / "production/sounds/watch.json"


def reels():
    o = json.loads((ROOT / "production/competitors/outliers.json").read_text(encoding="utf-8"))
    rows = [{"url": x["url"], "views": x.get("views") or 0, "x": x.get("x"), "handle": x.get("handle"),
             "hook": x.get("hook", "")[:80]} for x in o["outliers"] if x.get("platform") == "instagram"]
    if WATCH.exists():
        for r in json.loads(WATCH.read_text(encoding="utf-8")).get("reels", []):
            rows.append({"url": r["url"], "views": r.get("views") or 0, "x": None, "handle": r.get("handle", ""),
                         "hook": r.get("note", "")[:80]})
    seen, out = set(), []
    for r in rows:
        if r["url"] not in seen:
            seen.add(r["url"]); out.append(r)
    return out


MUSIC = re.compile(r'"music_asset_info"\s*:\s*\{.*?"title"\s*:\s*"((?:[^"\\]|\\.)*)".*?"display_artist"\s*:\s*"((?:[^"\\]|\\.)*)"', re.S)
ORIGINAL = re.compile(r'"original_sound_info"\s*:\s*\{.*?"original_audio_title"\s*:\s*"((?:[^"\\]|\\.)*)"', re.S)
CLUSTER = re.compile(r'"audio_cluster_id"\s*:\s*"?(\d{6,})')


def _unescape(t):
    try:
        return json.loads(f'"{t}"')
    except ValueError:
        return t


def sound_of(url, cookies):
    """The reel's sound. yt-dlp's -j leaves track/artist empty for Instagram, so the raw API pages it fetched are
    saved (--write-pages) and read for music_asset_info (licensed music) / original_sound_info (original audio)."""
    for use_cookies in ([True, False] if cookies else [False]):
        tmp = tempfile.mkdtemp()
        args = ["yt-dlp", "--skip-download", "--write-pages", "--no-warnings", "-o", f"{tmp}/x.%(ext)s", url]
        if use_cookies:
            args[1:1] = ["--cookies", cookies]
        p = subprocess.run(args, capture_output=True, text=True, timeout=90, cwd=tmp)
        pages = "".join(f.read_text(encoding="utf-8", errors="replace") for f in Path(tmp).glob("*.dump"))
        if p.returncode != 0 and not pages:
            continue
        m, o, c = MUSIC.search(pages), ORIGINAL.search(pages), CLUSTER.search(pages)
        if m:
            return {"ok": True, "kind": "music", "track": _unescape(m.group(1)).strip(),
                    "artist": _unescape(m.group(2)).strip(), "cluster": c.group(1) if c else None}
        if o:
            return {"ok": True, "kind": "original", "track": _unescape(o.group(1)).strip(), "artist": "",
                    "cluster": c.group(1) if c else None}
        return {"ok": p.returncode == 0, "kind": None, "track": "", "artist": "", "cluster": None,
                "pages": len(pages)}
    return {"ok": False}


def main():
    cookies = None
    if os.environ.get("IG_COOKIES"):
        cookies = os.path.join(tempfile.mkdtemp(), "cookies.txt")
        Path(cookies).write_text(os.environ["IG_COOKIES"], encoding="utf-8")
    prev = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else {}
    first_seen = {s["key"]: s.get("first_seen") for s in prev.get("sounds", [])}
    groups, read, blocked, no_info = {}, 0, 0, 0
    for r in reels():
        s = sound_of(r["url"], cookies)
        if not s["ok"]:
            blocked += 1
            continue
        read += 1
        if not s["track"]:
            no_info += 1
            continue
        if s["kind"] == "original" and r["views"] < 100000:
            continue  # small creators' own voice tracks: not a reusable sound
        key = f'{s["track"]} - {s["artist"]}' if s["artist"] else s["track"]
        g = groups.setdefault(key, {"key": key, "title": s["track"], "artist": s["artist"], "kind": s["kind"],
                                    "cluster": s["cluster"], "reels": []})
        g["reels"].append(r)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    sounds = []
    for g in groups.values():
        hit = None
        try:
            hit = audio.resolve(g["key"], "original_sound" if g["kind"] == "original" else "music")
        except audio.ApiError as e:
            print(f"lookup failed for {g['key']}: {e}")
        sounds.append({
            "key": g["key"], "title": g["title"], "artist": g["artist"], "kind": g["kind"],
            "instagram_audio_page": f"https://www.instagram.com/reels/audio/{g['cluster']}/" if g["cluster"] else None,
            "reels": len(g["reels"]), "views": sum(r["views"] for r in g["reels"]),
            "best_x": max([r["x"] for r in g["reels"] if r["x"]] or [None], key=lambda v: v or 0),
            "examples": sorted(g["reels"], key=lambda r: -r["views"])[:3],
            "audio_id": hit.get("audio_id") if hit else None,
            "cleared": bool(hit), "first_seen": first_seen.get(g["key"]) or today})
    sounds.sort(key=lambda s: (-s["reels"], -s["views"]))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"updated": today, "read": read, "blocked": blocked, "no_sound_info": no_info,
                               "_how": "tools/instagram/sound_scout.py. cleared=true sounds can be attached by the "
                                       "Audio API (audio_id); others only in the Instagram app.",
                               "sounds": sounds}, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"read {read} reels ({blocked} blocked, {no_info} without sound info), {len(sounds)} named sounds, "
          f"{sum(s['cleared'] for s in sounds)} cleared for the API")
    for s in sounds[:20]:
        print(f"  {'OK ' if s['cleared'] else '-- '}{s['reels']}x {s['views']:>9} views  {s['key']}  {s['audio_id'] or ''}")


if __name__ == "__main__":
    main()
