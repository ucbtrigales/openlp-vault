# OpenLP Vault

[English](README.md) | Español

OpenLP Vault crea respaldos completos de los datos de OpenLP y permite
guardarlos, restaurarlos y eliminarlos mediante Google Drive.

Proyecto: <https://ucbtrigales.github.io/openlp-vault/es/>

Repositorio: <https://github.com/ucbtrigales/openlp-vault>

## Características

- Interfaz gráfica para crear respaldos locales o subirlos a Google Drive.
- Descarga, restauración y eliminación de respaldos.
- CLI para autenticación, respaldo, restauración y eliminación.
- Detección automática del directorio de OpenLP en Linux, macOS y Windows.
- Autenticación OAuth con reutilización del token local.
- Utilidades de integridad y versionado con SHA-256.
- Empaquetado para Windows, macOS y Linux AppImage.

## Uso rápido con la GUI

Crea las credenciales siguiendo
[la guía de Google Drive](docs/es/drive_setup.md).

Luego abre la interfaz gráfica:

```bash
openlp-vault-gui
```

![Ventana principal de OpenLP Vault](docs/assets/screenshots/es/main-window.png)

En la primera ejecución, la GUI abre Configuración si no existe una
autorización OAuth reutilizable. Selecciona `credentials.json`, el directorio
de OpenLP y el nombre de la carpeta de Google Drive.

## Interfaz de línea de comandos

Después de crear `credentials.json` mediante
[la guía de Google Drive](docs/es/drive_setup.md), autoriza la aplicación y
ejecuta la operación necesaria:

```bash
openlp-vault auth --credentials credentials.json
openlp-vault backup
openlp-vault restore --list-only
openlp-vault restore --backup-id ID_DEL_RESPALDO
openlp-vault delete --backup-id ID_DEL_RESPALDO
```

Consulta [la guía de uso](docs/es/usage.md) para conocer todas las opciones y
[la arquitectura](docs/es/architecture.md) para una descripción del código.

## Instalación para desarrollo

OpenLP Vault requiere Python 3.10 o posterior:

```bash
python -m pip install -r requirements.txt
python -m pip install -e .
```

También se puede usar el script de preparación:

```bash
./setup.sh
source .venv/bin/activate
```

## Licencia

Copyright © 2026 Christian González G.

OpenLP Vault es software libre publicado bajo la
[Licencia Pública General de GNU versión 3.0 o posterior](LICENSE)
(`GPL-3.0-or-later`). Las modificaciones distribuidas deben conservar la
misma licencia y proporcionar el código fuente correspondiente según la GPL.

El proyecto es mantenido por la comunidad de la Iglesia Evangélica Unión de
Centros Bíblicos «Trigales».

Las contribuciones se aceptan bajo esa misma licencia. Consulta
[CONTRIBUTING.es.md](CONTRIBUTING.es.md).
