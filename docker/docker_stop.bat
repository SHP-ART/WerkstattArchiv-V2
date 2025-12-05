@echo off
chcp 65001 >nul

:: Wechsle ins Script-Verzeichnis (docker-Ordner)
cd /d "%~dp0"

echo ========================================
echo Werkstatt-Archiv Docker Stopper
echo ========================================
echo.

:: Prüfe ob Docker läuft
docker info >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [INFO] Docker ist nicht gestartet - nichts zu stoppen.
    pause
    exit /b 0
)

:: Stoppe Container
echo Stoppe Werkstatt-Archiv Container...
docker-compose down

if %ERRORLEVEL% equ 0 (
    echo.
    echo [OK] Container wurde gestoppt.
) else (
    echo.
    echo [INFO] Kein laufender Container gefunden.
)

echo.
pause
