import datetime as dt
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools" / "edit"))
import requests_cli as rq  # noqa: E402
import state  # noqa: E402


@pytest.fixture
def be(tmp_path, monkeypatch):
    monkeypatch.setenv("STATE_ROOT", str(tmp_path))
    fb = state.backend("file")
    monkeypatch.setattr(rq, "db", lambda: fb)
    return fb


def test_open_work_lists_uploads_and_requests_oldest_first(be):
    be.put("upload", "u2", {"status": "uploaded", "at": "2026-10-20T10:00:00Z", "name": "b.mov"})
    be.put("upload", "u1", {"status": "uploaded", "at": "2026-10-20T09:00:00Z", "name": "a.mov"})
    be.put("upload", "u0", {"status": "done", "at": "2026-10-19T09:00:00Z"})
    be.put("request", "r1", {"status": "open", "at": "2026-10-20T09:30:00Z", "text": "louder music"})
    assert [w["id"] for w in rq.open_work()] == ["u1", "r1", "u2"]


def test_budget_caps_runs_per_day(be):
    day = dt.date(2026, 10, 20)
    assert [rq.take_budget(3, day) for _ in range(4)] == [True, True, True, False]
    assert rq.take_budget(3, day + dt.timedelta(days=1)) is True


def test_add_talking_point_and_finish(be):
    tp = rq.add_talking_point("Why small fighters should love the reset", ["Hook A", "Hook B", "Hook C"],
                              ["point 1", "point 2"], source="https://instagram.com/reel/x")
    got = be.get("talking_point", tp)
    assert got["status"] == "new" and got["hooks"][0] == "Hook A"
    rq.finish("talking_point", tp, "filmed")
    assert be.get("talking_point", tp)["status"] == "filmed"
