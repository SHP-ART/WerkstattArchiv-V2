@echo off
REM ============================================================
REM Werkstatt-Archiv Server - EXE Build Script
REM Erstellt eine eigenständige server.exe für Windows
REM ============================================================

echo ============================================================
echo Werkstatt-Archiv Server - Build
echo ============================================================
echo.

REM Prüfe ob Python verfügbar ist (py launcher bevorzugt)
py --version >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [OK] Python gefunden
    echo.
) else (
    python --version >nul 2>&1
    if %ERRORLEVEL% NEQ 0 (
        echo [FEHLER] Python nicht gefunden!
        echo Bitte Python 3.9+ installieren: https://www.python.org/downloads/
        pause
        exit /b 1
    )
)

echo [1/5] Prüfe Virtual Environment...
if not exist ".venv\Scripts\python.exe" (
    echo     Virtual Environment nicht gefunden. Erstelle...
    py -m venv .venv
    if %ERRORLEVEL% NEQ 0 (
        echo     [FEHLER] Konnte venv nicht erstellen
        pause
        exit /b 1
    )
)

echo [2/5] Aktiviere Virtual Environment...
call .venv\Scripts\activate.bat

echo [3/5] Installiere/Aktualisiere PyInstaller...
python -m pip install --upgrade pyinstaller
if %ERRORLEVEL% NEQ 0 (
    echo     [FEHLER] PyInstaller-Installation fehlgeschlagen
    pause
    exit /b 1
)

echo [4/5] Installiere Abhängigkeiten...
python -m pip install -r requirements.txt
if %ERRORLEVEL% NEQ 0 (
    echo     [WARNUNG] Einige Abhängigkeiten konnten nicht installiert werden
    echo     Build wird trotzdem fortgesetzt...
)

echo.
echo [5/5] Baue Server.exe...
echo     Dies kann einige Minuten dauern...
echo.

REM Lösche alte Build-Artefakte
if exist "build" rmdir /s /q build
if exist "dist\WerkstattArchiv-Server.exe" del /f /q "dist\WerkstattArchiv-Server.exe"

REM PyInstaller ausführen
pyinstaller --clean --noconfirm server.spec

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [FEHLER] Build fehlgeschlagen!
    echo.
    echo Mögliche Ursachen:
    echo   - Fehlende Module (requirements.txt nicht installiert)
    echo   - Fehler in server.spec
    echo   - Unvollständige Python-Installation
    echo.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo Build erfolgreich!
echo ============================================================
echo.
echo Die ausführbare Datei wurde erstellt:
echo   dist\WerkstattArchiv-Server.exe
echo.
echo WICHTIG:
echo   - Tesseract muss auf dem Zielsystem installiert sein
echo   - Poppler muss auf dem Zielsystem installiert sein
echo   - Konfiguration (.archiv_config.json) muss im gleichen Ordner liegen
echo.
echo Dateien für Deployment:
echo   1. dist\WerkstattArchiv-Server.exe
echo   2. .archiv_config.json (Konfiguration)
echo.
echo Zum Testen:
echo   cd dist
echo   WerkstattArchiv-Server.exe
echo.
pause
