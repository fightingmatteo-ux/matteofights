# The 4-Week Power Plan (paid)

First paid product (decided 2026-11-01 from the money research: the power + fitness plan reel got about 165 "Plan"
comments and the best save rate on the account). $12 one-time, $6 in lower-income countries.

## Flow

`plan reel ("comment PLAN")` -> auto-DM (`signup-site/functions/api/ig-webhook.js`: free PROTOCOL session + plan link)
-> `matteofights.me/plan/?src=...` (sales page) -> `matteo-signup.pages.dev/api/plan/buy` (Lemon Squeezy checkout, price
by country) -> back to `matteofights.me/plan/#k=TOKEN`, the buyer's private link -> day 1 test -> 12 sessions -> retest
unlocks on day 28 (calendar file so they come back) -> before/after table.

| File | What |
|---|---|
| `signup-site/lib/plan_content.js` | The 12 sessions. Sent only to paid links. Edit sessions here (and the week notes in plan.js) |
| `docs/plan/plan.js` | Page logic, test fields, public week notes for the sales page |
| `docs/plan/index.html` | Sales page (no token) and buyer page (`#k=TOKEN`) |
| `signup-site/lib/plan.js` | Prices (`PRICE_FULL`, `PRICE_LOW`, low-price countries), Lemon Squeezy ids + API, D1 helpers |
| `signup-site/functions/api/plan/buy.js` | Makes the token, opens the Lemon Squeezy checkout. The link is also the button on the receipt email |
| `signup-site/functions/api/plan/webhook.js` | Lemon Squeezy order_created / order_refunded: marks paid (Telegram "sold") or locks |
| `signup-site/functions/api/plan/me.js` | The buyer page's API: paid?, the sessions (paid only), saves test + retest |

Buyers live in D1 (`docs`, kind `plan`, id = token): session, status, amount, country, src (which reel), email,
baseline, retest. Never copy buyer rows into this repo (it is public).

## Switch it on (Matteo, once)

Payments run through **Lemon Squeezy** (merchant of record: it collects VAT/sales tax worldwide, no registered
business needed, pays out twice a month to PayPal or bank once over $50). Switched from Stripe on 2026-11-02.

1. lemonsqueezy.com: create the store, finish identity verification, add a payout method (PayPal or bank).
2. Products > New: "The 4-Week Power Plan", single payment, $12 (the checkout overrides the price per country).
3. Send Claude the **store id** and the product's **variant id** (both numbers). They go in `LS_STORE_ID` /
   `LS_VARIANT_ID` in `signup-site/lib/plan.js` (not secret).
4. Settings > API: create a key (**test mode** first). GitHub repo > Settings > Secrets > Actions:
   `LEMONSQUEEZY_API_KEY`.
5. Settings > Webhooks > add: URL `https://matteo-signup.pages.dev/api/plan/webhook`, events `order_created` and
   `order_refunded`, signing secret = any long random string. Same string as GitHub secret `LEMONSQUEEZY_WEBHOOK_SECRET`.
6. Merge the branch to master ("Deploy signup endpoint" pushes the secrets). Test: matteofights.me/plan, buy with the
   test card 4242 4242 4242 4242, check the personal link unlocks and Telegram says "sold (TEST)".
7. Live: make a live-mode API key + live webhook, update both secrets, rerun "Deploy signup endpoint".

Refunds: Lemon Squeezy > Orders > Refund. The webhook locks that buyer's plan again.
