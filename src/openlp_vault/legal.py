"""Locate legal documents in development, installed, and frozen builds."""

from __future__ import annotations

import importlib.metadata
import sys
from pathlib import Path


LEGAL_DOCUMENTS = {"LICENSE", "NOTICE"}
PROJECT_URL = "https://ucbtrigales.github.io/openlp-vault/"
COPYRIGHT_NOTICE = "Copyright © 2026 Christian González G."
CONTACT_EMAIL = "christian.gonzalez@ucbtrigales.org"
MAINTAINING_COMMUNITY = (
    'Iglesia Evangélica Unión de Centros Bíblicos "Trigales"'
)


def legal_document_path(name: str) -> Path | None:
    """Return the path to a bundled legal document when available."""
    if name not in LEGAL_DOCUMENTS:
        raise ValueError(f"Unsupported legal document: {name}")

    candidates = []
    frozen_root = getattr(sys, "_MEIPASS", None)
    if frozen_root:
        candidates.append(Path(frozen_root) / name)

    candidates.extend(
        (
            Path(sys.executable).resolve().parent / name,
            Path(sys.executable).resolve().parent.parent / "share" / "doc" / "openlp-vault" / name,
            Path(__file__).resolve().parents[2] / name,
        )
    )
    for candidate in candidates:
        if candidate.is_file():
            return candidate

    try:
        distribution = importlib.metadata.distribution("openlp_vault")
    except importlib.metadata.PackageNotFoundError:
        return None
    for file in distribution.files or ():
        if file.name == name and "licenses" in file.parts:
            candidate = Path(str(distribution.locate_file(file)))
            if candidate.is_file():
                return candidate
    return None


def read_legal_document(name: str) -> str:
    """Read a bundled legal document as UTF-8."""
    path = legal_document_path(name)
    if path is None:
        raise FileNotFoundError(name)
    return path.read_text(encoding="utf-8")
