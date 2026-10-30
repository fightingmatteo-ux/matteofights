# Profile fix: more follows and link taps from profile visits (2026-10-30)

Live numbers (Buzzfy, 30 Sep to 30 Oct). Nothing here posts or changes anything; every step is Matteo's to do.

| | Last 30 days |
|---|---|
| Views | 193.1k (99.3% non-followers) |
| Profile visits | 662 |
| New follows | 88 (46 unfollows, net +42) |
| Follows per profile visit | 13% at most (some follows come straight from the reel, so the profile's real rate is lower) |
| Bio link taps | 3 (0.45% of visits) |

There's no reliable public benchmark for these rates (Meta removed profile views from the API in Jan 2025, so
nobody can measure them across accounts). We measure against ourselves: target 20%+ follows per visit and 3%+ link
taps per visit by 30 Nov.

> **Never share or pin the 2026-10-24 knockout-draw cuts (A/B/C).** Matteo 10-30: the KO story gets redone from
> a different angle; only the new version goes on the grid.

## Why visitors don't follow (in order of damage)

1. **The grid stopped on 24 Sep.** Every reel since then (about 70) is a trial reel and never reached the grid. The
   only one shared since is the 14 Oct "freeze" reel. Someone taps through from a sparring listicle and lands on a
   grid topped by two "Comment STANCE" app pitches from a month ago. The content they came for isn't there, so
   they have no reason to think there will be more of it. This is the biggest fix and it costs 5 minutes.
2. **The bio sells the wrong things.** Line 1 is an injury ("rebuilding from broken leg + ACL tear"), which reads
   "not fighting right now" to someone who just watched a fight-IQ reel. Line 2 ("stop training random") is vague.
   Line 3 asks for two things at once, and one is an app they've never heard of. strategy.md already says no
   Stance in the bio. Nothing says what they get by following.
3. **The name field is just "Matteo".** It's the only searchable text on the profile besides the handle. Nobody
   searching "muay thai" or "fighter" can find you.
4. **The reels don't show who's behind them.** Most listicles are text over clips. A visitor doesn't know the
   account is a real fighter until the profile, and then the profile doesn't make that clear either. The face
   reels hold attention far better: KO story 18.1 s avg watch, 66 comments; Saenchai 16.2 s; listicles 8-10 s.
5. **Highlights are labelled with emojis** (🔁, 🧾, 🥩🥦). Nobody taps a label they can't read.
6. **Following 991 vs 2,069 followers** looks like follow-for-follow. Small effect, but it costs trust.

## Why visitors don't tap the link

1. **The bio's link line is two asks** ("Find your weakness + Stance waitlist") and doesn't say what you get or
   how long it takes.
2. **"matteofights.me and 2 more"**: with 3 links, a tap opens a list first. One extra tap, three choices, fewer
   clicks. Keep one link.
3. **Your captions already send people to the DM** ("Comment PROTOCOL"). That's fine: those people get the link in
   the DM and never need the bio. So 3 bio taps understates interest. Count PROTOCOL DMs too
   (matteo-signup.pages.dev/api/signup).
4. **The landing page buried the offer.** On a phone, the first screen was the injury story; the PROTOCOL card
   started at the bottom edge. It also linked to TikTok (no account yet), back to Instagram, and said DM "HELP"
   (old trigger). **Fixed on branch `claude/profile-conversion`, not live** (see below).

## The fix (Matteo, about 20 minutes, in this order)

