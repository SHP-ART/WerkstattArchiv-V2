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
python --version >nul 2>&1
if errorlevel 1 (
    echo [FEHLER] Python ist nicht installiert!
    echo.
    echo Bitte installieren Sie Python 3.9 oder hoeher von:
    echo https://www.python.org/downloads/
    echo.
    echo WICHTIG: Waehlen Sie "Add Python to PATH" waehrend der Installation!
    echo.
    pause
    exit /b 1
)

echo [OK] Python gefunden:
python --version
echo.

REM Prüfe ob pip verfügbar ist
python -m pip --version >nul 2>&1
if errorlevel 1 (
    echo [FEHLER] pip ist nicht verfuegbar!
    echo.
    pause
    exit /b 1
)

echo [OK] pip gefunden
echo.

REM Installiere Python-Pakete
echo ============================================================
echo   Installiere Python-Pakete...
echo ============================================================
echo.

echo [*] Aktualisiere pip...
python -m pip install --upgrade pip

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
