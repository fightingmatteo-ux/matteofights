# Cinematic Reel System Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Stand up the full @matteofights cinematic reel production pipeline — folder structure, SFX library, shooting cheat sheets, DaVinci LUT guide, CapCut template guide, and reel checklist — so any reel shot on any of the 3 cameras can be produced with a consistent branded look.

**Architecture:** DaVinci Resolve handles color grading only (raw → graded clips); CapCut Desktop handles all editing (cuts, captions, music, SFX). Content bank fills with pre-graded b-roll over time. CapCut mobile is the fallback for quick phone-only edits.

**Tech Stack:** DaVinci Resolve (free), CapCut Desktop + Mobile, iPhone 13/15 Blackmagic Camera app, Nikon D750, Mixkit/Pixabay (free SFX)

---

## Task 1: Extend content-bank folder structure

**Files:**
- Modify: `content-bank/` (add subdirectories)
- Create: `content-bank/luts/.gitkeep`
- Create: `content-bank/music/.gitkeep`
- Create: `content-bank/real-footage/raw/.gitkeep`
- Create: `content-bank/real-footage/graded/.gitkeep`
- Create: `content-bank/real-footage/b-roll/outdoor/.gitkeep`
- Create: `content-bank/real-footage/b-roll/gym/.gitkeep`
- Create: `content-bank/real-footage/b-roll/conditioning/.gitkeep`
- Create: `content-bank/real-footage/b-roll/misc/.gitkeep`
- Create: `content-bank/sfx/impacts/.gitkeep`
- Create: `content-bank/sfx/whooshes/.gitkeep`
- Create: `content-bank/sfx/drops/.gitkeep`
- Create: `content-bank/sfx/ambience/.gitkeep`

- [ ] **Step 1: Create missing folders**

```powershell
$base = "C:\Users\matte\Documents\Claude\Projects\@matteofights\content-bank"
$dirs = @(
  "luts",
  "music",
  "real-footage\raw",
  "real-footage\graded",
  "real-footage\b-roll\outdoor",
  "real-footage\b-roll\gym",
  "real-footage\b-roll\conditioning",
  "real-footage\b-roll\misc",
  "sfx\impacts",
  "sfx\whooshes",
  "sfx\drops",
  "sfx\ambience"
)
foreach ($d in $dirs) {
  $path = Join-Path $base $d
  New-Item -ItemType Directory -Force -Path $path | Out-Null
  New-Item -ItemType File -Force -Path (Join-Path $path ".gitkeep") | Out-Null
}
Write-Host "Done"
```

Expected: `Done`

- [ ] **Step 2: Verify structure**

```powershell
Get-ChildItem "C:\Users\matte\Documents\Claude\Projects\@matteofights\content-bank" -Recurse -Directory | Select-Object FullName
```

Expected: all 12 new directories listed.

- [ ] **Step 3: Commit**

```bash
cd "C:/Users/matte/Documents/Claude/Projects/@matteofights"
git add content-bank/
git commit -m "chore: extend content-bank folder structure for cinematic pipeline"
```

---

## Task 2: Categorize the existing SFX clips

The 6 clips in `content-bank/sfx/raw/` (sfx_01.wav – sfx_06.wav) were split from `creator sound effects.mp3` and are unnamed. Listen to each one, rename it descriptively, and move it to the right category subfolder.

**Files:**
- Modify: `content-bank/sfx/raw/sfx_01.wav` → rename + move
- Modify: `content-bank/sfx/raw/sfx_02.wav` → rename + move
- (repeat for all 6)

- [ ] **Step 1: Play through each clip and label it**

Open each file in Windows Media Player, VLC, or any audio player. For each clip, decide:
- Is it a hit/thud/punch sound? → `impacts/`
- Is it a swipe/air/whoosh? → `whooshes/`
- Is it a bass drop/low boom? → `drops/`
- Is it background/room noise? → `ambience/`

Write down your mapping before moving anything.

