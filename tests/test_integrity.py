from pathlib import Path

from openlp_vault.integrity import compute_hash, verify_hash


def test_compute_hash_file(tmp_path: Path):
    file_path = tmp_path / "data.txt"
    file_path.write_text("hola mundo")

    digest = compute_hash(file_path)
    assert isinstance(digest, str)
    assert len(digest) == 64


def test_compute_hash_directory(tmp_path: Path):
    d = tmp_path / "backup"
    d.mkdir()
    (d / "a.txt").write_text("a")
    (d / "b.txt").write_text("b")
    nested = d / "nested"
    nested.mkdir()
    (nested / "c.txt").write_text("c")

    digest = compute_hash(d)
    assert isinstance(digest, str)
    assert len(digest) == 64


def test_verify_hash(tmp_path: Path):
    file_path = tmp_path / "data.txt"
    file_path.write_text("hola mundo")

    digest = compute_hash(file_path)
    assert verify_hash(file_path, digest)
    assert not verify_hash(file_path, "0" * 64)
