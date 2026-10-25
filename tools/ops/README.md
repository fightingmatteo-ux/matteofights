# Ops: every job has a free backup, nothing runs twice, no free limit runs out

Built 2026-10-25 after GitHub Actions ran out of minutes (3,000/month on Pro via the Student Pack) and every
posting job stopped for a day.

```
                 Cloudflare ticker (every 5 min, free)  ── the timer AND the router (tools/ticker)
                   │ heartbeat → D1 ops/ticker
                   │ mode = GitHub, unless GitHub refuses runs or is >= 85 % of its month (route.js)
          ┌────────┴─────────┐
   GitHub Actions        Modal "matteofights-ops" (tools/ops/modal_ops.py, $30/month free credits)
   (primary)             runs the SAME .github/workflows/*.yml through tools/ops/runner.py
          └────────┬─────────┘
                   │ both: clone, run, git push, D1 state; posting jobs hold a D1 lease (tools/ops/lock.py)
           Dashboard + Telegram approvals route the same way (control-site/lib/shared.js)
```

## Rules this guarantees
- **One definition.** A job is its workflow file. The backup interprets that file (runner.py); there is no
  second copy to drift. `python3 -P tools/ops/runner.py check` lists what can run outside GitHub (all but the two
  Claude-powered writers, edit-worker and talking-points, which wait for GitHub).
- **Never twice.** The ticker sends each job to ONE runner. On a switch to Modal it disables GitHub's own
  scheduled workflows (and re-enables them on the way back). Post queue and Cross-post also hold a D1 lease, so even
  a late GitHub cron can't double-post. A scheduled job is never re-sent as a manual GitHub run (wrong inputs).
- **Failover in 5 minutes.** Every GitHub dispatch is remembered (D1 ops_pending). If GitHub refuses it (billing)
  or never starts it, the next tick sends it to Modal and marks GitHub blocked for 6 h, then quietly re-checks.
- **The ticker has a backup too.** Modal's `watchdog` (every 30 min) runs Post queue + Cross-post itself if the
  ticker's heartbeat is 20+ min old.
- **Limits watched.** `tools/ops/budget.py` (in Health check, every 6 h) measures GitHub minutes, Modal credits,
  R2 storage, Pages deploys, the ticker heartbeat and schedules.json freshness; writes D1 ops/budget; Telegram at
  70/85/95 %. Router moves timed jobs to Modal at GitHub 85 %; Modal takes only posting + approvals at 75 % of its
  credits and stops at 100 %. All limits and prices: `tools/ops/limits.json`.

## Deploy / update (laptop)
`bash tools/ops/deploy.sh` (idempotent). After any token refresh: `bash tools/ops/sync-secrets.sh --github`.

## Change something
| Change | Do |
|---|---|
| A workflow's steps | Just edit the workflow. Both runners use it. |
| A workflow's cron | Edit it, run `python3 -P tools/ticker/gen_schedules.py`, redeploy the ticker (`deploy.sh`). budget.py warns if you forget. |
| A new secret | Add it to GitHub AND a `secrets/*.env` file, then `sync-secrets.sh`. |
| A new workflow | Never on every push, never more often than every 3 h (CLAUDE.md rule). Timed work goes through the ticker. |

## Tests
`python3 -P tools/ops/test_runner.py` · `python3 -P tools/ops/test_lock.py` · `python3 -P tools/ops/test_budget.py` ·
`cd tools/ticker && node --test due.test.js route.test.js` · `bash tools/ticker/sim/run.sh` (end-to-end failover).