- [ ] **Step 2: Rename and move each clip**

Use this naming pattern: `[descriptor]-[variant].wav`
Examples: `punch-heavy.wav`, `whoosh-fast.wav`, `bass-drop-deep.wav`

```powershell
$sfx = "C:\Users\matte\Documents\Claude\Projects\@matteofights\content-bank\sfx"
# Example — replace names and categories with what you actually heard:
Move-Item "$sfx\raw\sfx_01.wav" "$sfx\whooshes\whoosh-fast.wav"
Move-Item "$sfx\raw\sfx_02.wav" "$sfx\impacts\punch-heavy.wav"
# ... repeat for all 6
```

- [ ] **Step 3: Download 3–5 additional clips to fill gaps**

If any category has zero clips after moving, get free ones:
- Go to **mixkit.co/free-sound-effects** → search category (e.g. "whoosh", "impact hit", "bass drop")
- Download `.wav` files, rename descriptively, drop in the right subfolder

Minimum target: at least 2 clips per category (impacts, whooshes, drops). Ambience is optional.

- [ ] **Step 4: Verify and commit**

```powershell
Get-ChildItem "C:\Users\matte\Documents\Claude\Projects\@matteofights\content-bank\sfx" -Recurse -File | Select-Object Name, DirectoryName
```

Expected: no files left in `sfx/raw/` (or just the original .mp3 and script), named clips distributed across subcategories.

```bash
git add content-bank/sfx/
git commit -m "chore: categorize and rename SFX library clips"
```

---

## Task 3: Camera shooting cheat sheets

One short markdown doc per camera. Pinned to your phone or printed. Every session starts by checking this before you hit record.

**Files:**
- Create: `production/shooting/iphone-13-bm.md`
- Create: `production/shooting/iphone-15-bm.md`
- Create: `production/shooting/nikon-d750.md`

- [ ] **Step 1: Create the shooting directory**

```bash
mkdir -p "C:/Users/matte/Documents/Claude/Projects/@matteofights/production/shooting"
```

- [ ] **Step 2: Write iPhone 13 Blackmagic cheat sheet**

Create `production/shooting/iphone-13-bm.md`:

```markdown
# iPhone 13 — Blackmagic Camera Settings

## Before every shoot
- App: Blackmagic Camera (not native camera)
- Film format: **Blackmagic RAW** (if available) or **ProRes** — NOT H.265 if avoidable
- Color profile: **Film** (log-style, flat)
- Resolution: **1920×1080**
- Frame rate: **24fps** (or 25fps for PAL)
- ISO: Keep under 800 outdoors, under 1600 indoors
- Shutter: **1/48** (180° rule at 24fps)
- White balance: **Lock manually** — tap and hold on skin or neutral grey

## Exposure rule
Expose for skin. If outdoors in direct sun, use ND filter (clip-on) or reduce ISO to floor.
Slightly underexposed is fine — log recovers shadows well. Blown highlights are not recoverable.

## Framing — talking head
- Medium close-up: chest and above
- Subject slightly off-center (rule of thirds)
- Environment visible in background
- Phone held horizontal (landscape) if possible; vertical (portrait) for reel-native

## After shoot
- Transfer via USB cable to laptop → `content-bank/real-footage/raw/`
- Name folder: `YYYYMMDD-[location]` e.g. `20260608-outdoor-gym`
```

- [ ] **Step 3: Write iPhone 15 Blackmagic cheat sheet**

Create `production/shooting/iphone-15-bm.md`:

```markdown
# iPhone 15 Pro — Blackmagic Camera Settings

## Before every shoot
- App: Blackmagic Camera
- Color profile: **Apple Log** (native to iPhone 15 Pro — use this over Film)
- Resolution: **1920×1080** (not 4K — keeps files manageable)
- Frame rate: **24fps**
- ISO: Keep under 800 outdoors, under 3200 indoors (15 Pro handles noise better)
- Shutter: **1/48**
- White balance: Lock manually on skin or neutral surface

## Exposure rule
Same as iPhone 13 — expose for skin, slightly under is fine.
Apple Log has more dynamic range than iPhone 13 — trust it in tough lighting.

## In DaVinci
Input transform: **Apple Log → Rec.709** before applying creative LUT.

## After shoot
Transfer → `content-bank/real-footage/raw/YYYYMMDD-[location]/`
```

