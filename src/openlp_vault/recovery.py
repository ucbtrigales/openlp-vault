"""Manejo de respaldos locales temporales para recuperación ante fallos."""

from pathlib import Path
import shutil


def snapshot_local_state(openlp_path, dest):
    """Copia el estado local `openlp_path` a `dest` (dest debe ser una carpeta destino)."""
    src = Path(openlp_path)
    dst = Path(dest)
    if not src.exists():
        raise FileNotFoundError(src)
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)
    return dst


def restore_snapshot(snapshot_path, openlp_path):
    """Restaura la instantánea `snapshot_path` sobre `openlp_path`."""
    src = Path(snapshot_path)
    dst = Path(openlp_path)
    if not src.exists():
        raise FileNotFoundError(src)
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)
    return dst
