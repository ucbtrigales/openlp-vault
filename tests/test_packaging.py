from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKAGING = ROOT / "packaging"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_windows_installer_contains_cli_and_gui():
    build_script = _read(PACKAGING / "build-windows.ps1")
    installer = _read(PACKAGING / "windows-installer.nsi")

    assert '"--name", "openlp-vault"' in build_script
    assert '"--name", "openlp-vault-gui"' in build_script
    assert '"--add-data", "src/openlp_vault/assets/openlp-vault-logo.png:openlp_vault/assets"' in build_script
    assert 'File "${PROJECT_ROOT}\\dist\\openlp-vault.exe"' in installer
    assert 'File "${PROJECT_ROOT}\\dist\\openlp-vault-gui.exe"' in installer
    assert 'Icon "${__FILEDIR__}\\openlp-vault.ico"' in installer
    assert 'LicenseData "${PROJECT_ROOT}\\LICENSE"' in installer
    assert 'OutFile "${OUT_FILE}"' in installer
    assert '!include "LogicLib.nsh"' in installer
    assert "ReadRegStr" in installer
    assert "ReadRegExpandStr" not in installer
    assert 'ReadRegStr $0 HKLM "SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Environment" "Path"' in installer
    assert 'WriteRegExpandStr HKLM "SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Environment" "Path" $0' in installer
    assert "/DPRODUCT_VERSION=$version" in build_script


def test_linux_appimage_contains_cli_and_gui():
    script = _read(PACKAGING / "linux-appimage-build.sh")

    assert "--name openlp-vault " in script
    assert "--name openlp-vault-gui " in script
    assert "cp dist/openlp-vault AppDir/usr/bin/" in script
    assert "cp dist/openlp-vault-gui AppDir/usr/bin/" in script
    assert 'if [ "$1" = "--cli" ]' in script


def test_macos_app_bundle_contains_cli_and_gui():
    script = _read(PACKAGING / "build-macos-dmg.sh")

    assert '--name openlp-vault ' in script
    assert '--name "$APP_NAME"' in script
    assert 'cp dist/openlp-vault "$APP_BUNDLE/Contents/MacOS/openlp-vault"' in script
    assert 'cp -R "$APP_BUNDLE" dmg_temp/' in script
    assert 'ln -s "$APP_NAME.app/Contents/MacOS/openlp-vault"' in script
