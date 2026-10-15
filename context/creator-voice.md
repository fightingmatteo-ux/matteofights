# Creator voice: sound like Matteo, not a motivation page

_Read with [voice.md](voice.md) before writing any Threads post, caption, hook or carousel copy. voice.md says how
the words sound; this file says how to make them feel like a real creator thought them, and what actually grows
the account. Enforced mechanically by `tools/threads/lint.py`._

## The one test
Would a 19-year-old fighter who trains in Bangkok type this on his phone between sessions, and would a friend who
trains reply to it? If it could hang on a gym wall as a poster, or run on a quote page, rewrite it.

## What makes it sound real
- **Concrete over abstract.** Name a real thing: the first body shot, a bad sparring day, cutting weight, the
  6am run, the coach calling time, shin bruises, hands dropping in round three. Not "the grind", "the journey",
  "the process".
- **An opinion with a reason.** "Hard sparring every week makes most beginners worse, not tougher. You learn to
  survive, not to fight." beats "Train smart."
- **Observed, not preached.** Describe what happens ("Everyone's brave until the first body shot.") instead of
  issuing commands ("Be brave.").
- **Some dryness is allowed.** A small joke, an understatement, a fragment. Not every post ends on a quotable line.
- **First person only for real facts.** "I" is allowed when the fact is in [founder.md](founder.md): karate at 7,
  first Muay Thai fight at 16 (the KO that went down as a draw), BJJ then a street fight that tore a knee ligament,
  broken fibula, ACL surgery coming, ruptured appendix the day before a fight, gyms in Zurich, Essaouira, Sao Paulo,
  Koh Samui, Rome. Never invent fights, results, feelings, quotes, numbers or opinions as "I". At most ~3 first
  person posts a week; second person stays the default.

## Wide enough to grow, true enough to stay
Fighting is the lens, not the gate. Most posts should land for anyone who trains, competes or chases something
hard: fear, nerves, discipline, ego, losing, starting late, comparing yourself, quitting. Target mix per week:
**~60% broad** (a gym-goer, a runner or a student gets it) and **~40% craft** (real fight knowledge that earns
respect from fighters). A craft post must still make sense to someone who doesn't know the term (teep, sprawl,
southpaw): add four words of context rather than a jargon wall.

## Never
- **Motivation-page lines:** rise and grind, grind never stops, no days off, embrace the suck, champions are made
  when no one is watching, stay hungry, level up, built different (unless the listicle literally uses it),
  this is your sign, reminder that, nobody is coming to save you, be the hardest worker in the room, trust the
  process, beast mode, alpha, sigma, let that sink in, read that again, unlock, elevate, journey, transform.
- **Structural tells:** the three-line aphorism stack ending on "That's the difference."; "It's not X. It's Y."
  in more than one post a week; "Most people... Fighters..." in more than one post a week; a list of three
  abstract nouns; every post ending on a mic-drop.
- **Fake precision:** invented stats or neat math ("93% of fighters", "52 fixes a year") unless the number comes
  from a real source that you name.
- **Engagement bait:** "Agree?", "Who's with me?", "Comment YES", "Drop a 🔥", "Like if". Threads downranks
  low-effort reply farming, and it reads as cringe. (Instagram captions may keep the account's proven
  "Repost this so..." line; see CAPTION-ENGINE.)
- **Life-coach or guru tone**, wellness words (voice.md), Stance plugs (unless Matteo asks), links, hashtags on
  Threads, em dashes anywhere.

## What actually drives growth (evidence, newest wins)
Own numbers (context/content.md, viral-format.md):
- **Contrast and identity beat instruction about 7x** on this account: the caption opener "Some people train for
  fun." (the 331k reel, 7,413 likes + comments) vs "Sparring builds timing. Study builds IQ." (1,004).
- **The "You don't need X to Y" frame is spent:** 2,814 -> 669 -> 176 -> 24 -> 20 likes + comments over seven
  months. Don't open with it unless the barrier is new and the payoff concrete.
- **Identity posts drive shares and reach; tactical posts drive saves.** Rotate them.
- Instagram reels are judged on **follows per 1k views** at 72 h (LEDGER.md), not raw views.

Threads (research 2026-10-16, mostly vendor analyses; Meta publishes no weights, so treat as defaults until the
account's own report says otherwise):
- **Replies are the strongest signal.** A post that gets people talking beats one that gets silent likes.
- **Early replies matter** (first 30 to 60 minutes): Matteo replying to the first comments is the biggest lever,
  and it stays manual.
- **Since Nov 2024 Threads favours accounts people follow** over unconnected recommendations, so posts must also
  reward existing followers, not only chase strangers.
- **Bait is downranked** (see Never).

**The account's own report wins over all of the above** once a group has n >= 5:
`python3 -P tools/threads/report.py`.

## Reply-worthy, honestly
A reader replies when they have something to say. Give them that, without asking for it:
- a take they can disagree with **and** a reason they can argue with,
- a question they can answer in one line from their own training ("What did your first coach get wrong?"),
- a choice between concrete options ("Cardio, hands or head: which goes first in round three?"),
- a small confession prompt ("The thing you still do from your first month of training, even though you know it's wrong.").
