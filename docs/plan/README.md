# The 4-Week Power Plan (paid)

First paid product (decided 2026-11-01 from the money research: the power + fitness plan reel got about 165 "Plan"
comments and the best save rate on the account). $12 one-time, $6 in lower-income countries.

## Flow

`plan reel ("comment PLAN")` -> auto-DM (`signup-site/functions/api/ig-webhook.js`: free PROTOCOL session + plan link)
-> `matteofights.me/plan/?src=...` (sales page) -> `matteo-signup.pages.dev/api/plan/buy` (Stripe Checkout, price by
country) -> back to `matteofights.me/plan/#k=TOKEN`, the buyer's private link -> day 1 test -> 12 sessions -> retest
unlocks on day 28 (calendar file so they come back) -> before/after table.

| File | What |
|---|---|
| `signup-site/lib/plan_content.js` | The 12 sessions. Sent only to paid links. Edit sessions here (and the week notes in plan.js) |
| `docs/plan/plan.js` | Page logic, test fields, public week notes for the sales page |
| `docs/plan/index.html` | Sales page (no token) and buyer page (`#k=TOKEN`) |
| `signup-site/lib/plan.js` | Prices (`PRICE_FULL`, `PRICE_LOW`, low-price countries), Stripe + D1 helpers |
| `signup-site/functions/api/plan/buy.js` | Makes the token, opens Stripe Checkout. The link also goes on the Stripe invoice email |
| `signup-site/functions/api/plan/me.js` | Confirms payment with Stripe on first open (Telegram "sold" ping), saves test + retest |

Buyers live in D1 (`docs`, kind `plan`, id = token): session, status, amount, country, src (which reel), email,
baseline, retest. Never copy buyer rows into this repo (it is public).

## Switch it on (Matteo, once)

1. Stripe dashboard: create or finish your account (payouts to your bank). Settings > Customer emails: turn on
   "Successful payments". Optional: Settings > Payments > Adaptive Pricing ON (shows local currency).
2. Developers > API keys: copy the **secret key** (`sk_live_...`; use `sk_test_...` first to try it with card 4242 4242 4242 4242).
3. GitHub repo > Settings > Secrets > Actions: add `STRIPE_SECRET_KEY`.
4. Merge the branch to master. "Deploy signup endpoint" puts the key on the Pages project and GitHub Pages serves
   `/plan`. Test: open matteofights.me/plan, buy with the test key, check the personal link and the Telegram ping.
5. Swap to the live key (same secret), rerun "Deploy signup endpoint".

Refunds: Stripe dashboard > Payments > Refund. The buyer link keeps working (it only checks the first payment).
