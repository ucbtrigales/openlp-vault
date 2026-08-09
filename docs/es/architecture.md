# Arquitectura

[English](../en/architecture.md) | Español

El código se distribuye como el paquete `openlp_vault` dentro de `src/`. La
GUI y la CLI son capas de presentación separadas que reutilizan los módulos de
autenticación, respaldo y restauración.

## Módulos

- `gui` — Interfaz de escritorio construida con Tkinter.
- `cli` — Comandos `auth`, `backup`, `restore` y `delete` con Click.
- `i18n` — Detección del idioma y carga de catálogos con `gettext`.
- `legal` — Identidad del proyecto y localización de documentos legales en
  el código fuente, wheels y ejecutables congelados.
- `config` — Preferencias de la GUI en `~/.openlp-vault/config.json`.
- `discovery` — Localización del directorio de datos de OpenLP.
- `auth` — OAuth de Google Drive y persistencia del token.
- `backup` — Creación del ZIP temporal, hash SHA-256 y subida a Drive.
- `restore` — Listado, descarga, aplicación y eliminación de respaldos.
- `versioning` e `integrity` — Metadatos y utilidades SHA-256.
- `recovery` — Funciones de instantáneas locales, no expuestas por la CLI.
- `observability` — Configuración del registro.
- `compatibility` — Punto de extensión multiplataforma; la normalización aún
  no está implementada.

## Internacionalización

Los textos fuente de `gui.py` y `cli.py` están en inglés y sirven como
fallback natural de `gettext`. La traducción española está en:

```text
src/openlp_vault/locale/es/LC_MESSAGES/openlp_vault.po
src/openlp_vault/locale/es/LC_MESSAGES/openlp_vault.mo
```

El idioma se resuelve al iniciar desde `LC_ALL`, `LC_MESSAGES` y `LANG`.
Valores regionales como `es_CL.UTF-8` se normalizan a `es`. Los idiomas no
compatibles usan inglés. Los scripts de PyInstaller recopilan los datos del
paquete para incluir el catálogo en Windows, macOS y AppImage.

## Descubrimiento de OpenLP

`find_openlp_installation()` prueba primero `OPENLP_PATH` y después las
rutas predeterminadas de cada sistema. Una carpeta se acepta si contiene al
menos un marcador: `songs`, `bibles`, `images` o `presentations`. No es
necesario que estén todos.

## Persistencia

```text
~/.openlp-vault/config.json
~/.openlp-vault/token.json
```

La configuración contiene la ruta de credenciales, el directorio de OpenLP y
el nombre de la carpeta de Drive. El idioma no se almacena.
