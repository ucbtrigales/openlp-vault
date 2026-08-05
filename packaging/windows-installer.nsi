!include "MUI2.nsh"
Name "OpenLP Vault"
OutFile "dist\\OpenLPVault-installer.exe"
InstallDir "$PROGRAMFILES\\OpenLP Vault"
ShowInstDetails show

Page directory
Page instfiles

Section "Install"
  SetOutPath "$INSTDIR"
  File "dist\\openlp-vault-gui.exe"
  File "dist\\openlp-vault.exe"
  CreateShortCut "$SMPROGRAMS\\OpenLP Vault.lnk" "$INSTDIR\\openlp-vault-gui.exe"
SectionEnd

Section "Uninstall"
  Delete "$INSTDIR\\openlp-vault-gui.exe"
  Delete "$INSTDIR\\openlp-vault.exe"
  Delete "$SMPROGRAMS\\OpenLP Vault.lnk"
  RMDir "$INSTDIR"
SectionEnd
