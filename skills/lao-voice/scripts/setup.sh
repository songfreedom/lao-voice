#!/usr/bin/env bash
# Check (and optionally install) everything lao-voice needs. Safe to re-run.
# Usage: bash scripts/setup.sh
set -u

ok=1
need() {
  if command -v "$1" >/dev/null 2>&1; then
    echo "OK   $1 ($(command -v "$1"))"
  else
    echo "MISSING: $1 — $2"
    ok=0
  fi
}

need python3 "install Python 3.9+"
need ffmpeg  "macOS: brew install ffmpeg · Ubuntu: sudo apt-get install -y ffmpeg · Windows: winget install ffmpeg"
need curl    "install curl"

# Check edge-tts via direct binary, python module, or uvx
if command -v edge-tts >/dev/null 2>&1; then
  echo "OK   edge-tts (CLI)"
elif python3 -c "import edge_tts" >/dev/null 2>&1; then
  echo "OK   edge-tts (python3 -m edge_tts)"
elif command -v uvx >/dev/null 2>&1; then
  echo "OK   edge-tts (via uvx)"
else
  echo "INFO edge-tts not found; attempting pip install --user edge-tts..."
  if python3 -m pip install --quiet --user edge-tts >/dev/null 2>&1 || python3 -m pip install --quiet --break-system-packages --user edge-tts >/dev/null 2>&1; then
    echo "NEW  edge-tts (installed via pip)"
  else
    echo "MISSING: edge-tts — install with: pip install edge-tts  OR  install uv (https://docs.astral.sh/uv/)"
    ok=0
  fi
fi

if [ "$ok" = 1 ]; then
  echo "READY: lao-voice"
  exit 0
else
  echo "Setup incomplete — install the MISSING tools above and re-run."
  exit 1
fi
