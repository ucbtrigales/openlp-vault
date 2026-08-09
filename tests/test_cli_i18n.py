import os
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).parents[1]


def run_help(language: str) -> str:
    environment = os.environ.copy()
    environment.pop("LANGUAGE", None)
    environment["LC_ALL"] = language
    environment["PYTHONPATH"] = str(ROOT / "src")
    result = subprocess.run(
        [sys.executable, "-m", "openlp_vault.cli", "--help"],
        cwd=ROOT,
        env=environment,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout


def test_click_builtin_help_is_spanish():
    output = run_help("es_CL.UTF-8")
    assert "Uso:" in output
    assert "Opciones:" in output
    assert "Comandos:" in output
    assert "Muestra este mensaje y finaliza." in output


def test_click_builtin_help_falls_back_to_english():
    output = run_help("en_US.UTF-8")
    assert "Usage:" in output
    assert "Options:" in output
    assert "Commands:" in output
    assert "Show this message and exit." in output
