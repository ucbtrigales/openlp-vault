from pathlib import Path

from openlp_vault.discovery import _is_openlp_installation, find_openlp_installation


def test_is_openlp_installation(tmp_path: Path):
    root = tmp_path / "openlp"
    root.mkdir()
    (root / "openlp.conf").write_text("config")
    assert _is_openlp_installation(root)


def test_find_openlp_installation_env(tmp_path: Path, monkeypatch):
    root = tmp_path / "openlp"
    root.mkdir()
    (root / "openlp.conf").write_text("config")
    monkeypatch.setenv("OPENLP_PATH", str(root))
    found = find_openlp_installation()
    assert found == root
