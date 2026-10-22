"""Daily listicle factory: turn the next hooks in production/listicles/hooks.json into rendered trial reels,
one per day, waiting in production/schedule/queue.json for Matteo's yes.

    python -P tools/listicle/factory.py --count 7          # run by the "Listicle factory" workflow

For each hook: the footage agent (footage_agent.py) picks the clip that best fits the hook out of every clip in
the Drive folder, the reel is rendered (render.py) and the agent reviews the finished video; a failed review moves
on to the next-best clip (up to MAX_TRIES). Without ANTHROPIC_API_KEY it falls back to the least-used clip. Then push the
video to the "media" release, copy it to Drive output/listicles/ for Matteo to watch, write the caption + cover
under production/listicles/<id>/, and add a queue item with approved=false on the next free daily slot.
Nothing posts until the item is approved (tools/instagram/approve.py) after Matteo's explicit yes.

Copies for the other platforms (Matteo 2026-10-22, after Facebook views fell to ~0):
  music copy     a listicle whose Instagram sound is attached in the app also gets <asset>-music.mp4, the same reel
                 with royalty-free music in the file, for YouTube and Threads (video_asset_music).
  --fb-pick      once a day: the best Instagram reel at 72 h (views vs the account median, then shares + saves)
                 that clears platforms.facebook.winners in crosspost.json becomes the day's Facebook reel (fb_pick);
                 a listicle gets its Facebook version first (render.offsite: list on screen, music, no READ
                 DESCRIPTION) as <asset>-fb.mp4 (video_asset_fb). The Cross-post workflow posts it in the Facebook slot.
Needs: rclone remote "gdrive" (secret RCLONE_CONF), gh CLI (GH_TOKEN), ffmpeg, Pillow.
"""
import argparse, datetime as dt, json, os, subprocess, sys
from zoneinfo import ZoneInfo
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from render import render, candidate_windows, offsite  # noqa: E402
import footage_agent as agent  # noqa: E402
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "style"))
from lab import assign as lab_assign  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import state as store  # noqa: E402  (live state: the reel queue)
import r2  # noqa: E402
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "crosspost"))
import captions  # noqa: E402
HOOKS = ROOT / "production" / "listicles" / "hooks.json"
STATE = ROOT / "production" / "listicles" / "state.json"
CLIPS_FOLDER = "1EkBaa-a9m1lX5KQZnmNXQNj-E8E8hCKk"   # Matteo's raw training clips (top level only)
OUT_FOLDER = "1bHwCLpkK2w9e9BN22dXWgQnn8_CLYpR2"     # Drive output; previews go in output/listicles/
VIDEO_EXT = (".mov", ".mp4", ".m4v")
MOMENT_SHEETS = ROOT / "production" / "listicles" / "moment-sheets"  # candidate 8 s moments per clip, graded by Claude
SHEETS = ROOT / "production" / "listicles" / "clip-sheets"   # 6-frame contact sheet per Drive clip, for Claude to look at
MAX_BYTES = 700 * 1024 * 1024   # skip the 1 GB+ sparring masters: slow to pull, and one 8 s window is enough
REPO = os.environ.get("GITHUB_REPOSITORY", "fightingmatteo-ux/matteofights")
WORK = ROOT / "media" / "listicles"
MAX_TRIES = 3


def load(p, default):
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else default


def save(p, data):
    p.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def load_queue():
    """{"items": [...]} from tools/state.py; save_queue() writes back only what this run changed."""
    items, before = store.snapshot("queue")
    return {"items": items, "_before": before}


def save_queue(queue):
    store.save_changed("queue", queue["items"], queue["_before"])


def run(*cmd):
    print("+", " ".join(cmd), flush=True)
    subprocess.run(cmd, check=True, cwd=ROOT)


def ship(path, drive=False):
    """A finished render to the media release and R2 (+ Drive output/listicles/ for Matteo to watch)."""
    run("gh", "release", "upload", "media", str(path), "--clobber", "-R", REPO)
    r2.upload_render(path)  # posting prefers R2: never leave an older copy there
    if drive:
        run("rclone", "copyto", str(path), f"gdrive:listicles/{path.name}", "--drive-root-folder-id", OUT_FOLDER)


