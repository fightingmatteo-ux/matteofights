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
