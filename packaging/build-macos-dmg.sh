#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

rm -rf build dist dmg_temp
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r requirements.txt pyinstaller

python -m PyInstaller --clean --onefile --console --name openlp-vault --paths src --collect-submodules openlp_vault src/openlp_vault/__main__.py
python -m PyInstaller --clean --onefile --windowed --name OpenLPVault-gui --paths src --collect-submodules openlp_vault \
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

mkdir -p dmg_temp
cp -R dist/OpenLPVault-gui.app dmg_temp/
if [ -f "dist/openlp-vault" ]; then
  cp dist/openlp-vault dmg_temp/
  chmod +x dmg_temp/openlp-vault
fi

hdiutil create -volname "OpenLP Vault" -srcfolder dmg_temp -format UDZO -ov dist/OpenLPVault.dmg
