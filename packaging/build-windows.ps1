$root = Resolve-Path "$PSScriptRoot\.."
Set-Location $root

$projectMetadata = Get-Content "pyproject.toml" -Raw
if ($projectMetadata -notmatch '(?m)^version\s*=\s*"([^"]+)"') {
    throw "Error: no se pudo obtener la versión desde pyproject.toml."
}
$version = $Matches[1]

# 1. Limpiar construcciones previas
Remove-Item -Recurse -Force build, dist -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Path dist -Force

# 2. Compilar binarios de Python (Consola y GUI)
$pyInstallerConsoleArgs = @(
    "--clean",
    "--onefile",
    "--console",
    "--name", "openlp-vault",
    "--paths", "src",
    "--collect-submodules", "openlp_vault",
    "--collect-data", "openlp_vault",
    "--add-data", "LICENSE:.",
    "--add-data", "NOTICE:.",
    "packaging/openlp_vault_cli_launcher.py"
)

$pyInstallerGuiArgs = @(
    "--clean",
    "--onefile",
    "--windowed",
    "--name", "openlp-vault-gui",
    "--icon", "packaging/openlp-vault.ico",
    "--add-data", "src/openlp_vault/assets/openlp-vault-logo.png:openlp_vault/assets",
    "--paths", "src",
    "--collect-submodules", "openlp_vault",
    "--collect-data", "openlp_vault",
    "--add-data", "LICENSE:.",
    "--add-data", "NOTICE:.",
    "--hidden-import", "openlp_vault.backup",
    "--hidden-import", "openlp_vault.auth",
    "--hidden-import", "openlp_vault.config",
    "--hidden-import", "openlp_vault.discovery",
    "--hidden-import", "openlp_vault.integrity",
    "--hidden-import", "openlp_vault.observability",
    "--hidden-import", "openlp_vault.recovery",
    "--hidden-import", "openlp_vault.restore",
    "--hidden-import", "openlp_vault.utils",
    "--hidden-import", "openlp_vault.versioning",
    "packaging/openlp_vault_gui_launcher.py"
)

py -m PyInstaller $pyInstallerConsoleArgs
py -m PyInstaller $pyInstallerGuiArgs

# Comprobar que la CLI congelada puede iniciarse antes de empaquetarla.
& "dist\openlp-vault.exe" --version
if ($LASTEXITCODE -ne 0) {
    throw "Error: la CLI compilada no pudo ejecutarse."
}

# 3. Localizar makensis (NSIS) de forma segura
$makensisCmd = Get-Command makensis -ErrorAction SilentlyContinue

if ($makensisCmd) {
    $makensis = $makensisCmd.Source
} elseif (Test-Path "C:\ProgramData\chocolatey\bin\makensis.exe") {
    $makensis = "C:\ProgramData\chocolatey\bin\makensis.exe"
} elseif (Test-Path "C:\Program Files (x86)\NSIS\makensis.exe") {
    $makensis = "C:\Program Files (x86)\NSIS\makensis.exe"
} else {
    throw "Error: makensis (NSIS) no está instalado o no se encuentra en las rutas estándar."
}

# 4. Crear el instalador unificado con NSIS
& $makensis "/DPRODUCT_VERSION=$version" "$root\packaging\windows-installer.nsi"
if ($LASTEXITCODE -ne 0) {
    throw "Error: NSIS no pudo crear el instalador."
}

# 5. Eliminar los .exe individuales sueltos de dist/ para dejar solo el instalador Setup
Remove-Item "dist\openlp-vault.exe" -Force
Remove-Item "dist\openlp-vault-gui.exe" -Force

Write-Host "Instalador creado: dist\OpenLPVault-Setup-v$version.exe"
