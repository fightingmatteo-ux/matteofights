#!/usr/bin/env bash
# Drive I/O for the reel pipeline.
#   drive.sh list                 newest files in the inputs folder (public, no auth)
#   drive.sh get <fileId> <dir>   download a file from Drive (public link, no auth)
#   drive.sh put <file>           upload to the outputs folder (needs rclone remote "gdrive")
set -euo pipefail
IN_ID="19PgWfSa9nwzBcn7JD24EY7QEr12IONbL"
OUT_ID="1bHwCLpkK2w9e9BN22dXWgQnn8_CLYpR2"
case "${1:-}" in
  list)
    curl -sL "https://drive.google.com/embeddedfolderview?id=$IN_ID#list" \
      | python -c "import re,sys;s=sys.stdin.read();[print(i,t) for i,t in re.findall(r'file/d/([^/\"]+).*?flip-entry-title\">([^<]*)',s,re.S)]" ;;
  get)
    mkdir -p "$3"; NAME=$(curl -sIL "https://drive.usercontent.google.com/download?id=$2&export=download&confirm=t" | grep -i -o 'filename="[^"]*"' | tail -1 | cut -d'"' -f2)
    curl -sL -o "$3/${NAME:-$2.mov}" "https://drive.usercontent.google.com/download?id=$2&export=download&confirm=t"; echo "$3/${NAME:-$2.mov}" ;;
  put)
    rclone copy "$2" "gdrive:" --drive-root-folder-id "$OUT_ID" -P ;;
  *) sed -n '2,6p' "$0" ;;
esac
