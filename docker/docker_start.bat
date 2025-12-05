@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion

:: Wechsle ins Script-Verzeichnis (docker-Ordner)
cd /d "%~dp0"

echo ========================================
echo Werkstatt-Archiv Docker Starter
echo ========================================
echo.

:: Prüfe ob Docker läuft
docker info >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [FEHLER] Docker ist nicht gestartet!
    echo.
    echo Bitte starten Sie Docker Desktop und warten Sie,
    echo bis das Docker-Symbol in der Taskleiste erscheint.
    echo.
    pause
    exit /b 1
)

echo [OK] Docker ist gestartet
echo.

:: Prüfe ob Container existiert
docker ps -a --format "{{.Names}}" | findstr /i "werkstatt-archiv" >nul
if %ERRORLEVEL% equ 0 (
    echo Container existiert bereits.
    echo.
    
    :: Prüfe ob Container läuft
    docker ps --format "{{.Names}}" | findstr /i "werkstatt-archiv" >nul
    if %ERRORLEVEL% equ 0 (
        echo [OK] Container läuft bereits!
        echo.
        echo Öffne Browser...
        start http://localhost:8080
        goto :end
    ) else (
        echo Starte existierenden Container...
        docker start werkstatt-archiv
        if %ERRORLEVEL% equ 0 (
            echo [OK] Container gestartet!
            timeout /t 3 >nul
            start http://localhost:8080
        ) else (
            echo [FEHLER] Container konnte nicht gestartet werden!
        )
        goto :end
    )
)

:: Container existiert nicht - bauen und starten
echo Container wird erstellt (kann beim ersten Mal einige Minuten dauern)...
echo.

docker-compose up -d --build

if %ERRORLEVEL% equ 0 (
    echo.
    echo ========================================
    echo [OK] Werkstatt-Archiv wurde gestartet!
    echo ========================================
    echo.
    echo URL: http://localhost:8080
    echo.
    echo Öffne Browser...
    timeout /t 3 >nul
    start http://localhost:8080
) else (
    echo.
    echo [FEHLER] Container konnte nicht gestartet werden!
    echo Prüfen Sie die Fehlermeldungen oben.
)

:end
echo.
echo ----------------------------------------
echo Befehle:
echo   Container stoppen:  docker-compose down
echo   Logs anzeigen:      docker-compose logs -f
echo   Container neu bauen: docker-compose up -d --build
echo ----------------------------------------
echo.
pause
