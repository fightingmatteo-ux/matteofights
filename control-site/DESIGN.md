---
name: Matteo Fights Control
description: The round clock on the gym wall; a dark, one-user PWA where the next post is the countdown and the yes is held, not tapped.
colors:
  canvas: "#0B0B0D"
  housing: "#121214"
  face: "#08080A"
  rule: "#26252A"
  rule-hi: "#3A3840"
  paper: "#EEE7DC"
  dust: "#9C958B"
  red: "#C82020"
  red-ink: "#F0605A"
  red-lamp: "#E43A33"
  red-deep: "#6E0E0E"
  gold: "#C49040"
  gold-lamp: "#D9A552"
  unlit: "#1D1C20"
typography:
  display:
    fontFamily: "Bebas Neue, Arial Narrow, sans-serif"
    fontSize: "44px"
    fontWeight: 400
    lineHeight: 0.95
    letterSpacing: "0.02em"
  headline:
    fontFamily: "Bebas Neue, Arial Narrow, sans-serif"
    fontSize: "30px"
    fontWeight: 400
    lineHeight: 1
    letterSpacing: "0.02em"
  title:
    fontFamily: "Bebas Neue, Arial Narrow, sans-serif"
    fontSize: "26px"
    fontWeight: 400
    lineHeight: 1
    letterSpacing: "0.03em"
  body:
    fontFamily: "Geist, system-ui, -apple-system, sans-serif"
    fontSize: "16px"
    fontWeight: 400
    lineHeight: 1.5
  label:
    fontFamily: "Geist, system-ui, -apple-system, sans-serif"
    fontSize: "13px"
    fontWeight: 500
    lineHeight: 1.35
  figure:
    fontFamily: "Geist Mono, ui-monospace, SF Mono, Menlo, monospace"
    fontSize: "24px"
    fontWeight: 600
    lineHeight: 1
    letterSpacing: "-0.02em"
    fontFeature: "tnum"
  unit:
    fontFamily: "Geist Mono, ui-monospace, SF Mono, Menlo, monospace"
    fontSize: "11px"
    fontWeight: 500
    lineHeight: 1
    letterSpacing: "0.12em"
rounded:
  housing: "18px"
  face: "12px"
  ctl: "10px"
spacing:
  s1: "4px"
  s2: "8px"
  s3: "12px"
  s4: "16px"
  s5: "24px"
  s6: "32px"
  s7: "48px"
  s8: "72px"
  gutter: "16px"
  gutter-wide: "32px"
components:
  clock-housing:
    backgroundColor: "{colors.housing}"
    rounded: "{rounded.housing}"
    padding: "6px"
  clock-face:
    backgroundColor: "{colors.face}"
    textColor: "{colors.paper}"
    rounded: "{rounded.face}"
    padding: "14px 16px"
  button-primary:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.canvas}"
    rounded: "{rounded.ctl}"
    padding: "0 24px"
    height: "52px"
  button-line:
    backgroundColor: "transparent"
    textColor: "{colors.paper}"
    rounded: "{rounded.ctl}"
    padding: "0 24px"
    height: "52px"
  button-hold:
    backgroundColor: "{colors.red}"
    textColor: "#FFFFFF"
    rounded: "{rounded.ctl}"
    height: "52px"
    width: "100%"
  button-hold-holding:
    backgroundColor: "{colors.red-deep}"
  button-hold-done:
    backgroundColor: "{colors.gold}"
    textColor: "{colors.canvas}"
  answer-option:
    backgroundColor: "transparent"
    textColor: "{colors.paper}"
    rounded: "{rounded.ctl}"
    padding: "12px 16px"
    height: "52px"
  answer-option-picked:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.canvas}"
  filter-chip:
    backgroundColor: "transparent"
    textColor: "{colors.dust}"
    rounded: "{rounded.ctl}"
    padding: "0 14px"
    height: "40px"
  filter-chip-active:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.canvas}"
  waiting-block:
    textColor: "{colors.paper}"
    rounded: "{rounded.housing}"
    padding: "14px 16px"
  undo-bar:
    backgroundColor: "{colors.housing}"
    textColor: "{colors.paper}"
    padding: "8px 8px 8px 16px"
  sheet:
    backgroundColor: "{colors.housing}"
    textColor: "{colors.paper}"
    padding: "24px"
---

# Design System: Matteo Fights Control

## Overview

**Creative North Star: "The Gym Round Clock"**

The control center is the round clock bolted to the gym wall. It is read in a glance between rounds, from across the room, with gloves half on. A matte black housing holds an inset, slightly recessed face; on the face, seven-segment numerals count down to the next post with their unlit segments ghosted, a single phase lamp says whether anything needs attention, and a strip of fourteen cells shows the week as a program of rounds. Everything else in the product is the same hardware seen up close: LED meters for results, state lights on schedule rows, a segment digit counting down an undo.

