import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools" / "crosspost"))
import crosspost  # noqa: E402


def test_stats_only_uses_names_crosspost_has():
    used = set(re.findall(r"\bxp\.(\w+)", (REPO / "tools" / "crosspost" / "stats.py").read_text(encoding="utf-8")))
    assert sorted(n for n in used if not hasattr(crosspost, n)) == []
