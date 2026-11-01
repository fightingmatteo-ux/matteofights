# Take map: 2026-11-01 first-fight-lesson

Source: `assets/raw.mp4` (prepped, same timeline as `media/first-fight-lesson/raw.mp4`, 268.87 s, 1440x2560 HEVC -> 1080x1920, 30 fps).

**Transcript source: NOT a local medium.en run.** huggingface.co is blocked from this machine (403 from the egress proxy), so no Whisper model could be downloaded. Words/text come from the GitHub `fetch-video` run (`faster-whisper` small, VAD on), saved as `work/gh_words.json`, `work/gh_transcript.txt` (and copied to `work/words.json` in the transcribe.py format).

Whisper small word START times are unreliable at the start of a phrase (often 0.3-1.0 s early; end times are good). **All take start/end and all pauses below are measured from the audio energy envelope** (voiced = RMS > -39 dBFS, noise floor ~ -48 dB; `work/takes_energy.json`). `end` = last voiced frame + 0.10 s natural tail. Word-level text is small.en and can contain mishears; items marked 'verify by ear' need a listen.

## Summary table

| Take | start | end | dur | mean dB / p90 dB | words/s | pick |
|---|---|---|---|---|---|---|
| Body 1 | 2.97 | 27.14 | 24.17 | -28.4 / -20.8 | 3.27 | alt |
| Body 2 | 31.03 | 54.58 | 23.55 | -29.8 / -23.5 | 3.48 |  |
| Body 3 | 58.84 | 80.79 | 21.95 | -27.9 / -20.2 | 3.55 | BEST |
| Loop A 1 | 83.84 | 95.58 | 11.74 | -27.4 / -19.3 | 3.49 | BEST |
| Loop A 2 | 96.73 | 107.91 | 11.18 | -26.9 / -18.8 | 3.67 | alt |
| Loop B 1 | 109.13 | 120.86 | 11.73 | -26.5 / -18.3 | 3.58 | BEST |
| Loop B 2 | 121.91 | 132.82 | 10.91 | -27.4 / -19.6 | 3.94 |  |
| Loop C 1 | 134.19 | 145.57 | 11.38 | -26.9 / -19.0 | 3.25 |  |
| Loop C 2 | 146.63 | 158.15 | 11.52 | -26.2 / -18.1 | 3.21 | BEST |
| Loop C 3 | 159.18 | 169.58 | 10.40 | -26.9 / -19.3 | 3.75 | alt |
| Loop D 1 | 170.65 | 180.87 | 10.22 | -27.4 / -19.9 | 3.52 | BEST |
| Loop D 2 | 181.67 | 191.78 | 10.11 | -27.8 / -19.7 | 3.56 | alt |
| Loop E 1 | 192.75 | 203.30 | 10.55 | -28.2 / -20.3 | 3.13 |  |
| Loop E 2 | 204.41 | 214.76 | 10.35 | -28.1 / -19.6 | 3.48 | BEST |
| Share 1 | 217.76 | 223.62 | 5.86 | -23.4 / -14.7 | 3.24 |  |
| Share 2 | 226.35 | 231.39 | 5.04 | -23.2 / -15.1 | 3.77 | BEST |
| Share 3 | 234.12 | 239.14 | 5.02 | -24.2 / -15.7 | 3.78 |  |
| Follow 1 | 241.75 | 248.98 | 7.23 | -26.1 / -16.8 | 3.32 | BEST |
| Follow 2 | 252.14 | 259.17 | 7.03 | -26.3 / -18.5 | 3.41 | alt |
| Follow 3 | 261.67 | 268.98 | 7.31 | -26.7 / -17.1 | 3.83 |  |

Level is mean of voiced 10 ms frames (higher = louder/more energy). Loud + fast + few pauses = punchier delivery (judged from audio loudness only, not heard).

## Slates

Slate said before the take (energy-located); loops B-E have NO slate at all, mapped by content and order (two takes each, C has three). Order in file: Body x3, Loop A x2, B x2, C x3, D x2, E x2, Share x3, Follow x3.

