#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

rm -rf build dist AppDir OpenLPVault.AppImage appimagetool.AppImage
python -m PyInstaller --clean --onefile --console --name openlp-vault --paths src src/openlp_vault/__main__.py
python -m PyInstaller --clean --onefile --windowed --name openlp-vault-gui --paths src src/openlp_vault/gui.py

mkdir -p AppDir/usr/bin
cp dist/openlp-vault-gui AppDir/usr/bin/
chmod +x AppDir/usr/bin/openlp-vault-gui

cat > AppDir/AppRun <<'EOF'
#!/bin/sh
HERE="$(dirname "$(readlink -f "${0}")")"
exec "$HERE/usr/bin/openlp-vault-gui" "$@"
EOF
chmod +x AppDir/AppRun

cat > AppDir/openlp-vault-gui.desktop <<'EOF'
[Desktop Entry]
Type=Application
Name=OpenLP Vault
Exec=usr/bin/openlp-vault-gui
Icon=openlp-vault
Categories=Utility;
Terminal=false
EOF

curl -L -o appimagetool.AppImage https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage
chmod +x appimagetool.AppImage
./appimagetool.AppImage AppDir OpenLPVault.AppImage
mkdir -p dist
mv OpenLPVault.AppImage dist/
