"""Build the control center's data: control-site/public/data.json (+ cover images).

Runs as the Cloudflare Pages build command on every push, so the site always shows the repo's current state:
    python3 tools/control/build_data.py
Sources: production/schedule/queue.json, production/listicles/{hooks,clips}.json, production/control/*.json
(metrics.json is written by Claude's daily check from Buzzfy).
"""
import datetime as dt, json, os, shutil, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "control-site" / "public"
CTL = ROOT / "production" / "control"


def load(p, default):
    p = Path(p)
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else default


def style_images(questions):
    """Style lab comparison images go next to the page so the Decide tab can show them."""
    out = OUT / "style"
    shutil.rmtree(out, ignore_errors=True)
    for q in questions:
        src = ROOT / q["image"] if q.get("image") else None
        if src and src.exists():
            out.mkdir(parents=True, exist_ok=True)
            shutil.copy(src, out / src.name)
            q["image"] = f"style/{src.name}"
    return questions


PAGES_MAX = 24 * 1024 * 1024  # Cloudflare Pages rejects any file over 25 MiB (the whole deploy fails)


def shrink_for_pages(f):
    """Re-encode a render over the Pages limit into a 720p preview (same name). The dashboard only previews it;
    the full render stays on the media release for posting. Learned 2026-10-17: 39 MB Saenchai renders broke
    every deploy for a day."""
    if f.stat().st_size <= PAGES_MAX:
        return True
    tmp = f.with_suffix(".preview.mp4")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(f), "-vf", "scale=720:-2", "-c:v", "libx264",
                    "-preset", "veryfast", "-crf", "28", "-c:a", "aac", "-b:a", "96k", "-movflags", "+faststart",
                    str(tmp)], check=True)
    tmp.replace(f)
    if f.stat().st_size > PAGES_MAX:  # very long video: drop it rather than break the deploy
        f.unlink()
        print(f"video {f.name}: still over 24 MiB after the preview encode, left off the dashboard")
        return False
    return True


def fetch_videos(queue):
    """Copy the videos of reels waiting, scheduled or posted in the last 3 days next to the page (behind the Access
    login) so the dashboard can play them. Needs GH_TOKEN + gh (the deploy workflow); skipped locally."""
    if not os.environ.get("GH_TOKEN"):
        return {}
    vdir = OUT / "videos"
    shutil.rmtree(vdir, ignore_errors=True)
    vdir.mkdir(parents=True)
    cutoff = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=3)).strftime("%Y-%m-%dT%H:%M:%SZ")
    want = {i["id"]: i["video_asset"] for i in queue if i.get("video_asset") and
            (i["status"] == "queued" or (i["status"] == "posted" and (i.get("posted_at") or "") >= cutoff))}
    got = {}
    for qid, asset in want.items():
        r = subprocess.run(["gh", "release", "download", "media", "-p", asset, "-D", str(vdir), "--clobber"],
                           capture_output=True, text=True)
        if r.returncode == 0 and (vdir / asset).exists():
            if shrink_for_pages(vdir / asset):
                got[qid] = f"videos/{asset}"
        else:
            print(f"video {asset}: {r.stderr.strip()[:120]}")
    return got


