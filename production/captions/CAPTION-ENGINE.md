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

### 2) SUBHOOK (caption opener, 2 lines)
The first thing in the caption, mirroring the on-screen hook with a beat of tension:
- Tactical: `You don't need [expected requirement] to [outcome].`
- Identity: `Some people [do the easy thing]. / Some people [are built for the hard thing].`

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

## GOLD-STANDARD REFERENCES (real top performers)
- Identity, 320k views: `6 signs you were born to be a fighter` → "Repost this so the born fighters
  find out who they are."
- Tactical, 160k views (1,937 saves): `8 ways to become dangerous without living in the gym`.
- Tactical, 27k (664 saves): `8 ways to train boxing anywhere`.

## OUTPUT LOCATION
Save each generated reel as a draft:
```
content-bank/captions/drafts/<YYYY-MM-DD>-<slug>/reel.md
```
Use the scaffold: `node production/captions/new-reel.mjs "THUMBNAIL HOOK"` (creates the folder +
a templated `reel.md` to fill), or write `reel.md` directly following the template in that script.
