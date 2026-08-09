!include "LogicLib.nsh"

!define PRODUCT_NAME "OpenLP Vault"
!ifndef PRODUCT_VERSION
!define PRODUCT_VERSION "0.0.0"
!endif
!define PRODUCT_PUBLISHER "UCB Trigales"
!define PROJECT_ROOT "${__FILEDIR__}\.."
!define OUT_FILE "${PROJECT_ROOT}\dist\OpenLPVault-Setup-v${PRODUCT_VERSION}.exe"

OutFile "${OUT_FILE}"
InstallDir "$PROGRAMFILES64\OpenLP Vault"
RequestExecutionLevel admin
Icon "${__FILEDIR__}\openlp-vault.ico"
UninstallIcon "${__FILEDIR__}\openlp-vault.ico"

LicenseData "${PROJECT_ROOT}\LICENSE"
Page license
Page directory
Page instfiles

UninstPage uninstConfirm
UninstPage instfiles

Section "MainSection" SEC01
    SetOutPath "$INSTDIR"
    
    # Incluye AMBOS archivos compilados en el instalador final
    File "${PROJECT_ROOT}\dist\openlp-vault.exe"
    File "${PROJECT_ROOT}\dist\openlp-vault-gui.exe"
    File "${PROJECT_ROOT}\LICENSE"
    File "${PROJECT_ROOT}\NOTICE"
    
    # Accesos directos (Apuntando a la versión GUI como principal)
    CreateDirectory "$SMPROGRAMS\OpenLP Vault"
    CreateShortCut "$SMPROGRAMS\OpenLP Vault\OpenLP Vault.lnk" "$INSTDIR\openlp-vault-gui.exe"
    CreateShortCut "$DESKTOP\OpenLP Vault.lnk" "$INSTDIR\openlp-vault-gui.exe"

    # Agregar carpeta de instalación al PATH para que la CLI funcione desde la línea de comandos
    ReadRegStr $0 HKLM "SYSTEM\CurrentControlSet\Control\Session Manager\Environment" "Path"
    ${If} $0 == ""
      StrCpy $0 "$INSTDIR"
    ${Else}
      StrCpy $0 "$0;$INSTDIR"
    ${EndIf}
    WriteRegExpandStr HKLM "SYSTEM\CurrentControlSet\Control\Session Manager\Environment" "Path" $0
    System::Call 'Kernel32::SetEnvironmentVariableA(t, t) i("Path", "$0")'
    
    # Desinstalador
    WriteUninstaller "$INSTDIR\uninstall.exe"
    CreateShortCut "$SMPROGRAMS\OpenLP Vault\Uninstall.lnk" "$INSTDIR\uninstall.exe"
SectionEnd

Section "Uninstall"
    Delete "$INSTDIR\openlp-vault.exe"
    Delete "$INSTDIR\openlp-vault-gui.exe"
    Delete "$INSTDIR\LICENSE"
    Delete "$INSTDIR\NOTICE"
    Delete "$INSTDIR\uninstall.exe"
    RMDir "$INSTDIR"

    Delete "$SMPROGRAMS\OpenLP Vault\OpenLP Vault.lnk"
    Delete "$SMPROGRAMS\OpenLP Vault\Uninstall.lnk"
    RMDir "$SMPROGRAMS\OpenLP Vault"
    Delete "$DESKTOP\OpenLP Vault.lnk"
SectionEnd
