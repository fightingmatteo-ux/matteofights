# Reel Kit — watch → plan → film → edit 3 variants → trial-test → track

The @matteofights reel pipeline. Runs from this repo on the laptop or in a Claude cloud session.
**Goal (since 2026-10-12): followers + engaged, high-quality fighter audience.** Content = combat sport
psychology and fighter mindset. No Stance plug in reels for now. Nothing is ever posted automatically.

Headless daily listicles (old 331k format, no filming): `tools/listicle/README.md`.

**No laptop needed:** the **Reel studio** Action ingests Drive footage (prep + Whisper) and renders variants;
a cloud session does the edit decisions in between. Every reel's heavy media goes on the `media` release as
`<slug>-work.tar` (`tools/video/reel_work.sh push <slug>` after any laptop work). See `tools/video/README.md`
"Edit from your phone".

Reference builds:
- `production/reels/worst-decision/` — latest standard: multi-take assembly, beats/J-cuts, serif one-word
  subtitles, bottom-anchored zoom, templated timings (`work/template.html` + `inject.py`), cover in `thumb/`
- `production/reels/some-people-train-for-fun/` — contrast format (older style: captions ALL CAPS, warm grade)
- `production/reels/five-signs-real-fighter/` — listicle, number wipes

## 0. Setup (once per machine / cloud session)
```bash
# needs ffmpeg/ffprobe, python 3.11+, node 18+
python -m pip install -U faster-whisper yt-dlp numpy pillow
npx hyperframes skills update general-video        # HyperFrames skills (+ hyperframes-audio carve)
cd production/reels/<slug> && npm i                 # carve needs @hyperframes/core in the reel project
```
Secrets (never commit; `secrets/` is gitignored): `secrets/ig_cookies.txt` (Instagram, Netscape format).
Cloud: repo secret `IG_COOKIES` (Actions) holds the same file. Drive: rclone remote `gdrive`.

## 1. Watch references
```bash
bash production/editing/reel-kit/scripts/fetch_ref.sh <instagram-url> <slug>        # laptop
```
Cloud sessions can't reach Instagram: trigger the **Fetch video** Action (`tools/video/README.md`).
Output: `content-bank/references/videos/<slug>/` — read `contact.jpg` + `transcript.txt` first (cheap),
`scenes/` only if the edit rhythm matters. Write the breakdown into `content-bank/references/*.md`.

## 2. Plan: talking points, not a script
Copy `production/reels/_TEMPLATE/` to `production/reels/<yyyy-mm-dd-slug>/`. Fill `TALKING-POINTS.md`:
3 verbatim hook versions (the A/B/C test), one verifiable credibility beat (legend / system), 2–3 points
Matteo talks through freely, one real example, a growth CTA. Start `REEL.md`.

## 3. Footage in
Drive input `19PgWfSa9nwzBcn7JD24EY7QEr12IONbL` · output `1bHwCLpkK2w9e9BN22dXWgQnn8_CLYpR2`
```bash
bash production/editing/reel-kit/scripts/drive.sh list
bash production/editing/reel-kit/scripts/drive.sh get <fileId> media/<slug>/
bash production/editing/reel-kit/scripts/prep_footage.sh media/<slug>/<clip> production/reels/<slug>/assets/raw.mp4
```
`prep_footage.sh` fixes iPhone HDR and full-range ("yuvj") video and keeps colour **neutral**
(full-range read wrong = orange skin; Matteo rejected the warm grade). `GRADE=house` only on request.

## 4. Transcribe + assemble the variants
```bash
cd production/reels/<slug>
python -P ../../editing/reel-kit/scripts/transcribe.py assets/raw.mp4 work/words.json medium.en
# Claude reads the printed transcript, picks the best take per beat -> work/takes.json
python -P ../../editing/reel-kit/scripts/assemble.py work/takes.json     # assets/aroll_<V>.mp4 + work/edl_<V>.json
```
Single clean take instead? `cutlist.py` (tightens gaps) — but keep `--max-gap` ≥ 0.45 so beats survive.

## 5. Design the edit (Claude, per reel) — copy `worst-decision/`
`work/template.html` uses `{{expr}}` timings from the EDL (`S('seg')`, `E('seg')`, `W('seg','WORD')`);
`inject.py` renders it to `index.html`, `build.sh` = inject + carve. Re-timing never drifts.
House layout 1080x1920: top-band cards 170–790 · subtitles centred ~y1440 · IG UI covers y>1600, x>940 low.

