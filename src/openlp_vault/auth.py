"""Autenticación con Google Drive y manejo de credenciales.

Provee `authenticate()` que realiza el flujo OAuth2 (Installed App)
usando un archivo `credentials.json` de Google Cloud Console y guarda
el token en `~/.openlp_vault/token.json`.
"""

from pathlib import Path
import logging
from typing import Tuple

try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
except Exception:  # pragma: no cover - missing deps handled at runtime
    Request = None
    Credentials = None
    InstalledAppFlow = None
    build = None

LOG = logging.getLogger("openlp_vault.auth")

# Scopes: allow creating/uploading files and read metadata for listing
SCOPES = [
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/drive.metadata.readonly",
]


def authenticate(client_secrets_file: str | Path | None = None,
                 token_path: str | Path | None = None) -> Tuple[object, object]:
    """Authenticate and return (drive_service, credentials).

    - `client_secrets_file`: path to OAuth client secrets JSON (from Google).
    - `token_path`: location to store the obtained token (defaults to ~/.openlp_vault/token.json).

    Raises helpful errors if required libraries are absent.
    """
    if InstalledAppFlow is None:
        raise RuntimeError("Missing Google auth libraries. Install requirements.txt")

    client_secrets_file = Path(client_secrets_file) if client_secrets_file else Path.cwd() / "credentials.json"
    token_path = Path(token_path) if token_path else Path.home() / ".openlp_vault" / "token.json"

    creds = None
    if token_path.exists():
        try:
            creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
        except Exception:
            LOG.debug("Failed reading existing token, will request new credentials", exc_info=True)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not client_secrets_file.exists():
                raise FileNotFoundError(
                    f"Client secrets not found at {client_secrets_file}. Create OAuth credentials and place the file there."
                )
            flow = InstalledAppFlow.from_client_secrets_file(str(client_secrets_file), SCOPES)
            creds = flow.run_local_server(port=0)

        token_path.parent.mkdir(parents=True, exist_ok=True)
        token_path.write_text(creds.to_json())

    drive_service = build("drive", "v3", credentials=creds)
    return drive_service, creds