The system is dark, dense where it reports and sparse where it asks. It speaks in light, not in fills: color appears as a lit lamp, a lit segment or a lit cell, almost never as a painted panel. Red means a yes is waiting or something failed, gold means a win or a milestone, paper means all clear. The one decisive act, approving a week, is a physical gesture: you hold START and the bezel fills around the clock until it rings.

It refuses the creator-scheduler default: no KPI tile rows, no calendar grid, no card stacks. Brand stays binding from the fight-poster side: brand black, combat red, gold for wins, Bebas headlines, premium and serious, never playful or pastel.

**Key Characteristics:**
- Housing plus inset face as the one container idea; depth is carved inward, not lifted outward.
- Seven-segment SVG numerals with ghosted unlit segments for the hero figure and the undo count.
- Three phase colors (red, gold, paper) carried by lamps, segments and cells.
- Every number in Geist Mono with tabular figures.
- Press-and-hold and timed undo as the two guards on any action that changes what gets posted.

## Colors

A near-black instrument palette where color is light emitted by hardware, and only three things are allowed to glow.

### Primary
- **Combat Red** (`red`): the "a yes is waiting" and "a post failed" signal. Fills the hold-to-approve button, the needs-yes cell outline, failed cells, the decide badge, the normal line on every meter, and text selection. Brand-pinned.
- **Warning Ink** (`red-ink`): red for small text and for the lit segments when the clock is in its "yes waiting" phase (5.6:1 on canvas). Use it whenever red must be read, not just seen.
- **Lit Lamp Red** (`red-lamp`): the glowing bulb of the red phase lamp and the needs-yes state light. Bulb material only.
- **Pressed Red** (`red-deep`): the darkening fill that sweeps across the hold button while it is held.

### Secondary
- **Belt Gold** (`gold`): wins, milestones and confirmations. Winner cells, best meter rows, the hold progress bar and bezel fill, the approved state, focus rings, the text caret, "sent" notes, Matteo's own entries in the log, and the undo digit. Brand-pinned.
- **Lit Lamp Gold** (`gold-lamp`): the bulb of the gold phase lamp.

### Neutral
- **Gym Wall Black** (`canvas`): page background and the bars. Brand black.
- **Housing** (`housing`): the clock housing, sheets, the undo bar, row hover wash, image placeholders.
- **Inset Face** (`face`): the recessed clock face and text-field wells, darker than the wall it sits in.
- **Hairline** (`rule`): dividers, row borders, inner housing edge, chip outlines.
- **Bezel Highlight** (`rule-hi`): the top-edge catch light on housings and sheets, line-button and option outlines.
- **Lit Paper** (`paper`): primary text, lit segments in the all-clear phase, primary buttons, picked states, the next-up cell.
- **Chalk Dust** (`dust`): secondary text, units, posted cells, scheduled cell outlines (6.4:1 on canvas).
- **Unlit** (`unlit`): dark cells, empty meter segments and off lamps; the "off" state of every light.

### Named Rules
**The Three Lights Rule.** Only red, gold and paper may glow. Red is attention (a yes is waiting, something failed), gold is a win or a confirmation, paper is all clear or "this one". No other hue enters the interface.

**The Light, Not Paint Rule.** State color is carried by lamps, lit segments, cells, outlines and short ink, not by filled panels. The waiting block is the one tinted surface, and only as a faint red wash (10% to 4%) under a red hairline.

**The Ink Split Rule.** Brand red (`red`) is for fills and marks; any red text under 18px uses `red-ink`.

## Typography

**Display Font:** Bebas Neue (with Arial Narrow)
**Body Font:** Geist (with system-ui)
**Label/Mono Font:** Geist Mono (with ui-monospace, SF Mono, Menlo)

**Character:** Bebas is the fight poster on the wall, used only for words that announce. Geist is the training partner talking, plain and short. Geist Mono is the scoreboard: every count, time and view figure sits in it on tabular figures so numbers line up and never jitter.

### Hierarchy
- **Display** (Bebas 400, 44px, 0.95): page titles. Results verdicts go larger (52px, 0.95) as the one loud word per verdict.
- **Headline** (Bebas 400, 30px, 1; 40px from 960px): the day word and time on the clock face ("TONIGHT 6:30 PM").
- **Title** (Bebas 400, 26px, 1, 0.03em): section heads, the wordmark, the waiting block's count.
- **Body** (Geist 400, 16px, 1.5): running text; ledes and context capped at 60ch, hooks at 34 to 42ch.
- **Label** (Geist 500, 13px): row labels, day headers, lamp text (600), meta lines in Chalk Dust. Sentence case.
- **Figure** (Geist Mono 600, 24px, 1, -0.02em, tabular): split views and other headline numbers; table cells and metric values use the same face at 13 to 17px.
- **Unit** (Geist Mono 500, 11px, 0.12em, uppercase): the HRS / MIN units printed under the segment readout, like the legend on a clock face.

