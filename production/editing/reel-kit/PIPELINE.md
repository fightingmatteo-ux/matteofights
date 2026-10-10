# Reel Kit — talking head → premium reel

The @matteofights editing pipeline. Any Claude session (desktop, web, phone) can run it from this repo.
Goal of every reel: **Stance waitlist sign-ups + followers**. Nothing is ever posted automatically.

Reference builds (copy one as the starting point):
- `production/reels/some-people-train-for-fun/` — THEM vs YOU contrast, fight scorecard, latest pattern
- `production/reels/five-signs-real-fighter/` — numbered listicle, number wipes, checklist badges

Style rules: `production/reels/../../context/brand.md`, `context/voice.md`, and the reference reels above.

## 0. Setup (once per machine / cloud session)

```bash
# needs: ffmpeg/ffprobe, python 3.11+, node 18+
python -m pip install -U faster-whisper yt-dlp numpy
# HyperFrames CLI runs via npx; carve needs core in the reel project:
cd production/reels/<reel> && npm i -D @hyperframes/core@0.8.145
npx hyperframes skills update general-video   # installs the HyperFrames skills
```
Drive upload uses rclone with a remote named `gdrive` (`rclone config create gdrive drive scope=drive`).
In a cloud session, provide the rclone config as a secret (`RCLONE_CONFIG_GDRIVE_TOKEN` etc.) — never commit tokens.

## 1. Get the raw clip

Input folder (public): `19PgWfSa9nwzBcn7JD24EY7QEr12IONbL` · Output folder: `1bHwCLpkK2w9e9BN22dXWgQnn8_CLYpR2`

```bash
bash production/editing/reel-kit/scripts/drive.sh list          # newest files in inputs
bash production/editing/reel-kit/scripts/drive.sh get <fileId> production/reels/<slug>/raw/
```

## 2. Transcribe + cut (scripts/)

```bash
cd production/reels/<slug>
python -P ../../editing/reel-kit/scripts/transcribe.py raw/<clip> work/words.json medium.en
python -P ../../editing/reel-kit/scripts/cutlist.py raw/<clip> work/words.json work/cuts.json \
    --drop "stumbled phrase" --end-after "last phrase before the loop point"
```
Check the printed segments. If a segment starts on breath/noise, nudge it in `work/cuts.json`
(check the envelope around the cut first). Cuts are frame-snapped (30 fps) — keep them that way.

## 3. Prep footage

```bash
bash ../../editing/reel-kit/scripts/prep_footage.sh raw/<clip> assets/talking.mp4
```
Handles iPhone HLG/HDR → SDR tone-map, the house grade (warm, deep shadows, vignette), denoise,
compression and -14 LUFS voice. Do NOT use `content-bank/luts/matteofights-v1.cube` on phone footage
(it was built for log and turns skin blue).

## 4. Design the edit (the creative part — Claude does this per reel)

1. Read the transcript. Find the hook (first 2 s), the structure (listicle / contrast / story), the turn
   to Stance, the CTA and the loop line.
2. Write `build.py` (copy a reference) — all times in SOURCE seconds; `out()` maps to the cut timeline.
   Events dict `E`, b-roll list, emphasis words, SFX list, music drop alignment.
3. Write `work/template.html` — overlays per beat. House layout (1080x1920):
   - top band cards 196–480 px · tracker/scorecard ~500–590 · captions 612–752 (above the eyes)
   - face eyes usually ~900–950; never put captions over eyes/mouth; IG UI covers y > 1600 and x > 940 low
4. B-roll: `python -P ../../editing/reel-kit/scripts/mixkit.py search "<term>" ...` then `get assets/broll <ids>`.
   Prefer vertical clips. Mixkit license = free for social, no attribution.
5. Music: Mixkit hip-hop/trap (e.g. `mk318` Thunder drop @20.17 s, `mk357` Head Bang drop @29.18 s).
   Align the drop to the first "payoff" word of the hook; re-drop on the Stance logo.

Non-negotiables (learned the hard way):
- Frame 0 must already show the hook text (it is the thumbnail). No white flash on frame 0.
- Every entrance uses `enter()` (sets the from-state at t=0) — otherwise elements show early.
- Never mutate the same vars object twice (`Object.assign({}, a)`).
- Words pop in one-by-one (karaoke build); current word red; emphasis words slam + frame punch.
- Pattern interrupt every 2–5 s (b-roll whip, card swap, wipe, punch-in). Retention bar on top.
- Loop: end mid-sentence so the last words lead into the first line.
- Stance logo only as the payoff, never in the hook. CTA keyword: `STANCE` (waitlist) — note voice.md
  standardises `HELP` for coaching DMs; keep them separate.

## 5. Build, check, review

```bash
python -P build.py                       # writes index.html + carves music under the voice
npx hyperframes@0.8.145 check            # must pass; review contrast + layout notes
npx hyperframes@0.8.145 snapshot --at <times> --no-end   # eyeball every beat
```

## 6. Render, master, deliver

```bash
npx hyperframes@0.8.145 render -o renders/render.mp4
bash ../../editing/reel-kit/scripts/master.sh renders/render.mp4 renders/<slug>.mp4   # -14 LUFS, glitch scan
bash ../../editing/reel-kit/scripts/drive.sh put renders/<slug>.mp4
```
Also drop a short `<slug>-notes.txt` (cuts made, b-roll used, anything uncertain) next to it.
Posting/scheduling only after Matteo explicitly approves.
