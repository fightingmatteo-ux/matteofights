# Own Meta app: post trial reels for free

`ig.py` posts trial reels to @matteofights through our own Meta developer app (Instagram API with
Instagram Login, `graph.instagram.com`). The app stays in **development mode**: no App Review and
no business verification are needed, because the only account using it is the app owner's own.

## One-time setup (Matteo, ~10 min, in the browser)

1. **Create the app.** developers.facebook.com → My Apps → Create app. Use case:
   **"Manage messaging & content on Instagram"**. Name `matteofights-poster`. No business portfolio needed.
2. **Add Instagram login.** In the app: Use cases → Instagram → Customize → **API setup with Instagram login**.
   Under "Add required permissions", make sure `instagram_business_basic` and
   `instagram_business_content_publish` are on.
3. **Generate the token.** Same page → "Generate access tokens" → **Add account** → log in as
   @matteofights and allow. Click **Generate token** next to the account and copy it.
   (If Instagram asks for a tester invite: Instagram app → Settings → Website permissions →
   Apps and websites → Tester invites → Accept.)
4. **Store it yourself, never in chat.** Create `secrets/meta.env` (gitignored):
   ```
   IG_ACCESS_TOKEN=<the token>
   IG_USER_ID=<the number shown next to the account>
   ```
   For cloud runs: `gh secret set IG_ACCESS_TOKEN` and `gh secret set IG_USER_ID` (it prompts; paste there).
5. **Check:** `python -P tools/instagram/ig.py whoami` prints the username and follower count.

The token lasts 60 days. `ig.py refresh` extends it (do it monthly).

## Posting a trial reel

```bash
python -P tools/instagram/ig.py trial --asset <slug>-A.mp4 \
    --caption-file production/reels/<slug>/caption-A.txt --thumb-offset 500       # preview only
python -P tools/instagram/ig.py trial ... --confirm                               # after Matteo's yes
```
- Default `--strategy MANUAL`: the reel stays a trial until Matteo shares it in the app. `SS_PERFORMANCE`
  lets Instagram graduate it automatically.
- The video must be on the `media` release (`tools/video/media.sh push <file>`); ig.py hands Meta a signed
  GitHub download link (valid minutes). Direct upload is refused for this app ("video_url is required").
- The script prints the media id; log it in the reel's `REEL.md` and `LEDGER.md` (media id column).
- Limit: Instagram's 100 API posts per 24 h (shared with Buzzfy).

## Rule
Never run `--confirm` without showing Matteo the exact preview and getting an explicit yes in that conversation.

## From the cloud
Secrets `IG_ACCESS_TOKEN` and `IG_USER_ID` are set on the repo (Actions). Push the render to the media
release (`tools/video/media.sh push <file>`), commit the caption file, then run the **Post trial reel**
workflow: preview first, `confirm=true` only after Matteo's yes. After `ig.py refresh`, update the secret:
`gh secret set -f secrets/meta.env`.

## Post queue (remote, no laptop needed)
`production/schedule/queue.json` lists posts; the **Post queue** workflow runs every 30 min and posts the
earliest item that is `approved: true`, `status: queued`, past `not_before`, and at least `min_gap_hours`
after the account's latest post. It writes `status`, `media_id` and `permalink` back into the file.
- Videos go on the `media` release first: `bash tools/video/media.sh push <file>`.
- `approved: true` is set only after Matteo's explicit yes to the exact preview, via `python -P tools/instagram/approve.py <ids> --note "<when he said yes>"` (or by editing the file on github.com).
- A failed item gets `status: failed` + `error`; fix it and set it back to `queued`.
- Double-post guard: a post from the last 24 h starting with the same caption line counts as already posted.
