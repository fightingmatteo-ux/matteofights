# Fight-clip bank (real fight footage for b-roll)

Rule (Matteo 2026-11-02): b-roll on plan reels is REAL fight footage, a different clip per hook, matching the words;
iconic moments for named fighters. No stock footage.

## Where footage comes from (in this order)
1. **This bank** (`bank.json`): every downloaded source with tagged moments (fighter, action, seconds). Reuse first.
2. **YouTube via Matteo's laptop** (Remote Control, the durable route): connect to the laptop folder and run
   `yt-dlp --cookies-from-browser chrome -f "bv*[height<=1080]+ba/b" --merge-output-format mp4 -o media/<name>.mp4 <url>`
   from his home connection, then `tools/video/media.sh push media/<name>.mp4`. Nothing to export or refresh.
   Batch every download a week of reels needs in one session. Setup (once): Claude desktop app -> Settings ->
   Claude Code -> Remote Control -> add the matteofights folder.
3. **Fetch video workflow with `YT_COOKIES`** (fallback): works for 1-2 downloads, then YouTube flags cookies used from
   GitHub's IPs. Re-export from a private window if needed. Needs Deno (installed by the workflow).
4. **Official Instagram accounts** via `ig-browse.yml` (Business Discovery): recent fights only (e.g. @ufc knockouts).

Never use bot-check workarounds (alternate player clients, IP rotation): refused, and not needed with route 2.

## Using a clip
Pick exact seconds with a 10 s grid, then 4 fps 9:16 strips (see the 2026-11-02 session). Wire it into
`tools/planreel/editorial.py` REELS `hook` (spliced under the hook word, so the word sits behind the fighters) or
`clips` (cutaways). Long sources are trimmed on the runner by the reel's `work/precut.sh`.
