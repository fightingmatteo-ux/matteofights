# Research Agent 6 — Mobile Fitness UX
Target: THE PROTOCOL (matteofights.me/protocol) — mobile-first web, no native app, used mid-workout on iPhone, arriving from Instagram, fighter self-assessment + six training sessions.

Objective: identify what makes someone actually COMPLETE a workout rather than bookmark it and forget.

---

## Key Findings

1. **Friction, not motivation, is the primary killer.** Across e-commerce (Baymard) and mobile app research alike, abandonment correlates far more tightly with taps-to-completion, load time, and error-prone input than with "wanting it enough." Strong's UX (three taps to log a set once inside a session) and the "one action per screen, one button, one decision" principle from fitness-app UX practice both point the same direction: minimize decisions during the set, not before it.

2. **Load time has a hard, well-documented cliff.** 53% of mobile visits are abandoned past a 3-second load; a 2-second added delay on a transaction-like flow can push abandonment past 80%. For an Instagram-referred visitor with no prior trust in the destination, this cliff is steeper, not shallower — first-visit patience is lowest.

3. **The rest timer is the product's real second screen.** In Strong and comparable apps, the rest timer auto-starts after a logged set, is visible in a persistent but non-blocking position, and expands to full-screen on tap. It is the single most load-bearing timer UX pattern in the category — get this one interaction right before anything else.

4. **Screen-lock during rest is a real, well-documented failure mode**, not a hypothetical. iOS users training with the phone on the floor will let the screen sleep. The Screen Wake Lock API is now supported in Safari but has platform-specific caveats (see Technical Reality below) that this build must design around, not assume away.

5. **Progress visibility, not streaks, is the strongest documented long-term retention driver** for solo-use fitness contexts; streak/loss-aversion mechanics increase short-term engagement but generate documented "guilt churn" among users who miss a day and then quit rather than resume. For a six-session, finite protocol (not an infinite habit loop), a completion-percentage / sessions-remaining framing fits the content shape better than a daily streak.

6. **Video beats static images for movement comprehension, but only if it loads.** User studies comparing image vs. video vs. AR instruction found video's advantage is concentrated in exercises with high spatial/rotational complexity; for simpler moves, images perform nearly as well. Given the load-time cliff, this argues for images or short looping clips as the default with video reserved for genuinely complex movements, not blanket video-for-everything.

7. **No-login persistence is honest but fragile on iOS Safari specifically.** Regular (non-home-screen) Safari sessions cap script-writable storage (localStorage, IndexedDB) at 7 days of inactivity under ITP — verified current as of this research. A user who does session 1, then doesn't return for over a week, can lose local progress. This is a real constraint the product must design copy and fallback behavior around, not silently absorb.

8. **Add-to-home-screen materially changes the platform contract**, not just cosmetically: it exempts the app from the 7-day storage cap, unlocks Web Push (outside the EU), and reportedly correlates with a ~30% lift in conversion for the users who do it. But installation is entirely manual on iOS (Share → Add to Home Screen) — there is no install prompt — so it can only be a light, optional suggestion, timed after the user has had a good first experience, never a gate.

---

## Recommended Patterns (ranked by impact)

1. **Fast first render, work offline-first from load 1.** Ship a small HTML/CSS/minimal-JS shell that renders the assessment or first session instantly; defer anything non-critical (video, animation libraries, analytics) until after first paint. This single choice does more for completion than any in-workout feature, because it determines whether the Instagram visitor survives to see the workout at all.

2. **One-exercise-at-a-time "focus mode" during active sets, with a persistent rest timer.** Full workout list/overview is fine for browsing or planning, but the live session should show the current exercise large, with minimal chrome, following the pattern documented in Legend's Focus Mode and general fitness-UX guidance ("no pop-ups, no nav bar, no clutter"). Auto-advance from work to rest; require an explicit tap to advance from rest back into the next set (so the athlete controls pace, matching Strong's pattern of an auto-start but manually-skippable rest timer).

3. **Request the Wake Lock on session start, re-request on visibility change, and never assume it holds.** Treat wake lock as a nice-to-have, not a dependency — build the timer so it stays correct even if the screen sleeps (see Technical Reality below), and re-acquire the lock in a `visibilitychange` handler when the tab regains foreground, since the lock is released automatically when the page is hidden.

4. **Audio + haptic cues for transitions, not just visual ones.** A phone face-down on a gym floor is a documented real use case; visual-only cues fail it completely. Use the Vibration API for haptic pulses at rest-end/work-start boundaries and a distinct, cut-through-noise audio cue (not a generic beep) — consistent with interval-timer app practice.

