import logging
from pathlib import Path
import tempfile

import click
from . import __version__
from .discovery import find_openlp_installation
from .observability import setup_logging
from .utils import format_drive_timestamp


@click.group()
@click.version_option(version=__version__)
@click.option("--debug", is_flag=True, default=False, help="Mostrar información de depuración")
@click.pass_context
def cli(ctx, debug):
    """OpenLP Vault CLI"""
    setup_logging(logging.DEBUG if debug else logging.INFO)
    ctx.obj = {"debug": debug}


@cli.command()
@click.option("--debug", is_flag=True, default=False, help="Mostrar información de depuración")
@click.option("--credentials", type=click.Path(exists=True, dir_okay=False), default=None, help="Ruta al JSON de credenciales de OAuth 2.0")
@click.option("--token-path", type=click.Path(), default=None, help="Ruta donde guardar/leer el token OAuth")
def auth(debug, credentials, token_path):
    """Autoriza el acceso a Google Drive y guarda el token localmente."""
    if debug:
        setup_logging(logging.DEBUG)

    click.echo("Iniciando autenticación con Google Drive...")
    from .auth import authenticate

    drive_service, creds = authenticate(client_secrets_file=credentials, token_path=token_path)
    click.echo("Autenticación completada.")
    click.echo(f"Token guardado en: {creds.token}")
    if drive_service:
        click.echo("Servicio de Drive listo para usar.")


@cli.command()
@click.option("--debug", is_flag=True, default=False, help="Mostrar información de depuración")
@click.option("--source", type=click.Path(exists=False, file_okay=False), default=None, help="Directorio local de OpenLP para respaldar")
@click.option("--parent-folder-id", type=str, default=None, help="ID de carpeta en Google Drive donde subir el respaldo")
@click.option("--folder-name", type=str, default="OpenLP Vault", help="Nombre de carpeta en Drive donde guardar el respaldo")
@click.option("--no-upload", is_flag=True, default=False, help="Solo crear el respaldo local sin subirlo")
def backup(debug, source, parent_folder_id, folder_name, no_upload):
    """Crea un respaldo y lo sube a Google Drive"""
    if debug:
        setup_logging(logging.DEBUG)

    click.echo("Iniciando respaldo...")
    if source is None:
        source = find_openlp_installation()
        if source is None:
            click.echo("No se pudo encontrar la instalación de OpenLP. Usa --source o OPENLP_PATH.")
            raise click.Abort()
        click.echo(f"Origen detectado: {source}")

    from .auth import authenticate
    from .backup import cleanup_backup_file, create_backup, upload_backup

    # always use temporary directory for ZIPs
    backup_path = create_backup(source)
    click.echo(f"Archivo de respaldo creado: {backup_path}")

    if no_upload:
        click.echo("No se subirá el respaldo a Drive (--no-upload).")
        return

    click.echo("Autenticando con Google Drive...")
    drive_service, _ = authenticate()
    metadata = upload_backup(backup_path, drive_service, parent_folder_id=parent_folder_id, folder_name=folder_name)
    click.echo(f"Respaldo subido: {metadata.get('id')} ({metadata.get('name')})")
    cleanup_backup_file(backup_path)


@cli.command()
@click.option("--debug", is_flag=True, default=False, help="Mostrar información de depuración")
@click.option("--backup-id", type=str, default=None, help="ID del respaldo en Drive a restaurar")
@click.option("--destination", type=click.Path(file_okay=False), default=None, help="Directorio local donde restaurar OpenLP")
@click.option("--list-only", is_flag=True, default=False, help="Solo listar respaldos disponibles y no restaurar")
def restore(debug, backup_id, destination, list_only):
    """Restaura la instalación desde un respaldo"""
    if debug:
        setup_logging(logging.DEBUG)

    click.echo("Iniciando restauración...")
    from .auth import authenticate
    from .recovery import snapshot_local_state
    from .restore import list_backups, download_backup, apply_backup

    drive_service, _ = authenticate()
    backups = list_backups(drive_service)
    if not backups:
        click.echo("No se encontraron respaldos en Drive.")
        raise click.Abort()

    if list_only:
        click.echo("Respaldos disponibles:")
        for idx, backup in enumerate(backups, start=1):
            created = format_drive_timestamp(backup.get('createdTime', ''))
            click.echo(f"{idx}. {backup.get('name')} (id={backup.get('id')}) created={created} size={backup.get('size')}")
        return
        if choice < 1 or choice > len(backups):
            click.echo("Selección inválida.")
            raise click.Abort()
        backup_id = backups[choice - 1]["id"]

    if destination is None:
        destination = find_openlp_installation()
        if destination is None:
            destination = click.prompt("Ruta local de OpenLP para restaurar", type=click.Path(file_okay=False))
    click.echo(f"Ruta de restauración: {destination}")

    # snapshot_dir option removed; snapshots are no longer supported in CLI

    download_dir = Path(tempfile.mkdtemp(prefix="openlp_restore_"))
    archive_path = download_dir / f"{backup_id}.zip"
    click.echo(f"Descargando respaldo {backup_id}...")
    download_backup(backup_id, drive_service, archive_path)

    click.echo("Aplicando respaldo...")
    apply_backup(archive_path, destination)
    cleanup_backup_file(archive_path)
    click.echo("Restauración completada.")


@cli.command()
@click.option("--debug", is_flag=True, default=False, help="Mostrar información de depuración")
@click.option("--backup-id", type=str, default=None, help="ID del respaldo en Drive a eliminar")
@click.option("--force", is_flag=True, default=False, help="Eliminar sin pedir confirmación")
def delete(debug, backup_id, force):
    """Elimina un respaldo almacenado en Drive"""
    if debug:
        setup_logging(logging.DEBUG)

    click.echo("Iniciando eliminación de respaldo...")
    from .auth import authenticate
    from .restore import list_backups, delete_backup

    drive_service, _ = authenticate()
    backups = list_backups(drive_service)
    if not backups:
        click.echo("No se encontraron respaldos en Drive.")
        raise click.Abort()

    selected = None
    if backup_id is not None:
        for backup in backups:
            if backup.get("id") == backup_id:
                selected = backup
                break
        if selected is None:
            click.echo(f"No se encontró un respaldo con ID {backup_id}.")
            raise click.Abort()
    else:
        click.echo("Respaldos disponibles:")
        for idx, backup in enumerate(backups, start=1):
            click.echo(f"{idx}. {backup.get('name')} (id={backup.get('id')}) created={backup.get('createdTime')} size={backup.get('size')}")
        choice = click.prompt("Seleccione el número del respaldo a eliminar", type=int)
        if choice < 1 or choice > len(backups):
            click.echo("Selección inválida.")
            raise click.Abort()
        selected = backups[choice - 1]
        backup_id = selected["id"]

    backup_name = selected.get("name")
    if not force:
        if not click.confirm(f"¿Eliminar '{backup_name}' (id={backup_id})? Esta acción no se puede deshacer.", default=False):
            click.echo("Operación cancelada.")
            return

    delete_backup(backup_id, drive_service)
    click.echo(f"Respaldo eliminado: {backup_name} (id={backup_id})")


if __name__ == "__main__":
    cli()