- Body 1: 'Body one' 1.5-2.1
- Body 2: not transcribed; voiced blip 28.9-29.8 (probably 'Body two')
- Body 3: 'Body three' 57.4-58.0
- Loop A 1: 'Loop A' 82.6-83.3 (no number said)
- Loop A 2: none heard
- Loop B 1: none heard
- Loop B 2: none heard
- Loop C 1: none heard
- Loop C 2: none heard
- Loop C 3: none heard (EXTRA third C take)
- Loop D 1: none heard
- Loop D 2: none heard
- Loop E 1: none heard
- Loop E 2: none heard
- Share 1: 'Share one' 215.8-217.0
- Share 2: 'Share two' 224.8-225.9
- Share 3: 'Share three' 232.8-233.8
- Follow 1: 'Follow one' 240.4-241.4
- Follow 2: 'Follow two' 250.6-251.5
- Follow 3: 'Follow three' 260.5-261.2

## Bridge-to-hook gaps in loop takes (flag: gap > 0.25 s)

Measured silence between the bridge words and the first word of the hook. Trim these in the edit (they break the 'one breath' seam).

| Take | seam | silence at (s) | gap |
|---|---|---|---|
| Loop A 1 | 'And I would know' -> 'I knocked him out' | 89.10-89.55 | 0.45 s  **GAP > 0.25** |
| Loop A 2 | 'And I'd know' -> 'Knocked him out' | 101.34-101.86 | 0.52 s  **GAP > 0.25** |
| Loop B 1 | 'And I'd know' -> 'my first fight ended' | 114.19-114.49 | 0.30 s  **GAP > 0.25** |
| Loop B 2 | 'And I know' -> 'my first fight ended' | 126.43-126.85 | 0.42 s  **GAP > 0.25** |
| Loop C 1 | 'So you tell me' -> 'shouldn't/Should a knockout' | 139.18-139.86 | 0.68 s  **GAP > 0.25** (large) |
| Loop C 2 | 'So you tell me' -> 'shouldn't/Should a knockout' | 151.98-152.41 | 0.43 s  **GAP > 0.25** |
| Loop C 3 | 'So you tell me.' -> 'Should a knockout' | 163.53-164.11 | 0.58 s  **GAP > 0.25** |
| Loop D 1 | 'That's why' -> 'my first knockout' | none (no silence >= 0.1 s) | 0 s  OK (seam from 'earn it.' to 'That's' also tight) |
| Loop D 2 | 'That's why' -> 'my first knockout' | none (no silence >= 0.1 s) | 0 s  OK (but 0.47 s pause BEFORE the bridge: 'earn it.' -> 'That's' at 185.61-186.08) |
| Loop E 1 | '(I) learned that from' -> 'one punch' | none | 0 s OK, but 0.56 s pause BEFORE 'Learned' (196.89-197.45) and the 'I' looks missing |
| Loop E 2 | 'I learned that from' -> 'one punch' | 209.69-210.02 | 0.33 s  **GAP > 0.25** |

Also: every loop take has a pause between the end of the hook and 'I was 16...' (0.26-0.56 s, listed per take below); the loop is meant to be one breath with no pause.

## Per-take detail

### Body 1  [2.97 - 27.14]  (24.17 s)  (backup)
- Slate: 'Body one' 1.5-2.1
- Transcript (small.en): "I was 16 my first fight his sixth Someone told me knock him out or you're gonna lose so I hunted him the ref steps in to separate us And I throw the right hand anyways. He's out They called it a draw and to be honest They should have disqualified me because I thought fighting was about hurting people But in reality, it's about control if you break the rules to get the knockout. You didn't earn it"
- Flubs / changes vs teleprompter: 'you're gonna lose' (script: 'you lose'); adds 'and to be honest'; 'They should have disqualified me because I thought...' fuses two script lines; adds 'But in reality,' before 'it's about control'; no flub/restart. Complete.
- Pauses > 0.7 s inside: none
- Pauses 0.25-0.7 s: 5.41-5.98 (0.57, 'sixth' -> 'Someone'), 8.47-8.74 (0.27, 'lose' -> 'so'), 10.08-10.45 (0.37, 'him' -> 'the'), 13.93-14.19 (0.26, 'anyways.' -> 'He's'), 15.03-15.58 (0.55, 'out' -> 'They'), 16.55-16.83 (0.28, 'draw' -> 'and'), 21.03-21.44 (0.41, 'people' -> 'But'), 22.19-22.45 (0.26, 'reality,' -> 'it's'), 23.28-23.74 (0.46, 'control' -> 'if')

