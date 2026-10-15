"""Build the control center's data: control-site/public/data.json (+ cover images).

Runs as the Cloudflare Pages build command on every push, so the site always shows the repo's current state:
    python3 tools/control/build_data.py
Sources: production/schedule/queue.json, production/listicles/{hooks,clips}.json, production/control/*.json
(metrics.json is written by Claude's daily check from Buzzfy).
"""
import datetime as dt, json, shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "control-site" / "public"
CTL = ROOT / "production" / "control"


def load(p, default):
    p = Path(p)
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else default


def main():
    queue = load(ROOT / "production/schedule/queue.json", {"items": []})["items"]
    hooks = load(ROOT / "production/listicles/hooks.json", {"hooks": []})["hooks"]
    clips = load(ROOT / "production/listicles/clips.json", {})
    live = load(ROOT / "production/listicles/clip-sheets/index.json", {})
    metrics = load(CTL / "metrics.json", {})
    per = metrics.get("reels", {})
    hook_fmt = {h.get("queue_id"): h for h in hooks}

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
        if label and i.get("variant"):
            label = f"{i['variant']}: {label}"
        reels.append({
            "id": i["id"], "hook": label or i.get("reel", i["id"]),
            "format": i.get("format") or ("talking head" if not i["id"].startswith("lst-") else "listicle"),
            "time": i.get("not_before"), "state": state, "cover": cover,
            "clip": (i.get("clip") or "").split(" (")[0], "review": i.get("review"),
            "permalink": i.get("permalink"), "posted_at": i.get("posted_at"), "error": i.get("error"),
            "metrics": m,
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
        "questions": load(CTL / "questions.json", []),
        "ideas": load(CTL / "ideas.json", [])[-50:],
        "log": load(CTL / "log.json", [])[-60:],
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
