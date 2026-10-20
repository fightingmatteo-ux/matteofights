---
slug: 2026-10-20-freeze-editorial
status: test render (A only), sent to Matteo 2026-10-20 for a style check. Not queued, not posted
pillar: psychology
format: talking-head listicle, editorial look
test_variable: look (same takes as 2026-10-14-freeze-in-sparring A)
---

# Freeze in sparring A, editorial re-cut

Same takes as `2026-10-14-freeze-in-sparring` variant A, rebuilt with `reel-kit/editorial/` (the @kaixerb
"premium minimal" look, Matteo's call 2026-10-20). Compare against the posted freeze-A.

- Hook title on frame 0: "If you freeze when you spar, / it's your" + **head.** huge and red BEHIND his hair
  (v2: `fg_A.webm` cut-out from `cutout.py`, 0-3.6 s). Clears just before "and there are".
- Captions in the ceiling space (y330), phrases of 1–4 words, keywords THREE, ONE, TWO, JAB, RELAX, CAUGHT.
- White cards: "getting punched isn't a failure, it's just **information**" · "pick **one** job per round" ·
  "take a deep breath and **reset**" (slam + sub). Hard cut back to the face for "because", which holds the
  hook's framing so the loop has no jump.
- Audio: caption ticks, key tones, whoom into cards, synthesised piano bed (placeholder) ~19 dB under the voice,
  lifting ~12 dB on cards. Render: -15.7 LUFS, -1.5 dBTP.

Build (cloud): the raw is `media/freeze/media/freeze-in-sparring-raw.mp4` from the media release
(`freeze-in-sparring-raw.mp4`); `prep_footage.sh` it to `assets/raw.mp4`, set `audio_src` in `work/takes.json`
to wherever the raw is, then `assemble.py work/takes.json A`, `python -P build.py`, render.
Render v2: `media/freeze-editorial/freeze-editorial-A2.mp4` (+ `-phone.mp4`), check_render OK. v1 had black
frames 0/2 + a zoom jump (renderer cold start), fixed by re-rendering. The media release upload failed from
the cloud (proxy), so it only exists in the session and in the chat.

## v3 (2026-10-20, Matteo: "alternate behind and in front, effects that match the words, smoother like the reference")
- Keyword phrases alternate front / behind (full cut-out `fg_A_full.webm`, placed from `cutout.head_top`).
- Effects: three/one/two = count (ghost numeral), information = decode, jab = jab, relax = exhale,
  caught = impact, reset = rewind (slam). Matching synthesised sounds, 8-16 dB over baseline, under the voice.
- Transitions: focus-pull in, blur dissolve out, ~0.1 s crossfade; cards whip in/out.
- Render `media/freeze-editorial/freeze-editorial-A3.mp4` (+ `-phone`), check_render OK, peak -1.6 dBFS.

## v4 (2026-10-20, Matteo: "when I say head, it goes from behind me to in front of me")
- Hook: **head.** sits behind his hair until he says "head" (2.87 s), then punches through to the front
  (`#behind` hands over to `#front-head` above the cut-out, scale pop 0.9 -> 1.12 -> 1, camera punch, punch SFX).
- Render `media/freeze-editorial/freeze-editorial-A4.mp4` (+ `-phone`), check_render OK.
