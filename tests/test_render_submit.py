import sys
import tarfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools" / "render"))
import submit  # noqa: E402

R = "production/reels/x/assets/media/"


def test_keep_drops_other_variants_and_rebuilt_broll():
    assert submit.keep(R + "aroll_B.mp4", "B") and submit.keep(R + "fg_B_full.webm", "B")
    assert not submit.keep(R + "aroll_A.mp4", "B") and not submit.keep(R + "fg_C_full.webm", "B")
    assert not submit.keep(R + "b_sweep.mp4", "B")
    assert not submit.keep("production/reels/x/node_modules/a.js", "B")
    assert submit.keep(R + "bed.mp3", "B")


def test_bundle_writes_shell_scripts_with_lf(tmp_path, monkeypatch):
    reel = tmp_path / "production" / "reels" / "x"
    reel.mkdir(parents=True)
    (reel / "make.sh").write_bytes(b"#!/bin/bash\r\necho hi\r\n")
    (tmp_path / "production" / "editing" / "reel-kit").mkdir(parents=True)
    monkeypatch.setattr(submit, "REPO", tmp_path)
    out = tmp_path / "b.tar.gz"
    submit.bundle("production/reels/x", "B", [], out)
    with tarfile.open(out) as t:
        assert t.extractfile("production/reels/x/make.sh").read() == b"#!/bin/bash\necho hi\n"
