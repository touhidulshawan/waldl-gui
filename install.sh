#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────
#  install.sh  —  Install WallhavenDownloader system-wide
#  Must be run AFTER build.sh
#  Usage: sudo ./install.sh
# ─────────────────────────────────────────────────────────────
set -e

BINARY="dist/WallhavenDownloader"
INSTALL_DIR="/opt/wallhaven"
DESKTOP_FILE="wallhaven.desktop"

if [ ! -f "$BINARY" ]; then
    echo "ERROR: $BINARY not found. Run ./build.sh first."
    exit 1
fi

echo "==> Installing to $INSTALL_DIR ..."
mkdir -p "$INSTALL_DIR"
cp "$BINARY" "$INSTALL_DIR/WallhavenDownloader"
chmod +x "$INSTALL_DIR/WallhavenDownloader"

echo "==> Creating symlink in /usr/local/bin ..."
ln -sf "$INSTALL_DIR/WallhavenDownloader" /usr/local/bin/wallhaven

echo "==> Installing .desktop entry ..."
cp "$DESKTOP_FILE" /usr/share/applications/wallhaven.desktop
# Patch the Exec path
sed -i "s|Exec=.*|Exec=$INSTALL_DIR/WallhavenDownloader|" \
    /usr/share/applications/wallhaven.desktop
update-desktop-database /usr/share/applications 2>/dev/null || true

echo ""
echo "✅  Installed!"
echo "    Run from terminal : wallhaven"
echo "    Or find it in your app menu under Graphics / Network"
