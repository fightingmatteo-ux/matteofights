# Caption Engine — hook → subhook + caption

_The repeatable method for turning a hook into a ready-to-post reel package. In Phase 2 the agent
(or Claude in-session) runs this by hand; in Phase 3 the Jarvis backend runs it as a tool. Always
read the brain first: [viral-format.md](../../context/viral-format.md),
[voice.md](../../context/voice.md), [audience.md](../../context/audience.md),
[strategy.md](../../context/strategy.md)._

---

## INPUT
A **hook** (a topic or a finished hook line). If only a topic is given, write the hook first using
the formulas below.

## STEP 1 — Pick the archetype
Decide which engine the reel runs on (see [social.md](../../context/social.md) for why):

- **TACTICAL** → drives **saves**. Hook shape: `[N] WAYS TO [OUTCOME] WITHOUT [REQUIREMENT]`.
  Use when the payload is *usable tips* a beginner saves to apply.
- **IDENTITY** → drives **shares/reposts**. Hook shape: `[N] SIGNS YOU [ARE / AREN'T A REAL FIGHTER]`.
  Use when the payload is *recognition* — statements that make the viewer feel seen.

Alternate archetypes across the posting schedule; don't run the same one twice in a row.

## STEP 2 — Produce three outputs

### 1) THUMBNAIL TEXT (the on-screen overlay)
The hook, **ALL CAPS**, for the red-on-black overlay burned onto the footage. ≤ 12 words, breaks
cleanly across ~3 lines. This is the curiosity gap — the `WITHOUT` (tactical) or the `SIGNS`
(identity) does the work.

### 2) SUBHOOK (on-screen text under hook + caption opener — same text)
The subhook is the text that appears **on-screen under the hook** in the video AND also opens the
caption. Same words in both places. It is the first thing the viewer reads in the caption.

- **Identity:** 2-line binary contrast. Frame two types of people, one of whom the viewer wants
  to be. Short. No hedging.
  Line 1: `Some people [do the easy/common thing].` / `Some people [are built different / were made for this].`
  Line 2: points at a specific number — `Most fighters never figure out #[N].` Pick the most
  counterintuitive item on the list; don't default to #4, earn it.
  Gold standard opener: `Some people train for fun. / Some people were built for this.` (331k views)

- **Tactical:** 1 bold counterintuitive statement + number pointer.
  Line 1: `You don't need [expected requirement] to [aspirational outcome].`
  Line 2: `Most fighters never figure out #[N].` — point at the item that surprises people most.
  Gold standard: `You don't need to live in the gym to become dangerous.` (161k views)

### 3) CAPTION (full, in voice)
**Tactical structure:**
```
[subhook]

Here are [N] ways to [outcome] without [requirement]:

1. [Concept] [emoji] [short title] → [one-line elaboration]
... (N points)

Drop a 🥊 if [relatable beginner truth]
DM "HELP" if [specific free-advice offer]

[2–4 niche hashtags]
```

**Identity structure:**
```
[subhook]

[N] signs you [identity statement]:

1. [short identity statement — what they DO, not a tip]
... (N points)

Repost this so [real fighters / the right people] find it.

[2–4 niche hashtags]
```

---

## RULES (non-negotiable — from the brain)
- **DM trigger is always `HELP`.** Never FIGHT/POWER/IQ/etc. (deprecated). One word, clean funnel.
- **Watch-time first:** the hook must land in the first line; each numbered point resets attention.
- **Direct address; avoid "I" in the hook.** Talk to the viewer.
- **CTA matched to archetype:** Tactical → save + `DM "HELP"`. Identity → `Repost this so…` (the
  share CTA is what detonates reach). An identity reel may add `Comment HELP` as a soft secondary.
- **2–4 hashtags, combat-niche only.** No generic/banned tags.
- **Beginners are the core audience** — usable, not gatekept. No "serious fighters only" gatekeeping
  except where the identity format intentionally flatters in-group status.
- **No Stance mentions** (per [strategy.md](../../context/strategy.md)).
- Emojis are fine in caption *content* (they're native to the format); never in file/UI chrome.

## GOLD-STANDARD REFERENCES (top 5 by interactions, pulled 2026-06-06)

| Rank | Archetype | Hook (on-screen thumbnail) | Interactions | Views | Caption opener (subhook) |
|---|---|---|---|---|---|
| 1 | IDENTITY | 6 SIGNS YOU WERE BORN TO BE A FIGHTER | 6,543 | 331k | `Some people train for fun. / Some people were built for this.` |
| 2 | TACTICAL | 8 WAYS TO FIGHT LIKE A KILLER WITHOUT SPARRING 5X/WEEK | 5,091 | 161k | `You don't need to live in the gym to become dangerous.` |
| 3 | TACTICAL | 8 WAYS YOU CAN TRAIN BOXING ANYWHERE | 1,482 | 27k | `8 ways you can train boxing anywhere. No gym needed.` |
| 4 | TACTICAL | 7 WAYS TO BUILD FIGHT IQ WITHOUT SPARRING EVERYDAY | 1,480 | 32k | `Sparring builds timing. Study builds IQ.` |
| 5 | TACTICAL | 7 WAYS I DEVELOPED REAL POWER WITHOUT EVER TOUCHING A WEIGHT | 544 | 22k | `You don't need a barbell to hit like a truck.` |

## OUTPUT LOCATION
Save each generated reel as a draft:
```
content-bank/captions/drafts/<YYYY-MM-DD>-<slug>/reel.md
```
Use the scaffold: `node production/captions/new-reel.mjs "THUMBNAIL HOOK"` (creates the folder +
a templated `reel.md` to fill), or write `reel.md` directly following the template in that script.
