"""Generate localized GUI screenshots for the documentation.

Run this script from the repository root in a graphical session. It uses only
demonstration data and never reads credentials or contacts Google Drive.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_ROOT = ROOT / "docs" / "assets" / "screenshots"


def capture(window, destination: Path) -> None:
    window.update_idletasks()
    window.deiconify()
    window.lift()
    window.update()
    destination.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["import", "-window", str(window.winfo_id()), str(destination)],
        check=True,
    )


def generate() -> None:
    from openlp_vault.gui import OpenLPVaultGUI

    language = __import__("os").environ.get("SCREENSHOT_LANGUAGE", "en")
    output_dir = OUTPUT_ROOT / language

    with (
        patch("openlp_vault.gui.find_openlp_installation", return_value=None),
        patch("openlp_vault.gui.load_config", return_value={}),
        patch("openlp_vault.gui.has_reusable_token", return_value=True),
        patch.object(OpenLPVaultGUI, "_load_config", return_value=None),
        patch.object(OpenLPVaultGUI, "_refresh_backups", return_value=None),
    ):
        app = OpenLPVaultGUI()
        app.geometry("620x450")
        app.credentials_path.set("/home/demo/OpenLP Vault/credentials.json")
        app.source_path.set("/home/demo/.local/share/openlp")
        app.drive_service = object()
        app.drive_user_email = "media@example.org"
        app.backups = [
            {
                "id": "demo-1",
                "name": "openlp_backup_church_20260808T183000Z.zip",
                "createdTime": "2026-08-08T18:30:00Z",
            },
            {
                "id": "demo-2",
                "name": "openlp_backup_church_20260801T183000Z.zip",
                "createdTime": "2026-08-01T18:30:00Z",
            },
            {
                "id": "demo-3",
                "name": "openlp_backup_church_20260725T183000Z.zip",
                "createdTime": "2026-07-25T18:30:00Z",
            },
        ]

        capture(app, output_dir / "main-window.png")

        app._open_backup_dialog()
        backup_dialog = app.winfo_children()[-1]
        capture(backup_dialog, output_dir / "upload-backup.png")
        backup_dialog.destroy()

        app._show_restore_dialog()
        restore_dialog = app.winfo_children()[-1]
        capture(restore_dialog, output_dir / "download-backup.png")
        restore_dialog.destroy()

        app._open_configuration()
        settings_dialog = app._configuration_dialog
        capture(settings_dialog, output_dir / "settings.png")
        settings_dialog.grab_release()
        settings_dialog.destroy()
        app.destroy()


if __name__ == "__main__":
    try:
        generate()
    except subprocess.CalledProcessError as exc:
        sys.exit(f"Screenshot command failed: {exc}")
