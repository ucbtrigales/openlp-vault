# Usage guide

English | [Español](../es/usage.md)

## Development installation

```bash
python -m pip install -r requirements.txt
python -m pip install -e .
```

You can also run `./setup.sh`, which creates `.venv`, installs
dependencies, and installs the package in editable mode.

## Language

The GUI and CLI support English and Spanish. Language is read exclusively from
standard system variables, in this order:

1. `LC_ALL`
2. `LC_MESSAGES`
3. `LANG`

Regional locales are reduced to their base language. For example,
`es_CL.UTF-8` and `es_ES.UTF-8` use Spanish. If no variable specifies a
supported language, English is used.

```bash
LANG=es_CL.UTF-8 openlp-vault --help
LANG=en_US.UTF-8 openlp-vault-gui
```

There is no language selector in the GUI or dedicated language option.

## Desktop interface

Launch the application with:

```bash
openlp-vault-gui
```

If no reusable OAuth token exists, Settings opens on first launch. Provide:

- The path to `credentials.json`.
- The OpenLP data directory.
- The Google Drive folder name; the default is `OpenLP Vault`.

The main window can:

- Create and upload a backup.
- Create a local backup only.
- List, download, and restore backups.
- Delete Drive backups.
- Reopen Settings or disconnect Google Drive.

Settings are stored in `~/.openlp-vault/config.json`, and the OAuth token is
stored in `~/.openlp-vault/token.json`.

## Command-line interface

```bash
openlp-vault --help
```

Available commands are `auth`, `backup`, `restore`, and `delete`.
There is no `discover` command; discovery runs automatically when `backup`
or `restore` needs a path.

### Authentication

After following the [Google Drive setup guide](drive_setup.md), run:

```bash
openlp-vault auth --credentials credentials.json
```

Relevant options:

- `--credentials FILE` — Google OAuth credentials file.
- `--token-path PATH` — Alternative token read/write location.
- `--debug` — Detailed logging.

### OpenLP directory discovery

The application checks `OPENLP_PATH` before platform-specific defaults. A
path is accepted if it contains at least one of `songs`, `bibles`,
`images`, or `presentations`.

```bash
OPENLP_PATH=/path/to/openlp openlp-vault backup --no-upload
```

The backup command also accepts a path directly:

```bash
openlp-vault backup --source /path/to/openlp
```

### Backup

Create a local temporary ZIP without uploading it:

```bash
openlp-vault backup --no-upload
```

Create and upload a backup to the `OpenLP Vault` folder:

```bash
openlp-vault backup
```

Choose another Drive folder or a known parent:

```bash
openlp-vault backup --folder-name "OpenLP Backups"
openlp-vault backup --parent-folder-id FOLDER_ID
```

Generated names begin with `openlp_backup_`. After a successful upload, the
temporary ZIP is removed.

### Restore

List backups and copy the displayed `id`:

```bash
openlp-vault restore --list-only
```

Restore that backup:

```bash
openlp-vault restore \
  --backup-id BACKUP_ID \
  --destination /path/to/openlp
```

When `--destination` is omitted, OpenLP Vault attempts discovery and prompts
for a path if necessary. Restore replaces the destination directory with the
ZIP contents, so close OpenLP first.

The CLI currently provides neither interactive backup selection for restore
nor a `--snapshot-dir` option.

### Delete

List backups and select one interactively:

```bash
openlp-vault delete
```

Delete a known backup:

```bash
openlp-vault delete --backup-id BACKUP_ID
```

Skip confirmation:

```bash
openlp-vault delete --backup-id BACKUP_ID --force
```

Deletion from Google Drive cannot be undone through OpenLP Vault.
