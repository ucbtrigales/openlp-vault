import logging
from pathlib import Path
import tempfile

from .i18n import _, install_click_translations

import click
from . import __version__
from .discovery import find_openlp_installation
from .legal import (
    CONTACT_EMAIL,
    COPYRIGHT_NOTICE,
    MAINTAINING_COMMUNITY,
    PROJECT_URL,
)
from .observability import setup_logging
from .utils import format_drive_timestamp

install_click_translations()


@click.group(
    epilog=_(
        "License: GPL-3.0-or-later. Run 'openlp-vault license' for details."
    )
)
@click.version_option(version=__version__, message="OpenLP Vault %(version)s")
@click.option("--debug", is_flag=True, default=False, help=_("Show debugging information"))
@click.pass_context
def cli(ctx, debug):
    """OpenLP Vault CLI"""
    setup_logging(logging.DEBUG if debug else logging.INFO)
    ctx.obj = {"debug": debug}


@cli.command("license", help=_("Show copyright, license, and project information."))
def license_info():
    """Show the project's legal and maintenance information."""
    click.echo(f"OpenLP Vault {__version__}\n")
    click.echo(COPYRIGHT_NOTICE)
    click.echo(_("Contact: {email}").format(email=CONTACT_EMAIL))
    click.echo()
    click.echo(
        _(
            "Licensed under the GNU General Public License, version 3 or later "
            "(GPL-3.0-or-later)."
        )
    )
    click.echo()
    click.echo(
        _("Maintained by the community of {community}.").format(
            community=MAINTAINING_COMMUNITY
        )
    )
    click.echo(_("The church is not the copyright holder."))
    click.echo()
    click.echo(_("Contributors retain copyright in their contributions."))
    click.echo(_("See LICENSE and NOTICE for details."))
    click.echo(_("Project: {url}").format(url=PROJECT_URL))


@cli.command(help=_("Authorize access to Google Drive and save the token locally."))
@click.option("--debug", is_flag=True, default=False, help=_("Show debugging information"))
@click.option("--credentials", type=click.Path(exists=True, dir_okay=False), default=None, help=_("Path to the OAuth 2.0 credentials JSON"))
@click.option("--token-path", type=click.Path(), default=None, help=_("Path used to store/read the OAuth token"))
def auth(debug, credentials, token_path):
    """Autoriza el acceso a Google Drive y guarda el token localmente."""
    if debug:
        setup_logging(logging.DEBUG)

    click.echo(_("Starting Google Drive authentication..."))
    from .auth import authenticate

    drive_service, creds = authenticate(client_secrets_file=credentials, token_path=token_path)
    click.echo(_("Authentication complete."))
    click.echo(_("Token saved at: {token}").format(token=creds.token))
    if drive_service:
        click.echo(_("Drive service is ready."))


@cli.command(help=_("Create a backup and upload it to Google Drive."))
@click.option("--debug", is_flag=True, default=False, help=_("Show debugging information"))
@click.option("--source", type=click.Path(exists=False, file_okay=False), default=None, help=_("Local OpenLP directory to back up"))
@click.option("--parent-folder-id", type=str, default=None, help=_("Google Drive folder ID where the backup will be uploaded"))
@click.option("--folder-name", type=str, default="OpenLP Vault", help=_("Drive folder name where the backup will be stored"))
@click.option("--no-upload", is_flag=True, default=False, help=_("Only create the local backup without uploading it"))
def backup(debug, source, parent_folder_id, folder_name, no_upload):
    """Crea un respaldo y lo sube a Google Drive"""
    if debug:
        setup_logging(logging.DEBUG)

    click.echo(_("Starting backup..."))
    if source is None:
        source = find_openlp_installation()
        if source is None:
            click.echo(_("Could not find the OpenLP installation. Use --source or OPENLP_PATH."))
            raise click.Abort()
        click.echo(_("Detected source: {source}").format(source=source))

    from .auth import authenticate
    from .backup import cleanup_backup_file, create_backup, upload_backup

    # always use temporary directory for ZIPs
    backup_path = create_backup(source)
    click.echo(_("Backup file created: {path}").format(path=backup_path))

    if no_upload:
        click.echo(_("The backup will not be uploaded to Drive (--no-upload)."))
        return

    click.echo(_("Authenticating with Google Drive..."))
    drive_service, _credentials = authenticate()
    metadata = upload_backup(backup_path, drive_service, parent_folder_id=parent_folder_id, folder_name=folder_name)
    click.echo(_("Backup uploaded: {id} ({name})").format(id=metadata.get("id"), name=metadata.get("name")))
    cleanup_backup_file(backup_path)


