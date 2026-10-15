"""Daily listicle factory: turn the next hooks in production/listicles/hooks.json into rendered trial reels,
one per day, waiting in production/schedule/queue.json for Matteo's yes.

    python -P tools/listicle/factory.py --count 7          # run by the "Listicle factory" workflow

For each hook: pick the least-used training clip from the Drive clips folder, render it (render.py), push the
video to the "media" release, copy it to Drive output/listicles/ for Matteo to watch, write the caption + cover
under production/listicles/<id>/, and add a queue item with approved=false on the next free daily slot.
Nothing posts until the item is approved (tools/instagram/approve.py) after Matteo's explicit yes.
Needs: rclone remote "gdrive" (secret RCLONE_CONF), gh CLI (GH_TOKEN), ffmpeg, Pillow.
"""
import argparse, datetime as dt, json, os, subprocess, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from render import render  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
HOOKS = ROOT / "production" / "listicles" / "hooks.json"
STATE = ROOT / "production" / "listicles" / "state.json"
QUEUE = ROOT / "production" / "schedule" / "queue.json"
CLIPS_FOLDER = "1EkBaa-a9m1lX5KQZnmNXQNj-E8E8hCKk"   # Matteo's raw training clips (top level only)
OUT_FOLDER = "1bHwCLpkK2w9e9BN22dXWgQnn8_CLYpR2"     # Drive output; previews go in output/listicles/
VIDEO_EXT = (".mov", ".mp4", ".m4v")
NOT_TRAINING = ("grocery", "view", "motorbike", "driving", "eth.mov", "clip eth", "landmine", "pull ups")
MAX_BYTES = 700 * 1024 * 1024   # skip the 1 GB+ sparring masters: slow to pull, and one 8 s window is enough
REPO = os.environ.get("GITHUB_REPOSITORY", "fightingmatteo-ux/matteofights")


def load(p, default):
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else default


def save(p, data):
    p.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def run(*cmd):
    print("+", " ".join(cmd), flush=True)
    subprocess.run(cmd, check=True, cwd=ROOT)


def list_clips():
    out = subprocess.run(["rclone", "lsjson", "gdrive:", "--drive-root-folder-id", CLIPS_FOLDER, "--files-only"],
                         capture_output=True, text=True, check=True).stdout
    keep = [c for c in json.loads(out) if c["Name"].lower().endswith(VIDEO_EXT) and c.get("Size", 0) <= MAX_BYTES
            and not any(w in c["Name"].lower() for w in NOT_TRAINING)]
    return sorted(keep, key=lambda c: c["ModTime"])


