#!/usr/bin/env bash
# Steal from Legends Ep 2: download the Lomachenko fight footage on the LAPTOP (YouTube blocks cloud machines)
# and put it on the "media" release so Claude can pick the moments from a cloud session.
#
#   bash production/reels/2026-10-25-legends-ep2-lomachenko/get_footage.sh
#
# Official Top Rank Boxing uploads only (same footage everyone uses, from the rights holder's own channel).
# 720p is enough: the clips run as a "tape" panel (full 16:9 frame inside the vertical reel), so both fighters'
# feet stay visible for the highlight graphics. Needs: python + pip, ffmpeg, gh (logged in), node (for yt-dlp).
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
python -m pip install -q -U "yt-dlp[default]"
mkdir -p media/loma
for pair in \
  rigo:yvu2ch3U7Fo \
  walters:0igs8QLwXiU \
  marriaga:zRqFwCKasHI \
  linares:1PVKL1bY6nw ; do
  n=${pair%%:*}; id=${pair#*:}
  f="media/loma/loma-$n-toprank.mp4"
  if [ ! -s "$f" ]; then
    yt-dlp -f "bv*[height<=720][ext=mp4]+ba[ext=m4a]/b[height<=720]" --merge-output-format mp4 \
      -o "$f" "https://www.youtube.com/watch?v=$id"
  fi
  bash tools/video/media.sh push "$f"
done
echo "DONE. Tell Claude: footage is up."
