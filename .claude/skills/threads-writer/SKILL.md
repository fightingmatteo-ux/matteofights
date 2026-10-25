---
name: threads-writer
description: Write @matteofights' weekly written Threads posts (21 a week, 3 a day) from the account's own numbers, in Matteo's real voice. Use for the Sunday Threads batch, for single replacement posts, or whenever someone asks to write, rewrite or improve Threads posts for @matteofights. Reads tools/threads/report.py first, writes to production/threads/posts.json, gates on tools/threads/lint.py.
---

# Threads writer (@matteofights)

The job: posts that a real 19-year-old fighter would actually type, that people reply to, and that grow the
account. Not motivation-page content, not jargon only fighters get.

## 0. Read first (every time)
1. `context/voice.md`: how it sounds. `context/creator-voice.md`: how it stays real and what grows the account
   (bans, breadth mix, first-person rules, the evidence). `context/founder.md`: the only facts "I" may use.
2. **The numbers:** `python3 -P tools/threads/report.py`. Note which kinds, lengths and shapes get the most
   **replies per 1k views** (the main Threads lever), then shares per 1k. Trust only groups with n >= 5; the rest
   are hints.
3. `production/threads/posts.json` (everything already written, never repeat it) and the coming week's source
   listicles: `lst-*` items in `production/schedule/queue.json` + their `caption.txt`. Skim
   `production/reels/LEDGER.md` "Patterns so far" for angles that win on Instagram.
4. `production/control/briefs.json` → `threads.brief`: Matteo's standing direction for Threads from the dashboard.
   It wins over the defaults in this skill.

## 1. Plan the week before writing a word
- **Which week:** the 7 New York dates starting the day after the latest `at` in posts.json. If all 7 already
  have posts, stop.
- **Slots:** 3 a day at 07:30, 12:30, 17:30 America/New_York. Convert to UTC correctly: EDT = UTC-4 until the
  first Sunday of November, then EST = UTC-5.
- **Kinds (default mix):** 07:30 `take`, 12:30 `question`, 17:30 `tip` or `story`, plus about one `chain` a
  week (an opener + 3 to 5 replies in `chain`). **Let the report move this:** when a kind has n >= 5 and its
  median replies per 1k is clearly higher (about 1.5x the others), give it more slots; when one is clearly
  lowest, give it fewer. Keep ~20% of the week as deliberate experiments (a new shape, length or angle) so the
  report keeps learning. Write down the plan in one line per day before drafting.
- **Breadth:** ~60% broad (anyone who trains, competes or chases something hard gets it), ~40% craft. See
  creator-voice.md.
- **Sources:** each listicle feeds at most one post a day. Not every post needs a listicle: real fight knowledge
  and founder.md facts are fair sources too.
- **First person:** at most 3 posts, facts from founder.md only.

## 2. Write each post
- **Opener first.** The first line is what shows in the feed: <= 12 words, stands on its own, makes someone stop.
  Vary how openers start across the week (no two in a row the same way).
- **One idea.** Short lines, one idea per line, mostly 1 to 4 lines. Vary length: some one-liners, a few longer.
- **Reply-worthy, honestly** (creator-voice.md): a take with a reason someone can argue with, a question
  answerable in one line from their own training, a concrete choice, a confession prompt. Never bait.
- **Kinds:**
  - `take`: a real opinion and the reason, built from one listicle item or real fight knowledge. Ends where a
    reader could push back. Not a slogan.
  - `question`: a genuine question with concrete options or an easy personal answer. "Which one is you? 1/2/3"
    with three listicle items is allowed at most twice a week.
  - `tip`: one usable thing (training, nutrition, recovery, routine) with the why. Specific enough to try today.
  - `story`: a short lesson; first person only with founder.md facts, otherwise "you" or a named, real fighter
    or coach whose story is public and that you are sure of.
  - `chain`: opener post + 3 to 5 replies that each add something (not one idea cut into pieces).
- **Hard rules:** voice.md (no em dashes, no emojis, no hashtags, no links, no Stance plug, no "link in bio"),
  <= 500 characters per text and per chain item, no invented stats or experiences. `topic`: "Fight Psychology"
  for mindset, "Combat Sports" for training/lifestyle.

## 3. Review like Matteo would
For every draft ask, and rewrite if any answer is no:
1. Would Matteo type this on his phone, or does it sound like a quote page? (creator-voice "one test")
2. Is there a concrete thing in it (a moment, a body part, a round, a place), not just abstractions?
3. Would someone who trains have a reply? What would the first reply say?
4. Would a non-fighter who trains still get it?
5. Is it different from everything already in posts.json and from the other posts this week?
Then cut 20% of the words.

## 4. Save, check, ship
- Append to `posts` in `production/threads/posts.json`, keeping the format:
  `{"id": "th-MMDD-N" (N = slot 1/2/3), "at": "YYYY-MM-DDTHH:MM:SSZ" (UTC), "kind", "topic", "text",
  "chain": [], "from": "<listicle id or 'founder' or 'craft'>", "status": "queued", "approved": false}`.
- **Never set `approved` to true.** Only Matteo approves (Telegram or the control center).
- Gate: `python3 -P tools/threads/lint.py` must exit 0 (errors block). Read every warning and fix most of them.
  Also `python3 -c "import json;json.load(open('production/threads/posts.json'))"`.
- Commit `threads: posts for <first date>..<last date>` and push to master (`git pull --rebase`, retry up to 3
  times if the push races). The Cross-post workflow's notify step sends them to Matteo for one-tap approval.
  Don't message him yourself.

## How it learns
`tools/crosspost/stats.py` (every 2 h) measures posted posts, `tools/threads/collect.py` keeps the numbers in
`production/threads/results.json` for good, and `tools/threads/report.py` turns them into the brief in step 0.
Each week's plan is the last week's plan corrected by the numbers. When a pattern is clear (n >= 5 per side),
add one line to "Learnings" below with the numbers and the date.

## Learnings
- _None yet (first written posts went out 2026-10-16)._
