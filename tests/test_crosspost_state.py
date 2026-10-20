import json
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools" / "crosspost"))
import crosspost  # noqa: E402


def test_save_state_keeps_platform_changes(tmp_path, monkeypatch):
    shutil.copytree(REPO / "production" / "schedule", tmp_path / "production" / "schedule")
    monkeypatch.setenv("STATE_ROOT", str(tmp_path))
    monkeypatch.delenv("STATE_BACKEND", raising=False)
    st = {"platforms": crosspost.store.get("crosspost", "platforms"), "posts": crosspost.store.get("crosspost", "posts")}
    st["platforms"]["youtube"]["last_slot"] = "2026-10-20T16:30:00Z"
    st["posts"].setdefault("new-reel", {})["youtube"] = {"status": "posted"}
    crosspost.save_state(st)
    saved = json.loads((tmp_path / "production" / "schedule" / "crosspost.json").read_text(encoding="utf-8"))
    assert saved["platforms"]["youtube"]["last_slot"] == "2026-10-20T16:30:00Z"
    assert saved["posts"]["new-reel"]["youtube"] == {"status": "posted"}
    assert "_how" in saved
