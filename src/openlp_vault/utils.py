"""Utilidades auxiliares comunes."""

from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo
import shutil


def copytree_safe(src: Path, dst: Path):
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)


import locale


def format_drive_timestamp(value: str, tz_name: str | None = None) -> str:
    """Formatea un timestamp de Drive usando la zona horaria y formato local del sistema.

    El valor de Drive suele ser ISO 8601 con `Z` o offset.
    Devuelve la representación local de fecha/hora.
    """
    if not value:
        return "?"
    if isinstance(value, str) and value.endswith("Z"):
        value = value[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(value)
    except ValueError:
        return value
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    if tz_name is None:
        dt = dt.astimezone()
    else:
        dt = dt.astimezone(ZoneInfo(tz_name))

    try:
        locale.setlocale(locale.LC_TIME, "")
    except locale.Error:
        pass

    return dt.strftime(locale.nl_langinfo(locale.D_T_FMT) if hasattr(locale, "nl_langinfo") else "%c")
