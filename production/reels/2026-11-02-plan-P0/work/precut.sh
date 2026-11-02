#!/usr/bin/env bash
# run by the Submit render workflow on the runner: trims long fight videos to the hook seconds
set -euo pipefail
R=production/reels/2026-11-02-plan-P0
mkdir -p "$R/assets/media"
ffmpeg -v error -y -ss 0.0 -t 3.16 -i "media/plan/fight-ufc-rudeboy-ko.mp4" -an -vf "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1,fps=30" -c:v libx264 -crf 16 -pix_fmt yuv420p "$R/assets/media/hookcut_A.mp4"
ffmpeg -v error -y -ss 4.0 -t 4.34 -i "media/plan/yt-power-slowmo-kos.mp4" -an -vf "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1,fps=30" -c:v libx264 -crf 16 -pix_fmt yuv420p "$R/assets/media/hookcut_B.mp4"
ffmpeg -v error -y -ss 74.0 -t 4.74 -i "media/plan/yt-power-slowmo-kos.mp4" -an -vf "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1,fps=30" -c:v libx264 -crf 16 -pix_fmt yuv420p "$R/assets/media/hookcut_C.mp4"
ffmpeg -v error -y -ss 122.0 -t 3.22 -i "media/plan/yt-power-slowmo-kos.mp4" -an -vf "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1,fps=30" -c:v libx264 -crf 16 -pix_fmt yuv420p "$R/assets/media/hookcut_D.mp4"
ffmpeg -v error -y -ss 146.0 -t 3.12 -i "media/plan/yt-power-slowmo-kos.mp4" -an -vf "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1,fps=30" -c:v libx264 -crf 16 -pix_fmt yuv420p "$R/assets/media/hookcut_E.mp4"
