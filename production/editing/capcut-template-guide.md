# CapCut Brand Template Setup Guide

## One-time setup — do this once, then duplicate for every reel

### New project settings
1. Open CapCut Desktop → New Project
2. Ratio: **9:16** (vertical / Reels)
3. Resolution: **1080×1920**
4. Frame rate: **24fps**
5. Name it: `@matteofights TEMPLATE`

### Brand colors (save these in CapCut)
Anywhere CapCut lets you pick a custom color, save these:
- **Brand Red:** `#CC2222`
- **White:** `#FFFFFF`
- **Black:** `#000000`

---

## Text Preset 1: Word-Pop (voiceover reels)

Used for every word that appears synced to speech.

1. Add Text → choose a text clip
2. Font: **Impact** (or Arial Black if Impact not available)
3. Size: ~80–100 (fills about 1/3 of screen width per word)
4. Color: **White** (`#FFFFFF`)
5. ALL CAPS: on
6. Letter spacing: 2–4px
7. Background: solid **Black** (`#000000`), padding 8px horizontal / 4px vertical
8. Position: center, at ~55–60% height (not bottom, not top)
9. Animation IN: Scale → Fast (2–4 frames), slight overshoot if available
10. Animation OUT: Fade → 2 frames
11. Save as text preset: "WORD-POP-WHITE"

For emphasis words (key points): repeat with Background = **Brand Red** (`#CC2222`), Text = White.
Save as: "WORD-POP-RED"

---

## Text Preset 2: Title Card (impact moments)

Used 1–3 times per reel at the most important moments.

1. Add Text → 2 separate text elements stacked:
   **Line 1** (top label):
   - Font: Arial Black / Impact
   - Size: ~50
   - Color: White
   - ALL CAPS, letter spacing 6–8px
   - No background

   **Line 2** (key word):
   - Font: Impact
   - Size: ~90–110
   - Color: **Brand Red** (`#CC2222`)
   - ALL CAPS

2. Add a thin red line above Line 1:
   - Insert a shape → rectangle
   - Width: ~80px, Height: 3px
   - Fill: Brand Red

3. Optional: add `@matteofights` in tiny grey below (font size ~28, color `#888888`)

4. Animation IN: Slide from left (4–6 frames) — whole group
5. Animation OUT: Cut (instant, on the beat)

6. Group all elements → save as preset: "TITLE-CARD"

---

## Text Preset 3: Animated Lower Third (talking head)

Used for full sentences during talking head segments — appears once per thought, not word-by-word.

1. Add Text:
   - Font: Arial or Helvetica (lighter weight than the others)
   - Size: ~52
   - Color: White
   - Sentence case (not ALL CAPS)
   - Background: semi-transparent black (`#000000`, opacity 60%), rounded corners
   - Padding: 10px horizontal / 6px vertical

2. Position: bottom 25% of frame, centered

3. Animation IN: Slide up from below (6–8 frames)
4. Animation OUT: Fade (6 frames)
5. Duration: leave on screen 2.5–3 seconds

6. Save as preset: "LOWER-THIRD"

---

## SFX track setup

In the template project, add these tracks in the timeline:
- Track 1: Video (b-roll / talking head)
- Track 2: Voiceover / audio
- Track 3: Music (set volume to –18dB default — under VO)
- Track 4: SFX (set volume to –14 to –12dB)

Import your SFX folder into CapCut's media library:
Add → Local → select `content-bank/sfx/` folder

---

## Saving the template

Once all presets are configured:
1. Close the project (don't delete it)
2. Every new reel: duplicate the template project → rename to the reel topic

---

## Mobile LUT setup (one-time)

1. AirDrop or cable transfer `content-bank/luts/matteofights-v1.cube` to your iPhone
2. Open CapCut Mobile → any project → Filters → Import
3. Select the `.cube` file
4. It now appears in your filter library as a reusable filter
5. Name it "MATTEOFIGHTS" when prompted
