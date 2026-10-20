"""Mirror live state between the JSON files and D1. Which side is the truth: state.configured() (cloud.json).

    python3 -P tools/state_mirror.py push      # files -> D1, only while the files are the truth
    python3 -P tools/state_mirror.py pull      # D1 -> files, only once D1 is the truth (nightly readable backup)
    python3 -P tools/state_mirror.py compare   # exit 1 and list kind/id when D1 != files
    python3 -P tools/state_mirror.py sync      # workflows: push + compare while the files are the truth, else nothing

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
    if argv[:1] == ["sync"]:
        if state.configured() == "d1":
            print("D1 is the truth: nothing to sync")
            return 0
        return main(["push"]) or main(["compare"])
    if not argv or argv[0] not in ("push", "pull", "compare"):
        print(__doc__)
        return 2
    fb, d1 = state.backend("file"), state.backend("d1")
    truth = state.configured()
    if argv[0] == "push" and truth == "d1":
        print("D1 is the truth: push skipped (use pull)")
        return 0
    if argv[0] == "pull" and truth != "d1":
        print("the files are the truth: pull skipped (use push)")
        return 0
    if argv[0] == "pull":
        for kind in kinds(fb):
            for d in d1.all(kind):
                i = d.pop("id")
                if fb.get(kind, i) != d:
                    fb.put(kind, i, d)
            for i in diff(fb, d1, kind)[0]:  # in the files, gone from D1
                if d1.get(kind, i) is None:
                    fb.delete(kind, i)
        print("files updated from D1")
        return 0
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
