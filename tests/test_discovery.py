from pathlib import Path

import pytest

from openlp_vault import discovery
from openlp_vault.discovery import (
    COMMON_MARKERS,
    _linux_candidates,
    _mac_candidates,
    _windows_candidates,
    _is_openlp_installation,
    find_openlp_installation,
)


@pytest.mark.parametrize("marker", COMMON_MARKERS)
def test_is_openlp_installation_with_any_common_marker(tmp_path: Path, marker: str):
    root = tmp_path / "openlp"
    root.mkdir()
    (root / marker).mkdir()
    assert _is_openlp_installation(root)


def test_find_openlp_installation_env(tmp_path: Path, monkeypatch):
    root = tmp_path / "openlp"
    root.mkdir()
    (root / COMMON_MARKERS[0]).mkdir()
    monkeypatch.setenv("OPENLP_PATH", str(root))
    found = find_openlp_installation()
    assert found == root


def test_find_openlp_installation_uses_macos_data_folder(tmp_path: Path, monkeypatch):
    root = tmp_path / "Library" / "Application Support" / "openlp"
    root.mkdir(parents=True)
    (root / COMMON_MARKERS[0]).mkdir()
    monkeypatch.delenv("OPENLP_PATH", raising=False)
    monkeypatch.setattr(discovery.platform, "system", lambda: "Darwin")
    monkeypatch.setenv("HOME", str(tmp_path))

    assert find_openlp_installation() == root


def test_find_openlp_installation_uses_linux_default_path(tmp_path: Path, monkeypatch):
    root = tmp_path / ".local" / "share" / "openlp"
    root.mkdir(parents=True)
    (root / COMMON_MARKERS[0]).mkdir()
    monkeypatch.delenv("OPENLP_PATH", raising=False)
    monkeypatch.delenv("XDG_DATA_HOME", raising=False)
    monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setattr(discovery.platform, "system", lambda: "Linux")

    assert find_openlp_installation() == root


def test_linux_candidates_honor_xdg_locations(tmp_path: Path, monkeypatch):
    data_home = tmp_path / "data"
    config_home = tmp_path / "config"
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("XDG_DATA_HOME", str(data_home))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(config_home))

    assert _linux_candidates() == [
        tmp_path / ".var" / "app" / "org.openlp.OpenLP" / "data" / "openlp",
        data_home / "openlp",
        config_home / "openlp",
        tmp_path / ".openlp",
    ]


def test_windows_candidates_prefer_roaming_data_and_include_root(tmp_path: Path, monkeypatch):
    roaming = tmp_path / "Roaming"
    local = tmp_path / "Local"
    monkeypatch.setenv("APPDATA", str(roaming))
    monkeypatch.setenv("LOCALAPPDATA", str(local))
    monkeypatch.setenv("USERPROFILE", str(tmp_path / "User"))

    assert _windows_candidates() == [
        roaming / "OpenLP" / "data",
        roaming / "OpenLP",
        local / "OpenLP" / "data",
        local / "OpenLP",
    ]


def test_find_openlp_installation_uses_windows_roaming_root(tmp_path: Path, monkeypatch):
    roaming = tmp_path / "Roaming"
    root = roaming / "OpenLP"
    root.mkdir(parents=True)
    (root / COMMON_MARKERS[0]).mkdir()
    monkeypatch.delenv("OPENLP_PATH", raising=False)
    monkeypatch.setenv("APPDATA", str(roaming))
    monkeypatch.delenv("LOCALAPPDATA", raising=False)
    monkeypatch.setattr(discovery.platform, "system", lambda: "Windows")

    assert find_openlp_installation() == root


def test_windows_candidates_fall_back_to_user_profile(tmp_path: Path, monkeypatch):
    profile = tmp_path / "User"
    monkeypatch.delenv("APPDATA", raising=False)
    monkeypatch.delenv("LOCALAPPDATA", raising=False)
    monkeypatch.setenv("USERPROFILE", str(profile))

    root = profile / "AppData" / "Roaming" / "OpenLP"
    assert _windows_candidates() == [root / "data", root]


def test_macos_candidates_include_data_variants_before_base_folder(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    base = tmp_path / "Library" / "Application Support" / "openlp"

    assert _mac_candidates() == [base / "data", base / "Data", base]
