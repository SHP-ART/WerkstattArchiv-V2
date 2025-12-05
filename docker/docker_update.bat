@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion

:: Wechsle ins Script-Verzeichnis (docker-Ordner)
cd /d "%~dp0"

echo ========================================
echo Werkstatt-Archiv Docker Update
echo ========================================
echo.

:: Prüfe ob Docker läuft
docker info >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [FEHLER] Docker ist nicht gestartet!
    echo Bitte starten Sie Docker Desktop.
    pause
    exit /b 1
)

echo [OK] Docker ist gestartet
echo.

:: Wechsle ins Projekt-Root für git pull
cd ..

:: Git Update (optional)
echo [1/4] Prüfe auf Updates von GitHub...
git pull origin main 2>nul
if %ERRORLEVEL% equ 0 (
    echo [OK] Code aktualisiert
) else (
    echo [INFO] Git nicht verfügbar oder keine Änderungen
)
echo.

:: Zurück in docker-Ordner
cd docker

:: Container stoppen
echo [2/4] Stoppe laufenden Container...
docker-compose down 2>nul
echo [OK] Container gestoppt
echo.

:: Image neu bauen
echo [3/4] Baue neues Image (kann einige Minuten dauern)...
docker-compose build --no-cache
if %ERRORLEVEL% neq 0 (
    echo [FEHLER] Build fehlgeschlagen!
    pause
    exit /b 1
)
echo [OK] Image gebaut
echo.

:: Container starten
echo [4/4] Starte Container...
docker-compose up -d
if %ERRORLEVEL% equ 0 (
    echo.
    echo ========================================
    echo [OK] Update erfolgreich!
    echo ========================================
    echo.
    echo URL: http://localhost:8080
    echo.
    timeout /t 3 >nul
    start http://localhost:8080
) else (
    echo [FEHLER] Container konnte nicht gestartet werden!
)

echo.
pause
