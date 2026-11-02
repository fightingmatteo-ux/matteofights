#!/usr/bin/env bash
# Not a reel: downloads YouTube b-roll on Modal (GitHub runners get YouTube's bot check). bash make.sh N
# -> media/2026-11-02-yt-fetch/2026-11-02-yt-fetch-N.mp4 (line N of urls.txt), then the render workflow copies it
# to the media release like any render.
set -euo pipefail
cd "$(dirname "$0")"
N="$1"; URL=$(sed -n "${N}p" urls.txt | cut -d' ' -f1)
OUT="../../../media/2026-11-02-yt-fetch/2026-11-02-yt-fetch-$N.mp4"; mkdir -p "$(dirname "$OUT")"
python3 -m pip install -q -U "yt-dlp[default]"
curl -fsSL https://deno.land/install.sh | sh -s -- -y > /dev/null 2>&1 || true
export PATH="$HOME/.deno/bin:$PATH"
python3 -m yt_dlp --no-playlist -f "bv*[height<=1080][ext=mp4]+ba[ext=m4a]/b[height<=1080]/b" \
  --merge-output-format mp4 -o "$OUT" "$URL"
ls -la "$OUT"
