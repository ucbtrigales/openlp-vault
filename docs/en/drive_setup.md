# Configure Google Drive access

English | [Español](../es/drive_setup.md)

OpenLP Vault needs a desktop OAuth client to access Google Drive on behalf of
the user.

## Create credentials

1. Open [Google Cloud Console](https://console.cloud.google.com/).
2. Create or select a project.
3. Under **APIs & Services → Library**, enable **Google Drive API**.
4. Configure the OAuth consent screen:
   - Select the appropriate user type for your account or organization.
   - Complete the requested application and contact details.
   - If the application remains in testing, add its users as test users.
5. Under **APIs & Services → Credentials**, create an **OAuth client ID**.
6. Select **Desktop app**.
7. Download the JSON file and save it in an accessible location, such as
   `credentials.json`.

Do not publish `credentials.json` or `~/.openlp-vault/token.json`.

## Connect from the GUI

```bash
openlp-vault-gui
```

Settings opens on first launch:

1. Select `credentials.json`.
2. Select the OpenLP data directory.
3. Keep or change the Google Drive folder name.
4. Click **Connect to Google Drive**.
5. Complete authorization in the browser.
6. When the status bar reports a connection, accept the settings.

GUI authorization can be cancelled and has a two-minute timeout.

## Connect from the CLI

```bash
openlp-vault auth --credentials /path/to/credentials.json
```

The browser opens the authorization flow. By default, the resulting token is
stored at:

```text
~/.openlp-vault/token.json
```

Use `--token-path` to select another location.

## Permissions

The application requests:

- `drive.file` to create and manage files it creates.
- `drive.metadata.readonly` to inspect metadata and list backups.

Backups are stored in a folder named `OpenLP Vault` by default. If it does
not exist, the application creates it in the Drive root. The CLI accepts
`--folder-name` and `--parent-folder-id` during backup.

## Troubleshooting

- If credentials fail, verify that the JSON belongs to a desktop OAuth client
  and contains `client_id` and `client_secret`.
- If browser authorization does not finish, retry and confirm that the account
  is an allowed test user when applicable.
- To discard saved authorization, use **Disconnect Google Drive** in the GUI.
  You may also remove the local token manually while the application is closed.
- If OpenLP is not detected, select its directory in the GUI or define
  `OPENLP_PATH` for the CLI.
