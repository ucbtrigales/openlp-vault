from pathlib import Path

import pytest

from openlp_vault.discovery import (
    COMMON_MARKERS,
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
