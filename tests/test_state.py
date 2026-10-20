import json
import shutil
import sqlite3
from pathlib import Path

import pytest

import state

REPO = Path(__file__).resolve().parent.parent
CAPTION = "Some people train for fun. 🥊 มวยไทย “quotes”"


@pytest.fixture
def root(tmp_path, monkeypatch):
    shutil.copytree(REPO / "production" / "schedule", tmp_path / "production" / "schedule")
    monkeypatch.setenv("STATE_ROOT", str(tmp_path))
    return tmp_path


@pytest.fixture
def fake_d1(monkeypatch):
    db = sqlite3.connect(":memory:")
    db.row_factory = sqlite3.Row
    db.executescript((REPO / "tools" / "cloud" / "schema.sql").read_text(encoding="utf-8"))

    def run(sql, params):
        rows = db.execute(sql, params).fetchall()
        db.commit()
        return [dict(r) for r in rows]

    monkeypatch.setattr(state, "_d1", run)
    return db


@pytest.fixture(params=["file", "d1"])
def be(request, root):
    if request.param == "d1":
        request.getfixturevalue("fake_d1")
    return state.backend(request.param)


def test_file_roundtrip_queue_keeps_shape(root):
    path = root / "production" / "schedule" / "queue.json"
    before = json.loads(path.read_text(encoding="utf-8"))
    b = state.backend("file")
    first = before["items"][0]
    b.put("queue", first["id"], dict(first, note="x"))
    after = json.loads(path.read_text(encoding="utf-8"))
    assert after["_how"] == before["_how"]
    assert [i["id"] for i in after["items"]] == [i["id"] for i in before["items"]]
    assert after["items"][0]["note"] == "x"
    assert after["items"][1:] == before["items"][1:]
    assert path.read_text(encoding="utf-8").endswith("}\n")


def test_file_crosspost_keeps_shape(root):
    path = root / "production" / "schedule" / "crosspost.json"
    before = path.read_text(encoding="utf-8")
    b = state.backend("file")
    b.put("crosspost", "posts", b.get("crosspost", "posts"))
    b.put("crosspost", "_how", b.get("crosspost", "_how"))
    assert path.read_text(encoding="utf-8") == before


def test_patch_merges_fields(be):
    be.patch("queue", "x", {"status": "posted"})
    be.patch("queue", "x", {"approved": True})
    got = be.get("queue", "x")
    assert got["status"] == "posted" and got["approved"] is True


def test_patch_merges_nested(be):
    be.put("crosspost", "zz", {"facebook": {"status": "posted"}})
    be.patch("crosspost", "zz", {"youtube": {"status": "queued"}, "facebook": {"id": "1"}})
    assert be.get("crosspost", "zz") == {"facebook": {"status": "posted", "id": "1"}, "youtube": {"status": "queued"}}


def test_unicode_roundtrip(be):
    be.put("queue", "u", {"id": "u", "caption": CAPTION})
    assert be.get("queue", "u")["caption"] == CAPTION


def test_get_missing_returns_none(be):
    assert be.get("queue", "does-not-exist") is None
    assert be.get("job", "nope") is None


def test_all_sorted_by_id(be):
    for i in ["b", "a", "c"]:
        be.put("job", i, {"n": i})
    assert [d["id"] for d in be.all("job")] == ["a", "b", "c"]
    assert be.all("job")[0]["n"] == "a"


def test_delete(be):
    be.put("job", "d", {"n": 1})
    be.delete("job", "d")
    assert be.get("job", "d") is None


def test_module_functions_use_env_backend(root, monkeypatch):
    monkeypatch.delenv("STATE_BACKEND", raising=False)
    state.put("job", "m", {"n": 1})
    assert json.loads((root / "production" / "state" / "job.json").read_text(encoding="utf-8")) == {"m": {"n": 1}}
    assert state.get("job", "m") == {"n": 1}
