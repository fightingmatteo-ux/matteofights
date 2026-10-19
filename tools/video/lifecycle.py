"""Delete posted videos from the cloud, keep a permanent record of each one.

    python3 -P tools/video/lifecycle.py            # dry run: say what would be deleted
    python3 -P tools/video/lifecycle.py --apply    # write the records + mark the queue (then commit and push)
    python3 -P tools/video/lifecycle.py --delete   # delete the files whose record is pushed (Media cleanup, daily)

Records first, files second: nothing is deleted unless its record is already in git, so a failed push can't
lose a video's history.

A posted reel's video (on the "media" release, plus its preview copy in Drive output/) is deleted once ALL of:
  - it posted on Instagram at least KEEP_DAYS ago,
  - every enabled cross-post platform is done with it (posted/skipped/missed), or it posted MAX_HOLD_DAYS ago,
  - no unposted queue item still uses the same file,
  - Matteo didn't tap "Keep video" on the dashboard (queue item keep_video: true),
  - it isn't a winner (>= 2x median views) younger than WINNER_DAYS (he may re-post it to the grid).
Reference videos fetched by the Fetch video workflow are deleted REF_DAYS after upload: their frames, cuts and
transcript stay committed in content-bank/references/videos/<slug>/. Raw footage is never touched.

The record lives in production/archive/reels.json (id, hook, format, caption, cover, permalink, media_id, the
numbers at deletion time and every cross-post link). Analytics keep working after deletion: Instagram, Facebook
and Threads stats are read by post id, never from the file. The queue item gets video_deleted_at so nothing
tries to download it again.
Needs: GH_TOKEN + gh; rclone remote "gdrive" (RCLONE_CONF) for the Drive copies (skipped when missing).
"""
import argparse, datetime as dt, json, os, shutil, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPO = os.environ.get("GITHUB_REPOSITORY", "fightingmatteo-ux/matteofights")
QUEUE = ROOT / "production/schedule/queue.json"
XPOST = ROOT / "production/schedule/crosspost.json"
METRICS = ROOT / "production/control/metrics.json"
PLATFORMS = ROOT / "production/control/platforms.json"
ARCHIVE = ROOT / "production/archive/reels.json"
REFS = [ROOT / "content-bank/references/videos"]
OUT_FOLDER = "1bHwCLpkK2w9e9BN22dXWgQnn8_CLYpR2"  # Drive output/ (factory.py OUT_FOLDER); listicles in listicles/

KEEP_DAYS, MAX_HOLD_DAYS, WINNER_DAYS, REF_DAYS = 7, 21, 30, 14
VIDEO_PLATFORMS = ("facebook", "youtube", "threads", "tiktok")
DONE = ("posted", "skipped", "missed")


def now():
    return dt.datetime.now(dt.timezone.utc)


def stamp(t):
    return t.strftime("%Y-%m-%dT%H:%M:%SZ")


def parse(s):
    return dt.datetime.fromisoformat(s.replace("Z", "+00:00")) if s else None


def load(p, default):
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else default


def release_assets():
    out = subprocess.run(["gh", "api", "--paginate", f"repos/{REPO}/releases/tags/media", "--jq",
                          ".assets[] | [.id, .name, .size, .created_at] | @tsv"], capture_output=True, text=True)
    if out.returncode:
        sys.exit(f"could not list the media release: {out.stderr.strip()}")
    rows = [l.split("\t") for l in out.stdout.splitlines() if l.strip()]
    return {r[1]: {"id": r[0], "size": int(r[2]), "created": r[3]} for r in rows}


def crossposts_done(item, xpost, age_days):
    if age_days >= MAX_HOLD_DAYS:
        return True, "hold limit"
    posted = parse(item["posted_at"])
    recs = xpost.get("posts", {}).get(item["id"], {})
    for name in VIDEO_PLATFORMS:
        cfg = xpost.get("platforms", {}).get(name) or {}
        if not cfg.get("enabled") or (parse(cfg.get("since")) and posted < parse(cfg["since"])):
            continue
        if (recs.get(name) or {}).get("status") not in DONE:
            return False, f"waiting on {name}"
    return True, "cross-posts done"


def reel_record(item, metrics, platforms, xpost, asset, size):
    m = metrics.get("reels", {}).get(item.get("media_id") or "", {})
    folder = Path(item.get("caption_file", "x/x")).parent
    cover = folder / "cover.jpg"
    hook = item.get("hook")
    cap = ROOT / item.get("caption_file", "x")
    if not hook and cap.is_file():
        hook = next((l.strip() for l in cap.read_text(encoding="utf-8").splitlines() if l.strip()), None)
    return {
        "id": item["id"], "hook": hook, "format": item.get("format") or ("listicle" if item["id"].startswith("lst-") else "talking head"), "reel": item.get("reel"),
        "variant": item.get("variant"), "caption_file": item.get("caption_file"),
        "cover": str(cover) if (ROOT / cover).exists() else None,
        "posted_at": item.get("posted_at"), "media_id": item.get("media_id"), "permalink": item.get("permalink"),
        "metrics_at_deletion": {k: v for k, v in m.items() if v is not None},
        "platform_stats_at_deletion": {p: v for p, v in (platforms.get("posts", {}).get(item["id"]) or {}).items()},
        "crossposts": {p: {k: r.get(k) for k in ("status", "url", "id", "at")}
                       for p, r in xpost.get("posts", {}).get(item["id"], {}).items()},
        "video": {"asset": asset, "mb": round(size / 1e6, 1)},
    }


