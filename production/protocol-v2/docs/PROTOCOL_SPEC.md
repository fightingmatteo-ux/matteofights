# THE PROTOCOL — Product Specification

The At-Home Fighter Performance System. Free lead magnet at `matteofights.me/protocol`, built on the research in `PROTOCOL_RESEARCH.md`. This document is the build target — every decision below traces to a research finding or an explicit brief requirement; where it deviates from the original brief's proposed structure, the deviation and its reason are called out inline.

---

## 1. Target user / ICP

Primary: a beginner-to-early-intermediate boxer, Muay Thai fighter, kickboxer, or MMA athlete who already trains 2–6 times a week but has no structured strength & conditioning — the person `audience.md` already describes as training "random." They have a job or studies, limited or no gym access, and want to get genuinely dangerous without unlimited training time. Secondary: the broader fighter-identity audience the account's viral reels already reach, who may not train seriously yet but want to see themselves as the kind of person who does.

Not the target: someone who wants motivation without execution, or an elite/professional fighter who already has a full sports-science team — the product is honest that it's a foundation, not a replacement for a coach's eye.

## 2. Core promise

A complete, evidence-informed training system across six performance categories — Power, Speed, Conditioning, Footwork, Strength, Mobility — that a self-coached fighter can run from a phone, in almost any space, alongside their existing combat training, with the "why" explained at every step.

## 3. Positioning

**"Built in public by someone earning it, not claiming it."** Matteo isn't presenting as a credentialed sports scientist or a title-holder — he's a fighter rebuilding from injury, sharing the system he's building and using himself, with the reasoning shown, not just the instructions. Practicality — no equipment required, works in a bedroom, hotel room, or park — is supporting proof of that honesty, not the headline claim. This directly answers the research finding that "no equipment, works anywhere" is now commodity copy across the category, and that the one asset FightTrainer, Fight Plan Pro, and the anonymous-app tier structurally lack is a real, visible, audience-building creator (`PROTOCOL_RESEARCH.md` §4).

Tagline: **THE PROTOCOL — The At-Home Fighter Performance System.** Sub-line: *Build power, speed, conditioning and movement from almost anywhere — the system I use and the reasoning behind it.*

## 4. Training philosophy

Five load-bearing beliefs, each stated to the user somewhere in the product because they double as trust signals (research §1–2 shows explaining mechanism builds perceived expertise):

1. **Your legs and trunk throw the punch, not your arm.** Strength training here prioritizes lower-body and rotational-core work over pressing volume — the opposite of the "big bench = big punch" assumption.
2. **Fatigue takes your power before it takes your technique.** Conditioning is trained as repeat-effort ability (short maximal bursts, incomplete recovery, mirroring real round structure) plus a real aerobic base — not generic "get tired" cardio.
3. **One rule drives every session's progression.** Hit the top of your rep range with 1–2 reps left in the tank on every set → add reps. Hit the top of the range → make it harder and drop back down. No RPE math, no 1RM required.
4. **Sparring outranks the app.** Power and heavy strength work always yield to sparring recovery — never scheduled in the 24–72h after a hard sparring session, never in the hours right before one.
5. **A foundation, not a finish line.** The six sessions are a complete standalone system. What comes next — more depth, more specialization, live coaching, other fighters to train with — is a different kind of value, not a withheld piece of this one.

## 5. Evidence-informed principles

Full detail and grading in `PROTOCOL_RESEARCH.md` §1. Summary of what shapes programming:

- Legs (39%) and trunk (37%) supply most punch force; upper body (24%) is the smallest contributor [MODERATE].
- HIIT/repeat-effort training is the best-evidenced conditioning modality reviewed — two independent meta-analyses converge [MODERATE-STRONG].
- Bodyweight training builds real strength and hypertrophy up to a real, physics-based ceiling; one piece of external load (a band, one adjustable dumbbell/kettlebell) removes most of that ceiling [STRONG].
- Double progression outperforms RPE-based prescription for a self-coached, no-1RM population [MODERATE-WEAK evidence for RPE unreliability in novices, but converges with three independent design advantages — see research §1].
- No combat-specific mobility RCTs exist; mobility content stays in "sound practice" language.
- Plyometric transfer to striking-sport performance specifically is only trivial-to-small; never promise a quantified power gain from it.

