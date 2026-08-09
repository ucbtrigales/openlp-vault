$root = Resolve-Path "$PSScriptRoot\.."
Set-Location $root

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
    "src/openlp_vault/__main__.py"
)

$pyInstallerGuiArgs = @(
    "--clean",
    "--onefile",
    "--windowed",
    "--name", "openlp-vault-gui",
    "--paths", "src",
    "--collect-submodules", "openlp_vault",
    "--collect-data", "openlp_vault",
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
& $makensis "$root\packaging\windows-installer.nsi"

# 5. Eliminar los .exe individuales sueltos de dist/ para dejar solo el instalador Setup
Remove-Item "dist\openlp-vault.exe" -Force
Remove-Item "dist\openlp-vault-gui.exe" -Force
