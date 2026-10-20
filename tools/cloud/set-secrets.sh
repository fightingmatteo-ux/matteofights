#!/usr/bin/env bash
# Matteo runs this once (Claude's safety check blocks it from piping secrets). Values come from secrets/*.env.
set -euo pipefail
cd "$(dirname "$0")/../.."
set -a; . secrets/control.env; . secrets/modal.env; set +a

for pair in "CLOUDFLARE_D1_TOKEN:$CLOUDFLARE_BUILD_TOKEN" "R2_ACCESS_KEY_ID:$R2_ACCESS_KEY_ID" \
            "R2_SECRET_ACCESS_KEY:$R2_SECRET_ACCESS_KEY" "MODAL_TOKEN_ID:$MODAL_TOKEN_ID" \
            "MODAL_TOKEN_SECRET:$MODAL_TOKEN_SECRET" "RENDER_SECRET:$RENDER_SECRET"; do
  # env -u: use gh's own login, not the limited GITHUB_TOKEN PAT that control.env just exported
  printf '%s' "${pair#*:}" | env -u GITHUB_TOKEN -u GH_TOKEN gh secret set "${pair%%:*}" --repo fightingmatteo-ux/matteofights
done

python -m modal secret create matteofights --force \
  R2_ACCESS_KEY_ID="$R2_ACCESS_KEY_ID" R2_SECRET_ACCESS_KEY="$R2_SECRET_ACCESS_KEY" \
  CLOUDFLARE_D1_TOKEN="$CLOUDFLARE_BUILD_TOKEN" RENDER_SECRET="$RENDER_SECRET"
echo "done: 6 GitHub secrets + Modal secret 'matteofights'"
