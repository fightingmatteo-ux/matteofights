#!/usr/bin/env bash
# End-to-end ticker simulation (fake D1, GitHub, Modal, Telegram): GitHub refuses a run -> Modal takes over ->
# schedules run on Modal -> GitHub comes back. Run after any change to worker.js / route.js:
#   bash tools/ticker/sim/run.sh
set -euo pipefail
cd "$(dirname "$0")"
npx --yes esbuild@0.24 ../worker.js --bundle --format=esm --platform=neutral --outfile=worker.bundle.mjs --log-level=warning
node sim.mjs
rm -f worker.bundle.mjs
