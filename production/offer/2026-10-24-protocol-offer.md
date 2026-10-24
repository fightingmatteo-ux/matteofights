# THE PROTOCOL offer, rebalanced (draft, 2026-10-24)

Framework: the scale on @liamjohnston.ai's "Claude just learned to fix your offer" carousel, now checked against
his Offer Master skill (installed: `.claude/skills/offer-master` + 7 stage skills, MIT). Price on one side; PROMISE,
PROOF and GUARANTEE get stacked on the other until it tips. The skill's repo link is on slide 8
(github.com/Liamrjohnston/offer-master-skill), so no "comment Sold" needed.

Status: **draft only.** Nothing in `docs/protocol/` is changed. The live page changes only after Matteo's yes.

## The price (what a fighter actually pays)
It is free, but not costless: an email, about 3 minutes of questions, an 18-24 min session, and the
belief that a stranger's free workout is worth doing. "Free fitness content is thin" is the prior we
fight (research/05-trust-psychology.md). So the other side of the scale has to be heavy.

## Where the scale is today
| Weight | Now (data.js `UI_COPY.landing`) | Problem |
|---|---|---|
| Promise | "Find your biggest physical weakness. Get a workout built to address it." | No outcome, no time frame. "A workout" is the deliverable, not the result. |
| Proof | Matteo's story (Thailand, Switzerland, Rome, fibula, ACL) | Story is credibility of the person, zero proof the system works. No numbers, no other fighters. |
| Guarantee | "No spam, no newsletter." | Only guards the email. Nothing guards the result. |

## Rebalanced

### 1. Promise: specific result, specific time, specific place
Hook options (pick one). Rechecked with `/offer-master` rules: promise what we control (the test,
the plan, the 4 weeks of sessions), never a result with a time frame ("fix it in 4 weeks" was cut):
- **A.** "Find the one weakness costing you rounds. Get a 4-week plan built for it. At home, about 20 minutes a session."
- **B.** "3 minutes to find your weak link. A 4-week plan to train it, no gym needed."
- **C.** "Not another random workout: a plan built around the one thing holding your fighting back."
  (the "what free can't do" angle, answers "free fitness content is thin")

Why: the 4-week loop already exists (each protocol's progression ends "Week 4: retake the
assessment"), we just never sold it. CTA stays "Find My Weakness".

Subtitle: "The At-Home Fighter Performance System" becomes "Built for boxing, Muay Thai, kickboxing and MMA. No gym, no equipment."

### 2. Proof: stop telling, start showing
In order of what we can ship now:
1. **Count, live.** "[N] fighters have taken it" from the signup table (D1, kind `signup`). Only a
   real number, pulled at build time. Do not round up.
2. **Show the result before the email.** One example "Fighter Profile" screenshot on the landing
   page (the stat block). People trust what they can see they'll get.
3. **Show the mechanism.** One line under each workout: "Built from [X] sports-science studies on
   combat athletes" (count the sources in `production/protocol-v2/research/`, real number only).
4. **Borrowed reach.** "From the guy behind *6 Signs You Were Born To Be A Fighter* (331k views)."
   Identity proof the audience already recognises.
5. **Collect testimonials from now on.** The completion screen already asks optional questions: add
   "How did it feel? One line, I might share it." Then use real lines only, with permission.

### 3. Guarantee: on the result, not just the inbox
Proposal (needs Matteo to agree, it costs his time). Type "do the work", capped, per `/offer-guarantee`:
the score moving is not in our hands, so the guarantee is on what Matteo controls (a personal look):
> "Do your sessions for 4 weeks and retake the test. Stuck? DM me PROTOCOL with your result and I'll
> look at your answers myself and tell you what to change. This doesn't promise a score."

Cap: one reply per person (Matteo sets it, see Check these). Cost: his time, [minutes per reply] x
[DMs a week]. Every DM it produces is also a warm lead for the paid offer. Keep "No spam, no
newsletter" under the email field.

Lighter option if he doesn't want DMs: "Free forever. No card, no catch, no newsletter."

### 4. Lower the price further (the other side of the scale)
- Show the time cost up front: "3 min test, 20 min workout." Known cost feels smaller.
- Endowed progress: start the result screen at "Week 1 of 4: assessment done." (A-grade research, 05.)
- Keep the email as the only required field (form friction research, 05).

## Same frame for the paid offer (later)
The paid offer is still undefined (strategy.md). When it comes, build it on the same scale from day one:
promise = a measurable change by a date, proof = Protocol users' retest numbers (start logging
retest scores now so that proof exists), guarantee = result-based. The Protocol is where that proof gets made.

## Check these (questions for Matteo, from the `/offer-master` question bank)
1. How many people open matteofights.me/protocol in a normal month, how many enter an email, and how
   many finish a workout? (Without these we can't find the leak; first action is to count for 2 weeks.)
2. When people drop off or don't sign up, what do they say, word for word (DMs, comments)?
3. Will you personally answer the "stuck at week 4" DMs, and up to how many a week?

With those answers, run `/offer-master` on it for the full card (leak, lever scores, guarantee cost, one test).

## To ship (after Matteo's yes)
Edit `UI_COPY.landing` and `result.teaserSubtext` in `docs/protocol/data.js`, add the count and the
sample profile image, add the testimonial question to `OPTIONAL_FIELDS`.
