# Fighter Breakdown: Floyd Mayweather (shoulder roll), 5 hook variants

Source: 13 Pocket 3 clips in the Drive input folder (DJI 0197-0224, 17 Nov), one clip per section, each opening
with a spoken slate ("Floyd, take A"). Script in `../FILM-2026-11-16-month-shoot.md` (FLOYD). Clips prepped
(`prep_footage.sh`), joined into `media/floyd-ep-src/raw.mp4` (offsets in `list.txt` there) and flipped
horizontally: every clip was mirrored (the shirt sponsor read backwards). Git-ignored, rebuild from Drive.
Template copied from `2026-11-16-loma-breakdown/`. On-screen tag FIGHTER BREAKDOWN, no episode number (spoken
"Episode 3" cut out, as in Loma). Bed = the series bed (epic-bold-drums).

Structure per variant: hook (A-E), intro, body (50-0, shoulder roll), One, Two, the third one, Three (pull
counter), takeaway, plan cards, CTA. Only the hook differs. Lengths: A 83.1 s, B 83.7 s, C 82.9 s, D 82.1 s,
E 81.0 s.

## Takes (raw.mp4 seconds; full reasons in work/takes.json "why")
Only one take per section, so the work was the cut points: every range starts after the slate, onsets from the
audio energy (Whisper smears the first word after a slate by up to 1.5 s). `work/words.json` = each range
transcribed on its own (clean word times). Whisper heard "Thank you very much" in the room tone: removed.
Hook C runs past the sheet: "50 fights in 50 wins. He barely got hit clean. Here's the difference."
Room tone 60.2-63.0 (the body clip's silence) after "Monday to Friday" gives the 5 day cards 0.65 s each.

## B-roll (`work/broll.py` cuts, frames and places everything; sources in media/, not in the bank yet)
`yt-floyd-defense-highlights.mp4` (bQYeSXpC244, Canelo 2013 broadcast) and `yt-floyd-pull-counter.mp4`
(CxNZS5A59kg, Marquez 2009). Sharp 4:5 or 1:1 crop over a dark blurred copy, cutaways 0.12 s early.
Hooks: A Canelo's punches land on the raised shoulder ("but everyone ended up hitting Floyd's shoulders"); B-E
the same Marquez pull counter (throw, lean out, right hand back), so the hook test compares words, not clips.
Body: Floyd celebrating ("Floyd retired fifty-zero"), the shell at the ropes ("it's the shoulder roll"),
Canelo's right on the shoulder ("his right hand lands on your shoulder"), lead hand low ("Two. His lead hand",
2.0 s, the shot is short), pull counter on Marquez ("when you throw"), the right hand straight back
("his right hand is already coming straight back"). Face kept for the intro, "the third one" and the takeaway.

## Check notes
The red keyword "counter" collided with the FIGHTER BREAKDOWN tag (his head is high in that clip): dropped from
`keys`. Local check needs the real cut-out (`fg_<V>_full.webm`); a stand-in hides layout errors.
He says "miss by 1cm" (sheet: "an inch"); left as spoken.

## Facts
50-0, retired 2017 (Wikipedia). Shoulder roll / pull counter description matches the plan `floyd-shoulder-roll`.

## Renders
`media/2026-11-17-floyd-breakdown/2026-11-17-floyd-breakdown-<V>(-phone).mp4`, cloud (Modal). Queue: trial set
`floyd-breakdown`, approved false: A 23 Nov 16:00Z, D 23 Nov 20:30Z, B 24 Nov 16:00Z, C 24 Nov 20:30Z,
E 25 Nov 16:00Z (11:00 and 15:30 New York), after the Lomachenko trials (20 to 22 Nov).
Rescheduled 2026-11-17 (Matteo: 3 a day, Europe/US overlap only, 11:00/14:30/16:00 NY): A 22 Nov 19:30Z, D 22 Nov 21:00Z, B 23 Nov 16:00Z, C 23 Nov 19:30Z, E 23 Nov 21:00Z.
