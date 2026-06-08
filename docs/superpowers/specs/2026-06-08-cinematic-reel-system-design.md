# @matteofights Cinematic Reel System — Design Spec

_2026-06-08_

## Goal

A repeatable, branded production pipeline for making cinematic Instagram reels — voiceover + b-roll and talking head + b-roll formats — using iPhone 13 BM, iPhone 15 BM, and Nikon D750. Everything shot across all three cameras converges to the same @matteofights look: warm gritty skin tones, punchy high-contrast shadows, red/black brand palette. DaVinci Resolve handles color, CapCut Desktop handles editing. Content bank fills up with pre-graded clips that make future reels faster every week.

---

## 1. Shooting Protocol

All footage must be shot in a flat/log profile so the LUT has consistent material to work with.

| Camera | App | Profile | Resolution | Frame Rate |
|---|---|---|---|---|
| iPhone 13 | Blackmagic Camera | BM Log (or Apple Log if unavailable) | 1080p | 24fps |
| iPhone 15 | Blackmagic Camera | Apple Log | 1080p | 24fps |
| Nikon D750 | Native | Flat / Neutral picture profile | 1080p | 24fps |

**Why 24fps:** Cinematic feel, smaller files, easier on the laptop. 30fps acceptable if needed for slow-motion later.

**Exposure rule:** Expose for skin — especially outdoors. Slightly underexposed is easier to recover in DaVinci than blown highlights.

**Talking head framing:** Medium close-up (chest and above), subject slightly off-center, environment visible in background. Consistent across all cameras.

---

## 2. The LUT Strategy

One master look — warm skin tones (from the warm/gritty B direction), punchy high contrast with lifted shadows, slight red-orange push in the midtones. This bridges outdoor sunlit training and dark indoor gym footage.

**Three input variants:** Because each camera records log differently, DaVinci uses a camera-specific input transform before the creative LUT:
- iPhone 13 BM: BMD Film Gen 5 → Creative LUT
- iPhone 15 BM: Apple Log → Creative LUT  
- Nikon D750: Flat/Neutral (minor lift) → Creative LUT

**LUT file:** Exported as a `.cube` file, saved to `content-bank/luts/matteofights-v1.cube`. This same file is imported into CapCut mobile for the phone fallback workflow.

**Per-clip tweaks allowed:** After applying the LUT in DaVinci, minor per-clip exposure and white balance corrections are fine — outdoors vs indoors will need different starting points. The LUT defines the look; tweaks make it consistent.

---

## 3. DaVinci Resolve Workflow

DaVinci's only job is color. Do not edit, cut, or arrange clips here.

1. Import raw clips from `content-bank/raw/`
2. Apply camera-appropriate input transform + creative LUT
3. Minor per-clip corrections (exposure, WB)
4. Export to `content-bank/graded/` as H.265 1080p (keeps file sizes manageable on the laptop)
5. Move raw originals to `content-bank/raw/archive/` once graded

**DaVinci project settings:** Timeline at 1080×1920 (9:16 vertical). Color science: DaVinci YRGB Color Managed.

**Old footage:** Go through existing camera roll and training videos. Clip usable b-roll segments (5–15 seconds each) in DaVinci or CapCut. Grade them through the same LUT. Store in `content-bank/b-roll/` tagged by type.

---

## 4. Content Bank Structure

```
content-bank/
  raw/
    archive/          ← originals after grading
  graded/             ← DaVinci exports, ready to cut
  b-roll/
    outdoor/          ← sunlit training, street, running
    gym/              ← bag work, pad work, drills
    conditioning/     ← push-ups, injury training, mobility
    misc/             ← anything that doesn't fit above
  talking-head/       ← graded talking head clips
  luts/
    matteofights-v1.cube
  sfx/
    impacts/          ← punch hits, thuds
    whooshes/         ← text transition swooshes
    drops/            ← bass drops for title card moments
    ambience/         ← gym background noise
  music/              ← licensed tracks, named by vibe/tempo
```

Clip naming convention: `[type]_[descriptor]_[YYYYMMDD]` — e.g. `broll_outdoor-shadowbox_20260608.mp4`

---

## 5. CapCut Editing Workflow

CapCut Desktop is where the reel actually gets made. Every new reel starts from the brand template project.

**Brand template contains:**
- Canvas: 1080×1920, 24fps
- Brand colors saved: `#CC2222` (red), `#FFFFFF` (white), `#000000` (black)
- 3 preset caption styles (see Section 6)
- Placeholder tracks: video, VO/audio, music, SFX

**Editing sequence for a voiceover reel:**
1. Record or import VO audio first — this is the backbone
2. Cut b-roll from the content bank to picture against the VO
3. Sync music (underneath VO, cut on beats)
4. Add word-pop captions synced to VO words
5. Place title cards at impact moments
6. Drop SFX on cuts and text appearances
7. Export: H.264 1080×1920, high bitrate

**For talking head reels:** Same sequence but talking head clip comes first. B-roll cuts away at natural pause points. Caption style switches to animated lower-third for talking head segments.

---

## 6. Caption System (Animated, Never Static)

Three styles — all animated, nothing sits still:

### Word-Pop (primary — voiceover reels)
- Words burst on screen one at a time, synced to speech
- Key words: white box with black text OR red box with white text (alternate for emphasis)
- Font: heavy black/black weight sans-serif (Impact or Arial Black), ALL CAPS
- Appears at ~60% height on screen (not bottom, not top)
- Animation: fast scale-in + slight bounce, ~4–6 frames

### Title Card (impact moments)
- Full-width text, left-aligned
- Red thin rule above (2px, 30px wide)
- ALL CAPS, letter-spaced, large
- Key word on second line in red
- `@matteofights` in small grey below
- Animation: slide in from left, hold, fade out on cut
- Use sparingly — 1–3 per reel maximum

### Animated Lower Third (talking head segments)
- Single line at bottom third of frame
- White text, slightly transparent dark pill background
- Font: lighter weight than word-pop, sentence case
- Animation: slide up from below, fade out after ~3 seconds
- Used to caption full sentences during talking head, not word-by-word

---

## 7. SFX Library

Sources: Mixkit (free, no attribution) and Pixabay (free). Download ~25–30 clips total and organize into `content-bank/sfx/`.

| Category | Use | Examples to find |
|---|---|---|
| Impacts | Punch/hit b-roll cuts, hard text pop-in | "punch hit", "thud", "whomp" |
| Whooshes | Word-pop text animations, quick cuts | "whoosh", "swipe", "air swoosh" |
| Bass drops | Title card moments, section transitions | "bass drop", "sub boom", "low impact" |
| Ambience | Optional bed under music for gym footage | "gym ambience", "boxing gym", "crowd murmur" |

SFX should be mixed low (–18 to –12dB) under music, not on top of it.

---

## 8. Mobile Fallback (CapCut Mobile)

For quick reels when the laptop isn't available:

1. Import `matteofights-v1.cube` into CapCut mobile's filter library
2. Apply to all clips at the start of every project
3. Use CapCut mobile's built-in text templates — match word-pop style as closely as possible
4. Keep to simple voiceover + b-roll only (no complex title cards on mobile)
5. Transfer to laptop later if major edits needed

Mobile edits are acceptable for posting but should not replace the full pipeline — they're a "ship it quickly" valve, not the default.

---

## Success Criteria

- Any reel shot on any of the 3 cameras looks like it came from the same brand
- The content bank has enough pre-graded b-roll that a reel can be assembled in 1–2 hours
- Caption style is consistent enough that a viewer recognizes the account from the text alone before seeing the face or hearing the voice
- Old training footage is clipped, graded, and searchable in the content bank
