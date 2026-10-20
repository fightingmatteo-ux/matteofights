import shutil
import sqlite3
from pathlib import Path

import pytest

import state
import state_mirror

REPO = Path(__file__).resolve().parent.parent


@pytest.fixture
def env(tmp_path, monkeypatch):
    shutil.copytree(REPO / "production" / "schedule", tmp_path / "production" / "schedule")
    monkeypatch.setenv("STATE_ROOT", str(tmp_path))
    db = sqlite3.connect(":memory:")
    db.row_factory = sqlite3.Row
    db.executescript((REPO / "tools" / "cloud" / "schema.sql").read_text(encoding="utf-8"))

    def run(sql, params):
        rows = db.execute(sql, params).fetchall()
        db.commit()
        return [dict(r) for r in rows]

    monkeypatch.setattr(state, "_d1", run)
    return tmp_path


def test_push_then_compare_clean(env, capsys):
    state.backend("file").put("job", "j1", {"status": "done"})
    assert state_mirror.main(["push"]) == 0
    assert state_mirror.main(["compare"]) == 0
    d1 = state.backend("d1")
    assert len(d1.all("queue")) == len(state.backend("file").all("queue"))
    assert d1.get("job", "j1") == {"status": "done"}


def test_compare_reports_diff(env, capsys):
    state_mirror.main(["push"])
    first = state.backend("file").all("queue")[0]["id"]
    state.backend("d1").patch("queue", first, {"status": "changed"})
    state.backend("d1").put("queue", "only-in-d1", {"id": "only-in-d1"})
    assert state_mirror.main(["compare"]) == 1
    out = capsys.readouterr().out
    assert f"queue/{first}" in out and "queue/only-in-d1" in out


def test_push_removes_ids_gone_from_files(env):
    state_mirror.main(["push"])
    state.backend("d1").put("queue", "stale", {"id": "stale"})
    state_mirror.main(["push"])
    assert state.backend("d1").get("queue", "stale") is None


def test_pull_writes_d1_into_files_only_in_d1_mode(env, monkeypatch):
    state_mirror.main(["push"])
    first = state.backend("file").all("queue")[0]["id"]
    state.backend("d1").patch("queue", first, {"status": "from-d1"})
    monkeypatch.setattr(state, "configured", lambda: "file")
    assert state_mirror.main(["pull"]) == 0  # file mode: files are the truth, nothing pulled
    assert state.backend("file").get("queue", first)["status"] != "from-d1"
    monkeypatch.setattr(state, "configured", lambda: "d1")
    assert state_mirror.main(["push"]) == 0  # d1 mode: push refuses to overwrite the truth
    assert state.backend("d1").get("queue", first)["status"] == "from-d1"
    assert state_mirror.main(["pull"]) == 0
    assert state.backend("file").get("queue", first)["status"] == "from-d1"
    assert state_mirror.main(["compare"]) == 0
