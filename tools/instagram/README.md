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

## Audio API: Instagram library sounds without the app (added 2026-10-19, live since 2026-10-20)
**Sound scout** (`sound_scout.py`, Action **Sound scout**, Mondays 06:40 UTC): reads the sound of every Instagram
outlier + `production/sounds/watch.json` (yt-dlp raw pages: `music_asset_info` / `original_sound_info`), ranks them
by the views they carried and resolves each to an `audio_id` the API can attach -> `production/sounds/proven.json`.

`audio.py` attaches a sound from Instagram's library (e.g. Echo Sax End) when the reel is created, so `app_audio`
listicles no longer need posting by hand. Meta only offers this through **Facebook Login** (graph.facebook.com), not the
Instagram Login token above, so it runs on `FB_USER_TOKEN` and leaves `IG_ACCESS_TOKEN` / `ig.py` untouched.

**One-time:** `FB_USER_TOKEN` needs `instagram_basic` and `instagram_content_publish` on top of its Page scopes.
Graph API Explorer → app `matteofights-poster` → add those two → Generate → Extend → update `secrets/meta.env` and
the `FB_USER_TOKEN` secret. Then `python -P tools/instagram/audio.py check` (or the **Audio** workflow, action `check`).
Regenerating keeps the Page token working (`crosspost.py facebook-setup` again only if Facebook posting breaks).

```bash
python -P tools/instagram/audio.py search "echo sax end"            # find the id (empty query = trending)
python -P tools/instagram/audio.py trial --asset X.mp4 --caption-file ... --audio "Echo Sax End - Caleb Arredondo"
python -P tools/instagram/audio.py trial ... --audio-id <id> --confirm   # after Matteo's yes
```
- Default mix: sound 100 %, clip's own sound 20 % (`--audio-volume`, `--video-volume`; queue keys `audio_volume`, `video_volume`).
- **Queue:** an approved item with `app_audio` gets its `audio_id` looked up at post time (exact title, and artist if
  given). No exact match → `audio_status: "manual"`, Matteo posts it in the app. Token problem → skipped, retried next run.
- **Post trial reel** workflow: optional `audio` input (id or "Title - Artist").
- Meta's limits: only sounds cleared for third-party apps (some app songs are missing), no preview of reels with
  attached audio, and trial_params + audio together is undocumented: if Meta refuses the pair the item fails with
  Meta's message and nothing is posted.

## Comment PROTOCOL auto-DM (one-time, Matteo, ~10 min)

Someone comments "protocol" on any reel -> they get a DM with matteofights.me/protocol and a short public reply
("Sent it to your DMs 🥊"). Code: `signup-site/functions/api/ig-webhook.js` (Pages project `matteo-signup`), every
comment logged in D1 kind `protocol_dm`; counts at `https://matteo-signup.pages.dev/api/signup`.

1. **Permissions.** developers.facebook.com -> app `matteofights-poster` -> Use cases -> Instagram -> Customize ->
   API setup with Instagram login -> add `instagram_business_manage_comments` and
   `instagram_business_manage_messages` (keep the two you have).
2. **New token.** Same page -> Generate token for @matteofights (allow the new permissions) -> update the GitHub
   secret `IG_ACCESS_TOKEN` (and `secrets/meta.env`). The **Deploy signup endpoint** workflow copies it to the
   endpoint daily (or run it by hand to do it now).
3. **Messages on.** Instagram app -> Settings -> Messages and story replies -> Message controls -> Connected tools
   -> **Allow access to messages** ON.
4. **Webhook.** Same API setup page -> 3. Configure webhooks: Callback URL
   `https://matteo-signup.pages.dev/api/ig-webhook`, Verify token `matteofights-protocol` -> Verify and save ->
   subscribe the field **comments**. Then switch the webhook toggle for @matteofights on.
5. **Optional, safer:** App settings -> Basic -> App secret -> add it to the Pages project `matteo-signup` as secret
   `IG_APP_SECRET` (signature check). Without it every comment is re-read from Instagram before anything is sent.
6. **Test:** comment "protocol" on one of your reels from a second account. The DM should land within seconds.

Note: `ig.py refresh` keeps the same scopes; the daily **Deploy signup endpoint** run picks the refreshed token up.
Privacy policy URL for the Meta app (needed to switch it to Live): https://matteofights.me/privacy.html
