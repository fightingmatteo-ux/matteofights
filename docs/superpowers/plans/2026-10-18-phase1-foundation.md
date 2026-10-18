# Phase 1: Foundation (R2, D1, state layer, Modal renders, ticker) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Live state moves from committed JSON into D1, media into R2, renders onto Modal, and posting timing onto the Cloudflare ticker, while the current system keeps working until each piece is verified.

**Architecture:** One Python module (`tools/state.py`) is the only way scripts read/write live state; it has a `file` backend (today's JSON files) and a `d1` backend (Cloudflare D1 HTTP API), switched by `STATE_BACKEND`. One module (`tools/r2.py`) wraps R2 (S3 API). A Modal app renders a tarred reel folder from R2 and writes the MP4 back. The ticker Worker reads due items from D1 and dispatches GitHub workflows.

**Tech Stack:** Python 3.12 stdlib + `boto3` (R2) + `modal`; Cloudflare D1, R2, Workers (free plan), wrangler 3; HyperFrames 0.8.147, ffmpeg; pytest; `node --test` for the Worker.

**Spec:** `docs/superpowers/specs/2026-10-18-run-from-anywhere-design.md`. Later phases (dashboard, health check, lean setup, site move) get their own plans.

## Global Constraints

- Cost: free to test; fully automatic under $10/month. Cloudflare **free plan** only. Nothing renders on GitHub runners.
- Claude usage in automation: none in this phase.
- Never set `approved:true` from automation. Only `control.py` (Matteo's hold-to-approve) may.
- Never commit `secrets/`, `data.json`, `covers/`, `voice.wav`, `snaps/`, footage or renders.
- Commit only your own paths (other sessions and bots commit concurrently): `git add <paths>`, never `-a`.
- Python scripts run as `python3 -P`; JSON written with `ensure_ascii=False, indent=2` + trailing newline (existing style).
- Old path stays working until the cutover task; every task before Task 8 must leave `STATE_BACKEND` unset = `file`.
- Secrets: Cloudflare build token `CLOUDFLARE_BUILD_TOKEN` in `secrets/control.env`; Modal `MODAL_TOKEN_ID`/`MODAL_TOKEN_SECRET` in `secrets/modal.env`. Setting GitHub/Worker/Modal secrets from those files is a command Matteo runs (the auto-mode classifier blocks Claude from piping secrets); each such step prints the exact command for him.
- Copy rules: no em dashes in any user-facing text.

## Review Focus

1. **Two workflows patch the same queue item at once** (post-queue sets `status`, control sets `approved`): neither change may be lost. `state.patch` must update only the given fields (D1 `json_set`), never rewrite the whole doc. Test in Task 2.
2. **State write fails right after a successful Instagram post:** the item must not be posted twice. `run_queue` marks `status:"posting"` before the API call and never picks `posting` items. Test in Task 3.
3. **Instagram fetches the video minutes after we hand it a presigned R2 URL:** URL must still be valid; expiry ≥ 6 h. Test in Task 5.
4. **A Modal render fails or times out halfway:** no partial file may appear at `renders/<asset>`; job ends `failed` with the error. Render to a temp key, copy on success. Verified in Task 6.
5. **Captions with emoji, Thai or curly quotes** round-trip through D1 unchanged. Test in Task 2.

---

### Task 1: Cloudflare resources (R2 bucket, D1 database, schema)

**Files:**
- Create: `tools/cloud/schema.sql`, `tools/cloud/setup.sh`, `tools/cloud/cloud.json` (non-secret ids), `tools/cloud/README.md`

**Interfaces:**
- Produces: R2 bucket `matteofights-media` (CORS: PUT/GET from `https://control.matteofights.me`, `https://matteo-control.pages.dev`); D1 database `matteofights` with table `docs`; `tools/cloud/cloud.json` = `{"account_id": "849fbd13419572f8d5e345f23dd3de11", "d1_database_id": "<uuid>", "r2_bucket": "matteofights-media", "r2_endpoint": "https://849fbd13419572f8d5e345f23dd3de11.r2.cloudflarestorage.com"}`.

- [ ] **Step 1:** Write `schema.sql`:

```sql
CREATE TABLE IF NOT EXISTS docs (
  kind TEXT NOT NULL,          -- queue | queue_meta | crosspost | job | upload | broll | talking_point | stat | health | token
  id   TEXT NOT NULL,
  data TEXT NOT NULL,          -- JSON object
  updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
  PRIMARY KEY (kind, id)
);
CREATE INDEX IF NOT EXISTS docs_kind_updated ON docs(kind, updated_at);
```

- [ ] **Step 2:** `setup.sh` (idempotent; reads `CLOUDFLARE_BUILD_TOKEN` from `secrets/control.env` as `CLOUDFLARE_API_TOKEN` for wrangler): `wrangler r2 bucket create`, `wrangler r2 bucket cors set` (from an inline JSON file), `wrangler d1 create` (skip if exists), `wrangler d1 execute matteofights --remote --file tools/cloud/schema.sql`, then writes `cloud.json`. Also creates an R2 S3 API token is **not** possible via wrangler: print the dashboard link and the exact names `R2_ACCESS_KEY_ID`/`R2_SECRET_ACCESS_KEY` for Matteo to add to `secrets/control.env` (scope: Object Read & Write, bucket `matteofights-media` only).
- [ ] **Step 3: Verify:** `npx wrangler@3 r2 bucket list` shows `matteofights-media`; `npx wrangler@3 d1 execute matteofights --remote --command "select count(*) from docs"` returns 0.
- [ ] **Step 4: Commit** `tools/cloud/`.

### Task 2: State layer `tools/state.py`

**Files:**
- Create: `tools/state.py`, `tests/test_state.py`, `tests/conftest.py` (adds `tools/` to `sys.path`)

**Interfaces:**
- Produces:
  - `get(kind: str, id: str) -> dict | None`
  - `all(kind: str) -> list[dict]` (each dict includes `"id"`; ordered by id)
  - `put(kind: str, id: str, data: dict) -> None` (replace)
  - `patch(kind: str, id: str, fields: dict) -> None` (field-level merge; creates if missing)
  - `delete(kind: str, id: str) -> None`
  - `backend(name: str) -> Backend` (`"file"`|`"d1"`; object with the same five methods; module-level functions delegate to the env-selected one)
  - Backend from env `STATE_BACKEND` = `file` (default) | `d1`. D1 config from `tools/cloud/cloud.json` + env `CLOUDFLARE_D1_TOKEN` (falls back to `CLOUDFLARE_BUILD_TOKEN`).
  - File backend mapping: `queue` ↔ `production/schedule/queue.json["items"]` (by `id`), `queue_meta` id `_how` ↔ its `_how` key, `crosspost` ↔ `production/schedule/crosspost.json` (top-level keys = ids; check the file's shape before writing and keep it identical on save). Other kinds ↔ `production/state/<kind>.json` (dict by id).
  - D1 backend: one function `_d1(sql: str, params: list) -> list[dict]` POSTing to `/accounts/{account_id}/d1/database/{db}/query`; `patch` uses `INSERT ... ON CONFLICT DO UPDATE SET data = json_patch(docs.data, ?)` so concurrent patches to different fields both survive.

- [ ] **Step 1: Write failing tests** (file backend against a temp copy of the repo's schedule dir via `STATE_ROOT` env; D1 backend against a fake `_d1` that runs the same SQL on an in-memory `sqlite3`, which supports `json_patch`):
  - `test_file_roundtrip_queue_keeps_shape`: `put` then reload file → `_how` preserved, item order preserved, other items byte-identical.
  - `test_patch_merges_fields` (both backends): `patch(q,"x",{"status":"posted"})` then `patch(q,"x",{"approved":True})` → both fields set.
  - `test_unicode_roundtrip` (both): caption `"Some people train for fun. 🥊 มวยไทย “quotes”"` comes back equal.
  - `test_get_missing_returns_none`, `test_all_sorted_by_id`.
- [ ] **Step 2:** `pytest tests/test_state.py -v` → FAIL (module missing).
- [ ] **Step 3:** Implement `tools/state.py` (stdlib only: `urllib`, `json`, `os`, `pathlib`).
- [ ] **Step 4:** `pytest tests/test_state.py -v` → all PASS.
- [ ] **Step 5: Commit** `tools/state.py tests/`.

### Task 3: Scripts read/write through `state`

**Files:**
- Modify: `tools/instagram/run_queue.py` (load at :36, `save` at :74), `tools/crosspost/crosspost.py` (`STATE`/`QUEUE` reads at :471-472, `save_state` at :380), `tools/control/control.py` (queue reads at :56, :61 and its writer), `tools/control/build_data.py` (queue/crosspost reads)
- Test: `tests/test_run_queue.py`

**Interfaces:**
- Consumes: `state.get/all/put/patch` (Task 2).
- Produces: no new public names. Behavior with `STATE_BACKEND=file` is identical to today.

- [ ] **Step 1: Write failing tests** for `run_queue` with the IG API stubbed (monkeypatch its HTTP helper):
  - `test_skips_unapproved_and_not_due` (existing rule).
  - `test_marks_posting_before_api_call`: stub raises after the publish call succeeds-then-state-fails; assert item status in state is `"posting"`, and a second run does not call publish for it.
  - `test_posting_item_is_never_picked`.
- [ ] **Step 2:** Run → FAIL.
- [ ] **Step 3:** Replace direct JSON reads/writes in the four scripts with `state` calls; in `run_queue`, `state.patch("queue", id, {"status": "posting"})` before publishing, final `patch` with `status`, `media_id`, `posted_at`. A `posting` item older than 2 h becomes a "needs you" item later (Phase 3); here it is just skipped.
- [ ] **Step 4:** `pytest tests -v` → PASS. Then dry check: `STATE_BACKEND=file python3 -P tools/control/build_data.py` produces the same `data.json` as before (`git diff --stat` shows no change to tracked files other than the scripts).
- [ ] **Step 5: Commit** the four scripts + test.

### Task 4: Mirror files → D1 and compare

**Files:**
- Create: `tools/state_mirror.py`
- Modify: `.github/workflows/post-queue.yml`, `crosspost.yml`, `control.yml`, `listicle-factory.yml` (add a final step)

**Interfaces:**
- Consumes: `state` with both backends.
- Produces: CLI `python3 -P tools/state_mirror.py push` (file → D1, all kinds that exist in files) and `python3 -P tools/state_mirror.py compare` (exit 1 and print differing `kind/id` if D1 ≠ files).

- [ ] **Step 1:** Implement both commands with `state.backend("file")` and `state.backend("d1")` side by side.
- [ ] **Step 2:** Test `tests/test_state_mirror.py::test_push_then_compare_clean` (file → fake D1 → compare exit 0) and `::test_compare_reports_diff`.
- [ ] **Step 3:** Add workflow step `Mirror state to D1` (`continue-on-error: true`, env `CLOUDFLARE_D1_TOKEN: ${{ secrets.CLOUDFLARE_D1_TOKEN }}`) after each workflow's commit step. Print for Matteo: `gh secret set CLOUDFLARE_D1_TOKEN` (value = the build token or a D1-only token).
- [ ] **Step 4: Verify:** run `push` locally, then `compare` → exit 0; `select kind, count(*) from docs group by kind` shows queue and crosspost counts equal to the files.
- [ ] **Step 5: Commit.**

### Task 5: R2 helper + media goes to R2

**Files:**
- Create: `tools/r2.py`, `tests/test_r2.py`
- Modify: `tools/video/media.sh` (`push` also uploads to R2 `renders/<name>`), `tools/instagram/run_queue.py` + `tools/crosspost/crosspost.py` (video URL resolution)

**Interfaces:**
- Produces: `put_file(key: str, path: str) -> None`, `get_file(key: str, path: str) -> None`, `exists(key: str) -> bool`, `presign_get(key: str, expires: int = 21600) -> str`, `presign_put(key: str, expires: int = 3600) -> str`, `copy(src: str, dst: str) -> None`, `delete(key: str) -> None`; and `video_url(asset: str) -> str` = presigned `renders/<asset>` if it exists in R2, else today's media-release URL. Config: `cloud.json` + env `R2_ACCESS_KEY_ID`/`R2_SECRET_ACCESS_KEY`.

- [ ] **Step 1: Failing tests** with a stub client: `test_presign_default_expiry_at_least_6h` (parse `X-Amz-Expires` ≥ 21600), `test_video_url_prefers_r2`, `test_video_url_falls_back_to_release`.
- [ ] **Step 2:** Run → FAIL. **Step 3:** Implement with `boto3` (`endpoint_url` from cloud.json, `region_name="auto"`, signature v4). **Step 4:** PASS.
- [ ] **Step 5: Verify live:** `python3 -P -c "import sys;sys.path.insert(0,'tools');import r2;r2.put_file('renders/saenchai-bigger-men-A.mp4','media/2026-10-16-saenchai-bigger-men/renders/saenchai-bigger-men-A.mp4');print(r2.presign_get('renders/saenchai-bigger-men-A.mp4'))"` and `curl -sI <url>` → 200, `content-length` 28117553.
- [ ] **Step 6:** Workflows that post: add `pip install boto3` and env `R2_ACCESS_KEY_ID`/`R2_SECRET_ACCESS_KEY` secrets (print Matteo's `gh secret set` commands). **Commit.**

### Task 6: Modal render app

**Files:**
- Create: `tools/render/modal_app.py`, `tools/render/submit.py`, `tools/render/README.md`, `.github/workflows/render-deploy.yml`

**Interfaces:**
- Consumes: `r2` (Task 5), `state` (Task 2, kind `job`).
- Produces:
  - Job doc `job/<job_id>`: `{"reel": str, "variant": str, "asset": str, "status": "queued|rendering|done|failed", "error": str|None, "bundle": "jobs/<job_id>/bundle.tar.gz", "started_at", "finished_at", "seconds": int}`.
  - `submit.py <reel_dir> <variant> [--asset NAME] [--prep-cmd "..."]`: runs the reel's prep (Saenchai: `python -P make_broll.py V && python -P build_variant.py V`), tars the reel folder excluding `snaps/ work/ *.py render.sh node_modules`, uploads bundle, creates job doc, calls the Modal start endpoint, prints the job id.
  - Modal app `matteofights-render`: `render(job_id: str)` (cpu=4, memory=12288 MiB, timeout=7200) and web endpoint `POST /start {"job_id"}` requiring header `Authorization: Bearer <RENDER_SECRET>` → `render.spawn(job_id)`.
  - Render steps: download + untar to `/work`; `npx --yes hyperframes@0.8.147 render -q delivery -w 4 -o raw.mp4`; `ffmpeg -c:v libx264 -crf 22 -preset slow -c:a copy -movflags +faststart` → phone mp4; upload to `renders/tmp/<job_id>.mp4`, then `copy` to `renders/<asset>` and delete tmp; patch job `done` + `seconds`. Any exception → patch `failed` + error text (last 2,000 chars), no copy.
  - Image: `modal.Image.debian_slim(python_version="3.12")` + apt `ffmpeg`, Chrome runtime libs, `nodejs` 20 + `boto3`; copies `tools/state.py`, `tools/r2.py`, `tools/cloud/cloud.json`. Secrets from Modal secret `matteofights` (R2 keys, D1 token, `RENDER_SECRET`).

- [ ] **Step 1:** Implement both files. Print for Matteo: `modal secret create matteofights R2_ACCESS_KEY_ID=… R2_SECRET_ACCESS_KEY=… CLOUDFLARE_D1_TOKEN=… RENDER_SECRET=…` (values from his env files; he runs it) and `modal deploy tools/render/modal_app.py`.
- [ ] **Step 2: Verify on a real reel:** `python3 -P tools/render/submit.py production/reels/2026-10-16-saenchai-bigger-men B --asset saenchai-bigger-men-B.mp4`; poll `state.get("job", id)` until `done`; `ffprobe` the R2 file: 1080x1920, duration within 0.5 s of `work/edl_B.json` total; run `verify_cut.py` on it → pass. Record `seconds`.
- [ ] **Step 3: Verify failure path:** submit a bundle with a broken `index.html` → job `failed`, `r2.exists("renders/<asset>")` unchanged from before.
- [ ] **Step 4:** Repeat Step 2 for C. Push both to the media release too (`media.sh push`) so the old path has them.
- [ ] **Step 5:** `render-deploy.yml`: on push to `tools/render/**`, `pip install modal && modal deploy tools/render/modal_app.py` with `MODAL_TOKEN_ID`/`MODAL_TOKEN_SECRET` secrets. **Commit.**

### Task 7: Ticker on D1

**Files:**
- Modify: `tools/ticker/worker.js`, `tools/ticker/wrangler.toml`
- Create: `tools/ticker/due.js`, `tools/ticker/due.test.js`

**Interfaces:**
- Consumes: D1 binding `DB` (database `matteofights`).
- Produces: `due.js` exports `slotDue(nowMs: number, slots: string, tz = "America/New_York") -> boolean` and `queueDue(nowMs: number, items: object[]) -> boolean` (an item is due when `approved === true`, `status` not in `posted|posting|failed`, `not_before <= now`). Worker dispatches `post-queue.yml` when `slotDue(POST_SLOTS) || queueDue(items)` and `crosspost.yml` on `slotDue(XPOST_SLOTS)`. If the D1 read throws, it falls back to slots only and logs it.

- [ ] **Step 1: Failing tests** (`node --test tools/ticker/`): slot exactly at `12:31` NY → true; `12:35:59` → true; `12:36` → false; DST day (2026-11-01) still maps correctly; `queueDue` false for unapproved, for `posting`, true for approved+due.
- [ ] **Step 2:** FAIL. **Step 3:** Implement. **Step 4:** PASS.
- [ ] **Step 5: Deploy:** add `[[d1_databases]] binding = "DB"` to wrangler.toml; `npx wrangler@3 deploy` (token: build token). Print for Matteo: `npx wrangler@3 secret put GH_TOKEN` (value = `GITHUB_TOKEN` from `secrets/control.env`, the existing PAT, verified working 2026-10-18).
- [ ] **Step 6: Verify:** `npx wrangler@3 tail matteo-ticker` shows a tick within 5 min; at the next slot the Actions list shows a `workflow_dispatch` run of the right workflow. **Commit.**

### Task 8: Cutover and cleanup

**Files:**
- Modify: the four workflows from Task 4; `.github/workflows/control-deploy.yml`; `STATUS.md`; `CLAUDE.md` (routing row for `tools/cloud/README.md`, `tools/render/README.md`)

- [ ] **Step 1:** Precondition: `state_mirror.py compare` has been clean on 3 consecutive days of workflow runs (check run logs). If not, stop and report.
- [ ] **Step 2:** Set `STATE_BACKEND: d1` in those workflows; remove their `git add production/schedule/queue.json|crosspost.json` commits (D1 is now the truth); add a nightly `state_export.py` step that writes D1 → the JSON files and commits them as a readable backup only (`state_mirror.py pull`, add this command).
- [ ] **Step 3:** GitHub `schedule:` triggers for post-queue and crosspost → `0 */3 * * *` (backup only). `control-deploy.yml`: `on.push.paths: ["control-site/**", "tools/control/**"]`, drop `workflow_run`.
- [ ] **Step 4: Verify** over the next posting slot: item posted via ticker dispatch, D1 shows `posted`, no commit to queue.json from the posting run, nightly export commit appears.
- [ ] **Step 5:** Update STATUS.md (ticker done, Saenchai B/C rendered via Modal, cloud setup) and commit.

---

## Next plans (not in this one)

Phase 2 dashboard (live D1 data, upload to R2, pipeline, reel screen, push, momentum/reveal/bank, uploader login, delete `dashboard/`); Phase 3 scripted health check + Claude escalation + token-expiry tracking + talking-point matching plan job + listicle factory on Modal; Phase 4 lean Claude setup + site move to Cloudflare Pages + retire media release and Drive.
