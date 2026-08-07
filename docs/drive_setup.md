# Configurar acceso a Google Drive

1. Abre Google Cloud Console: https://console.cloud.google.com/
2. Selecciona el proyecto nuevo de tu Google Workspace.
3. Habilita la API de Google Drive:
   - Ve a `APIs y servicios` → `Biblioteca`
   - Busca `Google Drive API`
   - Haz clic en `Habilitar`
4. Configura la pantalla de consentimiento OAuth:
   - Ve a `APIs y servicios` → `Pantalla de consentimiento OAuth`
   - Selecciona `Interna` si solo lo usarán usuarios del dominio
   - Completa nombre de la aplicación, correo de soporte y demás datos básicos
   - Guarda los cambios
5. Crea credenciales de OAuth:
   - Ve a `APIs y servicios` → `Credenciales`
   - Haz clic en `+ Crear credenciales`
   - Elige `ID de cliente OAuth`
   - Selecciona `Aplicación de escritorio`
   - Pon un nombre descriptivo, por ejemplo `OpenLP Vault Desktop`
   - Descarga el JSON
6. Guarda el archivo descargado como `credentials.json` en la raíz del proyecto:
   - `/home/christian/Proyectos/Iglesia/OpenLP Vault/credentials.json`

## Autenticación en el proyecto

1. Activa el entorno virtual:

```bash
cd '/home/christian/Proyectos/Iglesia/OpenLP Vault'
source .venv/bin/activate
```

2. Ejecuta el comando de autenticación explícita:

```bash
openlp-vault auth --credentials credentials.json --debug
```

3. Sigue el flujo del navegador para autorizar la app.
4. Después de autorizar, el token se guardará en `~/.openlp-vault/token.json`.

## Uso adicional

- Para detectar la instalación de OpenLP:

```bash
openlp-vault discover --debug
```

- Para crear solo el ZIP sin subirlo:

```bash
openlp-vault backup --no-upload --debug
```

- Para crear y subir el respaldo:

```bash
openlp-vault backup --debug
```

- Para forzar una ruta de OpenLP:

```bash
OPENLP_PATH=/ruta/a/openlp openlp-vault backup --debug --no-upload
```

- Para listar respaldos disponibles en Drive:

```bash
openlp-vault restore --list-only --debug
```

- Para restaurar un respaldo:

```bash
openlp-vault restore --debug
```

- Para eliminar un respaldo de Drive:

```bash
openlp-vault delete --debug
```

Nota: usa el scope `drive.file` para limitar el acceso a los archivos que crea la aplicación.
