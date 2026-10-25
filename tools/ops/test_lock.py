"""Lease semantics on SQLite (the engine behind D1).  Run: python3 -P tools/ops/test_lock.py"""
import os
import sqlite3
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import state  # noqa: E402
import lock  # noqa: E402

db = sqlite3.connect(":memory:")
db.row_factory = sqlite3.Row
db.executescript((Path(__file__).resolve().parents[1] / "cloud" / "schema.sql").read_text())


def fake_d1(sql, params):
    cur = db.execute(sql, params)
    db.commit()
    return [dict(r) for r in cur.fetchall()]


state._d1 = fake_d1
for k in ("GITHUB_OUTPUT", "GITHUB_ENV", "OPS_LOCK_OWNER"):
    os.environ.pop(k, None)
got = []
lock._out = lambda go: got.append(go)


def as_runner(name, run_id):
    os.environ["OPS_RUNNER"], os.environ["GITHUB_RUN_ID"] = name, run_id
    os.environ.pop("OPS_LOCK_OWNER", None)


as_runner("github", "1"); lock.acquire("post-queue")
as_runner("modal", "2"); lock.acquire("post-queue")
assert got == [True, False], got                     # the second runner is refused
lock.release("post-queue")                           # modal can't free github's lease
as_runner("modal", "3"); lock.acquire("post-queue")
assert got[-1] is False
as_runner("github", "1"); lock.release("post-queue")  # the holder frees it
as_runner("modal", "4"); lock.acquire("post-queue")
assert got[-1] is True
db.execute("UPDATE docs SET data = json_set(data, '$.until', ?) WHERE id = 'post-queue'", [int(time.time()) - 1])
as_runner("github", "5"); lock.acquire("post-queue")  # an expired lease (crashed run) can be taken over
assert got[-1] is True
as_runner("github", "6"); lock.acquire("crosspost")   # different jobs don't block each other
assert got[-1] is True
print("ok lock", got)
