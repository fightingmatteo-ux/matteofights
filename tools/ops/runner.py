#!/usr/bin/env python3
"""Run a GitHub Actions workflow file anywhere (the Modal backup runner, or a laptop), step for step.

Why: the workflow files in .github/workflows are the ONLY definition of every job. When GitHub Actions can't run
(free minutes used up, outage), tools/ops/modal_ops.py runs the very same file through this interpreter, so the
two runners can never drift apart.

    python3 -P tools/ops/runner.py run post-queue.yml                      # really run it (repo = cwd checkout)
    python3 -P tools/ops/runner.py run listicle-factory.yml --input count=3
    python3 -P tools/ops/runner.py run listicle-factory.yml --event schedule --schedule "10 20 * * *"
    python3 -P tools/ops/runner.py plan post-queue.yml                     # dry run: print what would execute
    python3 -P tools/ops/runner.py check                                   # which workflows can run here

Supported (everything our workflows use): ${{ }} expressions (secrets, inputs, github.*, steps.<id>.outputs,
env, && || == != ! ( ), always/success/failure/cancelled, startsWith/endsWith/contains), job and step `if:`,
env at workflow/job/step level, `run:` with bash -eo pipefail, `shell:`, `working-directory` (+ job defaults),
`timeout-minutes`, `continue-on-error`, $GITHUB_ENV, $GITHUB_OUTPUT, $GITHUB_PATH, `needs:` ordering,
actions/checkout (the runner's clone IS the checkout), actions/setup-node|setup-python (tools are in the image).
Not supported, so refused up front: any other `uses:` action (e.g. claude-code-action in edit-worker.yml).

Secrets come from the environment under their GitHub names (the Modal secret "matteofights-ops" holds the same
names). ${{ github.token }} = RUNNER_GH_TOKEN (falls back to GH_TOKEN): a token that can push to the repo.
Every run on this runner is added to D1 (kind "ops_usage", id "<YYYY-MM>") for tools/ops/budget.py.
"""
import argparse
import datetime as dt
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[2]
WF_DIR = REPO / ".github" / "workflows"
SAFE_USES = ("actions/checkout", "actions/setup-node", "actions/setup-python")
DEFAULT_SHELL = "bash --noprofile --norc -eo pipefail {0}"
REPOSITORY = os.environ.get("GITHUB_REPOSITORY", "fightingmatteo-ux/matteofights")


# ---------------------------------------------------------------- expressions

class Ctx(dict):
    """Context object: attribute access, missing keys are '' (like GitHub's null in a string context)."""
    def __getattr__(self, k):
        v = self.get(k, "")
        return Ctx(v) if isinstance(v, dict) and not isinstance(v, Ctx) else v


TOKEN = re.compile(r"""\s*(?:
    (?P<str>'(?:[^']|'')*')
  | (?P<num>\d+(?:\.\d+)?)
  | (?P<op>&&|\|\||==|!=|<=|>=|<|>|!|\(|\)|,)
  | (?P<name>[A-Za-z_][A-Za-z0-9_-]*(?:\.[A-Za-z_*][A-Za-z0-9_-]*)*)
)""", re.X)
FUNCS = {"always", "success", "failure", "cancelled", "startsWith", "endsWith", "contains", "format", "toJSON",
         "fromJSON", "join"}
LITERALS = {"true": "True", "false": "False", "null": "None"}


def to_python(expr):
    """Translate one GitHub expression to a Python expression over the helpers in evaluate()."""
    out, pos = [], 0
    expr = expr.strip()
    while pos < len(expr):
        m = TOKEN.match(expr, pos)
        if not m or m.end() == pos:
            raise ValueError(f"can't parse expression near: {expr[pos:pos + 30]!r}")
        pos = m.end()
        if m["str"]:
            out.append(repr(m["str"][1:-1].replace("''", "'")))
        elif m["num"]:
            out.append(m["num"])
        elif m["op"]:
            out.append({"&&": " and ", "||": " or ", "!": " not ", ",": ", "}.get(m["op"], f" {m['op']} "))
        else:
            name = m["name"]
            if name in LITERALS:
                out.append(LITERALS[name])
            elif name in FUNCS:
                out.append(f"_f_{name}")
            else:
                head, *rest = name.split(".")
                out.append(f"_lookup({head!r}, {rest!r})")
    return "".join(out)