- [ ] **Step 4: Write Nikon D750 cheat sheet**

Create `production/shooting/nikon-d750.md`:

```markdown
# Nikon D750 — Video Settings

## Before every shoot
- Picture Control: **Flat** (most dynamic range, works best with LUT)
- Resolution: **1920×1080**
- Frame rate: **24fps** (NTSC: 23.976)
- Shutter: **1/50** (closest to 180° rule at 24fps on Nikon)
- ISO: Keep under 1600 (D750 is clean to 3200 but push it only if needed)
- White balance: **Lock manually** — custom WB or Kelvin value
- Focus mode: **MF** or **AF-S** (continuous AF hunts during video — avoid AF-C)
- Log: Nikon doesn't have log — Flat is the closest equivalent

## Lens suggestions for the look
- 50mm f/1.8 or f/1.4 → shallow depth of field, cinematic
- 35mm f/1.8 → slightly wider, good for environment-context shots

## In DaVinci
No input transform needed — Flat profile is already close to Rec.709.
Minor contrast lift before applying creative LUT.

## After shoot
- Transfer via SD card → laptop
- Drop into `content-bank/real-footage/raw/YYYYMMDD-[location]/`
```

- [ ] **Step 5: Commit**

```bash
git add production/shooting/
git commit -m "docs: add camera shooting cheat sheets for all 3 cameras"
```

---

## Task 4: DaVinci Resolve LUT building guide

Step-by-step guide for building `matteofights-v1.cube` in DaVinci. This is done once — the output LUT is saved to the repo and reused everywhere.

**Files:**
- Create: `production/color/davinci-lut-guide.md`
- Create: `content-bank/luts/matteofights-v1.cube` (produced by following the guide)

- [ ] **Step 1: Create color directory**

```bash
mkdir -p "C:/Users/matte/Documents/Claude/Projects/@matteofights/production/color"
```

- [ ] **Step 2: Write the guide**

Create `production/color/davinci-lut-guide.md`:

