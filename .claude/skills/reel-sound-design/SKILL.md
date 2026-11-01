---
name: reel-sound-design
description: Sound design pass for @matteofights talking-head reels and fight breakdowns - which SFX go where (hits, booms, whooshes, risers, bell, heartbeat, freeze shutter, real fight-tape audio), levels against the voice, silence as a tool, and how to place them from the EDL with production/editing/reel-kit/editorial/sound_design.py. Use whenever a reel is edited or re-cut, when Matteo says the sound or SFX is weak, or for a round-2 re-edit aimed at retention.
---

# Reel sound design (retention)

Sound is half the edit. On a muted-autoplay feed the first sound a viewer hears after tapping unmute decides if they
stay, and every visual change without a sound feels cheap. Library + placer: `production/editing/reel-kit/editorial/sound_design.py`
(synthesised, no downloads, no licences, deterministic). The editorial kit's quiet caption SFX (tick, key) stay
underneath; this is the layer you actually hear.

## The cue sheet (place from EDL word times, never by eye)

| Moment | Sound | Timing | Vol |
|---|---|---|---|
| Frame 0 / hook word punch | `hit` (or `boom` if the hook IS the payoff) | 0.02 s before the word | 0.7-0.9 |
| Every b-roll / tape whip-in, every card in/out | `whoosh` (auto-rotates 3 variants) | peak (+0.18 s) on the cut | 0.35-0.5 |
| Jump cut between takes (framing change) | `whoosh` low, or nothing if the cut is on a breath | on the join | 0.25 |
| A fight starts in the story ("my first fight") | `bell` | on the word | 0.35 |
| Pressure line (fear, nerves, "before I walked out") | `heart` | starts on the line | 0.5 |
| Build into the reveal | `riser` (2 s) ending hard 0.05 s before the reveal word; cut the music bed at the same moment | | 0.45 |
| The reveal / verdict line | silence (music out) then `boom` on the key word | | 0.8 |
| A punch landing on tape | `hit` + the tape's own audio (crowd, gloves) brought up under the voice | on the impact frame | 0.6 |
| Freeze frame | `shutter` | on the freeze | 0.6 |
| Each item in a list / number | `thud` | on the item's first word | 0.4 |
| Pattern interrupt (one per reel max) | `glitch` | | 0.3 |

## Rules
0. **Something visual or audible every 3 s, max** (Matteo 2026-11-01). Count cuts, b-roll, cards, keyword hits,
   punch-ins and audible SFX (caption ticks don't count). `sd.fill_gaps()` finds every longer stretch and the build
   adds a camera punch-in + a soft sound on the nearest phrase start.
1. **Every visual change has a sound, every sound has a visual.** No orphan SFX.
2. **Voice wins.** SFX peaks 6-10 dB under the voice; a hit/boom may touch -3 dB under it for one frame. Never cover a
   consonant attack of a word that isn't the hit word.
3. **Silence is the strongest SFX.** Drop the music 0.1 s before the biggest line; leave 0.3-0.5 s of air after it.
4. **Budget:** max one boom per ~10 s, one riser per reel (two if > 40 s), one glitch per reel. Whooshes: as many as cuts.
5. **Real audio beats synth:** when tape is on screen, use its own sound (crowd, ref, gloves), ducked ~12 dB under the
   voice, plus a synth `hit` on the impact frame.
6. **Loop seam:** nothing rings across the end of the video (no tail on the last 0.4 s), the music bed must loop on a
   matching bar, and the first frame's hit must not double with a tail from the end.
7. **Check by measurement:** after the render, the voice-only sections must stay at the a-roll's loudness (no SFX
   masking) and the whole reel lands about -14 to -16 LUFS, true peak under -1 dBTP.

## How to use
```python
import sys; sys.path.insert(0, "../../editing/reel-kit/editorial")
import sound_design as sd
sd.make_all("assets/sfx/sd")                         # once per reel
cues = [("hit", W("KNOCKED") - 0.02, 0.8), ("whoosh", card_t0 - 0.18, 0.45), ...]
html = sd.tags(cues, sfx_dir="assets/sfx/sd", track0=40, total=duration)   # -> <audio> tags for the template
```
Log what you placed in the reel's REEL.md so round-2 re-edits can change one thing at a time.