### Body 2  [31.03 - 54.58]  (23.55 s)
- Slate: not transcribed; voiced blip 28.9-29.8 (probably 'Body two')
- Transcript (small.en): "I was 16. It was my first fight. It was his sixth and someone told me knock him out or you lose So I hunted him the ref steps in to separate us and I throw the right hand anyways He's out. They called it a draw and to be honest They should have disqualified me because I thought fighting was about hurting people in reality It's about control if you break the rules to get the knockout. You didn't earn it"
- Flubs / changes vs teleprompter: Re-ordered/rephrased open: 'I was 16. It was my first fight. It was his sixth and someone told me...' (script: 'I was sixteen. My first fight. His sixth. Someone told me:'); 'and I throw' (script 'And'); adds 'and to be honest'; 'because I thought...'; 'people in reality It's about control' (drops 'But'). Complete but furthest from script.
- Pauses > 0.7 s inside: none
- Pauses 0.25-0.7 s: 34.18-34.83 (0.65, 'sixth' -> 'and'), 37.19-37.57 (0.38, 'lose' -> 'So'), 38.81-39.32 (0.51, 'him' -> 'the'), 49.14-49.56 (0.42, 'people' -> 'in'), 51.35-51.78 (0.43, 'control' -> 'if')

### Body 3  [58.84 - 80.79]  (21.95 s)  <- RECOMMENDED
- Slate: 'Body three' 57.4-58.0
- Transcript (small.en): "I was 16 my first fight his sixth Someone told me knock him out or you lose so I hunted him the ref steps in to separate us And I throw the right hand anyways. He's out They called it a draw and to be honest They should have disqualified me because I thought fighting was about hurting people But in reality, it's about control if you break the rules to get the knockout. You didn't earn it"
- Flubs / changes vs teleprompter: Closest to script on the 'you lose' line. Still adds 'and to be honest', fuses 'disqualified me because I thought', adds 'But in reality,'. No flub/restart. Complete.
- Pauses > 0.7 s inside: none
- Pauses 0.25-0.7 s: 61.02-61.53 (0.51, 'sixth' -> 'Someone'), 64.96-65.54 (0.58, 'him' -> 'the'), 69.69-70.12 (0.43, 'out' -> 'They'), 71.12-71.56 (0.44, 'draw' -> 'and'), 73.51-73.91 (0.40, 'me' -> 'because'), 77.87-78.32 (0.45, 'control' -> 'if')

