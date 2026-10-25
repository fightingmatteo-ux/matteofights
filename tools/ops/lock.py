#!/usr/bin/env python3
"""A lease in D1 so a job never runs on two runners at once (GitHub Actions and the Modal backup).

Used as the first and last step of the posting workflows (post-queue.yml, crosspost.yml), so it works the same
on both runners because both run those same files:

    python3 -P tools/ops/lock.py acquire post-queue     # writes go=yes|no to $GITHUB_OUTPUT (and prints it)
    python3 -P tools/ops/lock.py release post-queue     # only frees the lease if we hold it

The lease is one D1 row (kind "lock", id = name) with an expiry, taken with a single conditional UPSERT, so two
runners asking at the same moment can't both win. A crashed run frees it at expiry (default 40 min, longer than
any posting job). If D1 can't be reached the job still runs (fail open): the ticker only ever sends a job to ONE
runner, so the lease is the second line of defence, not the only one.
"""
import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def owner():
    return f"{os.environ.get('OPS_RUNNER', 'github')}:{os.environ.get('GITHUB_RUN_ID', '')}:{os.getpid()}"


def _out(go):
    line = f"go={'yes' if go else 'no'}"
    print(line)
    if os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as f:
            f.write(line + "\n")
    me = owner()
    if os.environ.get("GITHUB_ENV"):  # so `release` in a later step knows who we are
        with open(os.environ["GITHUB_ENV"], "a", encoding="utf-8") as f:
            f.write(f"OPS_LOCK_OWNER={me}\n")


def acquire(name, ttl=2400):
    import state  # noqa: PLC0415
    me, now = owner(), int(time.time())
    try:
        state._d1(
            "INSERT INTO docs (kind, id, data) VALUES ('lock', ?, ?) ON CONFLICT (kind, id) DO UPDATE "
            "SET data = excluded.data, updated_at = strftime('%Y-%m-%dT%H:%M:%SZ','now') "
            "WHERE coalesce(json_extract(docs.data, '$.until'), 0) < ?",
            [name, json.dumps({"owner": me, "until": now + ttl, "since": now}), now])
        rows = state._d1("SELECT data FROM docs WHERE kind = 'lock' AND id = ?", [name])
        held = json.loads(rows[0]["data"]) if rows else {}
    except Exception as e:  # noqa: BLE001 - D1 down must not stop posting
        print(f"lock: D1 unreachable ({e}), running anyway", file=sys.stderr)
        return _out(True)
    if held.get("owner") == me:
        return _out(True)
    left = int(held.get("until", 0)) - now
    print(f"lock: {name} is held by {held.get('owner')} for {left} s more, skipping this run", file=sys.stderr)
    return _out(False)


def release(name):
    import state  # noqa: PLC0415
    me = os.environ.get("OPS_LOCK_OWNER") or owner()
    try:
        state._d1("DELETE FROM docs WHERE kind = 'lock' AND id = ? AND json_extract(data, '$.owner') = ?", [name, me])
    except Exception as e:  # noqa: BLE001
        print(f"lock: release failed ({e}); it expires on its own", file=sys.stderr)


if __name__ == "__main__":
    if len(sys.argv) < 3 or sys.argv[1] not in ("acquire", "release"):
        sys.exit(__doc__)
    {"acquire": acquire, "release": release}[sys.argv[1]](sys.argv[2])
