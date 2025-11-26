@echo off
REM ============================================================
REM Server-Start mit ausfuehrlicher Diagnose
REM ============================================================

setlocal enabledelayedexpansion

echo.
echo ============================================================
echo   Werkstatt-Archiv - DIAGNOSE-MODUS
echo ============================================================
echo   Datum: %date% %time%
echo ============================================================
echo.

cd /d "%~dp0"
echo [INFO] Arbeitsverzeichnis: %CD%
echo.

REM ============================================================
echo [SCHRITT 1/8] Python-Installation pruefen
echo ============================================================
echo.

where python >nul 2>&1
if errorlevel 1 (
    echo [FEHLER] Python nicht im PATH gefunden!
    echo.
    echo Loesung:
    echo 1. Python installieren: https://www.python.org/downloads/
    echo 2. Bei Installation "Add Python to PATH" aktivieren
    echo 3. CMD-Fenster neu starten
    echo.
    pause
    exit /b 1
)

echo [OK] Python gefunden:
where python
python --version
echo.
echo Python-Pfad:
python -c "import sys; print(sys.executable)"
echo.

REM ============================================================
echo [SCHRITT 2/8] Virtual Environment pruefen
echo ============================================================
echo.

if not exist ".venv" (
    echo [FEHLER] .venv Ordner nicht gefunden!
    echo.
    echo Loesung: install.bat ausfuehren
    pause
    exit /b 1
)

if not exist ".venv\Scripts\activate.bat" (
    echo [FEHLER] .venv\Scripts\activate.bat nicht gefunden!
    echo.
    echo Loesung: .venv loeschen und install.bat neu ausfuehren
    pause
    exit /b 1
)

echo [OK] Virtual Environment gefunden
echo [*] Aktiviere venv...
call .venv\Scripts\activate.bat
if errorlevel 1 (
    echo [FEHLER] Konnte venv nicht aktivieren!
    pause
    exit /b 1
)
echo [OK] venv aktiviert
echo.

REM ============================================================
echo [SCHRITT 3/8] Python-Pakete pruefen
echo ============================================================
echo.

echo [*] Pruefe Flask...
python -c "import flask; print(f'Flask Version: {flask.__version__}')" 2>&1
if errorlevel 1 (
    echo [FEHLER] Flask nicht installiert!
    echo Loesung: pip install flask
    goto INSTALL_DEPS
)

echo [*] Pruefe Waitress...
python -c "import waitress; print(f'Waitress Version: {waitress.__version__}')" 2>&1
if errorlevel 1 (
    echo [FEHLER] Waitress nicht installiert!
    echo Loesung: pip install waitress
    goto INSTALL_DEPS
)

echo [*] Pruefe PyPDF2...
python -c "import PyPDF2; print(f'PyPDF2 Version: {PyPDF2.__version__}')" 2>&1
if errorlevel 1 (
    echo [FEHLER] PyPDF2 nicht installiert!
    goto INSTALL_DEPS
)

echo [*] Pruefe Pillow...
python -c "from PIL import Image; import PIL; print(f'Pillow Version: {PIL.__version__}')" 2>&1
if errorlevel 1 (
    echo [FEHLER] Pillow nicht installiert!
    goto INSTALL_DEPS
)

echo [*] Pruefe pytesseract...
python -c "import pytesseract; print('pytesseract OK')" 2>&1
if errorlevel 1 (
    echo [FEHLER] pytesseract nicht installiert!
    goto INSTALL_DEPS
)

echo [*] Pruefe pdf2image...
python -c "import pdf2image; print('pdf2image OK')" 2>&1
if errorlevel 1 (
    echo [FEHLER] pdf2image nicht installiert!
    goto INSTALL_DEPS
)

echo [*] Pruefe watchdog...
python -c "import watchdog; print('watchdog OK')" 2>&1
if errorlevel 1 (
    echo [FEHLER] watchdog nicht installiert!
    goto INSTALL_DEPS
)

echo.
echo [OK] Alle Pakete installiert
echo.
goto SKIP_INSTALL

