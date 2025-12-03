@echo off
setlocal EnableDelayedExpansion
chcp 65001 >nul 2>&1
title Git Repository einrichten

echo.
echo ============================================
echo    GIT REPOSITORY EINRICHTEN
echo ============================================
echo.
echo Dieses Script verbindet deinen Ordner mit GitHub,
echo damit du in Zukunft einfach Updates bekommst.
echo.

REM === Git finden ===
set "GIT_CMD="
set "GIT64=C:\Program Files\Git\cmd\git.exe"
set "GIT32=C:\Program Files (x86)\Git\cmd\git.exe"

where git >nul 2>&1
if !errorlevel!==0 (
    set "GIT_CMD=git"
    echo [OK] Git gefunden im PATH
) else if exist "!GIT64!" (
    set "GIT_CMD=!GIT64!"
    echo [OK] Git gefunden: 64-bit
) else if exist "!GIT32!" (
    set "GIT_CMD=!GIT32!"
    echo [OK] Git gefunden: 32-bit
) else (
    echo.
    echo [FEHLER] Git ist nicht installiert!
    echo.
    echo Bitte zuerst Git installieren:
    echo   1. Fuehre install_git.bat aus
    echo   2. Oder lade Git manuell: https://git-scm.com/download/win
    echo   3. Nach Installation: Computer neu starten
    echo.
    pause
    exit /b 1
)

echo.

REM === Pruefen ob bereits Git-Repository ===
if exist ".git" (
    echo [INFO] Dieser Ordner ist bereits ein Git-Repository!
    echo.
    echo Moechtest du trotzdem fortfahren und das Repository neu einrichten?
    echo (Deine lokalen Aenderungen bleiben erhalten)
    echo.
    set /p CONTINUE="Fortfahren? (j/n): "
    if /i not "!CONTINUE!"=="j" (
        echo Abgebrochen.
        pause
        exit /b 0
    )
    echo.
    echo Entferne altes .git Verzeichnis...
    rmdir /s /q .git 2>nul
)

REM === Config sichern ===
echo [1/5] Sichere Konfiguration...

set "CONFIG_BACKUP="
if exist ".archiv_config.json" (
    copy ".archiv_config.json" ".archiv_config.json.backup" >nul 2>&1
    set "CONFIG_BACKUP=1"
    echo       .archiv_config.json gesichert
)
if exist ".archiv_config.yaml" (
    copy ".archiv_config.yaml" ".archiv_config.yaml.backup" >nul 2>&1
    set "CONFIG_BACKUP=1"
    echo       .archiv_config.yaml gesichert
)

if not defined CONFIG_BACKUP (
    echo       Keine Konfiguration gefunden (wird spaeter erstellt)
)
echo.

REM === Git initialisieren ===
echo [2/5] Initialisiere Git-Repository...

"!GIT_CMD!" init
if !errorlevel! neq 0 (
    echo [FEHLER] Git init fehlgeschlagen!
    pause
    exit /b 1
)
echo.

REM === Remote hinzufuegen ===
echo [3/5] Verbinde mit GitHub...

"!GIT_CMD!" remote add origin https://github.com/SHP-ART/WerkstattArchiv-V2.git 2>nul
if !errorlevel! neq 0 (
    echo       Remote existiert bereits, aktualisiere...
    "!GIT_CMD!" remote set-url origin https://github.com/SHP-ART/WerkstattArchiv-V2.git
)
echo [OK] Remote: https://github.com/SHP-ART/WerkstattArchiv-V2.git
echo.

REM === Fetch ===
echo [4/5] Lade Repository-Daten von GitHub...

"!GIT_CMD!" fetch origin main
if !errorlevel! neq 0 (
    echo [FEHLER] Konnte nicht mit GitHub verbinden!
    echo          Pruefe deine Internetverbindung.
    pause
    exit /b 1
)
echo.

REM === Branch einrichten und Reset ===
echo [5/5] Synchronisiere mit GitHub...

"!GIT_CMD!" checkout -B main 2>nul
"!GIT_CMD!" branch --set-upstream-to=origin/main main 2>nul
"!GIT_CMD!" reset --hard origin/main

if !errorlevel! neq 0 (
    echo [WARNUNG] Reset fehlgeschlagen, versuche alternative Methode...
    "!GIT_CMD!" pull origin main --allow-unrelated-histories
)
echo.

REM === Config wiederherstellen ===
if defined CONFIG_BACKUP (
    echo Stelle Konfiguration wieder her...
    if exist ".archiv_config.json.backup" (
        copy ".archiv_config.json.backup" ".archiv_config.json" >nul 2>&1
        del ".archiv_config.json.backup" 2>nul
        echo [OK] .archiv_config.json wiederhergestellt
    )
    if exist ".archiv_config.yaml.backup" (
        copy ".archiv_config.yaml.backup" ".archiv_config.yaml" >nul 2>&1
        del ".archiv_config.yaml.backup" 2>nul
        echo [OK] .archiv_config.yaml wiederhergestellt
    )
    echo.
)

REM === Erfolgsmeldung ===
echo.
echo ============================================
echo    FERTIG!
echo ============================================
echo.
echo Dein Ordner ist jetzt mit GitHub verbunden.
echo.
echo NAECHSTE SCHRITTE:
echo   1. Fuehre install.bat aus (falls noch nicht geschehen)
echo   2. Starte den Server mit start_server.bat
echo.
echo FUER UPDATES:
echo   Fuehre einfach update.bat aus
echo.

REM === Aktuellen Status zeigen ===
echo Aktueller Git-Status:
"!GIT_CMD!" log --oneline -3 2>nul
echo.

pause
