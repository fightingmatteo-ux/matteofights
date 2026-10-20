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

## Keyword effects (the word's meaning drives the motion + its sound)
| Effect | Words (defaults in `plan.FX`) | Motion | Sound |
|---|---|---|---|
| `rewind` | reset, restart, again, back | letters scattered, rewind into place, chromatic ghost collapses, snap | tape rewind + click |
| `jab` | jab, punch(ed), hit, strike | thrown in from the left with a skewed streak, overshoots, camera takes the hit | swish + thump |
| `impact` | caught, knocked, slam, hurt | lands hard, shakes, white flash, camera punch | crack + low hit |
| `exhale` | relax, breath(e), calm | letters start packed tight and breathe out, word floats up | soft breath |
| `decode` | information, data, thinking, learn | letters scramble through glyphs, lock in left to right | computer blips |
| `count` | one … five | giant outlined numeral swells behind the word | key tone |
| `freeze` | freeze, froze, stuck | arrives ice-blue and shivering, thaws to red | shimmer |
| `focus` | anything else | deep focus pull | key tone |
Override per reel: `plan.build(..., fx={"WORD": "effect"})`. Add an effect = a function in `editorial.js` FX + a
sound in `make_audio.py` + a row in `plan.FX_SFX`. Everything is seeded, so renders repeat exactly.

## Behind / in front
Keyword phrases alternate front, behind, front... (`behind=True`). Behind phrases live in `#ed-caps-back` inside
the camera, under the full-length cut-out (`fg_<V>_full.webm`, ~5 min for 25 s). Their height comes from
`back_top=lambda t: cutout.head_top(fg, t) - 235`: the highest his head gets during the phrase, so his hair
always covers about the bottom quarter of the keyword, never more.

## Transitions (measured on the reference, frame by frame)
Words focus in (blur 14px -> 0, ~0.3 s, no bounce). A phrase dissolves into blur in ~0.18 s, ending just as the
next one starts focusing (overlap ~0.1 s; longer overlap smears). Cards whip in with a horizontal motion blur;
the face whips back in with a blur after.

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

**Punch-through hook (the default):** the hook word sits low enough that his head hides ~40% of it, winds back
(scale 0.92) just before the spoken word, then a second copy (`#front-head`, above the cut-out) flies forward
toward the camera (0.92 -> 1.26 -> 1.14, down over his forehead) with a camera punch and the punch SFX. Just
swapping layers in place is invisible (tried in v4): the word must be visibly cut by him first, and it must move. `check_render.py` keeps its default 1.5 s window, because a longer one flags this intended jump.

## Notes
- The piano bed is a synthesised placeholder (the cloud can't download music). Swap `assets/media/bed.wav` for a
  real track, or add a trending sound in the IG app and mute the bed.
- Levels (checked by subtracting the voice from a render): bed ~19 dB under the voice over the face, ~8–10 dB
  under it on cards. Render lands at about -15.7 LUFS, -1.5 dBTP.
