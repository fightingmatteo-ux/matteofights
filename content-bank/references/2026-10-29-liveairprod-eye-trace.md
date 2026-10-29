# Reference: invisible cuts by eye-trace (@liveairprod)

- **Link:** https://www.instagram.com/reel/DfAZMAjseOQ/
- **Saved:** 2026-10-29, by Matteo: "adding this cutting and editing technique to our pipeline would make our video
  quality and watch time go through the roof."
- **Status:** WATCHED. Frames, transcript, cuts and words are in `references/videos/liveairpod-edit-ref/`. The mp4 is on
  the `media` release (`liveairpod-edit-ref.mp4`).
- **What it is:** an editing-tips creator (Arthur, "Day 9/365"). 24.6 s, 7 hard cuts, average shot 3.1 s, 12k likes,
  71 comments. Caption: "How to make cuts like in the movies". We're studying the **edit craft**, not the topic.

## Transcript (Whisper)
> How to cut shots invisibly, just like in the movies. Let me show you. Right now your eyes are here. The next shot
> should start in exactly the same place. I move your gaze and this becomes the new point of focus. Every new shot
> should begin where the viewer's eyes were at the end of the previous one. This simple technique lets you cut
> without any visual discomfort for the audience. Use it in all of your videos. Follow for more.

## The technique: eye-trace cutting
At the moment of a cut the viewer is looking at one spot. If the next shot's subject starts on that same spot, the eye
doesn't have to hunt, so the cut feels invisible. If it starts somewhere else, the viewer gets a split second of
"where am I looking?", which is exactly when people swipe.

What he does at each of his 7 cuts:

| Cut | Before → after | Focus |
|---|---|---|
| 4.40 | face at desk → face, closer, other angle | eyes stay on the same spot (0.1% jump) |
| 7.16 | face → his face on the laptop screen | same spot, a gold frame marks it |
| 10.72 | laptop face → hand pulling a book off the shelf | the hand starts where the face was ("I move your gaze") |
| 12.76 | book shelf → him reading that book | the book is the bridge |
| 16.96 | book in hand (lower right) → him on the floor, lower right | same corner of the frame |
| 21.00 | writing at the desk → close-up of the pen on paper | match on action |
| 22.76 | pen on paper → him writing, end card | same hand, same move |

Measured with `production/editing/reel-kit/scripts/eyetrace.py`: **median jump 11% of frame height, 0 cuts over 30%.**

Also in it (not for us): gold outline boxes that mark the focus point, an orange light-leak flash on the "let me
show you" cut, and a moving gaze inside a shot (he moves the book, the eye follows, the next cut starts there).

## How it applies to @matteofights
**Our latest editorial cut already mostly does this.** Same check on `2026-10-24-knockout-draw-A`: median jump 10%,
0 cuts over 30%. Why: the white card's keyword sits at eye height (the card box starts at y 640), and fight tape is
centred, where his face is. So this is **not** a big hidden gain on the current talking heads. It is a rule to keep,
and it matters more as soon as we cut between more angles. Where we are weakest:

1. **Cards: the first word lands at the far left** (x 80) while his eyes are in the middle (cuts 20.70 and 33.43,
   16-26%). The eye goes left, then back to the red keyword. Option, not done (it changes the approved kaixerb
   layout): start the lead line nearer the centre.
2. **Fight-tape crops are picked for content, not for the eye.** Now: `eyetrace.crop_x(src, t, crop_w, 0.5)` gives the
   crop where the action lands where his eyes were. Use it in every `make_broll.py`.
3. **When Matteo films a 2nd angle or b-roll of himself:** plan each cut so the next shot starts where the last one
   ended (eyes to eyes, glove to glove, hand to hand). This is the real win from the reference: it is what lets him
   switch setups every 3 s without it feeling choppy. Shot guide line in `production/shooting/` when he films one.

Not adopting: the gold boxes (our look is "no boxes", PIPELINE.md) and the light-leak flash (flashes only on big hits).
