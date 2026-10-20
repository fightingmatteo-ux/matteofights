#!/usr/bin/env bash
# Idempotent: creates the R2 bucket (+ CORS), the D1 database and its schema, then writes cloud.json.
# Uses the Cloudflare REST API with CLOUDFLARE_BUILD_TOKEN from secrets/control.env.
set -euo pipefail
cd "$(dirname "$0")/../.."
set -a; . secrets/control.env; set +a
: "${CLOUDFLARE_BUILD_TOKEN:?missing in secrets/control.env}"

ACCOUNT=849fbd13419572f8d5e345f23dd3de11
BUCKET=matteofights-media
DB=matteofights
API="https://api.cloudflare.com/client/v4/accounts/$ACCOUNT"

cf() { # cf METHOD PATH [JSON]
  curl -sS -X "$1" "$API$2" -H "Authorization: Bearer $CLOUDFLARE_BUILD_TOKEN" \
    -H "Content-Type: application/json" ${3:+--data "$3"}
}
ok() { python -c "import sys,json;d=json.load(sys.stdin);sys.exit(0 if d.get('success') else (print(d.get('errors'),file=sys.stderr) or 1))"; }

# R2 bucket
if cf GET "/r2/buckets/$BUCKET" | ok 2>/dev/null; then echo "bucket $BUCKET exists"
else cf POST /r2/buckets "{\"name\":\"$BUCKET\"}" | ok && echo "bucket $BUCKET created"; fi

cf PUT "/r2/buckets/$BUCKET/cors" '{"rules":[{"allowed":{"origins":["https://control.matteofights.me","https://matteo-control.pages.dev"],"methods":["GET","PUT"],"headers":["*"]},"exposeHeaders":["ETag"],"maxAgeSeconds":3600}]}' | ok
echo "cors set"

# Keep under the 10 GB free tier: job bundles 2 days, half-uploaded render parts 1 day, renders 21 days
# (every platform has posted a reel within a week; the media release keeps anything pushed with media.sh).
rule() { echo "{\"id\":\"$1\",\"enabled\":true,\"conditions\":{\"prefix\":\"$2\"},\"deleteObjectsTransition\":{\"condition\":{\"type\":\"Age\",\"maxAge\":$(( $3 * 86400 ))}}}"; }
cf PUT "/r2/buckets/$BUCKET/lifecycle" "{\"rules\":[$(rule jobs jobs/ 2),$(rule render-tmp renders/tmp/ 1),$(rule renders renders/ 21)]}" | ok
echo "lifecycle set"

# D1 database
DB_ID=$(cf GET "/d1/database?name=$DB" | python -c "import sys,json;r=[d for d in json.load(sys.stdin)['result'] if d['name']=='$DB'];print(r[0]['uuid'] if r else '')")
if [ -z "$DB_ID" ]; then
  DB_ID=$(cf POST /d1/database "{\"name\":\"$DB\"}" | python -c "import sys,json;print(json.load(sys.stdin)['result']['uuid'])")
  echo "database $DB created"
else echo "database $DB exists"; fi

SQL=$(python -c "import json;print(json.dumps({'sql':open('tools/cloud/schema.sql',encoding='utf-8').read()}))")
cf POST "/d1/database/$DB_ID/query" "$SQL" | ok
echo "schema applied"

cat > tools/cloud/cloud.json <<JSON
{
  "account_id": "$ACCOUNT",
  "d1_database_id": "$DB_ID",
  "r2_bucket": "$BUCKET",
  "r2_endpoint": "https://$ACCOUNT.r2.cloudflarestorage.com"
}
JSON
echo "wrote tools/cloud/cloud.json"

cat <<MSG

One manual step (wrangler cannot create S3 keys):
  dash.cloudflare.com -> R2 -> Manage API Tokens -> Create API token
  Permission: Object Read & Write, bucket: $BUCKET only
  Add to secrets/control.env:
    R2_ACCESS_KEY_ID=...
    R2_SECRET_ACCESS_KEY=...
MSG
