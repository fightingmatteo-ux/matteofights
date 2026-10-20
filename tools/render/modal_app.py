"""Modal app "matteofights-render": runs a reel's build in the cloud, results go to R2.

Deploy:  python -m modal deploy tools/render/modal_app.py
Submit:  python -P tools/render/submit.py <reel_dir> <variant>   (see submit.py)

A job (D1 doc job/<id>) points at a bundle in R2 (jobs/<id>/bundle.tar.gz, a slice of the repo with the
same layout). render() unpacks it to /work, runs job["cmd"] in the reel folder (default: bash make.sh <V>),
uploads every job["outputs"] file to renders/tmp/ and only after all of them made it copies them to
renders/<name>, so a failed or timed-out job never leaves a partial file where posting looks.
"""
import datetime as dt
import shutil
import subprocess
import sys
import tarfile
import time
from pathlib import Path

import modal

TOOLS = Path(__file__).resolve().parents[1]
HF = "hyperframes@0.8.147"

image = (
    modal.Image.debian_slim(python_version="3.12")
    # chromium pulls in every system library chrome-headless-shell needs; HyperFrames brings its own Chrome
    .apt_install("ffmpeg", "curl", "ca-certificates", "chromium", "fonts-liberation", "fonts-noto-color-emoji",
                 "fonts-noto-core")
    .run_commands("curl -fsSL https://deb.nodesource.com/setup_22.x | bash -",
                  "apt-get install -y nodejs",
                  f"cd /tmp && npx --yes {HF} browser ensure")
    .pip_install("boto3", "numpy", "onnxruntime")
    .add_local_file(TOOLS / "state.py", "/repo/tools/state.py")
    .add_local_file(TOOLS / "r2.py", "/repo/tools/r2.py")
    .add_local_file(TOOLS / "cloud" / "cloud.json", "/repo/tools/cloud/cloud.json")
)
app = modal.App("matteofights-render", image=image)


def _now():
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


@app.function(cpu=8.0, memory=16384, timeout=7200, secrets=[modal.Secret.from_name("matteofights")])
def render(job_id: str):
    sys.path.insert(0, "/repo/tools")
    import r2
    import state

    jobs = state.backend("d1")
    job = jobs.get("job", job_id)
    t0 = time.time()
    jobs.patch("job", job_id, {"status": "rendering", "started_at": _now(), "error": None})
    try:
        work = Path("/work")
        shutil.rmtree(work, ignore_errors=True)
        work.mkdir()
        r2.get_file(job["bundle"], "/tmp/bundle.tar.gz")
        with tarfile.open("/tmp/bundle.tar.gz") as t:
            t.extractall(work, filter="data")
        reel = work / job["reel_dir"]
        if (reel / "package-lock.json").exists() and not (reel / "node_modules").exists():
            subprocess.run(["npm", "ci", "--silent"], cwd=reel, check=True)
        # under the 7200 s function timeout, so a hung build still ends as "failed" with its log
        p = subprocess.run(["bash", "-c", job["cmd"]], cwd=reel, capture_output=True, text=True, timeout=6600)
        log = (p.stdout + p.stderr)[-3000:]
        print(log)
        if p.returncode:
            raise RuntimeError(f"{job['cmd']} exited {p.returncode}\n{log}")
        names = []
        for rel in job["outputs"]:
            f = work / rel
            if not f.exists():
                raise RuntimeError(f"output missing: {rel}\n{log}")
            r2.put_file(f"renders/tmp/{job_id}/{f.name}", f)
            names.append(f.name)
        for n in names:  # all uploaded: now publish them
            r2.copy(f"renders/tmp/{job_id}/{n}", f"renders/{n}")
            r2.delete(f"renders/tmp/{job_id}/{n}")
        r2.delete(job["bundle"])  # failed jobs keep theirs for a look; R2 expires jobs/ after 2 days anyway
        jobs.patch("job", job_id, {"status": "done", "finished_at": _now(), "seconds": int(time.time() - t0),
                                   "keys": [f"renders/{n}" for n in names], "log": log[-1500:]})
    except Exception as e:  # noqa: BLE001 - every failure ends the job as failed with its reason
        jobs.patch("job", job_id, {"status": "failed", "finished_at": _now(), "seconds": int(time.time() - t0),
                                   "error": str(e)[-2000:]})
        raise
