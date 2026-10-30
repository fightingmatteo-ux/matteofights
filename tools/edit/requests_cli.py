"""The studio's work items in D1, for the edit worker and the talking-point writer (both Claude, see WORKER.md).

    python3 -P tools/edit/requests_cli.py open                    # open uploads + revision requests, oldest first (JSON)
    python3 -P tools/edit/requests_cli.py fetch <upload_id> <dir> # download an upload's footage from R2
    python3 -P tools/edit/requests_cli.py notes <request_id> <dir>   # download a revision's annotated frames from R2
    python3 -P tools/edit/requests_cli.py finish <kind> <id> <status> [--note "what was done"]
    python3 -P tools/edit/requests_cli.py tp-add "<title>" --hook A --hook B --hook C --point ... [--source URL] [--why ...]
    python3 -P tools/edit/requests_cli.py tps                     # talking points not filmed yet (JSON)
    python3 -P tools/edit/requests_cli.py budget <max>            # exit 1 when today's Claude runs are used up

Kinds (all D1-only, written by the dashboard's /api functions):
  upload/<id>         {status: uploaded|working|done|failed, key (R2), name, size, note, talking_point, at, result}
  request/<id>        {status: open|working|done|failed, target (reel or queue id), text, at, result,
                       from the reel player: asset, round (1 = first revision of this reel), tags[],
                       notes[{t (seconds), text, tags[], image (R2 key of the frame with Matteo's drawing)}];
                       from the Hook tests verdict: kind_detail "iterate", brief (path), hold_until (round-2 re-edits)}
  talking_point/<id>  {status: new|filmed|skipped, title, hooks[3], points[], source, why, at}
"""
import argparse
import datetime as dt
import json
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import state  # noqa: E402

OPEN = {"upload": "uploaded", "request": "open"}


def db():
    return state.backend("d1")


def now():
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def open_work():
    out = []
    for kind, status in OPEN.items():
        out += [dict(d, kind=kind) for d in db().all(kind)
                if d.get("status") == status and d.get("hold_until", "") <= now()]   # iterate jobs wait for Matteo's note
    return sorted(out, key=lambda d: d.get("at", ""))


def finish(kind, id, status, note=None):
    db().patch(kind, id, {"status": status, "finished_at": now(), **({"result": note} if note else {})})


def add_talking_point(title, hooks, points, source=None, why=None):
    tid = dt.date.today().isoformat() + "-" + uuid.uuid4().hex[:6]
    db().put("talking_point", tid, {"status": "new", "title": title, "hooks": hooks, "points": points,
                                    "source": source, "why": why, "at": now()})
    return tid


def take_budget(max_runs, day=None):
    """Count one Claude run against today's cap; False when the cap is reached."""
    day = (day or dt.date.today()).isoformat()
    b = db().get("worker", "budget") or {}
    runs = b.get("runs", 0) if b.get("day") == day else 0
    if runs >= max_runs:
        return False
    db().put("worker", "budget", {"day": day, "runs": runs + 1})
    return True


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("open")
    f = sub.add_parser("fetch"); f.add_argument("id"); f.add_argument("dir")
    nt = sub.add_parser("notes"); nt.add_argument("id"); nt.add_argument("dir")
    fi = sub.add_parser("finish"); fi.add_argument("kind"); fi.add_argument("id"); fi.add_argument("status")
    fi.add_argument("--note")
    t = sub.add_parser("tp-add"); t.add_argument("title"); t.add_argument("--hook", action="append", default=[])
    t.add_argument("--point", action="append", default=[]); t.add_argument("--source"); t.add_argument("--why")
    sub.add_parser("tps")
    b = sub.add_parser("budget"); b.add_argument("max", type=int)
    a = ap.parse_args()
    if a.cmd == "open":
        print(json.dumps(open_work(), indent=2, ensure_ascii=False))
    elif a.cmd == "fetch":
        import r2
        u = db().get("upload", a.id)
        dst = Path(a.dir) / u["name"]
        r2.get_file(u["key"], dst)
        db().patch("upload", a.id, {"status": "working"})
        print(dst)
    elif a.cmd == "notes":
        import r2
        r = db().get("request", a.id) or {}
        for n in r.get("notes") or []:
            if n.get("image"):
                dst = Path(a.dir) / Path(n["image"]).name
                r2.get_file(n["image"], dst)
                print(f"{n['t']:.2f}s  {dst}  [{', '.join(n.get('tags') or [])}] {n.get('text', '')}")
    elif a.cmd == "finish":
        finish(a.kind, a.id, a.status, a.note)
    elif a.cmd == "tp-add":
        print(add_talking_point(a.title, a.hook, a.point, a.source, a.why))
    elif a.cmd == "tps":
        print(json.dumps([d for d in db().all("talking_point") if d.get("status") == "new"], indent=2, ensure_ascii=False))
    elif a.cmd == "budget":
        ok = take_budget(a.max)
        print("ok" if ok else "daily Claude budget used up")
        sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
