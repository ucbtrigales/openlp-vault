"""Módulo de descubrimiento de la instalación de OpenLP."""

import os
import platform
from pathlib import Path


DEFAULT_LINUX_PATHS = [
    Path.home() / ".var" / "app" / "org.openlp.OpenLP" / "data" / "openlp",
    Path.home() / ".config" / "openlp",
    Path.home() / ".local" / "share" / "openlp",
    Path.home() / ".openlp",
]
DEFAULT_MAC_PATHS = [
    Path.home() / "Library" / "Application Support" / "OpenLP",
    Path.home() / "Library" / "Application Support" / "openlp",
]
DEFAULT_WINDOWS_PATHS = [
    Path(os.getenv("LOCALAPPDATA", "")) / "OpenLP",
    Path(os.getenv("APPDATA", "")) / "OpenLP",
    Path(os.getenv("USERPROFILE", "")) / "AppData" / "Local" / "OpenLP",
]
COMMON_MARKERS = [
    "openlp.conf",
    "openlp.cfg",
    "database.db",
    "openlp.sqlite",
    "songs",
    "resources",
    "presentations",
]


def _is_openlp_installation(path: Path) -> bool:
    path = path.expanduser().resolve()
    if not path.is_dir():
        return False

    for marker in COMMON_MARKERS:
        marker_path = path / marker
        if marker_path.exists():
            return True

    return False


def _default_candidates() -> list[Path]:
    system = platform.system().lower()
    if system == "darwin":
        return DEFAULT_MAC_PATHS
    if system == "windows":
        return DEFAULT_WINDOWS_PATHS
    return DEFAULT_LINUX_PATHS


def find_openlp_installation() -> Path | None:
    """Intenta localizar la carpeta de datos de OpenLP en el sistema.

    Retorna la ruta si se encuentra, o None en caso contrario.
    """
    env_path = os.getenv("OPENLP_PATH")
    if env_path:
        candidate = Path(env_path)
        if _is_openlp_installation(candidate):
            return candidate

    for candidate in _default_candidates():
        if candidate and _is_openlp_installation(candidate):
            return candidate

    return None
