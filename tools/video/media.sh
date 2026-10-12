#!/usr/bin/env bash
# Move big video files through GitHub Releases instead of git (git rejects files over 100 MB).
#   tools/video/media.sh list              list stored media
#   tools/video/media.sh pull NAME [DIR]   download a stored file (default DIR: media/)
#   tools/video/media.sh push FILE         upload a file (e.g. a finished render)
#     (Claude cloud sessions may be refused release writes; the Fetch video workflow can always write)
# Files live on the "media" release of this repo. Uses the gh CLI's REST access.
set -euo pipefail
REPO="${REPO:-fightingmatteo-ux/matteofights}"
TAG=media
cmd="${1:-list}"

release_id() {
  gh api "repos/$REPO/releases/tags/$TAG" --jq .id 2>/dev/null || \
    gh api -X POST "repos/$REPO/releases" -f tag_name=$TAG -f name="Media" \
      -f body="Raw footage, references and renders. Managed by tools/video/media.sh." --jq .id
}

case "$cmd" in
  list)
    gh api "repos/$REPO/releases/tags/$TAG" --jq '.assets[] | "\(.name)\t\(.size/1048576|floor) MB\t\(.updated_at)"' ;;
  pull)
    name="$2"; dir="${3:-media}"; mkdir -p "$dir"
    id=$(gh api "repos/$REPO/releases/tags/$TAG" --jq ".assets[] | select(.name==\"$name\") | .id")
    [ -n "$id" ] || { echo "no asset named $name" >&2; exit 1; }
    gh api -H "Accept: application/octet-stream" "repos/$REPO/releases/assets/$id" > "$dir/$name"
    echo "$dir/$name" ;;
  push)
    file="$2"; name="$(basename "$file")"; rid=$(release_id)
    old=$(gh api "repos/$REPO/releases/$rid/assets" --jq ".[] | select(.name==\"$name\") | .id")
    [ -z "$old" ] || gh api -X DELETE "repos/$REPO/releases/assets/$old"
    gh api -X POST -H "Content-Type: application/octet-stream" --input "$file" \
      "https://uploads.github.com/repos/$REPO/releases/$rid/assets?name=$name" --jq .browser_download_url ;;
  *) sed -n 2,7p "$0"; exit 1 ;;
esac
