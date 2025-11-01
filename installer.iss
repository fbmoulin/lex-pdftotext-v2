; Script Inno Setup para PDF Legal Extractor
; Gera instalador Windows (.exe)

#define MyAppName "PDF Legal Extractor"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Felipe Bertrand Sardenberg Moulin"
#define MyAppURL "https://github.com/fbmoulin/pdftotext"
#define MyAppExeName "PDF2MD.exe"

[Setup]
; Informações do aplicativo
AppId={{E5B7C3A0-1234-4567-89AB-CDEF01234567}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}

; Diretórios de instalação
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes

; Licença (opcional - criar arquivo LICENSE.txt se necessário)
;LicenseFile=LICENSE.txt

; Arquivo README (opcional)
;InfoBeforeFile=README.txt

; Saída do instalador
OutputDir=Output
OutputBaseFilename=PDF2MD_Setup
SetupIconFile=assets\logo.ico
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern

; Privilégios
PrivilegesRequired=admin
PrivilegesRequiredOverridesAllowed=dialog

; Arquitetura
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64

; Visual
WindowVisible=no
WindowShowCaption=yes
WindowStartMaximized=no
ShowLanguageDialog=no

[Languages]
Name: "portuguese"; MessagesFile: "compiler:Languages\Portuguese.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: checkablealone
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked; OnlyBelowVersion: 6.1; Check: not IsAdminInstallMode

[Files]
; Executável principal
Source: "dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion

; Documentação (opcional - descomente se existir)
;Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion; DestName: "LEIA-ME.txt"
;Source: "LICENSE.txt"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
; Ícone no Menu Iniciar
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"

; Ícone na Área de Trabalho
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

; Ícone na Barra de Tarefas
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: quicklaunchicon

[Run]
; Executar aplicativo após instalação (opcional)
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Limpar configurações do usuário ao desinstalar (opcional)
Type: filesandordirs; Name: "{userappdata}\{#MyAppName}"

[Code]
// Função para detectar se aplicativo já está rodando
function InitializeSetup(): Boolean;
var
  ResultCode: Integer;
begin
  Result := True;

  // Verificar se o aplicativo já está em execução
  if CheckForMutexes('Global\PDF2MD_Mutex') then
  begin
    if MsgBox('O PDF Legal Extractor parece estar em execução.' + #13#10 + #13#10 +
              'Por favor, feche o aplicativo antes de continuar com a instalação.' + #13#10 + #13#10 +
              'Deseja tentar novamente?',
              mbError, MB_YESNO) = IDYES then
    begin
      Result := False;
      Exit;
    end
    else
    begin
      Result := False;
      Exit;
    end;
  end;
end;

// Função executada antes de iniciar a desinstalação
function InitializeUninstall(): Boolean;
var
  ResultCode: Integer;
begin
  Result := True;

  // Verificar se o aplicativo está rodando
  if CheckForMutexes('Global\PDF2MD_Mutex') then
  begin
    MsgBox('O PDF Legal Extractor está em execução.' + #13#10 + #13#10 +
           'Por favor, feche o aplicativo antes de desinstalar.',
           mbError, MB_OK);
    Result := False;
    Exit;
  end;

  // Confirmar desinstalação
  if MsgBox('Deseja realmente remover o ' + ExpandConstant('{#MyAppName}') + '?',
            mbConfirmation, MB_YESNO) = IDNO then
  begin
    Result := False;
  end;
end;

// Mensagem de conclusão personalizada
procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    // Ações após a instalação (se necessário)
  end;
end;
