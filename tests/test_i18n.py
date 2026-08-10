import gettext

from openlp_vault import i18n
from openlp_vault.i18n import detect_language, get_translation, normalize_language


def test_normalize_supported_system_locales():
    assert normalize_language("es_CL.UTF-8") == "es"
    assert normalize_language("es-ES") == "es"
    assert normalize_language("en_US.UTF-8") == "en"
    assert normalize_language("fr_FR.UTF-8") is None


def test_locale_environment_precedence():
    environment = {"LANG": "en_US.UTF-8", "LC_MESSAGES": "es_CL.UTF-8", "LC_ALL": ""}
    assert detect_language(environment) == "es"
    environment["LC_ALL"] = "en_GB.UTF-8"
    assert detect_language(environment) == "en"


def test_windows_uses_current_user_display_language(monkeypatch):
    monkeypatch.setattr(i18n.platform, "system", lambda: "Windows")
    monkeypatch.setattr(i18n, "_windows_user_language", lambda: "es_CL")

    assert detect_language({}) == "es"


def test_environment_language_overrides_windows_display_language(monkeypatch):
    monkeypatch.setattr(i18n.platform, "system", lambda: "Windows")
    monkeypatch.setattr(i18n, "_windows_user_language", lambda: "es_CL")

    assert detect_language({"LANG": "en_US.UTF-8"}) == "en"


def test_unknown_or_missing_locale_falls_back_to_english():
    assert detect_language({"LANG": "fr_FR.UTF-8"}) == "en"
    assert detect_language({}) == "en"


def test_spanish_catalog_interpolation_and_plural():
    translation = get_translation("es")
    assert translation.gettext("Settings") == "Configuración"
    assert translation.gettext("Backup file created: {path}").format(path="/tmp/a.zip") == (
        "Archivo de respaldo creado: /tmp/a.zip"
    )
    assert translation.ngettext("{count} backup found.", "{count} backups found.", 2).format(count=2) == (
        "Se encontraron 2 respaldos."
    )


def test_english_catalog_and_missing_catalog_fallback():
    assert get_translation("en").gettext("Settings") == "Settings"
    assert isinstance(get_translation("fr"), gettext.NullTranslations)
