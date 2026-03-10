; ══════════════════════════════════════════════════════════════
; FitManager AI Studio — Inno Setup Script
; ══════════════════════════════════════════════════════════════
;
; Produce: FitManager_Setup_1.0.0.exe (~95 MB)
; Requisiti: Inno Setup 6+ (winget install JRSoftware.InnoSetup)
;
; Compilazione:
;   "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer\fitmanager.iss
;
; Struttura installazione:
;   {app}\
;     launcher.bat
;     backend\       (PyInstaller output)
;     frontend\      (Next.js standalone)
;     node\          (node.exe runtime ~40MB)
;     data\          (creata al primo avvio, preservata sugli aggiornamenti)

#define MyAppName "FitManager AI Studio"
#define MyAppVersion "1.0.0"

[Setup]
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher=FitManager
AppPublisherURL=https://fitmanager.it
DefaultDirName={autopf}\FitManager
DefaultGroupName=FitManager
OutputBaseFilename=FitManager_Setup_{#MyAppVersion}
OutputDir=..\dist
Compression=lzma2/ultra
SolidCompression=yes
; Icona personalizzata (placeholder — sostituire con icona reale)
; SetupIconFile=assets\fitmanager.ico
LicenseFile=assets\EULA.txt
PrivilegesRequired=lowest
WizardStyle=modern
DisableProgramGroupPage=yes
UninstallDisplayName={#MyAppName}

[Languages]
Name: "italian"; MessagesFile: "compiler:Languages\Italian.isl"

[Files]
; Backend (PyInstaller output)
Source: "..\dist\fitmanager\*"; DestDir: "{app}\backend"; Flags: ignoreversion recursesubdirs

; Frontend (Next.js standalone)
Source: "..\frontend\.next\standalone\*"; DestDir: "{app}\frontend"; Flags: ignoreversion recursesubdirs

; Node.js runtime (scaricato separatamente, ~40MB)
; NOTA: node.exe va scaricato da https://nodejs.org e messo in installer\node\
Source: "node\node.exe"; DestDir: "{app}\node"; Flags: ignoreversion

; Launcher
Source: "launcher.bat"; DestDir: "{app}"; Flags: ignoreversion

; Seed esercizi (prima installazione)
Source: "..\data\exercises\seed_exercises.json"; DestDir: "{app}\data\exercises"; Flags: ignoreversion
Source: "..\data\exercises\seed_exercise_relations.json"; DestDir: "{app}\data\exercises"; Flags: ignoreversion
Source: "..\data\exercises\seed_exercise_media.json"; DestDir: "{app}\data\exercises"; Flags: ignoreversion

; Catalog DB (tassonomia scientifica — muscoli, articolazioni, condizioni, metriche)
Source: "..\data\catalog.db"; DestDir: "{app}\data"; Flags: ignoreversion

; Chiave pubblica licenza (verifica firma JWT RSA)
Source: "assets\license_public.pem"; DestDir: "{app}\data"; Flags: ignoreversion

; Foto esercizi attivi (staging da build-media.sh, ~36MB)
Source: "..\dist\media\exercises\*"; DestDir: "{app}\data\media\exercises"; Flags: ignoreversion recursesubdirs

; EULA
Source: "assets\EULA.txt"; DestDir: "{app}"; Flags: ignoreversion

[Dirs]
; Cartella data preservata sugli aggiornamenti
Name: "{app}\data"; Flags: uninsneveruninstall
Name: "{app}\data\backups"; Flags: uninsneveruninstall
Name: "{app}\data\media"; Flags: uninsneveruninstall
Name: "{app}\data\media\exercises"; Flags: uninsneveruninstall

[Icons]
Name: "{group}\FitManager AI Studio"; Filename: "{app}\launcher.bat"; WorkingDir: "{app}"
Name: "{autodesktop}\FitManager AI Studio"; Filename: "{app}\launcher.bat"; WorkingDir: "{app}"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Crea icona sul Desktop"; GroupDescription: "Icone aggiuntive:"

[Run]
; Apri l'app dopo l'installazione
Filename: "{app}\launcher.bat"; Description: "Avvia FitManager AI Studio"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Non eliminare data/ durante la disinstallazione (dati utente)
; Elimina solo file di programma
Type: filesandordirs; Name: "{app}\backend"
Type: filesandordirs; Name: "{app}\frontend"
Type: filesandordirs; Name: "{app}\node"
Type: files; Name: "{app}\launcher.bat"
Type: files; Name: "{app}\EULA.txt"
