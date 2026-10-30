# Trial reel maxing (@browniegainz, 2026-10-30)

Source: https://www.instagram.com/reel/DeGv_9JTxn_/ (Ethan Brown, content strategist; 1,680 likes, 72 comments, 62 s).
Fetched: `content-bank/references/videos/2026-10-30-browniegainz/` (contact sheet, transcript).
Matteo (2026-10-30): both trial reel setups, @matteofights and Gypsy Amazon, take this on in full.

## The playbook (his three steps)
1. Script as usual, but **film 5 different hooks** every time you shoot.
2. **Post the same reel with the 5 hooks as trial reels in one go**; see which performs best.
3. The step most skip: **24 h later, don't post the winner to the feed. Re-edit it**: read the retention graph, find
   where people drop, make **5 iterations of the winner**, post those as trials, pick the best again. Repeat as often
   as you like; only when the one video is maxed out, post it to the main feed.

## The format (how the reel itself is built)
Single talking head, purple-lit room, one take feel, no hard cuts. A persistent top title (`Trial reelmaxxing in Q4`)
for the first 8 s, then a small illustrative image or meme above his head swapped every 1-2 s (literal to the word
being said: hourglass on "short time", a lightbulb on "ideas", a big "5" on "five hooks", a retention chart on
"retention"). Word-by-word captions at chest height. Insult-hook opening ("if you weren't such a ..."), dare
("most of you won't even do it"), FOMO ("enjoy watching your competitors overtake you"), "the third step is the one you'll
skip" as the re-hook, follow CTA. The swear-word hook is his voice, not Matteo's or Tatiana's.

## How we took it on
- @matteofights: `tools/trials/trials.py` (5 slots 15:00-16:00 NY, verdict at 24 h, round 2 = EDITS on the winner,
  round-2 job opened for the Edit worker; retention note from Matteo optional), `tools/edit/WORKER.md`, CLAUDE.md.
  Instagram's API gives no retention graph, only skip rate and avg watch: the cuts aim at those unless Matteo sends
  the drop-off seconds or a screenshot.
- Gypsy Amazon: `content-engine/brain/system.md` "Hook tests", from the batch after 14 Nov 2026.
- Borrowable for the reels themselves: the above-the-head image that changes with every key word (cheap B-roll
  for talking heads, keeps the eye moving without cutting away from the face).
