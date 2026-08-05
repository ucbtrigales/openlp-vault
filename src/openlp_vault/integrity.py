"""Funciones para verificar integridad de respaldos (hashes, firmas)."""

import hashlib
from pathlib import Path


def compute_hash(path):
    """Computa un hash SHA-256 de un archivo o directorio.

    Para directorios, se recorre el contenido en orden lexicográfico y se
    actualiza el digest con los nombres de ruta relativos y el contenido de
    cada archivo. Esto permite un hash determinista del árbol de archivos.
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(p)

    digest = hashlib.sha256()

    if p.is_file():
        with p.open("rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                digest.update(chunk)
        return digest.hexdigest()

    for child in sorted(p.rglob("*")):
        relative = child.relative_to(p).as_posix()
        digest.update(relative.encode("utf-8"))
        if child.is_file():
            with child.open("rb") as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    digest.update(chunk)
        else:
            digest.update(b"DIR")
    return digest.hexdigest()


def verify_hash(path, expected):
    """Verifica que el hash SHA-256 de `path` coincida con `expected`."""
    actual = compute_hash(path)
    return actual == expected
