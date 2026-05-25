#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────
#  build.sh  —  Build WallhavenDownloader for Linux
#  Produces: dist/WallhavenDownloader  (single binary)
# ─────────────────────────────────────────────────────────────
set -e

PYTHON=${PYTHON:-python3}
VENV=".venv-build"

echo "==> Checking Python..."
$PYTHON --version

# Create isolated build venv
echo "==> Creating build venv..."
$PYTHON -m venv "$VENV"
source "$VENV/bin/activate"

echo "==> Installing dependencies..."
pip install --upgrade pip -q
pip install -r requirements.txt pyinstaller -q

echo "==> Running PyInstaller..."
pyinstaller wallhaven.spec \
    --distpath dist \
    --workpath build \
    --noconfirm \
    --clean

echo ""
echo "✅  Build complete!"
echo "    Binary: $(pwd)/dist/WallhavenDownloader"
echo ""
echo "To run:"
echo "    ./dist/WallhavenDownloader"
echo ""

# Optional: create a simple launcher in the project root
cat > run.sh << 'EOF'
#!/usr/bin/env bash
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
"$DIR/dist/WallhavenDownloader" "$@"
EOF
chmod +x run.sh

deactivate