5. **Big touch targets, bottom-anchored primary actions.** Primary interactive controls (log set, skip rest, next exercise) belong in the thumb's natural bottom-center reach zone per thumb-zone research; meet at minimum WCAG 2.5.8 (24×24 CSS px) but design to the 44×44 px practical standard used by Strong/Nike-class apps, since sweaty-finger, one-handed, under-fatigue tapping is the default use condition here, not the edge case.

6. **Local-only persistence with an honest, visible "why this might reset" note**, not a fake promise of permanence. Save assessment results and session progress to localStorage immediately on each interaction (not just on exit); surface a lightweight, low-friction "Save this to your phone" prompt (add-to-home-screen) once the user has completed something — after value has been delivered, not before.

7. **Completion celebration scaled to the actual achievement — a full six-session protocol finish deserves more than a single set.** Match reward intensity to milestone size (per-set: subtle; per-session: clear but quick; protocol-complete: the one moment worth a bigger animation) — this mirrors both the general "celebrations should be earned and contextual, or they backfire" UX finding and Peloton's progressive-milestone progress bar approach.

8. **Progress-remaining framing over streak framing.** Given six fixed sessions, show "Session 3 of 6" / percentage-through-protocol rather than a daily-streak counter — streaks are the wrong mental model for a finite program and risk the documented guilt-churn effect if someone takes a rest day.

9. **Reduce coaching text to the minimum needed to move correctly, then progressively disclose more.** Freeletics community feedback specifically flags that seeing full workout complexity/instruction volume up front causes procrastination/skipping; default to a short primary cue (1 line) with an optional "more detail" tap-through, not a wall of instructional copy before the first rep.

---

## Timer & Screen-Lock Technical Reality

- **Screen Wake Lock API**: supported in Safari on iOS/iPadOS from 16.4 onward, and now supported across all major browsers as of the current WebKit release cycle. **However**, there was a long-standing WebKit bug where the Wake Lock API did not function correctly inside installed (add-to-home-screen) web apps specifically — Apple's own bug tracker (WebKit bug 254545) documents this; it was reportedly fixed in iOS 18.4. Build assuming: (a) wake lock works in-browser on 16.4+, (b) may be unreliable in home-screen-installed mode on older iOS versions, (c) always feature-detect with `'wakeLock' in navigator` and degrade gracefully — never let the timer's correctness depend on the lock succeeding.
- **Requires a secure context (HTTPS)** and re-acquisition after any tab/app backgrounding — the lock releases automatically on `visibilitychange` to hidden and must be explicitly re-requested when the page becomes visible again.
- **Background/inactive-tab JS timer throttling is real and severe**: browsers (including WebKit) throttle `setInterval`/`setTimeout` in backgrounded tabs, down to roughly once per minute after sustained inactivity in Chrome's documented behavior, and Safari does something comparable. **Implication for THE PROTOCOL:** never trust an interval counter incrementing in real time as the source of truth. Store an absolute end-timestamp (`Date.now() + duration`) and compute remaining time by diffing against the current time on every tick/resume — this makes the displayed timer self-correcting regardless of throttling or the screen sleeping, and is the standard workaround pattern.
- A Web Worker thread is not throttled the same way as the main thread and is a documented mitigation if a more precise background tick is needed — likely unnecessary here given the absolute-timestamp approach covers correctness.

---

## Persistence Reality

- **Safari ITP caps all script-writable storage (localStorage, IndexedDB, sessionStorage, Service Worker registrations, cookies) at 7 days without user interaction**, confirmed current in 2026 sources. Each interaction resets the 7-day counter, so a user training multiple times a week in-browser is very unlikely to hit the cap in practice — the risk case is someone who does the self-assessment, doesn't return for over a week, and finds their answers gone.
- **Web apps added to the home screen are exempt** from this cap — they run outside standard Safari storage partitioning and are not subject to the same 7-day deletion policy.
- **Design implication**: treat localStorage as a convenience, not a guarantee. Don't silently lose data — if state is missing on load, degrade to "let's start fresh" copy rather than a broken or blank UI. Consider making the assessment result shareable/exportable (e.g., a summary the user can screenshot or that generates a shareable link) as a durability fallback that doesn't depend on any storage API.

---

## Performance Budget

Recommended mobile budget consistent with 2026 Core Web Vitals guidance and CDN delivery assumptions:

