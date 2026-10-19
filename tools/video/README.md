# Video tools: watch and edit from the cloud

Claude's cloud sessions can't reach Instagram, TikTok, YouTube or Google Drive directly (network policy).
GitHub Actions runners can. So the pipeline is:

```
link ──► GitHub Actions "Fetch video" ──► analysis committed to the repo (frames, cuts, transcript)
                                     └──► the .mp4 stored on the "media" release
cloud session ──► media.sh pull ──► reel.py edits ──► finished render sent to you in the app
```

## Watch a video
- **Someone else's reel:** Actions tab → **Fetch video** → Run workflow → paste the link, a slug, `reference`.
  Works from the GitHub mobile app. Or just give Claude the link and it triggers the run.
- **Your own footage:** share the Drive file as "Anyone with the link", run the same workflow with
  that link and `footage`. Or upload it to the `media` release from github.com (up to 2 GB per file).
- Output lands in `content-bank/references/videos/<slug>/` (or `real-footage/analysis/<slug>/`):
  `contact.jpg`, `frames/`, `scenes/` (one per hard cut), `cuts.txt`, `transcript.txt`, `meta.json`,
  `source.json` (creator, caption, views when the site exposes them).

Locally (laptop can reach Instagram): `bash production/editing/reel-kit/scripts/fetch_ref.sh <url> <slug>`
downloads with `secrets/ig_cookies.txt` and runs `watch.py` (now also writes `words.json`; works on Windows).
Just a file: `python3 tools/video/watch.py VIDEO OUTDIR`. Editing: `production/editing/reel-kit/PIPELINE.md`.

## Edit a reel
```
python3 tools/video/reel.py out.render.mp4 \
  --clip media/bag.mov@2-5.5 --clip media/shadow.mp4@0-4 \
  --hook "8 ways to fight like a legend without a coach" \
  --sub "You don't need a coach to fight like a legend." \
  --music media/track.mp3 --mute-clips
```
Crops to 1080x1920, applies `content-bank/luts/matteofights-v1.cube`, burns in the hook (brand red, ALL
CAPS), the subhook, and a `READ DESCRIPTION` end card. Renders end in `.render.mp4` (gitignored).

## Move big files
`tools/video/media.sh list | pull NAME | push FILE` uses the `media` GitHub release, because git rejects
files over 100 MB. Never commit raw footage to git.

## Videos clean themselves up
The **Media cleanup** workflow (daily, `tools/video/lifecycle.py`) deletes a posted reel's video from the
media release and its Drive preview once it posted 7+ days ago and every cross-post platform has it (21 days
at most). Winners stay 30 days; "Keep video" on the dashboard keeps one for good. Watched reference videos go
after 14 days (their frames and transcript stay committed). Raw footage is never touched. Each deleted reel
keeps a record in `production/archive/reels.json` (caption, cover, permalink, numbers, cross-post links), and
stats keep updating because they're read by post id, not from the file. Dry run: `python3 -P tools/video/lifecycle.py`.

## Instagram blocks
Instagram sometimes refuses logged-out downloads from cloud IPs. If **Fetch video** fails on an
Instagram link, add a repo secret `IG_COOKIES` (Settings → Secrets → Actions) containing a
Netscape-format `cookies.txt` exported from a logged-in browser. Use a burner account if you can.
If yt-dlp still fails, the workflow falls back to Business Discovery (`tools/video/ig_discovery.py`, uses
the `FB_USER_TOKEN` secret): it finds the reel in the creator's posts and downloads it through the Meta API.
Works only for creator/business accounts; fill the optional `user` input if the username can't be looked up.
