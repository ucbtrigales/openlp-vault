!define PRODUCT_NAME "OpenLP Vault"
!define PRODUCT_VERSION "0.1.0"
!define PRODUCT_PUBLISHER "UCB Trigales"
!define OUT_FILE "dist\OpenLPVault-Setup-v0.1.0.exe"

OutFile "${OUT_FILE}"
InstallDir "$PROGRAMFILES64\OpenLP Vault"
RequestExecutionLevel admin

Page directory
Page instfiles

UninstPage uninstConfirm
UninstPage instfiles

Section "MainSection" SEC01
    SetOutPath "$WORKDIR"
    SetOutPath "$INSTDIR"
    
    # Incluye AMBOS archivos compilados en el instalador final
    File "dist\openlp-vault.exe"
    File "dist\openlp-vault-gui.exe"
    
    # Si tienes un icono para el ejecutable o instalador:
    # File "packaging\openlp-vault.ico"

    # Accesos directos (Apuntando a la versión GUI como principal)
    CreateDirectory "$SMPROGRAMS\OpenLP Vault"
    CreateShortCut "$SMPROGRAMS\OpenLP Vault\OpenLP Vault.lnk" "$INSTDIR\openlp-vault-gui.exe"
    CreateShortCut "$DESKTOP\OpenLP Vault.lnk" "$INSTDIR\openlp-vault-gui.exe"

    # Agregar carpeta de instalación al PATH para que la CLI funcione desde la línea de comandos
    ReadRegExpandStr $0 "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Environment" "Path"
    ${If} $0 == ""
      StrCpy $0 "$INSTDIR"
    ${Else}
      StrCpy $0 "$0;$INSTDIR"
    ${EndIf}
    WriteRegExpandStr "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Environment" "Path" $0
    System::Call 'Kernel32::SetEnvironmentVariableA(t, t) i("Path", "$0")'
    
    # Desinstalador
    WriteUninstaller "$INSTDIR\uninstall.exe"
    CreateShortCut "$SMPROGRAMS\OpenLP Vault\Uninstall.lnk" "$INSTDIR\uninstall.exe"
SectionEnd

Section "Uninstall"
    Delete "$INSTDIR\openlp-vault.exe"
    Delete "$INSTDIR\openlp-vault-gui.exe"
    Delete "$INSTDIR\uninstall.exe"
    RMDir "$INSTDIR"

    Delete "$SMPROGRAMS\OpenLP Vault\OpenLP Vault.lnk"
    Delete "$SMPROGRAMS\OpenLP Vault\Uninstall.lnk"
    RMDir "$SMPROGRAMS\OpenLP Vault"
    Delete "$DESKTOP\OpenLP Vault.lnk"
SectionEnd