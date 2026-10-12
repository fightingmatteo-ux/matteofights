#!/usr/bin/env bash
# Carve a music bed under the voice (HyperFrames hyperframes-audio skill), wherever the skill is installed.
# usage: carve.sh <index.html> <bed-audio-id> [voice-audio-id ...]
set -euo pipefail
for c in ~/.claude/skills/hyperframes-audio/scripts/carve.mjs ~/.agents/skills/hyperframes-audio/scripts/carve.mjs \
         ~/.claude/plugins/cache/*/hyperframes/*/skills/hyperframes-audio/scripts/carve.mjs; do
  [ -f "$c" ] && CARVE="$c" && break
done
[ -n "${CARVE:-}" ] || { echo "carve.mjs not found: run 'npx hyperframes skills update general-video'" >&2; exit 1; }
comp="$1" bed="$2"; shift 2
voices=(); for v in "$@"; do voices+=(--voice "$v"); done
node "$CARVE" --comp "$comp" --bed "$bed" "${voices[@]}" >/dev/null
echo "carved $bed under ${*:-auto-detected voice}"
