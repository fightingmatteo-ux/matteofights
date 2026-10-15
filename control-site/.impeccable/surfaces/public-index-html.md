---
version: 1
slug: "public-index-html"
primary_target: "public/index.html"
related_targets: ["public/style.css","public/app.js"]
---

Scope: the whole control center PWA (Home, Reels, Results, Decide, Activity, reel sheet, week review sheet). Mode: Operate.

Audience and job: Matteo, one-handed on his phone between rounds, sometimes at a laptop. Job: in 5 seconds know what posts next and when, whether a yes is waiting, how the latest reels did against his ~2.6k normal; approve the week and answer questions fast and never by accident; see which format wins on views and on follows per 1k.

Constraints: no build step, vanilla JS, Google Fonts only, data.json field names and api/act payloads unchanged, America/New_York everywhere, brand colors and Bebas pinned, dark only (brand).

## Direction contract

THESIS: The control center is the round clock on the gym wall. You glance at it between rounds: the next post is the countdown, the week is a 14-round program, and approving it is holding START. Refuses the creator-scheduler default of KPI tiles, calendar and cards.

OWN-WORLD: Matte black housing (#0B0B0D) with an inset clock face; seven-segment numerals drawn as live SVG with unlit segments ghosted; phase lights: red = a yes is waiting or a post failed, gold = winner or milestone, paper = all clear. Bebas for headings, Geist for text, Geist Mono for every figure. Segmented LED meters for results, a marked normal line at 2.6k. One radius family: 18px housing, 10px controls.

STORY: Matteo sees the countdown, the program strip and the last three bouts vs normal, knows the state, holds START when a week is waiting, taps answers knowing he has 4 seconds to undo.

FIRST VIEWPORT: Phone 390x844: slim top bar; clock face full width with NEXT POST label, day word, 7-seg time and countdown, phase light; under it the 14-cell program strip; then the waiting block (red light, "12 reels waiting", Review + hold START bar); then "Last bouts" three rows with views and x-normal. Bottom nav fixed.

FORM: Gym round clock, position 1 of my ordered list, seed key 21b09dc2 (taken as IMPECCABLE'S PICK). Signature interaction: hold START fills the clock bezel; answers send after a 4s segment-digit countdown with Undo.

FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance
