# OpenLP Vault

English | [Español](README.es.md)

OpenLP Vault creates complete backups of OpenLP data and lets you store,
restore, and delete them using Google Drive.

## Features

- Desktop GUI for local and Google Drive backups.
- Backup download, restoration, and deletion.
- CLI commands for authentication, backup, restore, and deletion.
- Automatic OpenLP data-directory discovery on Linux, macOS, and Windows.
- OAuth authentication with local token reuse.
- English and Spanish interfaces based on the system locale.
- SHA-256 integrity and versioning utilities.
- Packaging for Windows, macOS, and Linux AppImage.

## Development installation

OpenLP Vault requires Python 3.8 or later:

```bash
python -m pip install -r requirements.txt
python -m pip install -e .
```

Alternatively, use the setup script:

```bash
./setup.sh
source .venv/bin/activate
```

## Quick start

Create Google Drive credentials by following the
[Google Drive setup guide](docs/en/drive_setup.md).

```bash
openlp-vault auth --credentials credentials.json
openlp-vault backup
openlp-vault restore --list-only
openlp-vault restore --backup-id BACKUP_ID
openlp-vault delete --backup-id BACKUP_ID
```

Launch the desktop interface with:

```bash
openlp-vault-gui
```

On first launch, the GUI opens Settings when no reusable OAuth authorization
exists. Select `credentials.json`, the OpenLP data directory, and the Google
Drive folder name.

See the [usage guide](docs/en/usage.md) for all options and
[architecture](docs/en/architecture.md) for an overview of the codebase.
