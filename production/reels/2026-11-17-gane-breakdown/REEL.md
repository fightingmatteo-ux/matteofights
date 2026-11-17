# Fighter Breakdown: Ciryl Gane (distance), 5 hook variants

Source: one Pocket 3 long take in the Drive input folder (DJI 0225, 17 Nov), unscripted (no sheet entry), every
line repeated until clean. Prepped (`prep_footage.sh`) into `media/gane-ep-src/raw.mp4` and flipped horizontally
(same camera setting as the Floyd clips, which were mirrored). Git-ignored, rebuild from Drive. Template copied
from `2026-11-17-floyd-breakdown/`. Spoken "Episode four" cut out. Bed = the series bed (epic-bold-drums).

Structure per variant: hook (A-E), intro, body ("a heavyweight who moves like a lightweight"), One, Two, the third
one, Three, takeaway, CTA, 5 plan day cards on room tone. Only the hook differs.

## Takes (raw.mp4 seconds; reasons in work/takes.json "why")
Every hook take opens with a bridge line ("And that's the difference", "Which is why people ask", "And that's the
style behind it", "And here's the thing", "It all starts with where Gane came from"). Only the claim is kept:
A "Most heavyweights stand and trade. Gane never does." B "Why do the biggest hitters in the UFC keep missing
Gane?" C "Ciryl Gane beat Alex Pereira at the White House in the UFC, and here's how he fights." D "Gane's best
weapon isn't his power, it's his distance." E "Ciryl Gane started in Muay Thai, and you can see it in his feet."
Takeaway: he says "spar bigger hitters"; Whisper hears "support"/"sport". Captioned SPAR, worth a listen.
`work/words.json` = each range transcribed on its own; Whisper's room-tone "Thank you." removed.

## B-roll (`work/broll.py` cuts, frames and places everything; sources in media/, not in the bank yet)
`yt-gane-pereira-full.mp4` (ILPWCCLb16E, UFC's own full-fight upload, broadcast) and `yt-gane-muaythai.mp4`
(XHHsuuML1yQ, his Muay Thai fights). Gane = white/red flag shorts, Pereira = blue. 1:1 crop over a dark blurred
copy, cutaways 0.12 s early.
Hooks: A, B Pereira's high kick, Gane leans out of it; C the finish at the cage and the stoppage; D the close
jab from range; E the Muay Thai kick. Body: bouncing, lunge in and straight out ("moves like a lightweight");
Pereira lunges with the right, Gane is already off the line ("a small step to the side"); the jab paw then the
kick from range ("a long jab and teep"); Pereira steps in and Gane's counter drops him, R2 4:23 ("he has
already moved and the counter lands"). Face kept for the intro, "the third one" and the takeaway.

## Check notes
From ~290 s of the long take the framing is wider (the jersey's yellow band shows), so the takeaway and CTA cut
to a wider shot than the rest. Left as is: it reads as a camera change. Flip confirmed on the 0228 take (Boca
jersey: swoosh on his right chest, crest on his left).
Day cards start 0.7 s after the CTA's last word (at 0.1 s the caption overlapped the first card). Plan day
headings kept to one or two short words: the card heading is 200 px and a long one pushes the list into the
footer ("Counter when they commit" did).

## Facts
TKO R2 (1:27) over Pereira at UFC Freedom 250, White House South Lawn, 14 June 2026 (theScore 3553975, SI).
Gane came up in Muay Thai (his Muay Thai fights are in the source). Plan `gane-distance` (new, docs/plans).

## Renders
`media/2026-11-17-gane-breakdown/2026-11-17-gane-breakdown-<V>(-phone).mp4`, cloud (Modal).
Lengths A 55.9, B 56.8, C 59.0, D 56.2, E 55.8 s. Queue: trial set `gane-breakdown`, approved false: A 26 Nov
16:00Z, D 26 Nov 20:30Z, B 27 Nov 16:00Z, C 27 Nov 20:30Z, E 28 Nov 16:00Z, after the Floyd trials.
