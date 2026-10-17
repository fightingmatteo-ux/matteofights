#!/usr/bin/env bash
# Turn raw phone footage into a reel's starting point (PIPELINE.md steps 3-4, before Claude picks takes).
#   tools/video/reel_ingest.sh <slug> <clip> [clip ...]
# Creates production/reels/<slug>/ from _TEMPLATE if missing, then:
#   assets/raw.mp4    prep_footage.sh (neutral colour, HDR/full-range fixed); several clips are joined in order
#   assets/voice.wav  the original recording's audio, untouched (takes.json audio_src)
#   work/words.json + work/transcript.txt   Whisper word timings (model: WHISPER=medium.en)
# Runs in the Reel studio Action (cloud sessions can't download Whisper models) or on the laptop.
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
slug="${1:?slug}"; shift
[ $# -gt 0 ] || { sed -n 2,9p "$0"; exit 1; }
case "$slug" in *[!a-zA-Z0-9._-]*) echo "slug must be a simple name" >&2; exit 1;; esac
dir="production/reels/$slug"; kit=production/editing/reel-kit/scripts
[ -d "$dir" ] || { cp -r production/reels/_TEMPLATE "$dir"; sed -i "s/^slug:.*/slug: $slug/" "$dir/REEL.md" || true; }
mkdir -p "$dir/assets" "$dir/work"
tmp=$(mktemp -d)

i=0; : > "$tmp/v.txt"; : > "$tmp/a.txt"
for clip in "$@"; do
  i=$((i + 1))
  bash "$kit/prep_footage.sh" "$clip" "$tmp/v$i.mp4"
  ffmpeg -v error -y -i "$clip" -map 0:a:0 -vn -c:a pcm_s16le -ar 48000 "$tmp/a$i.wav"
  echo "file '$tmp/v$i.mp4'" >> "$tmp/v.txt"; echo "file '$tmp/a$i.wav'" >> "$tmp/a.txt"
done
ffmpeg -v error -y -f concat -safe 0 -i "$tmp/v.txt" -c copy -movflags +faststart "$dir/assets/raw.mp4"
ffmpeg -v error -y -f concat -safe 0 -i "$tmp/a.txt" -c copy "$dir/assets/voice.wav"
rm -rf "$tmp"

python3 -P "$kit/transcribe.py" "$dir/assets/raw.mp4" "$dir/work/words.json" "${WHISPER:-medium.en}" \
  | tee "$dir/work/transcript.txt"
echo "ingested $i clip(s) into $dir"
