# THE PROTOCOL

Live at **matteofights.me/protocol**. A free, mobile-first fighter performance assessment and
workout system: the first stage of the Matteo Fights to STANCE funnel. Product research and
rationale live in `production/protocol-v2/docs/PROTOCOL_RESEARCH.md` and `PROTOCOL_SPEC.md`. This
file is the technical README for the code in this folder.

Funnel: `Reel ("comment PROTOCOL") -> DM -> matteofights.me/protocol -> assessment -> email ->
workout -> completion -> STANCE waitlist`.

---

## Architecture

Static site, no build step, no framework, no backend. Matches the rest of this repo's GitHub
Pages deploy from `docs/`.

```
docs/protocol/
├── index.html   the entire app shell: six empty <section data-view="…"> containers,
│                  toggled by app.js. No page-specific markup lives here.
├── data.js       ALL content: categories, assessment questions plus scoring, the six
│                  workouts, and every string of UI copy. Pure data plus two pure functions
│                  (scoreAssessment, no DOM access). Reusable and unit-testable in Node.
├── app.js        application logic: state machine, router, timer, persistence,
│                  webhook calls, analytics. Reads everything from data.js, never hardcodes
│                  copy or workout content.
└── style.css     styling. Reuses the design tokens already live in
                   docs/the-protocol.html and docs/gate.html (same colors, same fonts).
                   Nothing reinvented.
```

The split matters for one reason: **editing a workout or a question never touches app.js.**
Content and logic are separate files on purpose.

### Runtime model

A single `state` object (view, answers, score result, email, workout progress, completed
categories) is mirrored to `localStorage` on every change. No accounts, no server round-trip to
determine what a user sees. The whole app reads and writes one JSON blob client-side. See
`STORAGE_KEY = "protocol_state_v1"` in `app.js`.

The router (`showView(name)`) just toggles the `hidden` attribute on the six `[data-view]`
sections in `index.html`. There's no client-side routing library, no hash routes, no history API
usage. Reloading always re-derives what to show from the persisted `state.view`. This also means
the phone's hardware or browser back button leaves the page entirely rather than stepping back a
screen, same as the previous `gate.html`. In-app "Back" only exists inside the assessment,
between its own questions.

---

## The six views

`landing -> assessment -> result -> hub -> workout -> complete`. `hub` (browse all six workouts)
is reachable from `result` and `complete`, not part of the primary linear funnel.

---

## Assessment scoring logic

**"Find Your Fighter Weakness."** 5 questions, roughly 60 to 90 seconds, defined in `data.js`
under `ASSESSMENT.questions`.

- **Q1 to Q3 score categories.** Each option maps to exactly one of the six categories (power,
  speed, conditioning, footwork, strength, mobility) and carries a fixed weight: **Q1 = 3** (the
  single most diagnostic question, "what gives out first under pressure"), **Q2 = 2** ("what do
  you want to improve"), **Q3 = 2** ("what do you train least"). A category's final score is just
  the sum of the weights of every option that pointed at it.
- **Q4 and Q5 never score anything.** They're segmentation only (training frequency, equipment
  access), used to personalize the email payload and, later, to route the right workout variant.
  They're marked `weight: 0, segment: true` in the data so this is enforced in code, not just by
  convention.
- **Determinism and ties.** `scoreAssessment(answers)` in `data.js` is a pure function: same
  answers always produce the same `{ scores, primary, secondary, ranked }`. Ties are broken by a
  fixed, documented order: `TIE_BREAK_ORDER = ["power", "conditioning", "strength", "speed",
  "footwork", "mobility"]`. A tie always resolves the same way, not by object-key iteration order
  or insertion order.
- **Why this design.** Every category is reachable as the primary result via Q1 alone (verified
  in `production/protocol-v2/tests/`), so no category is structurally impossible to surface, and
  no combination of answers can produce a missing or `undefined` result.

## Workout data structure

Every workout in `WORKOUTS` (`data.js`) is a list of **sections**, each a list of **steps**:

```js
{
  category: "power",
  title: "Power Protocol",
  duration: "20 minutes",
  equipment: "No equipment",
  goal: "...",
  whyThisWorks: "...",     // the trust-building "why" layer, shown in the unlocked result
  coachingNotes: [ "..." ], // session-level, not yet surfaced in v1's UI, see "Future work"
  progression: [ "..." ],   // 4-week progression, reserved for a future progression screen
  sections: [
    {
      title: "Warm-up",
      steps: [
        { type: "note", text: "..." },                             // instructional, not timed
        { type: "exercise", name, mode: "time", seconds, cues: [max 3],
          mistake, easier, harder, restSeconds },                   // auto-timed
        { type: "exercise", name, mode: "reps", repsLabel, cues, mistake, easier, harder,
          restSeconds }                                             // user taps "Done"
      ]
    }
    // more sections...
  ]
}
```

