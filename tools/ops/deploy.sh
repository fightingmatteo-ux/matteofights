#!/usr/bin/env bash
# One command, on the laptop (Git Bash), from the repo root:   bash tools/ops/deploy.sh
#
# Sets up / updates the free backup for every job and the router in front of it. Safe to run again any time.
#   1. secrets/ops.env: the shared OPS_TOKEN (created once)
#   2. Modal secret "matteofights-ops" from secrets/*.env (tools/ops/sync-secrets.sh)
#   3. Modal app "matteofights-ops" (tools/ops/modal_ops.py) -> its URL saved to secrets/ops.env
#   4. tools/ticker/schedules.json regenerated from the workflow files
#   5. Cloudflare ticker: secrets + deploy (the router)
#   6. Control center (Pages): OPS_URL/OPS_TOKEN so dashboard + Telegram approvals fail over too
#   7. Kicks off, on Modal: Health check (fills the budget numbers the router reads) and Deploy control center
# Needs (already on this laptop for the existing setup): python + modal login, node/npx, gh login, secrets/*.env.
set -euo pipefail
export PYTHONUTF8=1 PYTHONIOENCODING=utf-8
cd "$(dirname "$0")/../.."
step() { printf '\n== %s\n' "$*"; }

step "1/7 shared token"
if ! grep -q '^OPS_TOKEN=' secrets/ops.env 2>/dev/null; then
  mkdir -p secrets
  echo "OPS_TOKEN=$(python -c 'import secrets;print(secrets.token_urlsafe(32))')" >> secrets/ops.env
  echo "created secrets/ops.env"
fi
set -a; . secrets/ops.env; [ -f secrets/control.env ] && . secrets/control.env; set +a
export CLOUDFLARE_API_TOKEN="${CLOUDFLARE_API_TOKEN:-${CLOUDFLARE_BUILD_TOKEN:-}}"
export CLOUDFLARE_ACCOUNT_ID="${CLOUDFLARE_ACCOUNT_ID:-$(python -c "import json;print(json.load(open('tools/cloud/cloud.json'))['account_id'])")}"

step "2/7 Modal secret"
python -m pip install -q -U modal pyyaml
bash tools/ops/sync-secrets.sh

step "3/7 Modal app"
python -m modal deploy tools/ops/modal_ops.py | tee /tmp/modal-ops-deploy.log
URL=$(grep -oE 'https://[A-Za-z0-9-]+--matteofights-ops-ops[A-Za-z0-9-]*\.modal\.run' /tmp/modal-ops-deploy.log | head -1)
[ -n "$URL" ] || { echo "Couldn't find the endpoint URL in the deploy output above"; exit 1; }
grep -v '^OPS_URL=' secrets/ops.env > secrets/ops.env.tmp || true
echo "OPS_URL=$URL" >> secrets/ops.env.tmp && mv secrets/ops.env.tmp secrets/ops.env
export OPS_URL="$URL"
curl -fsS "$URL/health" && echo "  endpoint up: $URL"

step "4/7 schedules"
python -P tools/ticker/gen_schedules.py

step "5/7 Cloudflare ticker (router)"
(
  cd tools/ticker
  for s in OPS_URL OPS_TOKEN TELEGRAM_BOT_TOKEN TELEGRAM_CHAT_ID; do
    [ -n "${!s:-}" ] && printf '%s' "${!s}" | npx --yes wrangler@4 secret put "$s" > /dev/null && echo "  $s set"
  done
  npx --yes wrangler@4 deploy
)

step "6/7 Control center failover secrets"
for s in OPS_URL OPS_TOKEN; do
  printf '%s' "${!s}" | npx --yes wrangler@4 pages secret put "$s" --project-name matteo-control > /dev/null && echo "  $s set"
done

step "7/7 first runs on Modal"
for wf in health.yml control-deploy.yml; do
  curl -fsS -X POST "$URL/dispatch" -H "Authorization: Bearer $OPS_TOKEN" -H "Content-Type: application/json" \
    -d "{\"workflow\":\"$wf\"}" && echo
done

cat <<EOF

Done. The ticker now routes every job: GitHub while it has minutes, the Modal backup when it doesn't (or refuses
runs), and it switches GitHub's own timers off while Modal has the jobs so nothing runs twice. Telegram tells you
on every switch and at 70/85/95 % of any free limit. Watch it: Modal dashboard -> app matteofights-ops -> logs.
After any token refresh: bash tools/ops/sync-secrets.sh
EOF
