#ifndef AppVersion
  #error AppVersion is required
#endif
#ifndef PayloadFiles
  #error PayloadFiles is required
#endif
#ifndef OutputPath
  #error OutputPath is required
#endif
[Setup]
AppId={{9D0B957A-B430-4AB9-B27E-32B553503F95}
AppName=ChromaNeural
AppVersion={#AppVersion}
AppPublisher=Janus Rokkjær
AppPublisherURL=https://github.com/Janus5G/ChromaNeural
DefaultDirName={localappdata}\Programs\ChromaNeural\App
DefaultGroupName=ChromaNeural
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
OutputDir={#OutputPath}
OutputBaseFilename=ChromaNeural-{#AppVersion}-windows-x64
SetupIconFile=..\branding\ChromaNeural.ico
UninstallDisplayIcon={app}\client\assets\chroma.ico
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
DisableProgramGroupPage=yes
DisableWelcomePage=no
DisableFinishedPage=yes
UsePreviousAppDir=yes
CloseApplications=yes
RestartApplications=no
SetupLogging=yes
VersionInfoVersion=0.2.21.5
VersionInfoProductTextVersion={#AppVersion}
[Languages]
Name: "en"; MessagesFile: "compiler:Default.isl"
Name: "da"; MessagesFile: "compiler:Languages\Danish.isl"
[Files]
#include PayloadFiles
Source: "prerequisites.py"; Flags: dontcopy
[Icons]
Name: "{group}\ChromaNeural"; Filename: "{sys}\WindowsPowerShell\v1.0\powershell.exe"; Parameters: "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File ""{app}\Start-ChromaNeural.ps1"""; WorkingDir: "{app}"; IconFilename: "{app}\client\assets\chroma.ico"
[CustomMessages]
en.Prerequisites=Install Python 3.14 or newer with Tk and the py/pyw launchers, and Node.js 24 or newer. No software will be downloaded automatically.
da.Prerequisites=Installer Python 3.14 eller nyere med Tk og py/pyw-launcherne samt Node.js 24 eller nyere. Ingen software bliver hentet automatisk.
en.OlderVersion=A newer ChromaNeural version is installed. Remove it explicitly before installing an older version. Your separate user data is not removed.
da.OlderVersion=En nyere ChromaNeural-version er installeret. Afinstaller den eksplicit før installation af en ældre version. Dine separate brugerdata fjernes ikke.
[Code]
function InitializeSetup(): Boolean;
var Existing, Candidate: String; OldVersion, NewVersion: Int64;
begin
  Result := True;
  if RegQueryStringValue(HKCU, 'Software\Microsoft\Windows\CurrentVersion\Uninstall\{9D0B957A-B430-4AB9-B27E-32B553503F95}_is1', 'DisplayVersion', Existing) then
  begin
    Candidate := '{#AppVersion}';
    StringChangeEx(Existing, '-rc.', '.', True);
    StringChangeEx(Candidate, '-rc.', '.', True);
    if not StrToVersion(Existing, OldVersion) or not StrToVersion(Candidate, NewVersion) then Result := False
    else if ComparePackedVersion(OldVersion, NewVersion) > 0 then Result := False;
    if not Result then MsgBox(CustomMessage('OlderVersion'), mbError, MB_OK);
  end;
end;
function PrepareToInstall(var NeedsRestart: Boolean): String;
var Code: Integer;
begin
  ExtractTemporaryFile('prerequisites.py');
  if not Exec('py.exe', '-3 "' + ExpandConstant('{tmp}\prerequisites.py') + '"', '', SW_HIDE, ewWaitUntilTerminated, Code) then
    Result := CustomMessage('Prerequisites')
  else if Code <> 0 then Result := CustomMessage('Prerequisites')
  else Result := '';
end;
