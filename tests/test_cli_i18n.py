import os
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).parents[1]


def run_cli(language: str, *arguments: str) -> str:
    environment = os.environ.copy()
    environment.pop("LANGUAGE", None)
    environment["LC_ALL"] = language
    environment["PYTHONPATH"] = str(ROOT / "src")
    result = subprocess.run(
        [sys.executable, "-m", "openlp_vault.cli", *arguments],
        cwd=ROOT,
        env=environment,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout


def test_click_builtin_help_is_spanish():
    output = run_cli("es_CL.UTF-8", "--help")
    assert "Uso:" in output
    assert "Opciones:" in output
    assert "Comandos:" in output
    assert "Muestra este mensaje y finaliza." in output
    assert "openlp-vault license" in output


def test_click_builtin_help_falls_back_to_english():
    output = run_cli("en_US.UTF-8", "--help")
    assert "Usage:" in output
    assert "Options:" in output
    assert "Commands:" in output
    assert "Show this message and exit." in output


def test_license_command_is_localized_and_contains_project_information():
    output = run_cli("es_CL.UTF-8", "license")
    assert "Copyright © 2026 Christian González G." in output
    assert "Contacto: christian.gonzalez@ucbtrigales.org" in output
    assert "La iglesia no es titular del copyright." in output
    assert "https://github.com/ucbtrigales/openlp-vault" in output


def test_version_output_is_concise():
    assert run_cli("en_US.UTF-8", "--version").strip() == "OpenLP Vault 0.1.0"
