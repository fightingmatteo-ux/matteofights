#!/usr/bin/env bash
# run by the Submit render workflow on the runner: trims long fight videos to the hook seconds
set -euo pipefail
R=production/reels/2026-11-02-plan-L2
mkdir -p "$R/assets/media"
ffmpeg -v error -y -ss 1418.2 -t 2.62 -i "media/plan/yt-tyson-1987-training-kos.mp4" -an -vf "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1,fps=30" -c:v libx264 -crf 16 -pix_fmt yuv420p "$R/assets/media/hookcut_A.mp4"
ffmpeg -v error -y -ss 1400.0 -t 3.46 -i "media/plan/yt-tyson-1987-training-kos.mp4" -an -vf "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1,fps=30" -c:v libx264 -crf 16 -pix_fmt yuv420p "$R/assets/media/hookcut_D.mp4"