### Named Rules
**The Scoreboard Rule.** Every figure (counts, times, views, x-normal, percentages) is Geist Mono with tabular numerals. Words are never set in mono except clock-face units.

**The Poster Words Rule.** Bebas only announces: titles, the day word, the verdict word. It never sets a sentence, a button or a number that has to be compared.

## Layout

Phone first at 390px with a 16px gutter (32px from 720px). A slim sticky top bar carries the wordmark and the live New York time; a fixed five-item bottom nav (60px targets) holds the views. From 960px the nav moves under the top bar as a horizontal tab rail, content caps at 1240px, and Home splits 5:6 with the clock column sticky on the left.

Spacing runs on a 4px base (4, 8, 12, 16, 24, 32, 48, 72). The face itself is tighter (6px housing inset, 10 to 14px internal gaps) because it is an instrument; page sections breathe at 32 to 48px. Lists are ruled rows with hairlines, not boxes: schedule rows (cover, time, hook, state light), log rows, fact rows and the results ladder all sit on 1px dividers. The reels grid is edge-to-edge three across on phone with 2px gaps, five and six across on larger screens.

Times are always New York time and labeled as such. Touch targets stay at or above 44px; primary controls are 52px.

## Elevation & Depth

Depth is carved inward. The housing is a flat surface with an inner hairline and a 1px catch light on its top edge; the face is recessed into it with a black inner edge and a deep inner shadow. Nothing on the page floats except transient layers (undo bar, toast, sheets), which take one heavy ambient drop shadow because they sit above the wall.

### Shadow Vocabulary
- **Housing edge** (`box-shadow: inset 0 0 0 1px var(--rule), inset 0 1px 0 var(--rule-hi)`): the clock housing; sheets use the catch light alone.
- **Inset face** (`box-shadow: inset 0 0 0 1px #000, inset 0 10px 30px rgba(0,0,0,.6)`): the recessed clock face.
- **Lit bulb** (`box-shadow: inset 0 -2px 2px rgba(0,0,0,.35), inset 0 1px 1px rgba(255,255,255,.35)`): a lit phase lamp; an off lamp takes only `inset 0 1px 1px rgba(0,0,0,.6)`.
- **Transient lift** (`box-shadow: 0 12px 32px rgba(0,0,0,.55)`): undo bar and toast only.

### Named Rules
**The Carved-In Rule.** Resting surfaces never cast drop shadows. Depth comes from inset edges and the recessed face; only layers that appear and go away may lift.

## Shapes

One radius family: 18px for the housing and anything at housing scale (waiting block, skeletons), 12px for the face (the housing radius minus its 6px inset, so the curves stay concentric), and 10px for every control (buttons, options, chips, toggles, text fields, the idea reply well). Lamps and state lights are circles; segments are 3px-rounded bars with a 6-degree italic skew; program cells and meter segments are small rounded rectangles. Reel covers are always 9:16.

## Components

### Clock (signature)
The housing (Housing, 18px, 6px inset) holds the inset face (Inset Face, 12px). On the face: the phase lamp top right; the seven-segment countdown (h:mm until next post) with HRS / MIN units beneath; the day word and time in Bebas; the hook in two lines; a 9:16 cover shot bottom right; and the program strip across the bottom behind a hairline. The lit segment color follows the phase: paper normally, `red-ink` when a yes is waiting. The colon blinks at 2s steps. With no post scheduled the readout shows ghosted blanks and says so plainly.

### Seven-segment readout
Drawn as live SVG from data: each digit is seven bars (a to g) in a 56 x 100 cell, 70 units apart, colons as two small squares; lit bars fill with the current LED color, unlit bars with the same color at 7% so the ghost of every 8 is always there. The whole group is skewed -6 degrees. It carries an accessible label in words. Reused at 16px wide in Belt Gold for the undo count.

### Phase lamp
A 10px bulb plus a 13px/600 label. Off: Unlit with an inset shade, label in Chalk Dust ("All clear"). Red: Lit Lamp Red bulb, Warning Ink label ("Yes waiting", "A post failed"). Gold: Lit Lamp Gold bulb, Belt Gold label ("Winner this week"). Precedence: waiting, then failed, then winner, then clear.

