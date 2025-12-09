@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion

:: Wechsle ins Script-Verzeichnis (docker-Ordner)
cd /d "%~dp0"

echo ========================================
echo Werkstatt-Archiv Docker Installation
echo ========================================
echo.
echo Dieses Script bereitet die Docker-Umgebung vor und erstellt die Container.
echo.

:: 1. Prüfe Docker Installation
echo [1/3] Prüfe Docker Desktop...
docker info >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo.
    echo [FEHLER] Docker Desktop läuft nicht oder ist nicht installiert!
    echo.
    echo Bitte installieren Sie Docker Desktop für Windows:
    echo https://www.docker.com/products/docker-desktop/
    echo.
    echo Nach der Installation starten Sie dieses Script erneut.
    echo.
    pause
    exit /b 1
)
echo [OK] Docker ist bereit.
echo.

:: 2. Prüfe Konfiguration
echo [2/3] Prüfe Konfiguration...
if not exist ".archiv_config_docker.json" (
    echo [INFO] Erstelle Standard-Konfiguration...
    copy ".archiv_config_docker.json.example" ".archiv_config_docker.json" >nul 2>&1
    if not exist ".archiv_config_docker.json" (
        echo [WARNUNG] Konnte Config nicht kopieren. Wird beim Start erstellt.
    )
)
echo [OK] Konfiguration geprüft.
echo.

:: 3. Build Container
echo [3/3] Erstelle Docker Container (Build)...
echo Dies kann beim ersten Mal einige Minuten dauern (Download von Python, Tesseract, etc.).
echo.

docker-compose build --no-cache

if %ERRORLEVEL% neq 0 (
    echo.
    echo [FEHLER] Installation fehlgeschlagen!
    echo Bitte prüfen Sie die Fehlermeldungen oben.
    echo.
    pause
    exit /b 1
)

echo.
echo ========================================
echo [ERFOLG] Installation abgeschlossen!
echo ========================================
echo.
echo Sie können das System nun starten mit:
echo   docker_start.bat
echo.
pause
