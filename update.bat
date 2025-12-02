@echo off
setlocal EnableDelayedExpansion
chcp 65001 >nul 2>&1

echo.
echo ============================================================================
echo Werkstatt-Archiv UPDATE
echo ============================================================================
echo.

REM === Schritt 1: Git finden ===
echo [1/5] Suche Git...

set "GIT_CMD="
set "GIT64=C:\Program Files\Git\cmd\git.exe"
set "GIT32=C:\Program Files (x86)\Git\cmd\git.exe"

REM Erst im PATH suchen
where git >nul 2>&1
if !errorlevel!==0 (
    set "GIT_CMD=git"
    echo [OK] Git im PATH gefunden
    goto :check_repo
)

REM Dann Standard-Pfade
if exist "!GIT64!" (
    set "GIT_CMD=!GIT64!"
    echo [OK] Git gefunden: 64-bit
    goto :check_repo
)

if exist "!GIT32!" (
    set "GIT_CMD=!GIT32!"
    echo [OK] Git gefunden: 32-bit
    goto :check_repo
)

echo.
echo [FEHLER] Git nicht gefunden!
echo.
echo          Moegliche Loesungen:
echo          1. Fuehre install_git.bat aus
echo          2. Starte den Computer neu (nach Git-Installation)
echo          3. Lade Git manuell: https://git-scm.com/download/win
echo.
pause
exit /b 1

:check_repo
echo.
echo [2/5] Pruefe Git-Repository...

if not exist ".git" (
    echo.
    echo [FEHLER] Dies ist kein Git-Repository!
    echo.
    echo          Du hast das Projekt vermutlich als ZIP heruntergeladen.
    echo          Fuer Updates brauchst du ein Git-Repository.
    echo.
    echo          LOESUNG:
    echo          1. Sichere deine .archiv_config.json Datei
    echo          2. Loesche diesen Ordner komplett
    echo          3. Oeffne CMD und fuehre aus:
    echo.
    echo             cd %USERPROFILE%\Documents
    echo             git clone https://github.com/SHP-ART/WerkstattArchiv-V2.git
    echo.
    echo          4. Kopiere deine .archiv_config.json in den neuen Ordner
    echo          5. Fuehre install.bat aus
    echo.
    pause
    exit /b 1
)

echo [OK] Git-Repository gefunden
echo.

REM === Pruefe Virtual Environment ===
echo [3/5] Pruefe Virtual Environment...

if not exist ".venv\Scripts\activate.bat" (
    echo.
    echo [FEHLER] Virtual Environment nicht gefunden!
    echo          Bitte zuerst install.bat ausfuehren.
    echo.
    pause
    exit /b 1
)

echo [OK] Virtual Environment gefunden
echo.

REM === Git Pull ===
echo [4/5] Hole neueste Version von GitHub...

"!GIT_CMD!" pull
if !errorlevel! neq 0 (
    echo.
    echo [FEHLER] Git Pull fehlgeschlagen!
    echo          Pruefe deine Internetverbindung.
    echo.
    pause
    exit /b 1
)

echo.

REM === Pakete aktualisieren ===
echo [5/5] Aktualisiere Python-Pakete...

call .venv\Scripts\activate.bat
python -m pip install --upgrade pip >nul 2>&1
pip install -r requirements.txt --quiet
if !errorlevel! neq 0 (
    echo [WARNUNG] Einige Pakete konnten nicht aktualisiert werden.
) else (
    echo [OK] Pakete aktualisiert
)

echo.
echo ============================================================================
echo UPDATE ABGESCHLOSSEN!
echo ============================================================================
echo.
echo Starte den Server mit: start_server.bat
echo.
pause