def evaluate(expr, ctx, status):
    def lookup(head, rest):
        v = ctx.get(head, "")
        for k in rest:
            v = v.get(k, "") if isinstance(v, dict) else ""
        return "" if v is None else v

    def s(x):
        return x if isinstance(x, str) else json.dumps(x) if isinstance(x, (dict, list)) else str(x)

    ns = {
        "_lookup": lookup,
        "_f_always": lambda: True,
        "_f_success": lambda: status["failed"] is False,
        "_f_failure": lambda: status["failed"] is True,
        "_f_cancelled": lambda: False,
        "_f_startsWith": lambda a, b: s(a).lower().startswith(s(b).lower()),
        "_f_endsWith": lambda a, b: s(a).lower().endswith(s(b).lower()),
        "_f_contains": lambda a, b: (b in a) if isinstance(a, list) else s(b).lower() in s(a).lower(),
        "_f_format": lambda f, *a: re.sub(r"\{(\d+)\}", lambda m: s(a[int(m[1])]), f),
        "_f_toJSON": lambda a: json.dumps(a),
        "_f_fromJSON": lambda a: json.loads(a),
        "_f_join": lambda a, sep=",": sep.join(map(s, a)) if isinstance(a, list) else s(a),
    }
    return eval(to_python(expr), {"__builtins__": {}}, ns)  # noqa: S307 - our own workflow files only


def render(text, ctx, status):
    """Substitute every ${{ expr }} in a string."""
    if not isinstance(text, str):
        return text
    def one(m):
        v = evaluate(m[1], ctx, status)
        if v is True or v is False:
            return "true" if v else "false"
        return "" if v is None else (json.dumps(v) if isinstance(v, (dict, list)) else str(v))
    return re.sub(r"\$\{\{(.*?)\}\}", one, text, flags=re.S)


def condition(cond, ctx, status):
    """Step/job `if:`. Without a status function GitHub adds success() &&."""
    if cond is None:
        return status["failed"] is False
    if isinstance(cond, bool):
        return cond and status["failed"] is False
    c = str(cond).strip()
    if c.startswith("${{") and c.endswith("}}"):
        c = c[3:-2]
    if not re.search(r"\b(always|success|failure|cancelled)\s*\(", c):
        c = f"success() && ({c})"
    return bool(evaluate(c, ctx, status))


# ---------------------------------------------------------------- workflow files

def load(name):
    path = Path(name) if Path(name).exists() else WF_DIR / name
    if not path.suffix:
        path = path.with_suffix(".yml")
    wf = yaml.safe_load(path.read_text(encoding="utf-8"))
    wf["_on"] = wf.get("on", wf.get(True)) or {}   # PyYAML (YAML 1.1) reads the key `on` as True
    wf["_file"] = path.name
    return wf


def unsupported(wf):
    """Steps this runner can't do. Empty list = runnable here."""
    bad = []
    for jid, job in (wf.get("jobs") or {}).items():
        if job.get("strategy") or job.get("services") or job.get("container") or job.get("uses"):
            bad.append(f"{jid}: matrix/services/container/reusable workflow")
        for st in job.get("steps") or []:
            u = st.get("uses")
            if u and not u.startswith(SAFE_USES):
                bad.append(f"{jid}: uses {u}")
    return bad


def job_order(jobs):
    order, seen = [], set()
    def visit(j, stack=()):
        if j in seen:
            return
        if j in stack:
            raise ValueError(f"needs cycle at {j}")
        needs = jobs[j].get("needs") or []
        for n in ([needs] if isinstance(needs, str) else needs):
            visit(n, stack + (j,))
        seen.add(j)
        order.append(j)
    for j in jobs:
        visit(j)
    return order