- LCP < 2.5s, INP < 200ms, CLS < 0.1 (75th percentile, real users) — these are the pass/fail thresholds Google measures.
- Total initial payload target: HTML < 50KB, CSS < 60KB, JS < 150KB gzipped, above-fold images < 200KB, fonts < 80KB — roughly 540KB total initial load.
- **Practical implication for this build**: avoid a heavy JS framework runtime for what is fundamentally a content-and-timer app; a lean vanilla/lightweight-framework approach with minimal hydration cost will hit these numbers far more reliably on a mid-range phone over cellular from an Instagram in-app browser (historically one of the more constrained WebView environments) than a full SPA framework bundle.
- **Fonts**: use `font-display: swap` at minimum, or prefer a system font stack (zero network cost, zero layout shift, zero FOIT/FOUT) for body text, reserving any custom display font for headings only.

---

## Accessibility Requirements

- **Touch targets**: minimum 24×24 CSS px per WCAG 2.5.8 (AA), but design to 44×44 px as the practical floor — error rates on small targets are documented as substantially higher, and this population is training under fatigue with imprecise motor control.
- **Contrast**: standard WCAG 1.4.3 (4.5:1 normal text, 3:1 large text) applies fully in dark mode too — offering a dark theme does not itself satisfy contrast requirements; verify actual computed contrast values in the chosen dark palette, don't assume dark automatically passes.
- **Reduced motion**: respect `prefers-reduced-motion` — disable or minimize non-essential animation (celebration effects, transitions) for users who set this OS-level preference; this is a documented vestibular-safety accommodation, not a cosmetic nicety.
- **Screen reader / assistive tech**: for the timer, use `role="timer"` with `aria-live="polite"` and `aria-atomic="true"` rather than the default `aria-live="off"`, and throttle announcements to meaningful boundaries (not every second) so it doesn't overwhelm; for the exercise checklist, ensure checked/completed state changes are announced and that state is exposed via native checkbox semantics or proper ARIA roles, not div-based fake checkboxes.
- **Sunlight/gym-lighting readability**: gyms vary from harsh overhead fluorescent to near-window daylight; ensure sufficient luminance contrast independent of screen brightness settings and avoid relying on subtle color-only distinctions (e.g., "green means done") — pair color with an icon/shape change for colorblind and glare conditions.

---

## Anti-Patterns To Avoid

- **Any mandatory account creation or login gate before value is delivered.** This is the single most consistently cited mobile abandonment driver in adjacent research (checkout, onboarding) and directly contradicts the product's "free, no-friction, from Instagram" premise.
- **Auto-playing video or heavy animation on first load.** Actively worsens the load-time cliff that's already the top abandonment risk for a cold Instagram referral.
- **Full workout complexity/instruction volume shown all at once before starting.** Documented (Freeletics community) to cause procrastination and skipping — front-load only what's needed for the first rep.
- **Trusting a live-incrementing on-screen counter as the actual timer state.** Background throttling will desync it from real elapsed time; always recompute from an absolute timestamp.
- **Streak mechanics on a finite, six-session program.** Wrong content shape for loss-aversion mechanics; risks guilt-driven abandonment when the pattern (rightly) doesn't fit real training schedules.
- **Assuming Wake Lock always holds, especially in installed/home-screen mode on older iOS.** Silent timer failure when the screen sleeps and the lock silently didn't take is a credibility-destroying bug class for a mid-workout tool.
- **Confetti/celebration on every minor completion.** Documented to backfire and feel hollow when overused; reserve strong celebration for genuinely earned milestones (session complete, protocol complete).
- **Small, closely-packed tap targets for set-logging or timer controls**, given the sweaty-finger, one-handed, fatigued-grip real usage context this product is explicitly designed for.

---

## Sources

