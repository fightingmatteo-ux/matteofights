import datetime as dt
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools" / "health"))
import check  # noqa: E402

NOW = dt.datetime(2026, 10, 20, 12, 0, tzinfo=dt.timezone.utc)
iso = lambda h: (NOW - dt.timedelta(hours=h)).strftime("%Y-%m-%dT%H:%M:%SZ")


def keys(problems):
    return sorted(p["key"] for p in problems)


def test_queue_problems():
    items = [
        {"id": "ok", "approved": True, "status": "queued", "not_before": iso(-2)},
        {"id": "stuck", "approved": True, "status": "posting", "not_before": iso(5), "posting_since": iso(3)},
        {"id": "late", "approved": True, "status": "queued", "not_before": iso(4)},
        {"id": "manual", "approved": True, "status": "queued", "not_before": iso(4), "audio_status": "manual"},
        {"id": "broke", "approved": True, "status": "failed", "error": "x", "not_before": iso(1)},
        {"id": "unapproved-late", "approved": False, "status": "queued", "not_before": iso(9)},
    ]
    assert keys(check.queue_problems(items, NOW)) == ["queue:broke:failed", "queue:late:missed", "queue:stuck:posting"]


def test_job_problems():
    jobs = [{"id": "a", "status": "done"}, {"id": "b", "status": "failed", "error": "boom", "finished_at": iso(2)},
            {"id": "old", "status": "failed", "error": "x", "finished_at": iso(40)},
            {"id": "c", "status": "rendering", "started_at": iso(3)}]
    assert keys(check.job_problems(jobs, NOW)) == ["job:b:failed", "job:c:stuck"]


def test_run_problems_only_recent_failures_latest_per_workflow():
    runs = [{"workflowName": "Post queue", "conclusion": "failure", "createdAt": iso(1), "url": "u1"},
            {"workflowName": "Post queue", "conclusion": "success", "createdAt": iso(0.5), "url": "u2"},
            {"workflowName": "Cross-post", "conclusion": "failure", "createdAt": iso(1), "url": "u3"},
            {"workflowName": "Old", "conclusion": "failure", "createdAt": iso(30), "url": "u4"}]
    assert keys(check.run_problems(runs, NOW)) == ["run:Cross-post"]


def test_new_notes_are_sent_once_per_day():
    problems = [{"key": "queue:x:failed", "text": "t"}]
    seen = {}
    first = check.new_notes(problems, seen, NOW)
    assert len(first) == 1 and "t" in first[0]["text"]
    assert check.new_notes(problems, seen, NOW + dt.timedelta(hours=2)) == []
    assert len(check.new_notes(problems, seen, NOW + dt.timedelta(hours=25))) == 1
