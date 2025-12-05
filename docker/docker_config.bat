@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion

:: Wechsle ins Script-Verzeichnis (docker-Ordner)
cd /d "%~dp0"

echo ========================================
echo Werkstatt-Archiv Docker Konfiguration
echo ========================================
echo.
echo Dieses Script hilft bei der Einrichtung der
echo Netzwerkpfade für Docker.
echo.

:: Zeige aktuelle docker-compose.yml
echo Aktuelle Konfiguration in docker-compose.yml:
echo ----------------------------------------
findstr /C:"- ./" /C:"- Z:" /C:"- /Volumes" docker-compose.yml 2>nul
echo ----------------------------------------
echo.

echo.
echo ANLEITUNG:
echo ==========
echo.
echo 1. Öffnen Sie docker-compose.yml mit einem Texteditor
echo.
echo 2. Suchen Sie den Abschnitt "volumes:" unter "werkstatt-archiv:"
echo.
echo 3. Ändern Sie die Pfade für Archiv, Eingang und Backup:
echo.
echo    WINDOWS (mit Netzlaufwerk als Z:):
echo    ----------------------------------
echo    - Z:/Werkstatt/Archiv:/data/archiv
echo    - Z:/Werkstatt/Eingang:/data/eingang  
echo    - Z:/Werkstatt/Backup:/data/backup
echo.
echo    WICHTIG: UNC-Pfade (\\Server\Share) funktionieren NICHT!
echo    Sie müssen das Netzlaufwerk als Laufwerksbuchstabe mappen.
echo.
echo    So mappen Sie ein Netzlaufwerk:
echo    1. Windows Explorer öffnen
echo    2. Rechtsklick auf "Dieser PC" ^> "Netzlaufwerk verbinden"
echo    3. Laufwerksbuchstabe wählen (z.B. Z:)
echo    4. Ordner eingeben: \\Server\Freigabe
echo    5. "Verbindung bei Anmeldung wiederherstellen" aktivieren
echo.
echo 4. Speichern Sie die Datei
echo.
echo 5. Starten Sie docker_start.bat neu
echo.

:: Frage ob docker-compose.yml geöffnet werden soll
echo.
set /p OPEN="docker-compose.yml jetzt öffnen? (j/n): "
if /i "!OPEN!"=="j" (
    notepad docker-compose.yml
)

echo.
pause