def inputs_for(wf, given, event):
    """workflow_dispatch inputs with their defaults (booleans as booleans, like GitHub)."""
    spec = ((wf["_on"] or {}).get("workflow_dispatch") or {}).get("inputs") or {} if isinstance(wf["_on"], dict) else {}
    out = {}
    if event == "workflow_dispatch":
        for k, d in spec.items():
            v = (d or {}).get("default", "")
            if (d or {}).get("type") == "boolean":
                v = str(v).lower() == "true"
            out[k] = v
    for k, v in given.items():
        typ = (spec.get(k) or {}).get("type")
        out[k] = (str(v).lower() == "true") if typ == "boolean" else v
    return out


# ---------------------------------------------------------------- running

def parse_env_file(path):
    """$GITHUB_ENV / $GITHUB_OUTPUT format: KEY=value lines and KEY<<DELIM heredocs."""
    out = {}
    if not path.exists():
        return out
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        m = re.match(r"^([^=<]+)<<(.+)$", line)
        if m:
            key, delim, buf = m[1], m[2], []
            i += 1
            while i < len(lines) and lines[i] != delim:
                buf.append(lines[i])
                i += 1
            out[key] = "\n".join(buf)
        elif "=" in line:
            k, v = line.split("=", 1)
            out[k] = v
        i += 1
    path.write_text("")
    return out


