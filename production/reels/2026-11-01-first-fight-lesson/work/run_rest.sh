#!/usr/bin/env bash
set -e
cd "$(dirname "$0")/.."
M=../../../media/2026-11-01-first-fight-lesson
for V in "$@"; do
  python3 -P make_broll.py $V
  [ -f assets/media/fg_${V}_full.webm ] || .venv/bin/python ../../editing/reel-kit/editorial/cutout.py assets/media/aroll_$V.mp4 assets/media/fg_${V}_full.webm --model rvm.onnx | tail -1
  python3 -P build.py $V
  OUT=$M/2026-11-01-first-fight-lesson-$V.mp4
  rm -f $OUT
  for try in 1 2 3; do
    npx --yes hyperframes@0.8.147 render -q standard -w 3 -o $OUT 2>&1 | grep -E "rendered in|failed" || true
    [ -s $OUT ] && break
    echo "render failed, retry $try"; sleep 3
  done
  python3 -I ../../editing/reel-kit/editorial/check_render.py $OUT assets/media/aroll_$V.mp4 1.5 black || { npx --yes hyperframes@0.8.147 render -q standard -w 4 -o $OUT 2>&1 | grep -E "rendered in|failed"; python3 -I ../../editing/reel-kit/editorial/check_render.py $OUT assets/media/aroll_$V.mp4 1.5 black; }
  ffmpeg -v error -y -i $OUT -c:v libx264 -crf 23 -preset slow -c:a copy -movflags +faststart ${OUT%.mp4}-phone.mp4
  echo "DONE $V"
done