```markdown
# Building the matteofights-v1 LUT in DaVinci Resolve

## What this produces
A single `.cube` LUT file that gives every clip — shot on any of the 3 cameras —
the @matteofights look: warm gritty skin tones, punchy contrast, slightly orange-shifted
midtones, deep (not crushed) shadows.

## Setup
1. Open DaVinci Resolve → New Project → name it "matteofights-LUT-build"
2. Project Settings → Color Management: set to **DaVinci YRGB** (not color managed)
3. Timeline: 1920×1080, 24fps

## Import test clips (one per camera)
Import one representative clip from each camera into the Media Pool:
- 1 clip from iPhone 13 (outdoor, good skin tones in frame)
- 1 clip from iPhone 15 (same conditions if possible)
- 1 clip from Nikon D750

## Build the grade — iPhone 13 first (use as the reference)

In the Color page, on the iPhone 13 clip, build this node tree:

### Node 1: Input Transform
- Right-click in Nodes → "Add Node" → "Serial"
- Open "Color Space Transform" effect (Effects → Color Space Transform)
- Input color space: **Blackmagic Design Film Gen 5**
- Input gamma: **Blackmagic Design Film Gen 5**
- Output color space: **Rec.709**
- Output gamma: **Gamma 2.4**

### Node 2: Contrast & Warmth
- Add another serial node
- In Lift/Gamma/Gain wheels:
  - Lift: nudge toward warm (orange/brown) — subtle, maybe +5 in red
  - Gamma: warm midtones, push toward orange-amber
  - Gain: keep highlights clean, slight warm push
- Contrast slider: +0.10 to +0.20 (adds punch without crushing)
- Pivot: 0.45 (keeps skin tones in the lifted zone)

### Node 3: Hue vs Saturation
- Add serial node → open Curves → Hue vs Saturation
- Boost orange range (skin tones) slightly — pull the orange band up ~10–15%
- Slightly pull down the blue/cyan range — makes outdoor sky less distracting
- Don't touch green unless the gym footage looks off

### Node 4: Final Punch
- Add serial node
- Custom Curves: slight S-curve — lift the midtones gently, deepen shadows
- Shadows should be dark but not fully crushed (set black point at ~5–8% not 0)

## Match iPhone 15 and Nikon to this grade

### iPhone 15 clip:
- Node 1: Color Space Transform → Input: **Apple Log**, Output: **Rec.709 / Gamma 2.4**
- Nodes 2–4: copy from iPhone 13 (right-click node → "Append Node Graph")
- Minor per-clip tweaks to match the reference iPhone 13 look

### Nikon D750 clip:
- No color space transform needed — just copy Nodes 2–4 from iPhone 13
- Minor Lift adjustment — Nikon Flat often needs a small contrast boost

## Export the LUT

Once all 3 clips look matched:
1. On the iPhone 13 clip, select Nodes 2–4 (the creative grade, NOT Node 1)
2. Right-click → "Generate 3D LUT (33 point)"
3. Save as: `matteofights-v1.cube`
4. Save location: `content-bank/luts/`

Note: Node 1 (input transform) is NOT baked into the LUT — it stays as a per-camera
node in DaVinci. The LUT only contains the creative grade so it can be applied after
any input transform.

## Apply the LUT to new footage (standard workflow)

For every new batch of clips:
1. Node 1: Camera-appropriate input transform (see above)
2. Node 2: Apply LUT → right-click node → "3D LUT" → select `matteofinci-v1.cube`
3. Node 3 (optional): Per-clip correction if exposure is off

## Import LUT into CapCut mobile (one-time setup)
1. Open CapCut mobile → any project
2. Filter → "Import" → select `matteofights-v1.cube`
3. The LUT now appears in your filter library — name it "MATTEOFIGHTS"
```

- [ ] **Step 3: Follow the guide and export the actual LUT**

Follow `production/color/davinci-lut-guide.md` yourself. This is the hands-on step — you need real footage in DaVinci to build the grade. Use any recent iPhone or Nikon clip you have.

When done, save `matteofights-v1.cube` to `content-bank/luts/`.

- [ ] **Step 4: Verify**

Open a different clip in DaVinci. Apply the LUT. Confirm:
- Skin tones look warm and natural, not orange
- Shadows are dark but not crushed (you can still see detail in dark areas)
- The frame has punch — it doesn't look flat or washed out
- Outdoor and indoor clips treated with this LUT look like they're from the same show

- [ ] **Step 5: Commit**

```bash
git add production/color/ content-bank/luts/
git commit -m "docs: add DaVinci LUT building guide + export matteofights-v1.cube"
```

---

## Task 5: CapCut brand template setup guide

Step-by-step guide for creating the brand template project in CapCut Desktop. Done once — every new reel is duplicated from this template.

**Files:**
- Create: `production/editing/capcut-template-guide.md`

- [ ] **Step 1: Create editing directory**

```bash
mkdir -p "C:/Users/matte/Documents/Claude/Projects/@matteofights/production/editing"
```

- [ ] **Step 2: Write the guide**

Create `production/editing/capcut-template-guide.md`:

```markdown
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
   - Position: just above the text block

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
```

- [ ] **Step 3: Follow the guide and create the actual template in CapCut**

This is the hands-on step. Open CapCut Desktop, follow the guide, and save the template project. You should end up with 3 saved text presets (WORD-POP-WHITE, WORD-POP-RED, TITLE-CARD, LOWER-THIRD) and a template project ready to duplicate.

- [ ] **Step 4: Commit the guide**