`app.js` flattens every workout's sections into one ordered array of steps the moment a workout
is opened (`flattenWorkout`). The player just walks that array forward. A `rest` state is layered
on top of whichever step has `restSeconds > 0`. It is **not** a separate entry in the array, so
rest never consumes its own "step number."

`mistake`, `easier`, and `harder` use an empty string (`""`) when there's nothing to show for
that field. `app.js` only renders a line when the value is truthy, so an empty string is simply
skipped. Never leave the field out entirely; use `""`.

**Timer correctness. Read this before touching the timer code.** Every countdown
(`startCountdown` in `app.js`) is driven by an **absolute end-timestamp**
(`Date.now() + seconds * 1000`), never a live-incrementing counter. Backgrounded browser tabs
throttle `setInterval` to roughly once a minute, so a naive incrementing counter would desync
silently. Recomputing `remaining = endAt - Date.now()` on every tick self-corrects regardless of
throttling, screen lock, or the app losing focus mid-set. Do not simplify this back to a counter.

Screen Wake Lock is requested on workout start and re-requested on `visibilitychange`, but the
app never depends on it succeeding. It's unreliable on iOS in some configurations, and the timer
above stays correct with or without it.

## How to add or edit a workout

1. Open `data.js`, find the relevant key under `WORKOUTS` (`power`, `speed`, `conditioning`,
   `footwork`, `strength`, `mobility`).
