# Especificaciones

## Descripción general

La aplicación permite mantener sincronizada la información de OpenLP entre múltiples equipos mediante respaldos almacenados en Google Drive.

El sistema abstrae la complejidad del proceso de respaldo y restauración, ofreciendo una experiencia simple y consistente para usuarios que trabajan desde distintos computadores y sistemas operativos.

La unidad de sincronización es un respaldo completo de la instalación de OpenLP. En todo momento existe una única versión vigente de la información, representada por el respaldo más reciente disponible en Google Drive.

La aplicación no administra el contenido de OpenLP ni modifica su funcionamiento. Su responsabilidad consiste únicamente en preservar y transferir el estado de una instalación entre distintos dispositivos.

---

# Actores

## Usuario

Persona que administra el contenido de OpenLP y desea trasladar su configuración, canciones, recursos y demás información entre distintos equipos.

El usuario interactúa exclusivamente con la aplicación de respaldo y restauración.

---

## Google Drive

Servicio de almacenamiento utilizado como repositorio central de respaldos.

Representa el punto de intercambio entre todos los dispositivos autorizados.

---

## OpenLP

Aplicación cuya información es respaldada y posteriormente restaurada.

Su contenido constituye el objeto de trabajo del sistema, pero permanece completamente independiente de éste.

---

# Features

## Descubrimiento

La aplicación identifica la instalación de OpenLP presente en el equipo y determina el conjunto de información que forma parte del respaldo.

---

## Autenticación

La aplicación establece la identidad del usuario y obtiene acceso al espacio de almacenamiento utilizado para conservar los respaldos.

---

## Respaldo

La aplicación captura el estado completo de OpenLP existente en el dispositivo y lo publica como una nueva versión disponible para los demás equipos.

---

## Restauración

La aplicación recupera una versión previamente respaldada y reconstruye el estado de OpenLP en el dispositivo local.

---

## Versionado

Cada respaldo representa un estado completo e identificable de la información, permitiendo distinguir distintas versiones a lo largo del tiempo.

---

## Integridad

El sistema permite determinar que un respaldo corresponde exactamente al contenido que fue publicado originalmente.

---

## Compatibilidad

La información puede trasladarse entre equipos con distintos sistemas operativos preservando su contenido.

---

## Recuperación

Antes de reemplazar la información local, el sistema conserva el estado existente para facilitar la recuperación ante errores o decisiones incorrectas.

---

## Observabilidad

El sistema informa el estado de las operaciones realizadas y conserva evidencia suficiente para comprender su resultado.

---

## Configuración

La aplicación mantiene un conjunto reducido de preferencias relacionadas con el funcionamiento del proceso de respaldo y restauración, sin intervenir en la configuración propia de OpenLP.
