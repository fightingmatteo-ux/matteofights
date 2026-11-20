# Origin pin: "School came easy. Fighting didn't." (3 openings that look different, every variant a loop)

The "who is he" pin. Script and research: `SCRIPT.md`, `production/competitors/talking-heads-2026-11-20.md`.
Filmed 2026-11-20 at home, one continuous take (Drive input `DJI_20261120160331_0230_D.MP4`, 7:52, 4K HDR),
prepped to the 1080x1920 master by Fetch video and stored on the media release as `origin-pin-raw.mp4`
(transcript + frames: `content-bank/real-footage/analysis/origin-pin-raw/`). Matteo filmed 3 loop endings, A B C
(Matteo 11-20: 3 genuinely different beat 5 that look the same; spend the effort on edit quality instead).

## Variants (only the opening and its loop bridge differ)

| V | Opening | Frame 0 | Hook (bridge at the end runs into it) | Length |
|---|---|---|---|---|
| A | result | his face, board "One fight at 16. Still no SECOND." | "...because right now it's still this. / One fight at 16. I'm 19 and I still haven't had my second one." | 81.0 s |
| B | contrast | cold: his beginner pad kick (chaiya, 19.4 s), his face on "Fighting" | "...and honestly? / School came easy to me. Fighting was the first thing that didn't." | 76.3 s |
| C | story peak | cold: the stadium (first-fight-2, 6 s), then the hospital-gown photo on "I ended up in the hospital" | "...because this isn't my first time. / The day before my first fight, I ended up in the hospital." | 78.3 s |

## Edit decisions (for retention)
- Takes and reasons: `work/takes.json` ("why"). Eye contact first, then energy (taste.md).
- Cut "Same rule as that first fight": repeats point 5; the sharp bag combos straight into "Follow if you want to see the
  comeback" is the stronger end. B's body skips "school came easy", C's skips "the day before the fight" (said in
  their hooks).
- B-roll on the exact words (`work/make_broll_json.py`): Super Pro photo with Matteo circled on "jiu-jitsu at 10",
  Super8 pads on "switched to striking", the stadium on "booked my first fight", beginner pads on "if I hadn't
  trained", hospital photo on "appendicitis", Matteo's kicks in fight 2 (his pick, 24 s) on "different stadium",
  bag kicks on "trained three more months", a 1-cut-per-country flash (Thailand, Switzerland, Italy, Morocco; Brazil
  on his face), hand photo on "boxer's fracture", X-ray on "broken fibula, torn ACL", two sharp bag combos
  (Fitness First, 28 s and 40 s) on "but I can do this": Matteo 11-20, no home shadowboxing on screen. No kick clip near "I can't jump" (viewers would call it out).
- 2 white cards: "Scared to get knocked out in front of all my FRIENDS", "...you actually have to WORK your ass off
  for it" (slam). Keywords every 3-6 s; captions from frame 0 (Buzzfy: burned-in captions, skip 33% vs 44%).
- CTA pill "FOLLOW FOR THE COMEBACK" from "Follow" in the bridge. Bed: epic-bold-drums (same as the breakdowns).

## Render
Submit render, variants `A B C`, media `origin-pin-raw.mp4=media/origin-pin/raw.mp4
broll-pads-chaiya.mp4=media/origin-pin/broll-pads-chaiya.mp4 first-fight-2.mp4=media/origin-pin/first-fight-2.mp4`,
include `tools/planreel production/listicles/music/epic-bold-drums-alex-morgan.mp3`. precut.sh pulls Matteo's
Drive clips with gdown, cuts them + the photo push-ins, and builds the a-rolls; Modal runs make.sh.

## Queue
Not queued yet: Matteo watches A, B, C first. Then trial set `origin-pin`, same day 15:00-15:30 NY, `approved:false`.
