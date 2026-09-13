#!/bin/bash
# Double-click this file on macOS. It opens the desktop app with no Terminal window
# after the first Gatekeeper approval (right-click → Open once if macOS blocks it).
cd "$(dirname "$0")"
# If we are inside desktop/, go up one level to pack root
if [ -d "../backend" ]; then
  cd ..
fi
ROOT="$(pwd)"

# Prefer the project venv so we don't depend on system Python having pywebview.
if [ -x "$ROOT/venv/bin/python" ]; then
  PY="$ROOT/venv/bin/python"
else
  PY="$(command -v python3)"
fi

exec "$PY" "$ROOT/desktop/launcher.py"
