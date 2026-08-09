from pathlib import Path

import pytest

from openlp_vault import discovery
from openlp_vault.discovery import (
    COMMON_MARKERS,
    DEFAULT_MAC_PATHS,
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
    monkeypatch.setattr(discovery, "DEFAULT_MAC_PATHS", [root])

    assert find_openlp_installation() == root


@pytest.mark.parametrize(
    ("system_name", "candidates_attribute", "folder_name"),
    [
        ("Linux", "DEFAULT_LINUX_PATHS", "linux-openlp"),
        ("Windows", "DEFAULT_WINDOWS_PATHS", "windows-openlp"),
    ],
)
def test_find_openlp_installation_uses_platform_default_paths(
    tmp_path: Path,
    monkeypatch,
    system_name: str,
    candidates_attribute: str,
    folder_name: str,
):
    root = tmp_path / folder_name
    root.mkdir()
    (root / COMMON_MARKERS[0]).mkdir()
    monkeypatch.delenv("OPENLP_PATH", raising=False)
    monkeypatch.setattr(discovery.platform, "system", lambda: system_name)
    monkeypatch.setattr(discovery, candidates_attribute, [root])

    assert find_openlp_installation() == root


def test_macos_candidates_include_data_variants_before_base_folder():
    base = Path.home() / "Library" / "Application Support" / "openlp"

    assert DEFAULT_MAC_PATHS == [base / "Data", base / "data", base]
