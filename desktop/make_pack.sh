#!/usr/bin/env bash
# Build a transferable zip of ILovePDF Personal (no venv, no node_modules, no data).
# First launch on the destination machine installs those automatically.
set -e
cd "$(dirname "$0")/.."
ROOT="$(pwd)"
STAMP="$(date +%Y%m%d)"
OUT="$ROOT/dist"
NAME="ILovePDF-Personal-Local-$STAMP"
DEST="$OUT/$NAME"

mkdir -p "$DEST"
echo "Packing transferable folder → $DEST"

rsync -a \
  --exclude '.git' \
  --exclude 'venv' \
  --exclude 'frontend/node_modules' \
  --exclude 'frontend/.next' \
  --exclude 'data' \
  --exclude 'dist' \
  --exclude '__pycache__' \
  --exclude '*.pyc' \
  --exclude '.pytest_cache' \
  --exclude '.DS_Store' \
  --exclude '.env' \
  "$ROOT/" "$DEST/"

# Ensure launchers are executable
chmod +x "$DEST/desktop/Launch ILovePDF.command" 2>/dev/null || true
chmod +x "$DEST/desktop/macos/ILovePDF Personal.app/Contents/MacOS/ILovePDFPersonal" 2>/dev/null || true
chmod +x "$DEST/desktop/make_pack.sh" 2>/dev/null || true
chmod +x "$DEST/start.sh" 2>/dev/null || true

# Friendly root aliases so the pack is obvious after unzip
cp "$DEST/desktop/Launch ILovePDF.command" "$DEST/Launch ILovePDF.command" 2>/dev/null || true
cp "$DEST/desktop/Launch ILovePDF.vbs" "$DEST/Launch ILovePDF.vbs" 2>/dev/null || true
cp "$DEST/desktop/Launch ILovePDF.bat" "$DEST/Launch ILovePDF.bat" 2>/dev/null || true

# Copy the .app to the pack root so macOS users just double-click it
if [ -d "$DEST/desktop/macos/ILovePDF Personal.app" ]; then
  rm -rf "$DEST/ILovePDF Personal.app"
  cp -R "$DEST/desktop/macos/ILovePDF Personal.app" "$DEST/ILovePDF Personal.app"
  chmod +x "$DEST/ILovePDF Personal.app/Contents/MacOS/ILovePDFPersonal"
fi

# Write a short HOW-TO at the pack root
cat > "$DEST/HOW TO OPEN.txt" <<'EOF'
ILovePDF Personal — Local Private Edition
=========================================

macOS
  1. Unzip this folder anywhere (Desktop, USB drive, Documents).
  2. Double-click "ILovePDF Personal.app"
     If macOS says it can't be opened: right-click → Open → Open.
  3. First launch installs Python packages + the UI (1–3 minutes).
     After that it opens as a native window.

Windows
  1. Unzip this folder anywhere.
  2. Double-click "Launch ILovePDF.vbs"
     (or "Launch ILovePDF.bat" if .vbs is blocked).
  3. First launch installs packages, then a window / browser opens.

Master password: admin123   (change in .env)

Your files stay inside this folder:
  data/storage/originals
  data/storage/outputs
  data/ilovepdf.db

To move the app to another computer, zip this whole folder again
(or run desktop/make_pack.sh). Do NOT include data/ if you want a clean copy.
EOF

cd "$OUT"
ZIP="$NAME.zip"
rm -f "$ZIP"
if command -v zip >/dev/null 2>&1; then
  zip -r -q "$ZIP" "$NAME"
  echo "Created $OUT/$ZIP"
else
  echo "zip not found — folder is ready at $DEST"
fi

echo "Done."
echo "  Folder: $DEST"
echo "  Zip:    $OUT/$ZIP"
