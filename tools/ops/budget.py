#!/usr/bin/env python3
"""Watch every free limit so nothing ever runs out: GitHub Actions minutes, Modal credits, R2 storage, Pages
deploys, D1, the ticker's heartbeat and the ticker's copy of the workflow schedules.

Runs inside the Health check workflow (every 6 h, on whichever runner is live). Writes D1 ops/budget, which
  - the ticker reads to move timed jobs to the Modal backup when GitHub passes 85 % of its month (route.js), and
  - the Modal endpoint reads to take only essential jobs (posting, approvals) when Modal credits pass 75 %.
Telegram gets one message per limit per level (70 / 85 / 95 %) per month.

    python3 -P tools/ops/budget.py            # measure, save, alert
    python3 -P tools/ops/budget.py --dry-run  # measure and print only

Limits and prices: tools/ops/limits.json. GitHub minutes: the official billing API when BILLING_TOKEN (a
fine-grained token with the account permission "Plan: read") is set, else an estimate from this repo's runs
(each run rounded up to a whole minute; checked 2026-10: reads ~15 % above GitHub's own figure, so it switches
early, never late; refused runs that never started don't count).
Modal: estimated from the runner ledger (D1 ops_usage) + render jobs (D1 job) at Modal's per-second prices x1.5.
"""
import datetime as dt
import json
import math
import os
import subprocess
import sys
import urllib.parse
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(REPO / "tools"))
LIMITS = json.loads((HERE / "limits.json").read_text())
REPOSITORY = os.environ.get("GITHUB_REPOSITORY", "fightingmatteo-ux/matteofights")
OWNER = REPOSITORY.split("/")[0]
DRY = "--dry-run" in sys.argv


def now():
    return dt.datetime.now(dt.timezone.utc)


