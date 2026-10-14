"""Mark queue items approved after Matteo's explicit yes to their previews, then commit + push.

    python -P tools/instagram/approve.py freeze-A freeze-B --note "yes in chat 2026-10-15 20:10"

Only approves items that exist and are still queued; prints exactly what it changed.
"""
import argparse, datetime as dt, json, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
QUEUE = ROOT / "production" / "schedule" / "queue.json"

p = argparse.ArgumentParser()
p.add_argument("ids", nargs="+")
p.add_argument("--note", required=True, help="when/where Matteo said yes")
a = p.parse_args()

subprocess.run(["git", "pull", "--rebase", "-q"], cwd=ROOT, check=True)
q = json.loads(QUEUE.read_text(encoding="utf-8"))
items = {i["id"]: i for i in q["items"]}
missing = [i for i in a.ids if i not in items or items[i].get("status") != "queued"]
if missing:
    raise SystemExit(f"not in the queue or not queued: {', '.join(missing)}")
stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%MZ")
for i in a.ids:
    items[i].update(approved=True, approved_note=f"Matteo: {a.note} (recorded {stamp})")
    print(f"approved {i}: {items[i]['video_asset']}, not before {items[i]['not_before']}")
QUEUE.write_text(json.dumps(q, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
subprocess.run(["git", "add", str(QUEUE)], cwd=ROOT, check=True)
subprocess.run(["git", "commit", "-qm", f"queue: approve {', '.join(a.ids)} ({a.note})\n\n"
                "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"], cwd=ROOT, check=True)
subprocess.run(["git", "push", "-q"], cwd=ROOT, check=True)
