import json
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools" / "instagram"))
import run_queue  # noqa: E402
import state  # noqa: E402

CAPTION = "production/reels/2026-10-14-freeze-in-sparring/caption-A.txt"


def item(id, **kw):
    return dict(dict(id=id, video_asset=f"{id}.mp4", caption_file=CAPTION, not_before="2026-01-01T00:00:00Z",
                     approved=True, status="queued"), **kw)


@pytest.fixture
def q(tmp_path, monkeypatch):
    path = tmp_path / "production" / "schedule" / "queue.json"
    path.parent.mkdir(parents=True)
    monkeypatch.setenv("STATE_ROOT", str(tmp_path))
    monkeypatch.delenv("STATE_BACKEND", raising=False)
    monkeypatch.setenv("IG_ACCESS_TOKEN", "x")
    monkeypatch.setattr(run_queue, "recent_posts", lambda: [])
    calls = []

    def fake_run(cmd, **kw):
        calls.append(cmd)
        return subprocess.CompletedProcess(cmd, 0, "media id 123 https://instagram.com/reel/x\n", "")

    monkeypatch.setattr(run_queue.subprocess, "run", fake_run)

    def write(*items):
        path.write_text(json.dumps({"_how": "x", "items": list(items)}), encoding="utf-8")

    return write, calls


def test_skips_unapproved_and_not_due(q):
    write, calls = q
    write(item("a", approved=False), dict(item("b"), not_before="2999-01-01T00:00:00Z"))
    run_queue.main()
    assert calls == []


def test_posts_due_item(q):
    write, calls = q
    write(item("a"))
    with pytest.raises(SystemExit) as e:
        run_queue.main()
    assert e.value.code == 0 and len(calls) == 1
    got = state.get("queue", "a")
    assert got["status"] == "posted" and got["media_id"] == "123"


def test_marks_posting_before_api_call(q, monkeypatch):
    write, calls = q
    write(item("a"))
    real_patch = state.patch

    def flaky_patch(kind, id, fields):
        if fields.get("status") == "posted":
            raise RuntimeError("state write failed")
        real_patch(kind, id, fields)

    monkeypatch.setattr(state, "patch", flaky_patch)
    with pytest.raises(RuntimeError):
        run_queue.main()
    assert len(calls) == 1
    assert state.get("queue", "a")["status"] == "posting"
    run_queue.main()  # nothing due now
    assert len(calls) == 1


def test_posting_item_is_never_picked(q):
    write, calls = q
    write(item("a", status="posting"))
    run_queue.main()
    assert calls == []