def run_workflow(name, given=None, event="workflow_dispatch", schedule="", plan_only=False, log=print):
    wf = load(name)
    bad = unsupported(wf)
    if bad:
        raise SystemExit(f"{wf['_file']} can't run outside GitHub: {'; '.join(bad)}")
    sha = subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO, capture_output=True, text=True).stdout.strip()
    secrets = Ctx(os.environ)
    token = os.environ.get("RUNNER_GH_TOKEN") or os.environ.get("GH_TOKEN") or ""
    inputs = inputs_for(wf, given or {}, event)
    github = Ctx(token=token, event_name=event, ref_name="master", ref="refs/heads/master", sha=sha,
                 repository=REPOSITORY, workspace=str(REPO), run_number=str(int(time.time())), actor="modal-runner",
                 event=Ctx(schedule=schedule, inputs=inputs))
    tmp = Path(tempfile.mkdtemp(prefix="wf-"))
    files = {k: tmp / k for k in ("env", "output", "path", "summary")}
    for f in files.values():
        f.write_text("")
    wf_env = dict(wf.get("env") or {})
    added_env, added_path = {}, []
    t0, failed_any, results = time.time(), False, {}

    for jid in job_order(wf["jobs"]):
        job = wf["jobs"][jid]
        status = {"failed": False}
        steps_ctx = Ctx()
        ctx = Ctx(secrets=secrets, inputs=inputs, github=github, steps=steps_ctx, env=Ctx(), vars=Ctx(),
                  runner=Ctx(os="Linux", temp=str(tmp)), job=Ctx(status="success"))
        needs = job.get("needs") or []
        needs = [needs] if isinstance(needs, str) else needs
        needs_failed = any(results.get(n) != "success" for n in needs)
        ctx["needs"] = Ctx({n: Ctx(result=results.get(n, "skipped")) for n in needs})
        if not condition(job.get("if"), ctx, {"failed": needs_failed}):
            log(f"== job {jid}: skipped" + (f" (if: {job['if']})" if "if" in job else " (a needed job failed)"))
            results[jid] = "skipped"
            continue
        job_deadline = t0 + 60 * float(job.get("timeout-minutes", 360))
        workdir_default = ((job.get("defaults") or {}).get("run") or {}).get("working-directory")
        log(f"== job {jid}")
        for n, st in enumerate(job.get("steps") or [], 1):
            label = st.get("name") or st.get("uses") or (st.get("run") or "").splitlines()[0][:60]
            env = {}
            for layer in (wf_env, job.get("env") or {}):
                for k, v in layer.items():
                    env[k] = render(str(v), ctx, status)
            env.update(added_env)
            ctx["env"] = Ctx(env)
            for k, v in (st.get("env") or {}).items():
                env[k] = render(str(v), ctx, status)
            ctx["env"] = Ctx(env)
            if not condition(st.get("if"), ctx, status):
                log(f"-- {n}. {label}: skipped")
                if st.get("id"):
                    steps_ctx[st["id"]] = Ctx(outputs=Ctx(), outcome="skipped", conclusion="skipped")
                continue
            if st.get("uses"):
                u = st["uses"]
                if u.startswith("actions/checkout"):
                    ref = render(str((st.get("with") or {}).get("ref", "")), ctx, status)
                    log(f"-- {n}. {label}: the runner's clone is the checkout" + (f" (ref {ref})" if ref else ""))
                    if ref and ref not in ("master", "refs/heads/master") and not plan_only:
                        subprocess.run(["git", "fetch", "-q", "origin", ref], cwd=REPO, check=False)
                        subprocess.run(["git", "checkout", "-q", "FETCH_HEAD"], cwd=REPO, check=False)
                else:
                    log(f"-- {n}. {label}: provided by the image")
                if st.get("id"):
                    steps_ctx[st["id"]] = Ctx(outputs=Ctx(), outcome="success", conclusion="success")
                continue
            script = render(st.get("run", ""), ctx, status)
            wd = st.get("working-directory") or workdir_default
            wd = REPO / render(wd, ctx, status) if wd else REPO
            if plan_only:
                shown = {k: env[k] for k, raw in (st.get("env") or {}).items()
                         if "secrets." not in str(raw) and "github.token" not in str(raw)}
                log(f"-- {n}. {label}\n   cwd: {wd.relative_to(REPO) if wd != REPO else '.'}"
                    + "".join(f"\n   env {k}={v!r}" for k, v in shown.items()) + "\n"
                    + "\n".join("   | " + ln for ln in script.splitlines()))
                if st.get("id"):
                    steps_ctx[st["id"]] = Ctx(outputs=Ctx(), outcome="success", conclusion="success")
                continue
            sf = tmp / f"step{n}.sh"
            sf.write_text(script, encoding="utf-8")
            shell = (st.get("shell") or DEFAULT_SHELL)
            if shell in ("bash", "sh", "python"):
                shell = {"bash": DEFAULT_SHELL, "sh": "sh -e {0}", "python": "python3 {0}"}[shell]
            cmd = shell.replace("{0}", str(sf)) if "{0}" in shell else f"{shell} {sf}"
            penv = dict(os.environ)
            penv.update({"CI": "true", "GITHUB_ACTIONS": "true", "OPS_RUNNER": "modal",
                         "GITHUB_REPOSITORY": REPOSITORY, "GITHUB_WORKSPACE": str(REPO), "GITHUB_SHA": sha,
                         "GITHUB_REF": "refs/heads/master", "GITHUB_REF_NAME": "master", "GITHUB_EVENT_NAME": event,
                         "GITHUB_RUN_NUMBER": github["run_number"], "GITHUB_RUN_ID": github["run_number"],
                         "GITHUB_ENV": str(files["env"]), "GITHUB_OUTPUT": str(files["output"]),
                         "GITHUB_PATH": str(files["path"]), "GITHUB_STEP_SUMMARY": str(files["summary"]),
                         "RUNNER_TEMP": str(tmp)})
            penv.update(env)
            if added_path:
                penv["PATH"] = ":".join(added_path) + ":" + penv.get("PATH", "")
            limit = min(60 * float(st.get("timeout-minutes", 360)), max(30.0, job_deadline - time.time()))
            log(f"-- {n}. {label}")
            s0 = time.time()
            try:
                rc = subprocess.run(cmd, shell=True, cwd=wd, env=penv, timeout=limit).returncode
            except subprocess.TimeoutExpired:
                log(f"   timed out after {int(limit)} s")
                rc = 124
            outputs = parse_env_file(files["output"])
            added_env.update(parse_env_file(files["env"]))
            added_path += [p for p in files["path"].read_text().splitlines() if p.strip()]
            files["path"].write_text("")
            outcome = "success" if rc == 0 else "failure"
            ok = rc == 0 or bool(st.get("continue-on-error"))
            if st.get("id"):
                steps_ctx[st["id"]] = Ctx(outputs=Ctx(outputs), outcome=outcome,
                                          conclusion="success" if ok else "failure")
            log(f"   {outcome} (exit {rc}, {time.time() - s0:.0f} s)" + ("" if ok or rc == 0 else ""))
            if not ok:
                status["failed"] = True
                ctx["job"] = Ctx(status="failure")
        failed_any = failed_any or status["failed"]
        results[jid] = "failure" if status["failed"] else "success"
        log(f"== job {jid}: {'failure' if status['failed'] else 'success'}")
    shutil.rmtree(tmp, ignore_errors=True)
    seconds = int(time.time() - t0)
    if not plan_only:
        record_usage(wf["_file"], seconds, "failure" if failed_any else "success")
    return 1 if failed_any else 0


