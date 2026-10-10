#!/usr/bin/env bash
# Loudness-master a HyperFrames render and scan it for glitch frames / black frames.
# usage: master.sh <render.mp4> <final.mp4>
set -euo pipefail
IN="$1"; OUT="$2"
ffmpeg -v error -y -i "$IN" -c:v copy -af "loudnorm=I=-14:TP=-1.2:LRA=9" -ar 48000 -c:a aac -b:a 192k -movflags +faststart "$OUT"
echo "black frames: $(ffmpeg -v info -i "$OUT" -vf blackdetect=d=0.03:pix_th=0.06 -an -f null - 2>&1 | grep -c black_start || true)"
ffmpeg -v error -i "$OUT" -vf "scale=90:160,format=gray" -f rawvideo - | python -P -c "
import sys,numpy as np
d=np.frombuffer(sys.stdin.buffer.read(),np.uint8).reshape(-1,160,90).astype(np.int16)
b=[i/30 for i in range(1,len(d)-1) if (lambda a,c,s:a>18 and c>18 and s<a*0.45)(np.abs(d[i]-d[i-1]).mean(),np.abs(d[i+1]-d[i]).mean(),np.abs(d[i+1]-d[i-1]).mean())]
print('glitch frames:', ['%.2f'%t for t in b] or 'none')"
ffmpeg -v info -i "$OUT" -af ebur128 -f null - 2>&1 | grep -E '^\s+I:' | tail -1
