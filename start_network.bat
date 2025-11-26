@echo off
REM ============================================================
REM Server-Start - Erreichbar im Netzwerk
REM ============================================================

echo.
echo ============================================================
echo   Werkstatt-Archiv - Netzwerk-Modus
echo ============================================================
echo.

cd /d "%~dp0"

REM Virtual Environment aktivieren
if exist ".venv\Scripts\activate.bat" (
    echo [*] Aktiviere Virtual Environment...
    call .venv\Scripts\activate.bat
) else (
    echo [FEHLER] Virtual Environment nicht gefunden!
    echo Bitte fuehren Sie install.bat aus.
    pause
    exit /b 1
)

REM Port pruefen
echo [*] Pruefe Port 8080...
netstat -ano | findstr ":8080" >nul 2>&1
if not errorlevel 1 (
    echo [WARNUNG] Port 8080 ist bereits belegt!
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8080"') do (
        taskkill /F /PID %%a >nul 2>&1
    )
    timeout /t 2 /nobreak >nul
)
echo [OK] Port 8080 ist frei
echo.

REM Ermittle lokale IP-Adresse
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /C:"IPv4"') do set IP=%%a
set IP=%IP: =%

echo ============================================================
echo   Server wird im Netzwerk-Modus gestartet
echo ============================================================
echo.
echo [INFO] Server ist erreichbar unter:
echo.
echo   Lokal:     http://127.0.0.1:8080
if defined IP (
    echo   Netzwerk:  http://%IP%:8080
)
echo.
echo [WICHTIG] Firewall-Regel erforderlich!
echo.
echo Falls der Server nicht erreichbar ist:
echo 1. Windows Defender Firewall oeffnen
echo 2. "Eingehende Regeln" -^> "Neue Regel"
echo 3. Port: TCP 8080 freigeben
echo.
echo Oder automatisch mit:
echo    netsh advfirewall firewall add rule name="Werkstatt-Archiv" dir=in action=allow protocol=TCP localport=8080
echo.
echo ============================================================
echo.
echo Zum Beenden: Strg+C
echo.

python web_app.py --host 0.0.0.0 --port 8080

pause
