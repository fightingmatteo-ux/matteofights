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
2. Node 2: Apply LUT → right-click node → "3D LUT" → select `matteofights-v1.cube`
3. Node 3 (optional): Per-clip correction if exposure is off

## Import LUT into CapCut mobile (one-time setup)
1. Open CapCut mobile → any project
2. Filter → "Import" → select `matteofights-v1.cube`
3. The LUT now appears in your filter library — name it "MATTEOFIGHTS"