def clip_of(item):
    """(clip dict, rotate) of a queued/posted listicle, from its "Name (ID)" clip field."""
    cid = item["clip"].rsplit("(", 1)[1].rstrip(")")
    return {"ID": cid, "Name": item["clip"].split(" (")[0]}, item.get("rotate", 0)  # rotate is stored when not 0


def music_copy(item, hook_id, music_i):
    """<asset>-music.mp4: the same reel with royalty-free music in the file, for YouTube and Threads (the Instagram
    file has no music when its sound is attached in the app)."""
    clip, rot = clip_of(item)
    out = WORK / item["video_asset"].replace(".mp4", "-music.mp4")
    render(fetch(clip["ID"], clip["Name"]), hook_id, out, 8.0, None, music_i, rot)
    ship(out)
    item["video_asset_music"] = out.name


def list_clips():
    out = subprocess.run(["rclone", "lsjson", "gdrive:", "--drive-root-folder-id", CLIPS_FOLDER, "--files-only"],
                         capture_output=True, text=True, check=True).stdout
    keep = [c for c in json.loads(out) if c["Name"].lower().endswith(VIDEO_EXT) and c.get("Size", 0) <= MAX_BYTES
            ]
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
        rot = cat_rotate(manual_catalog(), clip["ID"])
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


def manual_catalog():
    return load(agent.CATALOG, {})


def review_sheet(video, out):
    """Cover + 4 frames of the finished reel, committed so Claude can review it in the scheduled session."""
    d = agent._duration(video)
    agent.sheet(video, [0.5, d * 0.3, d * 0.5, d * 0.7, max(0.5, d - 0.6)], out)


def cat_rotate(cat, clip_id):
    return (cat or {}).get(clip_id, {}).get("rotate_fix", 0)


SHEET_VERSION = 2  # 2 = 6 frames per moment + pose check


def moment_sheet(path, out, seconds=8.5):
    """Rows A-H = the clip's busiest non-overlapping moments, 6 frames each across the 8 s, labelled with the start
    time and the pose check (technique.py: guard, strikes, stance, in frame; or why it's vetoed). Claude grades
    them against context/boxing-technique.md (moments.json); the render uses the best one."""
    from PIL import Image, ImageDraw
    import technique
    d = agent._duration(path)
    starts = candidate_windows(path, d, seconds, k=8)
    poses = {}
    for t in starts:
        try:
            poses[t] = technique.score(path, t, seconds)
        except Exception as e:  # pose is a helper; never block the sheet
            poses[t] = {"score": None, "veto": None, "error": str(e)[:80]}
    tw, th = 160, 284
    sheet = Image.new("RGB", (tw * 6 + 150, th * len(starts)), "black")
    draw = ImageDraw.Draw(sheet)
    for r, t in enumerate(starts):
        p = poses[t]
        label = (f"{'ABCDEFGH'[r]}  {t:.1f}s\n\npose {p.get('score')}\n" +
                 (f"VETO:\n{p['veto']}" if p.get("veto") else f"guard {p.get('guard')}\nstrikes {p.get('strikes')}\nstance {p.get('stance')}"))
        draw.text((8, r * th + 8), label, fill=(255, 80, 80) if p.get("veto") else (255, 255, 0))
        for k, off in enumerate([0.3 + (seconds - 0.6) * i / 5 for i in range(6)]):
            f = WORK / "_m.jpg"
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t + off:.2f}", "-i", str(path), "-frames:v", "1",
                            "-vf", f"scale={tw}:{th}:force_original_aspect_ratio=decrease,pad={tw}:{th}:(ow-iw)/2:(oh-ih)/2",
                            "-q:v", "5", str(f)], check=True)
            sheet.paste(Image.open(f).convert("RGB"), (150 + k * tw, r * th))
    sheet.save(out, "JPEG", quality=78)
    return {"ABCDEFGH"[r]: t for r, t in enumerate(starts)}, {"ABCDEFGH"[r]: poses[t] for r, t in enumerate(starts)}


