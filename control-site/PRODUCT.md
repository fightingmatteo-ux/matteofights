# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

One user: Matteo, the creator behind @matteofights. He opens the control center on his phone between training
sessions and on his laptop at a desk. On the phone the job is a 5-second check plus the occasional decision; on the
laptop it is reviewing the week and reading results.

## Product Purpose

control.matteofights.me is the remote control for the @matteofights reel system. Claude and GitHub Actions make,
schedule and post reels; Matteo approves each week, answers Claude's questions, sends ideas and checks how reels did.
Success means that in 5 seconds on a phone he knows what posts next and when, whether anything needs his yes, and
how the latest reels did against his normal (median about 2.6k views), and that approving and answering are fast
and cannot happen by accident.

## Positioning

Not a social media scheduler. It is the one screen where a human says yes to a system that otherwise runs on its
own, so the yes is the product: deliberate, informed, and reversible where possible.

## Operating Context

- Static PWA on Cloudflare Pages behind Cloudflare Access (owner email only). Plain HTML/CSS/vanilla JS, no build step.
- `data.json` is rebuilt from repo state on every push by `tools/control/build_data.py`; field names are a contract.
- Buttons POST to `api/act`, which dispatches the `Control` GitHub workflow; Telegram is the parallel channel
  (`functions/api/telegram.js`). Changes appear on the page about a minute after an action.
- Actions and payloads: `approve_week` with `ids`, `answer` with `id` + `choice`, `idea` with `text`, `platform_set`
  with `platform` + `enabled` / `slots` / `brief`. Lead status goes to `/api/leads` (D1 directly).
- All times shown in New York time (America/New_York); the audience is US-weighted.
- Reels post at 6:30pm and 9:30pm New York; a new batch is made every Sunday morning.

## Capabilities and Constraints

- Views: Home, Platforms (overview, one page per platform, formats, rivals, reels), Leads (PROTOCOL signups to DM,
  Grow and earn), Studio, Decide; Activity behind the top-bar button.
- Approving the week is press-and-hold so a slip cannot post 14 reels.
- Formats tracked: listicle, statement, iykyk, builder, lifestyle, talking head. Results compare views per reel and
  follows per 1,000 views; a winner is 2x the median.
- No new paid services, no CDNs except Google Fonts.

## Brand Commitments

From `context/brand.md` (binding): black `#0B0B0D`, combat red `#C82020`, gold `#C49040` for wins and milestones,
Bebas Neue headlines. Fight poster meets training floor. Premium and serious, not playful. Raw beats polished;
pastel, wellness softness and ad-like over-production break the brand. Voice: short, blunt, direct, like a training
partner (`context/voice.md`).

## Evidence on Hand

Real reel covers (`covers/`, built from production folders), real hooks and schedule from `production/schedule/queue.json`.
Metrics come from `production/control/metrics.json` (Claude's daily Buzzfy pull); until it exists there are no
numbers, so empty states are real states, not edge cases. Never fabricate metrics in shipped UI.

## Product Principles

1. The yes is deliberate: every action that changes what gets posted needs intent (hold) or offers a way back (undo).
2. Answer the three phone questions before anything else; everything else is one tap deeper.
3. Compare against Matteo's normal, never against raw numbers alone.
4. Small samples are labeled as small; a format is not a winner on two reels.

## Accessibility & Inclusion

WCAG AA contrast, full keyboard use including the hold gesture, visible focus, reduced-motion support, 44px+ touch
targets, one-handed phone use.
