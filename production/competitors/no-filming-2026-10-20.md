# Reels we can make without Matteo filming (2026-10-20)

Built from: competitor outliers (`outliers.json`), Buzzfy niche search (reels over 300k views, last 120 days), Matteo's
own numbers (Buzzfy, baseline ~2.7k views / 8 saves / 1.5 shares per reel), and what's already on Drive + the
`media` release (raw talking-head recordings for origin, freeze and Saenchai; 58 usable training clips; fight-night
ringside clips; 3 rendered Saenchai variants).

## What our own numbers say
- Best reel: freeze C "Beginners try to win every exchange. Fighters don't." 4,260 views (1.57x), 6x saves,
  6x shares, 13.8 s watch. Tactical / fix content saves and shares; "Most adults quit by week three" 16x shares.
- Story reels (origin A/B/C, worst decision) watch long but get almost no saves or shares; origin C flopped (190).
- Identity listicles get views (1.3-1.5x) but few saves; tactical listicles get 4x saves.

## The slate, best first
| # | Reel | Source footage | Evidence | Status |
|---|---|---|---|---|
| 1 | Freeze C in the editorial look | freeze raw (Drive) | our best script; tests the new look against its own 4,260 | **rendered** `media/freeze-editorial/freeze-editorial-C.mp4`, needs Matteo's yes |
| 2 | Saenchai A/B/C | already rendered | legend-principle pattern, 17-54x on Lawrence Kenshin | **rendered**, waiting on approval (STATUS) |
| 3 | Freeze B in the editorial look | freeze raw | B did 3,032 | `bash make.sh B` after adding hook B to build.py (~10 min) |
| 4 | "No fight booked" gym-life iykyk | sparring clips (Drive) | imaan.lore 2.3M (relatable gym line over gym footage) | factory `iykyk`, hook to write |
| 5 | Fighter achievements unlocked | fight-night + gym clips | themuaythaiguy 4.7x, comment mechanic | factory listicle; list from founder.md facts |
| 6 | One-line technique "performance" clip | best bag/kick clip (kicking.mov) | superbadvlad 3.2M "First step lethal" | factory `statement` |

## Sounds (sound scout, `production/sounds/proven.json`)
- In this niche the outliers run on **original audio** (voice, gym sound): 21 of 30 sounds behind 66 outliers.
  Only 9 were licensed tracks, each used once, and none is in the library our app can attach.
- So: talking heads keep the voice as the sound (the bed is optional). Factory reels keep royalty-free music.
  The Audio API is live (FB_USER_TOKEN has the scopes); the scout re-runs every Monday and flags any cleared track
  that starts showing up in 2+ outliers, with the `audio_id` ready to attach.
- The API's "trending" list is localised to Thailand (Thai pop), so it is not a niche signal.
