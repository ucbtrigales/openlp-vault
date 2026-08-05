# OpenLP Vault

Herramienta para sincronizar respaldos completos de OpenLP usando Google Drive.

Características principales:

- Descubrimiento de instalación local de OpenLP
- Autenticación con Google Drive
- Respaldo y restauración de la instalación completa
- Eliminación de respaldos en Drive
- Versionado, integridad y recuperación
- CLI mínima para operaciones comunes

## Uso rápido

```bash
python -m pip install -r requirements.txt
python -m pip install -e .
```

```bash
openlp-vault auth --credentials credentials.json
openlp-vault backup --debug
openlp-vault restore --debug
openlp-vault delete --debug
```

Vea `docs/usage.md` para instrucciones completas.

## Interfaz gráfica

Si prefieres una interfaz visual, usa:

```bash
openlp-vault-gui
```

La GUI es portable y funciona en Windows, macOS y Linux siempre que Python y Tkinter estén disponibles.
