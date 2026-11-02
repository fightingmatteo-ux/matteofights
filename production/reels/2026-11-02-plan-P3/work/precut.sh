#!/usr/bin/env bash
# run by the Submit render workflow on the runner: trims long fight videos to the hook seconds
set -euo pipefail
R=production/reels/2026-11-02-plan-P3
mkdir -p "$R/assets/media"
ffmpeg -v error -y -ss 1426.0 -t 2.36 -i "media/plan/yt-tyson-1987-training-kos.mp4" -an -vf "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1,fps=30" -c:v libx264 -crf 16 -pix_fmt yuv420p "$R/assets/media/hookcut_A.mp4"
ffmpeg -v error -y -ss 40.0 -t 3.84 -i "media/plan/yt-power-slowmo-kos.mp4" -an -vf "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1,fps=30" -c:v libx264 -crf 16 -pix_fmt yuv420p "$R/assets/media/hookcut_B.mp4"
ffmpeg -v error -y -ss 20.0 -t 1.92 -i "media/plan/yt-power-slowmo-kos.mp4" -an -vf "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1,fps=30" -c:v libx264 -crf 16 -pix_fmt yuv420p "$R/assets/media/hookcut_C.mp4"
ffmpeg -v error -y -ss 1431.0 -t 3.40 -i "media/plan/yt-tyson-1987-training-kos.mp4" -an -vf "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1,fps=30" -c:v libx264 -crf 16 -pix_fmt yuv420p "$R/assets/media/hookcut_D.mp4"
ffmpeg -v error -y -ss 739.0 -t 1.72 -i "media/plan/yt-tyson-1987-training-kos.mp4" -an -vf "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1,fps=30" -c:v libx264 -crf 16 -pix_fmt yuv420p "$R/assets/media/hookcut_E.mp4"
