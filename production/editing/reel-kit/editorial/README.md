# Editorial kit: premium minimal captions, white quote cards, caption SFX

The talking-head look since 2026-10-20, from the @kaixerb reference
(`content-bank/references/2026-10-20-kaixerb-caption-sfx.md`). Worked example:
`production/reels/2026-10-20-freeze-editorial/` (`build.py`, `work/template.html`).

| File | What |
|---|---|
| `plan.py` | EDL + your choices -> caption phrases, card markup, SFX `<audio>` tags, bed automation, PLAN json |
| `editorial.css` / `editorial.js` | inlined into the template by the build; `Editorial.animate(tl, PLAN, {cam})` |
| `make_audio.py` | synthesises `sfx/*.wav` (tick, key, whoom, shimmer, sub) and the per-reel piano bed |
| `fonts/Geist-latin.woff2` | the caption face |

## Per reel you decide only three things (in `build.py`)
1. **keys**: the words that turn big + red over the face (one per phrase, ~every 3–6 s).
2. **cards**: `(start, end, KEYWORD)` for the 2–3 lines that carry the reel. Start ~0.06 s before the line's
   first word, end ~0.1 s before the next line. The keyword must be a word inside that span.
3. **slam** (optional, max one): a card keyword that over-scales with a sub hit. Plus `hide` for the hook title.

Then: `python -P build.py && npx --yes hyperframes@0.8.147 render -q standard -w 4 -o <out>.mp4` (~2 min in the
cloud for 25 s).

## Notes
- The piano bed is a synthesised placeholder (the cloud can't download music). Swap `assets/media/bed.wav` for a
  real track, or add a trending sound in the IG app and mute the bed.
- Levels (checked by subtracting the voice from a render): bed ~19 dB under the voice over the face, ~8–10 dB
  under it on cards. Render lands at about -15.7 LUFS, -1.5 dBTP.
- Not built yet: the hook word **behind** the head (subject cut-out, needs a segmentation model on the laptop).