## 6. Exercise selection principles

Every exercise in the system is written against the brief's eleven-question standard before inclusion. In practice this becomes five fields attached to every exercise in the content data (see §16, `data.js` schema):

- **`goal`** — the specific adaptation this exercise targets (not generic "strength")
- **`cue`** — one sentence, the single most important coaching point
- **`mistake`** — the most common way this exercise gets done wrong
- **`progress`** — the next step once it's mastered
- **`regress`** — the fallback if it's currently too hard or the athlete is fatigued/sore

An exercise is cut if it can't produce a real answer to "what adaptation are we trying to create" and "can a beginner understand it without a coach in the room" — this is the filter that keeps the library at "one genuinely complete workout per category" instead of a padded exercise list.

## 7. Complete workout architecture

Six sessions, matching the brief's six categories exactly — the research (§1, shared-core finding) confirms this is the right cut, not an arbitrary one, because it maps to real, distinct training qualities rather than marketing categories.

Every session follows the same shape, so the UI (§11) only needs to be built once:

```
Session
├─ Goal (1 sentence — what this session builds)
├─ Difficulty (Foundation / Building / Advanced — self-selected, not gated)
├─ Equipment (default: none; "with equipment" variant where relevant)
├─ Duration (15–40 min, stated up front)
├─ Warm-up / prep (3–5 min)
├─ Main blocks (2–4 blocks, each with 2–4 exercises)
├─ Cool-down (2–5 min)
├─ Coaching note (the "why," 2–4 sentences, in Matteo's voice)
├─ Common mistakes (2–3, session-level)
└─ When to stop (a specific, honest stop-rule — e.g. "if your rear-leg drive
   is visibly slower on the last 2 reps than the first 2, stop the set")
```

**The six sessions, each grounded in a specific research finding:**

1. **Power** — plyometric progressions dosed by foot-contact volume (not vibes), overcoming isometrics, rotational throws. Framed honestly: builds real power, doesn't promise a quantified striking-power increase.
2. **Speed** — lower-body power work (drives punch/kick velocity more than arm-speed drills) + reactive-agility work trained as a distinct quality from pure change-of-direction drills.
3. **Conditioning** — split into an aerobic-base block and a repeat-effort/HIIT block, explicitly explained as two different systems (research §1: aerobic = between-round recovery, not peak output).
4. **Footwork** — agility-ladder/tape patterns, pivot-and-angle shadowboxing, near-zero equipment by nature.
5. **Strength** — split-squat family, Nordic-curl progressions, push/pull/dip progressions, rotational + anti-rotational core, loaded carries. Framed around legs/trunk as the primary lever, upper body as support.
6. **Mobility** — hip/ankle/shoulder/thoracic, dynamic pre-training + static post-training + loaded end-range holds. Conservative claims throughout — "keeps you moving and durable," never "proven to prevent injury."

Two small, clearly labeled optional branches sit alongside the six core sessions rather than forking the whole product (research §1, shared-core-vs-divergence finding):

- **Kicking add-on** (Muay Thai / kickboxing / MMA) — hip/pelvis rotational ROM, shin/ankle load tolerance.
- **Clinch add-on** (Muay Thai / MMA) — isometric neck, grip, and hip-drive endurance.

A boxer skips both with zero loss of completeness — this is what keeps one product genuinely serving four sports instead of becoming generically useless (research §1).

## 8. Progression system

**The rule, stated once, in one sentence, and repeated at the top of every session:** *When every set in a session hits the top of its rep range with 1–2 reps left, add reps next time. Once you're at the top of the range, make the movement harder and drop back to the bottom.*

