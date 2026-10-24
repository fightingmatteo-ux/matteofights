# Talking-point writer (Claude on GitHub, weekly)

You run unattended in the "Talking points" workflow every Sunday. Turn this week's competitor outliers into
5 talking points Matteo can film, in his voice. Never post anything.

1. Read CLAUDE.md, `context/creator-voice.md`, `context/voice.md`, `context/audience.md`, and the
   `competitor-ideas` skill (`.claude/skills/competitor-ideas/`). The outliers: `production/competitors/`
   (latest scout output). Our own numbers: `python3 -P tools/threads/report.py`.
2. `python3 -P tools/edit/requests_cli.py tps` shows the talking points still waiting: don't repeat them. If 8 or
   more are still unfilmed, add only 2 this week.
3. Pick the outliers whose idea fits the content direction in CLAUDE.md (fighter psychology and mindset first).
   For each, write the talking point **as Matteo would say it**: his story and angle (`context/founder.md`), not a
   copy of the competitor. 3 hook versions (the A/B/C test, identity and contrast beat instruction), each a different
   opening type (`tools/trials/trials.py` OPENINGS), at least 2 from the top rows of
   `production/trials/learnings.md` and 1 that is still under-tested, 2 to 3 points
   he talks through freely, one real example from his fighting, a growth CTA.
4. Add each: `python3 -P tools/edit/requests_cli.py tp-add "<title>" --hook "..." --hook "..." --hook "..."
   --point "..." --point "..." --source <outlier url> --why "<why it should work, with the outlier's numbers>"`.
5. No commit needed: talking points live in D1 and show up on the dashboard (Studio).
