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
WizardSizePercent=120,115
WizardResizable=yes
WizardImageFile={#PayloadDir}\wizard-side.bmp
WizardSmallImageFile={#PayloadDir}\wizard-icon.bmp
WizardImageStretch=yes
DisableWelcomePage=no
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
Name: localai; Description: "Enable local AI - download or select an existing GGUF model"; GroupDescription: "Optional components:"; Flags: unchecked
Name: desktopicon; Description: "Create Desktop shortcuts for USER, CUSTOMER and MARKET"; GroupDescription: "Shortcuts:"

[Files]
#if FileExists(PayloadDir + "\source.zip")
Source: "{#PayloadDir}\source.zip"; Flags: dontcopy
#endif
Source: "{#PayloadDir}\bootstrap.ps1"; DestDir: "{app}\installer"; Flags: ignoreversion
Source: "{#PayloadDir}\windows_installer.py"; DestDir: "{app}\installer"; Flags: ignoreversion
Source: "{#PayloadDir}\manifest.json"; DestDir: "{app}\installer"; Flags: ignoreversion
Source: "{#PayloadDir}\app.ico"; DestDir: "{app}"; Flags: ignoreversion

[InstallDelete]
Type: files; Name: "{autodesktop}\AI Car Scanner.lnk"
Type: files; Name: "{group}\AI Car Scanner.lnk"
Type: files; Name: "{autodesktop}\AI Car User.lnk"; Tasks: not desktopicon
Type: files; Name: "{autodesktop}\AI Car Customer.lnk"; Tasks: not desktopicon
Type: files; Name: "{autodesktop}\AI Car Market.lnk"; Tasks: not desktopicon

[Icons]
Name: "{group}\AI Car User"; Filename: "{app}\repo\.venv\Scripts\pythonw.exe"; Parameters: """{app}\installer\windows_installer.py"" launch --app user --root ""{app}"""; WorkingDir: "{app}\repo"; IconFilename: "{app}\app.ico"
Name: "{group}\AI Car Customer"; Filename: "{app}\repo\.venv\Scripts\pythonw.exe"; Parameters: """{app}\installer\windows_installer.py"" launch --app customer --root ""{app}"""; WorkingDir: "{app}\repo"; IconFilename: "{app}\app.ico"
Name: "{group}\AI Car Market"; Filename: "{app}\repo\.venv\Scripts\pythonw.exe"; Parameters: """{app}\installer\windows_installer.py"" launch --app market --root ""{app}"""; WorkingDir: "{app}\repo"; IconFilename: "{app}\app.ico"
Name: "{autodesktop}\AI Car User"; Filename: "{app}\repo\.venv\Scripts\pythonw.exe"; Parameters: """{app}\installer\windows_installer.py"" launch --app user --root ""{app}"""; WorkingDir: "{app}\repo"; IconFilename: "{app}\app.ico"; Tasks: desktopicon
Name: "{autodesktop}\AI Car Customer"; Filename: "{app}\repo\.venv\Scripts\pythonw.exe"; Parameters: """{app}\installer\windows_installer.py"" launch --app customer --root ""{app}"""; WorkingDir: "{app}\repo"; IconFilename: "{app}\app.ico"; Tasks: desktopicon
Name: "{autodesktop}\AI Car Market"; Filename: "{app}\repo\.venv\Scripts\pythonw.exe"; Parameters: """{app}\installer\windows_installer.py"" launch --app market --root ""{app}"""; WorkingDir: "{app}\repo"; IconFilename: "{app}\app.ico"; Tasks: desktopicon
Name: "{group}\Uninstall AI Car Scanner"; Filename: "{uninstallexe}"
Name: "{group}\Installation logs"; Filename: "{app}\logs"

[Run]
Filename: "{app}\repo\.venv\Scripts\pythonw.exe"; Parameters: """{app}\installer\windows_installer.py"" launch --root ""{app}"""; WorkingDir: "{app}\repo"; Description: "Launch AI Car User"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Only the dedicated installer-owned application folder is removed.
; User diagnostics in AppData\Roaming\AI-Car-Scanner are retained.
Type: filesandordirs; Name: "{app}\repo"
Type: filesandordirs; Name: "{app}\logs"
Type: files; Name: "{app}\environment.json"
Type: files; Name: "{app}\.ai-car-installer.json"
Type: dirifempty; Name: "{app}\installer"
Type: dirifempty; Name: "{app}"

[Code]
var
  DownloadPage: TOutputProgressWizardPage;
  AIPage: TWizardPage;
  LocalModelCheck: TNewCheckBox;
  ModelPath: TNewEdit;
  BrowseModel: TNewButton;
  ModelHint: TNewStaticText;

const
  BackgroundColor = $211106;
  SurfaceColor = $41250B;
  TextColor = $FFF4EA;
  AccentColor = $FFC835;

procedure UpdateModelChoice(Sender: TObject);
begin
  ModelPath.Enabled := LocalModelCheck.Checked;
  BrowseModel.Enabled := LocalModelCheck.Checked;
  if LocalModelCheck.Checked then
    ModelHint.Caption := 'Use your existing GGUF model. Its file stays in its current folder; external model files are never removed by Uninstall.'
  else
    ModelHint.Caption := 'Download the verified Qwen3 8B GGUF model (approximately 5-6 GB). Interrupted model downloads can resume.';
end;

procedure ChooseModel(Sender: TObject);
var
  Filename: String;
begin
  Filename := ModelPath.Text;
  if GetOpenFileName('Choose your local AI model', Filename, '', 'GGUF models|*.gguf|All files|*.*', 'gguf') then begin
    ModelPath.Text := Filename;
    LocalModelCheck.Checked := True;
    UpdateModelChoice(Sender);
  end;
end;

function ShouldSkipPage(PageID: Integer): Boolean;
begin
  Result := (PageID = AIPage.ID) and not WizardIsTaskSelected('localai');
end;


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
  if (CurPageID = AIPage.ID) and LocalModelCheck.Checked then begin
    if (Trim(ModelPath.Text) = '') or not FileExists(ModelPath.Text) then begin
      MsgBox('Choose an existing local GGUF model, or uncheck Local model to download one.', mbError, MB_OK);
      Result := False;
      Exit;
    end;
  end;
  if CurPageID = wpSelectDir then begin
    if DirExists(WizardDirValue) and not IsEmptyDirectory(WizardDirValue) and
        not IsManagedDirectory(WizardDirValue) then begin
      MsgBox('Choose an empty application folder. Existing development checkouts and personal files are never replaced.', mbError, MB_OK);
      Result := False;
    end;
  end;
end;

procedure InitializeWizard;
var
  Title: TNewStaticText;
  Description: TNewStaticText;
begin
  WizardForm.Color := BackgroundColor;
  WizardForm.Font.Name := 'Segoe UI';
  WizardForm.Font.Size := 10;
  WizardForm.Font.Color := TextColor;
  WizardForm.MainPanel.Color := SurfaceColor;
  WizardForm.NextButton.Font.Color := $58340B;
  WizardForm.BackButton.Font.Color := $58340B;
  WizardForm.CancelButton.Font.Color := $58340B;
  WizardForm.DirBrowseButton.Font.Color := $58340B;
  WizardForm.InnerPage.Color := BackgroundColor;
  WizardForm.WelcomePage.Color := BackgroundColor;
  WizardForm.FinishedPage.Color := BackgroundColor;
  WizardForm.PageNameLabel.Font.Color := AccentColor;
  WizardForm.PageDescriptionLabel.Font.Color := TextColor;
  WizardForm.WelcomeLabel1.Font.Color := AccentColor;
  WizardForm.WelcomeLabel2.Font.Color := TextColor;
  WizardForm.FinishedHeadingLabel.Font.Color := AccentColor;
  WizardForm.FinishedLabel.Font.Color := TextColor;
  WizardForm.DirEdit.Color := SurfaceColor;
  WizardForm.DirEdit.Font.Color := TextColor;
  WizardForm.TasksList.Color := BackgroundColor;
  WizardForm.TasksList.Font.Color := TextColor;
  WizardForm.ReadyMemo.Color := SurfaceColor;
  WizardForm.ReadyMemo.Font.Color := TextColor;
  WizardForm.WelcomeLabel1.Caption := 'AI CAR SCANNER';
  WizardForm.WelcomeLabel2.Caption := 'SMART DIAGNOSTICS  /  LOCAL AI' + #13#10 + #13#10 +
    'Build your automotive workspace with Desktop and Backend.' + #13#10 + #13#10 +
    'Choose your AI model and shortcuts on the following pages.';
  AIPage := CreateCustomPage(wpSelectTasks, 'Local AI', 'Download a model or connect an existing GGUF file');
  AIPage.Surface.Color := BackgroundColor;
  Title := TNewStaticText.Create(WizardForm);
  Title.Parent := AIPage.Surface;
  Title.SetBounds(0, 0, AIPage.SurfaceWidth, ScaleY(28));
  Title.Caption := 'YOUR MODEL. YOUR WORKSPACE.';
  Title.Font.Size := 15;
  Title.Font.Color := AccentColor;
  Description := TNewStaticText.Create(WizardForm);
  Description.Parent := AIPage.Surface;
  Description.SetBounds(0, ScaleY(42), AIPage.SurfaceWidth, ScaleY(48));
  Description.AutoSize := False;
  Description.WordWrap := True;
  Description.Caption := 'The llama.cpp runtime is installed automatically. Choose below whether to download weights or use a model already on this computer.';
  Description.Font.Color := TextColor;
  LocalModelCheck := TNewCheckBox.Create(WizardForm);
  LocalModelCheck.Parent := AIPage.Surface;
  LocalModelCheck.SetBounds(0, ScaleY(104), AIPage.SurfaceWidth, ScaleY(24));
  LocalModelCheck.Caption := 'Local model - use an existing GGUF file';
  LocalModelCheck.Font.Color := TextColor;
  LocalModelCheck.OnClick := @UpdateModelChoice;
  ModelPath := TNewEdit.Create(WizardForm);
  ModelPath.Parent := AIPage.Surface;
  ModelPath.SetBounds(0, ScaleY(144), AIPage.SurfaceWidth - ScaleX(100), ScaleY(26));
  ModelPath.Color := SurfaceColor;
  ModelPath.Font.Color := TextColor;
  ModelPath.Anchors := [akLeft, akTop, akRight];
  ModelPath.Text := ExpandConstant('{param:LOCALMODEL|}');
  if ModelPath.Text = '' then ModelPath.Text := GetPreviousData('LocalModel', '');
  BrowseModel := TNewButton.Create(WizardForm);
  BrowseModel.Parent := AIPage.Surface;
  BrowseModel.SetBounds(AIPage.SurfaceWidth - ScaleX(90), ScaleY(144), ScaleX(90), ScaleY(26));
  BrowseModel.Caption := 'Browse...';
  BrowseModel.Font.Color := $58340B;
  BrowseModel.Anchors := [akTop, akRight];
  BrowseModel.OnClick := @ChooseModel;
  ModelHint := TNewStaticText.Create(WizardForm);
  ModelHint.Parent := AIPage.Surface;
  ModelHint.SetBounds(0, ScaleY(190), AIPage.SurfaceWidth, ScaleY(64));
  ModelHint.AutoSize := False;
  ModelHint.WordWrap := True;
  ModelHint.Font.Color := AccentColor;
  ModelHint.Anchors := [akLeft, akTop, akRight];
  LocalModelCheck.Checked := ModelPath.Text <> '';
  UpdateModelChoice(nil);
  DownloadPage := CreateOutputProgressPage('Preparing AI Car Scanner', 'Downloading and installing selected components');
  DownloadPage.Surface.Color := BackgroundColor;
end;

procedure RegisterPreviousData(PreviousDataKey: Integer);
begin
  if LocalModelCheck.Checked then
    SetPreviousData(PreviousDataKey, 'LocalModel', ModelPath.Text)
  else
    SetPreviousData(PreviousDataKey, 'LocalModel', '');
end;

function UpdateReadyMemo(Space, NewLine, MemoUserInfoInfo, MemoDirInfo, MemoTypeInfo,
  MemoComponentsInfo, MemoGroupInfo, MemoTasksInfo: String): String;
var
  Choice: String;
begin
  Choice := 'Local AI disabled';
  if WizardIsTaskSelected('localai') then begin
    Choice := 'Download Qwen3 8B GGUF';
    if LocalModelCheck.Checked then Choice := 'Use local GGUF: ' + ModelPath.Text;
  end;
  Result := MemoDirInfo + NewLine + NewLine + MemoTasksInfo + NewLine + NewLine +
    'AI model: ' + Choice + NewLine +
    'Global settings: ' + AddBackslash(WizardDirValue) + 'environment.json';
end;

function PrepareToInstall(var NeedsRestart: Boolean): String;
var
  Arguments: String;
  Code: Integer;
  ShowCommand: Integer;
  ErrorText: AnsiString;
begin
  Result := '';
  if DirExists(WizardDirValue) and not IsEmptyDirectory(WizardDirValue) and
      not IsManagedDirectory(WizardDirValue) then begin
    Result := 'Choose an empty folder or a previous AI Car Scanner installation.';
    Exit;
  end;
  if WizardIsTaskSelected('localai') and LocalModelCheck.Checked then begin
    if (Trim(ModelPath.Text) = '') or not FileExists(ModelPath.Text) then begin
      Result := 'Choose an existing GGUF model, or disable the Local model checkbox.';
      Exit;
    end;
  end;
  ExtractTemporaryFile('bootstrap.ps1');
  ExtractTemporaryFile('windows_installer.py');
  ExtractTemporaryFile('manifest.json');
  DeleteFile(ExpandConstant('{tmp}\installer-error.txt'));
#if FileExists(PayloadDir + "\source.zip")
  ExtractTemporaryFile('source.zip');
#endif
  Arguments := '-NoProfile -ExecutionPolicy Bypass -File "' + ExpandConstant('{tmp}\bootstrap.ps1') +
    '" -Root "' + WizardDirValue + '" -Manifest "' + ExpandConstant('{tmp}\manifest.json') +
    '" -Helper "' + ExpandConstant('{tmp}\windows_installer.py') +
    '" -ErrorFile "' + ExpandConstant('{tmp}\installer-error.txt') + '"';
#if FileExists(PayloadDir + "\source.zip")
  Arguments := Arguments + ' -SourceArchive "' + ExpandConstant('{tmp}\source.zip') + '"';
#endif
  if WizardIsTaskSelected('localai') then begin
    Arguments := Arguments + ' -WithAI';
    if LocalModelCheck.Checked then
      Arguments := Arguments + ' -LocalModel "' + ModelPath.Text + '"';
  end;
  DownloadPage.SetText('A console shows setup progress. Dependencies and optional AI require internet access.',
    'Local AI downloads several GB when selected. Close the application before repairing or upgrading.');
  ShowCommand := SW_SHOWNORMAL;
  if WizardSilent then ShowCommand := SW_HIDE
  else DownloadPage.Show;
  try
    if not Exec(ExpandConstant('{sys}\WindowsPowerShell\v1.0\powershell.exe'), Arguments,
        ExpandConstant('{tmp}'), ShowCommand, ewWaitUntilTerminated, Code) then
      Result := 'Could not start Windows PowerShell. Check the Setup log.'
    else if Code <> 0 then begin
      Result := 'Setup did not complete (exit ' + IntToStr(Code) + ').';
      if LoadStringFromFile(ExpandConstant('{tmp}\installer-error.txt'), ErrorText) then
        Result := Result + #13#10 + Copy(UTF8Decode(ErrorText), 1, 2500);
      Result := Result + #13#10 + 'Logs: ' + ExpandConstant('{localappdata}\AI-Car-Scanner\installer-logs');
    end;
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
