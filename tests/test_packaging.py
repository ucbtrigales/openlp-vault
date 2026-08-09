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
    assert 'File "dist\\openlp-vault.exe"' in installer
    assert 'File "dist\\openlp-vault-gui.exe"' in installer
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