def next_slots(queue, n, hour, minute):
    """Daily slots after the last listicle already in the queue (or from tomorrow if today's slot is gone)."""
    now = dt.datetime.now(dt.timezone.utc)
    taken = [dt.datetime.fromisoformat(i["not_before"].replace("Z", "+00:00"))
             for i in queue["items"] if i["id"].startswith("lst-") and i.get("status") == "queued"]
    day = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if taken:
        day = max(max(taken) + dt.timedelta(days=1), day)
    if day <= now + dt.timedelta(hours=2):  # leave time for the yes
        day += dt.timedelta(days=1)
    return [day + dt.timedelta(days=k) for k in range(n)]


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--count", type=int, default=7)
    p.add_argument("--slot", default="17:00", help="daily post time, UTC HH:MM")
    p.add_argument("--seconds", type=float, default=8.0)
    p.add_argument("--rerender", action="store_true",
                   help="re-render the queued, not-yet-approved listicles in place (same hook, clip and day)")
    a = p.parse_args()
    if a.rerender:
        return rerender(a.seconds)

    hooks, state, queue = load(HOOKS, None), load(STATE, {"clip_uses": {}, "last_clip": None, "music_i": 0}), load(QUEUE, None)
    todo = [h for h in hooks["hooks"] if h.get("status") == "ready"][: a.count]
    if not todo:
        sys.exit("no 'ready' hooks left in production/listicles/hooks.json - ask Claude for a new batch")
    clips = list_clips()
    if not clips:
        sys.exit(f"no video clips in Drive folder {CLIPS_FOLDER}")
    slots = next_slots(queue, len(todo), *map(int, a.slot.split(":")))
    work = ROOT / "media" / "listicles"
    work.mkdir(parents=True, exist_ok=True)

    for h, slot in zip(todo, slots):
        uses = state["clip_uses"]
        # Least-used clip first, never the same clip two days running, then the newest upload.
        pool = [c for c in clips if c["ID"] != state.get("last_clip")] or clips
        clip = min(pool, key=lambda c: (uses.get(c["ID"], 0), -dt.datetime.fromisoformat(
            c["ModTime"].replace("Z", "+00:00")).timestamp()))
        local = work / f"{clip['ID']}{Path(clip['Name']).suffix}"
        if not local.exists():  # by ID: names repeat in the folder
            run("rclone", "backend", "copyid", "gdrive:", clip["ID"], str(local))

        day = slot.strftime("%Y-%m-%d")
        asset = f"lst-{day}-{h['id']}.mp4"
        folder = ROOT / "production" / "listicles" / f"{day}-{h['id']}"
        folder.mkdir(parents=True, exist_ok=True)
        render(local, h["id"], work / asset, a.seconds, folder / "cover.jpg", state["music_i"])
        (folder / "caption.txt").write_text(h["caption"].strip() + "\n", encoding="utf-8")

        run("gh", "release", "upload", "media", str(work / asset), "--clobber", "-R", REPO)
        run("rclone", "copyto", str(work / asset), f"gdrive:listicles/{asset}", "--drive-root-folder-id", OUT_FOLDER)

        qid = f"lst-{day}-{h['id']}"
        queue["items"].append({
            "id": qid, "reel": f"listicles/{day}-{h['id']}", "variant": "-", "hook": h["hook"],
            "archetype": h["archetype"], "clip": f"{clip['Name']} ({clip['ID']})", "video_asset": asset,
            "caption_file": str((folder / "caption.txt").relative_to(ROOT)).replace("\\", "/"),
            "strategy": "MANUAL", "thumb_offset_ms": 500,
            "not_before": slot.strftime("%Y-%m-%dT%H:%M:%SZ"), "min_gap_hours": 2.5,
            "approved": False, "status": "queued"})
        h.update(status="rendered", clip=f"{clip['Name']} ({clip['ID']})", queue_id=qid,
                 rendered_at=dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%MZ"))
        uses[clip["ID"]] = uses.get(clip["ID"], 0) + 1
        state["last_clip"] = clip["ID"]
        state["music_i"] += 1
        save(HOOKS, hooks); save(STATE, state); save(QUEUE, queue)  # after each one: a crash keeps the finished ones
        print(f"{qid}: {h['hook']} | clip {clip['Name']} | posts {slot:%a %d %b %H:%M} UTC once approved", flush=True)


def rerender(seconds):
    """After a render.py change: rebuild every queued, unapproved lst-* item with its own hook and clip."""
    hooks, queue = load(HOOKS, None), load(QUEUE, None)
    by_q = {h.get("queue_id"): h for h in hooks["hooks"]}
    work = ROOT / "media" / "listicles"
    work.mkdir(parents=True, exist_ok=True)
    items = [i for i in queue["items"] if i["id"].startswith("lst-") and not i.get("approved") and i["status"] == "queued"]
    for n, item in enumerate(items):
        h, clip_id = by_q[item["id"]], item["clip"].rsplit("(", 1)[1].rstrip(")")
        local = work / f"{clip_id}{Path(item['clip'].split(' (')[0]).suffix}"
        if not local.exists():
            run("rclone", "backend", "copyid", "gdrive:", clip_id, str(local))
        folder = ROOT / Path(item["caption_file"]).parent
        render(local, h["id"], work / item["video_asset"], seconds, folder / "cover.jpg", n)
        run("gh", "release", "upload", "media", str(work / item["video_asset"]), "--clobber", "-R", REPO)
        run("rclone", "copyto", str(work / item["video_asset"]), f"gdrive:listicles/{item['video_asset']}",
            "--drive-root-folder-id", OUT_FOLDER)
        print(f"{item['id']}: re-rendered", flush=True)


if __name__ == "__main__":
    main()
