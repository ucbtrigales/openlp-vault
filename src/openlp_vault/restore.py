"""Lógica para descargar y restaurar respaldos."""

from pathlib import Path
import io
import shutil
import tempfile
from typing import Union

try:
    from googleapiclient.http import MediaIoBaseDownload
except Exception:  # pragma: no cover
    MediaIoBaseDownload = None


def list_backups(drive_service, page_size: int = 50):
    """Lista respaldos disponibles en Drive.

    Retorna una lista de dicts con `id`, `name` y `createdTime`.
    """
    q = "name contains 'openlp_backup_'"
    resp = drive_service.files().list(q=q, pageSize=page_size, fields="files(id,name,createdTime,size)").execute()
    return resp.get("files", [])


def download_backup(backup_id: str, drive_service, dest_path: str | Path):
    """Descarga un respaldo por `backup_id` a `dest_path` y retorna el Path."""
    if MediaIoBaseDownload is None:
        raise RuntimeError("googleapiclient not available; install requirements.txt")

    request = drive_service.files().get_media(fileId=backup_id)
    dest_path = Path(dest_path)
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    fh = io.FileIO(str(dest_path), "wb")
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while not done:
        status, done = downloader.next_chunk()
    fh.close()
    return dest_path


def delete_backup(backup_id: str, drive_service):
    """Elimina el respaldo con el ID dado de Google Drive."""
    drive_service.files().delete(fileId=backup_id).execute()
    return backup_id


def apply_backup(backup_file: str | Path, dest_installation_path: str | Path, snapshot_before: str | None = None):
    """Aplica el ZIP `backup_file` sobre `dest_installation_path`.

    - Si `snapshot_before` se provee, se asume que ya se realizó.
    - La aplicación es: descomprimir a una carpeta temporal y copiar sobre la instalación.
    """
    backup_file = Path(backup_file)
    dest = Path(dest_installation_path)
    if not backup_file.exists():
        raise FileNotFoundError(backup_file)

    temp_dir = Path(shutil.unpack_archive(str(backup_file), extract_dir=None, format='zip')) if False else None
    # shutil.unpack_archive does not return the dir; use a temporary extract
    import tempfile
    tmp = Path(tempfile.mkdtemp(prefix="openlp_restore_"))
    shutil.unpack_archive(str(backup_file), str(tmp))
    # copy extracted contents into destination
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(tmp, dest)
    shutil.rmtree(tmp)
    return dest