def drive_delete(asset):
    """Move the preview copy in Drive output/ (listicles/ or the top level) to the trash. Missing copies are fine."""
    if not shutil.which("rclone") or not os.environ.get("RCLONE_CONFIG_OK"):
        return False
    hit = False
    for path in (f"listicles/{asset}", asset):
        base = ["rclone", "--drive-root-folder-id", OUT_FOLDER]
        if subprocess.run(base + ["lsf", f"gdrive:{path}"], capture_output=True, text=True).stdout.strip():
            hit = True
            subprocess.run(base + ["deletefile", "--drive-use-trash=true", f"gdrive:{path}"], check=False)
    return hit


def delete_recorded():
    """Delete the files of every reel/reference whose record is committed (video_deleted_at set) but still stored."""
    q, archive = load(QUEUE, {"items": []}), load(ARCHIVE, {"reels": {}, "references": {}})
    assets = release_assets()
    names = [i["video_asset"] for i in q["items"] if i.get("video_deleted_at") and i.get("video_asset")]
    names += [r["asset"] for r in archive.get("references", {}).values()]
    still_needed = {i["video_asset"] for i in q["items"] if i.get("video_asset") and i["status"] != "posted"}
    for name in dict.fromkeys(names):
        if name in still_needed:
            print(f"  {name}: an unposted reel uses it again, kept")
            continue
        info = assets.get(name)
        if info:
            subprocess.run(["gh", "api", "-X", "DELETE", f"repos/{REPO}/releases/assets/{info['id']}"], check=True)
        drive = drive_delete(name)
        if info or drive:
            print(f"  deleted {name}{' (release)' if info else ''}{' (Drive)' if drive else ''}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="write records + mark the queue")
    ap.add_argument("--delete", action="store_true", help="delete files whose record is committed")
    a = ap.parse_args()
    if a.delete:
        return delete_recorded()

    q = load(QUEUE, {"items": []})
    xpost, metrics, platforms = load(XPOST, {}), load(METRICS, {}), load(PLATFORMS, {})
    archive = load(ARCHIVE, {"_how": "Posted reels whose video was deleted (tools/video/lifecycle.py). "
                             "The numbers keep updating in production/control/; this is the record at deletion.",
                             "reels": {}, "references": {}})
    assets = release_assets()
    t = now()
    still_needed = {i["video_asset"] for i in q["items"] if i.get("video_asset") and i["status"] != "posted"}
    deleted, kept, freed = [], [], 0

    for i in q["items"]:
        asset = i.get("video_asset")
        if i["status"] != "posted" or not asset or i.get("video_deleted_at") or not i.get("posted_at"):
            continue
        age = (t - parse(i["posted_at"])).total_seconds() / 86400
        m = metrics.get("reels", {}).get(i.get("media_id") or "", {})
        winner = (m.get("vs_median_x") or 0) >= 2
        ok, why = crossposts_done(i, xpost, age)
        reason = (None if age >= KEEP_DAYS else f"posted {age:.1f} d ago (< {KEEP_DAYS})") \
            or (None if ok else why) \
            or ("Matteo kept it" if i.get("keep_video") else None) \
            or (f"winner, kept {WINNER_DAYS} d" if winner and age < WINNER_DAYS else None) \
            or ("an unposted reel uses the same file" if asset in still_needed else None)
        if reason:
            kept.append(f"{i['id']}: {reason}")
            continue
        a_info = assets.get(asset)
        size = a_info["size"] if a_info else 0
        if a.apply:
            archive["reels"][i["id"]] = {**reel_record(i, metrics, platforms, xpost, asset, size),
                                         "video_deleted_at": stamp(t)}
            i["video_deleted_at"] = stamp(t)
        freed += size
        deleted.append(f"{i['id']}: {asset} ({size / 1e6:.0f} MB)")

    # Watched reference videos: the analysis is in the repo, the mp4 isn't needed after REF_DAYS
    queue_assets = {i.get("video_asset") for i in q["items"]}
    for name, info in assets.items():
        slug = name.rsplit(".", 1)[0]
        if name in queue_assets or slug in archive["references"] or not any((d / slug).is_dir() for d in REFS):
            continue
        age = (t - parse(info["created"])).total_seconds() / 86400
        if age < REF_DAYS:
            kept.append(f"reference {name}: {age:.0f} d old (< {REF_DAYS})")
            continue
        if a.apply:
            archive["references"][slug] = {"asset": name, "mb": round(info["size"] / 1e6, 1),
                                           "analysis": next(str((d / slug).relative_to(ROOT)) for d in REFS if (d / slug).is_dir()),
                                           "video_deleted_at": stamp(t)}
        freed += info["size"]
        deleted.append(f"reference {name} ({info['size'] / 1e6:.0f} MB)")

    print(("RECORDED, deleted after the push" if a.apply else "WOULD DELETE") + f" ({len(deleted)}, {freed / 1e6:.0f} MB):")
    print("\n".join(f"  {d}" for d in deleted) or "  nothing")
    print(f"KEPT ({len(kept)}):")
    print("\n".join(f"  {k}" for k in kept) or "  nothing")
    if a.apply and deleted:
        ARCHIVE.parent.mkdir(parents=True, exist_ok=True)
        ARCHIVE.write_text(json.dumps(archive, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
        QUEUE.write_text(json.dumps(q, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
