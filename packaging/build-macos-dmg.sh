#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

PROJECT_VERSION="$(sed -n 's/^version[[:space:]]*=[[:space:]]*"\([^"]*\)"/\1/p' pyproject.toml | head -n 1)"
if [ -z "$PROJECT_VERSION" ]; then
  echo "Error: no se pudo obtener la versión desde pyproject.toml." >&2
  exit 1
fi
APP_NAME="OpenLP Vault"
APP_BUNDLE="dist/${APP_NAME}.app"
MAC_ARCH="$(uname -m)"
DMG_NAME="OpenLPVault-${PROJECT_VERSION}-${MAC_ARCH}.dmg"

rm -rf build dist dmg_temp
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r requirements.txt pyinstaller pillow

python -m PyInstaller --clean --onefile --console --name openlp-vault --paths src --collect-all openlp_vault --collect-submodules openlp_vault --add-data "LICENSE:." --add-data "NOTICE:." packaging/openlp_vault_cli_launcher.py
python -m PyInstaller --clean --onefile --windowed --name "$APP_NAME" --icon packaging/openlp-vault.png --paths src --collect-all openlp_vault --collect-submodules openlp_vault --add-data "LICENSE:." --add-data "NOTICE:." \
  --hidden-import openlp_vault.backup \
  --hidden-import openlp_vault.auth \
  --hidden-import openlp_vault.config \
  --hidden-import openlp_vault.discovery \
  --hidden-import openlp_vault.integrity \
  --hidden-import openlp_vault.observability \
  --hidden-import openlp_vault.recovery \
  --hidden-import openlp_vault.restore \
  --hidden-import openlp_vault.utils \
  --hidden-import openlp_vault.versioning \
  packaging/openlp_vault_gui_launcher.py

# Comprobar la CLI congelada antes de incorporarla a la aplicación.
dist/openlp-vault --version

mkdir -p "$APP_BUNDLE/Contents/MacOS" dmg_temp
cp dist/openlp-vault "$APP_BUNDLE/Contents/MacOS/openlp-vault"
chmod +x "$APP_BUNDLE/Contents/MacOS/openlp-vault"

cp -R "$APP_BUNDLE" dmg_temp/
cp LICENSE dmg_temp/
cp NOTICE dmg_temp/
ln -s "$APP_NAME.app/Contents/MacOS/openlp-vault" dmg_temp/openlp-vault
ln -s /Applications dmg_temp/Applications

hdiutil create -volname "OpenLP Vault" -srcfolder dmg_temp -format UDZO -ov "dist/$DMG_NAME"

echo "DMG creado: dist/$DMG_NAME"
