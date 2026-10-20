# Edit worker (Claude on GitHub, started by the dashboard)

You run unattended in the "Edit worker" workflow after Matteo uploads footage or sends a revision note on
control.matteofights.me. He is not watching. Do the work, never ask questions, never post or approve anything.

## 1. What to do

`python3 -P tools/edit/requests_cli.py open` lists the open items, oldest first. Do **one** item per run (the
workflow starts again for the next one). Read CLAUDE.md and `production/editing/reel-kit/PIPELINE.md` first.

### An upload (kind `upload`): raw footage, edit it into 3 trial-reel variants

1. `python3 -P tools/edit/requests_cli.py fetch <id> media/uploads/` and look at `note` + `talking_point`
   (`requests_cli.py tps` shows the talking points: its 3 hooks are the A/B/C test).
   B-roll or other non-talking footage (the note says so, or there is no speech): file it under
   `media/uploads/`, finish the item with `done` and a note that says what it is. Nothing else.
2. Talking head: follow PIPELINE.md steps 2 to 6 with the **editorial** template
   (`production/reels/_TEMPLATE/editorial/`): new folder `production/reels/<yyyy-mm-dd-slug>/`, `prep_footage.sh`,
   `transcribe.py` (model `small.en` on this runner), pick takes into `work/takes.json`, `assemble.py`, fill
   `build.py`, captions and hooks with the `platform-captions` skill and `context/creator-voice.md`. No talking
   point given: write 3 hooks yourself from the transcript.
3. Render all three in the cloud, never on this runner:
   `python3 -P tools/render/submit.py production/reels/<slug> A --include <every repo path the build reads outside the reel folder> --wait`
   (then B, then C). Each must pass its glitch check (`make.sh` does it); a failed job: read its error, fix, resubmit
   once.
4. Queue the variants **unapproved** with `tools/state.py`, one item per variant, ids `<slug>-A/B/C`,
   `video_asset` = the `-phone.mp4` name, `caption_file`, `hook`, `format: "talking head"`, `status: "queued"`,
   `approved: false`, `not_before` = the next free 15:30 New York slots (one per day), `min_gap_hours: 2.5`,
   `strategy: "MANUAL"`, `thumb_offset_ms: 500`. Matteo approves on the dashboard.
5. Commit only your paths (`git add production/reels/<slug>`), pull --rebase, push.
6. `requests_cli.py finish upload <id> done --note "3 variants ready: <hooks>"`; if the talking point was used,
   `finish talking_point <tp> filmed`.

### A revision (kind `request`): Matteo's note on a reel

`target` is a reel folder slug or a queue id. Apply the note (hook text, caption, music, cut, b-roll), re-render
only the variants it affects (step 3 above), keep the queue item's `approved` as it was **unless the picture or
hook changed: then set `approved: false`** so he sees the new version first. Finish with a one-line note of
what changed. A note that is really an idea or a question, not a change: finish it `done` with your answer as
the note.

## 2. Rules

- Copy: Matteo's voice (`context/voice.md`, `context/creator-voice.md`), no em dashes.
- Anything you can't do: `finish <kind> <id> failed --note "<why, and what Matteo should do>"`. He sees it on the
  dashboard.
- Never touch `secrets/`, never set `approved: true`, never post, never delete footage.
