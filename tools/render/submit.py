"""Render a reel variant on Modal instead of this PC.

    python -P tools/render/submit.py production/reels/<slug> B [--include PATH ...] [--prep "cmd"] [--wait]

Packs the reel folder (minus node_modules/.venv/snaps, other variants' a-roll/cut-out, b-roll clips that
make_broll.py rebuilds) + production/editing/reel-kit + every --include path into a tar.gz, uploads it to R2,
writes job doc job/<id> to D1 and starts render() on Modal. --prep runs locally in the reel folder first.
Default command: bash make.sh <V>; outputs: media/<slug>/<slug>-<V>.mp4 and -phone.mp4.
--wait polls until the job ends and downloads the outputs to the same paths on this PC.
"""
import argparse
import datetime as dt
import io
import os
import re
import subprocess
import sys
import tarfile
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools"))
import r2  # noqa: E402
import state  # noqa: E402

SKIP_DIRS = {"node_modules", ".venv", "snaps", "__pycache__", ".git"}


def load_env():
    for f in ("control.env", "modal.env"):
        p = REPO / "secrets" / f
        if p.exists():
            for line in p.read_text(encoding="utf-8").splitlines():
                if "=" in line and not line.startswith("#"):
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip())


def keep(rel, variant):
    parts = Path(rel).parts
    if SKIP_DIRS & set(parts):
        return False
    name = parts[-1]
    if "assets" in parts and "media" in parts:
        if re.match(r"b_.*\.mp4$", name):  # make_broll.py rebuilds these every run
            return False
        m = re.match(r"(?:aroll_|fg_)([A-Z])[._]", name)
        if m and m.group(1) != variant:
            return False
    return True


def bundle(reel_dir, variant, includes, out):
    paths = [reel_dir, "production/editing/reel-kit", *includes]
    n = 0
    with tarfile.open(out, "w:gz", compresslevel=1) as t:  # mp4/webm don't compress: keep it fast
        for p in paths:
            root = REPO / p
            files = [root] if root.is_file() else sorted(x for x in root.rglob("*") if x.is_file())
            for f in files:
                rel = f.relative_to(REPO).as_posix()
                if not keep(rel, variant):
                    continue
                if f.suffix == ".sh":  # Windows checkouts are CRLF; bash on Linux chokes on \r
                    data = f.read_bytes().replace(b"\r\n", b"\n")
                    info = tarfile.TarInfo(rel)
                    info.size, info.mode, info.mtime = len(data), 0o755, int(f.stat().st_mtime)
                    t.addfile(info, io.BytesIO(data))
                else:
                    t.add(f, arcname=rel)
                n += 1
    return n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("reel_dir")
    ap.add_argument("variant")
    ap.add_argument("--include", action="append", default=[], help="extra repo path the build reads")
    ap.add_argument("--prep", help="command run locally in the reel folder before packing")
    ap.add_argument("--cmd", help="command run on Modal in the reel folder (default: bash make.sh V)")
    ap.add_argument("--wait", action="store_true")
    a = ap.parse_args()
    load_env()
    reel_dir = Path(a.reel_dir).resolve().relative_to(REPO).as_posix()
    slug, v = Path(reel_dir).name, a.variant
    if a.prep:
        subprocess.run(a.prep, shell=True, cwd=REPO / reel_dir, check=True)

    job_id = f"{slug}-{v}-{dt.datetime.now(dt.timezone.utc):%Y%m%dT%H%M%S}"
    tmp = REPO / "media" / "jobs" / f"{job_id}.tar.gz"
    tmp.parent.mkdir(parents=True, exist_ok=True)
    n = bundle(reel_dir, v, a.include, tmp)
    print(f"{job_id}: {n} files, {tmp.stat().st_size / 1e6:.0f} MB, uploading")
    key = f"jobs/{job_id}/bundle.tar.gz"
    r2.put_file(key, tmp)
    tmp.unlink()

    outputs = [f"media/{slug}/{slug}-{v}.mp4", f"media/{slug}/{slug}-{v}-phone.mp4"]
    jobs = state.backend("d1")
    jobs.put("job", job_id, {"reel": slug, "variant": v, "reel_dir": reel_dir, "bundle": key,
                             "cmd": a.cmd or f"bash make.sh {v}", "outputs": outputs, "status": "queued",
                             "error": None, "submitted_at": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")})
    import modal
    modal.Function.from_name("matteofights-render", "render").spawn(job_id)
    print(f"{job_id}: started on Modal")
    if a.wait:
        wait(job_id, outputs)


def wait(job_id, outputs):
    jobs, last = state.backend("d1"), None
    while True:
        j = jobs.get("job", job_id)
        if j["status"] != last:
            print(f"{job_id}: {j['status']}", flush=True)
            last = j["status"]
        if j["status"] == "done":
            for rel in outputs:
                r2.get_file(f"renders/{Path(rel).name}", REPO / rel)
                print(f"downloaded {rel}")
            print(f"{job_id}: done in {j.get('seconds', 0) // 60} min")
            return
        if j["status"] == "failed":
            sys.exit(f"{job_id}: FAILED\n{j.get('error')}")
        time.sleep(30)


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "wait":  # submit.py wait <job_id>
        load_env()
        j = state.backend("d1").get("job", sys.argv[2])
        wait(sys.argv[2], j["outputs"])
    else:
        main()
