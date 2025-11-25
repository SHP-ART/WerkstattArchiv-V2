@echo off
REM ============================================================
REM Werkstatt-Archiv - Windows Installation
REM ============================================================

echo.
echo ============================================================
echo   Werkstatt-Archiv - Installation
echo ============================================================
echo.

REM Prüfe ob Python installiert ist
echo [*] Prüfe Python-Installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo ============================================================
    echo   [FEHLER] Python ist nicht installiert!
    echo ============================================================
    echo.
    echo Bitte installieren Sie Python 3.9 oder hoeher von:
    echo https://www.python.org/downloads/
    echo.
    echo WICHTIG: Waehlen Sie "Add Python to PATH" waehrend der Installation!
    echo.
    echo Druecken Sie eine Taste um fortzufahren...
    pause
    exit /b 1
)

echo [OK] Python gefunden:
python --version
echo.

REM Pruefe ob Git installiert ist
echo [*] Pruefe Git Installation...
git --version >nul 2>&1
if errorlevel 1 (
    echo [WARNUNG] Git ist nicht installiert!
    echo.
    echo Git wird fuer das Update-System benoetigt (update.bat).
    echo Bitte installieren Sie Git von:
    echo https://git-scm.com/download/win
    echo.
    echo Installation kann fortgesetzt werden, aber Updates funktionieren nicht.
    echo.
    choice /C JN /M "Trotzdem fortfahren"
    if errorlevel 2 exit /b 1
) else (
    echo [OK] Git gefunden:
    git --version
)
echo.

REM Erstelle Virtual Environment
echo ============================================================
echo   Erstelle Virtual Environment...
echo ============================================================
echo.

if exist ".venv" (
    echo [INFO] Virtual Environment existiert bereits (.venv)
) else (
    echo [*] Erstelle .venv...
    echo [*] Erstelle Virtual Environment...
    
    REM Pruefe ob venv-Modul verfuegbar ist
    python -m venv --help >nul 2>&1
    if errorlevel 1 (
        echo [FEHLER] Python venv-Modul nicht gefunden!
        echo.
        echo Moegliche Loesungen:
        echo   1. Python neu installieren von https://www.python.org/
        echo   2. Bei Installation "Add Python to PATH" aktivieren
        echo   3. "pip" und "tcl/tk" Module mit installieren
        pause
        exit /b 1
    )
    
    python -m venv .venv
    if errorlevel 1 (
        echo [FEHLER] Konnte Virtual Environment nicht erstellen!
        echo.
        echo Moegliche Loesungen:
        echo   1. Python Version pruefen: python --version
        echo   2. Genug Speicherplatz vorhanden?
        echo   3. Schreibrechte im Verzeichnis vorhanden?
        pause
        exit /b 1
    )
    echo [OK] Virtual Environment erstellt
) else (
    echo [OK] Virtual Environment existiert bereits
)
echo.

REM Aktiviere Virtual Environment
echo [*] Aktiviere Virtual Environment...

REM Pruefe ob activate-Script existiert
if not exist .venv\Scripts\activate.bat (
    echo [FEHLER] .venv\Scripts\activate.bat nicht gefunden!
    echo.
    echo Virtual Environment koennte beschaedigt sein.
    echo Loesche .venv Ordner und starte erneut:
    echo   rmdir /s /q .venv
    echo   install.bat
    pause
    exit /b 1
)

call .venv\Scripts\activate.bat
if errorlevel 1 (
    echo [FEHLER] Konnte Virtual Environment nicht aktivieren!
    pause
    exit /b 1
)
echo [OK] Virtual Environment aktiv
python --version
echo.

REM Installiere Python-Pakete
echo ============================================================
echo   Installiere Python-Pakete...
echo ============================================================
echo.

echo [*] Aktualisiere pip...
python -m pip install --upgrade pip

