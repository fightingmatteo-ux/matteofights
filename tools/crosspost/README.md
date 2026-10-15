# Cross-posting: Facebook Reels, YouTube Shorts, Threads

Every reel that posts on Instagram (Post queue) is sent to the other platforms by the **Cross-post** workflow
(`crosspost.py run`), with the same video (media release) and caption. Results go to
`production/schedule/crosspost.json` and to Telegram ("📤 Facebook Reels: …" with the link).

A platform only posts when `platforms.<name>.enabled` is `true` in `crosspost.json`. That flag is Matteo's yes to
posting there; `since` keeps it from backfilling older reels. TikTok comes later (its API needs an app review first).

## One-time setup per platform (Matteo, in the browser; tokens go into files, never chat)

### Facebook Reels (Page "Matteo Fights")
1. developers.facebook.com/tools/explorer → **Meta App** `matteofights-poster` → **User or Page**: User Token →
   **Permissions**: keep the current ones and add `pages_manage_posts`, `pages_read_engagement`, `pages_show_list`
   → **Generate Access Token** → continue as yourself and allow the Page "Matteo Fights".
2. Click the **ⓘ** next to the token → **Open in Access Token Tool** → **Extend Access Token** → copy the new token.
3. Replace the `FB_USER_TOKEN=` line in `secrets/meta.env` with it.
4. Claude runs `crosspost.py facebook-setup` (saves a Page token that never expires) and sets the GitHub secrets.

### YouTube Shorts
1. console.cloud.google.com → new project `matteofights` → **APIs & Services → Library** → enable
   **YouTube Data API v3**.
2. **OAuth consent screen** (Google Auth Platform): External, app name `matteofights poster`, your email; add
   yourself as a test user; then **Publish app** (otherwise the login expires every 7 days).
3. **Clients → Create client → Desktop app** → copy Client ID and Client secret into `secrets/crosspost.env` as
   `YT_CLIENT_ID=` and `YT_CLIENT_SECRET=`.
4. Claude runs `crosspost.py youtube-auth`: pick the @matteofights channel, "Advanced → Go to matteofights poster",
   **Allow**.
5. Until Google's API audit passes, uploads are **private** (`privacy: "private"`): make each one public in the
   YouTube app. Audit form: support.google.com/youtube/contact/yt_api_form. After approval set `privacy` to `public`.

### Threads
1. In the `matteofights-poster` app: **Use cases → Add use case → Access the Threads API**; permissions
   `threads_basic` + `threads_content_publish`.
2. **Roles → Threads testers** → add your Threads username; accept in the Threads app (Settings → Account →
   Website permissions → Invites).
3. Use case **Settings** → User Token Generator → **Generate** for your account → copy into `secrets/crosspost.env`
   as `THREADS_ACCESS_TOKEN=` (and the Threads app secret from the same page as `THREADS_APP_SECRET=`).
4. Claude runs `crosspost.py threads-check` (long-lived token + user id). Refresh monthly: `threads-refresh`.

## GitHub secrets used by the workflow
`FB_PAGE_TOKEN`, `YT_CLIENT_ID`, `YT_CLIENT_SECRET`, `YT_REFRESH_TOKEN`, `THREADS_ACCESS_TOKEN`, `THREADS_USER_ID`,
plus `TELEGRAM_*` for the messages.
