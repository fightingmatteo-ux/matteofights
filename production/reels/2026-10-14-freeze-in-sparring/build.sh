#!/usr/bin/env bash
# Build one variant: index.html from work/template.html + work/edl_<V>.json.
#   bash build.sh A
set -euo pipefail
cd "$(dirname "$0")"
python -P inject.py "${1:-A}"
