# Reel Kit — watch → plan → film → edit 3 variants → trial-test → track

The @matteofights reel pipeline. Runs from this repo on the laptop or in a Claude cloud session.
**Goal (since 2026-10-12): followers + engaged, high-quality fighter audience.** Content = combat sport
psychology and fighter mindset. No Stance plug in reels for now. Nothing is ever posted automatically.

Headless daily listicles (old 331k format, no filming): `tools/listicle/README.md`.

Reference builds:
- `production/reels/2026-10-20-freeze-editorial/` — **current standard (editorial look)**: phrase captions, white
  quote cards, auto caption SFX, all from `reel-kit/editorial/`
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

## 5. Design the edit (Claude, per reel) — copy `2026-10-20-freeze-editorial/` (older motion-graphics: `worst-decision/`)
`work/template.html` uses `{{expr}}` timings from the EDL (`S('seg')`, `E('seg')`, `W('seg','WORD')`);
`inject.py` renders it to `index.html`, `build.sh` = inject + carve. Re-timing never drifts.
House layout 1080x1920: top-band cards 170–790 · subtitles centred ~y1440 · IG UI covers y>1600, x>940 low.

**Non-negotiables (each one learned from Matteo's feedback):**
- Frame 0 already shows the hook (it's the thumbnail). Hook = the first spoken line + on-screen text.
- **Pacing:** never trim on Whisper word ends (clips words). Keep tails; **no speed-up** (any time-stretch sounds robotic on his voice; Matteo heard it at 1.06x); leave 0.3–0.6 s of
  dead space after every reveal line. Build tension (riser → slam), drop the music for the quiet line.
- **No hard cut straight to the next line:** b-roll enters 0.12 s early (J-cut) with a zoom-blur;
  flashes only on big hits. Pattern interrupt every 2–4 s.
- **Face:** handheld footage, chin near the bottom → zoom ≤1.08x, `transform-origin: 50% 100%`.
  Whole face always in frame.
- **Look = editorial (Matteo 2026-10-20, from the kaixerb reference; replaces the Tinos one-word subtitles).**
  Use `reel-kit/editorial/` (README there; worked example `production/reels/2026-10-20-freeze-editorial/`):
  - **Captions:** short phrases (1–4 words) that build word by word in Geist, lowercase, white with a soft
    shadow (no outline). Max ONE keyword per phrase: its own line, ~170 px, red `#E8112D`. A keyword every
    ~3–6 s, not every line. Put captions in clean space (ceiling/background), never across the eyes or mouth.
  - **White quote cards:** the 2–3 lines that carry the reel cut hard to a white page: black type builds on
    the voice, the keyword huge in red (auto-fit), the music bed lifts ~12 dB under it so the line lands, then a
    hard cut back to the face. 1.2–3 s each. One card may "slam" (over-scaled keyword + sub hit).
  - **SFX:** quiet tick ~50 ms before each phrase, tonal "key" under keywords, whoom into each card, sub on
    the slam/dip. All far under the voice. Generated by `plan.py`, never placed by hand.
  - **Hook word behind the head** on frame 0 (`editorial/cutout.py`, works in the cloud): the thumbnail.
  - **Calm, premium motion:** blur-in, expo ease, no bounce, no emoji, no boxes. No letter-spacing animation
    (lint rejects it).
- **Pacing (measured on the reference):** speech ~3.5–4.3 words/s with breaths kept on the important lines;
  shots average ~3.5 s, but the screen changes every ~0.5 s (a new phrase, a word landing, a card). Camera is
  never static: slow push on each face stretch, a different framing after every card.
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
Editorial reels: after the render, `python3 -I ../../editing/reel-kit/editorial/check_render.py <render> assets/media/aroll_<V>.mp4`
(catches black / jumpy first frames; on FAIL render again).
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
