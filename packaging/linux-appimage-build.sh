#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

# 1. Limpieza inicial
rm -rf build dist AppDir OpenLPVault-x86_64.AppImage appimagetool.AppImage

# 2. Compilaciones con PyInstaller (Usando PYTHONPATH=src para resolver las importaciones del paquete)
PYTHONPATH=src python -m PyInstaller --clean --onefile --console \
  --name openlp-vault \
  --paths src \
  --collect-all openlp_vault \
  --collect-submodules openlp_vault \
  --add-data "LICENSE:." \
  --add-data "NOTICE:." \
  src/openlp_vault/__main__.py

PYTHONPATH=src python -m PyInstaller --clean --onefile --windowed \
  --name openlp-vault-gui \
  --paths src \
  --collect-all openlp_vault \
  --collect-submodules openlp_vault \
  --add-data "LICENSE:." \
  --add-data "NOTICE:." \
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

# 3. Preparación del directorio AppDir
mkdir -p AppDir/usr/bin
mkdir -p AppDir/usr/share/icons/hicolor/256x256/apps
mkdir -p AppDir/usr/share/doc/openlp-vault

cp dist/openlp-vault AppDir/usr/bin/
cp dist/openlp-vault-gui AppDir/usr/bin/
chmod +x AppDir/usr/bin/openlp-vault
chmod +x AppDir/usr/bin/openlp-vault-gui
cp LICENSE AppDir/usr/share/doc/openlp-vault/LICENSE
cp NOTICE AppDir/usr/share/doc/openlp-vault/NOTICE

# Copia de iconos
if [ -f "packaging/openlp-vault.png" ]; then
  cp packaging/openlp-vault.png AppDir/openlp-vault.png
  cp packaging/openlp-vault.png AppDir/usr/share/icons/hicolor/256x256/apps/openlp-vault.png
fi

# 4. Crear script AppRun
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

# 5. Crear archivo .desktop (Exec=openlp-vault-gui)
cat > AppDir/openlp-vault.desktop <<'EOF'
[Desktop Entry]
Type=Application
Name=OpenLP Vault
Exec=openlp-vault-gui
Icon=openlp-vault
Categories=Utility;
Terminal=false
EOF

# 6. Descargar appimagetool y empaquetar
curl -L -o appimagetool.AppImage https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage
chmod +x appimagetool.AppImage

mkdir -p dist
./appimagetool.AppImage AppDir dist/OpenLPVault-x86_64.AppImage
