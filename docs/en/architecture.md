# Architecture

English | [Español](../es/architecture.md)

The code is distributed as the `openlp_vault` package under `src/`. The GUI
and CLI are separate presentation layers that share authentication, backup,
and restore modules.

## Modules

- `gui` — Tkinter desktop interface.
- `cli` — Click commands: `auth`, `backup`, `restore`, and `delete`.
- `i18n` — Locale detection and `gettext` catalog loading.
- `legal` — Project identity and legal-document discovery in source, wheels,
  and frozen executables.
- `config` — GUI preferences in `~/.openlp-vault/config.json`.
- `discovery` — OpenLP data-directory discovery.
- `auth` — Google Drive OAuth and token persistence.
- `backup` — Temporary ZIP creation, SHA-256 hashing, and Drive upload.
- `restore` — Backup listing, download, application, and deletion.
- `versioning` and `integrity` — Metadata and SHA-256 utilities.
- `recovery` — Local snapshot helpers, currently not exposed by the CLI.
- `observability` — Logging configuration.
- `compatibility` — Cross-platform extension point; normalization is not yet
  implemented.

## Internationalization

Source strings in `gui.py` and `cli.py` are English and act as the natural
`gettext` fallback. Spanish translations live in:

```text
src/openlp_vault/locale/es/LC_MESSAGES/openlp_vault.po
src/openlp_vault/locale/es/LC_MESSAGES/openlp_vault.mo
```

At startup, the language is resolved from `LC_ALL`, `LC_MESSAGES`, and
`LANG`. Regional values such as `es_CL.UTF-8` normalize to `es`.
Unsupported locales use English. PyInstaller scripts collect package data so
the catalog is included in Windows, macOS, and AppImage builds.

## OpenLP discovery

`find_openlp_installation()` checks `OPENLP_PATH` first, followed by
platform-specific default locations. A directory is accepted when it contains
at least one marker: `songs`, `bibles`, `images`, or `presentations`.
Not all markers are required.

## Persistence

```text
~/.openlp-vault/config.json
~/.openlp-vault/token.json
```

The configuration stores the credentials path, OpenLP data directory, and
Drive folder name. Language is not persisted.
