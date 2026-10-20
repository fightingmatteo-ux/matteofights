# Editorial talking-head template (default since 2026-10-20)

Matteo's chosen look, from the @kaixerb reference: clean phrase captions that focus in and dissolve, keywords with
effects that mean the word, captions alternating behind / in front of him (cut-out), white quote cards on the
2-3 lines that carry the reel, caption SFX, and a hook word that flies from behind his head to the front when he
says it. Proof: `production/reels/2026-10-20-freeze-editorial/` (renders A-A5 in its REEL.md).

## New reel
1. Copy `production/reels/_TEMPLATE/` (REEL.md, TALKING-POINTS.md) **and** this folder's `build.py`, `make.sh`,
   `work/template.html` into `production/reels/<yyyy-mm-dd-slug>/`. Copy `assets/lib/gsap.min.js` and
   `package.json` from `2026-10-20-freeze-editorial/`.
2. Footage in + takes (PIPELINE.md steps 3-4) -> `work/takes.json`, `work/words.json`.
3. Fill the `REEL` block at the top of `build.py` from the transcript: per variant the hook lead lines, the hook
   word and the spoken word it flies forward on; the keywords; 2-3 cards; one slam.
4. `bash make.sh A` (then B, C, one at a time). It assembles, cuts Matteo out (~5 min for 25 s, cached in
   `assets/media/fg_<V>_full.webm`), builds, renders, runs the glitch check (re-renders once on FAIL), and writes
   a `-phone.mp4` to send.
5. Look at it before sending: `npx --yes hyperframes@0.8.147 snapshot --at <hook word>,<each keyword>,<each card>`.
   Behind-him keywords must stay readable (hair covers about a quarter), cards must fit the frame.

Kit, effects table and every rule: `production/editing/reel-kit/editorial/README.md`.
