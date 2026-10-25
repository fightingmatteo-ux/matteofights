#!/usr/bin/env python3
"""Write tools/ticker/schedules.json from the workflow files' `on.schedule` crons.

The ticker fires these on the Modal backup when GitHub can't run them, so the times must be the workflow files'
own. Never edit schedules.json by hand: run this (tools/ops/deploy.sh does, and tools/ops/budget.py warns when the
file no longer matches the workflows).

    python3 -P tools/ticker/gen_schedules.py          # write
    python3 -P tools/ticker/gen_schedules.py --check  # exit 1 if stale
"""
import json
import sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent / "schedules.json"
GITHUB_ONLY = {"edit-worker.yml", "talking-points.yml"}  # claude-code-action: can't run on Modal


def build():
    out = {}
    for p in sorted((REPO / ".github" / "workflows").glob("*.yml")):
        if p.name in GITHUB_ONLY:
            continue
        wf = yaml.safe_load(p.read_text(encoding="utf-8"))
        on = wf.get("on", wf.get(True)) or {}
        crons = [s["cron"] for s in (on.get("schedule") or [])] if isinstance(on, dict) else []
        if crons:
            out[p.name] = crons
    return out


if __name__ == "__main__":
    text = json.dumps(build(), indent=2) + "\n"
    if "--check" in sys.argv:
        stale = not OUT.exists() or OUT.read_text() != text
        print("schedules.json is stale: run tools/ticker/gen_schedules.py" if stale else "schedules.json up to date")
        sys.exit(1 if stale else 0)
    OUT.write_text(text)
    print(f"wrote {OUT.relative_to(REPO)}: {sum(len(v) for v in json.loads(text).values())} crons")
