# How Matteo's reels should look (learned)

The edit worker reads this before every edit and adds to it after every revision (tools/edit/WORKER.md, "Learn").
One line per rule: `- [tag] rule (source, date)`. Tags: hook, text, cut, pacing, framing, color, audio, broll,
captions, other. A rule is general ("keep faces clear of text"), never about one clip. When a new note contradicts a
rule, rewrite the rule and say so in the source. The dashboard (Studio, "Your edit taste") shows these rules and
charts the revisions they came from.

## Rules

- [look] Editorial look is the default for talking heads: start from production/reels/_TEMPLATE/editorial/ (Matteo approved v5, 2026-10-20)
- [cut] Fewer jump cuts: keep a thought in one take unless the cut removes dead air (Saenchai re-cut notes, 2026-10-20)
- [broll] Fewer tape clips, each held longer: 7 instead of 11 in a 40 s reel (Saenchai re-cut notes, 2026-10-20)
- [pacing] No slow motion on fight tape (Saenchai re-cut notes, 2026-10-20)
- [framing] Leave headroom above the head so the top text never covers the face (editorial look, 2026-10-20)
- [text] Hook text never sits over a face; move it to the lower plate instead (listicle review, 6 clips swapped, 2026-10-20)
- [framing] Never post sideways footage: check rotation before render (09:00 batch review, 2026-10-25)
- [broll] No clips under 3 s in listicles: they break the renderer and read as glitches (2026-10-25)
- [cut] When a line was filmed more than once (long takes with repeats), pick the take with the most eye contact with the lens first, then the loudest and most expressive voice, then the one that sounds most natural (no reading tone, no stumble). Check every repeat, not just the last one (Matteo, 2026-11-16)
- [broll] Cover any stretch where he looks away from the lens with b-roll; keep his face on screen for the lines where he holds eye contact (Matteo, 2026-11-16)
- [broll] B-roll shows exactly what the words say at that moment: "sweep" shows the sweep, "standing on one leg" shows the man on one leg. No generic fight footage over a specific line (Matteo, 2026-11-16)
- [broll] Longer b-roll holds are fine when they cover a look-away or show a full move, as long as the cut in and out is clean (Matteo, 2026-11-16)
- [broll] A cutaway opens on the move the words name, with no lead-in action: at "Three. The sweep" the clip opened on the opponent's punch and read as an elbow (Matteo, Saenchai Ep. 1, 2026-11-17)
- [broll] Matteo asked for "a better hook clip" and "better b-roll footage" on Saenchai Ep. 1 (2026-11-17). Read as: sharp broadcast footage over handheld crowd video, and a hook clip where something happens in its first second (the reading is Claude's, he did not spell it out)
- [broll] "Now" footage must make him look sharp: real training sessions graded good in production/listicles/moments.json, never casual home shadowboxing, and never old beginner pad work outside the beginner years of a story (Matteo, origin pin, 2026-11-20)
- [broll] Kicks are fine right after "I can't jump": Matteo wants his sharpest kicks (bag high kick, head kick) on "but I can do this" (Matteo, origin pin, 2026-11-20; replaces Claude's earlier "never contradict the line" reading)
- [broll] No punching-bag combo clips (Fitness First red bag work read as weak, "ass"); for "sharp now" use kicks: kicking.mov high kick, Impact MMA roundhouses, the head kick clip (Matteo, origin pin, 2026-11-20)
- [cut] No cutaways under ~2 s in talking heads: 0.6 s flashes (a country montage) read as glitches; hold one clip over a list instead (Matteo, origin pin, 2026-11-20)
- [cut] Calm transitions on long talking heads: clean cuts, one steady slow push, no whip-blur entries, no 1.0/1.1 zoom alternation, no camera punches ("jumpy", "buggy"; Matteo, origin pin, 2026-11-20). Template: Editorial.animate(..., {calm: true})
- [audio] Never end a range on Whisper's word end: it lands early and clips the word ("audio cuts off"); keep 0.15-0.3 s past it (Matteo, origin pin, 2026-11-20)
- [color] Never add overlays or filters that change the footage's look: no dark shade gradients, no dimmed cutaways ("the colour looks graded and shit"). Caption readability comes from the text's own shadow only (Matteo, origin pin, 2026-11-20)
- [captions] Every spoken line has a caption on screen, including over cutaways: put captions in the front layer (plan.build behind=False) unless the cut-out runs the full length (Matteo: "a lot of captions are missing", 2026-11-20)
- [audio] When a line ends on a long word Whisper times short ("consistency"), keep the whole sentence or 0.5 s past it; he must hear every word finish (Matteo, 2026-11-20)
- [color] Always render SDR (`hyperframes render --sdr`): one iPhone-HDR cutaway switches the whole reel to HDR (HLG/BT.2020), and phones then show his face too bright and red ("the light looks weird and red"; Matteo, origin pin, 2026-11-20). Check with ffprobe: color_transfer must be bt709, not arib-std-b67
