/*
 * THE PROTOCOL , scoring & content structure regression tests.
 * Pure Node, no dependencies. Run: node production/protocol-v2/tests/scoring.test.js
 * Re-run after any edit to docs/protocol/data.js.
 */
"use strict";

var path = require("path");
var D = require(path.join(__dirname, "..", "..", "..", "docs", "protocol", "data.js"));

var failures = 0;
var passed = 0;

function check(name, condition, detail) {
  if (condition) {
    passed++;
  } else {
    failures++;
    console.log("FAIL , " + name + (detail ? " :: " + JSON.stringify(detail) : ""));
  }
}

// ---------------------------------------------------------------------
// Every category is reachable as the primary result via Q1 alone.
// ---------------------------------------------------------------------
var q1OptionByCategory = {};
D.ASSESSMENT.questions[0].options.forEach(function (o) { q1OptionByCategory[o.category] = o.id; });

D.CATEGORY_ORDER.forEach(function (cat) {
  var answers = {};
  answers[D.ASSESSMENT.questions[0].id] = q1OptionByCategory[cat];
  var result = D.scoreAssessment(answers);
  check("category '" + cat + "' is reachable as primary via Q1 alone", result.primary === cat, result);
});

// ---------------------------------------------------------------------
// Determinism: same input always produces the same output.
// ---------------------------------------------------------------------
var sampleAnswers = { q1_breakdown: "a", q2_want: "c", q3_gap: "e", q4_frequency: "b", q5_equipment: "a" };
var r1 = JSON.stringify(D.scoreAssessment(sampleAnswers));
var r2 = JSON.stringify(D.scoreAssessment(sampleAnswers));
check("scoring is deterministic for identical input", r1 === r2);

// ---------------------------------------------------------------------
// Tie-break is deterministic and follows TIE_BREAK_ORDER.
// Q1=power(3), Q2=conditioning(2), Q3=strength(2) -> conditioning and
// strength tie at 2; TIE_BREAK_ORDER puts conditioning before strength.
// ---------------------------------------------------------------------
var tie = D.scoreAssessment({ q1_breakdown: "a", q2_want: "c", q3_gap: "e" });
check("tie resolves via TIE_BREAK_ORDER (conditioning before strength)",
  tie.primary === "power" && tie.secondary === "conditioning", tie);

// ---------------------------------------------------------------------
// Empty / partial answers never crash and never produce an undefined
// primary/secondary.
// ---------------------------------------------------------------------
var emptyResult = D.scoreAssessment({});
check("empty answers do not crash", !!emptyResult);
check("empty answers still produce a valid primary category", D.CATEGORY_ORDER.indexOf(emptyResult.primary) !== -1, emptyResult.primary);
check("empty answers still produce a valid secondary category", D.CATEGORY_ORDER.indexOf(emptyResult.secondary) !== -1, emptyResult.secondary);

var partialResult = D.scoreAssessment({ q1_breakdown: "b" });
check("partial answers (Q1 only) do not crash", !!partialResult);
check("partial answers still produce primary/secondary", D.CATEGORY_ORDER.indexOf(partialResult.primary) !== -1 && D.CATEGORY_ORDER.indexOf(partialResult.secondary) !== -1);

// ---------------------------------------------------------------------
// Segmentation questions (Q4/Q5) never contribute to scoring.
// ---------------------------------------------------------------------
var withSegmentOnly = D.scoreAssessment({ q4_frequency: "a", q5_equipment: "b" });
var allZero = D.CATEGORY_ORDER.every(function (c) { return withSegmentOnly.scores[c] === 0; });
check("segmentation-only answers (Q4/Q5) contribute zero score to every category", allZero, withSegmentOnly.scores);

// ---------------------------------------------------------------------
// Content structure: every category has a matching workout, and every
// workout's steps have the fields the UI requires.
// ---------------------------------------------------------------------
D.CATEGORY_ORDER.forEach(function (cat) {
  check("category '" + cat + "' has a matching workout", !!D.WORKOUTS[cat]);
  check("category '" + cat + "' has RESULT_COPY", !!D.RESULT_COPY[cat]);
});

Object.keys(D.WORKOUTS).forEach(function (key) {
  var workout = D.WORKOUTS[key];
  check("workout '" + key + "' has at least one section", Array.isArray(workout.sections) && workout.sections.length > 0);
  workout.sections.forEach(function (section) {
    check("section '" + section.title + "' in '" + key + "' has steps", Array.isArray(section.steps) && section.steps.length > 0);
    section.steps.forEach(function (step, i) {
      var label = key + " / " + section.title + " / step " + i;
      check(label + " has a valid type", ["note", "rest", "exercise"].indexOf(step.type) !== -1, step);
      if (step.type === "exercise") {
        check(label + " has a name", typeof step.name === "string" && step.name.length > 0);
        check(label + " has a valid mode", step.mode === "time" || step.mode === "reps", step.mode);
        if (step.mode === "time") {
          check(label + " (time mode) has numeric seconds", typeof step.seconds === "number" && step.seconds > 0, step.seconds);
        } else {
          check(label + " (reps mode) has a repsLabel", typeof step.repsLabel === "string" && step.repsLabel.length > 0);
        }
        check(label + " has at most 3 cues", Array.isArray(step.cues) && step.cues.length <= 3, step.cues);
        check(label + " has a mistake field", typeof step.mistake === "string");
        check(label + " has an easier field", typeof step.easier === "string");
        check(label + " has a harder field", typeof step.harder === "string");
      }
      if (step.type === "rest" || (step.restSeconds !== undefined)) {
        check(label + " restSeconds is a non-negative number when present",
          step.restSeconds === undefined || (typeof step.restSeconds === "number" && step.restSeconds >= 0));
      }
    });
  });
});

// ---------------------------------------------------------------------
// UI copy sanity: no Instagram field anywhere in copy (product decision,
// research §2 , Instagram handle is never asked for in this funnel).
// ---------------------------------------------------------------------
var allCopyText = JSON.stringify(D.UI_COPY).toLowerCase();
check("no 'instagram' text anywhere in UI_COPY", allCopyText.indexOf("instagram") === -1);

// STANCE copy must not claim the product is live.
check("STANCE note is honest that it's not launched", D.UI_COPY.stance.note.toLowerCase().indexOf("isn't launched") !== -1, D.UI_COPY.stance.note);

console.log("\n--- summary ---");
console.log(passed + "/" + (passed + failures) + " checks passed");
if (failures > 0) process.exitCode = 1;