```bash
git add production/editing/
git commit -m "docs: add CapCut brand template setup guide"
```

---

## Task 6: Old footage clipping guide + start the b-roll bank

How to process existing training videos from your camera roll into tagged, graded b-roll clips.

**Files:**
- Create: `production/editing/broll-clipping-guide.md`

- [ ] **Step 1: Write the guide**

Create `production/editing/broll-clipping-guide.md`:

```markdown
# B-Roll Clipping Guide — Building the Content Bank

## Goal
Turn your existing camera roll training footage into a library of 5–15 second
tagged clips in `content-bank/real-footage/b-roll/`. More clips = faster future reels.

## Step 1: Transfer raw footage
- Connect iPhone or SD card to laptop
- Copy video files to `content-bank/real-footage/raw/YYYYMMDD-[session]/`
- Leave originals on phone/card until confirmed transferred

## Step 2: Skim and select
Open each video. For every usable section (action, movement, expression, setting):
- Note the timecode range e.g. `0:12 – 0:24`
- Decide the category: outdoor / gym / conditioning / misc
- Note a 2-word descriptor: "shadowbox-heavy", "bag-combo", "push-ups-injured", "outside-run"

Aim to extract 4–8 clips per session video.

## Step 3: Clip in DaVinci (preferred) or CapCut

### In DaVinci (better quality):
1. Import the raw video into a DaVinci project
2. In the Cut page, mark In/Out points for each clip (press I and O)
3. Apply the camera's input transform + `matteofights-v1.cube` LUT
4. Export each clip: File → Export → Individual Clips → H.265 1080p
5. Save to appropriate subfolder in `content-bank/real-footage/b-roll/`

### In CapCut (faster):
1. Import video, drag to timeline
2. Split at in/out points, delete unwanted sections
3. Apply matteofights LUT filter to each clip
4. Export individual clips (or one export, split later)

## Step 4: Name the clip
Pattern: `[category]_[descriptor]_[YYYYMMDD].mp4`
Examples:
- `outdoor_shadowbox-sun_20260608.mp4`
- `gym_bag-combo-heavy_20260601.mp4`
- `conditioning_pushups-floor_20260530.mp4`

## Step 5: File into the right subfolder
- Outdoor training, sunlight, running → `b-roll/outdoor/`
- Bag, pads, mitts, drills at gym → `b-roll/gym/`
- Push-ups, conditioning, injury work → `b-roll/conditioning/`
- Everything else → `b-roll/misc/`

## Target: 30 clips in the bank before your first reel
With 30 tagged clips you have enough variety to cut 4–5 different reels
without repeating footage. Every session you clip adds to it permanently.
```

- [ ] **Step 2: Do a first clipping pass**

Pick 2–3 existing training videos from your camera roll. Follow the guide. Aim to get at least 10 clips into `content-bank/real-footage/b-roll/` before moving on.

- [ ] **Step 3: Commit the guide and any new clips**

```bash
git add production/editing/broll-clipping-guide.md
git add content-bank/real-footage/b-roll/
git commit -m "docs: add b-roll clipping guide + initial b-roll clips"
```

---

## Task 7: Reel production checklist

A quick-reference card — two formats (voiceover reel, talking head reel). Print it or keep it open while editing.

**Files:**
- Create: `production/editing/reel-checklist.md`

- [ ] **Step 1: Write the checklist**

Create `production/editing/reel-checklist.md`:

