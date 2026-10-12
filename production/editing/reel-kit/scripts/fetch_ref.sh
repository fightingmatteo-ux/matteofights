#!/usr/bin/env bash
# Download a reel/video by link and "watch" it locally (frames, cuts, transcript, words, metadata).
#   bash production/editing/reel-kit/scripts/fetch_ref.sh <url> <slug> [reference|footage]
# Instagram: uses secrets/ig_cookies.txt (Netscape cookies.txt, gitignored) when present.
# Cloud sessions can't reach Instagram: run the GitHub Actions "Fetch video" workflow instead
# (repo secret IG_COOKIES holds the same file); see tools/video/README.md.
set -euo pipefail
URL="$1"; SLUG="$2"; KIND="${3:-reference}"
ROOT="$(git -C "$(dirname "$0")" rev-parse --show-toplevel)"
cd "$ROOT"
mkdir -p media/refs
args=()
[ -f secrets/ig_cookies.txt ] && args+=(--cookies secrets/ig_cookies.txt)
python -m yt_dlp -q "${args[@]}" -f "bv*+ba/b" --merge-output-format mp4 --write-info-json \
  -o "media/refs/$SLUG.%(ext)s" "$URL"
if [ "$KIND" = reference ]; then DIR="content-bank/references/videos/$SLUG"; else DIR="content-bank/real-footage/analysis/$SLUG"; fi
python -P tools/video/watch.py "media/refs/$SLUG.mp4" "$DIR" > /dev/null
python -P - "media/refs/$SLUG.info.json" "$DIR" <<'PY'
import json, sys
i = json.load(open(sys.argv[1], encoding="utf-8"))
keep = {k: i.get(k) for k in ["uploader", "channel", "title", "description", "timestamp", "duration",
        "view_count", "like_count", "comment_count", "webpage_url", "track", "artist"]}
json.dump(keep, open(f"{sys.argv[2]}/source.json", "w", encoding="utf-8"), indent=2, ensure_ascii=False)
print(f"{keep['channel']} | {keep['duration']}s | likes {keep['like_count']} | comments {keep['comment_count']}")
PY
echo "watched -> $DIR (contact.jpg, transcript.txt, words.json, cuts.txt, source.json)"
