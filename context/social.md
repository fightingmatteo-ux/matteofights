# Social Media Status

_Snapshot. Pull live via Windsor (`instagram` connector) before relying on these numbers._

## Windsor connector

| Connector | Account | ID |
|---|---|---|
| `instagram` | Matteo (matteofights) | 17841465098113052 |
| `facebook_organic` | Matteo Fights (Page) | 1070947222779004 |

Account: joinstance@gmail.com. Rich per-reel insights available (reach, views, avg watch time,
total watch time, saves, shares, engagement) plus captions, permalinks, and follower/views daily
series. **Facebook organic IS connected** (confirmed 2026-06-16 — corrected after being
mislabeled "not connected" here previously). See [apps.md](apps.md) for a field-quirk note:
`get_fields` is broken on this connector and `page_fan_adds` always returns 0 — use `page_fans`
day-over-day delta instead.

## Facebook Page surge (Jun 6–16)
FB Page fans were flat at 226 through all of May. Surge started Jun 6, paralleling the IG surge:
226 (Jun 5) → 298 (Jun 7) → 1,054 (Jun 16). Already decelerating fast: +113 fans Jun 13 → +1 fan
Jun 16. Same shape as IG's surge-and-decay. FB is currently posting MORE reels/week than IG
(~11 vs ~7 in the Jun 10–16 window) including some with generic, off-brand captions that drop the
"COMMENT PROTOCOL" CTA entirely — free distribution with no funnel capture. Standardize: every
reel pushed to FB should carry the full caption, not a stripped one.

## Baseline (2026-06-15 pull)
- **Followers: 1,737** · Following: 804 · Posts: 68.
- **Post-surge plateau:** Daily reach peaked Jun 1–2 at ~58k/day, driven by "born to be a fighter"
  reel (now 362k views). Surge has tapered to ~3–5k/day as of Jun 10–14. Still well above
  pre-surge baseline (~5/day). Window is still open but closing — urgency to post.
- **Net new followers since Jun 5:** ~86. **Since surge started (May 24):** ~+323 new followers.
- Latest raw data: pull fresh; nearest report in `analytics/reports/2026-06-15.md`.

## Profile conversion snapshot (2026-10-24, Buzzfy, last 30 days)
- Followers 2,043 (net +15 in 30 d: 59 follows, 44 unfollows). Following 993.
- Reach 63.3k, 99.7% non-followers. Profile views 409, website clicks 4 (1%).
- **Grid frozen since 2026-09-24:** every reel after that is a MANUAL trial reel (`on_profile_grid: false`),
  so visitors land on a grid topped by two Stance pitches ("Comment STANCE") from September.
- Bio: "🇨🇭🇧🇷 in Bangkok / Fighter rebuilding from broken leg + ACL tear / I help fighters stop training
  random / ⬇️ Find your weakness + Stance waitlist", link matteofights.me. Name field: "Matteo".

## Biography (as of Jun 15)
> 🇨🇭🇧🇷 in Bangkok  
> Fighter rebuilding from broken leg + ACL tear  
> I help fighters stop training random  
> ⬇️THE PROTOCOL UFC fighters use (FREE)

Key change: now leads with vulnerability/injury story before the value prop.

## Top reels all-time by interactions

| Hook | Views | Likes | Shares | Saves | Comments | Interactions |
|---|---|---|---|---|---|---|
| 6 SIGNS YOU WERE BORN TO BE A FIGHTER (Jun 1) | 363k | 5,890 | 274 | 899 | 96 | 7,423 |
| 8 WAYS TO FIGHT LIKE A KILLER WITHOUT SPARRING 5X/WEEK* | 161k | 2,744 | 301 | 1,938 | 64 | 5,091 |
| 7 WAYS TO GET SMARTER WITHOUT TAKING DAMAGE (May 30) | 34k | 766 | 124 | 684 | 16 | 1,608 |
| 8 WAYS YOU CAN TRAIN BOXING ANYWHERE* | 27k | 633 | 148 | 664 | 18 | 1,482 |
| 7 WAYS TO BUILD FIGHT IQ WITHOUT SPARRING EVERYDAY* | 32k | 713 | 112 | 624 | 15 | 1,480 |

