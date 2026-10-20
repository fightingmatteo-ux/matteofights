# Cloud renders (Modal)

Render a reel variant on Modal instead of this PC (8 CPUs, about 7-9 min for an editorial talking head):

    python -P tools/render/submit.py production/reels/<slug> <V> [--include <repo path> ...] [--wait]

- Packs the reel folder + `production/editing/reel-kit` + every `--include` (footage, music the build reads
  from outside the reel folder) and uploads it to R2 `jobs/`. Other variants' a-roll/cut-out and b-roll clips
  that make_broll.py rebuilds are left out.
- Runs the reel's own `bash make.sh <V>` on Modal (`--cmd` to change). Outputs
  `media/<slug>/<slug>-<V>.mp4` + `-phone.mp4` go to R2 `renders/`, where posting looks first.
- `--wait` downloads them to the same paths here. Or later: `python -P tools/render/submit.py wait <job_id>`.
- Job status lives in D1 (`job/<id>`): queued, rendering, done (with `seconds`), failed (with `error`).
  A failed job never leaves a file under `renders/`.

Example (Saenchai editorial):

    python -P tools/render/submit.py production/reels/2026-10-21-saenchai-editorial C \
      --include media/saenchai-broll/aW6ew2j1ZmQ.mp4 --include media/saenchai-broll/EXPvZzeb5cE.mp4 \
      --include media/saenchai-broll/clips/05-harrison-down-1.mp4 \
      --include production/listicles/music/epic-bold-drums-alex-morgan.mp3 --wait

The app (`modal_app.py`) redeploys by itself on push (workflow "Deploy render app"). By hand:
`PYTHONUTF8=1 python -m modal deploy tools/render/modal_app.py` (UTF-8 mode: Modal prints characters the
Windows console can't). Cost: about 5-8 cents per talking-head variant, inside Modal's $30/month free credit.
