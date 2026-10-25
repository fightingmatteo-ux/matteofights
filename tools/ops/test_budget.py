"""Budget watcher logic on SQLite (D1's engine).  Run: python3 -P tools/ops/test_budget.py"""
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import state  # noqa: E402
import budget  # noqa: E402

db = sqlite3.connect(":memory:")
db.row_factory = sqlite3.Row
db.executescript((Path(__file__).resolve().parents[1] / "cloud" / "schema.sql").read_text())
state._d1 = lambda sql, p: [dict(r) for r in db.execute(sql, p).fetchall()] or (db.commit() or [])
sent = []
budget.telegram = lambda text: sent.append(text)
budget.DRY = False
budget.r2_gb = lambda: (2.0, {"renders": 1.9})
budget.pages_deploys = lambda s, m: 40
budget.ticker_age_min = lambda: 3


def run(gh_min, modal_usd):
    budget.github_minutes = lambda s: (gh_min, "test")
    budget.modal_usd = lambda m: (modal_usd, 10)
    budget.main()
    return state.backend("d1").get("ops", "budget")


b = run(1000, 3)
assert b["github_pct"] == 33 and b["modal_mode"] == "normal" and not sent, (b, sent)
b = run(2200, 3)                       # 73 % -> one 70 % alert
assert len(sent) == 1 and "GitHub" in sent[0] and "73%" in sent[0]
b = run(2300, 3)                       # still 70s: no repeat
assert len(sent) == 1
b = run(2600, 3)                       # 87 % -> the 85 % alert (the ticker switches on this number)
assert len(sent) == 2 and b["github_pct"] == 87
b = run(2600, 23)                      # Modal 77 % -> essential-only mode + its alert
assert b["modal_mode"] == "essential" and "Modal" in sent[-1]
b = run(2600, 31)                      # Modal 103 % -> off
assert b["modal_mode"] == "off"
budget.ticker_age_min = lambda: 50     # ticker dead -> one problem alert, not repeated
run(2600, 31); run(2600, 31)
assert sum("ticker" in s for s in sent) == 1
print("ok budget:", len(sent), "alerts")
