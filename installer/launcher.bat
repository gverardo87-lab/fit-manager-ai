@echo off
REM ══════════════════════════════════════════════════════════════
REM  FitManager AI Studio — Launcher
REM  Avvia backend API + frontend Next.js + apre il browser.
REM ══════════════════════════════════════════════════════════════
REM
REM  Uso: doppio-click su questo file, oppure:
REM    launcher.bat              (porte default: 8000 + 3000)
REM    launcher.bat --port 8002  (backend 8002, frontend 3002)
REM
REM  Struttura attesa:
REM    FitManager/
REM      launcher.bat        (questo file)
REM      backend/            (output PyInstaller — fitmanager.exe)
REM      frontend/           (output Next.js standalone — server.js)
REM      node/               (node.exe runtime)
REM      data/               (DB, media, licenza, backup)

setlocal EnableDelayedExpansion

REM ── Configurazione porte ──
set BACKEND_PORT=8000
set FRONTEND_PORT=3000

REM Supporta --port per backend (frontend = backend - 8000 + 3000)
if "%1"=="--port" (
    set BACKEND_PORT=%2
    set /a FRONTEND_PORT=%2 - 8000 + 3000
)

set INSTALL_DIR=%~dp0

echo.
echo  ══════════════════════════════════════════
echo   FitManager AI Studio
echo   Backend: http://localhost:%BACKEND_PORT%
echo   Frontend: http://localhost:%FRONTEND_PORT%
echo  ══════════════════════════════════════════
echo.

REM ── Crea cartella data se non esiste ──
if not exist "%INSTALL_DIR%data" mkdir "%INSTALL_DIR%data"

REM ── Variabili ambiente produzione ──
set LICENSE_ENFORCEMENT_ENABLED=true

REM ── Avvia Backend (in background) ──
echo  [1/3] Avvio backend API...
start /B "" "%INSTALL_DIR%backend\fitmanager.exe" --port %BACKEND_PORT%

REM ── Attendi che il backend sia pronto ──
echo  [2/3] Attesa backend...
set RETRIES=0
:wait_backend
timeout /t 1 /nobreak >nul
set /a RETRIES+=1
curl -s http://localhost:%BACKEND_PORT%/health >nul 2>&1
if errorlevel 1 (
    if %RETRIES% LSS 30 goto wait_backend
    echo  ERRORE: Backend non risponde dopo 30 secondi.
    pause
    exit /b 1
)
echo  Backend pronto!

REM ── Avvia Frontend (in background) ──
echo  [3/3] Avvio frontend...
set PORT=%FRONTEND_PORT%
set HOSTNAME=0.0.0.0
start /B "" "%INSTALL_DIR%node\node.exe" "%INSTALL_DIR%frontend\server.js"

REM ── Attendi frontend e apri browser ──
timeout /t 3 /nobreak >nul
start "" "http://localhost:%FRONTEND_PORT%"

echo.
echo  FitManager avviato!
echo  Chiudi questa finestra per terminare l'applicazione.
echo.
echo  Premi Ctrl+C per uscire...

REM ── Mantieni la finestra aperta (i processi background muoiono con lei) ──
pause >nul
