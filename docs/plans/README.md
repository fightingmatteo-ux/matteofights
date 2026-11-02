# Free per-reel plans (matteofights.me/plans/?p=SLUG)

Every plan reel gets its own free plan. Viewer comments PLAN -> the auto-DM (`signup-site/functions/api/ig-webhook.js`)
reads that reel's caption, finds the first plan in `plans.json` whose `match` phrase is in it, and DMs
`matteofights.me/plans/?p=<slug>`. No match (or caption unreadable) -> the free PROTOCOL link, as before. The plan
page ends with the 2-minute test (`/protocol?src=plans`), which is where emails are captured. Commenters show in the
control center Leads tab (kind `protocol_dm`, fields `keyword` and `plan`).

## Adding a plan reel (Claude, when cutting one)
1. Add the plan to `plans.json`: slug, reel id, `match` (a short natural phrase, e.g. "lomachenko footwork plan"),
   title, sub, optional note (documented facts only), days with `[exercise, dose, how]`. No metric units, no em dashes.
2. The caption MUST contain the match phrase, normally as the CTA line:
   `Comment PLAN and I'll send you the Lomachenko footwork plan.`
3. "Inspired by" plans never claim to be the fighter's own program or imply endorsement.
4. Check: `matteofights.me/plans/?p=<slug>` renders (pushes to master go live via GitHub Pages).
