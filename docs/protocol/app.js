/*
 * THE PROTOCOL . application logic.
 * Vanilla JS, no framework, no build step. Reads content from data.js
 * (window.ProtocolData). See README.md for architecture notes.
 */
(function () {
  "use strict";

  var D = window.ProtocolData;

  // -----------------------------------------------------------------
  // CONFIG . the only place external integrations are wired.
  // -----------------------------------------------------------------
  var CONFIG = {
    // Existing Make.com scenario used by the current gate.html. Kept as
    // the default sink so this ships without new infrastructure; swap
    // to a real ESP (ConvertKit/Beehiiv/Resend/etc.) by changing this
    // one URL and, if the payload shape needs to change, editing
    // submitEmail() below. Nothing else in the app needs to know.
    EMAIL_WEBHOOK_URL: "https://hook.eu1.make.com/7tieu19hys3tpolvxvj6ti1jn6t7x0ra",
    // Optional: point this at an analytics collector (e.g. a separate
    // Make.com webhook, or replace track() to call gtag()). Left null
    // by default . events still fire and are visible in
    // localStorage/console, they just aren't forwarded anywhere until
    // this is set. No analytics infra currently exists in this repo
    // (see context/apps.md), so nothing is invented here.
    ANALYTICS_ENDPOINT: null,
    STANCE_WEBHOOK_URL: null // falls back to EMAIL_WEBHOOK_URL with list:"stance"
  };

  var STORAGE_KEY = "protocol_state_v1";
  var RETRY_QUEUE_KEY = "protocol_retry_queue_v1";

  // Test-mode only: ?test=1 clamps every timer to at most 2 seconds so the
  // full flow (including rest steps and full workout completion) can be
  // exercised quickly in automated tests. Invisible and inert for real
  // users, never enabled unless the query param is explicitly present.
  var TEST_MODE = (function () {
    try { return new URLSearchParams(window.location.search).get("test") === "1"; }
    catch (e) { return false; }
  })();
  function clampSeconds(s) { return TEST_MODE ? Math.min(s, 2) : s; }

  // -----------------------------------------------------------------
  // Routing. Every view gets a real, bookmarkable URL hash so the quiz,
  // the email step, and the workout are each a distinct, findable place
  // instead of hidden inside one opaque single-page flow. Back/forward
  // work through popstate. Programmatic navigation always goes through
  // navigate(); direct hash entry (a bookmark, the back button, a typed
  // URL) is validated first so nobody lands on a screen that doesn't
  // make sense given what they've actually done (e.g. a workout screen
  // with no workout chosen).
  // -----------------------------------------------------------------
  var ROUTE_MAP = {
    landing: "",
    assessment: "quiz",
    gate: "email",
    result: "result",
    hub: "workouts",
    workout: "workout",
    complete: "complete"
  };
  var VIEW_BY_ROUTE = (function () {
    var map = {};
    Object.keys(ROUTE_MAP).forEach(function (view) { map[ROUTE_MAP[view]] = view; });
    return map;
  })();

  function hashFor(view) {
    var route = ROUTE_MAP[view] || "";
    return route ? "#" + route : "";
  }

  // Only used for hash-driven entry (initial load, back/forward, a typed
  // or bookmarked URL) , never for in-app button clicks, which call
  // navigate() directly and always know exactly what they're doing.
  function validateView(view) {
    if (view === "gate") return state.scoreResult ? "gate" : "assessment";
    if (view === "result") {
      if (state.emailUnlocked) return "result";
      return state.scoreResult ? "gate" : "assessment";
    }
    if (view === "hub") {
      if (state.emailUnlocked) return "hub";
      return state.scoreResult ? "gate" : "assessment";
    }
    // A live workout or a finished-session screen should never be
    // silently resumed from a URL, a bookmark, or the back button ,
    // land somewhere the user can deliberately choose from instead.
    if (view === "workout") return "hub";
    if (view === "complete") return "hub";
    return view; // landing, assessment always pass through as-is
  }

  function resolveViewFromHash() {
    var rawRoute = window.location.hash.replace(/^#/, "");
    var view = rawRoute ? (VIEW_BY_ROUTE[rawRoute] || "landing") : "landing";
    return validateView(view);
  }

  // -----------------------------------------------------------------
  // Small utilities
  // -----------------------------------------------------------------
  function qs(sel, root) { return (root || document).querySelector(sel); }
  function qsa(sel, root) { return Array.prototype.slice.call((root || document).querySelectorAll(sel)); }
  function el(tag, attrs, children) {
    var node = document.createElement(tag);
    attrs = attrs || {};
    Object.keys(attrs).forEach(function (k) {
      if (k === "text") node.textContent = attrs[k];
      else if (k === "html") node.innerHTML = attrs[k];
      else if (k.indexOf("on") === 0 && typeof attrs[k] === "function") node.addEventListener(k.slice(2), attrs[k]);
      else node.setAttribute(k, attrs[k]);
    });
    (children || []).forEach(function (c) { if (c) node.appendChild(c); });
    return node;
  }
  function isValidEmail(v) {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(String(v || "").trim());
  }
  function formatTime(totalSeconds) {
    var s = Math.max(0, Math.ceil(totalSeconds));
    var m = Math.floor(s / 60);
    var r = s % 60;
    return m + ":" + (r < 10 ? "0" : "") + r;
  }

  // -----------------------------------------------------------------
  // Analytics . see CONFIG.ANALYTICS_ENDPOINT above.
  // Events fired: protocol_page_visit, assessment_started,
  // assessment_completed, result_category, email_submitted,
  // workout_unlocked, workout_started, workout_completed,
  // stance_cta_clicked, stance_waitlist_signup
  // -----------------------------------------------------------------
  function track(eventName, props) {
    var payload = { event: eventName, props: props || {}, ts: new Date().toISOString() };
    try {
      var log = JSON.parse(localStorage.getItem("protocol_events_v1") || "[]");
      log.push(payload);
      if (log.length > 200) log = log.slice(log.length - 200);
      localStorage.setItem("protocol_events_v1", JSON.stringify(log));
    } catch (e) { /* storage unavailable . non-fatal */ }
    if (window.dataLayer && typeof window.dataLayer.push === "function") {
      window.dataLayer.push(Object.assign({ event: "protocol_" + eventName }, props || {}));
    }
    if (CONFIG.ANALYTICS_ENDPOINT) {
      fetch(CONFIG.ANALYTICS_ENDPOINT, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      }).catch(function () { /* best-effort only */ });
    }
  }

  // -----------------------------------------------------------------
  // Persistence
  // -----------------------------------------------------------------
  function defaultState() {
    return {
      view: "landing",
      answers: {},
      assessmentStep: 0,
      scoreResult: null,
      emailUnlocked: false,
      email: null,
      activeWorkoutCategory: null,
      workoutFlatIndex: 0,
      completedCategories: [],
      optionalDataSubmitted: false,
      createdAt: new Date().toISOString()
    };
  }
  var state = loadState();

  function loadState() {
    try {
      var raw = localStorage.getItem(STORAGE_KEY);
      if (!raw) return defaultState();
      var parsed = JSON.parse(raw);
      return Object.assign(defaultState(), parsed);
    } catch (e) {
      return defaultState();
    }
  }
  function saveState() {
    try {
      state.updatedAt = new Date().toISOString();
      localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
    } catch (e) { /* private mode / storage full . degrade silently */ }
  }

  // -----------------------------------------------------------------
  // Email submission . never blocks unlocking on network success.
  // Failed sends queue locally and retry on next load (best-effort;
  // this is a lead-gen webhook, not an auth system).
  // -----------------------------------------------------------------
  function queueRetry(payload) {
    try {
      var q = JSON.parse(localStorage.getItem(RETRY_QUEUE_KEY) || "[]");
      q.push(payload);
      localStorage.setItem(RETRY_QUEUE_KEY, JSON.stringify(q));
    } catch (e) { /* ignore */ }
  }
  function flushRetryQueue() {
    var q;
    try { q = JSON.parse(localStorage.getItem(RETRY_QUEUE_KEY) || "[]"); } catch (e) { q = []; }
    if (!q.length) return;
    var remaining = [];
    q.forEach(function (payload) {
      fetch(payload.url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload.body)
      }).catch(function () { remaining.push(payload); });
    });
    localStorage.setItem(RETRY_QUEUE_KEY, JSON.stringify(remaining));
  }

  function submitEmail(email, extra) {
    var body = Object.assign({
      email: email,
      primaryFocus: state.scoreResult ? state.scoreResult.primary : null,
      secondaryFocus: state.scoreResult ? state.scoreResult.secondary : null,
      trainingFrequency: state.answers.q4_frequency || null,
      equipmentAccess: state.answers.q5_equipment || null,
      source: "matteofights.me/protocol",
      date: new Date().toISOString()
    }, extra || {});
    fetch(CONFIG.EMAIL_WEBHOOK_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body)
    }).catch(function () {
      queueRetry({ url: CONFIG.EMAIL_WEBHOOK_URL, body: body });
    });
  }

  function submitOptionalData(fields) {
    var url = CONFIG.EMAIL_WEBHOOK_URL;
    var body = Object.assign({ email: state.email, kind: "optional_profile", date: new Date().toISOString() }, fields);
    fetch(url, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) })
      .catch(function () { queueRetry({ url: url, body: body }); });
  }

  function submitStanceWaitlist() {
    var url = CONFIG.STANCE_WEBHOOK_URL || CONFIG.EMAIL_WEBHOOK_URL;
    var body = {
      email: state.email,
      list: "stance_waitlist",
      primaryFocus: state.scoreResult ? state.scoreResult.primary : null,
      date: new Date().toISOString()
    };
    fetch(url, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) })
      .catch(function () { queueRetry({ url: url, body: body }); });
  }

  // -----------------------------------------------------------------
  // Audio + haptic cues (workout timer transitions)
  // -----------------------------------------------------------------
  var audioCtx = null;
  function beep(freq, durationMs) {
    try {
      audioCtx = audioCtx || new (window.AudioContext || window.webkitAudioContext)();
      var osc = audioCtx.createOscillator();
      var gain = audioCtx.createGain();
      osc.frequency.value = freq;
      osc.connect(gain);
      gain.connect(audioCtx.destination);
      gain.gain.setValueAtTime(0.15, audioCtx.currentTime);
      osc.start();
      gain.gain.exponentialRampToValueAtTime(0.0001, audioCtx.currentTime + durationMs / 1000);
      osc.stop(audioCtx.currentTime + durationMs / 1000);
    } catch (e) { /* audio unavailable . non-fatal */ }
  }
  function cueWorkStart() { beep(880, 180); if (navigator.vibrate) navigator.vibrate(120); }
  function cueRestStart() { beep(440, 180); if (navigator.vibrate) navigator.vibrate([60, 60, 60]); }

  // -----------------------------------------------------------------
  // Wake Lock . requested, never trusted. Timer correctness never
  // depends on this succeeding (see startCountdown, absolute timestamp).
  // -----------------------------------------------------------------
  var wakeLockSentinel = null;
  function requestWakeLock() {
    if (!("wakeLock" in navigator)) return;
    navigator.wakeLock.request("screen").then(function (sentinel) {
      wakeLockSentinel = sentinel;
    }).catch(function () { /* ignore . degrade gracefully */ });
  }
  function releaseWakeLock() {
    if (wakeLockSentinel) { wakeLockSentinel.release().catch(function () {}); wakeLockSentinel = null; }
  }
  document.addEventListener("visibilitychange", function () {
    if (document.visibilityState === "visible" && state.view === "workout") requestWakeLock();
  });

  // -----------------------------------------------------------------
  // Router. renderView() shows a view and renders its content but never
  // touches history. navigate() is the one function every in-app button
  // should call: it renders the view AND pushes the matching URL hash.
  // popstate (browser back/forward) calls renderView() directly with a
  // validated hash so it never double-pushes history.
  // -----------------------------------------------------------------
  function renderView(view) {
    qsa("[data-view]").forEach(function (v) { v.hidden = v.getAttribute("data-view") !== view; });
    state.view = view;
    saveState();
    if (view !== "workout") releaseWakeLock();
    renderNav();
    if (view === "landing") renderLanding();
    else if (view === "assessment") renderAssessmentStep();
    else if (view === "gate") renderGate();
    else if (view === "result") renderResult();
    else if (view === "hub") renderHub();
    else if (view === "workout") renderWorkoutStep();
    else if (view === "complete") renderCompletion();
    window.scrollTo(0, 0);
  }

  function navigate(view) {
    renderView(view);
    var target = hashFor(view);
    if (window.location.hash !== target) {
      history.pushState({ view: view }, "", window.location.pathname + window.location.search + target);
    }
  }

  // Both events matter here: popstate fires on browser back/forward,
  // hashchange fires whenever the URL's fragment changes by any other
  // means (a typed/pasted link, a bookmark opened into an already-loaded
  // tab). navigate() itself uses pushState, which triggers neither, so
  // this can't create a feedback loop with in-app navigation.
  function handleExternalHashChange() {
    var view = resolveViewFromHash();
    renderView(view);
    var correctHash = hashFor(view);
    if (window.location.hash !== correctHash) {
      history.replaceState({ view: view }, "", window.location.pathname + window.location.search + correctHash);
    }
  }
  window.addEventListener("popstate", handleExternalHashChange);
  window.addEventListener("hashchange", handleExternalHashChange);

  // -----------------------------------------------------------------
  // Persistent nav. Shown on every screen except the live workout
  // (focus mode stays uncluttered there, per the mobile-UX research) ,
  // just an Exit link during a session instead.
  // -----------------------------------------------------------------
  function renderNav() {
    var nav = qs("#site-nav");
    if (!nav) return;
    nav.innerHTML = "";
    var uic = D.UI_COPY.nav;

    if (state.view === "workout") {
      nav.appendChild(el("button", { class: "nav-exit", onclick: function () { navigate("hub"); }, text: uic.exitWorkout }));
      return;
    }

    nav.appendChild(el("button", { class: "nav-wordmark", onclick: function () { navigate("landing"); }, text: "THE PROTOCOL" }));

    var links = el("div", { class: "nav-links" });
    links.appendChild(el("button", {
      class: "nav-link" + (state.view === "assessment" ? " nav-link-active" : ""),
      onclick: startAssessment,
      text: state.scoreResult ? uic.retakeQuiz : uic.quiz
    }));
    if (state.emailUnlocked) {
      links.appendChild(el("button", {
        class: "nav-link" + (state.view === "result" ? " nav-link-active" : ""),
        onclick: function () { navigate("result"); },
        text: uic.yourWorkout
      }));
      links.appendChild(el("button", {
        class: "nav-link" + (state.view === "hub" ? " nav-link-active" : ""),
        onclick: function () { navigate("hub"); },
        text: uic.allWorkouts
      }));
    }
    nav.appendChild(links);
  }

  // ===================================================================
  // LANDING
  // ===================================================================
  function renderLanding() {
    var c = D.UI_COPY.landing;
    qs("[data-view='landing']").innerHTML = "";
    var root = qs("[data-view='landing']");

    root.appendChild(el("div", { class: "eyebrow" }, [document.createTextNode(c.eyebrow)]));
    root.appendChild(el("h1", { class: "hero-title", text: c.title }));
    root.appendChild(el("div", { class: "hero-subtitle", text: c.subtitle }));
    root.appendChild(el("p", { class: "hero-hook", text: c.hook }));
    root.appendChild(el("button", { class: "btn btn-primary btn-large", onclick: startAssessment, text: c.cta }));

    var problem = el("section", { class: "section" }, [
      el("h2", { class: "section-title", text: c.problemTitle }),
      el("p", { class: "section-body", text: c.problemBody })
    ]);
    root.appendChild(problem);

    var systemSection = el("section", { class: "section" }, [el("h2", { class: "section-title", text: c.systemTitle })]);
    var grid = el("div", { class: "category-grid" });
    D.CATEGORY_ORDER.forEach(function (id) {
      var cat = D.CATEGORIES[id];
      grid.appendChild(el("div", { class: "category-card" }, [
        el("div", { class: "category-card-name", text: cat.name }),
        el("div", { class: "category-card-desc", text: cat.oneLiner })
      ]));
    });
    systemSection.appendChild(grid);
    root.appendChild(systemSection);

    root.appendChild(el("section", { class: "section" }, [
      el("h2", { class: "section-title", text: c.whyBuiltTitle }),
      el("p", { class: "section-body voice", text: c.whyBuiltBody })
    ]));

    root.appendChild(el("button", { class: "btn btn-primary btn-large", onclick: startAssessment, text: c.cta }));
    root.appendChild(el("p", { class: "disclaimer", text: D.UI_COPY.disclaimer }));
  }

  // ===================================================================
  // ASSESSMENT
  // ===================================================================
  function startAssessment() {
    if (!state.answers || Object.keys(state.answers).length === 0) {
      track("assessment_started", {});
    }
    state.assessmentStep = 0;
    saveState();
    navigate("assessment");
  }

  function renderAssessmentStep() {
    var questions = D.ASSESSMENT.questions;
    var i = state.assessmentStep;
    var q = questions[i];
    var root = qs("[data-view='assessment']");
    root.innerHTML = "";

    var progressWrap = el("div", { class: "progress-dots" });
    questions.forEach(function (_, idx) {
      progressWrap.appendChild(el("span", { class: "dot" + (idx <= i ? " dot-active" : "") }));
    });
    root.appendChild(progressWrap);

    root.appendChild(el("div", { class: "assessment-eyebrow", text: D.ASSESSMENT.title }));
    root.appendChild(el("h2", { class: "assessment-prompt", text: q.prompt }));

    var optionsWrap = el("div", { class: "options" });
    q.options.forEach(function (opt) {
      var selected = state.answers[q.id] === opt.id;
      optionsWrap.appendChild(el("button", {
        class: "option" + (selected ? " option-selected" : ""),
        onclick: function () { selectAnswer(q.id, opt.id); }
      }, [document.createTextNode(opt.label)]));
    });
    root.appendChild(optionsWrap);

    if (i > 0) {
      root.appendChild(el("button", { class: "btn btn-text", onclick: goToPreviousQuestion, text: "Back" }));
    }
  }

  function selectAnswer(questionId, optionId) {
    state.answers[questionId] = optionId;
    saveState();
    var questions = D.ASSESSMENT.questions;
    if (state.assessmentStep < questions.length - 1) {
      state.assessmentStep += 1;
      saveState();
      renderAssessmentStep();
    } else {
      finishAssessment();
    }
  }

  function goToPreviousQuestion() {
    if (state.assessmentStep > 0) {
      state.assessmentStep -= 1;
      saveState();
      renderAssessmentStep();
    }
  }

  function finishAssessment() {
    var result = D.scoreAssessment(state.answers);
    state.scoreResult = result;
    saveState();
    track("assessment_completed", { answers: state.answers });
    track("result_category", { primary: result.primary, secondary: result.secondary });
    navigate("gate");
  }

  // ===================================================================
  // GATE. The dedicated email step: a real teaser of the result, then a
  // single email field. Its own view/URL (#email) so it's a findable
  // place, not a hidden sub-state of the result screen.
  // ===================================================================
  function renderGate() {
    var root = qs("[data-view='gate']");
    root.innerHTML = "";
    var result = state.scoreResult;
    if (!result) { navigate("assessment"); return; }
    if (state.emailUnlocked) { navigate("result"); return; }

    var copy = D.RESULT_COPY[result.primary];
    var uic = D.UI_COPY.result;

    root.appendChild(el("div", { class: "result-eyebrow", text: uic.teaserTitle }));
    root.appendChild(el("h2", { class: "result-headline", text: copy.headline }));
    root.appendChild(el("p", { class: "result-teaser-line", text: copy.why.split(". ")[0] + "." }));

    var gate = el("div", { class: "email-gate" });
    gate.appendChild(el("div", { class: "email-gate-title", text: uic.teaserPrompt }));
    gate.appendChild(el("div", { class: "email-gate-subtext", text: uic.teaserSubtext }));
    // novalidate: browser-native validation bubbles are inconsistent
    // across browsers and would show a light-mode tooltip against this
    // dark UI. The app's own inline error (below) is the single,
    // consistently-styled source of truth for email validity.
    var form = el("form", { class: "email-form", novalidate: "novalidate" });
    var input = el("input", { type: "email", class: "email-input", placeholder: uic.emailPlaceholder, required: "required", autocomplete: "email" });
    var errorMsg = el("div", { class: "field-error", hidden: "hidden" });
    var submitBtn = el("button", { type: "submit", class: "btn btn-primary btn-large", text: uic.emailCta });
    form.appendChild(input);
    form.appendChild(errorMsg);
    form.appendChild(submitBtn);
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      var value = input.value.trim();
      if (!isValidEmail(value)) {
        errorMsg.textContent = "Enter a valid email address.";
        errorMsg.hidden = false;
        input.setAttribute("aria-invalid", "true");
        return;
      }
      errorMsg.hidden = true;
      submitBtn.disabled = true;
      submitBtn.textContent = "Unlocking…";
      unlockResult(value);
    });
    gate.appendChild(form);
    root.appendChild(gate);
  }

  function unlockResult(email) {
    state.email = email;
    state.emailUnlocked = true;
    saveState();
    submitEmail(email);
    track("email_submitted", { email: email });
    track("workout_unlocked", { primary: state.scoreResult.primary });
    navigate("result");
  }

  // ===================================================================
  // FIGHTER PROFILE. Animated stat-bar breakdown across all six
  // categories, using the same scores already computed for the result.
  // Bars fill in on a short stagger rather than jumping straight to
  // final width, respecting prefers-reduced-motion via the global rule.
  // ===================================================================
  function renderStatBar(categoryId, result, maxScore, index) {
    var cat = D.CATEGORIES[categoryId];
    var score = result.scores[categoryId] || 0;
    var pct = Math.max(4, Math.round((score / maxScore) * 100)); // 4% floor so a zero score still reads as a bar, not a gap
    var isPrimary = categoryId === result.primary;
    var isSecondary = categoryId === result.secondary;

    var row = el("div", { class: "stat-row" });
    row.appendChild(el("div", { class: "stat-label" + (isPrimary ? " stat-label-primary" : ""), text: cat.name }));
    var track = el("div", { class: "stat-track" });
    var fillClass = "stat-fill" + (isPrimary ? " stat-fill-primary" : isSecondary ? " stat-fill-secondary" : "");
    var fill = el("div", { class: fillClass });
    fill.style.width = "0%";
    track.appendChild(fill);
    row.appendChild(track);

    setTimeout(function () { fill.style.width = pct + "%"; }, 120 + index * 90);
    return row;
  }

  function renderStatBlock(result) {
    var maxScore = D.ASSESSMENT.questions.reduce(function (sum, q) { return sum + (q.weight || 0); }, 0);
    var wrap = el("div", { class: "stat-block" });
    D.CATEGORY_ORDER.forEach(function (id, index) {
      wrap.appendChild(renderStatBar(id, result, maxScore, index));
    });
    return wrap;
  }

  // ===================================================================
  // RESULT. Unlocked only: the full "why," secondary focus, and the
  // matching workout. Its own view/URL (#result) so "your workout" is
  // always a specific place to come back to, not a re-run of the quiz.
  // ===================================================================
  function renderResult() {
    var root = qs("[data-view='result']");
    root.innerHTML = "";
    var result = state.scoreResult;
    if (!result) { navigate("assessment"); return; }
    if (!state.emailUnlocked) { navigate("gate"); return; }

    var copy = D.RESULT_COPY[result.primary];
    var secCat = D.CATEGORIES[result.secondary];
    var uic = D.UI_COPY.result;

    var hero = el("div", { class: "result-hero" });
    hero.appendChild(el("div", { class: "result-hero-glow" }));
    hero.appendChild(el("div", { class: "result-eyebrow", text: uic.fullResultTitle }));
    hero.appendChild(el("h2", { class: "result-headline", text: copy.headline }));
    root.appendChild(hero);

    root.appendChild(el("p", { class: "result-why", text: copy.why }));

    root.appendChild(el("div", { class: "stat-block-label", text: uic.statBlockTitle }));
    root.appendChild(renderStatBlock(result));

    var secondaryBlock = el("div", { class: "secondary-focus" }, [
      el("span", { class: "secondary-label", text: uic.secondaryLabel + ": " }),
      el("span", { class: "secondary-name", text: secCat.name })
    ]);
    root.appendChild(secondaryBlock);

    var workout = D.WORKOUTS[result.primary];
    var whatToDo = el("div", { class: "what-to-do" }, [
      el("div", { class: "what-to-do-label", text: uic.whatToDoLabel }),
      el("div", { class: "what-to-do-title", text: workout.title }),
      el("div", { class: "what-to-do-meta", text: workout.duration + " · " + workout.equipment })
    ]);
    root.appendChild(whatToDo);

    root.appendChild(el("button", {
      class: "btn btn-primary btn-large",
      onclick: function () { openWorkout(result.primary); },
      text: uic.startWorkoutCta
    }));
    var actionRow = el("div", { class: "btn-row" });
    actionRow.appendChild(el("button", {
      class: "btn btn-text",
      onclick: function () { navigate("hub"); },
      text: uic.browseAllCta
    }));
    actionRow.appendChild(el("button", {
      class: "btn btn-text",
      onclick: function () { downloadWorkout(result.primary); },
      text: uic.downloadCta
    }));
    root.appendChild(actionRow);
  }

  // ===================================================================
  // DOWNLOAD. Plain-text export of a workout, generated client-side.
  // No dependency, works offline, opens/saves cleanly on any device.
  // ===================================================================
  function generateWorkoutText(workout) {
    var lines = [];
    lines.push("THE PROTOCOL");
    lines.push(workout.title.toUpperCase());
    lines.push(workout.duration + " | " + workout.equipment);
    lines.push("");
    lines.push("GOAL");
    lines.push(workout.goal);
    lines.push("");
    lines.push("WHY THIS WORKS");
    lines.push(workout.whyThisWorks);
    lines.push("");
    workout.sections.forEach(function (section) {
      lines.push("== " + section.title.toUpperCase() + " ==");
      section.steps.forEach(function (step) {
        if (step.type === "note") {
          lines.push("- " + step.text);
        } else if (step.type === "exercise") {
          var detail = step.mode === "time" ? formatTime(step.seconds) : step.repsLabel;
          lines.push("- " + step.name + " (" + detail + ")");
          (step.cues || []).forEach(function (c) { lines.push("    cue: " + c); });
          if (step.mistake) lines.push("    avoid: " + step.mistake);
          if (step.easier) lines.push("    easier: " + step.easier);
          if (step.harder) lines.push("    harder: " + step.harder);
          if (step.restSeconds) lines.push("    rest: " + formatTime(step.restSeconds));
        }
      });
      lines.push("");
    });
    lines.push("COACHING NOTES");
    (workout.coachingNotes || []).forEach(function (n) { lines.push("- " + n); });
    lines.push("");
    lines.push("PROGRESSION");
    (workout.progression || []).forEach(function (p) { lines.push("- " + p); });
    lines.push("");
    lines.push("matteofights.me/protocol");
    return lines.join("\n");
  }

  function downloadTextFile(filename, text) {
    try {
      var blob = new Blob([text], { type: "text/plain;charset=utf-8" });
      var url = URL.createObjectURL(blob);
      var a = document.createElement("a");
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      setTimeout(function () { URL.revokeObjectURL(url); }, 1000);
    } catch (e) { /* download unsupported in this browser, non-fatal */ }
  }

  function downloadWorkout(categoryId) {
    var workout = D.WORKOUTS[categoryId];
    if (!workout) return;
    downloadTextFile("the-protocol-" + categoryId + ".txt", generateWorkoutText(workout));
    track("workout_downloaded", { category: categoryId });
  }

  // ===================================================================
  // HUB. Browse all six protocols (available post-unlock only)
  // ===================================================================
  function renderHub() {
    var root = qs("[data-view='hub']");
    root.innerHTML = "";
    var huic = D.UI_COPY.hub;
    root.appendChild(el("h2", { class: "section-title", text: huic.title }));
    var grid = el("div", { class: "category-grid" });
    D.CATEGORY_ORDER.forEach(function (id) {
      var cat = D.CATEGORIES[id];
      var workout = D.WORKOUTS[id];
      var done = state.completedCategories.indexOf(id) !== -1;
      var card = el("div", { class: "category-card category-card-interactive" });
      card.appendChild(el("button", { class: "category-card-open", onclick: function () { openWorkout(id); } }, [
        el("div", { class: "category-card-name", text: cat.name + (done ? " ✓" : "") }),
        el("div", { class: "category-card-desc", text: cat.oneLiner }),
        el("div", { class: "category-card-meta", text: workout.duration })
      ]));
      card.appendChild(el("button", {
        class: "category-card-download",
        onclick: function (e) { e.stopPropagation(); downloadWorkout(id); },
        text: D.UI_COPY.workout.downloadCta
      }));
      grid.appendChild(card);
    });
    root.appendChild(grid);
    if (state.scoreResult) {
      root.appendChild(el("button", { class: "btn btn-text", onclick: function () { navigate("result"); }, text: huic.backCta }));
    }
  }

  // ===================================================================
  // WORKOUT PLAYER
  // ===================================================================
  var activeFlatSteps = [];
  var timerHandle = null;
  var timerEndAt = null;
  var timerOnComplete = null;

  function flattenWorkout(workout) {
    var flat = [];
    workout.sections.forEach(function (section) {
      section.steps.forEach(function (step, idx) {
        flat.push(Object.assign({}, step, { sectionTitle: section.title }));
      });
    });
    return flat;
  }

  function openWorkout(categoryId) {
    state.activeWorkoutCategory = categoryId;
    state.workoutFlatIndex = 0;
    saveState();
    activeFlatSteps = flattenWorkout(D.WORKOUTS[categoryId]);
    track("workout_started", { category: categoryId });
    requestWakeLock();
    navigate("workout");
  }

  function stopTimer() {
    if (timerHandle) { clearInterval(timerHandle); timerHandle = null; }
    timerEndAt = null;
    timerOnComplete = null;
  }

  function startCountdown(seconds, onTick, onComplete) {
    stopTimer();
    timerEndAt = Date.now() + seconds * 1000;
    timerOnComplete = onComplete;
    function tick() {
      var remaining = (timerEndAt - Date.now()) / 1000;
      if (remaining <= 0) {
        onTick(0);
        stopTimer();
        if (onComplete) onComplete();
        return;
      }
      onTick(remaining);
    }
    tick();
    timerHandle = setInterval(tick, 250);
  }

  function renderWorkoutStep() {
    stopTimer();
    var root = qs("[data-view='workout']");
    root.innerHTML = "";
    var workout = D.WORKOUTS[state.activeWorkoutCategory];
    var idx = state.workoutFlatIndex;
    var step = activeFlatSteps[idx];

    if (!step) { finishWorkout(); return; }

    var header = el("div", { class: "workout-header" }, [
      el("div", { class: "workout-header-title", text: workout.title }),
      el("div", { class: "workout-header-progress", text: (idx + 1) + " / " + activeFlatSteps.length + ", " + step.sectionTitle })
    ]);
    root.appendChild(header);

    if (step.type === "note") {
      root.appendChild(el("div", { class: "step-note", text: step.text }));
      root.appendChild(el("button", { class: "btn btn-primary btn-large", onclick: advanceStep, text: "Continue" }));
      return;
    }

    if (step.type === "rest") {
      renderRestStep(clampSeconds(step.seconds));
      return;
    }

    // exercise step
    root.appendChild(el("div", { class: "exercise-name", text: step.name }));
    root.appendChild(el("div", { class: "exercise-meta", text: step.mode === "time" ? formatTime(step.seconds) : step.repsLabel }));

    var cuesList = el("ul", { class: "cue-list" });
    (step.cues || []).slice(0, 3).forEach(function (cue) { cuesList.appendChild(el("li", { text: cue })); });
    root.appendChild(cuesList);

    var detailsWrap = el("details", { class: "exercise-details" });
    detailsWrap.appendChild(el("summary", { text: "More detail" }));
    if (step.mistake) detailsWrap.appendChild(el("p", { text: "Common mistake: " + step.mistake }));
    if (step.easier) detailsWrap.appendChild(el("p", { text: "Easier: " + step.easier }));
    if (step.harder) detailsWrap.appendChild(el("p", { text: "Harder: " + step.harder }));
    root.appendChild(detailsWrap);

    if (step.mode === "time") {
      var timerDisplay = el("div", { class: "timer-display", text: formatTime(step.seconds) });
      root.appendChild(timerDisplay);
      var actionBtn = el("button", { class: "btn btn-primary btn-large", text: D.UI_COPY.workout.startCta });
      root.appendChild(actionBtn);
      actionBtn.addEventListener("click", function () {
        actionBtn.disabled = true;
        cueWorkStart();
        startCountdown(clampSeconds(step.seconds), function (remaining) {
          timerDisplay.textContent = formatTime(remaining);
        }, function () {
          if (step.restSeconds) { advanceToRest(clampSeconds(step.restSeconds)); } else { advanceStep(); }
        });
      });
    } else {
      var doneBtn = el("button", { class: "btn btn-primary btn-large", text: D.UI_COPY.workout.doneCta });
      root.appendChild(doneBtn);
      doneBtn.addEventListener("click", function () {
        if (step.restSeconds) { advanceToRest(clampSeconds(step.restSeconds)); } else { advanceStep(); }
      });
    }
  }

  function advanceToRest(seconds) {
    var root = qs("[data-view='workout']");
    root.innerHTML = "";
    var workout = D.WORKOUTS[state.activeWorkoutCategory];
    var idx = state.workoutFlatIndex;
    root.appendChild(el("div", { class: "workout-header" }, [
      el("div", { class: "workout-header-title", text: workout.title }),
      el("div", { class: "workout-header-progress", text: (idx + 1) + " / " + activeFlatSteps.length })
    ]));
    renderRestStep(seconds, root);
  }

  function renderRestStep(seconds, existingRoot) {
    var root = existingRoot || qs("[data-view='workout']");
    root.appendChild(el("div", { class: "rest-label", text: D.UI_COPY.workout.restLabel }));
    var timerDisplay = el("div", { class: "timer-display timer-rest", text: formatTime(seconds) });
    root.appendChild(timerDisplay);
    var nextStep = activeFlatSteps[state.workoutFlatIndex + 1];
    if (nextStep && nextStep.type === "exercise") {
      root.appendChild(el("div", { class: "next-up", text: D.UI_COPY.workout.nextUp + ": " + nextStep.name }));
    }
    var skipBtn = el("button", { class: "btn btn-text", text: D.UI_COPY.workout.skipRestCta });
    root.appendChild(skipBtn);
    skipBtn.addEventListener("click", function () { stopTimer(); advanceStep(); });
    cueRestStart();
    startCountdown(seconds, function (remaining) {
      timerDisplay.textContent = formatTime(remaining);
    }, function () {
      advanceStep();
    });
  }

  function advanceStep() {
    state.workoutFlatIndex += 1;
    saveState();
    renderWorkoutStep();
  }

  function finishWorkout() {
    var categoryId = state.activeWorkoutCategory;
    if (state.completedCategories.indexOf(categoryId) === -1) {
      state.completedCategories.push(categoryId);
    }
    saveState();
    track("workout_completed", { category: categoryId });
    releaseWakeLock();
    navigate("complete");
  }

  // ===================================================================
  // COMPLETION
  // ===================================================================
  function renderCompletion() {
    var root = qs("[data-view='complete']");
    root.innerHTML = "";
    var uic = D.UI_COPY.completion;
    var categoryId = state.activeWorkoutCategory;
    var workout = D.WORKOUTS[categoryId];
    var cat = D.CATEGORIES[categoryId];

    root.appendChild(el("h2", { class: "completion-title", text: uic.title }));
    root.appendChild(el("p", { class: "completion-body", text: uic.body }));

    root.appendChild(el("div", { class: "completion-block" }, [
      el("div", { class: "completion-label", text: uic.whatYouTrainedLabel }),
      el("div", { class: "completion-value", text: cat.name + ": " + workout.title })
    ]));
    root.appendChild(el("div", { class: "completion-block" }, [
      el("div", { class: "completion-label", text: uic.nextLabel }),
      el("div", { class: "completion-value", text: uic.nextBody })
    ]));

    var progWrap = el("div", { class: "completion-progress" });
    progWrap.appendChild(el("div", { text: state.completedCategories.length + " of 6 Protocols complete" }));
    root.appendChild(progWrap);

    root.appendChild(el("button", { class: "btn btn-primary btn-large", onclick: function () { navigate("hub"); }, text: D.UI_COPY.result.browseAllCta }));
    root.appendChild(el("button", { class: "btn btn-text", onclick: retakeAssessment, text: uic.reassessCta }));

    if (!state.optionalDataSubmitted) {
      root.appendChild(renderOptionalDataForm());
    }

    if (state.completedCategories.length >= 1) {
      root.appendChild(renderStanceCTA());
    }
  }

  function renderOptionalDataForm() {
    var uic = D.UI_COPY.completion;
    var wrap = el("div", { class: "optional-data" });
    wrap.appendChild(el("div", { class: "optional-data-title", text: uic.optionalDataTitle }));
    wrap.appendChild(el("div", { class: "optional-data-body", text: uic.optionalDataBody }));

    var igInput = el("input", { type: "text", class: "select", placeholder: D.OPTIONAL_FIELDS.instagram.placeholder, autocomplete: "off" });

    var sportSelect = el("select", { class: "select" });
    sportSelect.appendChild(el("option", { value: "", text: D.OPTIONAL_FIELDS.combatSport.label }));
    D.OPTIONAL_FIELDS.combatSport.options.forEach(function (o) { sportSelect.appendChild(el("option", { value: o, text: o })); });

    var expSelect = el("select", { class: "select" });
    expSelect.appendChild(el("option", { value: "", text: D.OPTIONAL_FIELDS.experience.label }));
    D.OPTIONAL_FIELDS.experience.options.forEach(function (o) { expSelect.appendChild(el("option", { value: o, text: o })); });

    wrap.appendChild(el("label", { class: "field-label", text: D.OPTIONAL_FIELDS.instagram.label }));
    wrap.appendChild(igInput);
    wrap.appendChild(sportSelect);
    wrap.appendChild(expSelect);

    var btnRow = el("div", { class: "btn-row" });
    var skipBtn = el("button", { class: "btn btn-text", text: uic.optionalDataSkip });
    var submitBtn = el("button", { class: "btn btn-secondary", text: uic.optionalDataSubmit });
    btnRow.appendChild(skipBtn);
    btnRow.appendChild(submitBtn);
    wrap.appendChild(btnRow);

    skipBtn.addEventListener("click", function () {
      state.optionalDataSubmitted = true;
      saveState();
      renderCompletion();
    });
    submitBtn.addEventListener("click", function () {
      submitOptionalData({
        instagram: igInput.value.trim() || null,
        combatSport: sportSelect.value || null,
        experience: expSelect.value || null
      });
      state.optionalDataSubmitted = true;
      saveState();
      renderCompletion();
    });

    return wrap;
  }

  function retakeAssessment() {
    state.answers = {};
    state.assessmentStep = 0;
    state.scoreResult = null;
    // emailUnlocked and email persist . no re-gating a returning user.
    saveState();
    startAssessment();
  }

  // ===================================================================
  // STANCE CTA
  // ===================================================================
  function renderStanceCTA() {
    var uic = D.UI_COPY.stance;
    var wrap = el("div", { class: "stance-cta" });
    wrap.appendChild(el("div", { class: "stance-eyebrow", text: uic.eyebrow }));
    wrap.appendChild(el("h2", { class: "stance-title", text: uic.title }));
    wrap.appendChild(el("p", { class: "stance-body", text: uic.body }));
    var btn = el("button", { class: "btn btn-primary btn-large", text: uic.cta });
    wrap.appendChild(btn);
    wrap.appendChild(el("p", { class: "stance-note", text: uic.note }));

    btn.addEventListener("click", function () {
      track("stance_cta_clicked", {});
      if (state.email) {
        submitStanceWaitlist();
        track("stance_waitlist_signup", { email: state.email });
        btn.textContent = "You're on the list";
        btn.disabled = true;
      } else {
        // Shouldn't normally happen (email is captured before any workout
        // can be reached) but handle gracefully rather than crash.
        var emailInput = window.prompt("Enter your email to join the STANCE waitlist:");
        if (emailInput && isValidEmail(emailInput)) {
          state.email = emailInput;
          saveState();
          submitStanceWaitlist();
          track("stance_waitlist_signup", { email: emailInput });
          btn.textContent = "You're on the list";
          btn.disabled = true;
        }
      }
    });

    return wrap;
  }

  // ===================================================================
  // INIT
  // ===================================================================
  function init() {
    track("protocol_page_visit", {});
    flushRetryQueue();

    if (state.activeWorkoutCategory) {
      activeFlatSteps = flattenWorkout(D.WORKOUTS[state.activeWorkoutCategory]);
    }

    // A hash in the URL (a bookmark, a shared link, a fresh visit to
    // matteofights.me/protocol/#quiz) takes priority over the persisted
    // view; otherwise resume wherever this browser last left off. Either
    // way the result is validated against actual state before it's ever
    // rendered, so nobody lands on a screen that doesn't make sense yet.
    var rawRoute = window.location.hash.replace(/^#/, "");
    var initialView = rawRoute ? validateView(VIEW_BY_ROUTE[rawRoute] || "landing") : validateView(state.view || "landing");

    renderView(initialView);

    var correctHash = hashFor(initialView);
    if (window.location.hash !== correctHash) {
      history.replaceState({ view: initialView }, "", window.location.pathname + window.location.search + correctHash);
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