*Older reels not in last-30d pull — stats from Jun-06 snapshot.

## Top reels last 30 days (May 17 – Jun 15)

| Hook | Posted | Views | Avg Watch | Saves | Shares | Interactions |
|---|---|---|---|---|---|---|
| 6 SIGNS BORN TO BE A FIGHTER | Jun 1 | 362,572 | 11.1s | 899 | 274 | 7,423 |
| 7 WAYS TO GET SMARTER WITHOUT TAKING DAMAGE | May 30 | 34,304 | 11.2s | 684 | 124 | 1,608 |
| 7 WAYS I DEVELOPED REAL POWER WITHOUT TOUCHING A WEIGHT | May 29 | 24,998 | 10.2s | 332 | 32 | 656 |
| 8 SIGNS YOUR FIGHT CAMP ISN'T PREPARING YOU | Jun 7 | 12,748 | **13.3s** | 18 | 1 | 62 |
| HARD SPARRING TOO EARLY (6 SIGNS NOT READY) | Jun 5 | 13,058 | 12.2s | 29 | 4 | 129 |

## What drives each metric

**Likes** — agreement/emotional resonance. Like rate is similar across archetypes (~1.5–1.7%). Raw
like count follows view count, not format. Identity wins on total likes because it reaches more people.

**Saves** — 100% tactical, driven by barrier removal. Identity saves at ~0.25%; tactical saves at
1.2–2.5%. People save tips to use later; they don't save identity statements. Save rate benchmark:
`train anywhere` = 2.46% (highest), `fight IQ without sparring everyday` = 1.95%, `killer without sparring 5x/week` = 1.20%.