def main():
    queue = load(ROOT / "production/schedule/queue.json", {"items": []})["items"]
    hooks = load(ROOT / "production/listicles/hooks.json", {"hooks": []})["hooks"]
    clips = load(ROOT / "production/listicles/clips.json", {})
    live = load(ROOT / "production/listicles/clip-sheets/index.json", {})
    metrics = load(CTL / "metrics.json", {})
    per = metrics.get("reels", {})
    hook_fmt = {h.get("queue_id"): h for h in hooks}

    xpost = load(ROOT / "production/schedule/crosspost.json", {}).get("posts", {})
    videos = fetch_videos(queue)
    covers = OUT / "covers"
    shutil.rmtree(covers, ignore_errors=True)
    covers.mkdir(parents=True, exist_ok=True)
    reels = []
    for i in queue:
        folder = ROOT / Path(i.get("caption_file", "x/x")).parent
        cover = None
        if (folder / "cover.jpg").exists():
            cover = f"covers/{folder.name}.jpg"
            shutil.copy(folder / "cover.jpg", OUT / cover)
        m = per.get(i.get("media_id") or "", {})
        h = hook_fmt.get(i["id"], {})
        if i["status"] == "posted":
            state = "posted"
        elif i["status"] == "failed":
            state = "failed"
        elif i.get("approved"):
            state = "scheduled"
        else:
            state = "needs_yes"
        label = i.get("hook") or h.get("hook")
        if not label and (ROOT / i.get("caption_file", "x")).is_file():
            first = (ROOT / i["caption_file"]).read_text(encoding="utf-8").strip().splitlines()
            label = first[0][:90] if first else None
        if label and (i.get("variant") or "") .isalpha():
            label = f"{i['variant']}: {label}"
        reels.append({
            "id": i["id"], "hook": label or i.get("reel", i["id"]),
            "format": i.get("format") or ("talking head" if not i["id"].startswith("lst-") else "listicle"),
            "time": i.get("not_before"), "state": state, "cover": cover,
            "clip": (i.get("clip") or "").split(" (")[0], "review": i.get("review"),
            "permalink": i.get("permalink"), "posted_at": i.get("posted_at"), "error": i.get("error"),
            "metrics": m,
            "video": videos.get(i["id"]),
            "links": {k: v.get("url") for k, v in xpost.get(i["id"], {}).items() if v.get("status") == "posted" and v.get("url")},
        })

    # per-format results (posted reels with numbers)
    fmt = {}
    for r in reels:
        v = r["metrics"].get("views")
        if v is None:
            continue
        f = fmt.setdefault(r["format"], {"reels": 0, "views": 0, "shares": 0, "saves": 0, "follows": 0, "winners": 0})
        f["reels"] += 1
        f["views"] += v
        for k in ("shares", "saves", "follows"):
            f[k] += r["metrics"].get(k) or 0
        f["winners"] += 1 if (r["metrics"].get("vs_median_x") or 0) >= 2 else 0

    data = {
        "generated_at": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "account": "matteofights",
        "baseline": {k: metrics.get(k) for k in ("median_views", "updated", "audience")},
        "reels": sorted(reels, key=lambda r: r["time"] or "", reverse=True),
        "formats": fmt,
        "questions": style_images(load(CTL / "questions.json", [])),
        "lab": load(ROOT / "production/style/lab.json", {"experiments": []}),
        "ideas": load(CTL / "ideas.json", [])[-50:],
        "log": load(CTL / "log.json", [])[-60:],
        "platforms": load(CTL / "platforms.json", {}),
        # other platforms (tools/crosspost): per-reel results + written Threads posts (approved weekly)
        "crosspost": {k: v for k, v in load(ROOT / "production/schedule/crosspost.json", {}).items() if k != "_how"},
        "threads_posts": sorted(load(ROOT / "production/threads/posts.json", {"posts": []})["posts"],
                                key=lambda p: p["at"])[-60:],
        # Results > Rivals: competitor outliers (tools/competitors/scout.py) + idea cards (competitor-ideas skill)
        "competitors": {**{k: v for k, v in load(ROOT / "production/competitors/outliers.json", {}).items() if k != "outliers"},
                        "outliers": load(ROOT / "production/competitors/outliers.json", {}).get("outliers", [])[:80],
                        "ideas": load(ROOT / "production/competitors/ideas.json", {}).get("ideas", []),
                        "skip": load(ROOT / "production/competitors/ideas.json", {}).get("skip", [])},
        "health": {
            "hooks_ready": sum(1 for h in hooks if h.get("status") == "ready"),
            "clips_live": len(live), "clips_catalogued": len([k for k in clips if k in live]) if live else len(clips),
            "clips_usable": sum(1 for k, v in clips.items() if v.get("usable") and (not live or k in live)),
            "failed": [r["id"] for r in reels if r["state"] == "failed"],
            "last_post": max((r["posted_at"] for r in reels if r.get("posted_at")), default=None),
            "next_post": min((r["time"] for r in reels if r["state"] == "scheduled" and r["time"]), default=None),
        },
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "data.json").write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    print(f"data.json: {len(reels)} reels, {len(data['questions'])} questions, {len(data['ideas'])} ideas")


if __name__ == "__main__":
    main()
