; Compile locally with Inno Setup 6.3+; no CI/CD or global app dependencies.
#ifndef PayloadDir
  #error PayloadDir must point to the prepared installer payload
#endif
#ifndef OutputDir
  #error OutputDir is required
#endif
#ifndef AppVersion
  #define AppVersion "1.0"
#endif

[Setup]
AppId={{4E345D50-4373-44EA-8639-608B89B01344}
AppName=AI Car Scanner
AppVersion={#AppVersion}
VersionInfoVersion=1.0.0.0
AppPublisher=AI Car Scanner
AppPublisherURL=https://github.com/Grigor1995/AI-CAR-SCANER
DefaultDirName={localappdata}\Programs\AI-Car-Scanner
DefaultGroupName=AI Car Scanner
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0
WizardStyle=modern
SetupLogging=yes
SetupMutex=AI-Car-Scanner-Online-Setup
Compression=lzma2
SolidCompression=yes
OutputDir={#OutputDir}
OutputBaseFilename=AI-Car-Scanner-Setup
SetupIconFile={#PayloadDir}\app.ico
UninstallDisplayIcon={app}\app.ico
UninstallDisplayName=AI Car Scanner
CloseApplications=no
RestartApplications=no
DiskSpanning=no

[Tasks]
Name: localai; Description: "Install local offline AI (Qwen3 8B, approximately 5-6 GB extra download)"; GroupDescription: "Optional components:"; Flags: unchecked
Name: desktopicon; Description: "Create a Desktop shortcut"; GroupDescription: "Shortcuts:"

[Files]
Source: "{#PayloadDir}\bootstrap.ps1"; DestDir: "{app}\installer"; Flags: ignoreversion
Source: "{#PayloadDir}\windows_installer.py"; DestDir: "{app}\installer"; Flags: ignoreversion
Source: "{#PayloadDir}\manifest.json"; DestDir: "{app}\installer"; Flags: ignoreversion
Source: "{#PayloadDir}\app.ico"; DestDir: "{app}"; Flags: ignoreversion

[InstallDelete]
Type: files; Name: "{autodesktop}\AI Car Scanner.lnk"; Tasks: not desktopicon

[Icons]
Name: "{group}\AI Car Scanner"; Filename: "{app}\repo\.venv\Scripts\pythonw.exe"; Parameters: """{app}\installer\windows_installer.py"" launch --root ""{app}"""; WorkingDir: "{app}\repo"; IconFilename: "{app}\app.ico"
Name: "{autodesktop}\AI Car Scanner"; Filename: "{app}\repo\.venv\Scripts\pythonw.exe"; Parameters: """{app}\installer\windows_installer.py"" launch --root ""{app}"""; WorkingDir: "{app}\repo"; IconFilename: "{app}\app.ico"; Tasks: desktopicon
Name: "{group}\Uninstall AI Car Scanner"; Filename: "{uninstallexe}"
Name: "{group}\Installation logs"; Filename: "{app}\logs"

[Run]
Filename: "{app}\repo\.venv\Scripts\pythonw.exe"; Parameters: """{app}\installer\windows_installer.py"" launch --root ""{app}"""; WorkingDir: "{app}\repo"; Description: "Launch AI Car Scanner"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Only the dedicated installer-owned application folder is removed.
; User diagnostics in AppData\Roaming\AI-Car-Scanner are retained.
Type: filesandordirs; Name: "{app}\repo"
Type: filesandordirs; Name: "{app}\logs"
Type: files; Name: "{app}\.ai-car-installer.json"
Type: dirifempty; Name: "{app}\installer"
Type: dirifempty; Name: "{app}"

[Code]
var
  DownloadPage: TOutputProgressWizardPage;

function IsManagedDirectory(Dir: String): Boolean;
var
  Marker: AnsiString;
begin
  Result := LoadStringFromFile(AddBackslash(Dir) + '.ai-car-installer.json', Marker);
  if Result then
    Result := Pos('AI-Car-Scanner-online-installer-v1', String(Marker)) > 0;
end;

function IsEmptyDirectory(Dir: String): Boolean;
var
  Item: TFindRec;
begin
  Result := True;
  if FindFirst(AddBackslash(Dir) + '*', Item) then begin
    try
      repeat
        if (Item.Name <> '.') and (Item.Name <> '..') then begin
          Result := False;
          Break;
        end;
      until not FindNext(Item);
    finally
      FindClose(Item);
    end;
  end;
end;

function NextButtonClick(CurPageID: Integer): Boolean;
begin
  Result := True;
  if CurPageID = wpSelectDir then begin
    if DirExists(WizardDirValue) and not IsEmptyDirectory(WizardDirValue) and
        not IsManagedDirectory(WizardDirValue) then begin
      MsgBox('Choose an empty application folder. Existing development checkouts and personal files are never replaced.', mbError, MB_OK);
      Result := False;
    end;
  end;
end;

procedure InitializeWizard;
begin
  DownloadPage := CreateOutputProgressPage('Preparing AI Car Scanner', 'Downloading and installing selected components');
end;

function PrepareToInstall(var NeedsRestart: Boolean): String;
var
  Arguments: String;
  Code: Integer;
  ShowCommand: Integer;
begin
  Result := '';
  if DirExists(WizardDirValue) and not IsEmptyDirectory(WizardDirValue) and
      not IsManagedDirectory(WizardDirValue) then begin
    Result := 'Choose an empty folder or a previous AI Car Scanner installation.';
    Exit;
  end;
  ExtractTemporaryFile('bootstrap.ps1');
  ExtractTemporaryFile('windows_installer.py');
  ExtractTemporaryFile('manifest.json');
  Arguments := '-NoProfile -ExecutionPolicy Bypass -File "' + ExpandConstant('{tmp}\bootstrap.ps1') +
    '" -Root "' + WizardDirValue + '" -Manifest "' + ExpandConstant('{tmp}\manifest.json') +
    '" -Helper "' + ExpandConstant('{tmp}\windows_installer.py') + '"';
  if WizardIsTaskSelected('localai') then
    Arguments := Arguments + ' -WithAI';
  DownloadPage.SetText('Internet access is required. A console shows download and installation progress.',
    'Local AI downloads several GB when selected. Close the application before repairing or upgrading.');
  ShowCommand := SW_SHOWNORMAL;
  if WizardSilent then ShowCommand := SW_HIDE
  else DownloadPage.Show;
  try
    if not Exec(ExpandConstant('{sys}\WindowsPowerShell\v1.0\powershell.exe'), Arguments,
        ExpandConstant('{tmp}'), ShowCommand, ewWaitUntilTerminated, Code) then
      Result := 'Could not start Windows PowerShell. Check the Setup log.'
    else if Code <> 0 then
      Result := 'Setup did not complete. See the console and ' + WizardDirValue + '\logs. Check your internet connection and retry.';
  finally
    if not WizardSilent then DownloadPage.Hide;
  end;
end;

function InitializeUninstall: Boolean;
var
  Code: Integer;
begin
  Result := IsManagedDirectory(ExpandConstant('{app}'));
  if not Result then
    MsgBox('The installation ownership marker is missing. Automatic removal was stopped to protect existing files.', mbError, MB_OK);
  if Result then begin
    Result := Exec(ExpandConstant('{sys}\WindowsPowerShell\v1.0\powershell.exe'),
      '-NoProfile -ExecutionPolicy Bypass -File "' + ExpandConstant('{app}\installer\bootstrap.ps1') +
      '" -Root "' + ExpandConstant('{app}') + '" -CheckRunning', '', SW_HIDE, ewWaitUntilTerminated, Code);
    if Result then Result := Code = 0;
    if not Result then
      MsgBox('Close AI Car Scanner, its backend and local AI before uninstalling. Then retry.', mbError, MB_OK);
  end;
end;