:INSTALL_DEPS
echo.
echo [*] Versuche fehlende Pakete zu installieren...
pip install -r requirements.txt
if errorlevel 1 (
    echo [FEHLER] Paket-Installation fehlgeschlagen!
    pause
    exit /b 1
)
echo [OK] Pakete installiert
echo.

:SKIP_INSTALL

REM ============================================================
echo [SCHRITT 4/8] web_app.py Syntax pruefen
echo ============================================================
echo.

python -m py_compile web_app.py 2>&1
if errorlevel 1 (
    echo [FEHLER] Syntax-Fehler in web_app.py!
    echo.
    echo Details:
    python -m py_compile web_app.py
    pause
    exit /b 1
)
echo [OK] web_app.py Syntax OK
echo.

REM ============================================================
echo [SCHRITT 5/8] web_app.py Import-Test
echo ============================================================
echo.

echo [*] Teste Import (kann einige Sekunden dauern)...
python -c "import web_app; print('[OK] web_app.py kann importiert werden')" 2>&1
if errorlevel 1 (
    echo [FEHLER] web_app.py Import fehlgeschlagen!
    echo.
    echo Details:
    python -c "import web_app"
    pause
    exit /b 1
)
echo.

REM ============================================================
echo [SCHRITT 6/8] Konfiguration pruefen
echo ============================================================
echo.

if exist ".archiv_config.json" (
    echo [OK] Konfiguration gefunden: .archiv_config.json
    echo.
    echo Inhalt:
    type .archiv_config.json
    echo.
) else if exist ".archiv_config.yaml" (
    echo [OK] Konfiguration gefunden: .archiv_config.yaml
) else (
    echo [WARNUNG] Keine Konfigurationsdatei gefunden
    echo [INFO] Erstelle Standard-Konfiguration...
    python -c "from config import Config; c = Config(); c.save(); print('[OK] Config erstellt')"
)
echo.

REM ============================================================
echo [SCHRITT 7/8] Port 8080 pruefen
echo ============================================================
echo.

echo [*] Pruefe ob Port 8080 frei ist...
netstat -ano | findstr ":8080" >nul 2>&1
if not errorlevel 1 (
    echo [WARNUNG] Port 8080 ist belegt!
    echo.
    echo Belegende Prozesse:
    netstat -ano | findstr ":8080"
    echo.
    echo [*] Versuche Prozesse zu beenden...
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8080" ^| findstr "LISTENING"') do (
        echo   Beende PID: %%a
        taskkill /F /PID %%a >nul 2>&1
    )
    timeout /t 2 /nobreak >nul
    
    REM Erneut pruefen
    netstat -ano | findstr ":8080" >nul 2>&1
    if not errorlevel 1 (
        echo [FEHLER] Port 8080 ist immer noch belegt!
        echo.
        echo Loesung: Anderen Port verwenden oder Prozess manuell beenden
        pause
        exit /b 1
    )
)
echo [OK] Port 8080 ist frei
echo.

REM ============================================================
echo [SCHRITT 8/8] Server starten
echo ============================================================
echo.

echo ============================================================
echo   DIAGNOSE ABGESCHLOSSEN - ALLES OK
echo ============================================================
echo.
echo Server wird jetzt gestartet...
echo.
echo   URL:     http://127.0.0.1:8080
echo   Beenden: Strg+C
echo.
echo Falls der Server nicht erreichbar ist:
echo   1. Firewall pruefen (Port 8080 freigeben)
echo   2. Antivirus pruefen (Python erlauben)
echo   3. Im Browser: http://localhost:8080 probieren
echo.
echo ============================================================
echo.
echo [SERVER LOG - Fehler erscheinen hier:]
echo ============================================================
echo.

python web_app.py --port 8080

echo.
echo ============================================================
echo   Server wurde beendet
echo ============================================================
echo.
echo Falls der Server unerwartet beendet wurde:
echo   - Fehler oben in der Ausgabe pruefen
echo   - logs\server.log pruefen (falls vorhanden)
echo.
pause
