#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

if [ ! -d ".venv" ]; then
  python3 -m venv .venv
fi

source .venv/bin/activate
if ! python -m pip --version >/dev/null 2>&1; then
  python -m ensurepip --upgrade
fi
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r requirements.txt
python -m pip install -e .

echo "Setup completo. Activa el entorno con: source .venv/bin/activate"
echo "Prueba el CLI con: openlp-vault --help"
echo "Prueba la GUI con: openlp-vault-gui"
