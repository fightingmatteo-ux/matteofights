---
name: competitor-ideas
description: Turn competitor outliers (production/competitors/outliers.json) into idea cards for @matteofights (production/competitors/ideas.json), adapted to Matteo's real story and voice, with a version per platform. Use for the weekly Monday ideas run, when asked for video ideas from competitors, or to add/clean competitor accounts.
---

# Competitor ideas (@matteofights)

Outliers prove an idea worked for someone like Matteo. The job: find the transferable pattern, then write the version
only Matteo can make. Never copy a creator's hook, script or footage.

## 0. Read first
`context/creator-voice.md`, `context/voice.md`, `context/founder.md` (the only facts "I" may use), `context/content.md`
(pillars), `production/competitors/outliers.json` (rule: >= 3x the creator's own median), the current
`production/competitors/ideas.json` (don't duplicate a card or reuse a skipped outlier) and
`python3 -P tools/threads/report.py` (what already works on Matteo's own account).

## 1. Triage new outliers
New = `first_seen` since the last `updated` in ideas.json. For each:
- **Skip** it (add the id to `skip`) when it isn't combat sports or fighter life, needs something Matteo doesn't have
  (a famous guest, a gym business, kids' classes), or only worked because of who posted it (a celebrity moment).
- **Group** the rest by pattern, not by topic: the same shape across different creators is the strongest evidence.
  Two or more outliers from different creators beat one big one.

## 2. Write a card per pattern (2 to 5 new cards a week, quality over count)
Shape (keep it exactly, the control center renders it):
```
{"id": "<kebab-slug>", "title": "<short name>", "status": "new",
 "evidence": [{"id", "platform", "handle", "name", "views", "x", "url", "hook"}],   copied from outliers.json, best first
 "pattern": "<the transferable shape in one sentence>",
 "why": "Likely why: <hypothesis>. <the real numbers>",
 "version": {"format": "<format + length>", "hook": "<ALL CAPS hook in Matteo's voice>",
             "beats": ["<3 to 5 talking points or list items>"], "needs": "<what Matteo must supply, or 'Nothing'>"},
 "platforms": {"instagram": "...", "facebook": "...", "tiktok": "...", "youtube": "<keyword-first Short title>",
               "threads": "<kind>: '<a ready Threads text in his voice, <= 500 chars>'"}}
```
- **"why" is a hypothesis**, say "Likely why", and show the numbers. Never present a guess as fact.
- **Matteo's version** uses his real material: Bangkok, Koh Samui, the KO that went down as a draw at 16, BJJ then the
  street fight and knee, the fibula, ACL surgery, the mindset pivot, the builder lane. Use clips from his own folder,
  never the creator's footage.
- **Formats** must be makeable by the system: listicle / statement / iykyk factory reels, talking head (talking
  points), voiceover b-roll, Threads text. Prefer patterns the listicle factory can produce without Matteo filming.
- Any number in the hook or beats (costs, stats) must come from Matteo or a named source; otherwise put it in `needs`.
- Run every Threads text and hook through the creator-voice rules (no em dashes, no motivation lines, no bait).

## 3. Save and ship
Update `updated` (YYYY-MM-DD), append new cards (newest first), keep `skip` current, validate
`python3 -c "import json;json.load(open('production/competitors/ideas.json'))"`, commit
`competitors: ideas <date>` and push to master (pull --rebase, retry 3x). Matteo sees them under Results > Rivals and
taps "Use this idea" to send one to his idea queue. Don't message him.

## Accounts
`production/competitors/accounts.json` lists who is measured. Add a creator only when they are close to Matteo
(combat sports plus mindset, psychology, self-improvement, documenting the journey, or fighting plus building) and
the account is readable: Instagram must be a creator/business account (test with
`python3 -P tools/instagram/competitors.py <handle>`), YouTube needs >= 8 Shorts. TikTok, Threads and Facebook can't
be read for other accounts: their versions come from Instagram and YouTube outliers.
