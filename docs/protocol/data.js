/*
 * THE PROTOCOL. Content and scoring data.
 * Pure data + pure functions only. No DOM access here so this file is
 * unit-testable in Node (see production/protocol-v2/tests/) and reusable
 * if the UI is ever rebuilt.
 *
 * To add or edit a workout: edit WORKOUTS below. To add a category, add it
 * to CATEGORIES, add matching assessment-option entries, and add a WORKOUTS
 * entry with the same key. Nothing else needs to change.
 *
 * Style rule: no em dashes anywhere in this file. Use a period, comma, or
 * colon instead.
 */
(function (root) {
  "use strict";

  // ---------------------------------------------------------------------
  // CATEGORIES
  // ---------------------------------------------------------------------
  var CATEGORIES = {
    power: {
      id: "power",
      name: "Power",
      short: "Power",
      oneLiner: "Explosiveness and force production.",
      color: "#C82020"
    },
    speed: {
      id: "speed",
      name: "Speed",
      short: "Speed",
      oneLiner: "Fast hands, fast feet, fast reactions.",
      color: "#C82020"
    },
    conditioning: {
      id: "conditioning",
      name: "Conditioning",
      short: "Conditioning",
      oneLiner: "Repeat-effort ability and a real gas tank.",
      color: "#C82020"
    },
    footwork: {
      id: "footwork",
      name: "Footwork",
      short: "Footwork",
      oneLiner: "Positioning, angles, pivots, balance.",
      color: "#C82020"
    },
    strength: {
      id: "strength",
      name: "Strength",
      short: "Strength",
      oneLiner: "Full-body strength that actually transfers.",
      color: "#C82020"
    },
    mobility: {
      id: "mobility",
      name: "Mobility",
      short: "Mobility",
      oneLiner: "Hips, ankles, shoulders, thoracic spine.",
      color: "#C82020"
    }
  };

  var CATEGORY_ORDER = ["power", "speed", "conditioning", "footwork", "strength", "mobility"];

  // ---------------------------------------------------------------------
  // ASSESSMENT. "Find Your Fighter Weakness"
  // 5 questions, about 60-90 seconds. Q1-Q3 score categories (weighted).
  // Q4-Q5 are segmentation only (never scored). They personalize copy and
  // become optional lead-segmentation data, never gate anything.
  // Tie-break order is fixed and documented so results are deterministic.
  // ---------------------------------------------------------------------
  var TIE_BREAK_ORDER = ["power", "conditioning", "strength", "speed", "footwork", "mobility"];

  var ASSESSMENT = {
    title: "Find Your Fighter Weakness",
    subhead: "Answer a few questions and we'll show you where to start.",
    disclaimer: "This is a training-priority tool, not a medical assessment.",
    questions: [
      {
        id: "q1_breakdown",
        weight: 3,
        prompt: "When you're sparring or drilling hard, what gives out first?",
        options: [
          { id: "a", label: "My power fades late in the round", category: "power" },
          { id: "b", label: "My hands and feet slow down", category: "speed" },
          { id: "c", label: "My gas tank goes", category: "conditioning" },
          { id: "d", label: "My positioning falls apart", category: "footwork" },
          { id: "e", label: "I feel physically weak, not out of breath", category: "strength" },
          { id: "f", label: "I tighten up and can't move freely", category: "mobility" }
        ]
      },
      {
        id: "q2_want",
        weight: 2,
        prompt: "What do you most want to improve right now?",
        options: [
          { id: "a", label: "Punch and kick power", category: "power" },
          { id: "b", label: "Speed and reaction time", category: "speed" },
          { id: "c", label: "Conditioning", category: "conditioning" },
          { id: "d", label: "Footwork and movement", category: "footwork" },
          { id: "e", label: "Overall strength", category: "strength" },
          { id: "f", label: "Mobility and flexibility", category: "mobility" }
        ]
      },
      {
        id: "q3_gap",
        weight: 2,
        prompt: "Outside of combat training, what do you do the least right now?",
        options: [
          { id: "a", label: "Explosive or power work", category: "power" },
          { id: "b", label: "Dedicated speed or reaction drills", category: "speed" },
          { id: "c", label: "Structured conditioning", category: "conditioning" },
          { id: "d", label: "Footwork or movement drills", category: "footwork" },
          { id: "e", label: "Strength training", category: "strength" },
          { id: "f", label: "Stretching or mobility work", category: "mobility" }
        ]
      },
      {
        id: "q4_frequency",
        weight: 0,
        segment: true,
        prompt: "How often are you training combat sports right now?",
        options: [
          { id: "a", label: "1 to 2x a week", value: "1-2" },
          { id: "b", label: "3x a week", value: "3" },
          { id: "c", label: "4 to 5x a week", value: "4-5" },
          { id: "d", label: "6+ times a week", value: "6+" }
        ]
      },
      {
        id: "q5_equipment",
        weight: 0,
        segment: true,
        prompt: "What equipment do you usually have access to?",
        options: [
          { id: "a", label: "None", value: "none" },
          { id: "b", label: "Basic (bands, jump rope, pull-up bar)", value: "basic" },
          { id: "c", label: "Full gym", value: "gym" },
          { id: "d", label: "Depends where I am", value: "varies" }
        ]
      }
    ]
  };

  // ---------------------------------------------------------------------
  // SCORING. Deterministic. Same answers always produce the same result.
  // ---------------------------------------------------------------------
  function scoreAssessment(answers) {
    answers = answers || {};
    var scores = {};
    CATEGORY_ORDER.forEach(function (c) { scores[c] = 0; });

    var q1Category = null;

    ASSESSMENT.questions.forEach(function (q) {
      if (!q.weight) return; // segmentation questions don't score
      var chosenOptionId = answers[q.id];
      if (!chosenOptionId) return;
      var opt = q.options.filter(function (o) { return o.id === chosenOptionId; })[0];
      if (!opt || !opt.category) return;
      scores[opt.category] += q.weight;
      if (q.id === "q1_breakdown") q1Category = opt.category;
    });

    var ranked = CATEGORY_ORDER.slice().sort(function (a, b) {
      if (scores[b] !== scores[a]) return scores[b] - scores[a];
      return TIE_BREAK_ORDER.indexOf(a) - TIE_BREAK_ORDER.indexOf(b);
    });

    return {
      scores: scores,
      primary: ranked[0],
      secondary: ranked[1],
      ranked: ranked,
      q1Category: q1Category
    };
  }

  // ---------------------------------------------------------------------
  // RESULT COPY. Per category. "why" combines the user's own Q1 answer
  // with a mechanism-based explanation, never a generic blurb.
  // ---------------------------------------------------------------------
  var RESULT_COPY = {
    power: {
      headline: "Power",
      why: "Power fading late is a force problem, not a cardio problem. About 75% of punch force comes from your legs and trunk, not your arm. This session trains your legs and hips to keep producing force when it matters."
    },
    speed: {
      headline: "Speed",
      why: "Losing speed under pressure is about how fast you produce force, not your cardio. Your legs drive hand and foot speed more than people assume. Reacting to something unpredictable is a different skill than moving fast on cue, so this session trains both."
    },
    conditioning: {
      headline: "Conditioning",
      why: "A gas tank that disappears mid-fight is usually an aerobic problem. Your aerobic system recovers you between bursts, even though each exchange itself is anaerobic. This session builds that base and trains you to repeat hard efforts without a full reset."
    },
    footwork: {
      headline: "Footwork",
      why: "Positioning breaking down under pressure is a movement and balance problem. Footwork that looks clean at a walk doesn't always survive contact. This session sharpens angles, pivots and balance under time pressure."
    },
    strength: {
      headline: "Strength",
      why: "Feeling weak rather than gassed points to a real strength gap: not size, but the base force your power and durability are built on. This session prioritizes your legs and trunk, since that's where most of your usable strength lives."
    },
    mobility: {
      headline: "Mobility",
      why: "Tightening up under fatigue is often a mobility problem showing up as a technique problem. Hips, ankles, shoulders and your upper back matter most for a striker. This session opens those up and keeps them durable."
    }
  };

  // ---------------------------------------------------------------------
  // WORKOUTS
  // Every workout is a flat list of "sections" -> "steps".
  // A step is one of:
  //   { type: 'exercise', name, mode: 'time'|'reps', seconds?, repsLabel?,
  //     cues: [max 3], mistake, easier, harder, restSeconds }
  //   { type: 'rest', seconds }
  //   { type: 'note', text }   (a short instruction shown, not timed)
  // mistake/easier/harder use "" when there's nothing to show. app.js only
  // renders them when truthy, so an empty string is simply skipped.
  // ---------------------------------------------------------------------
  var WORKOUTS = {

    power: {
      category: "power",
      title: "Power Protocol",
      duration: "20 minutes",
      equipment: "No equipment",
      goal: "Build explosive force through your legs, hips and trunk, the parts of your body that actually generate punching and kicking power.",
      whyThisWorks: "About 75% of strike force comes from your legs and trunk, not your arm. Plyometric training's direct effect on striking power is real but modest, so this session builds the underlying quality (rate of force development) rather than promising a specific power increase. Combined with your technical training, that's what turns into fight power.",
      coachingNotes: [
        "Every rep is maximal intent. This is not a burnout session.",
        "Full rest between sets is mandatory, not optional. Power needs a fresh nervous system.",
        "Stop a set the moment reps visibly slow down. Slow reps here build fatigue, not power."
      ],
      progression: [
        "Week 1: baseline. Do exactly what's written.",
        "Week 2: add 1 rep per set across the board.",
        "Week 3: hold reps, move to the harder variation on 2 exercises.",
        "Week 4: retake the assessment and reassess your priority."
      ],
      sections: [
        {
          title: "Warm-up",
          steps: [
            { type: "note", text: "5 minutes. Get the hips, ankles and shoulders moving before anything explosive." },
            { type: "exercise", name: "Hip and ankle circles", mode: "time", seconds: 45, cues: ["Big, controlled circles, both directions"], mistake: "Rushing through with tiny movements", easier: "Hold a wall for balance", harder: "", restSeconds: 15 },
            { type: "exercise", name: "Bodyweight squats", mode: "reps", repsLabel: "10 reps, easy pace", cues: ["Full depth, controlled"], mistake: "Bouncing at the bottom", easier: "Squat to a chair", harder: "Add a pause at the bottom", restSeconds: 15 },
            { type: "exercise", name: "Easy shadowboxing", mode: "time", seconds: 90, cues: ["Build intensity gradually, don't go hard yet"], mistake: "Starting at full speed", easier: "Footwork only, no punches", harder: "", restSeconds: 30 },
            { type: "exercise", name: "Light pogo hops", mode: "time", seconds: 20, cues: ["Small, quick, off the floor. Priming, not working."], mistake: "Jumping high and heavy this early", easier: "Ankle bounces, feet barely leave floor", harder: "", restSeconds: 30 }
          ]
        },
        {
          title: "Round 1: Lower Body Power",
          steps: [
            { type: "exercise", name: "Squat jumps", mode: "reps", repsLabel: "3 sets x 5 reps", cues: ["Explode up, land soft and quiet", "Reset fully between reps"], mistake: "Rushing reps back to back", easier: "Step-back lunge jump, lower height", harder: "Add a pause squat before each jump", restSeconds: 90 },
            { type: "exercise", name: "Broad jump", mode: "reps", repsLabel: "3 sets x 3 reps", cues: ["Jump for distance, stick the landing"], mistake: "Chasing distance with a bad landing", easier: "Explosive squat-to-calf-raise, no jump", harder: "Single-leg broad jump", restSeconds: 90 }
          ]
        },
        {
          title: "Round 2: Upper Body and Trunk Power",
          steps: [
            { type: "exercise", name: "Explosive push-ups", mode: "reps", repsLabel: "3 sets x 5 reps", cues: ["Push hard enough that your hands leave the floor, or push as fast as you can"], mistake: "Slowing down to control the descent, let it be quick", easier: "Explosive push-up from knees", harder: "Clap push-up", restSeconds: 90 },
            { type: "exercise", name: "Overcoming wall press", mode: "reps", repsLabel: "5 sets x 5 sec, both arms", cues: ["Push into the wall as hard as you can, like you're trying to move it"], mistake: "Half effort, this should feel maximal even though nothing moves", easier: "Reduce to 3 sec holds", harder: "Single-arm", restSeconds: 60 },
            { type: "exercise", name: "Rotational shadow pivot-punch", mode: "reps", repsLabel: "3 sets x 6 reps / side", cues: ["Drive the punch from your back foot through your hip, not your arm"], mistake: "Punching with just the shoulder, no hip turn", easier: "Slow the pivot down, focus on the sequence", harder: "Add a resistance band anchored behind you", restSeconds: 60 }
          ]
        },
        {
          title: "Cool-down",
          steps: [
            { type: "exercise", name: "Easy shadowboxing", mode: "time", seconds: 90, cues: ["Loose, easy, let your heart rate come down"], mistake: "", easier: "", harder: "", restSeconds: 0 },
            { type: "exercise", name: "Breathing reset", mode: "time", seconds: 60, cues: ["Slow nasal breathing, relax the shoulders"], mistake: "", easier: "", harder: "", restSeconds: 0 }
          ]
        }
      ]
    },

    speed: {
      category: "speed",
      title: "Speed Protocol",
      duration: "18 minutes",
      equipment: "No equipment",
      goal: "Develop fast hands, fast feet, and the ability to react and change direction on an unpredictable cue, not just move fast on command.",
      whyThisWorks: "Punch and kick speed is driven more by your legs than most people assume. It's a ground-up movement, not an arm movement. Reacting to something unpredictable and moving fast on cue are two different, mostly independent skills, so this session trains both.",
      coachingNotes: [
        "Max intent on every rep. The second your speed drops, the rep stops teaching you speed.",
        "Rest is long here on purpose. Rushing it defeats the point.",
        "This should feel sharp and fast, not exhausting. If it feels like conditioning, you're going too long."
      ],
      progression: [
        "Week 1: baseline, exactly as written.",
        "Week 2: add 1 rep to each round.",
        "Week 3: keep reps the same, make the reactive drill less predictable.",
        "Week 4: retake the assessment and reassess your priority."
      ],
      sections: [
        {
          title: "Warm-up",
          steps: [
            { type: "note", text: "4 minutes. Raise heart rate and prime fast-twitch output without fatiguing it." },
            { type: "exercise", name: "High knees", mode: "time", seconds: 30, cues: ["Quick, light steps, not high effort yet"], mistake: "", easier: "March in place", harder: "", restSeconds: 15 },
            { type: "exercise", name: "Ankle bounces", mode: "time", seconds: 30, cues: ["Stay on the balls of your feet"], mistake: "", easier: "", harder: "", restSeconds: 15 },
            { type: "exercise", name: "Build-up shadow sprints", mode: "reps", repsLabel: "3 x 5 sec, building each time", cues: ["Each one a little faster than the last"], mistake: "Going all-out on the first one", easier: "", harder: "", restSeconds: 30 }
          ]
        },
        {
          title: "Round 1: Fast Feet",
          steps: [
            { type: "exercise", name: "Quick-feet footwork pattern", mode: "time", seconds: 20, cues: ["Ladder or taped-line pattern on the floor, max speed, stay light"], mistake: "Landing heavy and flat-footed", easier: "Half speed, focus on the pattern", harder: "Call your own direction changes mid-pattern", restSeconds: 75 },
            { type: "note", text: "Repeat the footwork pattern 4 times total." }
          ]
        },
        {
          title: "Round 2: Fast Hands",
          steps: [
            { type: "exercise", name: "Max-speed combo shadowboxing", mode: "time", seconds: 15, cues: ["Jab-cross-hook at maximum hand speed, form stays clean"], mistake: "Adding power and losing speed. This round is about speed, not force.", easier: "Single punches, not combos", harder: "4-5 punch combos", restSeconds: 60 },
            { type: "note", text: "Repeat 4 times total." }
          ]
        },
        {
          title: "Round 3: Reactive Agility",
          steps: [
            { type: "exercise", name: "Self-cued direction change", mode: "time", seconds: 10, cues: ["Call out a direction unpredictably (left, right, back, pivot) and react to your own voice as fast as possible"], mistake: "Planning the pattern in advance, that trains the wrong skill", easier: "Use only 2 directions", harder: "Add a partner calling directions instead of yourself", restSeconds: 75 },
            { type: "note", text: "Repeat 5 times total." }
          ]
        },
        {
          title: "Round 4: Acceleration",
          steps: [
            { type: "exercise", name: "Short sprint burst", mode: "time", seconds: 6, cues: ["Stairs, a hallway, or a short outdoor stretch. Maximal acceleration."], mistake: "Not resting long enough between reps", easier: "Fast walk or power-step version", harder: "Uphill or stairs", restSeconds: 90 },
            { type: "note", text: "Repeat 4 times total." }
          ]
        },
        {
          title: "Cool-down",
          steps: [
            { type: "exercise", name: "Easy footwork", mode: "time", seconds: 60, cues: ["Loose and easy, bring the heart rate down"], mistake: "", easier: "", harder: "", restSeconds: 0 }
          ]
        }
      ]
    },

    conditioning: {
      category: "conditioning",
      title: "Conditioning Protocol",
      duration: "24 minutes",
      equipment: "No equipment",
      goal: "Improve your ability to sustain repeated hard efforts without unnecessarily destroying your recovery: both your aerobic base and your repeat-effort capacity.",
      whyThisWorks: "Your aerobic system recovers you between bursts, even though each exchange in a fight is powered anaerobically. In boxing, oxygen demand climbs toward your max by the final round, which is why a bigger aerobic base means faster recovery between exchanges. Interval training that mirrors real work-rest patterns is the single best-evidenced conditioning method for combat athletes in current research, which is what the main block here is built around.",
      coachingNotes: [
        "The interval rounds should feel like real rounds: hard, with output that dips late but never fully stops.",
        "Use the talk test for the steady block. You should manage short phrases, not full sentences.",
        "If your form completely breaks down, stop the round early. Finishing badly doesn't build anything."
      ],
      progression: [
        "Week 1: baseline, 3 rounds.",
        "Week 2: add a 4th round.",
        "Week 3: keep 4 rounds, increase your output within each round.",
        "Week 4: retake the assessment and reassess your priority."
      ],
      sections: [
        {
          title: "Warm-up",
          steps: [
            { type: "exercise", name: "Easy shadowboxing, building intensity", mode: "time", seconds: 180, cues: ["Start slow, build to moderate by the end"], mistake: "Starting too hard", easier: "Footwork only for the first minute", harder: "", restSeconds: 30 }
          ]
        },
        {
          title: "Round 1: Repeat Effort",
          steps: [
            { type: "exercise", name: "Shadowboxing and bodyweight circuit", mode: "time", seconds: 180, cues: ["Alternate 30 sec shadowboxing combos with 30 sec burpees or mountain climbers", "Effort should feel like an 8-9 out of 10"], mistake: "Pacing it like a marathon instead of a real round", easier: "Reduce burpees to step-back burpees, no jump", harder: "Add a 4th minute", restSeconds: 60 }
          ]
        },
        {
          title: "Round 2: Repeat Effort",
          steps: [
            { type: "exercise", name: "Shadowboxing and bodyweight circuit", mode: "time", seconds: 180, cues: ["Same structure as Round 1. Output will naturally drop a little, that's expected."], mistake: "Quitting early instead of pacing through the dip", easier: "Extend rest slightly if needed", harder: "", restSeconds: 60 }
          ]
        },
        {
          title: "Round 3: Repeat Effort",
          steps: [
            { type: "exercise", name: "Shadowboxing and bodyweight circuit", mode: "time", seconds: 180, cues: ["Last round. Hold your output as close to Round 1 as you can."], mistake: "", easier: "", harder: "", restSeconds: 60 }
          ]
        },
        {
          title: "Aerobic Base Finisher",
          steps: [
            { type: "exercise", name: "Continuous skipping or jog in place", mode: "time", seconds: 300, cues: ["Moderate, conversational pace. Base-building, not another hard round."], mistake: "Turning this into another max-effort round", easier: "Fast walk", harder: "", restSeconds: 0 }
          ]
        },
        {
          title: "Cool-down",
          steps: [
            { type: "exercise", name: "Walk it out and breathe", mode: "time", seconds: 120, cues: ["Slow nasal breathing"], mistake: "", easier: "", harder: "", restSeconds: 0 }
          ]
        }
      ]
    },

    footwork: {
      category: "footwork",
      title: "Footwork Protocol",
      duration: "18 minutes",
      equipment: "No equipment",
      goal: "Sharpen positioning, angles, pivots and balance, the movement quality that usually falls apart first once things speed up.",
      whyThisWorks: "This is a skill session, not a conditioning session. Footwork that only holds up at a walking pace doesn't survive real pressure. Practicing pivots and angle-creation, then adding an unpredictable reactive element, is what makes movement quality hold up when things get fast.",
      coachingNotes: [
        "Go at a controlled pace where every step is clean. Speed comes later, not today.",
        "A good angle beats fast feet with no purpose.",
        "If you have a mirror or a phone camera, use it. You can't feel a dropped guard or a wide stance."
      ],
      progression: [
        "Week 1: baseline, controlled pace.",
        "Week 2: add one more pattern or round.",
        "Week 3: add the reactive element to every drill, not just the pivot round.",
        "Week 4: retake the assessment and reassess your priority."
      ],
      sections: [
        {
          title: "Warm-up",
          steps: [
            { type: "exercise", name: "Ankle mobility and easy bounce", mode: "time", seconds: 120, cues: ["Stay light on your feet the whole time"], mistake: "", easier: "", harder: "", restSeconds: 30 }
          ]
        },
        {
          title: "Round 1: Ladder and Line Patterns",
          steps: [
            { type: "exercise", name: "In-in-out-out pattern", mode: "time", seconds: 30, cues: ["Ladder or taped line on the floor, controlled and precise steps"], mistake: "Rushing and missing squares or lines", easier: "Half speed", harder: "Add a punch at the end of each pattern", restSeconds: 30 },
            { type: "exercise", name: "Lateral shuffle", mode: "time", seconds: 30, cues: ["Stay low, don't cross your feet"], mistake: "Standing too upright", easier: "Reduce distance", harder: "Add direction changes mid-shuffle", restSeconds: 30 },
            { type: "exercise", name: "Carioca (grapevine)", mode: "time", seconds: 30, cues: ["Rotate the hips, stay light"], mistake: "Losing balance on the crossover step", easier: "Slow the tempo down", harder: "", restSeconds: 30 }
          ]
        },
        {
          title: "Round 2: Pivots and Angles",
          steps: [
            { type: "exercise", name: "Step-pivot off the jab", mode: "time", seconds: 60, cues: ["Jab, then pivot off your lead foot to create a new angle", "Finish facing your imaginary opponent, not side-on"], mistake: "Pivoting the upper body without moving the feet", easier: "Practice the pivot alone, no jab yet", harder: "Add a follow-up punch after the pivot", restSeconds: 30 },
            { type: "exercise", name: "Circle off the line", mode: "time", seconds: 60, cues: ["Imagine a fence or ropes behind you. Circle away from it, not into it."], mistake: "Circling into the imaginary danger zone", easier: "Walk through it slowly first", harder: "", restSeconds: 30 }
          ]
        },
        {
          title: "Round 3: Reactive Movement",
          steps: [
            { type: "exercise", name: "Self-cued angle change", mode: "time", seconds: 60, cues: ["Call your own direction unpredictably and react: left, right, pivot, back"], mistake: "Planning the sequence ahead of time", easier: "Use only 2 directions", harder: "Add a partner calling it instead", restSeconds: 30 }
          ]
        },
        {
          title: "Cool-down",
          steps: [
            { type: "exercise", name: "Easy movement and breathing", mode: "time", seconds: 90, cues: ["Loose and relaxed"], mistake: "", easier: "", harder: "", restSeconds: 0 }
          ]
        }
      ]
    },

    strength: {
      category: "strength",
      title: "Strength Protocol",
      duration: "28 minutes",
      equipment: "No equipment (bodyweight)",
      goal: "Build real, useful full-body strength, prioritizing your legs and trunk, since that's where most of your usable striking strength actually lives.",
      whyThisWorks: "Legs and trunk supply the large majority of striking force, so this session is built around single-leg and rotational-trunk work, with upper-body pushing and pulling as support. Bodyweight training builds real strength up to a genuine ceiling. Once these get easy, the single best upgrade is one resistance band or one adjustable dumbbell, not a gym membership.",
      coachingNotes: [
        "The rule: hit the top of your rep range on every set with 1-2 reps left in the tank. Next session, add a rep. Once you're at the top of the range, make the exercise harder and drop back to the bottom.",
        "The last 1-2 reps of a set should be hard but clean, not a grinding fight to failure.",
        "If a movement is too hard to do with good form, use the easier version. That's correct programming, not a failure."
      ],
      progression: [
        "Week 1: baseline sets and reps as written.",
        "Week 2: apply the double-progression rule. Add reps wherever you hit the top of the range clean.",
        "Week 3: wherever you've maxed the rep range, move to the harder variation and drop back to the bottom.",
        "Week 4: retake the assessment and reassess your priority."
      ],
      sections: [
        {
          title: "Warm-up",
          steps: [
            { type: "exercise", name: "Bodyweight squats", mode: "reps", repsLabel: "10 reps, easy", cues: ["Full range, controlled"], mistake: "", easier: "", harder: "", restSeconds: 20 },
            { type: "exercise", name: "Arm circles and hip openers", mode: "time", seconds: 60, cues: ["Big, controlled range"], mistake: "", easier: "", harder: "", restSeconds: 20 }
          ]
        },
        {
          title: "Block 1: Legs",
          steps: [
            { type: "exercise", name: "Split squat (rear foot elevated if you have a chair)", mode: "reps", repsLabel: "3 sets x 8-15 / leg", cues: ["Front knee tracks over the foot, controlled descent"], mistake: "Rushing the eccentric, slow it down", easier: "Standard reverse lunge, no elevation", harder: "Add a pause at the bottom", restSeconds: 90 },
            { type: "exercise", name: "Single-leg RDL or Nordic curl (couch or partner-anchored)", mode: "reps", repsLabel: "3 sets x 5-10 / leg", cues: ["Slow and controlled, this is about the lowering phase"], mistake: "Using momentum instead of control", easier: "Reduce range of motion", harder: "Slow the eccentric further, 5+ seconds down", restSeconds: 90 }
          ]
        },
        {
          title: "Block 2: Push and Pull",
          steps: [
            { type: "exercise", name: "Push-up progression", mode: "reps", repsLabel: "3 sets x 8-15", cues: ["Full range, chest to just above the floor"], mistake: "Half reps to hit a number", easier: "Incline push-up, hands elevated", harder: "Decline push-up, feet elevated", restSeconds: 90 },
            { type: "exercise", name: "Doorframe or table row", mode: "reps", repsLabel: "3 sets x 6-12", cues: ["Squeeze the shoulder blades together at the top"], mistake: "Using body swing instead of pulling with the back", easier: "Reduce the angle, stand more upright", harder: "Pull-up if you have a bar", restSeconds: 90 }
          ]
        },
        {
          title: "Block 3: Core and Carry",
          steps: [
            { type: "exercise", name: "Anti-rotation hold (towel, band, or isometric plank reach)", mode: "reps", repsLabel: "3 sets x 10 / side", cues: ["Resist the urge to let your hips rotate"], mistake: "Letting the trunk twist under load", easier: "Reduce hold time", harder: "Add a band for resistance", restSeconds: 60 },
            { type: "exercise", name: "Rotational shadow throw", mode: "reps", repsLabel: "3 sets x 10 / side", cues: ["Drive the rotation from your hips, not just your arms"], mistake: "Arm-only rotation", easier: "Slow the tempo down", harder: "Add a light weighted object", restSeconds: 60 },
            { type: "exercise", name: "Loaded carry (backpack or any heavy household object)", mode: "time", seconds: 35, cues: ["Stand tall, brace your core, walk with control"], mistake: "Leaning to one side under the load", easier: "Reduce the load or the time", harder: "Increase the load", restSeconds: 60 }
          ]
        },
        {
          title: "Cool-down",
          steps: [
            { type: "exercise", name: "Easy stretch and breathing", mode: "time", seconds: 90, cues: ["Nothing intense, just settle down"], mistake: "", easier: "", harder: "", restSeconds: 0 }
          ]
        }
      ]
    },

    mobility: {
      category: "mobility",
      title: "Mobility Protocol",
      duration: "18 minutes",
      equipment: "No equipment",
      goal: "Open up and maintain the ranges of motion that matter most for a striker: hips, ankles, thoracic spine, and shoulders.",
      whyThisWorks: "There isn't strong direct research proving a specific mobility routine prevents injury in combat athletes, so this session is built on sound, honest practice rather than an overstated guarantee: dynamic movement before training, static holds after, and a few strength-through-range holds that build mobility and durability at the same time.",
      coachingNotes: [
        "Move to the edge of a comfortable range, not into pain.",
        "Controlled and steady. No bouncing.",
        "This is durability work, not a stretch-and-forget routine. The loaded holds matter as much as the stretches."
      ],
      progression: [
        "Week 1: baseline hold times.",
        "Week 2: add 5-10 seconds to each hold.",
        "Week 3: add range where it's pain-free. Go slightly deeper, not faster.",
        "Week 4: retake the assessment and reassess your priority."
      ],
      sections: [
        {
          title: "Warm-up",
          steps: [
            { type: "exercise", name: "Total-body joint circles", mode: "time", seconds: 120, cues: ["Ankles, hips, shoulders, neck: easy and controlled"], mistake: "", easier: "", harder: "", restSeconds: 15 }
          ]
        },
        {
          title: "Block 1: Hips and Ankles",
          steps: [
            { type: "exercise", name: "90/90 hip switches", mode: "reps", repsLabel: "3 rounds x 8 switches", cues: ["Keep the chest tall, rotate through the hips"], mistake: "Using your hands to muscle the switch instead of the hips", easier: "Reduce range, go slower", harder: "Add a reach overhead as you switch", restSeconds: 30 },
            { type: "exercise", name: "Deep lunge rotation stretch", mode: "time", seconds: 40, cues: ["Reach through and rotate toward your front leg"], mistake: "Rushing the rotation", easier: "Reduce lunge depth", harder: "", restSeconds: 20 },
            { type: "exercise", name: "Deep squat ankle rocks", mode: "time", seconds: 40, cues: ["Rock your weight forward over your toes, heels down"], mistake: "Letting the heels lift", easier: "Hold onto something for balance", harder: "", restSeconds: 20 }
          ]
        },
        {
          title: "Block 2: Thoracic Spine",
          steps: [
            { type: "exercise", name: "Open-book rotation", mode: "reps", repsLabel: "2 sets x 8 / side", cues: ["Rotate from the mid-back, keep the hips still"], mistake: "Rotating from the lower back or hips instead", easier: "Reduce range", harder: "Slow the tempo further", restSeconds: 20 },
            { type: "exercise", name: "Thread-the-needle", mode: "reps", repsLabel: "2 sets x 8 / side", cues: ["Follow your hand with your eyes"], mistake: "", easier: "", harder: "", restSeconds: 20 }
          ]
        },
        {
          title: "Block 3: Shoulders and Loaded Holds",
          steps: [
            { type: "exercise", name: "Wall slides", mode: "reps", repsLabel: "2 sets x 10", cues: ["Keep your lower back flat against the wall"], mistake: "Arching the back to force the range", easier: "Reduce range", harder: "", restSeconds: 30 },
            { type: "exercise", name: "Deep split-squat isometric hold", mode: "time", seconds: 30, cues: ["Sink as deep as you can control, breathe steadily"], mistake: "Holding your breath", easier: "Reduce depth", harder: "Add 5-10 seconds", restSeconds: 30 }
          ]
        },
        {
          title: "Cool-down",
          steps: [
            { type: "exercise", name: "Box breathing", mode: "time", seconds: 120, cues: ["4 sec in, 4 sec hold, 4 sec out, 4 sec hold"], mistake: "", easier: "", harder: "", restSeconds: 0 }
          ]
        }
      ]
    }
  };

  // ---------------------------------------------------------------------
  // UI COPY. Landing page, STANCE CTA, disclaimers, completion screens.
  // Kept here so none of it is hardcoded into index.html/app.js.
  // ---------------------------------------------------------------------
  var UI_COPY = {
    nav: {
      home: "Home",
      quiz: "Quiz",
      retakeQuiz: "Retake",
      yourWorkout: "My Workout",
      allWorkouts: "Protocols",
      exitWorkout: "Exit"
    },
    landing: {
      eyebrow: "@matteofights / Free",
      title: "THE PROTOCOL",
      subtitle: "The At-Home Fighter Performance System",
      hook: "Find your biggest physical weakness. Get a workout built to address it.",
      cta: "Find My Weakness",
      problemTitle: "Your combat training develops technique.",
      problemBody: "It doesn't automatically develop power, speed, conditioning, footwork, strength and mobility. Most of that can be trained outside the gym: a bedroom, a hotel room, a park.",
      systemTitle: "The System",
      whyBuiltTitle: "Why I built this",
      whyBuiltBody: "I've trained across Thailand, Switzerland and Rome. First Muay Thai fight at 16. Broken fibula. Now rebuilding from a torn ACL. I built this because I wish someone had handed it to me early. Not a random workout, a system with a reason behind every part of it."
    },
    assessment: {
      startCta: "Start the assessment",
      nextCta: "Next",
      progressLabel: "Question {current} of {total}"
    },
    result: {
      teaserTitle: "Your Priority",
      teaserCta: "Get My Protocol",
      teaserPrompt: "Want your personalized protocol?",
      teaserSubtext: "Enter your email and I'll unlock your result and your workout. No spam, no newsletter.",
      emailPlaceholder: "you@email.com",
      emailCta: "Get My Protocol",
      secondaryLabel: "Secondary focus",
      statBlockTitle: "Your Fighter Profile",
      fullResultTitle: "Your Result",
      whatToDoLabel: "What to do",
      startWorkoutCta: "Start Your Workout",
      browseAllCta: "Browse all 6 Protocols",
      downloadCta: "Download this workout"
    },
    workout: {
      startCta: "Start",
      doneCta: "Done",
      skipRestCta: "Skip rest",
      restLabel: "Rest",
      nextUp: "Next up",
      downloadCta: "Download"
    },
    hub: {
      title: "All 6 Protocols",
      backCta: "Back to your result"
    },
    completion: {
      title: "Session Complete",
      body: "You just finished your first Protocol session.",
      whatYouTrainedLabel: "What you trained",
      nextLabel: "Next",
      nextBody: "Repeat this session 1-2x this week, then move to your secondary focus or come back and reassess in 2-4 weeks.",
      reassessCta: "Retake the assessment",
      optionalDataTitle: "Help me build better protocols",
      optionalDataBody: "Totally optional. Two quick questions, then you're done.",
      optionalDataSkip: "Skip",
      optionalDataSubmit: "Submit"
    },
    stance: {
      eyebrow: "The Next Step",
      title: "Don't train alone.",
      body: "We're building STANCE, a platform to help fighters train, improve and connect with other fighters. Train anywhere. Find fighters. Get better.",
      cta: "Join the early access list",
      note: "STANCE isn't launched yet. This joins the early access list, nothing more."
    },
    disclaimer: "Training should be appropriate to your current ability and health status. Stop if you experience pain, dizziness, instability, or other concerning symptoms, and seek appropriate professional guidance when needed. This is a training-priority tool, not medical advice."
  };

  // ---------------------------------------------------------------------
  // OPTIONAL POST-WORKOUT ICP FIELDS (never required, never gate anything)
  // ---------------------------------------------------------------------
  var OPTIONAL_FIELDS = {
    instagram: {
      label: "Instagram handle (optional)",
      placeholder: "@yourhandle"
    },
    combatSport: {
      label: "What do you train?",
      options: ["Boxing", "Muay Thai", "Kickboxing", "MMA", "Other or multiple"]
    },
    experience: {
      label: "How would you describe your level?",
      options: ["New (under 1 year)", "Intermediate (1-3 years)", "Experienced (3+ years)"]
    }
  };

  var api = {
    CATEGORIES: CATEGORIES,
    CATEGORY_ORDER: CATEGORY_ORDER,
    TIE_BREAK_ORDER: TIE_BREAK_ORDER,
    ASSESSMENT: ASSESSMENT,
    RESULT_COPY: RESULT_COPY,
    WORKOUTS: WORKOUTS,
    UI_COPY: UI_COPY,
    OPTIONAL_FIELDS: OPTIONAL_FIELDS,
    scoreAssessment: scoreAssessment
  };

  if (typeof module !== "undefined" && module.exports) {
    module.exports = api;
  }
  if (typeof root !== "undefined") {
    root.ProtocolData = api;
  }
})(typeof window !== "undefined" ? window : globalThis);
