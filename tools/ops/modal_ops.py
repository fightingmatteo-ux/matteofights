"""Modal app "matteofights-ops": the free backup runner for every GitHub workflow (Modal Starter = $30/month credits).

It runs the SAME .github/workflows/*.yml files through tools/ops/runner.py, on a fresh clone of the repo, and
pushes results back exactly like a GitHub run would. Nothing here defines what a job does; the workflow file does.

Who starts it
  - the Cloudflare ticker (tools/ticker), via POST <ops url>/dispatch, whenever the router sends a job here
    (GitHub out of minutes, GitHub down, or GitHub refusing a run). Body: {"workflow": "post-queue.yml",
    "inputs": {...}, "event": "workflow_dispatch"|"schedule", "schedule": "<cron>"}, header Authorization: Bearer
    <OPS_TOKEN>. Answers 202 + call id at once; the run continues in the background.
  - `watchdog` (every 30 min): if the ticker has gone quiet for 20+ min (Cloudflare broken or paused), it runs
    Post queue and Cross-post itself. The D1 lease (tools/ops/lock.py) stops doubles with GitHub's backup crons.
  - by hand: python -m modal run tools/ops/modal_ops.py --workflow health.yml

Deploy (laptop): bash tools/ops/deploy.sh     Secret: "matteofights-ops" = every GitHub secret name + RUNNER_GH_TOKEN
(push access to the repo) + OPS_TOKEN (shared with the ticker). Usage lands in D1 ops_usage/<YYYY-MM> for
tools/ops/budget.py, which tells this app to take only essential jobs when the month's credits run low.
"""
import json
import os
import subprocess
import time

import modal

REPO = "fightingmatteo-ux/matteofights"
# heavy = renders / downloads / image work; everything else gets a small container (billed per second)
HEAVY = {"listicle-factory.yml", "carousel.yml", "fetch-video.yml", "competitors.yml", "sound-scout.yml",
         "render-submit.yml", "drive-upload.yml", "control-deploy.yml"}
# what still runs when the month's Modal credits are nearly used (budget mode "essential")
ESSENTIAL = {"post-queue.yml", "crosspost.yml", "post-trial-reel.yml", "control.yml", "health.yml"}
GITHUB_ONLY = {"edit-worker.yml", "talking-points.yml"}  # claude-code-action: can't run outside GitHub

image = (
    modal.Image.debian_slim(python_version="3.12")
    .apt_install("git", "ffmpeg", "curl", "ca-certificates", "rclone", "jq", "fonts-noto-color-emoji",
                 "fonts-dejavu-core", "fonts-liberation", "unzip")
    .run_commands(
        "curl -fsSL https://deb.nodesource.com/setup_22.x | bash -", "apt-get install -y nodejs",
        # workflow steps say `sudo apt-get ...`; the container already runs as root
        "printf '#!/bin/sh\\nexec \"$@\"\\n' > /usr/local/bin/sudo && chmod +x /usr/local/bin/sudo",
        "curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg -o /usr/share/keyrings/gh.gpg",
        "echo 'deb [signed-by=/usr/share/keyrings/gh.gpg] https://cli.github.com/packages stable main' "
        "> /etc/apt/sources.list.d/gh.list && apt-get update -qq && apt-get install -y -qq gh")
    .pip_install("pyyaml", "boto3", "pillow", "requests", "numpy", "fastapi[standard]")
)
app = modal.App("matteofights-ops", image=image)
SECRET = modal.Secret.from_name("matteofights-ops")


def _clone():
    token = os.environ["RUNNER_GH_TOKEN"]
    subprocess.run(["rm", "-rf", "/repo"], check=True)
    subprocess.run(["git", "clone", "-q", "--depth", "50", f"https://x-access-token:{token}@github.com/{REPO}.git",
                    "/repo"], check=True)
    for k, v in (("user.name", "modal-runner[bot]"), ("user.email", "modal-runner@users.noreply.github.com"),
                 ("pull.rebase", "true")):
        subprocess.run(["git", "config", k, v], cwd="/repo", check=True)


def _run(workflow, inputs=None, event="workflow_dispatch", schedule=""):
    t0 = time.time()
    _clone()
    os.environ["OPS_RUNNER"] = "modal"
    os.environ.setdefault("GH_TOKEN", os.environ["RUNNER_GH_TOKEN"])
    cmd = ["python3", "-P", "tools/ops/runner.py", "run", workflow, "--event", event]
    if schedule:
        cmd += ["--schedule", schedule]
    for k, v in (inputs or {}).items():
        cmd += ["--input", f"{k}={v}"]
    rc = subprocess.run(cmd, cwd="/repo").returncode
    print(f"{workflow}: exit {rc} in {time.time() - t0:.0f} s")
    return rc


