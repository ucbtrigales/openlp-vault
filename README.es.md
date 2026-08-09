# OpenLP Vault

[English](README.md) | Español

OpenLP Vault crea respaldos completos de los datos de OpenLP y permite
guardarlos, restaurarlos y eliminarlos mediante Google Drive.

## Características

- Interfaz gráfica para crear respaldos locales o subirlos a Google Drive.
- Descarga, restauración y eliminación de respaldos.
- CLI para autenticación, respaldo, restauración y eliminación.
- Detección automática del directorio de OpenLP en Linux, macOS y Windows.
- Autenticación OAuth con reutilización del token local.
- Interfaz en inglés y español según el idioma del sistema.
- Utilidades de integridad y versionado con SHA-256.
- Empaquetado para Windows, macOS y Linux AppImage.

## Instalación para desarrollo

OpenLP Vault requiere Python 3.8 o posterior:

```bash
python -m pip install -r requirements.txt
python -m pip install -e .
```

También se puede usar el script de preparación:

```bash
./setup.sh
source .venv/bin/activate
```

## Uso rápido

Crea las credenciales siguiendo
[la guía de Google Drive](docs/es/drive_setup.md).

```bash
openlp-vault auth --credentials credentials.json
openlp-vault backup
openlp-vault restore --list-only
openlp-vault restore --backup-id ID_DEL_RESPALDO
openlp-vault delete --backup-id ID_DEL_RESPALDO
```

Abre la interfaz gráfica con:

```bash
openlp-vault-gui
```

En la primera ejecución, la GUI abre Configuración si no existe una
autorización OAuth reutilizable. Selecciona `credentials.json`, el directorio
de OpenLP y el nombre de la carpeta de Google Drive.

## Idioma

OpenLP Vault consulta `LC_ALL`, `LC_MESSAGES` y `LANG`, en ese orden.
Admite inglés y español, y utiliza inglés para idiomas no compatibles.

```bash
LANG=es_CL.UTF-8 openlp-vault --help
LANG=en_US.UTF-8 openlp-vault-gui
```

Consulta [la guía de uso](docs/es/usage.md) para conocer todas las opciones y
[la arquitectura](docs/es/architecture.md) para una descripción del código.
