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
| `cutout.py` | Robust Video Matting -> `fg_<V>.webm` (Matteo only, with alpha) for text **behind his head** |
| `check_render.py` | fails a render whose first second has black / out-of-step frames (cold-start glitch) |

## Per reel you decide only three things (in `build.py`)
1. **keys**: the words that turn big + red over the face (one per phrase, ~every 3–6 s).
2. **cards**: `(start, end, KEYWORD)` for the 2–3 lines that carry the reel. Start ~0.06 s before the line's
   first word, end ~0.1 s before the next line. The keyword must be a word inside that span.
3. **slam** (optional, max one): a card keyword that over-scales with a sub hit. Plus `hide` for the hook title.

Then: `python -P build.py && npx --yes hyperframes@0.8.147 render -q standard -w 4 -o <out>.mp4` (~2 min in the
cloud for 25 s), then **always** `python3 -I check_render.py <out>.mp4 assets/media/aroll_<V>.mp4`. On FAIL, render
again (2026-10-20: the session's first render had black frames 0 and 2 and a zoom jump; the re-render was clean).

## Text behind the head (works in the cloud)
```bash
python3 -m venv .venv && .venv/bin/pip install onnxruntime numpy
curl -L -o rvm.onnx https://github.com/PeterL1n/RobustVideoMatting/releases/download/v1.0.0/rvm_mobilenetv3_fp32.onnx
.venv/bin/python ../../editing/reel-kit/editorial/cutout.py assets/media/aroll_A.mp4 assets/media/fg_A.webm --to 3.6 --model rvm.onnx
```
~0.4 s per frame on 4 CPUs (hook only: ~40 s). In the template, inside `#cam-inner`: A-roll, then the big word
(`#behind`, ~360 px, placed so the hair covers its lower edge), then `fg_A.webm` with the same start. All three sit
in the camera, so the push-in moves them together. Example: `2026-10-20-freeze-editorial/work/template.html`.

## Notes
- The piano bed is a synthesised placeholder (the cloud can't download music). Swap `assets/media/bed.wav` for a
  real track, or add a trending sound in the IG app and mute the bed.
- Levels (checked by subtracting the voice from a render): bed ~19 dB under the voice over the face, ~8–10 dB
  under it on cards. Render lands at about -15.7 LUFS, -1.5 dBTP.
