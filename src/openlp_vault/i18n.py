"""Internationalization helpers for OpenLP Vault."""

from __future__ import annotations

import ctypes
import gettext
import importlib
import locale
import os
import platform
from pathlib import Path

DOMAIN = "openlp_vault"
LOCALE_DIR = Path(__file__).with_name("locale")
SUPPORTED_LANGUAGES = {"en", "es"}
LANGUAGE_ENVIRONMENT_VARIABLES = ("LC_ALL", "LC_MESSAGES", "LANG")


def normalize_language(value: str | None) -> str | None:
    """Return a supported base language from a POSIX locale value."""
    if not value:
        return None
    language = value.strip().split(":", 1)[0].split(".", 1)[0]
    language = language.split("@", 1)[0].replace("-", "_").split("_", 1)[0]
    language = language.lower()
    return language if language in SUPPORTED_LANGUAGES else None


def _windows_user_language() -> str | None:
    """Read the Windows display language for the current user."""
    try:
        language_id = ctypes.windll.kernel32.GetUserDefaultUILanguage()
    except (AttributeError, OSError):
        return None
    return locale.windows_locale.get(language_id)


def detect_language(environ: dict[str, str] | None = None) -> str:
    """Resolve the language from explicit settings and the operating system."""
    environment = os.environ if environ is None else environ
    for variable in LANGUAGE_ENVIRONMENT_VARIABLES:
        language = normalize_language(environment.get(variable))
        if language:
            return language

    if platform.system().lower() == "windows":
        language = normalize_language(_windows_user_language())
        if language:
            return language

    return "en"


def get_translation(language: str | None = None) -> gettext.NullTranslations:
    """Load a catalog, falling back safely to source English."""
    selected_language = normalize_language(language) or detect_language()
    return gettext.translation(
        DOMAIN, localedir=LOCALE_DIR, languages=[selected_language], fallback=True
    )


_translation = get_translation()
_ = _translation.gettext
ngettext = _translation.ngettext


def install_click_translations() -> None:
    """Make Click's built-in messages use the application's translation."""
    module_names = (
        "click.core",
        "click.decorators",
        "click.exceptions",
        "click.formatting",
        "click.parser",
        "click.shell_completion",
        "click.termui",
        "click.types",
        "click.utils",
        "click._termui_impl",
    )
    for module_name in module_names:
        module = importlib.import_module(module_name)
        if hasattr(module, "_"):
            setattr(module, "_", _)
        if hasattr(module, "ngettext"):
            setattr(module, "ngettext", ngettext)

# Keeping these markers here makes xgettext include Click's built-in strings
# in our catalog.
_CLICK_MESSAGE_MARKERS = (
    _("Usage:"),
    _("Options"),
    _("Commands"),
    _("Show the version and exit."),
    _("Show this message and exit."),
    _("Error: {message}"),
)
