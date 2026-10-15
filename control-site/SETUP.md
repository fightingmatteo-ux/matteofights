# Control center setup (one time, ~20 min, free)

Site: `control.matteofights.me` (Cloudflare Pages, login-protected). Bot: Telegram. Both drive the
`Control` GitHub workflow; nothing runs on your laptop. Tokens go into Cloudflare/GitHub settings, never into chat.

## 1. Cloudflare + domain
1. Sign up at dash.cloudflare.com (free plan) → **Add a domain** → `matteofights.me`.
2. Cloudflare imports your DNS records. Check the GitHub Pages ones are there (the `A` records
   185.199.108–111.153 and/or the `CNAME` for `www`). Set them to **DNS only** (grey cloud).
3. At your domain registrar, replace the nameservers with the two Cloudflare gives you. Wait for "Active".

## 2. Telegram bot
1. In Telegram, open **@BotFather** → `/newbot` → name it (e.g. *Matteo Control*) → copy the **bot token**.
2. Make up a long random **webhook secret** (letters/numbers only, 30+ chars). Keep it for step 3 and 5.

## 3. Pages project
1. Cloudflare → **Workers & Pages → Create → Pages → Connect to Git** → pick `matteofights`.
2. Production branch `master`. Root directory `control-site`. Build command
   `python3 ../tools/control/build_data.py`. Output directory `public`.
3. **Settings → Variables and secrets** (Production), add:

| Name | Value |
|---|---|
| `GITHUB_TOKEN` | Fine-grained token (github.com → Settings → Developer settings): only repo `matteofights`, permission **Actions: Read and write** |
| `GITHUB_REPO` | `fightingmatteo-ux/matteofights` |
| `OWNER_EMAIL` | your login email |
| `ACCESS_TEAM` | your Zero Trust team name (step 4), e.g. `matteo` |
| `ACCESS_AUD` | the Application Audience (AUD) tag (step 4) |
| `TELEGRAM_BOT_TOKEN` | bot token from step 2 |
| `TELEGRAM_WEBHOOK_SECRET` | secret from step 2 |
| `TELEGRAM_CHAT_ID` | leave empty for now (step 5) |

4. **Custom domains** → add `control.matteofights.me`. Redeploy.

## 4. Login (Cloudflare Access, free up to 50 users)
1. Cloudflare → **Zero Trust** → pick a team name → free plan.
2. **Access → Applications → Add → Self-hosted**: domain `control.matteofights.me`, policy **Allow**,
   include **Emails** = your email (one-time code login). Copy the **AUD tag** into `ACCESS_AUD`.
3. Add a second self-hosted application for `control.matteofights.me/api/telegram` with policy
   action **Bypass**, include **Everyone** (Telegram can't log in; that endpoint checks the secret instead).

## 5. Connect Telegram
1. In a browser open (fill in your values):
   `https://api.telegram.org/bot<BOT_TOKEN>/setWebhook?url=https://control.matteofights.me/api/telegram&secret_token=<WEBHOOK_SECRET>`
2. Message your bot `/start`. It replies with your **chat id**. Put it in Pages `TELEGRAM_CHAT_ID` and redeploy.
3. GitHub repo → Settings → Secrets → Actions: add `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` (same values).
4. Send the bot any text: it becomes an idea, and the bot confirms after the Control workflow saves it.