```markdown
# Reel Production Checklist

## Before you start editing
- [ ] Voiceover recorded? (or talking head clip ready?)
- [ ] B-roll pulled from `content-bank/real-footage/b-roll/` (minimum 5–6 clips)
- [ ] Music track chosen from `content-bank/music/` (or licensed source)
- [ ] SFX clips loaded in CapCut media library
- [ ] Duplicate the `@matteofights TEMPLATE` project → rename to topic

---

## Voiceover + B-Roll Reel

- [ ] Drop VO audio onto Track 2 — this is the backbone, don't touch it
- [ ] Cut b-roll to picture against VO (rough cut first, no text yet)
- [ ] Add music on Track 3 — set to –18dB, cut on beats
- [ ] Add word-pop captions (WORD-POP-WHITE / WORD-POP-RED), synced word by word to VO
- [ ] Add 1–2 title cards at the most impactful lines (TITLE-CARD preset)
- [ ] Drop SFX on each word-pop appearance (whoosh, –14dB) and title card (bass drop, –12dB)
- [ ] Add `READ DESCRIPTION ⬇️` text overlay near the end (plain white text, center)
- [ ] First frame check: does the thumbnail frame have the hook text on screen?
- [ ] Watch full reel once without sound — does the b-roll cutting make visual sense?
- [ ] Watch full reel with sound — does the music hit on cuts? Does VO land clearly?
- [ ] Export: H.264, 1080×1920, high bitrate

---

## Talking Head + B-Roll Reel

- [ ] Grade talking head clip in DaVinci → export to `real-footage/talking-head/`
- [ ] Duplicate `@matteofights TEMPLATE` → rename
- [ ] Drop talking head on Track 1 as base
- [ ] Cut away to b-roll at natural pause points or for visual variety (every 4–8 seconds max)
- [ ] Add lower-third captions (LOWER-THIRD preset) for full sentences when talking
- [ ] Add music at –22dB (under talking head) → bring up slightly on b-roll cuts
- [ ] Add title card at the opening hook moment
- [ ] SFX: subtle whooshes only — don't fight the talking
- [ ] Add `READ DESCRIPTION ⬇️` near end
- [ ] Watch + check same as above
- [ ] Export same settings

---

## After export
- [ ] Caption written? (use CAPTION-ENGINE.md for hook → caption)
- [ ] Thumbnail frame selected (or screengrab from video)
- [ ] Hashtags ready (5 max, niche-specific)
- [ ] Post manually — no scheduling without explicit approval
```

- [ ] **Step 2: Commit**

```bash
git add production/editing/reel-checklist.md
git commit -m "docs: add reel production checklist (voiceover + talking head formats)"
```

---

## Task 8: Update context/brand.md with visual system reference

The brand file should reference the new visual system so future sessions know the cinematic look is defined.

**Files:**
- Modify: `context/brand.md`

- [ ] **Step 1: Read the current brand file**

```bash
cat "C:/Users/matte/Documents/Claude/Projects/@matteofights/context/brand.md"
```

- [ ] **Step 2: Append the visual system section**

Add this section at the end of `context/brand.md`:

```markdown
## Video / Cinematic Look

**Color grade:** Warm-gritty base with punchy contrast. Warm orange-brown skin tones,
deep (not crushed) shadows, slight red push in midtones. Consistent across all cameras.
LUT: `content-bank/luts/matteofights-v1.cube`

**Camera pipeline:** iPhone 13 BM (Blackmagic Film log) + iPhone 15 BM (Apple Log) +
Nikon D750 (Flat profile) → DaVinci grade → CapCut edit.

**Caption style on video:** Three animated styles — Word-Pop (bold, synced to speech),
Title Card (impact moments, red accent word), Lower Third (talking head full sentences).
All animated, nothing static. Colors: white, black, #CC2222 red. Font: Impact / Arial Black.

**Reel formats:** Voiceover + b-roll (primary), Talking head + b-roll (secondary).
Production guides: `production/shooting/`, `production/color/`, `production/editing/`
```

- [ ] **Step 3: Commit**

```bash
git add context/brand.md
git commit -m "docs: add cinematic video look to brand context"
```

---

## Done — system is live

At this point:
- Folder structure is in place and ready to receive footage
- SFX library is categorized and loaded in CapCut
- You have cheat sheets for every camera
- You can build the LUT in DaVinci and use it everywhere
- You have a CapCut template to duplicate for every reel
- You know how to clip old footage into the content bank
- You have a checklist to run through every reel before posting
