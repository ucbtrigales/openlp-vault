"""Módulo de descubrimiento de la instalación de OpenLP."""

import os
import platform
from pathlib import Path


def _linux_candidates() -> list[Path]:
    """Return standard OpenLP data locations in Linux preference order."""
    home = Path.home()
    data_home = Path(os.getenv("XDG_DATA_HOME", home / ".local" / "share"))
    config_home = Path(os.getenv("XDG_CONFIG_HOME", home / ".config"))
    return [
        home / ".var" / "app" / "org.openlp.OpenLP" / "data" / "openlp",
        data_home / "openlp",
        config_home / "openlp",
        home / ".openlp",
    ]


def _mac_candidates() -> list[Path]:
    """Return standard OpenLP data locations in macOS preference order."""
    application_support = Path.home() / "Library" / "Application Support"
    openlp_root = application_support / "openlp"
    return [openlp_root / "data", openlp_root / "Data", openlp_root]


def _windows_candidates() -> list[Path]:
    """Return standard OpenLP data locations in Windows preference order."""
    candidates = []
    appdata = os.getenv("APPDATA")
    local_appdata = os.getenv("LOCALAPPDATA")
    user_profile = os.getenv("USERPROFILE")

    if appdata:
        roaming_root = Path(appdata) / "OpenLP"
        candidates.extend((roaming_root / "data", roaming_root))
    elif user_profile:
        roaming_root = Path(user_profile) / "AppData" / "Roaming" / "OpenLP"
        candidates.extend((roaming_root / "data", roaming_root))

    # Retain compatibility with non-standard or older local installations, but
    # only after the documented roaming locations.
    if local_appdata:
        local_root = Path(local_appdata) / "OpenLP"
        candidates.extend((local_root / "data", local_root))

    return candidates


COMMON_MARKERS = [
    "songs",
    "bibles",
    "images",
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
        return _mac_candidates()
    if system == "windows":
        return _windows_candidates()
    return _linux_candidates()


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
