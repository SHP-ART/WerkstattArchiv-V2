@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion

:: Wechsle ins Script-Verzeichnis (docker-Ordner)
cd /d "%~dp0"

echo ========================================
echo Werkstatt-Archiv Docker Backup
echo ========================================
echo.

:: Prüfe ob Docker läuft
docker info >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [FEHLER] Docker ist nicht gestartet!
    pause
    exit /b 1
)

:: Prüfe ob Container läuft
docker ps --format "{{.Names}}" | findstr /i "werkstatt-archiv" >nul
if %ERRORLEVEL% neq 0 (
    echo [WARNUNG] Container läuft nicht.
    echo Backup kann trotzdem erstellt werden.
    echo.
)

:: Backup-Verzeichnis (im Elternverzeichnis)
set BACKUP_DIR=..\backups
if not exist "%BACKUP_DIR%" mkdir "%BACKUP_DIR%"

:: Timestamp für Backup-Name
for /f "tokens=2 delims==" %%I in ('wmic os get localdatetime /value') do set datetime=%%I
set TIMESTAMP=%datetime:~0,4%-%datetime:~4,2%-%datetime:~6,2%_%datetime:~8,2%-%datetime:~10,2%

:: Backup-Dateiname
set BACKUP_FILE=%BACKUP_DIR%\werkstatt_backup_%TIMESTAMP%.zip

echo Erstelle Backup: %BACKUP_FILE%
echo.

:: Option 1: Backup über den Container (empfohlen)
echo [1/3] Starte Backup im Container...
docker exec werkstatt-archiv python -c "import backup; backup.create_backup('/data/backup')" 2>nul

if %ERRORLEVEL% equ 0 (
    echo [OK] Container-Backup erstellt in /data/backup
) else (
    echo [INFO] Container-Backup übersprungen (Container nicht aktiv)
)

:: Option 2: Lokales Backup der wichtigsten Dateien
echo.
echo [2/3] Sichere Konfiguration...

:: PowerShell für ZIP verwenden (Pfade relativ zum Projekt-Root)
powershell -Command "Compress-Archive -Path '../.archiv_config.json', '../logs' -DestinationPath '%BACKUP_FILE%' -Force" 2>nul

if %ERRORLEVEL% equ 0 (
    echo [OK] Konfiguration gesichert
) else (
    echo [WARNUNG] Konfiguration konnte nicht gesichert werden
)

echo.
echo [3/3] Backup abgeschlossen!
echo.
echo ========================================
echo WICHTIG: Die Datenbank (werkstatt.db) liegt
echo im ARCHIV-Ordner und wird dort gespeichert.
echo.
echo Backup-Speicherorte:
echo   - Container: /data/backup (= Ihr Backup-Volume)
echo   - Lokal: %BACKUP_FILE%
echo ========================================
echo.

:: Zeige Backup-Ordner
echo Vorhandene Backups:
dir /b "%BACKUP_DIR%\*.zip" 2>nul || echo   (keine lokalen Backups)
echo.

pause