**Motion craft (Emil Kowalski's skills, in `.claude/skills/`):** write new animation with `animate`, run
`review-animations` on the template before rendering, name an effect Matteo describes with `animation-vocabulary`,
use `apple-design` for spring and physical feel. They're written for app UI, so translate:
- **Keep:** ease-out (or expo) entrances, never ease-in on anything appearing; no `scale(0)` (start ~0.9 + opacity);
  blur-to-sharp entrances; springs for slams; staggered reveals; only animate transform/opacity/filter.
- **Drop:** the 100-times-a-day frequency gate, UI duration caps (a reveal can hold longer), hover and reduced-motion
  gating. A viewer watches a reel and doesn't click anything; the gate is "does it help the line land".
- **HyperFrames wins on conflicts:** everything runs on the one paused GSAP timeline (seek-safe). No CSS transitions
  or real-time springs, so use GSAP eases that match the skill's curves.

**Non-negotiables (each one learned from Matteo's feedback):**
- Frame 0 already shows the hook (it's the thumbnail). Hook = the first spoken line + on-screen text.
- **Pacing:** never trim on Whisper word ends (clips words). Keep tails; **no speed-up** (any time-stretch sounds robotic on his voice; Matteo heard it at 1.06x); leave 0.3–0.6 s of
  dead space after every reveal line. Build tension (riser → slam), drop the music for the quiet line.
- **No hard cut straight to the next line:** b-roll enters 0.12 s early (J-cut) with a zoom-blur;
  flashes only on big hits. Pattern interrupt every 2–4 s.
- **Face:** handheld footage, chin near the bottom → zoom ≤1.08x, `transform-origin: 50% 100%`.
  Whole face always in frame.
- **Subtitles:** one word at a time, Tinos Bold (Times-style serif), sentence case, white + key words
  red `#E8112D`, 9 px black outline. Cinematic: rise from blur (expo ease), red words slam bigger,
  each word clears before the next lands. No letter-spacing animation (lint rejects it).
- **Voice:** first person, a real detail. Never "they vs you" lecturing (rejected as cringe).
- **Colour:** neutral; check skin vs source after any re-encode.
- **Voice:** never denoise/compress phone audio (afftdn = watery, robotic voice). takes.json `audio_src` = the
  original recording; assemble.py only low-cuts and sets -14 LUFS once (speed stays 1.0).
- Every entrance sets its from-state at t=0; never tween the same property from two timelines.
- Loop: film close + bridge + hook as ONE continuous take per variant; start the video at the hook inside
  that take and end it just before the hook. Replay = one unbroken sentence, no visual jump.
- CTA: follow + one comment question, or a comment keyword with a REAL deliverable (Karst pattern:
  322 comments on 501 likes). Stance only when Matteo asks for it again.

## 6. Build, check, review, render
```bash
bash build.sh && npx hyperframes check                      # must pass
npx hyperframes snapshot --at <beat times> --no-end         # read contact sheets, not every frame
npx hyperframes render -q delivery -o ../../../media/<slug>/<slug>-<V>.mp4
ffmpeg -i <render> -c:v libx264 -crf 23 -c:a copy -movflags +faststart <render>-phone.mp4   # to send
```
Cover: copy `worst-decision/thumb/` (HyperFrames snapshot at 0.5 s). Keep text inside the grid crop
(y 285–1635). Real photos beat stills from the talking head.

## 7. Deliver + trial-test
- Upload the 3 renders + covers to Drive output. Laptop: `rclone copyto <file> gdrive:<name> --drive-root-folder-id
  1bHwCLpkK2w9e9BN22dXWgQnn8_CLYpR2`. Cloud: `bash tools/video/media.sh push <file>` then run the **Upload to Drive**
  Action (`gh workflow run drive-upload.yml -f asset=<file>`; secret `RCLONE_CONF`).
- Matteo posts all 3 as **Instagram trial reels** himself, the SAME day, 2–3 h apart (spam-safe, same-day conditions). Trial reels
  only reach non-followers, so spacing protects nobody and adds day-to-day noise. Auto-share OFF.
  (The Windsor `instagram` connector can't post trial reels.)
- Or Claude posts them through our own Meta app: `tools/instagram/ig.py trial` (setup + usage in
  `tools/instagram/README.md`). Flow: preview → Matteo's explicit yes → `--confirm`. Never skip the yes.
  Remote: add the variants to `production/schedule/queue.json` (renders on the media release), set
  `approved: true` after the yes; the **Post queue** Action posts them 2.5 h+ apart.
- Log every variant in the reel's `REEL.md` + `production/reels/LEDGER.md`.

## 8. Track
Pull per-media metrics via **Buzzfy** (MCP; skills `reel-checkup`, `instagram-audit`) at 24 h / 72 h / 7 d;
fallback Windsor (`instagram`, account `17841465098113052`). Before posting, run Buzzfy `reel-checkup` on the hook.
Compare at 72 h. Winner metric: follows per 1k views, then shares, then avg watch time. Winner → shared
to the grid (and pinned if it's a profile reel). Write the one-line learning into
`LEDGER.md` "Patterns so far". If trial reels don't show in the API, ask Matteo for the insights screenshot.
