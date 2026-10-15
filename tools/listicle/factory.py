"""Daily listicle factory: turn the next hooks in production/listicles/hooks.json into rendered trial reels,
one per day, waiting in production/schedule/queue.json for Matteo's yes.

    python -P tools/listicle/factory.py --count 7          # run by the "Listicle factory" workflow

For each hook: the footage agent (footage_agent.py) picks the clip that best fits the hook out of every clip in
the Drive folder, the reel is rendered (render.py) and the agent reviews the finished video; a failed review moves
on to the next-best clip (up to MAX_TRIES). Without ANTHROPIC_API_KEY it falls back to the least-used clip. Then push the
video to the "media" release, copy it to Drive output/listicles/ for Matteo to watch, write the caption + cover
under production/listicles/<id>/, and add a queue item with approved=false on the next free daily slot.
Nothing posts until the item is approved (tools/instagram/approve.py) after Matteo's explicit yes.
Needs: rclone remote "gdrive" (secret RCLONE_CONF), gh CLI (GH_TOKEN), ffmpeg, Pillow.
"""
import argparse, datetime as dt, json, os, subprocess, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from render import render  # noqa: E402
import footage_agent as agent  # noqa: E402

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
WORK = ROOT / "media" / "listicles"
MAX_TRIES = 3


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


def fetch(clip_id, name):
    local = WORK / f"{clip_id}{Path(name).suffix}"
    if not local.exists():  # by ID: names repeat in the folder
        run("rclone", "backend", "copyid", "gdrive:", clip_id, str(local))
    return local


def nearby_clips(queue, day, skip_id=None, days=2):
    """Clip ids already used by queued reels within `days` of this one: no same-looking reels back to back."""
    d0 = dt.date.fromisoformat(day)
    out = set()
    for i in queue["items"]:
        if i["id"].startswith("lst-") and i["id"] != skip_id and i.get("status") == "queued" and "(" in i.get("clip", ""):
            if abs((dt.date.fromisoformat(i["not_before"][:10]) - d0).days) <= days:
                out.add(i["clip"].rsplit("(", 1)[1].rstrip(")"))
    return out


def produce(h, out, cover, music_i, seconds, clips, cat, uses, avoid, first=None):
    """Render h onto the best clip. Returns (clip dict, rotate, review or None).

    With the agent: candidates = [first] + agent.match(...); render, review, keep the best; stop at the first pass."""
    by_id = {c["ID"]: c for c in clips}
    if cat is None:  # no API key: least-used clip, newest upload first
        pool = [c for c in clips if c["ID"] not in avoid] or clips
        clip = first or min(pool, key=lambda c: (uses.get(c["ID"], 0), -dt.datetime.fromisoformat(
            c["ModTime"].replace("Z", "+00:00")).timestamp()))
        rot = cat_rotate(cat, clip["ID"])
        render(fetch(clip["ID"], clip["Name"]), h["id"], out, seconds, cover, music_i, rot)
        return clip, rot, None
    cands = ([first] if first else []) + [by_id[m["id"]] for m in
             agent.match(h["hook"], h["caption"], cat, set(by_id), uses, avoid, n=MAX_TRIES + 1)]
    if not cands:  # nothing usable in the catalog: behave like the no-agent path
        return produce(h, out, cover, music_i, seconds, clips, None, uses, avoid, first)
    tried, best = [], None
    for clip in cands:
        if clip["ID"] in tried or len(tried) >= MAX_TRIES:
            continue
        tried.append(clip["ID"])
        rot = cat_rotate(cat, clip["ID"])
        render(fetch(clip["ID"], clip["Name"]), h["id"], out, seconds, cover, music_i, rot)
        rv = agent.review(out, h["hook"])
        print(f"  review {clip['Name']}: {'PASS' if rv['passed'] else 'fail'} {rv['score']}/10 - {rv['fit']}"
              + (f" | {'; '.join(rv['issues'])}" if rv["issues"] else ""), flush=True)
        if best is None or rv["score"] > best[2]["score"]:
            best = (clip, rot, rv)
        if rv["passed"]:
            return clip, rot, rv
    clip, rot, rv = best
    if clip["ID"] != tried[-1]:  # the last render wasn't the best one: put the best back
        render(fetch(clip["ID"], clip["Name"]), h["id"], out, seconds, cover, music_i, rot)
    print(f"  no candidate passed; kept the best ({clip['Name']}, {rv['score']}/10)", flush=True)
    return clip, rot, rv


