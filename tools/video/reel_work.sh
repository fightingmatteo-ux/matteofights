#!/usr/bin/env bash
# Keep a reel's heavy working media (footage, voice, A-rolls, b-roll, music) on the "media" release as one
# tarball, so any machine — laptop, Claude cloud session, GitHub Action — can rebuild and re-render the reel.
#   tools/video/reel_work.sh push <slug>   pack + upload <slug>-work.tar   (laptop or Action; cloud sessions can't write)
#   tools/video/reel_work.sh pull <slug>   download + unpack into the repo  (anywhere)
# Packs every gitignored file under production/reels/<slug>/ (minus node_modules, renders, caches), plus
# media/<slug>/ and any repo paths listed one per line in production/reels/<slug>/work/bundle-extra.txt.
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
cmd="${1:-}"; slug="${2:-}"
[ -n "$slug" ] || { sed -n 2,7p "$0"; exit 1; }
case "$slug" in *[!a-zA-Z0-9._-]*) echo "slug must be a simple name" >&2; exit 1;; esac
dir="production/reels/$slug"; tar="$slug-work.tar"
media=tools/video/media.sh

case "$cmd" in
  push)
    [ -d "$dir" ] || { echo "no $dir" >&2; exit 1; }
    list=$(mktemp)
    git ls-files --others --ignored --exclude-standard -- "$dir" \
      | grep -Ev '/(node_modules|renders|snapshots|\.hyperframes|\.thumbnails|\.waveform-cache)/' > "$list" || true
    [ -d "media/$slug" ] && find "media/$slug" -type f >> "$list"
    if [ -f "$dir/work/bundle-extra.txt" ]; then
      grep -v '^\s*\(#\|$\)' "$dir/work/bundle-extra.txt" | while read -r p; do
        [ -e "$p" ] && find "$p" -type f || echo "missing extra: $p" >&2
      done >> "$list"
    fi
    [ -s "$list" ] || { echo "nothing to pack for $slug" >&2; exit 1; }
    mkdir -p media && tar -cf "media/$tar" -T "$list"
    echo "packed $(wc -l < "$list") files, $(du -m "media/$tar" | cut -f1) MB"
    bash "$media" push "media/$tar" ;;
  pull)
    bash "$media" pull "$tar" media > /dev/null || { echo "no work bundle for $slug yet" >&2; exit 1; }
    tar -xf "media/$tar" && echo "unpacked media/$tar" ;;
  *) sed -n 2,7p "$0"; exit 1 ;;
esac