@app.function(secrets=[SECRET], cpu=1.0, memory=2048, timeout=3 * 3600)
def run_light(workflow: str, inputs: dict = None, event: str = "workflow_dispatch", schedule: str = ""):
    return _run(workflow, inputs, event, schedule)


@app.function(secrets=[SECRET], cpu=4.0, memory=8192, timeout=6 * 3600)
def run_heavy(workflow: str, inputs: dict = None, event: str = "workflow_dispatch", schedule: str = ""):
    return _run(workflow, inputs, event, schedule)


def _d1(sql, params):
    import urllib.request
    acct, db = "849fbd13419572f8d5e345f23dd3de11", "bf069f02-2394-43aa-a11b-ea10985f78c6"
    req = urllib.request.Request(
        f"https://api.cloudflare.com/client/v4/accounts/{acct}/d1/database/{db}/query",
        data=json.dumps({"sql": sql, "params": params}).encode(), method="POST",
        headers={"Authorization": f"Bearer {os.environ['CLOUDFLARE_D1_TOKEN']}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.load(r)["result"][0]["results"]


def _doc(kind, id):
    try:
        rows = _d1("SELECT data, updated_at FROM docs WHERE kind = ? AND id = ?", [kind, id])
        return (json.loads(rows[0]["data"]), rows[0]["updated_at"]) if rows else ({}, None)
    except Exception as e:  # noqa: BLE001
        print("D1 read failed:", e)
        return {}, None


def start(workflow, inputs=None, event="workflow_dispatch", schedule=""):
    fn = run_heavy if workflow in HEAVY else run_light
    return fn.spawn(workflow, inputs or {}, event, schedule).object_id


# One web endpoint (Modal Starter limits how many): POST /dispatch for the ticker, GET /health for checks.
@app.function(secrets=[SECRET], cpu=0.25, memory=256)
@modal.asgi_app()
def ops():
    from fastapi import FastAPI, Header, HTTPException  # noqa: PLC0415
    web = FastAPI()

    @web.post("/dispatch", status_code=202)
    def _dispatch(body: dict, authorization: str = Header(default="")):
        if authorization != f"Bearer {os.environ['OPS_TOKEN']}":
            raise HTTPException(401, "bad token")
        wf = str(body.get("workflow", ""))
        if not wf.endswith(".yml") or "/" in wf or wf in GITHUB_ONLY:
            raise HTTPException(400, f"{wf} can't run on Modal")
        budget, _ = _doc("ops", "budget")
        if budget.get("modal_mode") == "essential" and wf not in ESSENTIAL:
            raise HTTPException(429, f"Modal credits nearly used this month: only essential jobs run ({wf} skipped)")
        if budget.get("modal_mode") == "off":
            raise HTTPException(429, "Modal credits used up this month")
        call = start(wf, body.get("inputs") or {}, body.get("event") or "workflow_dispatch", body.get("schedule") or "")
        return {"started": wf, "call_id": call}

    @web.get("/health")
    def _health():
        return {"ok": True}

    return web


@app.function(secrets=[SECRET], cpu=0.25, memory=256, schedule=modal.Cron("*/30 * * * *"))
def watchdog():
    """Last line of defence: the ticker is quiet (Cloudflare down/paused) -> run the posting jobs from here."""
    import datetime as dt  # noqa: PLC0415
    beat, updated = _doc("ops", "ticker")
    if not updated:
        print("no ticker heartbeat yet (first deploy?): not acting")
        return
    last = dt.datetime.fromisoformat(updated.replace("Z", "+00:00"))
    quiet = (dt.datetime.now(dt.timezone.utc) - last).total_seconds() / 60
    print(f"ticker last seen {quiet:.0f} min ago")
    if quiet < 20:
        return
    for wf in ("post-queue.yml", "crosspost.yml"):
        print("ticker silent: starting", wf, start(wf))


@app.local_entrypoint()
def main(workflow: str = "health.yml", event: str = "workflow_dispatch"):
    fn = run_heavy if workflow in HEAVY else run_light
    print("exit", fn.remote(workflow, {}, event, ""))