def make_sheets(clips):
    """Per clip that doesn't have them yet: a 6-frame contact sheet (what the clip is) and a moment sheet (which
    8 s stretch looks best). Claude (scheduled session, Matteo's account) reads them, describes each clip in
    clips.json, grades the moments in moments.json and picks a clip per hook (hooks.json clip_id)."""
    SHEETS.mkdir(parents=True, exist_ok=True)
    MOMENT_SHEETS.mkdir(parents=True, exist_ok=True)
    idx_path, pose_path = MOMENT_SHEETS / "index.json", MOMENT_SHEETS / "pose.json"
    moments_idx, pose_idx = load(idx_path, {}), load(pose_path, {})
    if moments_idx.get("_version") != SHEET_VERSION:  # older sheets: make them again with the current layout
        for f in MOMENT_SHEETS.glob("*.jpg"):
            f.unlink()
        moments_idx, pose_idx = {"_version": SHEET_VERSION}, {}
    for c in clips:
        out = SHEETS / f"{c['ID']}.jpg"
        mout = MOMENT_SHEETS / f"{c['ID']}.jpg"
        if out.exists() and mout.exists():
            continue
        local = WORK / f"{c['ID']}{Path(c['Name']).suffix}"
        temp = not local.exists()
        try:
            path = fetch(c["ID"], c["Name"])
            d = agent._duration(path)
            if not out.exists():
                lo, hi = min(1.0, d * 0.1), max(d - 1.0, d * 0.9)
                agent.sheet(path, [lo + (hi - lo) * k / 5 for k in range(6)], out)
            if not mout.exists():
                moments_idx[c["ID"]], pose_idx[c["ID"]] = moment_sheet(path, mout)
                idx_path.write_text(json.dumps(moments_idx, indent=1) + "\n", encoding="utf-8")
                pose_path.write_text(json.dumps(pose_idx, indent=1) + "\n", encoding="utf-8")
            print(f"sheets: {c['Name']} ({d:.0f}s)", flush=True)
        except Exception as e:  # one broken clip must not stop the run
            print(f"sheet: {c['Name']}: {e}", flush=True)
        finally:
            if temp:
                local.unlink(missing_ok=True)
    live = {c["ID"]: c["Name"] for c in clips}
    (SHEETS / "index.json").write_text(json.dumps(live, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


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


TZ = ZoneInfo("America/New_York")  # slots are US Eastern evening: US prime time, India asleep (3-7am IST)


def next_slots(queue, n, hour, minute):
    """Daily slots (New York time, DST-safe) after the last listicle already queued at this local time of day."""
    now = dt.datetime.now(dt.timezone.utc)
    taken = []
    for i in queue["items"]:
        if i["id"].startswith("lst-") and i.get("status") == "queued":
            t = dt.datetime.fromisoformat(i["not_before"].replace("Z", "+00:00")).astimezone(TZ)
            if (t.hour, t.minute) == (hour, minute):  # each daily slot fills its own days
                taken.append(t.date())
    day = now.astimezone(TZ).date()
    if taken:
        day = max(max(taken) + dt.timedelta(days=1), day)
    slots = []
    while len(slots) < n:
        t = dt.datetime(day.year, day.month, day.day, hour, minute, tzinfo=TZ).astimezone(dt.timezone.utc)
        if t > now + dt.timedelta(hours=2):  # leave time for the yes
            slots.append(t)
        day += dt.timedelta(days=1)
    return slots


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--count", type=int, default=7)
    p.add_argument("--slot", default="18:30", help="daily post time, New York HH:MM")
    p.add_argument("--seconds", type=float, default=8.0)
    p.add_argument("--audio", default="",
                   help="Instagram library sound, 'Title - Artist' (e.g. 'Echo Sax End - Caleb Arredondo'): rendered "
                        "without music and the Post queue attaches the sound through the Audio API (audio.py); if the "
                        "API's library lacks it, Matteo adds it in the app. Default '' = royalty-free music in the file")
    p.add_argument("--only", default="", help="with --rerender: comma-separated queue ids to rebuild")
    p.add_argument("--sounds-only", action="store_true",
                   help="re-render queued listicles that carry app_audio (approved too) on the same clip, music removed")
    p.add_argument("--rerender", action="store_true",
                   help="re-render the queued, not-yet-approved listicles in place (same hook and day)")
    p.add_argument("--rematch", action="store_true",
                   help="with --rerender: let the footage agent pick the clip again from the whole folder")
    p.add_argument("--music-copies", action="store_true",
                   help="render the missing music copies (YouTube/Threads) of queued and recent listicles with app_audio")
    p.add_argument("--fb-pick", action="store_true",
                   help="pick today's Facebook reel from the Instagram numbers at 72 h and render its Facebook version")
    p.add_argument("--catalog-only", action="store_true", help="just describe new Drive clips (needs API key)")
    p.add_argument("--sheets-only", action="store_true", help="just make contact sheets for new Drive clips")
    a = p.parse_args()
    WORK.mkdir(parents=True, exist_ok=True)
    if a.catalog_only:
        return load_catalog(list_clips())
    if a.sheets_only:
        return make_sheets(list_clips())
    if a.music_copies:
        return music_copies()
    if a.fb_pick:
        return fb_pick()
    if a.rerender or a.sounds_only:
        return rerender(a.seconds, {x.strip() for x in a.only.split(',') if x.strip()}, a.rematch, a.sounds_only)

    hooks, state, queue = load(HOOKS, None), load(STATE, {"clip_uses": {}, "last_clip": None, "music_i": 0}), load_queue()
    # --audio "A - X; B - Y": rotate through the sounds, one per reel (Matteo 2026-10-20: proven sounds, not only one)
    sounds = [x.strip() for x in a.audio.split(";") if x.strip()]
    todo = [h for h in hooks["hooks"] if h.get("status") == "ready"][: a.count]
    if not todo:
        sys.exit("no 'ready' hooks left in production/listicles/hooks.json - ask Claude for a new batch")
    clips = list_clips()
    if not clips:
        sys.exit(f"no video clips in Drive folder {CLIPS_FOLDER}")
    slots = next_slots(queue, len(todo), *map(int, a.slot.split(":")))
    make_sheets(clips)
    cat = load_catalog(clips)
    work = WORK

    for h, slot in zip(todo, slots):
        uses = state["clip_uses"]
        day = slot.astimezone(TZ).strftime("%Y-%m-%d")
        asset = f"lst-{day}-{h['id']}.mp4"
        folder = ROOT / "production" / "listicles" / f"{day}-{h['id']}"
        folder.mkdir(parents=True, exist_ok=True)
        avoid = nearby_clips(queue, day) | ({state["last_clip"]} if state.get("last_clip") else set())
        sound = sounds[state.get("sound_i", 0) % len(sounds)] if sounds else ""
        test = lab_assign(h["id"])  # style lab A/B: render reads hooks.json, so the variant goes there first
        if test and test[0] == "hook_style":
            h["style"] = test[1]
            save(HOOKS, hooks)
        picked = {c["ID"]: c for c in clips}.get(h.get("clip_id"))
        if picked and cat is None:  # Claude chose this clip from the sheets: render it as chosen
            rot = cat_rotate(manual_catalog(), picked["ID"])
            render(fetch(picked["ID"], picked["Name"]), h["id"], work / asset, a.seconds, folder / "cover.jpg",
                   None if a.audio else state["music_i"], rot)
            clip, rv = picked, None
        else:
            clip, rot, rv = produce(h, work / asset, folder / "cover.jpg", None if a.audio else state["music_i"],
                                    a.seconds, clips, cat, uses, avoid, picked)
        review_sheet(work / asset, folder / "review.jpg")
        (folder / "caption.txt").write_text(h["caption"].strip() + "\n", encoding="utf-8")

        run("gh", "release", "upload", "media", str(work / asset), "--clobber", "-R", REPO)
        r2.upload_render(work / asset)  # posting prefers R2: never leave an older copy there
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
            **({"test": test[2]} if test else {}),
            **({"app_audio": f"{sound} (add in the Instagram app)"} if sound else {})})
        if sound:
            music_copy(queue["items"][-1], h["id"], state["music_i"])
        h.update(status="rendered", clip=f"{clip['Name']} ({clip['ID']})", queue_id=qid,
                 rendered_at=dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%MZ"))
        uses[clip["ID"]] = uses.get(clip["ID"], 0) + 1
        state["last_clip"] = clip["ID"]
        state["music_i"] += 1
        if sounds:
            state["sound_i"] = state.get("sound_i", 0) + 1
        save(HOOKS, hooks); save(STATE, state); save_queue(queue)  # after each one: a crash keeps the finished ones
        print(f"{qid}: {h['hook']} | clip {clip['Name']} | posts {slot.astimezone(TZ):%a %d %b %H:%M} New York once approved", flush=True)


def rerender(seconds, only=(), rematch=False, sounds_only=False):
    """Rebuild queued, unapproved lst-* items. The agent reviews each; a failed review (or --rematch) re-picks the clip.
    sounds_only: rebuild every queued lst-* item that has app_audio (approved or not) on its SAME clip without the
    baked-in music, so the Post queue attaches the Instagram sound (Matteo 2026-10-20: a sound on every listicle).
    Approval is kept: the picture is unchanged and the sound is what Matteo asked for."""
    hooks, queue, state = load(HOOKS, None), load_queue(), load(STATE, {"clip_uses": {}})
    by_q = {h.get("queue_id"): h for h in hooks["hooks"]}
    items = [i for i in queue["items"] if i["id"].startswith("lst-") and i["status"] == "queued"
             and (i.get("app_audio") if sounds_only else not i.get("approved"))
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
        if cat is None or sounds_only:  # no agent / sound swap only: plain re-render on the same clip, keep any rotate
            rot = item.get("rotate") or cat_rotate(manual_catalog(), cur_id)
            render(fetch(cur_id, cur["Name"]), h["id"], WORK / item["video_asset"], seconds, folder / "cover.jpg",
                   None if item.get("app_audio") else n, rot)
            clip, rv = cur, None
        else:
            # The current clip is reviewed first and only swapped if it fails; --rematch starts from scratch.
            clip, rot, rv = produce(h, WORK / item["video_asset"], folder / "cover.jpg",
                                    None if item.get("app_audio") else n, seconds, clips, cat,
                                    state["clip_uses"], avoid, None if rematch else cur)
        review_sheet(WORK / item["video_asset"], folder / "review.jpg")
        item["clip"] = f"{clip['Name']} ({clip['ID']})"
        item.pop("rotate", None)
        if rot:
            item["rotate"] = rot
        if rv:
            item["review"] = rv
        h["clip"] = item["clip"]
        run("gh", "release", "upload", "media", str(WORK / item["video_asset"]), "--clobber", "-R", REPO)
        r2.upload_render(WORK / item["video_asset"])  # a re-render must replace the R2 copy too
        run("rclone", "copyto", str(WORK / item["video_asset"]), f"gdrive:listicles/{item['video_asset']}",
            "--drive-root-folder-id", OUT_FOLDER)
        if item.get("app_audio"):
            music_copy(item, h["id"], n)
        item.pop("sound_pending", None)  # the music-free render is on the release: the Post queue may take it now
        save_queue(queue); save(HOOKS, hooks)
        print(f"{item['id']}: re-rendered on {clip['Name']}", flush=True)


def music_copies():
    """Backfill: music copies for listicles that rely on an in-app sound, still queued or posted in the last 3 days
    (older ones are past the cross-post lookback)."""
    hooks, queue = load(HOOKS, None), load_queue()
    by_q = {h.get("queue_id"): h for h in hooks["hooks"]}
    recent = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=3)).strftime("%Y-%m-%dT%H:%M:%SZ")
    todo = [i for i in queue["items"] if i["id"].startswith("lst-") and i.get("app_audio") and not i.get("video_asset_music")
            and i["id"] in by_q and (i.get("status") == "queued" or (i.get("posted_at") or "") >= recent)]
    for n, item in enumerate(todo):
        music_copy(item, by_q[item["id"]]["id"], n)
        save_queue(queue)  # after each one: a crash keeps the finished ones
        print(f"{item['id']}: music copy {item['video_asset_music']}", flush=True)


