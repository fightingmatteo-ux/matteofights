---
name: platform-captions
description: Write @matteofights reel hooks, subhooks and captions (production/listicles/hooks.json) from the account's own numbers, in Matteo's real voice, so every platform's version (Instagram source, then Facebook, YouTube, Threads via tools/crosspost/captions.py) performs. Use for the Saturday hook batch, any new hook or caption, rewriting a caption, or carousel/slide copy for @matteofights.
---

# Platform captions (@matteofights)

One Instagram caption is the source. `tools/crosspost/captions.py` reshapes it for Facebook (short hook + list +
question), YouTube (keyword title + description) and Threads (hook + list + question, no hashtags). So: write the
Instagram caption well **and in the shape captions.py can parse**, and every platform gets a good version.

## 0. Read first (every time)
1. `context/voice.md`, `context/creator-voice.md` (bans, breadth, evidence), `production/captions/CAPTION-ENGINE.md`
   (archetypes and structures), `context/viral-format.md` (the proven posts), `tools/listicle/README.md` (formats,
   weekly mix, lifestyle lane).
2. **The numbers:** `python3 -P tools/threads/report.py` (Instagram section: formats and hooks by
   **follows per 1k views**, the account's winner metric) and `production/reels/LEDGER.md` "Patterns so far".
   Lean the batch toward what grows the account; groups with n < 5 are hints only.
3. Every existing hook and caption in `production/listicles/hooks.json`: never repeat a hook frame, list item or
   opener that's already there.

## 1. Choose before writing
- **Format mix** (tools/listicle/README.md): ~7 listicles, ~3 statements, 1 to 2 iykyk, 2 to 3 lifestyle-for-fighters,
  ~2 builder per 14. Move it toward formats that win on follows per 1k once n >= 5.
- **Archetype:** identity (shares, reach) vs tactical (saves). Identity leads on this account (contrast beat
  instruction about 7x); alternate, never two tactical in a row.
- **Hook frame:** the "You don't need X to Y" frame is spent (2,814 -> 20 likes + comments). Covered barriers
  (sparring often, no gym, no weights, no partner) are off the table. Prefer contrast, recognition ("signs you"),
  misconception flips ("People think combat sports is just violence."), insider moments.
- **Breadth:** most hooks should pull in anyone who trains or competes, framed through fighting (creator-voice.md).

## 2. Write the package
- **Hook** (on screen): ALL CAPS, <= 12 words, the curiosity gap does the work.
- **Subhook** (2 lines, also the caption opener): two groups or two things set against each other, concrete.
  Gold standard: "Some people train for fun. / Some people were built for this."
- **Caption, in this exact shape** (captions.py depends on it):
  ```
  <subhook line 1>
  <subhook line 2>

  <N signs / ways ...:>          (listicle; statement lists skip this line)

  1. <item>
  2. <item>
  ...

  <one CTA line>

  #tag #tag #tag
  ```
  - Items: what the viewer recognises or can use, concrete, one line each, no filler emoji chains. The most
    counterintuitive item earns a mid-list spot; the last item lands.
  - **CTA, one line, matched to the goal:** identity -> "Repost this so <the right people> find it." (drove the
    331k reel); tactical -> "Save this before your next session."; iykyk -> tag a training partner. The DM "HELP"
    funnel only when Matteo asks for conversion (growth is the goal now).
  - 2 to 4 combat hashtags (voice.md list).
  - iykyk: one-line caption + the tag line, no list. Builder: fighting teaches building, no business-guru tone, no
    Stance plug. Lifestyle: still speaks to fighters ("WHAT I EAT BEFORE A FIGHT"), never generic wellness.
- **First person** only for founder.md facts (creator-voice.md).

## 3. Review like Matteo would
Same five questions as threads-writer step 3: real, concrete, reply/share-worthy, wide enough, not a repeat.
Read the Threads and Facebook versions in your head: `python3 -c "import sys;sys.path.insert(0,'tools/crosspost');import captions;print(captions.threads(open('caption.txt').read(),'HOOK'))"`
style check on one caption if unsure.

## 4. Save and check
- hooks.json entry: `{"id", "archetype", "hook", "subhook": [l1, l2], "caption", "status": "ready", "format",
  "clip_id"}` (clip_id per the daily check's rules).
- Gate: `python3 -P tools/threads/lint.py --captions` must exit 0; read the warnings.
- Commit and push with the batch.

## Learnings
- _Add one line with numbers and date when the ledger settles a pattern (n >= 5)._
