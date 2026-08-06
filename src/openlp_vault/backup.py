"""Lógica para crear y publicar respaldos en Google Drive."""

import hashlib
import logging
import shutil
import socket
import tempfile
import datetime
from pathlib import Path

try:
    from googleapiclient.http import MediaFileUpload
except Exception:  # pragma: no cover - runtime
    MediaFileUpload = None

LOG = logging.getLogger("openlp_vault.backup")


def compute_file_hash(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    digest = h.hexdigest()
    LOG.debug("Computed hash for %s: %s", path, digest)
    return digest


def _sanitize_zip_name(name: str) -> str:
    name = Path(name).stem
    sanitized = "".join(c if c.isalnum() or c in "-_" else "_" for c in name)
    return sanitized or "openlp_backup"


def create_backup(source_path, zip_name=None):
    """Crea un archivo ZIP con el contenido de `source_path` en el directorio temporal y devuelve su Path.

    - `source_path`: carpeta de OpenLP a respaldar
    - `zip_name`: nombre base para el archivo ZIP sin extensión
    """
    src = Path(source_path)
    if not src.exists():
        LOG.error("Ruta de origen no existe: %s", source_path)
        raise FileNotFoundError(src)
    target_dir = Path(tempfile.gettempdir())
    archive_base = target_dir / (_sanitize_zip_name(zip_name) if zip_name else _sanitize_zip_name(f"openlp_backup_{socket.gethostname().replace(' ', '_')}_{datetime.datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}"))

    target_dir.mkdir(parents=True, exist_ok=True)
    LOG.debug("Creando respaldo de %s en %s", src, archive_base)
    archive_path = shutil.make_archive(str(archive_base), "zip", root_dir=str(src))
    backup_path = Path(archive_path)
    LOG.info("Archivo de respaldo generado: %s", backup_path)
    compute_file_hash(backup_path)
    return backup_path


def cleanup_backup_file(backup_path: Path) -> None:
    """Elimina un archivo de respaldo temporal y su directorio temporal vacío si aplica."""
    try:
        backup_path = backup_path.resolve()
        tmpdir = Path(tempfile.gettempdir()).resolve()

        if backup_path.exists():
            if backup_path.is_file():
                backup_path.unlink()
                LOG.info("Respaldo temporal eliminado: %s", backup_path)
            elif backup_path.is_dir():
                shutil.rmtree(backup_path)
                LOG.info("Directorio temporal eliminado: %s", backup_path)

        parent = backup_path.parent
        if parent != tmpdir and parent.parent == tmpdir and parent.exists() and parent.is_dir():
            try:
                parent.rmdir()
                LOG.info("Directorio temporal vacío eliminado: %s", parent)
            except OSError:
                LOG.debug("No se pudo eliminar el directorio temporal %s porque no está vacío", parent)
    except Exception as exc:
        LOG.warning("No se pudo eliminar el respaldo temporal %s: %s", backup_path, exc)


def _find_drive_folder(drive_service, folder_name: str, parent_folder_id: str | None = None) -> str | None:
    escaped_folder_name = folder_name.replace("'", "\\'")

    query = [
        "mimeType = 'application/vnd.google-apps.folder'",
        f"name = '{escaped_folder_name}'",
        "trashed = false",
    ]
    if parent_folder_id:
        query.append(f"'{parent_folder_id}' in parents")
    else:
        query.append("'root' in parents")

    response = drive_service.files().list(q=" and ".join(query), fields="files(id,name)", spaces="drive").execute()
    files = response.get("files", [])
    if files:
        folder_id = files[0]["id"]
        LOG.debug("Carpeta Drive encontrada: %s (%s)", folder_name, folder_id)
        return folder_id
    return None


def _create_drive_folder(drive_service, folder_name: str, parent_folder_id: str | None = None) -> str:
    metadata = {
        "name": folder_name,
        "mimeType": "application/vnd.google-apps.folder",
    }
    if parent_folder_id:
        metadata["parents"] = [parent_folder_id]

    folder = drive_service.files().create(body=metadata, fields="id,name").execute()
    folder_id = folder.get("id")
    LOG.info("Carpeta Drive creada: %s (%s)", folder_name, folder_id)
    return folder_id


def get_or_create_drive_folder(drive_service, folder_name: str, parent_folder_id: str | None = None) -> str:
    folder_id = _find_drive_folder(drive_service, folder_name, parent_folder_id)
    if folder_id:
        return folder_id
    LOG.info("No se encontró la carpeta Drive '%s'; creando una nueva.", folder_name)
    return _create_drive_folder(drive_service, folder_name, parent_folder_id)


def upload_backup(backup_file: Path, drive_service, parent_folder_id: str | None = None, folder_name: str | None = "OpenLP Vault"):
    """Sube `backup_file` a Google Drive y retorna el metadata del archivo subido.

    Requiere un `drive_service` obtenido desde `auth.authenticate()`.
    """
    if MediaFileUpload is None:
        LOG.error("googleapiclient no disponible")
        raise RuntimeError("googleapiclient not available; install requirements.txt")

    if not backup_file.exists():
        LOG.error("Archivo de respaldo no encontrado: %s", backup_file)
        raise FileNotFoundError(backup_file)

    if parent_folder_id is None and folder_name:
        parent_folder_id = get_or_create_drive_folder(drive_service, folder_name)

    file_metadata = {"name": backup_file.name}
    if parent_folder_id:
        file_metadata["parents"] = [parent_folder_id]
        LOG.debug("Subiendo a carpeta Drive %s", parent_folder_id)

    LOG.debug("Subiendo archivo %s a Drive", backup_file)
    media = MediaFileUpload(str(backup_file), mimetype="application/zip")
    created = drive_service.files().create(
        body=file_metadata,
        media_body=media,
        fields="id,name,md5Checksum,size,createdTime",
    ).execute()
    LOG.info("Backup subido: %s", created)
    return created