### 1. Share 5 reels to the grid (biggest lever)
Open each reel, `...` > "Share to profile" (or the trial reel's "Share to followers"). Best of the last 5 weeks by
saves and watch time:

| Reel | Views | Why |
|---|---|---|
| 8 ways to get fight fit without running (26 Oct) | 13.4k | Best reel this month, 149 saves |
| 7 ways to kill fight nerves (25 Oct) | 8.0k | Mindset, 81 saves |
| 6 ways to read your opponent in round one (25 Oct) | 5.5k | 3.2% save rate, best of the month |
| Saenchai: win the reset (21 Oct, "Always sparring someone bigger?") | 2.6k | Face + breakdown, 16 s watch |
| Most adults quit by week three (5 Oct) | 2.1k | 10% engagement, 24 shares, older audience |

Then keep doing it: every Sunday share the week's best 2 (STATUS item "Plan reels + older audience" point 3).
Once the grid has fresh reels, archive the two 24 Sep Stance pitches (or just let them slide down).

### 2. Pin 3
1. **Saenchai: "Always sparring someone bigger?"** (21 Oct, share it first): your face, 16 s watch. Holds the "who I
   am" slot until the re-angled KO story exists; then that takes it.
2. **Boxing power 3-day plan** (23 Aug, already pinned): proof you give real value; 6.8% save rate, best ever.
3. **6 signs you were born to be a fighter** (Jun): 331k+ views, social proof.
Unpin "Muay Thai vs Boxing technical sparring".

### 3. Name field
`Matteo | Muay Thai Fighter` (searchable: "muay thai", "fighter").

### 4. Bio (pick one, all under 150 characters, no Stance, no injury)
**Final pick (10-30, after Matteo: "the problem is the profile"). The name field already says Muay Thai Fighter,
so line 1 is proof instead (148 characters):**
```
🇨🇭🇧🇷 Bangkok · trained in 5 countries
For people who don't train for fun
Fighter mindset + sparring IQ, daily
⬇️ Free 4-week plan for your weak spot
```
Line 1 = why trust me, line 2 = who this is for (the subhook of the 331k reel), line 3 = what you get by
following (what they just watched), line 4 = one free thing, named the way people already ask for it (the
"Comment PLAN" reel got 164 comments). Link title: `Free fighter plan`.

**A (first draft):**
```
🇨🇭🇧🇷 Muay Thai fighter in Bangkok
For people who don't train for fun
Fighter mindset + training, daily
⬇️ Free: find your weak spot, get the plan
```
**B:**
```
🇨🇭🇧🇷 Fighting out of Bangkok
The mental side of fighting, from inside it
New lesson every day
⬇️ Free 4-week plan for your weakest area
```
**C:**
```
🇨🇭🇧🇷 Muay Thai fighter | trained in 5 countries
I post what fighters think, not just how they train
⬇️ Free: find your weak spot in 1 min
```
The injury story isn't lost: it goes in the "START HERE" highlight (and the re-angled KO reel once made).

### 5. One link
Edit profile > Links: keep only `matteofights.me`, title it `Free fighter plan`. Remove the other 2.

### 6. Highlights: words, not emojis, in this order
`START HERE` (who you are: first fight, 5 countries, the injury, 3-4 stories) · `FREE PLAN` (PROTOCOL walkthrough
+ link sticker) · `MY FIGHTS` (fight clips) · `FUEL`. Drop or rename `ARCHIVE`; rename the 🧾 one to `RESULTS` if
it holds screenshots of people's progress, else drop it.

### 7. Small ones
- Profile music "La Verdolaga": remove it unless it means something to you; it says nothing about fighting.
- Unfollow ~20 dead or random accounts a day until following is under 500 (no bulk, Instagram flags it).

## Landing page (done, needs Matteo's yes to go live)
Branch `claude/profile-conversion`, `docs/index.html` and `docs/links.html`:
- Hero copy: "Muay Thai fighter. First fight at 16. Trained in 5 countries. I post the mental side of fighting,
  every day." (was the injury list, with em dashes).
- Smaller hero on phones: the PROTOCOL card now starts at about half the screen (was at the bottom edge).
- Card: "Free · 1 minute / Answer 5 questions. Find your weakest area. Get the 4-week plan to fix it."
- Removed the Instagram link (they came from there) and TikTok (no account yet).
- DM button opens your Instagram DMs directly (ig.me/m/matteofights) with "Got a question about your training? DM
  me" (was DM "HELP", which no longer triggers anything).
Goes live when merged to master (GitHub Pages).

## How we'll know (Claude pulls every Sunday with ig_account_stats + ig_follower_growth)
| | Now (30 d) | Target 30 Nov |
|---|---|---|
| Follows per profile visit | 13% | 20%+ |
| Link taps per profile visit | 0.45% | 3%+ |
| Net followers | +42 | +150 |
