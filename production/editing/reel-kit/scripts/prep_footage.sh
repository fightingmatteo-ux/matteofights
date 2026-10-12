#!/usr/bin/env bash
# Grade + normalise a raw talking-head clip into an H.264 master.
# usage: prep_footage.sh <raw clip> <out.mp4>
# Auto-detects iPhone HLG/PQ HDR (tone-maps to SDR bt709) and full-range "yuvj" footage (maps to tv range;
# otherwise the browser renderer reads it wrong and skin goes orange).
# Audio: untouched apart from a 70 Hz low-cut. NO denoise/compressor: on phone audio afftdn sounds
# watery/robotic (Matteo heard it immediately). Loudness is set once, in assemble.py.
# Grade: neutral by default (Matteo prefers the original colour). GRADE=house for the old warm/contrast look.
set -euo pipefail
IN="$1"; OUT="$2"
TRC=$(ffprobe -v error -select_streams v:0 -show_entries stream=color_transfer -of csv=p=0 "$IN" || true)
TM=""
case "$TRC" in
  arib-std-b67) TM="zscale=t=linear:npl=100:tin=arib-std-b67:pin=bt2020:min=bt2020nc,format=gbrpf32le,zscale=p=bt709,tonemap=hable:desat=0,zscale=t=bt709:m=bt709:r=tv," ;;
  smpte2084)    TM="zscale=t=linear:npl=100:tin=smpte2084:pin=bt2020:min=bt2020nc,format=gbrpf32le,zscale=p=bt709,tonemap=hable:desat=0,zscale=t=bt709:m=bt709:r=tv," ;;
esac
RANGE=$(ffprobe -v error -select_streams v:0 -show_entries stream=color_range -of csv=p=0 "$IN" || true)
[ "$RANGE" = "pc" ] && [ -z "$TM" ] && TM="scale=in_range=pc:out_range=tv,"
HOUSE="eq=contrast=1.12:brightness=-0.02:saturation=1.06:gamma=0.96,colorbalance=gs=-0.01:bs=-0.01:rm=0.02:bm=-0.01:bh=0.01,curves=all='0/0 0.12/0.07 0.5/0.5 0.9/0.94 1/1',vignette=PI/4.5,"
if [ "${GRADE:-neutral}" = house ]; then G="$HOUSE"; else G=""; fi
ffmpeg -v error -y -i "$IN" -map 0:v:0 -map 0:a:0 \
  -vf "${TM}${G}scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30,format=yuv420p" \
  -color_primaries bt709 -color_trc bt709 -colorspace bt709 -color_range tv \
  -c:v libx264 -preset slow -crf 16 -g 15 \
  -af "highpass=f=70" \
  -ar 48000 -c:a aac -b:a 192k -movflags +faststart "$OUT"
echo "prepped -> $OUT (trc=$TRC range=$RANGE grade=${GRADE:-neutral})"