def cat_rotate(cat, clip_id):
    return (cat or {}).get(clip_id, {}).get("rotate_fix", 0)


def load_catalog(clips):
    """Describe any clip the agent hasn't seen yet (downloads it once, then deletes the local copy)."""
    if not agent.enabled():
        print("ANTHROPIC_API_KEY not set: footage agent off, using least-used clips", flush=True)
        return None
    def get(c):
        local = WORK / f"{c['ID']}{Path(c['Name']).suffix}"
        temp = not local.exists()
        return fetch(c["ID"], c["Name"]), temp
    return agent.catalog(clips, get)


def next_slots(queue, n, hour, minute):
    """Daily slots after the last listicle already queued at this time of day (or from tomorrow if today's slot is gone)."""
    now = dt.datetime.now(dt.timezone.utc)
    taken = [t for t in (dt.datetime.fromisoformat(i["not_before"].replace("Z", "+00:00"))
             for i in queue["items"] if i["id"].startswith("lst-") and i.get("status") == "queued")
             if (t.hour, t.minute) == (hour, minute)]  # each daily slot (17:00, 20:00...) fills its own days
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
    p.add_argument("--audio", default="Echo Sax - Caleb Arredondo",
                   help="Instagram library sound Matteo adds in the app ('' = burn in our own music and auto-post)")
    p.add_argument("--only", default="", help="with --rerender: comma-separated queue ids to rebuild")
    p.add_argument("--rerender", action="store_true",
                   help="re-render the queued, not-yet-approved listicles in place (same hook and day)")
    p.add_argument("--rematch", action="store_true",
                   help="with --rerender: let the footage agent pick the clip again from the whole folder")
    p.add_argument("--catalog-only", action="store_true", help="just describe new Drive clips")
    a = p.parse_args()
    WORK.mkdir(parents=True, exist_ok=True)
    if a.catalog_only:
        return load_catalog(list_clips())
    if a.rerender:
        return rerender(a.seconds, {x.strip() for x in a.only.split(',') if x.strip()}, a.rematch)

    hooks, state, queue = load(HOOKS, None), load(STATE, {"clip_uses": {}, "last_clip": None, "music_i": 0}), load(QUEUE, None)
    todo = [h for h in hooks["hooks"] if h.get("status") == "ready"][: a.count]
    if not todo:
        sys.exit("no 'ready' hooks left in production/listicles/hooks.json - ask Claude for a new batch")
    clips = list_clips()
    if not clips:
        sys.exit(f"no video clips in Drive folder {CLIPS_FOLDER}")
    slots = next_slots(queue, len(todo), *map(int, a.slot.split(":")))
    cat = load_catalog(clips)
    work = WORK

    for h, slot in zip(todo, slots):
        uses = state["clip_uses"]
        day = slot.strftime("%Y-%m-%d")
        asset = f"lst-{day}-{h['id']}.mp4"
        folder = ROOT / "production" / "listicles" / f"{day}-{h['id']}"
        folder.mkdir(parents=True, exist_ok=True)
        avoid = nearby_clips(queue, day) | ({state["last_clip"]} if state.get("last_clip") else set())
        clip, rot, rv = produce(h, work / asset, folder / "cover.jpg", None if a.audio else state["music_i"],
                                a.seconds, clips, cat, uses, avoid)
        (folder / "caption.txt").write_text(h["caption"].strip() + "\n", encoding="utf-8")

        run("gh", "release", "upload", "media", str(work / asset), "--clobber", "-R", REPO)
        run("rclone", "copyto", str(work / asset), f"gdrive:listicles/{asset}", "--drive-root-folder-id", OUT_FOLDER)

        qid = f"lst-{day}-{h['id']}"
        queue["items"].append({
            "id": qid, "reel": f"listicles/{day}-{h['id']}", "variant": "-", "hook": h["hook"],
            "archetype": h["archetype"], "format": h.get("format", "listicle"), "clip": f"{clip['Name']} ({clip['ID']})", "video_asset": asset,
            "caption_file": str((folder / "caption.txt").relative_to(ROOT)).replace("\\", "/"),
            "strategy": "MANUAL", "thumb_offset_ms": 500,
            "not_before": slot.strftime("%Y-%m-%dT%H:%M:%SZ"), "min_gap_hours": 2.5,
            "approved": False, "status": "queued", **({"rotate": rot} if rot else {}),
            **({"review": rv} if rv else {}),
            **({"app_audio": f"{a.audio} (add in the Instagram app)"} if a.audio else {})})
        h.update(status="rendered", clip=f"{clip['Name']} ({clip['ID']})", queue_id=qid,
                 rendered_at=dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%MZ"))
        uses[clip["ID"]] = uses.get(clip["ID"], 0) + 1
        state["last_clip"] = clip["ID"]
        state["music_i"] += 1
        save(HOOKS, hooks); save(STATE, state); save(QUEUE, queue)  # after each one: a crash keeps the finished ones
        print(f"{qid}: {h['hook']} | clip {clip['Name']} | posts {slot:%a %d %b %H:%M} UTC once approved", flush=True)


def rerender(seconds, only=(), rematch=False):
    """Rebuild queued, unapproved lst-* items. The agent reviews each; a failed review (or --rematch) re-picks the clip."""
    hooks, queue, state = load(HOOKS, None), load(QUEUE, None), load(STATE, {"clip_uses": {}})
    by_q = {h.get("queue_id"): h for h in hooks["hooks"]}
    items = [i for i in queue["items"] if i["id"].startswith("lst-") and not i.get("approved") and i["status"] == "queued"
             and (not only or i["id"] in only)]
    clips = list_clips()
    by_id = {c["ID"]: c for c in clips}
    cat = load_catalog(clips)
    for n, item in enumerate(items):
        h = by_q[item["id"]]
        cur_id = item["clip"].rsplit("(", 1)[1].rstrip(")")
        cur = by_id.get(cur_id) or {"ID": cur_id, "Name": item["clip"].split(" (")[0]}
        folder = ROOT / Path(item["caption_file"]).parent
        avoid = nearby_clips(queue, item["not_before"][:10], skip_id=item["id"]) | {cur_id}
        if cat is None:  # no agent: plain re-render, keep any manual rotate
            render(fetch(cur_id, cur["Name"]), h["id"], WORK / item["video_asset"], seconds, folder / "cover.jpg",
                   None if item.get("app_audio") else n, item.get("rotate", 0))
            clip, rot, rv = cur, item.get("rotate", 0), None
        else:
            # The current clip is reviewed first and only swapped if it fails; --rematch starts from scratch.
            clip, rot, rv = produce(h, WORK / item["video_asset"], folder / "cover.jpg",
                                    None if item.get("app_audio") else n, seconds, clips, cat,
                                    state["clip_uses"], avoid, None if rematch else cur)
        item["clip"] = f"{clip['Name']} ({clip['ID']})"
        item.pop("rotate", None)
        if rot:
            item["rotate"] = rot
        if rv:
            item["review"] = rv
        h["clip"] = item["clip"]
        save(QUEUE, queue); save(HOOKS, hooks)
        run("gh", "release", "upload", "media", str(WORK / item["video_asset"]), "--clobber", "-R", REPO)
        run("rclone", "copyto", str(WORK / item["video_asset"]), f"gdrive:listicles/{item['video_asset']}",
            "--drive-root-folder-id", OUT_FOLDER)
        print(f"{item['id']}: re-rendered on {clip['Name']}", flush=True)


if __name__ == "__main__":
    main()