def record_usage(workflow, seconds, conclusion):
    """Add this run to D1 ops_usage/<YYYY-MM> (modal.<workflow>.{runs,seconds,failures}). Never fails the run."""
    if os.environ.get("OPS_RUNNER_NO_LEDGER"):
        return
    try:
        sys.path.insert(0, str(REPO / "tools"))
        import state  # noqa: PLC0415
        month = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m")
        key = workflow.replace(".yml", "").replace("-", "_")
        base = f"$.modal.{key}"
        state._d1("INSERT INTO docs (kind, id, data) VALUES ('ops_usage', ?, '{}') ON CONFLICT (kind, id) DO NOTHING",
                  [month])
        state._d1(
            "UPDATE docs SET data = json_set(data, "
            f"'{base}.runs', coalesce(json_extract(data, '{base}.runs'), 0) + 1, "
            f"'{base}.seconds', coalesce(json_extract(data, '{base}.seconds'), 0) + ?, "
            f"'{base}.failures', coalesce(json_extract(data, '{base}.failures'), 0) + ?, "
            f"'{base}.last', ?), updated_at = strftime('%Y-%m-%dT%H:%M:%SZ','now') "
            "WHERE kind = 'ops_usage' AND id = ?",
            [seconds, 1 if conclusion == "failure" else 0, dt.datetime.now(dt.timezone.utc).isoformat()[:19] + "Z",
             month])
    except Exception as e:  # noqa: BLE001
        print(f"(usage not recorded: {e})", file=sys.stderr)


def check_all():
    rows = []
    for p in sorted(WF_DIR.glob("*.yml")):
        bad = unsupported(load(p.name))
        rows.append((p.name, "ok" if not bad else "GitHub only: " + "; ".join(bad)))
    return rows


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for c in ("run", "plan"):
        p = sub.add_parser(c)
        p.add_argument("workflow")
        p.add_argument("--input", action="append", default=[], help="key=value (workflow_dispatch input)")
        p.add_argument("--event", default="workflow_dispatch", choices=["workflow_dispatch", "schedule"])
        p.add_argument("--schedule", default="", help='the cron line for --event schedule, e.g. "10 20 * * *"')
    sub.add_parser("check")
    a = ap.parse_args()
    if a.cmd == "check":
        for f, s in check_all():
            print(f"{f:24} {s}")
        return 0
    given = dict(kv.split("=", 1) for kv in a.input)
    return run_workflow(a.workflow, given, a.event, a.schedule, plan_only=(a.cmd == "plan"))


if __name__ == "__main__":
    sys.exit(main())
