# Control center: how it is set up

Live since 2026-10-15. Site `https://control.matteofights.me` (Cloudflare Pages + Access login), bot
`@matteofights_control_bot` (Telegram). Both start the `Control` GitHub workflow; nothing runs on the laptop.
Tokens live in Cloudflare / GitHub secrets and in `secrets/control.env` (gitignored), never in the repo or chat.

## How the pieces connect

```
dashboard button ─► /api/act (Pages Function, checks Access JWT + OWNER_EMAIL) ─┐
Telegram message ─► /api/telegram (checks secret header + TELEGRAM_CHAT_ID) ────┴► GitHub "Control" workflow
   └─ control.py act → commits production/control + queue.json → control.py notify → Telegram reply
push to master / Control / Post queue / Listicle factory / Post trial reel finished
   └─► "Deploy control center" workflow: build_data.py → wrangler pages deploy (site + Functions)
```

Deploys come from `.github/workflows/control-deploy.yml`, not from Cloudflare's Git integration, so the data
(`data.json`, covers) is rebuilt from the repo on every push and after every workflow that changes `production/`.
Manual redeploy: Actions → **Deploy control center** → Run workflow (or `gh workflow run control-deploy.yml`).

## Studio and live data (2026-10-20)

Pages bindings `DB` (D1 `matteofights`) and `MEDIA` (R2 `matteofights-media`), set on the project via the API.
`/api/live` (everything from D1, polled every 30 s by `public/studio.js`), `/api/upload` (footage straight to R2
`uploads/` in 50 MB parts, then starts the "Edit worker" workflow), `/api/studio` (revision notes, talking-point
skip, retry). All check the Access login like `/api/act`.

## Platforms, Leads, Grow (2026-10-25)

Nav is Home, Platforms, Leads, Studio, Decide; the activity log sits behind the pulse button in the top bar.
`public/hub.js` draws Platforms (views per platform and in total from `production/control/platforms.json`, a
verdict per platform from its own per-post median, on/off + NY slots + a free-text brief, saved through
`/api/act` `platform_set` → `control.py` → `crosspost.json` via `tools/state.py` and `production/control/briefs.json`,
which the platform-captions and threads-writer skills read), Leads and Grow. `/api/leads` reads D1 `signup`
(the PROTOCOL page) and `protocol_dm` (commenters who got the auto-DM, no signup yet); follow-up status is stored on
the signup doc (`lead_status`, `contacted_at`, `lead_note`) or kind `lead` (`ig:<handle>`). "Message" copies a
personal DM and opens `ig.me/m/<handle>`: Instagram's API can't cold-DM someone who never messaged the account.

## Cloudflare (account `849fbd13419572f8d5e345f23dd3de11`, fightingmatteo@gmail.com)

- **DNS:** `matteofights.me` zone on Cloudflare (nameservers `derek`/`melinda.ns.cloudflare.com`, set at
  Namecheap). GitHub Pages records are **DNS only**: apex A 185.199.108–111.153, `www` CNAME
  `fightingmatteo-ux.github.io`. Namecheap mail-forwarding MX + SPF copied over. `control` CNAME
  `matteo-control.pages.dev` (proxied).
- **Pages project `matteo-control`**, production branch `master`, custom domain `control.matteofights.me`.
  Secrets (Settings → Variables and secrets):

| Name | Value |
|---|---|
| `GITHUB_TOKEN` | fine-grained PAT `matteo-control`: only repo `matteofights`, **Actions: Read and write** |
| `GITHUB_REPO` | `fightingmatteo-ux/matteofights` |
| `OWNER_EMAIL` | `fightingmatteo@gmail.com` |
| `ACCESS_TEAM` | `small-pond-1c50` |
| `ACCESS_AUD` | AUD tag of the "Matteo control center" Access app |
| `TELEGRAM_BOT_TOKEN` | bot token |
| `TELEGRAM_WEBHOOK_SECRET` | random secret, also sent by Telegram as `X-Telegram-Bot-Api-Secret-Token` |
| `TELEGRAM_CHAT_ID` | `6698804992` |

  Pages secrets only apply to the next deployment: redeploy after changing one.
- **Zero Trust / Access** (team `small-pond-1c50`, Free plan), login method **One-time PIN**:
  - App **Matteo control center**: `control.matteofights.me`, `matteo-control.pages.dev`,
    `*.matteo-control.pages.dev`; policy Allow, email `fightingmatteo@gmail.com`; 30-day session.
  - App **Matteo control: Telegram webhook**: `control.matteofights.me/api/telegram`, policy **Bypass** (Everyone).
    Telegram can't log in; the function rejects requests without the secret header (403).

## GitHub Actions secrets

`CLOUDFLARE_API_TOKEN` (deploy-only token, **Pages: Edit** on this account), `CLOUDFLARE_ACCOUNT_ID`,
`TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`.

## Local `secrets/control.env`

`TELEGRAM_BOT_TOKEN`, `TELEGRAM_WEBHOOK_SECRET`, `TELEGRAM_CHAT_ID`, `GITHUB_TOKEN`,
`CLOUDFLARE_API_TOKEN` (admin token `matteo-control-setup`: Pages, Access apps/policies + orgs/IdPs, Zone, DNS,
API Tokens; used for setup and changes, never stored in GitHub), `CLOUDFLARE_DEPLOY_TOKEN` (same value as the
GitHub secret).

## Common jobs

- **Re-register the Telegram webhook** (new bot token or secret): call
  `https://api.telegram.org/bot<TOKEN>/setWebhook` with `url=https://control.matteofights.me/api/telegram`,
  `secret_token=<TELEGRAM_WEBHOOK_SECRET>`, `allowed_updates=["message","callback_query"]`; check
  `getWebhookInfo` shows no `last_error_message`.
- **Rotate the bot token** (@BotFather → `/revoke`): update it in `secrets/control.env`, the Pages secret and the
  GitHub secret, redeploy, then re-register the webhook.
- **Rotate `GITHUB_TOKEN`**: new fine-grained PAT with the same scope → Pages secret → redeploy.
- **Change the chat**: clear `TELEGRAM_CHAT_ID` in Pages and redeploy; `/start` then replies with the new chat id.
- **Check it works**: logged out, `control.matteofights.me` redirects to `small-pond-1c50.cloudflareaccess.com`;
  `POST /api/telegram` without the header answers 403; a text to the bot runs **Control** green and replies
  "💡 Saved…".
- **404 on `/cdn-cgi/access/authorized` right after login**: the Access app was created before the zone was
  active. Re-save the "Matteo control center" app (Zero Trust → Access → Applications → Edit → Save, or a `PUT`
  with the same config). Fixed this way on 2026-10-15.
