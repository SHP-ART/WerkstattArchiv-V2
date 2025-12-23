@echo off
REM Quick-Test für Server.exe (ohne Build)
REM Testet ob server.py funktioniert

echo ============================================================
echo Werkstatt-Archiv Server - Test
echo ============================================================
echo.

REM Prüfe Python
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [FEHLER] Python nicht gefunden!
    pause
    exit /b 1
)

echo Starte Server (Test-Modus)...
echo.
echo Browser oeffnen: http://localhost:8080
echo STRG+C zum Beenden
echo.
echo ============================================================
echo.

python server.py

pause