### Program strip
The week as seven day columns of 10px cells, one cell per reel, with two-letter mono day labels (today in paper). Cell states: unlit (empty), posted (Chalk Dust fill), scheduled (Chalk Dust 1.5px outline), needs yes (red outline over a faint red wash), failed (red fill), winner (gold fill), next (current LED color). A line above reads "Round n of 14".

### Waiting block
Appears only when reels need a yes. Housing radius, faint red wash, red hairline. Bebas count ("12 reels need your yes"), the date range in New York time, then a row: the hold button (full width) and a line-style Review button, with a one-line hint underneath.

### Buttons
- **Shape:** 10px corners, 52px tall, 24px side padding, Geist 600 16px.
- **Primary:** Lit Paper fill, black text; hover goes to white; press scales to 0.98.
- **Line:** transparent with a Bezel Highlight hairline; hover brightens the hairline to Chalk Dust.
- **Hold to approve (signature):** Combat Red fill, white label "Hold to approve 12". Holding for 1.2s sweeps a Pressed Red fill left to right, runs a 4px Belt Gold progress bar along the bottom and fills the clock bezel with a gold conic sweep; release early and it all rewinds in 0.25s. On completion the bezel rings (two gold flashes then fades), the button turns Belt Gold with black text and stays disabled as "Approved". Works with pointer and keyboard; haptic tick on start and a double pulse on ring.
- **Disabled:** 55% opacity, no press.

### Answer options and chips
Options are 52px, 10px, outlined in Bezel Highlight; the picked one turns Lit Paper with black text and the rest dim to 45%. Filter chips and the views/follows toggle are 40px, 10px (7px inside the toggle well), Chalk Dust text on a hairline, active in Lit Paper with black text; counts inside chips are mono.

### Last reels splits
Three columns on a hairline, divided by hairlines: views as a 24px mono figure, "x normal" beneath in mono (gold when a winner, paper when above normal, dust when below), and the post day in 12px dust. Each split opens the reel sheet.

### Schedule rows
Ruled rows: 34px 9:16 thumb, mono time, two-line hook with format and meta beneath, and a state light at the right (8px dot plus label: red for needs yes, paper for scheduled; failed in Warning Ink, winner in Belt Gold). Day headers sit above in 13px/600 dust, today in paper. Below 420px the time column folds into the meta line.

### LED meter
A 24-segment bar, 14px tall, 2px gaps, 2px-rounded segments; unlit segments in Unlit, lit in Lit Paper, Belt Gold for the best row, Chalk Dust for thin samples. A 2px Combat Red normal line marks the 2.6k median (or the follows median) and overshoots the bar by 5px top and bottom. A legend repeats the red tick. Values sit right in mono, best in gold, with the sample size under them.

### Undo bar
Fixed above the bottom nav, max 420px, 14px corners, Housing with a Bezel Highlight edge and the transient lift. Left: a gold seven-segment digit counting 4, 3, 2, 1; middle: "Sending <answer>"; right: a 44px line button "Undo". Escape also undoes; leaving the page sends immediately.

### Sheets
Native dialogs in Housing with a top catch light: bottom sheet on phone (rises 28px over 0.32s), centered from 720px, behind a 72% black blurred backdrop. The reel sheet pairs a 112px cover with the hook and a three-up mono stat row; the week review lists every pending reel by day with thumbs and repeats the hold button in its footer.

### Navigation
Five line icons (22px, 1.6 stroke) with 12px labels in Chalk Dust; current page in paper with a 2px paper tick on the nav edge. The decide badge is a red mono count. From 960px it becomes a horizontal tab rail with an underline tick.

## Do's and Don'ts

### Do:
- **Do** draw hero numerals as seven-segment SVG with unlit segments ghosted at 7% of the lit color.
- **Do** keep color to the three lights: red for a waiting yes or a failure, gold for a win or confirmation, paper for all clear.
- **Do** set every figure in Geist Mono with tabular numerals, and compare views against the 2.6k normal line, not raw numbers alone.
- **Do** guard any action that changes what posts with a 1.2s hold or a 4s timed undo.
- **Do** keep depth carved in: housing edge plus inset face; drop shadows only on undo bar and toast.
- **Do** use the radius family exactly: 18px housing, 12px face, 10px controls.
- **Do** label every time as New York time.

### Don't:
- **Don't** build KPI tile rows, calendar grids or card stacks; report in rows, cells and meters.
- **Don't** introduce any hue beyond black, red, gold and the neutrals; no pastel, no wellness softness.
- **Don't** fill panels with state color; light a lamp, a segment or an outline instead.
- **Don't** set red text under 18px in `red`; use `red-ink`.
- **Don't** set sentences, buttons or comparable numbers in Bebas.
- **Don't** add a light theme; the wall is black.
