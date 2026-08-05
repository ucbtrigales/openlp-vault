# Arquitectura

El proyecto está organizado en un paquete `openlp_vault` con módulos que reflejan las features especificadas:

- `discovery` — Detecta la instalación local de OpenLP.
- `auth` — Maneja autenticación con Google Drive.
- `backup`/`restore` — Lógica de respaldo y restauración.
- `versioning` — Metadatos de cada respaldo.
- `integrity` — Comprobación de integridad (hashes/firmas).
- `compatibility` — Ajustes entre plataformas.
- `recovery` — Instantáneas locales para recuperación.
- `observability` — Logging y métricas.