"Harder" resolves through a fixed ladder so it never requires judgment calls the athlete can get wrong: harder leverage/variation → unilateral shift → reduced rest / increased density → slower tempo/eccentric. Every exercise's `progress` and `regress` fields point along this same ladder in both directions.

**Regression** is always visible, never hidden behind a "too advanced" wall — every exercise shows its regressed version inline, so a sore, fatigued, or beginner athlete always has a legal fallback rather than skipping the session.

**Monitoring:** two cheap inputs, nothing more (research §1, monitoring finding). After each session: RPE (1–10) × duration → logged automatically as session load, no math shown to the user. Once daily: a 3-question check (sleep, soreness, fatigue, 1–5 each, under 15 seconds to complete). No Acute:Chronic Workload Ratio, no wearable integration in v1 — both are explicitly out of scope per the research (§1, §6).

**No hardcoded deload week.** Instead, if the wellness check or session-load trend signals accumulated fatigue, the app surfaces a plain-language "back off" recommendation — mobility/conditioning only for a few days — rather than forcing a fixed 4-week cycle the evidence doesn't clearly support at this training volume.

## 9. Weekly programming

These are the S&C session days layered onto an athlete's existing combat training (2–6 sessions/week) and sparring (0–2/week) — not a replacement for it. The one hard rule threaded through every template: **power/strength work moves away from sparring; mobility/conditioning can move toward it.**

**3 days/week** (for an athlete already doing 4–5 combat sessions + 1–2 sparring):
- Day A — Strength (full body)
- Day B — Power + Speed (placed on a day with no sparring within 24h either direction)
- Day C — Conditioning + Mobility

**4 days/week:**
- Day A — Lower Strength
- Day B — Power/Speed
- Day C — Upper Strength
- Day D — Conditioning + Mobility

**5 days/week** (higher-volume week; extra days stay low-fatigue-cost, not extra hard sessions):
- Day A — Lower Strength · Day B — Power/Speed · Day C — Upper Strength · Day D — Conditioning · Day E — Mobility + light aerobic

The app presents these three as starting templates the user picks once (matching their real training days), not a rigid calendar — sessions can be dragged to different days, with a plain-language warning (not a hard block) if the user schedules power/strength within 24h of a sparring day they've marked.

## 10. Safety considerations

- **Sparring-fatigue rule is enforced in the scheduler UI**, not just written as advice (§9).
- **Claims-to-avoid list is binding on all copy** (research §1, §6): no "this builds your punch power by X%," no "static stretching before training hurts your power" as a blanket statement, no "cardio kills your gains," no presenting any mobility protocol as proven to prevent injury, no citing a single study as settled consensus.
- **Generic medical disclaimer**, stated once on first use, not repeated as nagging boilerplate: this is a training system, not medical advice or a replacement for in-person coaching; stop any exercise that causes sharp or worsening pain and see a professional.
- **"When to stop" is written per-session, specifically** (§7) — not a generic "listen to your body" line, but a concrete, observable signal (e.g., visible slowdown, form breakdown, a named symptom).

## 11. UX architecture

Mobile-first, single-page web app, no login, no native app. Built lean specifically because the mobile-UX research (§3) identifies load speed as the single biggest completion risk for a cold Instagram-referral visitor — this rules out a heavy JS framework for what is fundamentally a content-and-timer app.

