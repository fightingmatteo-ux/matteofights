# Listicle factory: one trial reel a day in the old proven format

The 331k / 161k format: training clip, red ALL-CAPS hook, contrast subhook, `READ CAPTION ⬇️`, with the
numbered list living in the caption. No talking, so it renders headless.

## Flow
1. **Hooks.** Claude writes hooks + captions into `production/listicles/hooks.json` (status `ready`).
   It alternates identity (`N SIGNS YOU…`, gets shares) and tactical (`N WAYS TO… WITHOUT…`, gets saves).
   Captions open with the two-line contrast (`Some people… / Some people…`); the "You don't need X" opener is spent.
2. **Clips.** Matteo drops raw training clips (bag, pads, shadowboxing, roadwork) in Drive folder
   `1EkBaa-a9m1lX5KQZnmNXQNj-E8E8hCKk` (top level; subfolders are ignored). It picks the least-used clip and
   never uses the same clip two days running.
3. **Render.** The **Listicle factory** Action runs every Sunday 09:00 UTC (or on demand: count, slot). For each hook:
   `render.py` → 8 s 1080x1920, video to the `media` release + Drive `output/listicles/`, caption + cover in
   `production/listicles/<date>-<id>/`, a queue item `lst-<date>-<id>` with `approved: false`, one per day at the slot.
4. **Yes.** Matteo watches the week in Drive and reads the captions. On his explicit yes:
   `python -P tools/instagram/approve.py lst-… lst-… --note "<when he said yes>"`.
5. **Post.** The **Post queue** Action posts each one as a MANUAL trial reel on its day (cover = 0.5 s frame).
6. **Track.** At 72 h, pull metrics (Buzzfy → Windsor) and log a row in `production/reels/LEDGER.md`.
   Winner metric: follows per 1k views, then shares. Winners get shared to the grid in the app.

## Smoothness (render.py)
- Hook + subhook sit on one black plate from frame 0 (it's the cover). They never animate.
- Clip window chosen by motion: the busiest steady stretch, skipping the first/last second and camera jolts.
- Seamless loop: the end crossfades into the window's own start (seam measured = a normal frame step).
- Slow push-in to 4.5% and back, sub-pixel (perspective filter, cubic), zero speed at the loop point. No jitter.
- READ CAPTION rises and fades in at about 4.6 s, fades out before the loop. Music fades in and out, -14 LUFS.

## Local
```bash
python -P tools/listicle/render.py <clip> <hook id> out.mp4 --cover cover.jpg   # one reel
```
Music: the tracks in `production/reels/five-signs-real-fighter/assets/music/`, rotated. Gym sound stays underneath at 35%.
When the backlog has no `ready` hooks left, the factory stops and says so. Ask Claude for the next batch.
