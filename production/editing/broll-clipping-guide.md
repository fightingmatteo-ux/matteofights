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
