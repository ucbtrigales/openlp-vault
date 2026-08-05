#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

rm -rf build dist AppDir OpenLPVault.AppImage appimagetool.AppImage
python -m PyInstaller --clean --onefile --console --name openlp-vault --paths src src/openlp_vault/__main__.py
python -m PyInstaller --clean --onefile --windowed --name openlp-vault-gui --paths src packaging/openlp_vault_gui_launcher.py

mkdir -p AppDir/usr/bin
mkdir -p AppDir/usr/share/icons/hicolor/256x256/apps

cp dist/openlp-vault AppDir/usr/bin/
cp dist/openlp-vault-gui AppDir/usr/bin/
chmod +x AppDir/usr/bin/openlp-vault
chmod +x AppDir/usr/bin/openlp-vault-gui

if [ -f "packaging/openlp-vault.png" ]; then
  cp packaging/openlp-vault.png AppDir/
  cp packaging/openlp-vault.png AppDir/usr/share/icons/hicolor/256x256/apps/
fi

cat > AppDir/AppRun <<'EOF'
#!/bin/sh
HERE="$(dirname "$(readlink -f "${0}")")"
if [ "$1" = "--cli" ] || [ "$1" = "openlp-vault" ]; then
  shift
  exec "$HERE/usr/bin/openlp-vault" "$@"
fi
exec "$HERE/usr/bin/openlp-vault-gui" "$@"
EOF
chmod +x AppDir/AppRun

cat > AppDir/openlp-vault.desktop <<'EOF'
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
