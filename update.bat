@echo off
REM ============================================================================
REM Werkstatt-Archiv UPDATE Script (Windows)
REM ============================================================================
REM Dieses Script aktualisiert das Programm ohne Datenbank oder Archiv zu loeschen
REM - Git Pull (neueste Version)
REM - Python Dependencies aktualisieren
REM - Konfiguration und Daten bleiben erhalten
REM ============================================================================

setlocal enabledelayedexpansion

echo.
echo ============================================================================
echo Werkstatt-Archiv UPDATE
echo ============================================================================
echo.

REM Pruefe ob Git installiert ist
where git >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [FEHLER] Git ist nicht installiert oder nicht im PATH!
    echo          Bitte Git installieren: https://git-scm.com/download/win
    pause
    exit /b 1
)

REM Pruefe ob wir in einem Git-Repository sind
if not exist ".git" (
    echo [FEHLER] Kein Git-Repository gefunden!
    echo          Bitte fuehre dieses Script im Werkstatt-Archiv Ordner aus.
    pause
    exit /b 1
)

REM Pruefe ob Virtual Environment existiert
if not exist ".venv\Scripts\activate.bat" (
    echo [FEHLER] Virtual Environment nicht gefunden!
    echo          Bitte zuerst install.bat ausfuehren.
    pause
    exit /b 1
)

echo [1/5] Pruefe auf lokale Aenderungen...
echo ------------------------------------------------------------------------------

REM Pruefe auf uncommittete Aenderungen (nur Code-Dateien)
git diff --quiet HEAD -- *.py *.bat *.sh templates/ static/ 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [WARNUNG] Du hast lokale Aenderungen an Code-Dateien!
    echo           Diese werden beim Update ueberschrieben.
    echo.
    git status --short
    echo.
    set /p confirm="Trotzdem fortfahren? Aenderungen gehen verloren! (j/n): "
    if /i not "!confirm!"=="j" (
        echo Update abgebrochen.
        pause
        exit /b 0
    )
    
    REM Setze Code-Dateien zurueck (Config und Daten bleiben erhalten)
    echo Setze Code-Dateien zurueck...
    git checkout -- *.py *.bat *.sh templates/ static/ 2>nul
)

echo OK - Keine Konflikte mit Konfiguration/Daten
echo.

echo [2/5] Hole neueste Version von GitHub...
echo ------------------------------------------------------------------------------

REM Aktueller Branch
for /f "tokens=*" %%a in ('git rev-parse --abbrev-ref HEAD') do set BRANCH=%%a
echo Branch: %BRANCH%

REM Aktueller Commit (vor Update)
for /f "tokens=*" %%a in ('git rev-parse --short HEAD') do set OLD_COMMIT=%%a
echo Aktueller Commit: %OLD_COMMIT%

REM Git Pull
git pull origin %BRANCH%
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [FEHLER] Git Pull fehlgeschlagen!
    echo          Pruefe deine Internetverbindung oder GitHub-Zugriff.
    pause
    exit /b 1
)

REM Neuer Commit (nach Update)
for /f "tokens=*" %%a in ('git rev-parse --short HEAD') do set NEW_COMMIT=%%a

echo.
if "%OLD_COMMIT%"=="%NEW_COMMIT%" (
    echo Bereits auf neuestem Stand ^(%OLD_COMMIT%^)
) else (
    echo Update: %OLD_COMMIT% -^> %NEW_COMMIT%
    echo.
    echo Aenderungen:
    git log --oneline %OLD_COMMIT%..%NEW_COMMIT%
)
echo.

echo [3/5] Aktiviere Virtual Environment...
echo ------------------------------------------------------------------------------
call .venv\Scripts\activate.bat
if %ERRORLEVEL% NEQ 0 (
    echo [FEHLER] Konnte Virtual Environment nicht aktivieren!
    pause
    exit /b 1
)
echo OK - Virtual Environment aktiv
echo.

echo [4/5] Aktualisiere Python-Pakete...
echo ------------------------------------------------------------------------------
python -m pip install --upgrade pip >nul 2>&1
pip install -r requirements.txt
if %ERRORLEVEL% NEQ 0 (
    echo [FEHLER] Paket-Installation fehlgeschlagen!
    pause
    exit /b 1
)
echo OK - Alle Pakete aktualisiert
echo.

echo [5/5] Pruefe Konfiguration...
echo ------------------------------------------------------------------------------

REM Pruefe ob Config existiert
if exist ".archiv_config.json" (
    echo OK - Konfiguration gefunden: .archiv_config.json
) else if exist ".archiv_config.yaml" (
    echo OK - Konfiguration gefunden: .archiv_config.yaml
) else (
    echo [WARNUNG] Keine Konfiguration gefunden!
    echo           Bitte Config erstellen mit: python main.py --set-input-folder [PFAD]
)

REM Pruefe ob Datenbank existiert
python -c "import config; c = config.Config(); db_path = c.get_archiv_root() / 'werkstatt.db'; exit(0 if db_path.exists() else 1)" 2>nul
if %ERRORLEVEL% EQU 0 (
    echo OK - Datenbank gefunden und intakt
) else (
    echo [INFO] Datenbank wird beim ersten Start automatisch erstellt
)

echo.
echo ============================================================================
echo UPDATE ERFOLGREICH ABGESCHLOSSEN!
echo ============================================================================
echo.
echo Naechste Schritte:
echo   - Server starten:  start_server.bat
echo   - CLI verwenden:   python main.py --help
echo.
echo Wichtig: Deine Konfiguration, Datenbank und Archiv wurden NICHT veraendert!
echo ============================================================================
echo.

pause
