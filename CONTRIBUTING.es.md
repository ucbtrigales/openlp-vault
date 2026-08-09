# Contribuir a OpenLP Vault

[English](CONTRIBUTING.md) | Español

## Licencia de las contribuciones

OpenLP Vault se publica bajo `GPL-3.0-or-later`.

Al enviar una contribución, certificas que tienes derecho a hacerlo y aceptas
que se proporcione bajo la Licencia Pública General de GNU, versión 3 o, a
elección del destinatario, cualquier versión posterior. No se exige una cesión
de copyright: cada colaborador conserva los derechos sobre su trabajo.

No envíes código, traducciones, imágenes, documentación u otro material que no
pueda distribuirse bajo `GPL-3.0-or-later`. Identifica claramente cualquier
material de terceros y su licencia.

## Autoría

Usa tu propia identidad en los commits de Git y conserva los avisos existentes
de autoría y copyright. El historial de Git es el registro principal de
contribuciones del proyecto. No reescribas la autoría de otro colaborador.

## Antes de enviar cambios

Ejecuta las comprobaciones automáticas:

```bash
.venv/bin/python -m pytest
git diff --check
```

Mantén sincronizada la documentación en inglés y español cuando cambie el
comportamiento o las instrucciones para usuarios.
