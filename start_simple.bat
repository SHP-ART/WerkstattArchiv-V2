@echo off
REM ============================================================
REM Einfacher Server-Start (mit sichtbaren Fehlern)
REM ============================================================

echo.
echo ============================================================
echo   Werkstatt-Archiv - Einfacher Server-Start
echo ============================================================
echo.

cd /d "%~dp0"

REM Virtual Environment aktivieren
if exist ".venv\Scripts\activate.bat" (
    echo [*] Aktiviere Virtual Environment...
    call .venv\Scripts\activate.bat
    echo [OK] venv aktiviert
    echo.
) else (
    echo [FEHLER] Virtual Environment nicht gefunden!
    echo Bitte fuehren Sie install.bat aus.
    echo.
    pause
    exit /b 1
)

REM Zeige Python-Info
echo [*] Python-Info:
python --version
echo.

REM Port pruefen
echo [*] Pruefe Port 8080...
netstat -ano | findstr ":8080" >nul 2>&1
if not errorlevel 1 (
    echo [WARNUNG] Port 8080 ist bereits belegt!
    echo.
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8080"') do (
        echo   Beende PID: %%a
        taskkill /F /PID %%a >nul 2>&1
    )
    timeout /t 2 /nobreak >nul
)
echo [OK] Port 8080 ist frei
echo.

REM Server starten (IM VORDERGRUND mit sichtbaren Fehlern)
echo ============================================================
echo   Server wird gestartet...
echo ============================================================
echo.
echo URL: http://127.0.0.1:8080
echo.
echo Zum Beenden: Strg+C
echo.
echo ============================================================
echo.

python web_app.py --port 8080

REM Falls Server abstuerzt
echo.
echo.
echo ============================================================
echo   Server wurde beendet
echo ============================================================
echo.
pause
