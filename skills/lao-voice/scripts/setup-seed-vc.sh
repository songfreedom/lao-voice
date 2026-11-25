#!/usr/bin/env bash
# Optional one-time installer for free local zero-shot voice cloning via Seed-VC (Plachtaa/seed-vc).
# Allows lao_voice.py --clone <any_5s_voice.wav> to create unlimited realistic Lao character voices for free!
# Usage: bash scripts/setup-seed-vc.sh [install_dir]
# Default install_dir: ~/seed-vc
set -euo pipefail

DEST="${1:-$HOME/seed-vc}"
command -v git >/dev/null 2>&1 || { echo "MISSING: git"; exit 1; }
command -v python3 >/dev/null 2>&1 || { echo "MISSING: python3"; exit 1; }

if [ -d "$DEST/.git" ]; then
  echo "OK   Seed-VC repo exists at $DEST (updating...)"
  git -C "$DEST" pull -q --ff-only || true
else
  echo "NEW  Cloning Plachtaa/seed-vc -> $DEST"
  git clone --depth 1 https://github.com/Plachtaa/seed-vc.git "$DEST"
fi

if [ ! -d "$DEST/.venv" ]; then
  python3 -m venv "$DEST/.venv"
fi

OS="$(uname -s)"
if [ "$OS" = "Darwin" ] && [ -f "$DEST/requirements-mac.txt" ]; then
  REQ="$DEST/requirements-mac.txt"
else
  REQ="$DEST/requirements.txt"
fi

echo "Installing Seed-VC dependencies from $REQ (this may take a few minutes)..."
"$DEST/.venv/bin/pip" install --upgrade pip
"$DEST/.venv/bin/pip" install -r "$REQ"

echo ""
echo "READY: Seed-VC installed at $DEST"
echo "Use it with lao-voice:"
echo "  python3 scripts/lao_voice.py speak --profile narrator --clone my_voice.wav --text \"ສະບາຍດີ!\" --out out.mp3"
