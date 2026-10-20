"""The only way scripts read and write live state (queue, cross-posts, jobs, ...).

Backend: env STATE_BACKEND, else "state_backend" in tools/cloud/cloud.json, else "file" (the JSON files).
"d1" = Cloudflare D1. Flipping cloud.json is the cutover: every workflow and local run follows it.
Every record is (kind, id) -> JSON object. Non-object values (like a file's "_how" text)
are stored as {"value": ...}.

    import state
    state.get("queue", "freeze-A")
    state.patch("queue", "freeze-A", {"status": "posting"})   # merges fields, never rewrites the doc

File backend layout (root = env STATE_ROOT or the repo):
    queue       production/schedule/queue.json["items"] (list, matched by "id")
    queue_meta  production/schedule/queue.json top-level keys other than "items"
    crosspost   production/schedule/crosspost.json top-level keys
    <other>     production/state/<kind>.json, a dict by id
D1 backend: table docs(kind, id, data) from tools/cloud/schema.sql; ids from tools/cloud/cloud.json,
token from env CLOUDFLARE_D1_TOKEN (falls back to CLOUDFLARE_BUILD_TOKEN).
"""
import json
import os
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CLOUD = REPO / "tools" / "cloud" / "cloud.json"


def merge(target, patch):
    """RFC 7396 merge patch, the same rule as SQLite/D1 json_patch."""
    if not isinstance(patch, dict):
        return patch
    out = dict(target) if isinstance(target, dict) else {}
    for k, v in patch.items():
        if v is None:
            out.pop(k, None)
        else:
            out[k] = merge(out.get(k), v)
    return out


def _wrap(v):
    return v if isinstance(v, dict) else {"value": v}


def _unwrap(d):
    return d["value"] if set(d) == {"value"} else d


def _read(path, default):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else default


def _write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


class FileBackend:
    def __init__(self, root=None):
        self.root = Path(root or os.environ.get("STATE_ROOT") or REPO)

    def _path(self, kind):
        if kind in ("queue", "queue_meta"):
            return self.root / "production" / "schedule" / "queue.json"
        if kind == "crosspost":
            return self.root / "production" / "schedule" / "crosspost.json"
        return self.root / "production" / "state" / f"{kind}.json"

    def _load(self, kind):
        """Return (whole file, dict view of kind) - for queue the view maps id -> item."""
        doc = _read(self._path(kind), {"items": []} if kind == "queue" else {})
        if kind == "queue":
            return doc, {i["id"]: i for i in doc.get("items", [])}
        if kind == "queue_meta":
            return doc, {k: _wrap(v) for k, v in doc.items() if k != "items"}
        return doc, {k: _wrap(v) for k, v in doc.items()}

    def _store(self, kind, doc, id, data):
        """Set (data) or remove (None) one id inside the whole file and save it."""
        if kind == "queue":
            items = doc.setdefault("items", [])
            idx = next((n for n, i in enumerate(items) if i.get("id") == id), None)
            if data is None:
                if idx is not None:
                    items.pop(idx)
            elif idx is None:
                items.append(dict(data, id=id))
            else:
                items[idx] = dict(data, id=id)
        elif data is None:
            doc.pop(id, None)
        else:
            doc[id] = _unwrap(data)
        _write(self._path(kind), doc)

    def get(self, kind, id):
        return self._load(kind)[1].get(id)

    def all(self, kind):
        view = self._load(kind)[1]
        return [dict(view[k], id=k) for k in sorted(view)]

    def put(self, kind, id, data):
        self._store(kind, self._load(kind)[0], id, data)

    def patch(self, kind, id, fields):
        doc, view = self._load(kind)
        self._store(kind, doc, id, merge(view.get(id, {}), fields))

    def delete(self, kind, id):
        self._store(kind, self._load(kind)[0], id, None)

    def set_paths(self, kind, id, values, remove=()):
        doc, view = self._load(kind)
        data = json.loads(json.dumps(view.get(id, {})))
        for path, v in values.items():
            node = data
            for k in path[:-1]:
                node = node.setdefault(k, {})
            node[path[-1]] = v
        for path in remove:
            node = data
            for k in path[:-1]:
                node = node.get(k, {})
            node.pop(path[-1], None)
        self._store(kind, doc, id, data)


