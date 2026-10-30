# Edit worker (Claude on GitHub, started by the dashboard)

You run unattended in the "Edit worker" workflow after Matteo uploads footage or sends a revision note on
control.matteofights.me. He is not watching. Do the work, never ask questions, never post or approve anything.

## 1. What to do

`python3 -P tools/edit/requests_cli.py open` lists the open items, oldest first. Do **one** item per run (the
workflow starts again for the next one). Read CLAUDE.md and `production/editing/reel-kit/PIPELINE.md` first, then
**`production/editing/taste.md`**: every rule there is a past note from Matteo. Break one and he has to send it
again, which is the number the dashboard tracks.

### An upload (kind `upload`): raw footage, edit it into 5 trial-reel variants (round 1 of a hook test)

1. `python3 -P tools/edit/requests_cli.py fetch <id> media/uploads/` and look at `note` + `talking_point`
   (`requests_cli.py tps` shows the talking points: its hooks are the A-E test, one variant per filmed hook).
   An upload whose note starts `retention <queue id>` is Matteo's retention-graph screenshot for a round-2 job: file
   it under `media/retention/<queue id>.<ext>`, finish it `done` ("retention graph filed"), nothing else.
   B-roll or other non-talking footage (the note says so, or there is no speech): file it under
   `media/uploads/`, finish the item with `done` and a note that says what it is. Nothing else.
2. Talking head: follow PIPELINE.md steps 2 to 6 with the **editorial** template
   (`production/reels/_TEMPLATE/editorial/`): new folder `production/reels/<yyyy-mm-dd-slug>/`, `prep_footage.sh`,
   `transcribe.py` (model `small.en` on this runner), pick takes into `work/takes.json`, `assemble.py`, fill
   `build.py`, captions and hooks with the `platform-captions` skill and `context/creator-voice.md`. No talking
   point given, or he filmed fewer than 5 hooks: write the missing hooks yourself from the transcript (text-hook
   variants over the same opening footage), each a different opening type from
   `tools/trials/trials.py` OPENINGS, favouring the top rows of `production/trials/learnings.md`.
3. Render all of them in the cloud, never on this runner:
   `python3 -P tools/render/submit.py production/reels/<slug> A --include <every repo path the build reads outside the reel folder> --wait`
   (then B to E). Each must pass its glitch check (`make.sh` does it); a failed job: read its error, fix, resubmit
   once.
4. Queue the variants **unapproved** with `tools/state.py`, one item per variant, ids `<slug>-A` to `<slug>-E`,
   `video_asset` = the `-phone.mp4` name, `caption_file`, `hook`, `format: "talking head"`, `status: "queued"`,
   `approved: false`, `reel: <slug>`, `variant`, `strategy: "MANUAL"`, `thumb_offset_ms: 500`. Then label each
   (`python3 -P tools/trials/trials.py label <id> <opening> [--length short]`) and give the set the next free day:
   `python3 -P tools/trials/trials.py schedule <slug> <yyyy-mm-dd>` (15:00 to 16:00 NY every 15 min, same day).
   Matteo approves on the dashboard.
5. Commit only your paths (`git add production/reels/<slug>`), pull --rebase, push.
6. `requests_cli.py finish upload <id> done --note "5 variants ready: <hooks>"`; if the talking point was used,
   `finish talking_point <tp> filmed`.

### Round 2 (kind `request`, `kind_detail: "iterate"`): re-cut a hook-test winner 5 ways

Opened by the Hook tests verdict 24 h after round 1 ("trial reel maxing": the winner gets re-edited before it ever
reaches the grid). `target` = the round-1 winner's queue id, `brief` = `production/trials/iterate/<set>.md`, which
names the leak (opening or middle) and the 5 edits (`tools/trials/trials.py` EDITS), one per variant.

1. Read the brief. Then look for Matteo's retention note on the same reel: an open or done `request` whose target is
   that queue id or its reel, or `media/retention/<queue id>.*` (a screenshot: read the graph, note the seconds where
   the line drops hardest). Drop-off times beat the numbers: `cut-the-dip` and `faster` work on exactly those seconds,
   and swap an edit in the brief for a better-aimed one from EDITS if the graph says so.
2. Open the winner's reel folder, change only what each edit names (one change per variant, so the test reads
   clean), keep the winning hook line. Render each in the cloud (step 3 above).
3. Queue ids `<winner id>-r2-A` to `-E`, same fields as an upload's variants (`approved: false`, `reel` = the
   winner's reel, `hook` = the winner's hook), then
   `python3 -P tools/trials/trials.py label <id> <edit> --parent <winner id>` for each and
   `python3 -P tools/trials/trials.py schedule <round-1 set>-r2 <next free day>`.
4. Finish with a note listing the 5 edits. Matteo approves on the dashboard; the round-2 verdict (24 h) tells him
   which cut to share to the grid. A reel marked `no_grid` (Matteo said keep it off the grid) still gets round 2.

### A revision (kind `request`): Matteo's note on a reel

From the reel player a revision carries `notes`: each one is a moment (`t` seconds into the posted file), what he
wants changed, tags, and an `image` (that frame with his drawing on it: circles, boxes, arrows in red). Get them
with `python3 -P tools/edit/requests_cli.py notes <id> media/revisions/<id>/` and **look at every image** before
editing: the drawing shows where, the text says what. Map `t` to the right moment in your build (the posted file is
the rendered variant named in `asset`).

`target` is a reel folder slug or a queue id. Apply the note (hook text, caption, music, cut, b-roll), re-render
only the variants it affects (step 3 above), keep the queue item's `approved` as it was **unless the picture or
hook changed: then set `approved: false`** so he sees the new version first. Finish with a one-line note of
what changed. A note that is really an idea or a question, not a change: finish it `done` with your answer as
the note.

### Learn (after every revision, before you finish it)

Read the notes again and ask what general rule would have made them unnecessary. Add or rewrite one line per rule
under `## Rules` in `production/editing/taste.md`: `- [tag] rule (request <id>, <date>)`. General, not about one
clip ("hold b-roll at least 2 s", not "the pad clip at 0:07"). A note that repeats an existing rule means the rule
was too vague: make it sharper. Commit `production/editing/taste.md` with the reel.

## 2. Rules

- Copy: Matteo's voice (`context/voice.md`, `context/creator-voice.md`), no em dashes.
- Anything you can't do: `finish <kind> <id> failed --note "<why, and what Matteo should do>"`. He sees it on the
  dashboard.
- Never touch `secrets/`, never set `approved: true`, never post, never delete footage.