METRICS = ROOT / "production" / "control" / "metrics.json"      # Buzzfy numbers per media id (+ account median)
PLATFORMS = ROOT / "production" / "control" / "platforms.json"  # Instagram API numbers per queue id (stats.py)


def ig_numbers(item, metrics, platforms):
    """(views, shares + saves) on Instagram: Buzzfy's numbers when it has the reel, else the API's."""
    m = (metrics.get("reels") or {}).get(item.get("media_id") or "") or {}
    if m.get("views") is None:
        m = ((platforms.get("posts") or {}).get(item["id"]) or {}).get("instagram") or {}
    return m.get("views"), (m.get("shares") or 0) + (m.get("saves") or 0)


def fb_pick():
    """Today's Facebook reel: the best Instagram reel aged min_age_hours..max_age_days that isn't on Facebook yet and
    did at least min_vs_median x the account's median views. At most one pick per day; none when nothing clears the
    bar (a dud costs the Page reach). Matteo 2026-10-22: Facebook gets 1 reel a day, only Instagram winners."""
    cfg = (store.get("crosspost", "platforms") or {}).get("facebook") or {}
    rule = cfg.get("winners")
    if not cfg.get("enabled") or not rule:
        sys.exit("Facebook is off or not in winners mode (crosspost.json platforms.facebook.winners)")
    hooks, queue = load(HOOKS, None), load_queue()
    by_q = {h.get("queue_id"): h for h in hooks["hooks"]}
    xposted = store.get("crosspost", "posts") or {}
    metrics, platforms = load(METRICS, {}), load(PLATFORMS, {})
    median = metrics.get("median_views") or 0
    now = dt.datetime.now(dt.timezone.utc)
    iso = lambda t: t.strftime("%Y-%m-%dT%H:%M:%SZ")  # noqa: E731
    if any((i.get("fb_pick") or {}).get("at", "") >= iso(now - dt.timedelta(hours=20)) for i in queue["items"]):
        return print("fb-pick: already picked in the last 20 h")
    young, old = iso(now - dt.timedelta(hours=rule.get("min_age_hours", 72))), iso(now - dt.timedelta(days=rule.get("max_age_days", 7)))
    cands = []
    for i in queue["items"]:
        if (i.get("status") != "posted" or not (old <= (i.get("posted_at") or "") <= young) or i.get("fb_pick")
                or (i.get("posted_at") or "") < cfg.get("since", "") or ("crosspost_to" in i and "facebook" not in i["crosspost_to"])
                or (xposted.get(i["id"]) or {}).get("facebook", {}).get("status") == "posted"):
            continue
        views, ss = ig_numbers(i, metrics, platforms)
        if views:
            cands.append((views, ss * 1000 / views, i))
    cands.sort(key=lambda c: (c[0], c[1]), reverse=True)
    for views, ss_k, i in cands[:5]:
        print(f"  {i['id']}: {views} views ({views / median:.2f}x median), {ss_k:.1f} shares+saves /1k" if median else f"  {i['id']}: {views}")
    if not cands or (median and cands[0][0] < rule.get("min_vs_median", 1.0) * median):
        return print(f"fb-pick: nothing clears {rule.get('min_vs_median', 1.0)}x the {median} median views: no Facebook reel today")
    views, ss_k, item = cands[0]
    if item["id"].startswith("lst-"):
        h = by_q[item["id"]]
        cap = (ROOT / item["caption_file"]).read_text(encoding="utf-8")
        content = captions.slides(cap, item.get("hook", ""))
        if not content:
            sys.exit(f"{item['id']}: caption has no list, can't make its Facebook version")
        clip, rot = clip_of(item)
        out = WORK / item["video_asset"].replace(".mp4", "-fb.mp4")
        offsite(fetch(clip["ID"], clip["Name"]), h["id"], out, content[1], content[2], now.timetuple().tm_yday, rot)
        ship(out, drive=True)
        item["video_asset_fb"] = out.name
    else:  # talking head / own audio: its own file is already the Facebook version
        item["video_asset_fb"] = item["video_asset"]
    item["fb_pick"] = {"at": iso(now), "ig_views": views, "vs_median": round(views / median, 2) if median else None,
                       "shares_saves_per_1k": round(ss_k, 1)}
    save_queue(queue)
    print(f"fb-pick: {item['id']} ({views} Instagram views) -> {item['video_asset_fb']}", flush=True)


if __name__ == "__main__":
    main()
