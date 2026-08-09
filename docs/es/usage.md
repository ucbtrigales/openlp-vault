# Guía de uso

[English](../en/usage.md) | Español

## Interfaz gráfica

Crea las credenciales siguiendo
[la guía de Google Drive](drive_setup.md).

Inicia la aplicación con:

```bash
openlp-vault-gui
```

Si no hay un token OAuth reutilizable, la ventana de configuración se abre en
la primera ejecución. Debes indicar:

- La ruta de `credentials.json`.
- El directorio de datos de OpenLP.
- El nombre de la carpeta de Google Drive; por defecto, `OpenLP Vault`.

Desde la ventana principal se puede:

- Crear y subir un respaldo.
- Crear solamente un respaldo local.
- Consultar, descargar y restaurar respaldos.
- Eliminar respaldos de Drive.
- Abrir nuevamente la configuración o desconectar Google Drive.

La configuración se guarda en `~/.openlp-vault/config.json` y el token OAuth
en `~/.openlp-vault/token.json`.

### Capturas de pantalla

Ventana principal:

![Ventana principal de OpenLP Vault](../assets/screenshots/es/main-window.png)

Crear y subir un respaldo:

![Crear y subir un respaldo](../assets/screenshots/es/upload-backup.png)

Descargar y restaurar un respaldo:

![Descargar y restaurar un respaldo](../assets/screenshots/es/download-backup.png)

Configuración:

![Configuración de OpenLP Vault](../assets/screenshots/es/settings.png)

## Interfaz de línea de comandos

```bash
openlp-vault --help
```

Los comandos disponibles son `auth`, `backup`, `restore` y `delete`.
No existe un subcomando `discover`: el descubrimiento se ejecuta
automáticamente cuando `backup` o `restore` necesitan una ruta.

### Autenticación

Después de crear las credenciales según
[la guía de Google Drive](drive_setup.md), ejecuta:

```bash
openlp-vault auth --credentials credentials.json
```

Opciones relevantes:

- `--credentials FILE` — Archivo OAuth de Google.
- `--token-path PATH` — Ubicación alternativa para leer o guardar el token.
- `--debug` — Registro detallado.

### Descubrimiento del directorio de OpenLP

La aplicación consulta primero `OPENLP_PATH` y después las rutas habituales
de Linux, macOS o Windows. Una ruta se acepta si contiene al menos uno de los
directorios `songs`, `bibles`, `images` o `presentations`.

```bash
OPENLP_PATH=/ruta/a/openlp openlp-vault backup --no-upload
```

También se puede proporcionar la ruta directamente:

```bash
openlp-vault backup --source /ruta/a/openlp
```

### Respaldo

Crear un ZIP local temporal sin subirlo:

```bash
openlp-vault backup --no-upload
```

Crear y subir un respaldo a la carpeta `OpenLP Vault`:

```bash
openlp-vault backup
```

Elegir otra carpeta de Drive o un padre conocido:

```bash
openlp-vault backup --folder-name "Respaldos OpenLP"
openlp-vault backup --parent-folder-id ID_DE_LA_CARPETA
```

Los nombres generados comienzan por `openlp_backup_`. Tras una subida
correcta, el ZIP temporal se elimina.

### Restauración

Primero consulta los respaldos y toma el valor mostrado como `id`:

```bash
openlp-vault restore --list-only
```

Después restaura el respaldo indicando su ID:

```bash
openlp-vault restore \
  --backup-id ID_DEL_RESPALDO \
  --destination /ruta/a/openlp
```

Si se omite `--destination`, se intenta detectar el directorio de OpenLP y,
si no se encuentra, se solicita la ruta. La restauración reemplaza el
directorio de destino con el contenido del ZIP; cierra OpenLP antes de
continuar.

### Eliminación

Listar los respaldos y seleccionar uno interactivamente:

```bash
openlp-vault delete
```

Eliminar uno conocido por ID:

```bash
openlp-vault delete --backup-id ID_DEL_RESPALDO
```

Omitir la confirmación:

```bash
openlp-vault delete --backup-id ID_DEL_RESPALDO --force
```

La eliminación en Google Drive no se puede deshacer desde OpenLP Vault.

## Instalación para desarrollo

OpenLP Vault requiere Python 3.10 o posterior:

```bash
python -m pip install -r requirements.txt
python -m pip install -e .
```

También puedes ejecutar `./setup.sh`, que crea `.venv`, instala las
dependencias y deja el paquete en modo editable.

## Información legal y del proyecto

La ayuda de la CLI incluye una referencia breve a la licencia. Para mostrar
copyright, licencia, mantenimiento, contacto y URL del proyecto, ejecuta:

```bash
openlp-vault license
```

En la GUI, pulsa el texto subrayado `OpenLP Vault VERSIÓN` de Configuración
para abrir **Acerca de OpenLP Vault**. El diálogo enlaza al correo del
mantenedor y a <https://ucbtrigales.github.io/openlp-vault/es/>, y permite
consultar `LICENSE` y `NOTICE` en vistas desplazables.