- [Screen Wake Lock API — MDN](https://developer.mozilla.org/en-US/docs/Web/API/Screen_Wake_Lock_API)
- [WakeLockSentinel — MDN](https://developer.mozilla.org/en-US/docs/Web/API/WakeLockSentinel)
- [The Screen Wake Lock API is now supported in all browsers — web.dev](https://web.dev/blog/screen-wake-lock-supported-in-all-browsers)
- [Screen Wake Lock API — caniuse](https://caniuse.com/wake-lock)
- [WebKit bug 254545 — New Wake Lock API does not work in Home Screen Web Apps](https://bugs.webkit.org/show_bug.cgi?id=254545)
- [WebKit bug 205104 — Feature Request: Implement the Wake Lock API](https://bugs.webkit.org/show_bug.cgi?id=205104)
- [Apple adds a 7-Day Cap on All Script-Writable Storage — Didomi](https://support.didomi.io/apple-adds-a-7-day-cap-on-all-script-writable-storage)
- [What is Intelligent Tracking Prevention (ITP)? — Avenga](https://www.avenga.com/magazine/intelligent-tracking-prevention/)
- [Safari :: Current status — cookiestatus.com](https://www.cookiestatus.com/safari/)
- [PWA iOS Limitations and Safari Support 2026 — MagicBell](https://www.magicbell.com/blog/pwa-ios-limitations-safari-support-complete-guide)
- [Web Push in iOS: Add to Home Screen — Notificare](https://notificare.com/blog/2024/09/16/web-push-in-ios-add-to-home-screen/)
- [PWA Push Notifications on iOS in 2026 — webscraft.org](https://webscraft.org/blog/pwa-pushspovischennya-na-ios-u-2026-scho-realno-pratsyuye?lang=en)
- [PWA on iOS — Neoteric](https://neoteric.eu/blog/all-you-need-to-know-about-pwa-on-ios/)
- [Heavy throttling of chained JS timers beginning in Chrome 88 — Chrome for Developers](https://developer.chrome.com/blog/timer-throttling-in-chrome-88)
- [Browser Tab Throttling: The Hidden Performance Killer — WebTech Timeline](https://www.getintechs.com/blog/inactive-tab-throttling)
- [About Rest Timer — Strong Help Center](https://help.strongapp.io/article/231-rest-timer)
- [Fitness App UI Design: Key Principles — Stormotion](https://stormotion.io/blog/fitness-app-ux/)
- [Focus Mode for Workouts — Legend](https://legend-tracker.com/feature/focus-mode-for-workouts/)
- [UX Design Principles From 5 Top Health and Fitness Apps — Superside](https://www.superside.com/blog/ux-design-principles-fitness-apps)
- [Comparative Study of AR Versus Image and Video for Exercise Learning — arXiv](https://arxiv.org/abs/2209.02161)
- [Digital Behavior Change Intervention Designs for Habit Formation: Systematic Review — JMIR](https://www.jmir.org/2024/1/e54375)
- [Implementation Intention and Reminder Effects on Behavior Change — JMIR](https://www.jmir.org/2017/11/e397/)
- [Instant habits versus flexible tenacity: implementation intentions and habit formation — PMC](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC10585941/)
- [Use of mHealth Technology for Improving Exercise Adherence — JMIR](https://www.jmir.org/2025/1/e54524)
- [Factors Influencing Adherence to mHealth Apps — PMC](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC9178451/)
- [How Streaks and Daily Rewards Engineer Habit Loops — Bootcamp/Medium](https://medium.com/design-bootcamp/streaks-and-daily-rewards-as-habit-forming-systems-dab7f5a34539)
- [Calm Tech in Fitness UX: What Peloton Gets Right — Medium](https://medium.com/@blessingokpala/calm-tech-in-fitness-ux-what-peloton-gets-right-about-motivation-and-flow-30b9891c092d)
- [The Peloton experience: a usability heuristics analysis — UX Collective](https://uxdesign.cc/the-peloton-experience-c072e305fad6)
- [The Thumb Zone: Designing For Mobile Users — Smashing Magazine](https://www.smashingmagazine.com/2016/09/the-thumb-zone-designing-for-mobile-users/)
- [WCAG 2.5.8 Target Size Minimum — TestParty](https://testparty.ai/blog/wcag-2-5-8-target-size-minimum-2025-guide)
- [All accessible touch target sizes — LogRocket](https://blog.logrocket.com/ux-design/all-accessible-touch-target-sizes/)
- [Dark Mode: How Users Think About It and Issues to Avoid — NN/g](https://www.nngroup.com/articles/dark-mode-users-issues/)
- [Offering a Dark Mode Doesn't Satisfy WCAG Color Contrast Requirements — BOIA](https://www.boia.org/blog/offering-a-dark-mode-doesnt-satisfy-wcag-color-contrast-requirements)
- [ARIA live regions — MDN](https://developer.mozilla.org/en-US/docs/Web/Accessibility/ARIA/Guides/Live_regions)
- [ARIA Timer Role: Complete Guide — Digital Thrive](https://digitalthriveai.com/en-nz/resources/docs/web-development/timer-role/)
- [Haptic Feedback Design for Workout Apps — DEV Community](https://dev.to/lalo132/haptic-feedback-design-for-workout-apps-48h5)
- [What is the role of haptic feedback in fitness wearables? — Elitac Wearables](https://elitacwearables.com/what-is-the-role-of-haptic-feedback-in-fitness-wearables/)
- [Core Web Vitals Guide 2026 — Launchcodex](https://launchcodex.com/blog/web-digital-infrastructure/core-web-vitals-guide/)
- [Web Performance Benchmarks 2026 — Locally Lost](https://locallylost.com/guides/web-performance-benchmarks-2026-core-web-vitals-page-speed-trends/)
- [Web Font Optimization Guide: FOUT, FOIT — Medium](https://medium.com/@vigneshwiki07/mastering-web-fonts-a-guide-to-performance-and-user-experience-958bdc3654d6)
- [The Ultimate Guide to Font Performance Optimization — DebugBear](https://www.debugbear.com/blog/website-font-performance)
- [The 3-Second Rule: Why 53% of Mobile Visitors Abandon Sites That Load Too Slowly — WebBoost](https://webboost.dev/articles/the-3-second-rule-why-53-of-mobile-visitors-abandon-sites-that-load-too-slowly/)
- [Google: 53% of mobile users abandon sites that take over 3 seconds to load — Marketing Dive](https://www.marketingdive.com/news/google-53-of-mobile-users-abandon-sites-that-take-over-3-seconds-to-load/426070/)
- [Checkout Optimization: Minimize Form Fields — Baymard](https://baymard.com/blog/checkout-flow-average-form-fields)
- [Progressive exercise disclosure in a coach session — Freeletics Forum](https://forum.freeletics.com/t/progressive-exercise-disclosure-in-a-coach-session/24054)
- [Sunlight Readable Displays — Riverdi](https://riverdi.com/blog/sunlight-readable-displays-the-most-important-parameters-of-outdoor-lcd-displays-you-need-to-know)
- [Why Confetti Celebrations Backfire — UX Planet](https://uxplanet.org/why-confetti-celebrations-backfire-and-how-to-make-them-work-be838a6e7b8b)

---

## Uncertainties

- **Exact current behavior of Wake Lock inside iOS home-screen-installed apps** is reported fixed in iOS 18.4 by secondary sources referencing the WebKit bug tracker, but this research did not verify against Apple's own release notes directly — treat as probable, not certain, and feature-detect/degrade regardless.
- **The mHealth/exercise-adherence peer-reviewed literature is thin on combat-sports-specific populations** — most systematic reviews cover general physical activity, cardiac rehab, or chronic disease management, not striking/grappling athletes. Findings on adherence design features are directionally applicable but not sport-specific.
- **No direct, controlled UX studies were found comparing web-app (browser, no install) fitness experiences specifically against native-app equivalents** for completion rates — most category benchmarking (Nike Training Club, Strong, Hevy) is native-app UX, applied here by pattern-analogy since THE PROTOCOL is explicitly web-only.
- **The reported "30% better conversion via Add to Home Screen" and "34% longer streaks with social features" figures** come from industry/marketing blog sources rather than peer-reviewed or primary platform data; treat as directional, not precise.
- Did not independently verify current EU-specific iOS web-push restrictions against Apple's own documentation — relying on secondary source consensus (iOS 17.4+ excludes EU).

---

## What This Means For The Product

THE PROTOCOL's biggest completion risk is lost before the workout screen ever loads: a slow, JS-heavy first paint on an Instagram in-app browser over cellular will bleed more users than any in-workout UX decision could ever recover. Ship lean, ship fast, and treat the sub-2.5s LCP target as non-negotiable.

Inside the workout, the rest timer is the product's core interaction — get the auto-start/manual-skip pattern right, back it with an absolute-timestamp calculation (never a naive incrementing counter) so it survives background throttling and screen sleep, and layer haptic/audio cues on top since the phone will often be face-down or out of sight. Request Wake Lock but never depend on it holding, especially if the product later adds home-screen installation.

Keep the six-session structure framed as visible progress-toward-completion rather than a streak — it's a finite protocol, not an infinite habit loop, and streak mechanics fit the wrong shape here and risk guilt-driven abandonment. Persist state to localStorage immediately and constantly, but be honest that on iOS Safari without home-screen installation, that data has a real (if unlikely-in-practice) 7-day inactivity expiry — a lightweight, earned "save this" prompt toward add-to-home-screen after the first good experience is worth having, both for storage durability and for unlocking Web Push later, but it must never gate access.

Design every tap target, contrast pair, and instructional density decision around the real physical context: one hand, sweaty fingers, fatigue, variable gym lighting, phone possibly on the floor. That context, more than any competitive feature parity with Nike Training Club or Strong, should drive the interface decisions here.