**Flow (as shipped — refined from the original 8-step draft above by a follow-up brief that specified the assessment/gate sequencing precisely):**
1. **Landing** — hero hook, the six categories shown as a grid, one CTA into the assessment. No email wall here (research §2 — deliver value before asking).
2. **Assessment — "Find Your Fighter Weakness"** — 5 questions, ~60–90 seconds, one per screen with a progress-dot indicator and an in-assessment Back button. Q1–Q3 score the six categories (weighted 3/2/2 — see `docs/protocol/README.md` for the exact scoring logic); Q4–Q5 are segmentation only (training frequency, equipment access) and never affect the result.
3. **Result — teaser, then a single-field email gate.** Immediately on finishing Q5: the primary category headline and one teaser sentence appear (real value shown before any ask), directly below which sits one email field and nothing else — no name, no Instagram handle, no second question. Submitting invalid or empty input shows an inline error and never unlocks; a valid email unlocks instantly, client-side, regardless of whether the webhook call itself succeeds (see §12).
4. **Result — unlocked.** The full "why" explanation (grounded in the user's own Q1 answer, never generic), the secondary focus named, and the exact matching workout (title/duration/equipment) — with **Start Your Workout** as the primary action. This is the workout for their *primary* result specifically, not a generic hub — matching the explicit instruction to hand over the actual workout immediately, with no second signup gate. A **Browse all 6 Protocols** link is also available for a user who wants to explore beyond their result.
5. **Workout player** — one step at a time, focus mode: exercise name large, up to 3 coaching cues, a collapsible "more detail" section (mistake/easier/harder), and either a countdown timer (time-based exercises) or a **Done** button (rep-based exercises, since reps can't be auto-timed). Auto-starting, manually-skippable rest between exercises. Progress shown as "4 / 12 — Round 2," not a percentage bar. Timer is built on an absolute end-timestamp, never a live-incrementing counter (research §3, non-negotiable). Wake Lock requested on start and re-requested on `visibilitychange`, never trusted as the sole mechanism keeping the timer correct.
6. **Session complete** — "Session Complete," what was trained, "N of 6 Protocols complete" (progress-toward-completion, not a streak — research §2), a **Browse all 6 Protocols** link, and a no-account **Retake the assessment** link.
7. **Optional post-workout data** — appears once, on the completion screen, only if not already answered: combat sport + experience level, two dropdowns, clearly skippable, never blocks anything (brief's explicit "get them trained first" instruction).
8. **STANCE CTA** — appears on the completion screen once the user has completed at least one session, not before (§14). Honest, single-screen waitlist signup — reuses the already-captured email, never asks again.

A **hub** view (all six category cards, duration shown, completed ones marked) is reachable from the unlocked result and from the completion screen for a user who wants more than their one primary result — it is not part of the primary linear funnel, which stays exactly: assessment → gate → workout → complete.

The original draft's "weekly builder" (§9's 3/4/5-day templates) is written and documented as product content but is not yet a dedicated interactive screen in v1 — see §15/Implementation Status below.

**Persistence:** localStorage, written on every interaction, no account required. Copy is honest about the constraint rather than silent about it — if state is missing on load (possible after 7+ days of inactivity on iOS Safari without home-screen install, research §3), the app shows a plain "let's pick up from your last result" prompt instead of a blank or broken screen. A lightweight, earned "add to your home screen" suggestion appears after the first completed session — never before, never as a gate.

**Accessibility:** 44px practical touch-target floor, WCAG AA contrast verified against the actual dark palette (not assumed), `prefers-reduced-motion` respected, timer uses `role="timer"` with throttled `aria-live` announcements, checklist state exposed via real checkbox semantics.

## 12. Lead-generation flow

Existing funnel (`strategy.md`, `voice.md`) stays intact up to the point of arrival:

```
Instagram Reel → Comment/DM "HELP" → matteofights.me/protocol → [this product]
```

**What changes from the current `gate.html`, and why:** the current flow asks for email *and* Instagram handle before showing any content, then redirects to a static page. Research (§2) shows both of those are conversion-costly and unnecessary — form friction is one of the most reliably quantified effects reviewed, and asking for a handle upfront is a separately documented conversion-killer. The shipped flow (§11, steps 2–4) runs the full assessment and shows a real teaser (primary category + one sentence) before asking for anything, then asks for a single email field to unlock the full result and the matching workout. Instagram handle is never asked for anywhere in this product — verified by an automated check that the string "instagram" never appears in any UI copy or in any webhook payload. If a handle is ever needed for STANCE, that's a second-touch ask inside STANCE itself, not a gate here. The two linktree entry points (`docs/index.html`, `docs/links.html`) were updated to point at `/protocol/` instead of the old `gate.html`, so the funnel actually reaches this product.

**Delivery mechanism:** instant, on-page — never "check your email" as the only path to value. Email capture still fires a webhook so the list keeps building for future marketing, same integration point as today.

**Provider:** no email marketing provider is currently configured in this repo (`context/apps.md` lists only Windsor and Higgsfield). The existing Make.com webhook (`https://hook.eu1.make.com/7tieu19hys3tpolvxvj6ti1jn6t7x0ra`) is kept as the default sink, but the capture call is written against a single small `submitEmail(email)` function so swapping in ConvertKit/Beehiiv/Resend/whatever is chosen later touches one function, not the UI. Single opt-in for this launch (double opt-in is a defensible later upgrade if paid traffic starts hitting this funnel — research §2, flagged as a judgment call, not a settled finding).

## 13. Conversion strategy

No STANCE mentions before the user has completed at least one session — the free product has to stand on its own first (research §2, freemium give-too-little/give-too-much finding). The STANCE screen, when it appears, is one screen: honest about being a waitlist, no feature claims beyond what's actually built, framed as a natural next step ("THE PROTOCOL teaches you how to train. STANCE is training with other people who take this seriously.") rather than a sales pitch. No urgency language, no fake spot-scarcity.

## 14. Relationship between Matteo Fights, THE PROTOCOL, and STANCE

- **@matteofights** — the audience and trust layer. Reels build the following; THE PROTOCOL is where "HELP" DMs land.
- **THE PROTOCOL** — free, complete, standalone. Teaches how to train alone. The proof that Matteo's paid work will be worth it.
- **STANCE** — the future paid/network layer. Training *with* other people — finding training partners, other fighters, eventually gyms. Currently pre-product (an early-access waitlist only); the CTA must never claim a feature that isn't live.

**Flag for Matteo, not a blocking question:** `context/strategy.md` currently says explicitly *"Stance — keep it OUT of @matteofights content for now... no Stance mentions in content"* — written 2026-06 before this brief. This spec follows the brief (which explicitly asks for a STANCE waitlist CTA) rather than the older strategy note, and treats the brief as the more current instruction. `strategy.md` should be updated to reflect that STANCE is now allowed to appear at the end of THE PROTOCOL specifically, once this ships — worth a one-line correction, not a re-litigation.

## 15. Future expansion opportunities

Architected for, not built now (§16 keeps content/UI separated specifically so this is additive, not a rewrite):

- **Per-category paid systems** (POWER SYSTEM, GAS TANK SYSTEM, FOOTWORK SYSTEM, SPEED SYSTEM, STRENGTH SYSTEM) — each is "more of" one of the six existing categories, so the data schema for a session already generalizes to a multi-week program without a new content model.
- **COMPLETE FIGHTER SYSTEM** — the six categories combined into a structured multi-week periodized program, using the same double-progression/sparring-aware scheduling logic already built for the free version.
- **STANCE integration** — once STANCE has real features, the waitlist CTA becomes a real link; the assessment results (already structured, per-category, timestamped) are the natural seed data for a future "find a training partner with complementary strengths" matching feature, without needing to be redesigned.
- **Personalization/adaptive progression** — the sRPE + wellness data already being collected in v1 (§8) is exactly the input a future adaptive-progression feature would need; nothing in v1 needs to be thrown away to build it.

---

## 16. Technical architecture

Matches the existing site: static, no build step, deployed via GitHub Pages from `docs/`. No framework runtime, per the mobile-UX load-speed finding (research §3).

```
docs/protocol/
├── index.html       — the entire app shell (six <section data-view> containers, §11)
├── app.js           — state machine, timer logic, localStorage, webhook calls, analytics
├── data.js          — all content: categories, assessment questions + scoring,
│                       the six workouts, every UI copy string — edited without
│                       touching app.js or index.html
├── style.css        — extends the existing design tokens (see below), no new palette
└── README.md        — technical documentation: scoring logic, workout data
                        schema, how to add/edit workouts, email + analytics
                        integration points, deployment, known limitations

production/protocol-v2/
├── docs/            — this spec and PROTOCOL_RESEARCH.md
└── tests/
    └── scoring.test.js  — Node, no dependencies, 539 assertions covering every
                            category's reachability, deterministic tie-breaking,
                            and every workout's structural integrity. Re-run after
                            any data.js edit: `node production/protocol-v2/tests/scoring.test.js`
```

**Design tokens — reused, not reinvented**, pulled directly from the live `docs/the-protocol.html` and `docs/gate.html`:
`--bg:#0B0B0D · --bg-2:#111114 · --bg-3:#17171b · --text:#e8e8e8 · --red:#C82020 · --gold:#C49040 · --border-2:#2a2a30`. Typography: Bebas Neue (display) / Inter (body) / DM Mono (numerals, timers, labels) — same stack already loaded site-wide.

**Timer implementation:** absolute end-timestamp diffed against `Date.now()` on every tick and on every `visibilitychange`/resume — never a naive incrementing counter (research §3, non-negotiable finding).

**State:** a single JS object mirrored to `localStorage` on every mutation; no backend, no database, no accounts.

**Legacy content:** the current `production/lead-magnet/` and `docs/the-protocol.html`/`gate.html` (the 4-week UFC-PI boxing plan) are a different, earlier product — left in place, not deleted, and not linked from the new `/protocol` once it ships. `docs/CNAME` and the GitHub Pages config are unchanged; the new app simply becomes what `matteofights.me/protocol` resolves to.

---

## 17. Implementation status

Shipped and tested (see `docs/protocol/README.md` for exact details):

- Landing, 5-question assessment, teaser + single-field email gate, unlocked result with the
  matching workout, six-category hub, full workout player (timed and rep-based steps, rest
  handling, absolute-timestamp timer), completion screen, optional post-workout combat-sport/
  experience micro-form, and an honest STANCE waitlist CTA.
- Deterministic scoring across all six categories, verified by 539 automated checks
  (`production/protocol-v2/tests/scoring.test.js`).
- Full interactive flow verified end-to-end via Chrome DevTools Protocol: assessment → gate →
  invalid/empty/valid email → unlock → workout → timer countdown → full completion → optional
  data skip → STANCE signup → no-account reassessment → refresh-mid-flow persistence. 42/42
  assertions passing, including confirmation that no Instagram field is ever shown or sent to the
  webhook, and that the STANCE copy never claims a feature that isn't live.
- The two existing linktree entry points now route to `/protocol/` instead of the legacy
  `gate.html`, and `context/strategy.md`'s "no Stance mentions" note was corrected to reflect the
  one explicit, brief-approved exception (the completion-screen waitlist CTA).

**Not yet built (architected for, not required for launch):** the interactive 3/4/5-day weekly
builder screen (§9's templates are written as workout-level `progression` copy but don't yet have
their own dedicated UI screen); per-session sRPE/wellness logging (§8's monitoring model is
documented as the future-product mechanism, not wired into v1's free flow, which the trust research
explicitly recommends keeping minimal); add-to-home-screen prompting (mobile-UX research flags this
as a legitimate later addition, not a launch requirement).

## 18. What "done" looks like

Direct callback to the brief's own final standard — this spec is complete when every one of these is true of the shipped product, not just the plan:

- A serious fighter with no gym and no coach could genuinely follow this and get stronger, faster, and better-conditioned.
- The mechanism ("why this drill") is visible enough that a user finishes thinking Matteo understands programming, not just exercises.
- The site feels like a premium sports-performance product on a phone, not a free PDF or a Canva template.
- Nothing in the copy claims more than the evidence in `PROTOCOL_RESEARCH.md` supports.
- Completing THE PROTOCOL leaves someone more likely to trust whatever Matteo builds or sells next — without anything in the free product being deliberately withheld to manufacture that effect.
