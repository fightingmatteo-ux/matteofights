#!/usr/bin/env bash
# Build one variant: index.html from work/template.html + work/edl_<V>.json, then carve the music under the voice.
#   bash build.sh A
set -euo pipefail
cd "$(dirname "$0")"
V="${1:-A}"
python -P inject.py "$V"
bash ../../editing/reel-kit/scripts/carve.sh index.html music-bed vo
bash ../../editing/reel-kit/scripts/carve.sh index.html music-bed-2 vo
