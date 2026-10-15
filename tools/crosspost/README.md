# Other platforms: Facebook, YouTube Shorts, Threads (TikTok next)

Instagram stays the source. Every reel that posts there (Post queue) is re-posted by the **Cross-post** workflow
(`crosspost.py run`, every ~30 min) to each enabled platform in **that platform's own New York time slots**, one per
slot, oldest first, with a caption shaped for that platform (`captions.py`). On top of the reels:

- **Facebook slides** (`facebook_slides`): each listicle also becomes a photo album (title, one slide per sign,
  question), rendered by `slides.py`, at 09:00 NY the morning after.
- **Written Threads posts** (`threads_text`): 3 a day (07:30 hot take, 12:30 question, 17:30 tip/story) from
  `production/threads/posts.json`. They only post after Matteo approves the week (Telegram "✅ Approve Threads posts",
  or `approve_threads` / `approve_week` on the dashboard API). Never the same text twice (Threads flags repeats).

Results: `production/schedule/crosspost.json` (per reel and platform) and Telegram ("📤 Facebook Reels: …").
Everything also lands in the dashboard's data (`crosspost`, `threads_posts` in data.json).

## Plan per platform (research 2026-10-16, Buffer/Metricool/Socialinsider + official API docs)

| Platform | Volume | Slots (NY) | Shape |
|---|---|---|---|
| Instagram | 2 listicle trial reels/day (8 s loops) | 18:30, 21:30 | unchanged |
| Facebook | 2 reels + 1 slide album/day | reels 12:30, 19:30; album 09:00 | 1-3 line hook, list, question, ≤3 hashtags, no IG CTAs |
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

## One-time setup per platform (done 2026-10-16 except TikTok)

### Facebook (Page "Matteo Fights")
Graph API Explorer → app `matteofights-poster` → User Token with `pages_manage_posts`, `pages_read_engagement`,
`pages_show_list` (the app needs the "Manage everything on your Page" use case) → Extend in the Access Token Tool →
`FB_USER_TOKEN=` in `secrets/meta.env` → `crosspost.py facebook-setup` (Page token that never expires) → GitHub
secret `FB_PAGE_TOKEN`.

### YouTube
Google Cloud project `matteofights`, YouTube Data API v3 on, Google Auth Platform app `matteofights poster`
(External, **published**; home page matteofights.me, privacy matteofights.me/privacy.html), Desktop client →
`YT_CLIENT_ID` / `YT_CLIENT_SECRET` in `secrets/crosspost.env` → `crosspost.py youtube-auth` → GitHub secrets.
Uploads stay **private** until the API audit passes (support.google.com/youtube/contact/yt_api_form); then set
`platforms.youtube.privacy` to `public`.

### Threads
Use case "Access the Threads API" on `matteofights-poster`, Threads Tester role accepted in the Threads app, token
from the User Token Generator → `THREADS_ACCESS_TOKEN` → `crosspost.py threads-check` → GitHub secrets
`THREADS_ACCESS_TOKEN`, `THREADS_USER_ID`. The token expires ~2026-12-14: `crosspost.py threads-refresh`, then update
the GitHub secret.

## GitHub secrets used
`FB_PAGE_TOKEN`, `YT_CLIENT_ID`, `YT_CLIENT_SECRET`, `YT_REFRESH_TOKEN`, `THREADS_ACCESS_TOKEN`, `THREADS_USER_ID`,
`TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`.
