#!/usr/bin/env bash
# Cuts this reel's cutaways into assets/broll/b_<name>.mp4 (1080x1920, 30 fps, no audio) and builds the a-rolls.
# Submit render runs it on the runner before packing, after fetching from the media release:
#   media: origin-pin-raw.mp4=media/origin-pin/raw.mp4 broll-pads-chaiya.mp4=media/origin-pin/broll-pads-chaiya.mp4
#          first-fight-2.mp4=media/origin-pin/first-fight-2.mp4
# Matteo's own Drive clips (folder "Hella footage u needa clip", shared by link) come straight from Drive with gdown.
# Moments: production/listicles/moments.json (graded for technique) + Matteo's picks (2026-11-20).
set -euo pipefail
cd "$(dirname "$0")/.."
S=../../../media/origin-pin
mkdir -p assets/broll "$S"
command -v gdown > /dev/null || python3 -m pip install -q gdown
drive() {  # id file: download a Drive clip once
  [ -f "$S/$2" ] || gdown -q "$1" -O "$S/$2"
}
cut() {  # name source start dur [crop-center-x 0-1 for landscape sources]
  local out="assets/broll/b_$1.mp4" x="${5:-0.5}"
  [ -f "$out" ] && return 0
  vf="crop=w='min(iw,ih*9/16)':h='min(ih,iw*16/9)':x='max(0,min(iw-min(iw,ih*9/16),iw*$x-min(iw,ih*9/16)/2))':y='(ih-min(ih,iw*16/9))/2',scale=1080:1920"
  ffmpeg -nostdin -v error -y -ss "$3" -t "$4" -i "$S/$2" -vf "$vf,setsar=1,fps=30,format=yuv420p" -an -c:v libx264 -crf 18 -preset medium "$out"
  echo "b_$1: $2 @ $3 +$4"
}
photo() {  # name jpg dur: slow push-in on a still (Ken Burns, 1.00 -> 1.08), 30 fps
  local out="assets/broll/b_$1.mp4"
  [ -f "$out" ] && return 0
  local n; n=$(python3 -c "print(int(round($3*30)))")
  ffmpeg -nostdin -v error -y -loop 1 -i "assets/photos/$2" -t "$3" \
    -vf "scale=2160:3840,zoompan=z='1+0.08*on/$n':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s=1080x1920:fps=30,setsar=1,format=yuv420p" \
    -an -c:v libx264 -crf 18 -preset medium "$out"
  echo "b_$1: photo $2 +$3"
}

drive 1kY_fR5PwN07yk9dasbW4Q_5k39muHf-T kicking.mov          # low-angle bag kicks, red shirt (sharp, quality 4)
drive 1vj6GxY875E36-_u9yC84tWzqDm4-9SIc impact-mma.mov       # Zurich, Impact MMA: roundhouses (Matteo: 15-20 s)
drive 1-XaH84HgvgRKgajbc1F15GxBakWA7oO_ fitness-first.mov    # Bangkok red BOX bag: sharp combos, full extension
drive 1cO7ZS2vB0GficgdhERknFjIt1zkldbU6 super8.mp4           # Super8 pads close (first striking years)
drive 1HwvYUojYUMftZfNlofwE3qDwK2ggLCa5 morocco.mov          # Essaouira pad work with the old coach
drive 1-GxiwEjn1oJCJKUEkPb9W_lIXsOMsAAw rome.mp4             # Rome garden bag work
drive 1A9Awnno2e_KHq52e4PWWnRp9GUEEDY9V success.mov          # Success gym, Thailand: ring sparring from the corner

# filled in by work/make_broll_json.py's CLIPS table (same names, same seconds)
while read -r name kind src start dur x <&3; do
  case "$name" in ""|\#*) continue;; esac
  if [ "$kind" = photo ]; then photo "$name" "$src" "$dur"; else cut "$name" "$src" "$start" "$dur" "$x"; fi
done 3< work/clips.txt

R=$S/raw.mp4   # the media release copy is already the prepped 1080x1920 master (fetch-video prep_footage.sh, no trim)
for V in A B C; do
  [ -f "assets/media/aroll_$V.mp4" ] || python3 -P ../../editing/reel-kit/scripts/assemble.py work/takes.json "$V"
done