echo.
echo [*] Pruefe requirements.txt...
if not exist requirements.txt (
    echo [WARNUNG] requirements.txt nicht gefunden - erstelle Fallback...
    (
        echo # Core dependencies
        echo pytesseract^>=0.3.10
        echo pdf2image^>=1.16.3
        echo Pillow^>=10.0.0
        echo PyPDF2^>=3.0.0
        echo.
        echo # File watching
        echo watchdog^>=3.0.0
        echo.
        echo # Web-UI
        echo flask^>=3.0.0
        echo werkzeug^>=3.0.0
        echo waitress^>=2.1.2
        echo.
        echo # Configuration
        echo PyYAML^>=6.0.1
        echo.
        echo # Utilities
        echo python-dateutil^>=2.8.2
    ) > requirements.txt
    echo [OK] requirements.txt erstellt
)

echo.
echo [*] Installiere Abhaengigkeiten aus requirements.txt...
python -m pip install -r requirements.txt

echo.
echo [*] Pruefe Waitress Installation...
python -c "import waitress; print('Waitress Version:', waitress.__version__)" 2>nul
if errorlevel 1 (
    echo [WARNUNG] Waitress nicht gefunden, installiere manuell...
    python -m pip install waitress>=2.1.2
)

if errorlevel 1 (
    echo.
    echo [FEHLER] Installation fehlgeschlagen!
    echo.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo   Pruefe Tesseract OCR...
echo ============================================================
echo.

REM Prüfe ob Tesseract installiert ist
tesseract --version >nul 2>&1
if errorlevel 1 (
    echo [WARNUNG] Tesseract OCR ist nicht installiert!
    echo.
    echo Tesseract wird fuer die OCR-Texterkennung benoetigt.
    echo.
    echo Download-Link:
    echo https://github.com/UB-Mannheim/tesseract/wiki
    echo.
    echo Installation:
    echo 1. Laden Sie den Installer herunter
    echo 2. Installieren Sie mit deutscher Sprachunterstuetzung (deu.traineddata^)
    echo 3. Standard-Pfad: C:\Program Files\Tesseract-OCR\tesseract.exe
    echo.
    echo WICHTIG: Fuegen Sie Tesseract zum PATH hinzu oder setzen Sie
    echo          tesseract_cmd in der Konfiguration!
    echo.
) else (
    echo [OK] Tesseract gefunden:
    for /f "delims=" %%v in ('tesseract --version 2^>^&1 ^| findstr "tesseract"') do echo     %%v
    echo.
)

REM Erstelle Logs-Verzeichnis
if not exist "logs" (
    echo [ERSTELLE] Logs-Verzeichnis...
    mkdir logs
    echo [OK] logs\ Verzeichnis erstellt
    echo.
)

REM Erstelle Konfigurationsdatei wenn nicht vorhanden
if not exist ".archiv_config.json" (
    echo ============================================================
    echo   Erstelle Beispiel-Konfiguration...
    echo ============================================================
    echo.
    
    python -c "import config; cfg = config.Config(); cfg.save(); print('Beispiel-Konfiguration erstellt: .archiv_config.json')"
    
    echo.
    echo WICHTIG: Bitte konfigurieren Sie vor dem ersten Start:
    echo 1. Input-Ordner: python main.py --set-input-folder "C:\Scans\Eingang"
    echo 2. Archiv-Ordner: python main.py --set-archiv-root "C:\Archiv"
    echo 3. Backup-Ordner: python main.py --set-backup-target "C:\Backups"
    echo.
    echo Oder verwenden Sie die Web-UI fuer die Konfiguration:
    echo    start_server.bat
    echo    Dann im Browser: http://localhost:8080/settings
    echo.
)

echo ============================================================
echo   Installation abgeschlossen!
echo ============================================================
echo.
echo Naechste Schritte:
echo.
echo [1] KONFIGURATION (Web-UI - EMPFOHLEN):
echo     start_server.bat
echo     Oeffnen Sie: http://localhost:8080/settings
echo.
echo [2] KONFIGURATION (CLI):
echo     python main.py --set-input-folder "C:\Scans\Eingang"
echo     python main.py --set-archiv-root "C:\Archiv"
echo     python main.py --set-backup-target "C:\Backups"
echo.
echo [3] TESSERACT TESTEN:
echo     python main.py --test-tesseract
echo.
echo [4] PROGRAMM STARTEN:
echo     start.bat           (Menue-Auswahl)
echo     start_server.bat    (Web-UI direkt)
echo.
echo.
echo Oder verwenden Sie die Web-UI:
echo python web_app.py
echo.
pause
