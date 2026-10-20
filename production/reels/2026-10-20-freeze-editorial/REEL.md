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

- Hook title on frame 0: "If you freeze when you spar, / **it's your head.**" Clears just before "and there are".
- Captions in the ceiling space (y330), phrases of 1–4 words, keywords THREE, ONE, TWO, JAB, RELAX, CAUGHT.
- White cards: "getting punched isn't a failure, it's just **information**" · "pick **one** job per round" ·
  "take a deep breath and **reset**" (slam + sub). Hard cut back to the face for "because", which holds the
  hook's framing so the loop has no jump.
- Audio: caption ticks, key tones, whoom into cards, synthesised piano bed (placeholder) ~19 dB under the voice,
  lifting ~12 dB on cards. Render: -15.7 LUFS, -1.5 dBTP.

Build (cloud): the raw is `media/freeze/media/freeze-in-sparring-raw.mp4` from the media release
(`freeze-in-sparring-raw.mp4`); `prep_footage.sh` it to `assets/raw.mp4`, set `audio_src` in `work/takes.json`
to wherever the raw is, then `assemble.py work/takes.json A`, `python -P build.py`, render.
Render: `media/freeze-editorial/freeze-editorial-A.mp4` (+ `-phone.mp4`). The media release upload failed from
the cloud (proxy), so it only exists in the session and in the chat.
