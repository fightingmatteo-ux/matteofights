#!/usr/bin/env bash
# Editorial talking-head reel, one variant end to end:  bash make.sh A
#   assemble (work/takes.json) -> cut-out of Matteo (RVM) -> build.py -> render -> glitch check (re-renders once)
# Works in a cloud session and on the laptop (Git Bash). One variant at a time, never in parallel.
set -euo pipefail
cd "$(dirname "$0")"
V="${1:-A}"
K=../../editing/reel-kit/editorial
PY=$(command -v python3 || command -v python)
SLUG=$(basename "$PWD")
OUT="../../../media/$SLUG/$SLUG-$V.mp4"

[ -f "assets/media/aroll_$V.mp4" ] || "$PY" -P ../../editing/reel-kit/scripts/assemble.py work/takes.json "$V"
# fight tape cut to this variant's lines (needs media/saenchai-broll/ from the original research on the laptop)
"$PY" -P make_broll.py "$V"

if [ ! -f "assets/media/fg_${V}_full.webm" ]; then
  [ -d .venv ] || "$PY" -m venv .venv
  VPY=.venv/bin/python; [ -x "$VPY" ] || VPY=.venv/Scripts/python.exe
  "$VPY" -m pip install -q onnxruntime numpy
  [ -f rvm.onnx ] || curl -sSL -o rvm.onnx https://github.com/PeterL1n/RobustVideoMatting/releases/download/v1.0.0/rvm_mobilenetv3_fp32.onnx
  "$VPY" "$K/cutout.py" "assets/media/aroll_$V.mp4" "assets/media/fg_${V}_full.webm" --model rvm.onnx
fi

"$PY" -P build.py "$V"
mkdir -p "$(dirname "$OUT")"
render() { npx --yes hyperframes@0.8.147 render -q standard -w 4 -o "$OUT" 2>&1 | grep -E "rendered in|failed|rror" || true; }
render
"$PY" -I "$K/check_render.py" "$OUT" "assets/media/aroll_$V.mp4" || { echo "glitch: rendering again"; render; "$PY" -I "$K/check_render.py" "$OUT" "assets/media/aroll_$V.mp4"; }
ffmpeg -v error -y -i "$OUT" -c:v libx264 -crf 23 -preset slow -c:a copy -movflags +faststart "${OUT%.mp4}-phone.mp4"
echo "done: $OUT (+ -phone.mp4)"