**Shares** — two mechanisms:
- Identity shares: "this is me" expression, amplified by CTA framing ("Repost so born fighters
  find out who they are" = sharing feels like a *gift*, not self-promotion)
- Tactical shares: "my friend needs this" — most shareable hook = `fight like a killer without sparring 5x/week` (301 shares)

**Comments** — low unless explicitly invited. `Drop a 🥊 if...` drives emoji engagement. A real
question or contrast at the close gets actual replies.

**Avg watch time** — viral threshold ~10–13s; flops sit at ~5–7s. Jun 7 fight camp reel hit 13.3s
(highest recorded) — data-heavy UFC PI research content holds attention longer. Identity reels hold
~10–11s when performing.

## Two viral archetypes (the engines)
1. **Tactical listicle** — `"X ways to [outcome] WITHOUT [requirement]"`. Drives **saves** (the
   algorithmic rocket fuel). Always a barrier-removal topic. 8 items > 6. Arrow format proven.
2. **Identity listicle** — `"X signs you [are/aren't a real fighter]"`. Drives **shares + reposts**
   via `Repost this so [specific person] [specific discovery]` CTA. "Born" framing (nature not skill)
   is most flattering and got 363k views.

**Watch time leader: data-heavy / research-backed content.** Fight camp reel (8 signs your fight
camp isn't preparing you, packed with UFC PI stats) hit 13.3s avg — highest in dataset. Worth
testing as a third archetype: `Research reveals` or `Data shows` framing.

## Hook precision matters enormously
The original "6 signs you were born to be a FIGHTER" hit 362k. The June 7 follow-up
"8 signs you were born to FIGHT" hit 2,618 views. Same structure, different hook — 138x difference.
Exact wording of the identity statement (what you ARE vs what you DO) is the variable.

## Barriers already covered (don't repeat these WITHOUT topics)
- Sparring too often / 5x a week ✓
- Sparring every day / fight IQ ✓
- No gym / train anywhere ✓
- No weights / weightlifting ✓
- No training partner (solo training) ✓ (Jun 7)

## Barriers not yet covered (high upside for next tactical reels)
- No coach / no access to coaching
- No natural size, reach, or physical gifts
- No years of experience ("too late to start" / "starting from zero")
- No money / cheap training
- No time (busy schedule framing — subhook territory, not done as a hook yet)

## Improved prototype rules (data-derived)
- **Tactical ceiling push:** 8 items, barrier-removal topic not yet covered, explicit `Save this
  before [specific action]` CTA, arrow format `[concept] [emoji] [title] → [elaboration]`
- **Identity ceiling push:** "born" framing or equivalent (nature, not skill), binary subhook
  (`Some people X. / Some people Y.`), list items that feel like psychological X-rays, CTA frames
  sharing as a service not self-promotion. **Hook wording is the key variable.**
- **Research/data angle (new, worth testing):** UFC PI data as hook — "The UFC tests every fighter
  for this." Long watch time performance suggests deep audience engagement with data-backed content.
- **Hybrid worth testing:** identity hook + tactical payload — `Some people train. Some people obsess.
  / 7 things obsessive fighters do that normal people think is crazy.`

## New format emerging: personal story / vulnerability reel
Jun 14 reel — "Started with kicks. No hands. Now I've got both. / This is what 2 years of training
alone looks like." — departure from the listicle format. Matches the new bio direction (injury,
rebuilding, showing up). Only 1,692 views so far (just posted). This format hasn't been tested
at scale but is the most authentic angle and aligns with what the bio is now leading with.

Short entertainment clips (Jun 9 Canelo/Crawford, Jun 12 "Tag your bro" sparring) get decent
engagement rates (7%+) but low reach — good for warmth and relatability, not for growth.

## Posting cadence (Jun 5–14)
12+ reels in 10 days — high volume. Most performing at 2–14k views. The surge created a
backlog-posting window. Cadence can probably throttle back to 1/day and focus on hook quality.

## Account history (full Windsor view, Sep 2025 – Jun 2026)

The account started September 2025 with generic algorithmic content (short tech clips, keyword-stuffed
captions, no consistent format). Views sat at 1,500–3,000 range. Breakthrough came January 2026.

**Key milestones:**

- **Nov 18, 2025** — "4 boxing drills to feel lighter on your feet": 1,984 views but **15.1s avg watch** —
  highest watch time in the entire account history. Demo/tutorial format holds attention longest.
- **Dec 18, 2025** — Boxing vs Muay Thai sparring clip: 5,933 views, **13.0s avg watch** — real
  sparring footage also holds very high watch time.
- **Jan 17, 2026** — "8 ways to build elite-level fight shape on a busy schedule" (the "busy schedule / fight like a killer" reel):
  **161,410 views**, 5,097 interactions, 12.7s avg watch — **the original breakthrough reel**.
  Hook proved the format worked; seeded the Jun 1 surge.
- **Feb 13, 2026** — "8 ways you can train boxing anywhere": 27,383 views, 1,480 interactions —
  confirmed the tactical barrier-removal format.
- **Jun 1, 2026** — "6 signs born to be a fighter": 362,572 views — current peak.

**Watch time hierarchy (all published content):**

| Reel | Avg Watch |
|---|---|
| 4 boxing drills for footwork (Nov 2025) | **15.1s** |
| 8 signs fight camp isn't preparing you (Jun 2026) | 13.3s |
| Boxing vs Muay Thai sparring (Dec 2025) | 13.0s |
| Fight like a killer / busy schedule (Jan 2026) | 12.7s |
| 6 signs not ready to spar hard (Jun 2026) | 12.2s |
| Born to be a fighter (Jun 2026) | 11.1s |
| Fight IQ without taking damage (May 2026) | 11.2s |

Demo/tutorial and real sparring footage consistently holds the highest watch time — even above viral listicles.

## Note on archived and trial reels
Windsor uses Instagram's Graph API which **does not return archived or trial reels** — only live
published content is accessible. To view archived/trial content, check the Instagram app directly.
The profile shows 68 total posts; Windsor surfaces ~65, meaning ~3 items may be archived.

## Useful Windsor fields (instagram)
- Profile: `followers_count`, `follows_count`, `media_count`, `biography`, `username`.
- Daily series: `reach`/`reach_1d`, `views`, `follower_count_1d` (last 30 days, excl. today).
- Per media: `media_caption`, `media_permalink`, `media_type`, `timestamp`, `media_reach`,
  `media_views`, `media_saved`, `media_shares`, `media_engagement`,
  `media_reel_avg_watch_time` (ms), `media_reel_total_watch_time` (ms),
  `media_reel_total_interactions`, `media_like_count`, `media_comments_count`.
