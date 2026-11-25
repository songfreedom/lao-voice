#!/usr/bin/env bash
# Fetch Noto Sans Lao variable font (SIL OFL) into a project's fonts directory.
# Usage: bash scripts/fetch-lao-font.sh [target_dir]
# Default target_dir: ./public/fonts
set -euo pipefail

OUT_DIR="${1:-./public/fonts}"
mkdir -p "$OUT_DIR"

FONT_URL="https://raw.githubusercontent.com/google/fonts/main/ofl/notosanslao/NotoSansLao%5Bwdth%2Cwght%5D.ttf"
OFL_URL="https://raw.githubusercontent.com/google/fonts/main/ofl/notosanslao/OFL.txt"

FONT_FILE="$OUT_DIR/NotoSansLao[wdth,wght].ttf"
OFL_FILE="$OUT_DIR/NotoSansLao-OFL.txt"

if [ ! -s "$FONT_FILE" ]; then
  curl -sfL -o "$FONT_FILE" "$FONT_URL"
  echo "NEW  $FONT_FILE"
else
  echo "OK   $FONT_FILE"
fi

if [ ! -s "$OFL_FILE" ]; then
  curl -sfL -o "$OFL_FILE" "$OFL_URL" || true
fi

echo "READY: Noto Sans Lao -> $OUT_DIR"
