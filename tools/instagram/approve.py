"""Mark queue items approved after Matteo's explicit yes to their previews, then commit + push.

    python -P tools/instagram/approve.py freeze-A freeze-B --note "yes in chat 2026-10-15 20:10"

Only approves items that exist and are still queued; prints exactly what it changed.
"""
import argparse, datetime as dt, os, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
QUEUE = ROOT / "production" / "schedule" / "queue.json"
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import state as store  # noqa: E402  (live state: the reel queue)

p = argparse.ArgumentParser()
p.add_argument("ids", nargs="+")
p.add_argument("--note", required=True, help="when/where Matteo said yes")
a = p.parse_args()

subprocess.run(["git", "pull", "--rebase", "-q"], cwd=ROOT, check=True)
items = {i["id"]: i for i in store.all("queue")}
missing = [i for i in a.ids if i not in items or items[i].get("status") != "queued"]
if missing:
    raise SystemExit(f"not in the queue or not queued: {', '.join(missing)}")
stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%MZ")
for i in a.ids:
    store.patch("queue", i, dict(approved=True, approved_note=f"Matteo: {a.note} (recorded {stamp})"))
    print(f"approved {i}: {items[i]['video_asset']}, not before {items[i]['not_before']}")
if store.configured() != "file":
    raise SystemExit(0)  # D1 is the truth: nothing to commit
subprocess.run(["git", "add", str(QUEUE)], cwd=ROOT, check=True)
subprocess.run(["git", "commit", "-qm", f"queue: approve {', '.join(a.ids)} ({a.note})\n\n"
                "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"], cwd=ROOT, check=True)
subprocess.run(["git", "push", "-q"], cwd=ROOT, check=True)
