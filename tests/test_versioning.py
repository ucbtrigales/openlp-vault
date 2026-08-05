from pathlib import Path

from openlp_vault.versioning import describe_backup


def test_describe_backup(tmp_path: Path):
    backup_file = tmp_path / "backup.zip"
    backup_file.write_bytes(b"binary content")

    metadata = describe_backup(backup_file)
    assert metadata["name"] == "backup.zip"
    assert metadata["size_bytes"] == backup_file.stat().st_size
    assert metadata["sha256"].startswith("")
    assert metadata["version_id"].startswith(metadata["created_time"][:10])


def test_describe_backup_missing(tmp_path: Path):
    missing = tmp_path / "missing.zip"
    try:
        describe_backup(missing)
        assert False, "Expected FileNotFoundError"
    except FileNotFoundError:
        pass
