# Reference: caption style + caption sound effects (@kaixerb)

- **Link:** https://www.instagram.com/reel/DYnDXzwSGXS/
- **Saved:** 2026-10-20, by Matteo. He liked the **sound effects on the captions** and how **clean the captions** are.
- **Status:** WATCHED. Frames, transcript and cuts are in `references/videos/kaixerb-caption-sfx/`. The mp4 is on the
  `media` release (`kaixerb-caption-sfx.mp4`).
- **What it is:** an 18-year-old editor's day-1 portfolio piece. A 9 s intro to camera, then a re-edited podcast clip
  (Rick Rubin), then a 4 s outro. 41.5 s long, 11 hard cuts, average shot 3.5 s. 35k likes, 1,026 comments (the caption
  asks for feedback on "pacing, captions, or sounds"). We're studying the **edit craft**, not the topic.

## The captions: why they look clean

1. **One short phrase at a time, never a block.** Usually 1–4 words ("I'm 18", "a clip", "of a podcast"). The previous
   phrase is gone before the next lands. The screen is never busy.
2. **Two sizes only.** Small lead-in words in a tight, heavy sans (Inter/SF-style, sentence case, white) plus **one big
   keyword** in the same family, much larger and tightly tracked: `FIRST DAY`, `CLIENT`, `interesting`, `your own`,
   `predict`, `telling`. The size jump does the emphasis. No outline boxes and no emoji.
3. **Colour only on the keyword, and it follows the meaning.** `CLIENT` is neon green (money/goal). `interesting` is
   pink-red. `predict` / `telling` are red. Everything else stays white. About one coloured word every 5–8 s.
4. **The keyword goes behind the subject.** The opening `HEY` is huge and sits *behind* his head (subject cut-out /
   rotoscope), and `FIRST DAY` overlaps the mic. That depth is a big part of why it looks expensive.
5. **Entrances are soft.** Words fade or blur in, often a few letters at a time (frames show "my name's K..."
   half-revealed), with a slight drift. No bouncy scale-pop on the small words.
6. **Typography cutaways.** On the punch lines the video cuts to a **plain white card** with just the text in black
   plus one red word (15 s `do what's interesting`, 19–21 s `we can never predict the outcome`, 33–36 s
   `why is it telling you this?`). At 21 s `predict` is scaled past the edges of the frame for a slam.
   Then 1 s of pure black (37 s) before the outro.
7. **Placement:** lower-middle on the speaker (chest height), clear of the IG UI. It moves up when the shot needs room.
8. **Small visual props:** a Philippines flag graphic pops in on "from the Philippines". It's literal and quick, and
   it's gone in about 1 s.

## The sound effects (from the audio)

Measured from spectrograms and onset timing against `words.json`, so read the levels as approximate.

- **A soft "tick/pop" on caption landings.** These are short (~50 ms), tonal (~1.1–1.4 kHz) blips that sit well under
  the voice. Most land **0–80 ms before the word** they belong to: e.g. 22.05 s → `Follow` 22.10, 22.70 → `own` 22.78.
  They don't fire on every word, only on **caption-group changes and keywords**. That's why it reads as "satisfying"
  rather than as clicking noise.
- **A longer tonal swell on the big keyword.** About 0.3–0.4 s of sustained ~1.4 kHz under `HEY` (0–0.4 s) and
  under the white `listen` card (33.6–34.1 s). Like a soft "whoom"/"ding" that matches the big text.
- **A high shimmer/chirp** (~6–7 kHz, short) on graphic pop-ins: 2.9 s when the flag clears, 5.2 s, 6.9 s around
  `CLIENT`. A sparkle/"swish" on visual accents.
- **A piano/music bed** with sustained notes under the whole podcast section (from ~9.7 s), quiet. In the gap at
  35.8–37 s it's alone in the mix.
- **A sub-bass hit + drone at the black frame** (~37.0 s, 40–90 Hz, ~1 s tail). This is the impact that ends the
  podcast section before the outro.
- **The whole mix stays quiet.** Every SFX is far below the voice. Nothing competes with the words.

## What we take for @matteofights

- **Keep our Tinos serif one-word subtitles** (PIPELINE.md non-negotiable). What to copy is the *system*, not the font:
  - Add a **quiet tick under each subtitle change** and a **slightly bigger tonal hit under red keywords**, landing
    ~2 frames (≈60 ms) before the word. Keep it ~20–25 dB under the voice.
  - Keep **one keyword size jump + colour** per line (our red `#E8112D`) instead of styling many words.
  - **White-card typography cutaways** for the 1–2 reveal lines per reel (black serif + one red word). These work as
    a pattern interrupt every few seconds without needing b-roll, which is good for talking-point reels with thin footage.
  - **Big hook word behind Matteo's head** on frame 0 (subject cut-out). This also makes the thumbnail.
  - A **sub hit on a black frame** before the CTA/loop as the section break.
- **Don't copy:** the multi-colour keyword palette (green/pink). It's off-brand for us; we stay red/black/ivory.

## Next step (not done yet)

`production/editing/reel-kit/` has no caption-SFX layer yet. To build it: a small tick/pop/sub set (free source,
e.g. Mixkit SFX), then have the HyperFrames template place a tick on every `W('seg','WORD')` subtitle change and a
hit on red words, offset −0.06 s. Test it on the next talking-points reel.
