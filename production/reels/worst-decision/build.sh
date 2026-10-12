#!/usr/bin/env bash
# Rebuild index.html from work/template.html + work/edl.json, then carve both music beds under the voice.
set -euo pipefail
cd "$(dirname "$0")"
python -P inject.py
bash ../../editing/reel-kit/scripts/carve.sh index.html music-bed vo
bash ../../editing/reel-kit/scripts/carve.sh index.html music-bed-2 vo
