# Cloud resources (Cloudflare)

- R2 bucket `matteofights-media` (videos, render bundles). CORS: GET/PUT from the control center.
- D1 database `matteofights`, one table `docs(kind, id, data JSON, updated_at)`. See `schema.sql`.
- Non-secret ids: `cloud.json`. Read by `tools/state.py` and `tools/r2.py`.

`bash tools/cloud/setup.sh` creates or updates all of it (safe to rerun). It uses
`CLOUDFLARE_BUILD_TOKEN` from `secrets/control.env` (D1, R2, Workers Scripts: Edit).

R2 S3 keys (`R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`) live in `secrets/control.env`;
created in the dashboard under R2 → Manage API Tokens, scoped to this bucket only.

Check:
    CLOUDFLARE_API_TOKEN=$CLOUDFLARE_BUILD_TOKEN npx wrangler@3 d1 execute matteofights --remote --command "select kind, count(*) from docs group by kind"

## Which side is the truth

`"state_backend"` in `cloud.json` (missing = `file`). While `file`: the JSON files in production/schedule are
the truth and every state workflow runs `state_mirror.py sync` (files to D1 + compare). Set it to `d1` for the
cutover: scripts read and write D1, sync stops, and the "State backup" workflow writes D1 back into the files
every night. Scripts never touch the queue files directly; they use `tools/state.py`.

## Keys in cloud sessions (any device)

`python -P tools/cloud/env_block.py` on the laptop copies every key in `secrets/*.env` to the clipboard; paste it
into claude.ai/code > environment menu > Edit > Environment variables. Scripts read env vars first, so cloud sessions
(phone, browser, any laptop) then work with no `secrets/` folder. Rerun and repaste after a token refresh. Gypsy
Amazon has the same script (`tools/env_block.py`) and needs its OWN environment: same names, different accounts.

R2 keeps job bundles 2 days and renders 21 days (lifecycle rules in setup.sh).
