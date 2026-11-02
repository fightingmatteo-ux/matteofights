#!/usr/bin/env bash
# Not a reel: free Mixkit stock b-roll for the plan reels, on Modal (this session can't reach mixkit.co).
#   bash make.sh search        -> prints vertical/horizontal results for the terms below (read it in the job log)
#   bash make.sh <mixkit id>   -> downloads that clip -> media/2026-11-02-stock/2026-11-02-stock-<id>.mp4 (+ 480p proxy)
set -euo pipefail
cd "$(dirname "$0")"
V="$1"; OUT="../../../media/2026-11-02-stock/2026-11-02-stock-$V.mp4"; mkdir -p "$(dirname "$OUT")"
MK=../../editing/reel-kit/scripts/mixkit.py
if [ "$V" = search ]; then
  python3 -P $MK search boxing boxer "punching bag" "boxing training" kickboxing "martial arts" mma fighter \
    "boxing gloves" "heavy bag" "exhausted athlete" "tired athlete" "tired runner" "out of breath" "jump rope" \
    sprint sprinting sweat "hard workout" "intense workout" "crossfit" "battle ropes" "burpees" "athlete resting" | tee search.txt
  ffmpeg -v error -y -f lavfi -i color=c=black:s=64x64:d=1 "$OUT"
else
  python3 -P $MK get tmp "$V"
  mv "tmp/mk$V.mp4" "$OUT"
fi
ffmpeg -v error -y -i "$OUT" -vf scale=-2:480 -c:v libx264 -crf 30 -preset veryfast -an "${OUT%.mp4}-phone.mp4"
ls -la "$OUT"
