Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$root = Split-Path $PSScriptRoot -Parent
Set-Location $root

Remove-Item -Recurse -Force build, dist -ErrorAction SilentlyContinue
py -m pip install --upgrade pip setuptools wheel
py -m pip install -r requirements.txt pyinstaller

py -m PyInstaller --clean --onefile --console --name openlp-vault --paths src src/openlp_vault/__main__.py
py -m PyInstaller --clean --onefile --windowed --name openlp-vault-gui --paths src src/openlp_vault/gui.py

if (-not (Get-Command makensis -ErrorAction SilentlyContinue)) {
    choco install nsis -y
}

& makensis "$root\packaging\windows-installer.nsi"
