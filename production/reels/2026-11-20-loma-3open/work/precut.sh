#!/usr/bin/env bash
# Cuts this reel's cutaways from the big sources into assets/broll/b_<name>.mp4 (1080x1920, no audio), and builds the
# a-rolls if they aren't there yet. Run from anywhere; Submit render runs it on the runner before packing, after
# fetching the sources from the media release:
#   media: loma-breakdown-src.mp4=media/loma-breakdown-src/raw.mp4 broll-pads-chaiya.mp4=media/loma-src/broll-pads-chaiya.mp4
#          yt-loma-highlights.mp4=media/loma-src/yt-loma-highlights.mp4 yt-loma-angles-footwork.mp4=media/loma-src/yt-loma-angles-footwork.mp4
#          yt-loma-skillr.mp4=media/loma-src/yt-loma-skillr.mp4
# The original b-roll (yt-loma-how-he-trained, -rigondeaux-stool, -toprank-highlight-reel) isn't on the release and
# YouTube blocks runners, so these are re-picked from the sources that are (checked frame by frame 2026-11-19).
set -euo pipefail
cd "$(dirname "$0")/.."
S=../../../media/loma-src
mkdir -p assets/broll
cut() {  # name source start dur crop-center-x (0-1, of the 16:9 frame; "-" = already vertical)
  local out="assets/broll/b_$1.mp4"
  [ -f "$out" ] && return 0
  if [ "$5" = "-" ]; then vf="scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920"
  else vf="crop=w=ih*9/16:h=ih:x=max(0\,min(iw-ih*9/16\,iw*$5-ih*9/32)),scale=1080:1920"; fi
  ffmpeg -v error -y -ss "$3" -t "$4" -i "$S/$2" -vf "$vf,setsar=1,fps=30" -an -c:v libx264 -crf 18 -preset medium -pix_fmt yuv420p "$out"
  echo "b_$1: $2 @ $3 +$4"
}
cut pads  broll-pads-chaiya.mp4        4.40  2.30 -      # Matteo's own pad work, punches (G frame 0)
cut feet  yt-loma-highlights.mp4      46.10  2.30 0.57   # close on Loma's feet, footwork drill (opens on the feet)
cut lost  yt-loma-angles-footwork.mp4 182.40 3.60 0.40   # overhead, Loma vs Pedraza: Loma moves around him in the corner, he turns to find him (H frame 0)
cut side1 yt-loma-skillr.mp4          411.20 3.00 0.50   # Loma vs Pedraza: Loma throws, then moves off the line
cut side2 yt-loma-skillr.mp4          30.40  3.60 0.50   # Loma vs Pedraza: after his combo he is out of range
cut inout yt-loma-highlights.mp4      34.60  6.90 0.48   # Loma alone in the ring, small steps in and out, never still
cut pivot yt-loma-angles-footwork.mp4 189.40 3.30 0.48   # overhead: Loma pivots around him, he has to turn
for V in F G H; do
  [ -f "assets/media/aroll_$V.mp4" ] || python3 -P ../../editing/reel-kit/scripts/assemble.py work/takes.json "$V"
done
