// Paid content of the 4-Week Power Plan, sent by functions/api/plan/me.js only to paid links (not on the static site).
// Edit sessions here. Week notes are also shown on the sales page (docs/plan/plan.js WEEK_NOTES): keep both in sync.
const EX = {
  warm: { n: "Warm-up", d: "5 min: hip and ankle circles, 10 easy squats, 90 s easy shadowboxing, 20 s light pogo hops." },
  cool: { n: "Cool-down", d: "2 min easy shadowboxing, 1 min slow nasal breathing." },
  squatJump: { n: "Squat jumps", d: "Explode up, land soft and quiet, reset between reps. Easier: step-back lunge jump. Rest 90 s." },
  broad: { n: "Broad jumps", d: "Jump for distance and stick the landing. Bad landing = rep doesn't count. Rest 90 s." },
  expPush: { n: "Explosive push-ups", d: "Push hard enough that your hands leave the floor (or as fast as you can). Easier: from knees. Rest 90 s." },
  clapPush: { n: "Clap push-ups", d: "Same as explosive push-ups, add the clap only if every rep stays crisp. Rest 90 s." },
  wall: { n: "Wall press", d: "Push the wall like you're trying to move it, 5 s max effort, both arms. Rest 60 s." },
  pivot: { n: "Pivot punches", d: "Shadow rear straight, drive from the back foot through the hip, not the shoulder. Each side. Rest 60 s." },
  round: { n: "Gas tank round", d: "3 min: 30 s hard shadowboxing combos, 30 s burpees or mountain climbers, repeat. Effort 8 to 9 out of 10. Rest 60 s." },
  skip: { n: "Easy finisher", d: "Skipping or jog in place at a pace where you can still talk in short phrases." },
  test: { n: "Retest", d: "Today is test day. Open the test card at the top and beat your day 1 numbers." }
};
function s(id, dose) { return { ex: EX[id], dose: dose || "" }; }
function power(sets, reps, push) {
  var r = sets + " x " + reps;
  return [s("warm"), s("squatJump", r), s("broad", sets + " x 3"), s(push || "expPush", r), s("wall", "5 x 5 s"), s("pivot", sets + " x 6 / side"), s("cool")];
}
function gas(rounds, finisher) {
  return [s("warm"), s("round", rounds + " rounds"), s("skip", finisher), s("cool")];
}
function combo(sets, rounds) {
  return [s("warm"), s("squatJump", sets + " x 5"), s("expPush", sets + " x 5"), s("round", rounds + " rounds"), s("cool")];
}
export const PLAN = [
  { week: 1, note: "Learn the moves. Every rep at full intent, full rest. Do the day 1 test before session 1.",
    days: [{ t: "Power", items: power(3, 5) }, { t: "Gas tank", items: gas(3, "5 min") }, { t: "Power + gas", items: combo(2, 2) }] },
  { week: 2, note: "One more rep and one more round. Stop a set when reps slow down.",
    days: [{ t: "Power", items: power(3, 6) }, { t: "Gas tank", items: gas(4, "5 min") }, { t: "Power + gas", items: combo(3, 2) }] },
  { week: 3, note: "Hardest week. Clap push-ups if they stay crisp, 4 rounds holding your round 1 pace.",
    days: [{ t: "Power", items: power(4, 5, "clapPush") }, { t: "Gas tank", items: gas(4, "7 min") }, { t: "Power + gas", items: combo(3, 3) }] },
  { week: 4, note: "Lighter on purpose so you test fresh. Retest on day 28.",
    days: [{ t: "Power (light)", items: power(2, 5) }, { t: "Gas tank (light)", items: gas(2, "5 min") }, { t: "Test day", items: [s("warm"), s("test")] }] }
];