@cli.command(help=_("Restore the OpenLP installation from a backup."))
@click.option("--debug", is_flag=True, default=False, help=_("Show debugging information"))
@click.option("--backup-id", type=str, default=None, help=_("ID of the Drive backup to restore"))
@click.option("--destination", type=click.Path(file_okay=False), default=None, help=_("Local directory where OpenLP will be restored"))
@click.option("--list-only", is_flag=True, default=False, help=_("Only list available backups without restoring"))
def restore(debug, backup_id, destination, list_only):
    """Restaura la instalación desde un respaldo"""
    if debug:
        setup_logging(logging.DEBUG)

    click.echo(_("Starting restore..."))
    from .auth import authenticate
    from .backup import cleanup_backup_file
    from .restore import list_backups, download_backup, apply_backup

    drive_service, _credentials = authenticate()
    backups = list_backups(drive_service)
    if not backups:
        click.echo(_("No backups were found in Drive."))
        raise click.Abort()

    if list_only:
        click.echo(_("Available backups:"))
        for idx, backup in enumerate(backups, start=1):
            created = format_drive_timestamp(backup.get('createdTime', ''))
            click.echo(f"{idx}. {backup.get('name')} (id={backup.get('id')}) created={created} size={backup.get('size')}")
        return
        if choice < 1 or choice > len(backups):
            click.echo(_("Invalid selection."))
            raise click.Abort()
        backup_id = backups[choice - 1]["id"]

    if destination is None:
        destination = find_openlp_installation()
        if destination is None:
            destination = click.prompt(_("Local OpenLP path to restore"), type=click.Path(file_okay=False))
    click.echo(_("Restore path: {destination}").format(destination=destination))

    # snapshot_dir option removed; snapshots are no longer supported in CLI

    download_dir = Path(tempfile.mkdtemp(prefix="openlp_restore_"))
    archive_path = download_dir / f"{backup_id}.zip"
    click.echo(_("Downloading backup {id}...").format(id=backup_id))
    download_backup(backup_id, drive_service, archive_path)

    click.echo(_("Applying backup..."))
    apply_backup(archive_path, destination)
    cleanup_backup_file(archive_path)
    click.echo(_("Restore complete."))


@cli.command(help=_("Delete a backup stored in Drive."))
@click.option("--debug", is_flag=True, default=False, help=_("Show debugging information"))
@click.option("--backup-id", type=str, default=None, help=_("ID of the Drive backup to delete"))
@click.option("--force", is_flag=True, default=False, help=_("Delete without confirmation"))
def delete(debug, backup_id, force):
    """Elimina un respaldo almacenado en Drive"""
    if debug:
        setup_logging(logging.DEBUG)

    click.echo(_("Starting backup deletion..."))
    from .auth import authenticate
    from .restore import list_backups, delete_backup

    drive_service, _credentials = authenticate()
    backups = list_backups(drive_service)
    if not backups:
        click.echo(_("No backups were found in Drive."))
        raise click.Abort()

    selected = None
    if backup_id is not None:
        for backup in backups:
            if backup.get("id") == backup_id:
                selected = backup
                break
        if selected is None:
            click.echo(_("No backup with ID {id} was found.").format(id=backup_id))
            raise click.Abort()
    else:
        click.echo(_("Available backups:"))
        for idx, backup in enumerate(backups, start=1):
            click.echo(f"{idx}. {backup.get('name')} (id={backup.get('id')}) created={backup.get('createdTime')} size={backup.get('size')}")
        choice = click.prompt(_("Select the number of the backup to delete"), type=int)
        if choice < 1 or choice > len(backups):
            click.echo(_("Invalid selection."))
            raise click.Abort()
        selected = backups[choice - 1]
        backup_id = selected["id"]

    backup_name = selected.get("name")
    if not force:
        if not click.confirm(_("Delete '{name}' (id={id})? This action cannot be undone.").format(name=backup_name, id=backup_id), default=False):
            click.echo(_("Operation cancelled."))
            return

    delete_backup(backup_id, drive_service)
    click.echo(_("Backup deleted: {name} (id={id})").format(name=backup_name, id=backup_id))


if __name__ == "__main__":
    cli()
