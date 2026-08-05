# Uso básico

Instalar dependencias y el paquete en editable mode:

```bash
python -m pip install -r requirements.txt
python -m pip install -e .
```

Ejecutar la CLI:

```bash
openlp-vault --help
python -m openlp_vault.cli -h
```

Comandos principales:

- `auth` — Autentica con Google Drive y guarda el token.
- `discover` — Detecta la instalación local de OpenLP.
- `backup` — Crea y publica un respaldo.
- `restore` — Restaura desde Drive.

## Autenticación

1. Genera un OAuth client ID de tipo "Aplicación de escritorio" en Google Cloud Console.
2. Descarga el JSON de credenciales y colócalo en la raíz del proyecto como `credentials.json`.
3. Ejecuta:

```bash
openlp-vault auth --credentials credentials.json --debug
```

El token se guardará por defecto en `~/.openlp_vault/token.json`.

## Descubrimiento de OpenLP

```bash
openlp-vault discover --debug
```

Si el directorio no se detecta automáticamente, usa:

```bash
OPENLP_PATH=/ruta/a/openlp openlp-vault discover --debug
```

## Respaldo

Crear solo el archivo ZIP local:

```bash
openlp-vault backup --no-upload --debug
```

Crear y subir el respaldo a Google Drive:

```bash
openlp-vault backup --debug
```

Forzar la ruta de OpenLP si no se detecta automáticamente:

```bash
openlp-vault backup --source /ruta/a/openlp --debug
```

## Restauración

Listar respaldos disponibles en Drive:

```bash
openlp-vault restore --list-only --debug
```

Restaurar seleccionando el respaldo de forma interactiva:

```bash
openlp-vault restore --debug
```

Restaurar un respaldo específico por su ID:

```bash
openlp-vault restore --backup-id <ID> --destination /ruta/a/openlp --debug
```

Guardar un snapshot local antes de restaurar:

```bash
openlp-vault restore --backup-id <ID> --destination /ruta/a/openlp --snapshot-dir /ruta/a/snapshot --debug
```

## Eliminación de respaldos

Eliminar un respaldo de Drive de forma interactiva:

```bash
openlp-vault delete --debug
```

Eliminar un respaldo por ID:

```bash
openlp-vault delete --backup-id <ID> --debug
```

Eliminar sin confirmación:

```bash
openlp-vault delete --backup-id <ID> --force --debug
```
