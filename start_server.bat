@echo off
REM ============================================================
REM Werkstatt-Archiv Web-Server Startvorgang (Windows)
REM Ähnlich zu start_server.sh für macOS/Linux
REM ============================================================

setlocal enabledelayedexpansion

echo ============================================================
echo   Werkstatt-Archiv Web-Server Startvorgang
echo ============================================================
echo.

REM Wechsle in das Script-Verzeichnis
cd /d "%~dp0"

REM [1/8] Erstelle Log-Verzeichnis
echo [1/8] Erstelle Log-Verzeichnis...
if not exist "logs" mkdir logs
echo [OK] Log-Verzeichnis bereit: logs
echo.

REM [2/8] Prüfe auf laufende Server-Prozesse
echo [2/8] Pruefe auf laufende Server-Prozesse...
set "pids="
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8080" 2^>nul') do (
    set "pids=!pids! %%a"
)

if not "!pids!"=="" (
    echo [WARNUNG] Port 8080 ist belegt ^(PIDs:!pids!^)
    for %%p in (!pids!) do (
        taskkill /F /PID %%p >nul 2>&1
    )
    timeout /t 1 /nobreak >nul
    echo [OK] Alte Prozesse beendet
) else (
    echo [OK] Port 8080 ist frei
)
echo.

REM [3/8] Prüfe Python-Installation und Virtual Environment
echo [3/8] Pruefe Python-Installation und Virtual Environment...
python --version >nul 2>&1
if errorlevel 1 (
    echo [FEHLER] Python nicht gefunden!
    echo Bitte installieren Sie Python von https://www.python.org/
    pause
    exit /b 1
)

for /f "tokens=2" %%v in ('python --version 2^>^&1') do echo [OK] Python %%v

REM Virtual Environment prüfen und aktivieren
if exist ".venv\Scripts\activate.bat" (
    echo [OK] Virtual Environment gefunden
    call .venv\Scripts\activate.bat
    if errorlevel 1 (
        echo [FEHLER] Konnte Virtual Environment nicht aktivieren!
        pause
        exit /b 1
    )
    echo [OK] Virtual Environment aktiviert
) else (
    echo [FEHLER] Kein Virtual Environment gefunden ^(.venv^)
    echo Bitte fuehren Sie install.bat aus.
    pause
    exit /b 1
)
echo.

REM [4/8] Prüfe Python-Abhängigkeiten im venv
echo [4/8] Pruefe Python-Abhaengigkeiten ^(venv^)...
REM Note: Pillow is imported as 'PIL', not 'Pillow'
python -c "import flask, waitress, PIL, pytesseract, PyPDF2" >nul 2>&1
if errorlevel 1 (
    echo [FEHLER] Fehlende Abhaengigkeiten!
    echo Installiere mit: pip install -r requirements.txt
    pause
    exit /b 1
)
echo [OK] Alle Abhaengigkeiten installiert ^(venv^)
echo [OK] Alle Abhaengigkeiten installiert
echo.

REM [5/8] Prüfe Konfiguration
echo [5/8] Pruefe Konfiguration...
if not exist ".archiv_config.json" (
    if not exist ".archiv_config.yaml" (
        echo [FEHLER] Keine Konfigurationsdatei gefunden!
        echo Bitte erstellen Sie .archiv_config.json
        pause
        exit /b 1
    )
    echo [OK] Konfigurationsdatei gefunden: .archiv_config.yaml
) else (
    echo [OK] Konfigurationsdatei gefunden: .archiv_config.json
)
echo.

REM [6/8] Prüfe Python-Syntax
echo [6/8] Pruefe Python-Syntax...
python -m py_compile web_app.py 2>nul
if errorlevel 1 (
    echo [FEHLER] Syntax-Fehler in web_app.py
    pause
    exit /b 1
)
echo [OK] Syntax OK
echo.

REM [7/8] Starte Web-Server
echo [7/8] Starte Web-Server...
set LOGFILE=logs\server.log

REM Starte Python im Hintergrund und leite in Log um
start /B python web_app.py > %LOGFILE% 2>&1

REM Warte kurz bis Server startet
timeout /t 2 /nobreak >nul
echo [OK] Server gestartet
echo.

REM [8/8] Warte auf Server-Bereitschaft und zeige Live-Log
echo [8/8] Warte auf Server-Bereitschaft...
echo.
echo ============================================================
echo   Live-Log von: %LOGFILE%
echo ============================================================

REM Zeige die ersten Zeilen des Logs
timeout /t 1 /nobreak >nul
if exist %LOGFILE% (
    for /f "delims=" %%i in (%LOGFILE%) do echo ^| %%i
)

echo ============================================================
echo.
echo ============================================================
echo   [OK] SERVER ERFOLGREICH GESTARTET!
echo ============================================================
echo.
echo   URL:      http://127.0.0.1:8080
echo   Logs:     type logs\server.log
echo   Beenden:  Strg+C oder Fenster schliessen
echo.
echo ============================================================
echo.

REM Warte auf Benutzereingabe
echo Druecken Sie eine beliebige Taste um das Fenster zu schliessen...
echo Der Server laeuft weiter im Hintergrund.
echo.
pause >nul

echo.
echo Server laeuft weiter. Zum Beenden:
echo 1. Oeffnen Sie Task-Manager
echo 2. Beenden Sie den Python-Prozess
echo.
echo Oder verwenden Sie: taskkill /F /IM python.exe
echo.
