# Configurar acceso a Google Drive

[English](../en/drive_setup.md) | Español

OpenLP Vault necesita un cliente OAuth de tipo aplicación de escritorio para
acceder a Google Drive en nombre del usuario.

## Crear las credenciales

1. Abre [Google Cloud Console](https://console.cloud.google.com/).
2. Crea o selecciona un proyecto.
3. En **APIs y servicios → Biblioteca**, busca y habilita **Google Drive API**.
4. Configura la pantalla de consentimiento OAuth:
   - Selecciona el tipo de usuario apropiado para tu cuenta u organización.
   - Completa el nombre de la aplicación y los datos de contacto solicitados.
   - Si la aplicación permanece en modo de prueba, agrega las cuentas que la
     utilizarán como usuarios de prueba.
5. En **APIs y servicios → Credenciales**, crea un **ID de cliente OAuth**.
6. Selecciona **Aplicación de escritorio**.
7. Descarga el archivo JSON y guárdalo en una ubicación accesible, por ejemplo
   como `credentials.json`.

No publiques `credentials.json` ni `~/.openlp-vault/token.json` en el
repositorio.

## Conectar desde la GUI

Ejecuta:

```bash
openlp-vault-gui
```

En la primera ejecución se abrirá Configuración:

1. Selecciona `credentials.json`.
2. Selecciona el directorio de datos de OpenLP.
3. Conserva o modifica el nombre de la carpeta de Google Drive.
4. Pulsa **Conectar con Google Drive**.
5. Completa la autorización en el navegador.
6. Cuando la barra indique que Drive está conectado, acepta la configuración.

La autorización desde la GUI puede cancelarse y tiene un tiempo de espera de
dos minutos.

## Conectar desde la CLI

```bash
openlp-vault auth --credentials /ruta/a/credentials.json
```

El navegador abrirá el flujo de autorización. De forma predeterminada, el
token resultante se guarda en:

```text
~/.openlp-vault/token.json
```

Se puede elegir otra ubicación con `--token-path`.

## Permisos utilizados

La aplicación solicita estos scopes:

- `drive.file` para crear y administrar los archivos que genera.
- `drive.metadata.readonly` para consultar metadatos y listar respaldos.

Los respaldos se guardan por defecto en una carpeta llamada `OpenLP Vault`.
Si no existe, la aplicación la crea en la raíz de Drive. La CLI permite usar
`--folder-name` o `--parent-folder-id` durante el respaldo.

## Solución de problemas

- Si aparece un error de credenciales, confirma que el JSON corresponde a un
  cliente OAuth de escritorio y contiene `client_id` y `client_secret`.
- Si el navegador no completa la autorización, vuelve a intentarlo y comprueba
  que la cuenta esté habilitada como usuario de prueba cuando corresponda.
- Para descartar una autorización guardada desde la GUI, usa
  **Desconectar Google Drive**. También puedes retirar manualmente el token
  local en `~/.openlp-vault/token.json`.
- Si no se detecta OpenLP, selecciona el directorio en la GUI o define
  `OPENLP_PATH` para la CLI.
