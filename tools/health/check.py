"""Scripted health check (no AI). Run by the "Health check" workflow every 2 hours.

    python3 -P tools/health/check.py          # writes problems to D1 health/latest + Telegram notes (once a day each)

Looks at: reel queue (stuck mid-post, failed, missed its slot), cloud render jobs (failed in the last day, stuck),
GitHub workflow runs (latest run of a workflow failed in the last 6 h). Login expiry is Platform stats' job
(tools/crosspost/stats.py). Never fixes posting state itself: a stuck "posting" item may already be on Instagram,
so it becomes a note with what to check.
"""
import datetime as dt
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import state  # noqa: E402

NOTES = ROOT / "production" / "control" / "notes.json"
SEEN = ROOT / "production" / "control" / "health_seen.json"


def _t(s):
    return dt.datetime.fromisoformat(s.replace("Z", "+00:00")) if s else None


def _ago(now, s, hours):
    t = _t(s)
    return t is not None and now - t > dt.timedelta(hours=hours)


def queue_problems(items, now):
    out = []
    for i in items:
        if i.get("status") == "posting" and (_ago(now, i.get("posting_since"), 2) or
                                             (not i.get("posting_since") and _ago(now, i.get("not_before"), 3))):
            out.append({"key": f"queue:{i['id']}:posting", "text": f"⚠️ {i['id']} has been 'posting' for over 2 h. "
                        "Check Instagram: if it is up, set status posted; if not, set it back to queued."})
        elif i.get("status") == "failed":
            out.append({"key": f"queue:{i['id']}:failed",
                        "text": f"⚠️ {i['id']} failed to post: {(i.get('error') or '')[:200]}"})
        elif (i.get("approved") is True and i.get("status") == "queued" and i.get("audio_status") != "manual"
              and _ago(now, i.get("not_before"), 3)):
            out.append({"key": f"queue:{i['id']}:missed",
                        "text": f"⏰ {i['id']} was due {i['not_before']} and still hasn't posted."})
    return out


def job_problems(jobs, now):
    out = []
    for j in jobs:
        if j.get("status") == "failed" and not _ago(now, j.get("finished_at"), 24):
            out.append({"key": f"job:{j['id']}:failed",
                        "text": f"⚠️ Cloud render {j['id']} failed: {(j.get('error') or '')[-200:]}"})
        elif j.get("status") in ("queued", "rendering") and _ago(now, j.get("started_at") or j.get("submitted_at"), 2.25):
            out.append({"key": f"job:{j['id']}:stuck", "text": f"⚠️ Cloud render {j['id']} has had no result for over 2 h."})
    return out


def run_problems(runs, now):
    latest = {}
    for r in sorted(runs, key=lambda r: r["createdAt"]):
        latest[r["workflowName"]] = r
    return [{"key": f"run:{name}", "text": f"⚠️ Workflow '{name}' failed: {r.get('url', '')}"}
            for name, r in sorted(latest.items())
            if r.get("conclusion") == "failure" and not _ago(now, r["createdAt"], 6)]


def new_notes(problems, seen, now):
    """Notes for problems not reported in the last 24 h; updates `seen` (key -> last reported)."""
    out = []
    for p in problems:
        if _ago(now, seen.get(p["key"]), 24) or p["key"] not in seen:
            seen[p["key"]] = now.strftime("%Y-%m-%dT%H:%M:%SZ")
            out.append({"id": f"health-{p['key']}-{now:%Y%m%d%H}", "text": p["text"]})
    return out


def recent_runs():
    try:
        r = subprocess.run(["gh", "run", "list", "--limit", "60", "--json", "workflowName,conclusion,createdAt,url"],
                           capture_output=True, text=True, timeout=60, cwd=ROOT)
        return json.loads(r.stdout) if r.returncode == 0 else []
    except (OSError, subprocess.TimeoutExpired, json.JSONDecodeError):
        return []


def _load(p, default):
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else default


def _save(p, data):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main():
    now = dt.datetime.now(dt.timezone.utc)
    problems = queue_problems(state.all("queue"), now) + run_problems(recent_runs(), now)
    try:  # jobs only live in D1
        problems += job_problems(state.backend("d1").all("job"), now)
    except Exception as e:  # noqa: BLE001 - no D1 token here: skip jobs, still report the rest
        print(f"jobs skipped: {e}")
    seen = _load(SEEN, {})
    notes = new_notes(problems, seen, now)
    if notes:
        _save(NOTES, (_load(NOTES, []) + notes)[-200:])
    _save(SEEN, {k: v for k, v in seen.items() if not _ago(now, v, 72)})
    try:
        state.backend("d1").put("health", "latest", {"at": now.strftime("%Y-%m-%dT%H:%M:%SZ"), "problems": problems})
    except Exception as e:  # noqa: BLE001
        print(f"health doc not written to D1: {e}")
    print(f"{len(problems)} problem(s), {len(notes)} new note(s)")
    for p in problems:
        print(" -", p["key"])


if __name__ == "__main__":
    main()
