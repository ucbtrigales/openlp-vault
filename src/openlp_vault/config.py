"""Configuración y preferencias del sistema."""

from pathlib import Path
import json


def default_config_path() -> Path:
    return Path.home() / ".openlp-vault" / "config.json"


def load_config(path: Path | None = None) -> dict:
    p = path or default_config_path()
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text())
    except Exception:
        return {}


def save_config(data: dict, path: Path | None = None) -> None:
    p = path or default_config_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, indent=2))
