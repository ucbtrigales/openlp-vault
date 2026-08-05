Feature: Respaldo y restauración de OpenLP mediante Google Drive

  Background:
    Given existe una aplicación de escritorio desarrollada en Python
    And la aplicación utiliza la API oficial de Google Drive mediante OAuth 2.0
    And la aplicación es compatible con Windows, macOS y Linux
    And el usuario ha iniciado sesión en Google previamente
    And OpenLP utiliza una carpeta de datos local
    And la aplicación puede detectar automáticamente la ubicación de dicha carpeta

  Rule: Nunca debe modificarse la carpeta de datos mientras OpenLP esté abierto.

  ###########################################################################
  # Descubrimiento de la instalación
  ###########################################################################

  Scenario: Detectar automáticamente la carpeta de datos de OpenLP
    Given OpenLP está instalado en el equipo
    When el usuario inicia la aplicación
    Then la aplicación debe localizar automáticamente la carpeta de datos
    And debe mostrar la ruta encontrada
    And debe permitir modificarla manualmente si el usuario lo desea

  Scenario: No se encuentra la carpeta de datos
    Given la carpeta de datos no puede localizarse automáticamente
    When el usuario inicia la aplicación
    Then la aplicación debe solicitar seleccionar la carpeta manualmente
    And debe recordar dicha ubicación para futuros usos

  ###########################################################################
  # Interfaz principal
  ###########################################################################

  Scenario: Mostrar una interfaz simple
    When la aplicación se abre
    Then debe mostrar una ventana con un diseño simple
    And debe contener un botón "Subir respaldo"
    And debe contener un botón "Restaurar respaldo"
    And debe mostrar la fecha del último respaldo disponible
    And debe mostrar el tamaño del último respaldo
    And debe mostrar la versión de OpenLP detectada
    And debe indicar el estado de conexión con Google Drive

  ###########################################################################
  # Autenticación
  ###########################################################################

  Scenario: Primer inicio de sesión
    Given el usuario nunca ha iniciado sesión
    When selecciona cualquier operación que requiera Google Drive
    Then debe abrirse el navegador para autenticar al usuario
    And debe solicitar permisos únicamente para la carpeta utilizada por la aplicación
    And las credenciales deben almacenarse de forma segura

  Scenario: Reutilizar credenciales existentes
    Given el usuario ya inició sesión anteriormente
    When abre nuevamente la aplicación
    Then la autenticación debe realizarse automáticamente

  ###########################################################################
  # Crear respaldo
  ###########################################################################

  Scenario: Crear y subir un respaldo correctamente
    Given OpenLP está cerrado
    When el usuario presiona "Subir respaldo"
    Then la aplicación debe verificar que OpenLP no está ejecutándose
    And debe generar un archivo ZIP con toda la carpeta de datos
    And el nombre del archivo debe seguir el formato
      """
      OpenLP-YYYY-MM-DD_HH-MM.zip
      """
    And debe calcular el hash SHA-256 del archivo
    And debe subir el ZIP a Google Drive
    And debe subir el hash correspondiente
    And debe mostrar una barra de progreso
    And debe informar que el respaldo fue exitoso

  Scenario: Intentar crear un respaldo con OpenLP abierto
    Given OpenLP está ejecutándose
    When el usuario presiona "Subir respaldo"
    Then la aplicación debe advertir que OpenLP debe cerrarse
    And no debe continuar hasta que OpenLP haya sido cerrado

  ###########################################################################
  # Gestión de respaldos
  ###########################################################################

  Scenario: Mantener un historial de respaldos
    Given existen más de veinte respaldos almacenados
    When se completa un nuevo respaldo
    Then la aplicación debe conservar únicamente los veinte más recientes
    And debe eliminar automáticamente los más antiguos

  Scenario: Consultar los respaldos disponibles
    When el usuario abre la lista de respaldos
    Then debe visualizar la fecha de creación
    And el tamaño del archivo
    And la versión de OpenLP utilizada
    And el hash SHA-256
    And el nombre del archivo

  ###########################################################################
  # Restauración
  ###########################################################################

  Scenario: Restaurar el respaldo más reciente
    Given OpenLP está cerrado
    And existe al menos un respaldo en Google Drive
    When el usuario presiona "Restaurar respaldo"
    Then la aplicación debe descargar el respaldo más reciente
    And debe descargar el hash asociado
    And debe verificar la integridad del archivo
    And debe crear un respaldo automático de la instalación local
    And debe reemplazar la carpeta de datos
    And debe informar que la restauración fue exitosa

  Scenario: Restaurar un respaldo antiguo
    Given existen múltiples respaldos
    When el usuario selecciona uno específico
    Then la aplicación debe restaurar exactamente ese respaldo

  ###########################################################################
  # Compatibilidad de versiones
  ###########################################################################

  Scenario: Restaurar un respaldo creado con una versión distinta de OpenLP
    Given el respaldo fue creado con una versión diferente
    When el usuario intenta restaurarlo
    Then la aplicación debe mostrar ambas versiones
    And debe advertir sobre posibles incompatibilidades
    And debe solicitar confirmación antes de continuar

  ###########################################################################
  # Integridad
  ###########################################################################

  Scenario: Detectar un respaldo corrupto
    Given el archivo ZIP fue alterado
    When la aplicación verifica el hash
    Then la verificación debe fallar
    And la restauración debe cancelarse
    And el usuario debe ser informado del problema

  ###########################################################################
  # Respaldo automático previo
  ###########################################################################

  Scenario: Crear un respaldo antes de restaurar
    Given existe información local
    When comienza una restauración
    Then la aplicación debe crear un respaldo automático local
    And dicho respaldo debe incluir fecha y hora
    And debe permitir recuperarlo posteriormente

  ###########################################################################
  # Estado y progreso
  ###########################################################################

  Scenario: Mostrar progreso de una operación
    When se realiza una subida o descarga
    Then debe mostrarse una barra de progreso
    And debe mostrarse la velocidad de transferencia
    And debe mostrarse el tamaño transferido
    And debe mostrarse el tiempo restante estimado

  ###########################################################################
  # Manejo de errores
  ###########################################################################

  Scenario: Sin conexión a Internet
    Given no existe conexión a Internet
    When el usuario intenta subir un respaldo
    Then debe mostrarse un mensaje indicando el problema
    And la operación debe cancelarse

  Scenario: Google Drive no disponible
    Given Google Drive no responde
    When el usuario intenta cualquier operación
    Then la aplicación debe informar el error
    And no debe modificar los datos locales

  Scenario: Espacio insuficiente en Google Drive
    Given el espacio disponible es insuficiente
    When se intenta subir un respaldo
    Then la subida debe cancelarse
    And debe mostrarse un mensaje indicando el espacio restante

  ###########################################################################
  # Seguridad
  ###########################################################################

  Scenario: Limitar el acceso a Google Drive
    Then la aplicación debe acceder únicamente a su carpeta de respaldos
    And no debe solicitar permisos para acceder al resto de Google Drive

  ###########################################################################
  # Configuración
  ###########################################################################

  Scenario: Configurar el número máximo de respaldos
    When el usuario modifica la configuración
    Then debe poder indicar cuántos respaldos conservar
    And el valor por defecto debe ser veinte

  Scenario: Configurar el nombre de la carpeta de Google Drive
    When el usuario cambia el nombre de la carpeta
    Then todos los respaldos futuros deben almacenarse allí

  ###########################################################################
  # Registro de eventos
  ###########################################################################

  Scenario: Registrar todas las operaciones
    When ocurre cualquier respaldo o restauración
    Then debe registrarse la fecha y hora
    And el tipo de operación
    And el resultado
    And la duración
    And cualquier mensaje de error

  ###########################################################################
  # Plataforma
  ###########################################################################

  Scenario Outline: Ejecutar correctamente en distintos sistemas operativos
    Given la aplicación se ejecuta en "<Sistema>"
    When el usuario crea un respaldo
    Then la operación debe completarse correctamente
    And el respaldo debe poder restaurarse desde cualquier otro sistema operativo compatible

    Examples:
      | Sistema |
      | Windows |
      | macOS   |
      | Linux   |