def _d1(sql, params):
    cfg = json.loads(CLOUD.read_text(encoding="utf-8"))
    token = os.environ.get("CLOUDFLARE_D1_TOKEN") or os.environ.get("CLOUDFLARE_BUILD_TOKEN")
    if not token:  # local run: read it from secrets/control.env
        env = REPO / "secrets" / "control.env"
        lines = env.read_text(encoding="utf-8").splitlines() if env.exists() else []
        token = next((l.split("=", 1)[1].strip() for l in lines if l.startswith("CLOUDFLARE_BUILD_TOKEN=")), None)
    if not token:
        raise RuntimeError("D1 token missing: set CLOUDFLARE_D1_TOKEN")
    url = (f"https://api.cloudflare.com/client/v4/accounts/{cfg['account_id']}"
           f"/d1/database/{cfg['d1_database_id']}/query")
    req = urllib.request.Request(url, method="POST",
                                 data=json.dumps({"sql": sql, "params": params}).encode(),
                                 headers={"Authorization": f"Bearer {token}",
                                          "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        body = json.load(r)
    if not body.get("success"):
        raise RuntimeError(f"D1 query failed: {body.get('errors')}")
    return body["result"][0]["results"]


def _jpath(path):
    return "$" + "".join('."' + str(k).replace('"', '') + '"' for k in path)


NOW = "strftime('%Y-%m-%dT%H:%M:%SZ','now')"


class D1Backend:
    def get(self, kind, id):
        rows = _d1("SELECT data FROM docs WHERE kind = ? AND id = ?", [kind, id])
        return json.loads(rows[0]["data"]) if rows else None

    def all(self, kind):
        rows = _d1("SELECT id, data FROM docs WHERE kind = ? ORDER BY id", [kind])
        return [dict(json.loads(r["data"]), id=r["id"]) for r in rows]

    def put(self, kind, id, data):
        _d1(f"INSERT INTO docs (kind, id, data) VALUES (?, ?, ?) "
            f"ON CONFLICT (kind, id) DO UPDATE SET data = excluded.data, updated_at = {NOW}",
            [kind, id, json.dumps(data, ensure_ascii=False)])

    def patch(self, kind, id, fields):
        # json_patch runs inside D1, so two workflows patching different fields both survive.
        _d1(f"INSERT INTO docs (kind, id, data) VALUES (?, ?, json_patch('{{}}', ?)) "
            f"ON CONFLICT (kind, id) DO UPDATE SET data = json_patch(docs.data, ?), "  # raw patch: nulls delete
            f"updated_at = {NOW}",
            [kind, id, json.dumps(fields, ensure_ascii=False), json.dumps(fields, ensure_ascii=False)])

    def delete(self, kind, id):
        _d1("DELETE FROM docs WHERE kind = ? AND id = ?", [kind, id])

    def set_paths(self, kind, id, values, remove=()):
        # json_set/json_remove run inside D1 on each path only: other fields (someone else's change) survive.
        # A path's parent must exist; callers set a missing parent whole instead.
        _d1("INSERT INTO docs (kind, id, data) VALUES (?, ?, '{}') ON CONFLICT (kind, id) DO NOTHING", [kind, id])
        expr, params = "data", []
        if values:
            expr = "json_set(data" + ", ?, json(?)" * len(values) + ")"
            for path, v in values.items():
                params += [_jpath(path), json.dumps(v, ensure_ascii=False)]
        if remove:
            expr = f"json_remove({expr}" + ", ?" * len(remove) + ")"
            params += [_jpath(path) for path in remove]
        _d1(f"UPDATE docs SET data = {expr}, updated_at = {NOW} WHERE kind = ? AND id = ?", params + [kind, id])


def backend(name):
    if name == "file":
        return FileBackend()
    if name == "d1":
        return D1Backend()
    raise ValueError(f"unknown state backend: {name}")


def configured():
    if os.environ.get("STATE_BACKEND"):
        return os.environ["STATE_BACKEND"]
    try:
        return json.loads(CLOUD.read_text(encoding="utf-8")).get("state_backend", "file")
    except FileNotFoundError:
        return "file"


def _current():
    return backend(configured())


def get(kind, id):
    return _current().get(kind, id)


def all(kind):
    return _current().all(kind)


def put(kind, id, data):
    _current().put(kind, id, data)


def patch(kind, id, fields):
    _current().patch(kind, id, fields)


def delete(kind, id):
    _current().delete(kind, id)


def set_paths(kind, id, values, remove=(), be=None):
    """Replace whole values at nested paths ({("reel", "youtube"): {...}}) and remove paths, touching nothing else."""
    (be or _current()).set_paths(kind, id, values, remove)


def snapshot(kind, be=None):
    """(items, before) for scripts that edit many items in place: change `items`, then save_changed()."""
    items = (be or _current()).all(kind)
    return items, {i["id"]: json.loads(json.dumps(i)) for i in items}


def save_changed(kind, items, before, be=None):
    """Write only the fields that differ from `before`, each replaced whole (removed fields are deleted), so a
    field someone else changed meanwhile (an approval, a post status) is never overwritten with a stale copy."""
    be = be or _current()
    for item in items:
        old = before.get(item["id"])
        if old is None:
            be.put(kind, item["id"], item)
        else:
            changed = {(k,): v for k, v in item.items() if old.get(k) != v}
            gone = [(k,) for k in old if k not in item]
            if changed or gone:
                be.set_paths(kind, item["id"], changed, gone)
        before[item["id"]] = json.loads(json.dumps(item))
