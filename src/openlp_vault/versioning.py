"""Mecanismos para versionar y describir respaldos."""

from datetime import datetime, timezone
from pathlib import Path
from .integrity import compute_hash


def describe_backup(backup_path) -> dict:
    """Genera metadatos que describen un respaldo.

    Incluye información básica del archivo, tamaño, marcas de tiempo y hash.
    """
    backup_file = Path(backup_path)
    if not backup_file.exists():
        raise FileNotFoundError(backup_file)

    stat = backup_file.stat()
    file_hash = compute_hash(backup_file)
    created = datetime.fromtimestamp(stat.st_ctime, tz=timezone.utc).isoformat().replace("+00:00", "Z")
    modified = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat().replace("+00:00", "Z")

    return {
        "name": backup_file.name,
        "path": str(backup_file.resolve()),
        "size_bytes": stat.st_size,
        "created_time": created,
        "modified_time": modified,
        "sha256": file_hash,
        "version_id": f"{created}-{file_hash[:12]}",
    }
