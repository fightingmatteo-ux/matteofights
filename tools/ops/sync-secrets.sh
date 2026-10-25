#!/usr/bin/env bash
# Copy every secret the workflows use from the laptop's secrets/*.env into the Modal secret "matteofights-ops",
# so the backup runner posts with the SAME tokens as GitHub. Run it after ANY token refresh
# (ig.py refresh, crosspost.py threads-refresh, a new FB/YouTube token), and tools/ops/deploy.sh runs it too.
#
#   bash tools/ops/sync-secrets.sh            # Modal only (safe default)
#   bash tools/ops/sync-secrets.sh --github   # also overwrite the GitHub secrets with the laptop values
#
# Names = every ${{ secrets.X }} in .github/workflows, so a new secret in a workflow is picked up automatically.
set -euo pipefail
export PYTHONUTF8=1 PYTHONIOENCODING=utf-8
cd "$(dirname "$0")/../.."
set -a
for f in secrets/control.env secrets/meta.env secrets/crosspost.env secrets/modal.env secrets/ops.env; do
  [ -f "$f" ] && . "$f"
done
set +a

# the same aliases tools/cloud/set-secrets.sh uses, plus the runner's own
: "${CLOUDFLARE_D1_TOKEN:=${CLOUDFLARE_BUILD_TOKEN:-}}"
: "${CLOUDFLARE_API_TOKEN:=${CLOUDFLARE_BUILD_TOKEN:-}}"
: "${CLOUDFLARE_ACCOUNT_ID:=$(python -c "import json;print(json.load(open('tools/cloud/cloud.json'))['account_id'])")}"
: "${IG_ACCESS_TOKEN:=${IG_GRAPH_ACCESS_TOKEN:-}}"
[ -z "${IG_COOKIES:-}" ] && [ -f secrets/ig_cookies.txt ] && IG_COOKIES="$(cat secrets/ig_cookies.txt)"
[ -z "${YT_COOKIES:-}" ] && [ -f secrets/yt_cookies.txt ] && YT_COOKIES="$(cat secrets/yt_cookies.txt)"
[ -z "${RCLONE_CONF:-}" ] && for c in "$HOME/.config/rclone/rclone.conf" "$APPDATA/rclone/rclone.conf"; do
  [ -f "$c" ] && RCLONE_CONF="$(cat "$c")" && break; done
# push access for the runner's clone: the gh CLI login (not the limited dashboard PAT in control.env)
RUNNER_GH_TOKEN="$(env -u GITHUB_TOKEN -u GH_TOKEN gh auth token)"
: "${OPS_TOKEN:?missing: run tools/ops/deploy.sh (it creates secrets/ops.env)}"

names=$(grep -ohE 'secrets\.[A-Z0-9_]+' .github/workflows/*.yml | sed 's/secrets\.//' | sort -u)
args=() missing=()
for n in $names RUNNER_GH_TOKEN OPS_TOKEN; do
  v="${!n:-}"
  if [ -n "$v" ]; then args+=("$n=$v"); else missing+=("$n"); fi
done
python -m modal secret create matteofights-ops --force "${args[@]}" > /dev/null
echo "Modal secret matteofights-ops: ${#args[@]} values set."

if [ "${1:-}" = "--github" ]; then
  for kv in "${args[@]}"; do
    n="${kv%%=*}"
    case "$n" in RUNNER_GH_TOKEN|OPS_TOKEN) continue;; esac
    printf '%s' "${kv#*=}" | env -u GITHUB_TOKEN -u GH_TOKEN gh secret set "$n" --repo fightingmatteo-ux/matteofights
  done
  echo "GitHub secrets updated from the laptop values."
fi

if [ ${#missing[@]} -gt 0 ]; then
  echo "Not on this laptop, so the Modal backup doesn't have them: ${missing[*]}"
  echo "  (jobs needing them still run on GitHub; add the value to a secrets/*.env file and run this again)"
fi
