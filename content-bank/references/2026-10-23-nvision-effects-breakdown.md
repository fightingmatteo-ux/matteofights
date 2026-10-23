# nvision.media effects edit (via @willrvail breakdown), 2026-10-23

Source: https://www.instagram.com/reel/Deb-VcJRpxp/ (Will Vail reviewing an @nvision.media music-video edit,
43k likes, 454 comments). Analysis: `content-bank/references/videos/shotcraft-Deb-VcJRpxp/` (frames, transcript,
`fx/` = crops of the inset edit at 8-12 fps). The edit itself is 16:9, Yosemite, 24 fps, teal/amber grade.
Note: Will freezes the inset while he talks, so the holds in the frames are his pauses, not the edit's pacing.
The real edit changes effect every 1-3 s.

How to film each one for us: `production/shooting/effects-shots.md`.

## The 11 effects, what they actually are

| # | Effect (his name) | What happens on screen | Made at the camera or in the edit |
|---|---|---|---|
| 1 | Masking (hook) | On black: a white matte of the subject's body, then head, then just the sunglasses, one per beat (~3 frames each), then the full colour shot hits. `fx/01-masking-hook.jpg` | Edit (subject matte). Camera: one clean, still-ish shot with a signature prop |
| 2 | Wipe the frame | Hand reaches into the lens, fills the frame with blur, next shot opens out of that blur to a wide hero shot | Camera. Both shots must be planned as a pair |
| 3 | Layer effect | 4-6 delayed copies of the subject stacked (echo trail) on a locked shot, then a blurred smear into the next scene. `fx/03-layer-echo-smear.jpg` | Edit, but needs a tripod and slow movement |
| 4 | Sound wave | The echo copies pulse with the bass (offset grows on each kick) | Edit only, on top of #3 |
| 5 | Clone | Same locked frame, 3 takes of the same person composited side by side, each moving differently. `fx/05-clone-flash.jpg` | Camera: tripod, locked exposure/focus/WB, an empty plate |
| 6 | Flash | One-frame white silhouette of a subject (or full white frame) on a hit | Edit only (matte from #5 / any shot) |
| 7 | Silhouette overlay | Subject's head on a white page, the silhouette filled with other clips that change every ~0.3 s | Camera: backlit profile against bright sky, held 3 s. Edit: matte + fill |
| 8 | Lyric pop | One serif word in gold ("CRAZY") pops on the lyric, over a wide | Edit only |
| 9 | Slow-mo | A 4-6 s slow waterfall: the breather between effect runs | Camera: 60/120 fps |
| 10 | Handheld | Low, handheld selfie-style shots, sky behind, for movement | Camera |
| 11 | Inverted shot | Black and white, crushed, subject as black shape against a white sky; also a white cross-shaped mask wipe ("Jesus" moment) | Camera (backlit) + edit (B&W, threshold, shape mask) |
| + | Closer | Wide walking shot, logo animates in over the landscape | Camera (wide, slow walk across frame) + logo |

## Why it feels premium (the transferable rules)
1. **Effects only happen on the beat.** Every flash, matte and copy lands on a kick or snare. No effect is decorative.
2. **Effect runs, then a breather.** 3-5 effects in a row, then one clean or slow shot (the waterfall), then go again.
3. **Every effect reuses one shot.** Masking, flash, clone and silhouette all come from the same subject matte. Few
   shots, many looks: the cost is in planning, not in filming hours.
4. **One grade, one prop, one location.** Teal/amber everywhere, the white sunglasses come back, so 30 tricks still
   read as one film.
5. **Hook is abstract first, real second.** Shapes on black make you wait for the reveal (the 331k "identity" hook
   works the same way: tell them what they are before you show it).

## Fit with @matteofights (what to take, what to leave)
- Take: masking hook, wipe the frame, clone, flash, silhouette overlay, handheld, inverted. All work with talking
  points and fight b-roll, all run off the `cutout.py` matte (Robust Video Matting) we already use.
- Careful: slow-mo. Matteo cut it from the Saenchai re-cut (10-20). Only as silent b-roll breather, never on voice.
- Leave: lyric pop in gold serif. Our editorial captions (Geist, red keyword) already do this job.
- Cap: 2-4 effects per talking-head reel, all in the first 3 s and on keywords. More reads as an ad (brand.md).
  A full effects run is for a brand film / fight-week hype reel, not the daily reel.
