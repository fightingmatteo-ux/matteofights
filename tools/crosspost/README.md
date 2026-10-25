# Other platforms: Facebook, YouTube Shorts, Threads (TikTok next)

Instagram stays the source. Every reel that posts there (Post queue) is re-posted by the **Cross-post** workflow
(`crosspost.py run`, every ~30 min) to each enabled platform in **that platform's own New York time slots**, one per
slot, oldest first, with a caption shaped for that platform (`captions.py`). On top of the reels:

- **Facebook slides** (`facebook_slides`): each listicle also becomes a photo album (title, one slide per sign,
  question), rendered by `slides.py`, at 09:00 NY the morning after.
- **Written Threads posts** (`threads_text`): 3 a day (07:30 hot take, 12:30 question, 17:30 tip/story) from
  `production/threads/posts.json`. They only post after Matteo approves the week (Telegram "✅ Approve Threads posts",
  or `approve_threads` / `approve_week` on the dashboard API). Never the same text twice (Threads flags repeats).

**Facebook since 2026-10-22** (Matteo's yes after Facebook views fell from ~100 to ~0 a reel): `platforms.facebook.winners`
is on, so Facebook only gets the daily pick. The Listicle factory's daily `--fb-pick` run (20:10 UTC) takes the best Instagram
reel aged 72 h to 7 days that isn't on Facebook yet and did at least `min_vs_median` x the account median views (Buzzfy
`metrics.json`, else the API numbers; ties by shares + saves per 1k; follows per reel aren't available), renders its
Facebook version (`render.offsite`: the list as cards on screen, royalty-free music, ~25 s) as `<asset>-fb.mp4`, and marks
the queue item (`fb_pick`, `video_asset_fb`). No reel clears the bar = no Facebook reel that day. YouTube and Threads
take a listicle's music copy (`video_asset_music`, rendered by the factory) when its Instagram sound is attached in the app.

Results: `production/schedule/crosspost.json` (per reel and platform) and Telegram ("📤 Facebook Reels: …").
Everything also lands in the dashboard's data (`crosspost`, `threads_posts` in data.json).

## Plan per platform (research 2026-10-16, Buffer/Metricool/Socialinsider + official API docs)

| Platform | Volume | Slots (NY) | Shape |
|---|---|---|---|
| Instagram | 2 listicle trial reels/day (8 s loops) | 18:30, 21:30 | unchanged |
| Facebook | 1 reel/day, only the best Instagram reel at 72 h (since 2026-10-22); slide albums paused | 19:30 | Facebook version: list on screen, music in the file, no READ DESCRIPTION; caption 1-3 line hook, list, question, ≤3 hashtags |
| YouTube | 2 Shorts/day; long-form 1/week later (needs Matteo) | 12:30, 19:00 | keyword title "… 🥊 #shorts", list in description, 3 hashtags |
| Threads | 2 reels + 3 written posts/day | reels 10:00, 15:30; text 07:30, 12:30, 17:30 | hook first, no hashtags, one topic tag ("Fight Psychology") |
| TikTok | 1 video + 1 photo carousel/day (after app review) | ~12:30, 19:30 | drafts to the inbox; Matteo adds a trending sound in-app |

API ceilings (not targets): Threads 250 posts/24 h, Facebook 30 API reels/24 h per Page, YouTube 100 uploads/day,
TikTok ~15 posts/day. Replies to comments stay manual (biggest growth lever on Threads; automated replies get flagged).
Check every 3-4 weeks against each platform's own analytics and move the slots/volumes in `crosspost.json`.

## Who writes the Threads posts

A scheduled **Claude routine** (Matteo's subscription, runs in the cloud, no device needed) runs every Sunday after
the listicle factory: it reads the coming week's listicles in `production/schedule/queue.json` + `context/voice.md`,
appends 21 new posts to `production/threads/posts.json` (`status: queued`, `approved: false`) and pushes. The next
notify sends them to Telegram for one-tap approval. Rules: voice.md (no em dashes, short lines, second person), never
invent Matteo's personal stories, never repeat an earlier text, ≤500 characters per post.

Since 2026-10-16 the routine follows the repo skill **`threads-writer`** (`.claude/skills/threads-writer/SKILL.md`):
it reads `tools/threads/report.py` (the account's own numbers: replies, shares and likes per 1k views by kind,
length, question vs statement), plans the week from them, writes in the voice of `context/creator-voice.md`, and
must pass `tools/threads/lint.py` before pushing. Results are kept for good in `production/threads/results.json`
(`tools/threads/collect.py`, run by the Platform stats workflow after `stats.py`). Hooks and captions follow the
**`platform-captions`** skill.

## One-time setup per platform (done 2026-10-16 except TikTok)

### Facebook (Page "Matteo Fights")
Graph API Explorer → app `matteofights-poster` → User Token with `pages_manage_posts`, `pages_read_engagement`,
`pages_show_list`, **`read_insights`** (reach and watch time per reel, added 2026-10-25) (the app needs the
"Manage everything on your Page" use case) → Extend in the Access Token Tool →
`FB_USER_TOKEN=` in `secrets/meta.env` → `crosspost.py facebook-setup` (Page token that never expires) → GitHub
secret `FB_PAGE_TOKEN`.

### YouTube
Google Cloud project `matteofights`, YouTube Data API v3 on, Google Auth Platform app `matteofights poster`
(External, **published**; home page matteofights.me, privacy matteofights.me/privacy.html), Desktop client →
`YT_CLIENT_ID` / `YT_CLIENT_SECRET` in `secrets/crosspost.env` → `crosspost.py youtube-auth` → GitHub secrets.
Uploads stay **private** until the API audit passes (support.google.com/youtube/contact/yt_api_form); then set
`platforms.youtube.privacy` to `public`.

**Browser-only refresh (no laptop, 2026-10-25):** developers.facebook.com/tools/explorer → app
`matteofights-poster` → "User or Page": Get User Access Token → tick `pages_show_list`, `pages_read_engagement`,
`pages_manage_posts`, `read_insights` → Generate, allow for the Matteo Fights Page → copy the token →
developers.facebook.com/tools/debug/accesstoken → paste → Debug → **Extend Access Token** → copy the long-lived token
→ back in the Explorer, paste it into the token box and run `GET me/accounts` → copy the Matteo Fights
`access_token` (a Page token from a long-lived user token never expires) → GitHub secret `FB_PAGE_TOKEN`.

### Threads
Use case "Access the Threads API" on `matteofights-poster`, Threads Tester role accepted in the Threads app, token
from the User Token Generator → `THREADS_ACCESS_TOKEN` → `crosspost.py threads-check` → GitHub secrets
`THREADS_ACCESS_TOKEN`, `THREADS_USER_ID`. The token expires ~2026-12-14: `crosspost.py threads-refresh`, then update
the GitHub secret.

### TikTok (started 2026-10-25)
Plan: videos go to Matteo's TikTok **drafts** (scope `video.upload`), he adds a trending sound in the app and posts.
Drafts need no audit; direct posting (`video.publish`) stays private-only until TikTok audits the app, so we skip it.

1. developers.tiktok.com → log in with the @matteofights TikTok → Manage apps → **Connect an app** → name
   `matteofights poster`, type: Individual/personal developer.
2. App details (copy exactly):
   - Category: **Entertainment** (or Lifestyle). Platform: **Web**.
   - Description: "Private tool that sends Matteo's own short fight-training videos from his production pipeline to
     his own TikTok drafts, and shows his own follower and view counts on his private dashboard. Not offered to
     other users."
   - Website URL: `https://matteofights.me` → Verify: pick **URL prefix**, download TikTok's signature file and send
     it to Claude (it goes into `docs/` and is live in a minute), then press Verify.
   - Terms of service: `https://matteofights.me/terms.html`. Privacy policy: `https://matteofights.me/privacy.html`.
   - App icon: `docs/avatar.jpg` (1024×1024 if it asks; Claude can resize).
3. Products: add **Login Kit** (redirect URI `https://matteofights.me/tiktok-callback.html`) and **Content Posting
   API** (leave Direct Post off). Scopes: `user.info.basic`, `user.info.stats`, `video.upload`, `video.list`.
4. **Sandbox** first: create a sandbox, add @matteofights as a target user. Put the sandbox Client key and Client
   secret in `secrets/crosspost.env` as `TIKTOK_CLIENT_KEY=` / `TIKTOK_CLIENT_SECRET=` and run
   `python -P tools/crosspost/crosspost.py tiktok-auth` (log in, Authorize, paste the code the page shows).
5. Test one draft (Claude runs it with you), **screen-record** it: dashboard → reel → TikTok inbox notification →
   draft opens in TikTok. That recording is the demo video the review asks for.
6. Submit for review with the recording. Explain: "Single-user tool. The creator connects his own account with
   Login Kit; videos he produced are uploaded to his TikTok inbox as drafts with the Content Posting API (upload
   only); he edits and posts them himself in the TikTok app. user.info.stats and video.list show his own follower
   and view counts on his private dashboard."
7. Approved: swap in the production key/secret, run `tiktok-auth` again, add GitHub secrets `TIKTOK_CLIENT_KEY`,
   `TIKTOK_CLIENT_SECRET`, `TIKTOK_REFRESH_TOKEN`. Turning TikTok on in `crosspost.json` (`platforms.tiktok`,
   slots ~12:30 and 19:30 NY) is Matteo's yes, like every platform.

The refresh token is kept in D1 (`token/tiktok`), never in this public repo, because TikTok may rotate it.
Stats (`stats.py`) read followers and the last 20 videos' views once the secrets exist.

## GitHub secrets used
`FB_PAGE_TOKEN`, `YT_CLIENT_ID`, `YT_CLIENT_SECRET`, `YT_REFRESH_TOKEN`, `YT_API_KEY`, `THREADS_ACCESS_TOKEN`, `THREADS_USER_ID`,
`TIKTOK_CLIENT_KEY`, `TIKTOK_CLIENT_SECRET`, `TIKTOK_REFRESH_TOKEN`,
`TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`.

## YouTube numbers on the dashboard (2026-10-25)

The uploader's login is upload-only, so it can't read views. `stats.py` (Platform stats workflow) reads views, likes,
comments per Short and the subscriber count with either:

1. **`YT_API_KEY`** (simplest, public numbers only): Google Cloud console, the same project as `YT_CLIENT_ID` →
   APIs & Services → Credentials → Create credentials → API key → restrict it to "YouTube Data API v3". Add it as the
   GitHub Actions secret `YT_API_KEY`. The next Platform stats run fills the dashboard.
2. Re-run `python -P tools/crosspost/crosspost.py youtube-auth` on the laptop (it now asks for upload + read +
   YouTube Analytics) and update the `YT_REFRESH_TOKEN` secret. Needed for watch time (% viewed, average view
   duration, subscribers gained per Short): turn on **YouTube Analytics API** in the project first
   (console.cloud.google.com/apis/library/youtubeanalytics.googleapis.com).

Until one of them is set, the dashboard's YouTube card says "No view numbers yet" instead of showing 0.
