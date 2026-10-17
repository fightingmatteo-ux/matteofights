#!/usr/bin/env bash
# Build + render a HyperFrames reel on any Linux box (laptop, cloud session, GitHub Action).
#   tools/video/reel_render.sh <slug> [A,B,C] [outdir]
# Needs the reel's working media in place first (tools/video/reel_work.sh pull <slug>).
# Per variant: build_variant.py <V> if the reel has one (else build.sh, rendered once), hyperframes check,
# delivery render to <outdir>/<name>-<V>.mp4 and a smaller <name>-<V>-phone.mp4 to send to a phone.
# <name> = slug without its date prefix (matches the release/Drive names, e.g. saenchai-bigger-men-A.mp4).
# CHECK=0 skips the check gate (only for a quick preview).
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
slug="${1:?slug}"; variants="${2:-A,B,C}"; out="${3:-media/$slug}"
case "$slug" in *[!a-zA-Z0-9._-]*) echo "slug must be a simple name" >&2; exit 1;; esac
dir="production/reels/$slug"; name="${slug#[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]-}"
[ -d "$dir" ] || { echo "no $dir" >&2; exit 1; }
HF="npx --yes hyperframes@0.8.147"

# Toolchain: carve (music under the voice) runs against worst-decision's @hyperframes/core.
[ -d production/reels/worst-decision/node_modules ] || (cd production/reels/worst-decision && npm ci --no-audit --no-fund)
[ -d "$dir/node_modules" ] || (cd "$dir" && npm i --no-audit --no-fund)
[ -f ~/.claude/skills/hyperframes-audio/scripts/carve.mjs ] || $HF skills update general-video > /dev/null

mkdir -p "$out"; out="$(realpath "$out")"
cd "$dir"
if [ -f build_variant.py ]; then vs="${variants//,/ }"; else vs="-"; fi
for V in $vs; do
  if [ "$V" = - ]; then file="$name"; bash build.sh; else file="$name-$V"; python3 -P build_variant.py "$V"; fi
  [ "${CHECK:-1}" = 0 ] || $HF check
  $HF render -q delivery -o "$out/$file.mp4"
  ffmpeg -v error -y -i "$out/$file.mp4" -c:v libx264 -crf 23 -c:a copy -movflags +faststart "$out/$file-phone.mp4"
  echo "rendered $out/$file.mp4"
done
