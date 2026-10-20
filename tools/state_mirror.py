"""Mirror live state between the JSON files and D1 (phase 1: files are still the truth).

    python3 -P tools/state_mirror.py push      # files -> D1 (writes only what differs, removes ids gone from files)
    python3 -P tools/state_mirror.py compare   # exit 1 and list kind/id when D1 != files

Kinds: queue, queue_meta, crosspost, and every production/state/<kind>.json. D1 kinds that have no file
(jobs written by the Modal render app, for example) are left alone.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import state  # noqa: E402


def kinds(fb):
    found = ["queue", "queue_meta", "crosspost"]
    sdir = fb.root / "production" / "state"
    if sdir.exists():
        found += sorted(p.stem for p in sdir.glob("*.json"))
    return found


def diff(fb, d1, kind):
    """(changed: {id: file data}, gone: [ids only in D1])"""
    have = {d.pop("id"): d for d in fb.all(kind)}
    there = {d.pop("id"): d for d in d1.all(kind)}
    changed = {i: v for i, v in have.items() if there.get(i) != v}
    gone = sorted(set(there) - set(have))
    return changed, gone


def main(argv):
    if not argv or argv[0] not in ("push", "compare"):
        print(__doc__)
        return 2
    fb, d1 = state.backend("file"), state.backend("d1")
    bad = 0
    for kind in kinds(fb):
        changed, gone = diff(fb, d1, kind)
        if argv[0] == "push":
            for i, v in changed.items():
                d1.put(kind, i, v)
            for i in gone:
                d1.delete(kind, i)
            print(f"{kind}: {len(changed)} written, {len(gone)} removed")
        else:
            for i in sorted(changed):
                print(f"differs: {kind}/{i}")
            for i in gone:
                print(f"only in D1: {kind}/{i}")
            bad += len(changed) + len(gone)
    if argv[0] == "compare":
        print("D1 matches the files" if not bad else f"{bad} differences")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