### Loop A 1  [83.84 - 95.58]  (11.74 s)  <- RECOMMENDED
- Slate: 'Loop A' 82.6-83.3 (no number said)
- Transcript (small.en): "it's about control if you break the rules to get a knockout You didn't earn it and I would know I knocked him out in my first fight and it shouldn't have counted I was 16 my first fight his sixth"
- Flubs / changes vs teleprompter: 'get a knockout' (script 'the'); 'and I would know' (script 'And I'd know'); tail 'I was 16 my first fight his sixth' ok. Complete.
- Pauses > 0.7 s inside: none
- Pauses 0.25-0.7 s: 89.10-89.55 (0.45, 'know' -> 'I'), 92.47-92.78 (0.31, 'counted' -> 'I'), 94.74-95.00 (0.26, 'fight' -> 'his')

### Loop A 2  [96.73 - 107.91]  (11.18 s)  (backup)
- Slate: none heard
- Transcript (small.en): "It's about control if you break the rules to get a knockout. You didn't earn it and I'd know I Knocked him out in my first fight and it shouldn't have counted. I was 16 my first fight and his sixth"
- Flubs / changes vs teleprompter: 'get a knockout' (script 'the'); 'I'd know' ok; tail 'my first fight AND his sixth' (extra 'and'). Complete.
- Pauses > 0.7 s inside: none
- Pauses 0.25-0.7 s: 101.34-101.86 (0.52, 'know' -> 'I'), 104.78-105.09 (0.31, 'counted.' -> 'I')

### Loop B 1  [109.13 - 120.86]  (11.73 s)  <- RECOMMENDED
- Slate: none heard
- Transcript (small.en): "It's about control if you break the rules to get the knockout You didn't earn it and I'd know my first fight ended in a knockout and I'm the one who should have lost I was 16 my first fight his sixth"
- Flubs / changes vs teleprompter: Matches script ('the knockout', 'I'd know', hook, tail). Clean.
- Pauses > 0.7 s inside: none
- Pauses 0.25-0.7 s: 110.16-110.45 (0.29, 'control' -> 'if'), 114.19-114.49 (0.30, 'know' -> 'my'), 117.65-118.10 (0.45, 'lost' -> 'I')

### Loop B 2  [121.91 - 132.82]  (10.91 s)
- Slate: none heard
- Transcript (small.en): "It's about control if you break the rules to get the knockout You didn't earn it and I know my first fight ended in a knockout and I'm the one who should have lost I was 16 my first fight in his sixth"
- Flubs / changes vs teleprompter: Transcribed 'and I know' (script 'I'd know'; may be mishear, check by ear); tail 'my first fight IN his sixth' (script 'His sixth'; may be mishear).
- Pauses > 0.7 s inside: none
- Pauses 0.25-0.7 s: 126.43-126.85 (0.42, 'know' -> 'my'), 129.92-130.35 (0.43, 'lost' -> 'I')

### Loop C 1  [134.19 - 145.57]  (11.38 s)
- Slate: none heard
- Transcript (small.en): "it's about control if you break the rules to get the knockout you didn't earn it so you tell me shouldn't knockout count if the refs already in between I was 16 my first fight his sixth"
- Flubs / changes vs teleprompter: Hook transcribed 'shouldn't knockout count if the refs already in between' (script 'Should a knockout count if the ref's already in between?'); probably a mishear of 'Should a', verify by ear. Rest matches.
- Pauses > 0.7 s inside: none
- Pauses 0.25-0.7 s: 135.24-135.53 (0.29, 'control' -> 'if'), 139.18-139.86 (0.68, 'me' -> 'shouldn't'), 142.35-142.86 (0.51, 'between' -> 'I'), 143.80-144.05 (0.25, '16' -> 'my')

### Loop C 2  [146.63 - 158.15]  (11.52 s)  <- RECOMMENDED
- Slate: none heard
- Transcript (small.en): "it's about control if you break the rules to get the knockout you didn't earn it so you tell me shouldn't knockout count if the refs already in between I was 16 my first fight his sixth"
- Flubs / changes vs teleprompter: Same hook transcription as C 1 ('shouldn't knockout count'); verify by ear. Rest matches.
- Pauses > 0.7 s inside: none
- Pauses 0.25-0.7 s: 147.58-148.01 (0.43, 'control' -> 'if'), 151.98-152.41 (0.43, 'me' -> 'shouldn't'), 155.12-155.38 (0.26, 'between' -> 'I')

### Loop C 3  [159.18 - 169.58]  (10.40 s)  (backup)
- Slate: none heard (EXTRA third C take)
- Transcript (small.en): "It's about control. If you break the rules to get the knockout, you didn't earn it, so you tell me. Should a knockout count if the refs are already in between? I was 16, my first fight is 6th."
- Flubs / changes vs teleprompter: EXTRA take (3 C takes). Transcribed cleanly: 'Should a knockout count if the refs are already in between?'; 'refs are' vs script 'ref's'; tail transcribed 'my first fight is 6th' (probably 'his sixth').
- Pauses > 0.7 s inside: none
- Pauses 0.25-0.7 s: 163.53-164.11 (0.58, 'me.' -> 'Should'), 166.57-167.06 (0.49, 'between?' -> 'I')

### Loop D 1  [170.65 - 180.87]  (10.22 s)  <- RECOMMENDED
- Slate: none heard
- Transcript (small.en): "It's about control. If you break the rules to get the knockout, you didn't earn it. That's why my first knockout is the one I'm least proud of. I was 16, my first fight is 6th."
- Flubs / changes vs teleprompter: Matches script. Tail transcribed 'my first fight is 6th' (probably 'his sixth', verify).
- Pauses > 0.7 s inside: none
- Pauses 0.25-0.7 s: 171.56-171.83 (0.27, 'control.' -> 'If'), 177.77-178.33 (0.56, 'of.' -> 'I')

### Loop D 2  [181.67 - 191.78]  (10.11 s)  (backup)
- Slate: none heard
- Transcript (small.en): "It's about control. If you break the rules to get the knockout, you didn't earn it. That's why my first knockout is the one i'm least proud of i was 16 my first fight his sixth"
- Flubs / changes vs teleprompter: Matches script. Complete.
- Pauses > 0.7 s inside: none
- Pauses 0.25-0.7 s: 185.61-186.08 (0.47, 'it.' -> 'That's'), 189.08-189.41 (0.33, 'of' -> 'i')

### Loop E 1  [192.75 - 203.30]  (10.55 s)
- Slate: none heard
- Transcript (small.en): "It's about control if you break the rules to get the knockout you didn't earn it Learned that from one punch half a second too late. I was 16 my firstembide his sixth"
- Flubs / changes vs teleprompter: 'I' appears to be missing: 'Learned that from one punch half a second too late' (script 'I learned that from'); transcript tail garbled ('firstembide'), verify by ear.
- Pauses > 0.7 s inside: none
- Pauses 0.25-0.7 s: 193.82-194.24 (0.42, 'control' -> 'if'), 196.89-197.45 (0.56, 'it' -> 'Learned'), 199.23-199.59 (0.36, 'punch' -> 'half'), 200.61-200.86 (0.25, 'late.' -> 'I')

### Loop E 2  [204.41 - 214.76]  (10.35 s)  <- RECOMMENDED
- Slate: none heard
- Transcript (small.en): "It's about control if you break the rules to get the knockout you didn't earn it I learned that from one punch half a second too late. I was 16 my first fight in his sixth"
- Flubs / changes vs teleprompter: Matches script ('I learned that from one punch. Half a second too late.'). Tail 'my first fight IN his sixth' (script 'His sixth'; may be mishear).
- Pauses > 0.7 s inside: none
- Pauses 0.25-0.7 s: 208.44-208.77 (0.33, 'it' -> 'I'), 209.69-210.02 (0.33, 'from' -> 'one'), 211.92-212.39 (0.47, 'late.' -> 'I')

### Share 1  [217.76 - 223.62]  (5.86 s)
- Slate: 'Share one' 215.8-217.0
- Transcript (small.en): "If you know someone with their first fight coming up, send them this. Here's what I wish I knew."
- Flubs / changes vs teleprompter: Matches script word for word.
- Pauses > 0.7 s inside: none
- Pauses 0.25-0.7 s: 220.47-220.73 (0.26, 'up,' -> 'send'), 221.77-222.12 (0.35, 'this.' -> 'Here's')

### Share 2  [226.35 - 231.39]  (5.04 s)  <- RECOMMENDED
- Slate: 'Share two' 224.8-225.9
- Transcript (small.en): "If you know someone with their first fight coming up, send them this. Here's what I wish I knew."
- Flubs / changes vs teleprompter: Matches script word for word.
- Pauses > 0.7 s inside: none
- Pauses 0.25-0.7 s: 229.82-230.15 (0.33, 'this.' -> 'Here's')

### Share 3  [234.12 - 239.14]  (5.02 s)
- Slate: 'Share three' 232.8-233.8
- Transcript (small.en): "If you know someone with their first fight coming up, send them this. Here's what I wish I knew."
- Flubs / changes vs teleprompter: Matches script word for word.
- Pauses > 0.7 s inside: none
- Pauses 0.25-0.7 s: 236.49-236.79 (0.30, 'up,' -> 'send'), 237.59-237.92 (0.33, 'this.' -> 'Here's')

### Follow 1  [241.75 - 248.98]  (7.23 s)  <- RECOMMENDED
- Slate: 'Follow one' 240.4-241.4
- Transcript (small.en): "And if you think that's bad, wait till you hear about my appendix. It burst the day before a fight. Follow. That one's next."
- Flubs / changes vs teleprompter: Matches script ('Follow. That one's next.'). Clean.
- Pauses > 0.7 s inside: none
- Pauses 0.25-0.7 s: 247.31-247.78 (0.47, 'fight.' -> 'Follow.')

### Follow 2  [252.14 - 259.17]  (7.03 s)  (backup)
- Slate: 'Follow two' 250.6-251.5
- Transcript (small.en): "And if you think that's bad, wait till you hear about my appendix. It burst the day before a fight. Follow. That one's next."
- Flubs / changes vs teleprompter: Matches script.
- Pauses > 0.7 s inside: none
- Pauses 0.25-0.7 s: 257.32-257.74 (0.42, 'fight.' -> 'Follow.')

### Follow 3  [261.67 - 268.98]  (7.31 s)
- Slate: 'Follow three' 260.5-261.2
- Transcript (small.en): "And if you think that's bad, wait till you hear about my appendix. It burst the day before a fight night. Okay, follow me because that one's next."
- Flubs / changes vs teleprompter: FLUB: 'It burst the day before a fight night. Okay, follow me because that one's next.' (script: 'a fight. Follow, that one's next.'). Not usable as is.
- Pauses > 0.7 s inside: 266.16-266.89 (0.73 s, 'Okay,' -> 'follow')
- Pauses 0.25-0.7 s: 

## Recommended best take per label

- **Body**: Body 3. closest to script ('or you lose'), tightest (21.95 s), no pause > 0.6 s, energy on par with Body 1. Body 1 is the backup ('you're gonna lose' is off-script); Body 2 rewrites the opening.
- **Loop A**: Loop A 1. tail matches script and smaller bridge gap (0.45 vs 0.52); A 2 is slightly louder but adds 'and his sixth'. Both need the 'know' -> 'I' gap trimmed.
- **Loop B**: Loop B 1. only take that matches script exactly; smallest bridge gap among the non-D/E loops (0.30 s).
- **Loop C**: Loop C 2. loudest/most energetic take (-26.2 mean), smallest bridge gap of the C's (0.43 s) and only 0.26 s pause before 'I was 16'. C 3 (0.58 s bridge gap) is the backup; confirm by ear whether C 1/2 say 'Should a' or 'shouldn't'.
- **Loop D**: Loop D 1. zero gap across 'earn it. That's why my first knockout' (the seam the loop needs); trim the 0.56 s pause before 'I was 16'. D 2 is the backup (tail pause only 0.33 s but 0.47 s pause before the bridge).
- **Loop E**: Loop E 2. complete and script-exact ('I learned that from'); needs the 0.33 s 'from'->'one' gap and 0.47 s tail pause trimmed. E 1 has no gap before the hook but seems to drop the 'I' and has a 0.56 s pause before 'Learned': verify by ear.
- **Share**: Share 2. word-perfect, shortest (5.04 s), only one pause (0.33 s before 'Here's'), energy within ~0.2 dB of the others.
- **Follow**: Follow 1. word-perfect, loudest of the three (-26.1 mean), no pause before 'That one's next'. Follow 2 is the backup; Follow 3 is flubbed ('fight night. Okay, follow me because...').

## Other notes

- Between takes there is only silence/room tone; no restart, cough or false start anywhere except the Follow 3 flub.
- 'Loop C' was recorded 3 times; every other loop twice.
- Voiced frames run to the very end of the file (268.88 s, Follow 3 tail); irrelevant unless Follow 3 is used.