2. Edit `sections` directly: add, remove, or reorder steps. Every `exercise` step needs `name`,
   `mode` (`"time"` or `"reps"`), the matching `seconds` or `repsLabel`, up to 3 `cues`, and
   `mistake` / `easier` / `harder` (use `""` when there's nothing to show, never omit the field).
3. Nothing in `app.js`, `index.html`, or `style.css` needs to change. The player renders whatever
   structure it's given.
4. Run the tests (below) before shipping. They check every workout's structural integrity
   automatically: every exercise has its required fields, every category has a workout, and so on.

## How to add a new category

More work than editing a workout, but still fully data-driven:

1. Add an entry to `CATEGORIES` in `data.js` (id, name, oneLiner).
2. Add it to `CATEGORY_ORDER` and `TIE_BREAK_ORDER`. Pick where it sits in the tie-break priority
   deliberately; this is a real product decision, not a formality.
3. Add a matching option (same category id) to each of the three scoring questions (Q1 to Q3) in
   `ASSESSMENT.questions`.
4. Add a `RESULT_COPY[newCategory]` entry (`headline`, `why`).
5. Add a `WORKOUTS[newCategory]` entry following the structure above.
6. Re-run the scoring tests. `scoreAssessment` and the UI both iterate `CATEGORY_ORDER`
   generically, so a correctly-added category needs no changes to `app.js`.

## Email integration

`CONFIG.EMAIL_WEBHOOK_URL` in `app.js` points at the **existing** Make.com scenario already used
by the previous `gate.html`. Kept as the default sink so this ships without new infrastructure.
No email marketing provider (ConvertKit, Beehiiv, Resend, or similar) is currently configured
anywhere in this repo. To add one, point `CONFIG.EMAIL_WEBHOOK_URL` at it and adjust the payload
shape in `submitEmail()` if the new provider needs a different format. Nothing else in the app
needs to know.

**What's sent, and when:**
- `submitEmail(email)`: fired once, the moment a user unlocks their result. Payload: `email`,
  `primaryFocus`, `secondaryFocus`, `trainingFrequency`, `equipmentAccess` (from the assessment),
  `source`, `date`. **Instagram handle is never collected or sent anywhere**, deliberately. See
  `PROTOCOL_RESEARCH.md` for why: asking for it upfront is a documented conversion-killer.
- `submitOptionalData(fields)`: fired only if the user fills in the optional post-workout
  combat-sport/experience micro-form. Skippable, never blocks anything.
- `submitStanceWaitlist()`: fired when the STANCE CTA is clicked. Uses
  `CONFIG.STANCE_WEBHOOK_URL` if set, otherwise reuses the same email webhook with
  `list: "stance_waitlist"`, so it lands in the same place until a dedicated STANCE list exists.

**Failure handling:** a failed webhook call never blocks the user from what they were promised.
Unlocking is a client-side state change that happens regardless of network success. Failed sends
queue in `localStorage` (`protocol_retry_queue_v1`) and retry on the next page load
(`flushRetryQueue()`). This is a lead-gen webhook, not an auth system; a dropped request should
never be the reason someone can't see their own result.

**Duplicate emails:** there's no backend here to de-duplicate against, so re-entering an email
that's already on the list just sends another webhook call, which is safe and idempotent from
the app's side. True de-duplication is the ESP's job once one is configured.

## Analytics events

No analytics infrastructure currently exists in this repo (`context/apps.md` lists only
Windsor.ai and Higgsfield). Nothing is invented here. Every event below fires through a single
`track(name, props)` function in `app.js` that:

1. Always logs locally (`localStorage.protocol_events_v1`, capped at the last 200 events), so
   events are inspectable in dev tools even with zero external wiring.
2. Pushes to `window.dataLayer` if present (GTM/GA4-compatible, a no-op otherwise).
3. POSTs to `CONFIG.ANALYTICS_ENDPOINT` if it's set (`null` by default).

**To wire real analytics:** set `CONFIG.ANALYTICS_ENDPOINT` to a collector URL (a dedicated
Make.com webhook is the path of least resistance given the rest of this repo), or drop a real GTM
container or `gtag()` call on the page. `track()` already pushes to `window.dataLayer`, so a GTM
container picks these up with zero code changes here.

**Events fired:** `protocol_page_visit`, `assessment_started`, `assessment_completed`,
`result_category`, `email_submitted`, `workout_unlocked`, `workout_started`, `workout_completed`,
`stance_cta_clicked`, `stance_waitlist_signup`.

The metric that matters most isn't page visits or email captures. It's `workout_completed` versus
`workout_started`, and eventually `stance_waitlist_signup` versus `assessment_completed` (Protocol
to STANCE conversion). Build any dashboard around those ratios first.

## Deployment

No build step. GitHub Pages serves `docs/` on `main` directly (see the repo's existing `CNAME`
pointing at `matteofights.me`). Pushing a commit that touches `docs/protocol/*` **is** the deploy;
there's no separate build or publish step to run.

`matteofights.me/protocol` resolves to `docs/protocol/index.html` via GitHub Pages' standard
directory-index behavior.

## Testing

`production/protocol-v2/tests/` holds the durable regression check:

- **`scoring.test.js`** (Node, no dependencies) tests `data.js`'s `scoreAssessment` in isolation:
  every category reachable as primary, deterministic tie-breaking, every workout matched to a
  category and vice versa, every exercise step carrying its required fields. Run with
  `node production/protocol-v2/tests/scoring.test.js`.

The full interactive flow (assessment through email gate, validation, unlock, workout, timer,
completion, optional data, STANCE signup, reassessment) was verified end-to-end via Chrome
DevTools Protocol during development: 42 assertions covering mobile viewport, invalid/empty/valid
email, refresh mid-flow, scoring edge cases, no Instagram field anywhere, webhook payload shape,
and STANCE staying honest about not being launched yet. That harness lives outside this repo as
scratch tooling; the Node scoring tests above are what's kept here as a durable check. Re-run them
after any `data.js` edit.

A `?test=1` query-string flag (see `TEST_MODE` in `app.js`) clamps every workout timer to at most
2 seconds. It's inert for real users, never enabled unless the param is explicitly present, and
exists purely so the full workout-completion flow can be exercised quickly in automated testing
without waiting out real workout minutes.

## Future STANCE integration

The STANCE CTA (`renderStanceCTA` in `app.js`) is currently an honest waitlist signup. It never
claims a feature that doesn't exist yet (`UI_COPY.stance.note` says so directly: "STANCE isn't
launched yet. This joins the early access list, nothing more.") When STANCE has real features:

1. Point the CTA at STANCE's actual signup or app URL instead of the local
   `submitStanceWaitlist()` webhook call.
2. The assessment's per-category scores (`state.scoreResult.scores`, already computed and
   available) are natural seed data for a future "match with a training partner who complements
   your weaknesses" feature. No redesign needed; the data already exists per user.
3. `CONFIG.STANCE_WEBHOOK_URL` is already a separate config slot from the email list, so STANCE
   signups can be routed to their own list the moment one exists, without touching the signup
   flow itself.

## Known limitations (intentional, not oversights)

- No native browser back-button or history integration, same as the previous `gate.html`. Back
  navigation only exists between assessment questions.
- `localStorage` isn't permanent on iOS Safari without the page being added to the home screen
  (Apple's ITP caps script-writable storage at 7 days of site inactivity). The app is honest
  about this rather than promising permanence it can't guarantee. See the mobile UX research in
  `PROTOCOL_RESEARCH.md`.
- No account system, on purpose. Reassessment and progress tracking are all local-device,
  single-browser. A returning user on a different device starts fresh, matching the brief's
  explicit instruction not to require an account.
