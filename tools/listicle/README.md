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
Music: `production/listicles/music/*.mp3` (with `tracks.json`: title, artist, vibe, license, source) once it has
tracks, else the original 4 in `production/reels/five-signs-real-fighter/assets/music/`; rotated. Each reel uses the
track's **strongest 8 s (its drop), cut on a beat** (`render.music_start`), never the intro. Gym sound underneath at
18% (high-passed), loudness -15 LUFS. Only royalty-free tracks whose license allows social posts go in the folder.

Moments (since 2026-10-16): motion alone can't tell skilled boxing from messing around, so for every clip the
Saturday sheets run also writes `production/listicles/moment-sheets/<id>.jpg` (rows A-H = the busiest
non-overlapping 8 s stretches, 6 frames each, plus a body-pose check from `technique.py` that vetoes the obvious
failures in red; start seconds in `moment-sheets/index.json`, pose numbers in `moment-sheets/pose.json`). The daily Claude check
grades them against the rubric in `context/boxing-technique.md` into `production/listicles/moments.json` `{clip_id: {good: [s...], bad: [s...]}}` and every
render starts at the clip's first good moment (`render.graded_start`); ungraded clips use the best moment that passed the pose check,
then the busiest stretch.
When the backlog has no `ready` hooks left, the factory stops and says so. Ask Claude for the next batch.

## Audio (since 2026-10-20): his proven sounds, rotated
Matteo's call: listicles do better on the sounds his best ones used (`production/sounds/own_proven.json`, sound scout
`own` mode): Echo Sax End on 5 of his top 15 (incl. the 331k), INSONAMIA on 2, then Ethereal, Not You Too, Memory
Reboot, 180db_, Fever once each. Only Echo Sax End is in the API library from its own artist; INSONAMIA and Memory
Reboot are pinned fan uploads (`id:<audio_id> name`, checked at post time, gone = post by hand); the rest aren't
attachable. Rotation (workflow default): Echo, INSONAMIA, Echo, Memory Reboot. The factory renders them without music and the queue item
carries `app_audio: Echo Sax End - Caleb Arredondo`; at post time `audio.py resolve` finds it (music first, then the
artist's own original-sound upload @caleb.arredondo, id 530317382955170) and the Audio API attaches it. Workflow input
`audio` changes the sound; `none` = royalty-free music in the file. Unproven: trial reel + attached audio in one call
is undocumented by Meta; if it is refused the item fails with Meta's message and nothing posts (then re-render with `none`).

## Audio + posting (since 2026-10-15)
The API can't attach Instagram library sounds, so trial reels carry royalty-free music in the file and the
**Post queue posts them automatically** (after Matteo's one weekly yes via approve.py). Trending sounds are used
where they matter: when a trial reel hits ~2x the account's normal views at 72 h, Claude flags it and suggests a
fitting trending sound; Matteo re-posts that winner to the grid from the app with the sound (1-2 a week).
`--audio "<sound>"` still exists for the manual route (renders without music, Post queue skips the item).
Two factory runs every Sunday (09:00 and 09:40 UTC) fill the 18:30 and 21:30 New York slots: US evening, 3-7am in India (reach was skewing Indian at the old 17:00 UTC slot = 22:30 IST). 14 reels/week.

## Look (since 2026-10-15, copied from the 398k / 162k reels)
Instagram's native text style: red bold serif hook, each line on its own rounded black highlight, centred in
the upper third. Hook only on screen (subhook opens the caption). Footage bright and neutral, not darkened.
`READ DESCRIPTION ⬇️` on a rounded black pill in the last ~3 s.

## Formats (field `format` in hooks.json, copied to the queue for the ledger)
- `listicle`: N SIGNS / N WAYS hook, numbered list in the caption (the 398k / 162k format).
- `statement`: one bold line on screen (THERE'S NO SUCH THING AS AN EX-FIGHTER, 13k), short list in the caption.
- `builder`: fighter-who-builds lane (approved 2026-10-15), ~2/week, no Stance plug.
- `iykyk`: insider gym moment, one-line caption + tag-a-friend. No READ DESCRIPTION pill.
Weekly mix while testing: 4 listicles, 2 statements, 1 iykyk. Second daily slot: run the factory with `--slot 20:00`.

## Footage agent (footage_agent.py, needs repo secret ANTHROPIC_API_KEY)
Every run, before rendering:
1. **Catalog**: any Drive clip it hasn't seen gets 6 frames looked at by Claude (activity, setting, is the fighter
   in frame, face visible, rotation needed, quality, energy, usable or not). Cached in `production/listicles/clips.json`,
   so only new clips cost anything. Clips removed from Drive stop being candidates.
2. **Match**: for each hook, Claude ranks the best-fitting clips out of the whole catalog (fit to the words first,
   then framing/quality, then least used). Clips used within 2 days of the reel are skipped.
3. **Review**: after each render Claude looks at the cover + 4 frames of the finished reel. Fails on: fighter not
   clearly in the cover, text over face/upper body, sideways footage, floor/empty/phone-handling frames, poor fit.
   A fail renders the next candidate (max 3); if none pass, the best-scored one is kept. Verdicts land in the queue item (`review`).
`--rerender` reviews the current clip first and only swaps it on a fail; `--rerender --rematch` re-picks from scratch.
Model: Claude Opus 5.5 (structured JSON output, fallbacks on). Cost: about a few cents per clip catalogued, ~10 cents per reel.

## No API key: Claude works from the scheduled session (Matteo's account)
The footage agent's API path is off without `ANTHROPIC_API_KEY`. Instead:
- **Saturday 07:00 UTC**: the factory makes a 6-frame contact sheet for every new Drive clip
  (`production/listicles/clip-sheets/<drive id>.jpg`, live list in `index.json`).
- **Saturday daily check**: Claude looks at new sheets and writes `production/listicles/clips.json` (same fields as
  footage_agent.CLIP_SCHEMA: activity, setting, fighter_visible, rotate_fix, quality, usable...), writes next week's
  14 hooks, and sets `clip_id` on each hook to the best-fitting clip from the whole folder.
- **Sunday**: the factory renders each hook on its `clip_id` (rotation from clips.json) and saves a `review.jpg` next to
  each cover. Claude's Sunday check reviews them, swaps any bad clip (`clip` in queue.json + `--rerender --only`), then
  sends Matteo the week for his yes.

## Lifestyle lane (since 2026-10-15)
Not only training clips: food, recovery, routine, travel clips in the folder can carry adjacent fighter topics
(nutrition, sleep, recovery, discipline outside the gym). Rule: the hook still speaks to fighters
("WHAT I EAT BEFORE A FIGHT", "5 RECOVERY HABITS..."), never generic lifestyle. About 2-3 of 14 per week.