def _gh(path, token=None):
    req = urllib.request.Request(f"https://api.github.com{path}", headers={
        "Authorization": f"Bearer {token or os.environ.get('GH_TOKEN', '')}", "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28", "User-Agent": "matteofights-budget"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def _ts(s):
    return dt.datetime.fromisoformat(s.replace("Z", "+00:00"))


# ---------------------------------------------------------------- GitHub

def github_minutes(month_start):
    tok = os.environ.get("BILLING_TOKEN")
    if tok:
        try:
            d = _gh(f"/users/{OWNER}/settings/billing/usage?year={month_start.year}&month={month_start.month}", tok)
            mins = sum(i.get("quantity", 0) for i in d.get("usageItems", [])
                       if i.get("product", "").lower() == "actions" and "minute" in i.get("unitType", "").lower())
            return round(mins), "GitHub billing API"
        except Exception as e:  # noqa: BLE001
            print(f"billing API unavailable ({e}); estimating from runs", file=sys.stderr)
    total, seen, day = 0.0, set(), month_start
    end = now()
    while day <= end:  # 3-day windows: the runs API returns at most 1,000 results per query
        nxt = min(day + dt.timedelta(days=3), end + dt.timedelta(seconds=1))
        rng = f"{day.strftime('%Y-%m-%dT%H:%M:%SZ')}..{nxt.strftime('%Y-%m-%dT%H:%M:%SZ')}"
        page = 1
        while page <= 10:
            q = urllib.parse.quote(rng)
            runs = _gh(f"/repos/{REPOSITORY}/actions/runs?per_page=100&page={page}&created={q}").get("workflow_runs", [])
            for r in runs:
                if r["id"] in seen or not r.get("run_started_at") or r.get("status") != "completed":
                    continue
                seen.add(r["id"])
                secs = (_ts(r["updated_at"]) - _ts(r["run_started_at"])).total_seconds()
                if r.get("conclusion") == "failure" and secs < 15:
                    continue  # refused before starting (spending limit): not billed
                if r.get("name") == "pages build and deployment":
                    continue  # GitHub Pages builds are not billed as Actions minutes
                total += max(1, math.ceil(secs / 60))
            if len(runs) < 100:
                break
            page += 1
        day = nxt
    return round(total), "estimate from runs (reads ~15 % high: switches early, never late)"


# ---------------------------------------------------------------- Modal

def modal_usd(month):
    m = LIMITS["modal"]
    p = m["profiles"]
    rate = lambda prof, secs: secs * (prof["cpu"] * m["cpu_usd_per_core_second"] +  # noqa: E731
                                      prof["gib"] * m["memory_usd_per_gib_second"])
    import state  # noqa: PLC0415
    heavy = {"listicle_factory", "carousel", "fetch_video", "competitors", "sound_scout", "render_submit",
             "drive_upload", "control_deploy"}
    usage = state.backend("d1").get("ops_usage", month) or {}
    usd, runs = 0.0, 0
    for wf, u in (usage.get("modal") or {}).items():
        usd += rate(p["heavy" if wf in heavy else "light"], float(u.get("seconds", 0)))
        runs += int(u.get("runs", 0))
    usd += runs * rate(p["endpoint_per_call"], p["endpoint_per_call"]["seconds"])
    usd += rate(p["watchdog_per_month"], p["watchdog_per_month"]["seconds"])
    for j in state.backend("d1").all("job"):   # cloud renders (tools/render/modal_app.py) share the same credits
        if str(j.get("finished_at", "")).startswith(month):
            usd += rate(p["render"], float(j.get("seconds") or 0))
    return round(usd * m["safety_factor"], 2), runs


# ---------------------------------------------------------------- Cloudflare

def r2_gb():
    import r2  # noqa: PLC0415
    if not r2.configured():
        return None
    total, token, prefixes = 0, None, {}
    c = r2._client()
    while True:
        kw = {"Bucket": r2._bucket(), "MaxKeys": 1000}
        if token:
            kw["ContinuationToken"] = token
        out = c.list_objects_v2(**kw)
        for o in out.get("Contents", []):
            total += o["Size"]
            top = o["Key"].split("/")[0]
            prefixes[top] = prefixes.get(top, 0) + o["Size"]
        if not out.get("IsTruncated"):
            break
        token = out["NextContinuationToken"]
    return round(total / 1e9, 2), {k: round(v / 1e9, 2) for k, v in sorted(prefixes.items(), key=lambda x: -x[1])}


def pages_deploys(month_start, month):
    """Control center + signup deploys this month (GitHub runs + Modal runs), against Pages' 500 builds."""
    n = 0
    for wf in ("control-deploy.yml", "signup-deploy.yml"):
        q = urllib.parse.quote(f">={month_start.strftime('%Y-%m-%d')}")
        try:
            d = _gh(f"/repos/{REPOSITORY}/actions/workflows/{wf}/runs?per_page=1&status=success&created={q}")
            n += int(d.get("total_count", 0))
        except Exception:  # noqa: BLE001
            pass
    import state  # noqa: PLC0415
    u = (state.backend("d1").get("ops_usage", month) or {}).get("modal") or {}
    n += sum(int((u.get(k) or {}).get("runs", 0)) for k in ("control_deploy", "signup_deploy"))
    return n


def ticker_age_min():
    import state  # noqa: PLC0415
    rows = state._d1("SELECT updated_at FROM docs WHERE kind = 'ops' AND id = 'ticker'", [])
    return None if not rows else round((now() - _ts(rows[0]["updated_at"])).total_seconds() / 60)


# ---------------------------------------------------------------- report

def telegram(text):
    tok, chat = os.environ.get("TELEGRAM_BOT_TOKEN"), os.environ.get("TELEGRAM_CHAT_ID")
    if DRY or not tok or not chat:
        print("TELEGRAM (not sent):", text)
        return
    data = json.dumps({"chat_id": chat, "text": text}).encode()
    req = urllib.request.Request(f"https://api.telegram.org/bot{tok}/sendMessage", data=data,
                                 headers={"Content-Type": "application/json"})
    try:
        urllib.request.urlopen(req, timeout=20).read()
    except Exception as e:  # noqa: BLE001
        print("telegram failed:", e, file=sys.stderr)


def main():
    t = now()
    month = t.strftime("%Y-%m")
    start = t.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    gh_inc = LIMITS["github"]["included_minutes"]
    m, cf = LIMITS["modal"], LIMITS["cloudflare"]
    b = {"month": month, "at": t.isoformat()[:19] + "Z"}
    problems = []

    try:
        mins, src = github_minutes(start)
        b.update(github_minutes=mins, github_included=gh_inc, github_pct=round(100 * mins / gh_inc), github_source=src)
    except Exception as e:  # noqa: BLE001
        problems.append(f"GitHub minutes unreadable: {e}")
    try:
        usd, runs = modal_usd(month)
        pct = round(100 * usd / m["monthly_credit_usd"])
        b.update(modal_usd=usd, modal_credit=m["monthly_credit_usd"], modal_pct=pct, modal_runs=runs,
                 modal_mode="off" if pct >= m["off_pct"] else "essential" if pct >= m["essential_only_pct"] else "normal")
    except Exception as e:  # noqa: BLE001
        problems.append(f"Modal usage unreadable: {e}")
        b["modal_mode"] = "normal"
    try:
        r = r2_gb()
        if r:
            b.update(r2_gb=r[0], r2_pct=round(100 * r[0] / cf["r2_storage_gb"]), r2_top=r[1])
    except Exception as e:  # noqa: BLE001
        problems.append(f"R2 size unreadable: {e}")
    try:
        n = pages_deploys(start, month)
        b.update(pages_deploys=n, pages_pct=round(100 * n / cf["pages_builds_month"]))
    except Exception as e:  # noqa: BLE001
        problems.append(f"Pages deploys unreadable: {e}")
    try:
        age = ticker_age_min()
        b["ticker_age_min"] = age
        if age is None or age > 30:
            problems.append(f"the Cloudflare ticker hasn't run for {age} min (posting falls back to the Modal watchdog)")
    except Exception as e:  # noqa: BLE001
        problems.append(f"ticker heartbeat unreadable: {e}")
    stale = subprocess.run([sys.executable, "-P", str(REPO / "tools/ticker/gen_schedules.py"), "--check"],
                           capture_output=True, text=True).returncode
    if stale:
        problems.append("tools/ticker/schedules.json no longer matches the workflow crons: run "
                        "tools/ticker/gen_schedules.py and redeploy the ticker (tools/ops/deploy.sh)")
    b["problems"] = problems

    print(json.dumps(b, indent=2))
    if DRY:
        return 0

    import state  # noqa: PLC0415
    d1 = state.backend("d1")
    d1.put("ops", "budget", b)
    sent = d1.get("ops", "alerts") or {}
    if sent.get("month") != month:
        sent = {"month": month}
    names = {"github_pct": f"GitHub Actions minutes ({b.get('github_minutes')}/{gh_inc})",
             "modal_pct": f"Modal credits (~${b.get('modal_usd')}/${m['monthly_credit_usd']})",
             "r2_pct": f"R2 storage ({b.get('r2_gb')}/{cf['r2_storage_gb']} GB)",
             "pages_pct": f"Cloudflare Pages deploys ({b.get('pages_deploys')}/{cf['pages_builds_month']})"}
    what = {"github_pct": "Timed jobs move to the Modal backup at 85 %, so posting keeps going.",
            "modal_pct": "At 75 % Modal only runs posting + approvals; at 100 % it stops until next month.",
            "r2_pct": "Old renders expire after 21 days; delete big files under the top folders if this keeps rising.",
            "pages_pct": "The control center redeploys every 6 h + on changes; a manual refresh costs one deploy."}
    for key, label in names.items():
        pct = b.get(key)
        if pct is None:
            continue
        level = max([lv for lv in LIMITS["alert_levels_pct"] if pct >= lv], default=0)
        if level and sent.get(key, 0) < level:
            extra = f" Biggest: {b.get('r2_top')}" if key == "r2_pct" else ""
            telegram(f"📊 {label} is at {pct}% of the free limit this month. {what[key]}{extra}")
            sent[key] = level
    for p in problems:
        k = "problem:" + p[:40]
        if not sent.get(k):
            telegram(f"⚠️ Free-limit watcher: {p}")
            sent[k] = 1
    d1.put("ops", "alerts", sent)
    return 0


if __name__ == "__main__":
    sys.exit(main())
