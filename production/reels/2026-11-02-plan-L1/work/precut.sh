#!/usr/bin/env bash
# run by the Submit render workflow on the runner: trims long fight videos to the hook seconds
set -euo pipefail
R=production/reels/2026-11-02-plan-L1
mkdir -p "$R/assets/media"
ffmpeg -v error -y -ss 34.0 -t 3.72 -i "media/plan/yt-loma-highlights.mp4" -an -vf "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1,fps=30" -c:v libx264 -crf 16 -pix_fmt yuv420p "$R/assets/media/hookcut_A.mp4"
ffmpeg -v error -y -ss 29.0 -t 2.90 -i "media/plan/yt-loma-angles-footwork.mp4" -an -vf "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1,fps=30" -c:v libx264 -crf 16 -pix_fmt yuv420p "$R/assets/media/hookcut_B.mp4"
ffmpeg -v error -y -ss 89.0 -t 4.20 -i "media/plan/yt-loma-highlights.mp4" -an -vf "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1,fps=30" -c:v libx264 -crf 16 -pix_fmt yuv420p "$R/assets/media/hookcut_C.mp4"
ffmpeg -v error -y -ss 189.0 -t 3.60 -i "media/plan/yt-loma-angles-footwork.mp4" -an -vf "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1,fps=30" -c:v libx264 -crf 16 -pix_fmt yuv420p "$R/assets/media/hookcut_D.mp4"
ffmpeg -v error -y -ss 59.0 -t 2.62 -i "media/plan/yt-loma-angles-footwork.mp4" -an -vf "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1,fps=30" -c:v libx264 -crf 16 -pix_fmt yuv420p "$R/assets/media/hookcut_E.mp4"
