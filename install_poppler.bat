@echo off
echo ============================================================
echo Poppler Installation fuer Werkstatt-Archiv
echo ============================================================
echo.
echo Poppler wird benoetigt, um PDFs in Bilder zu konvertieren.
echo.

REM Prüfe ob winget verfügbar ist
where winget >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [FEHLER] winget nicht gefunden!
    echo.
    echo Bitte Poppler manuell installieren:
    echo 1. Download: https://github.com/oschwartz10612/poppler-windows/releases/
    echo 2. Entpacke poppler-XX.XX.X.zip
    echo 3. Kopiere den Ordner nach C:\Program Files\poppler
    echo 4. Fuege C:\Program Files\poppler\Library\bin zum PATH hinzu
    echo.
    pause
    exit /b 1
)

echo Installiere Poppler via winget...
echo.
winget install --id=poppler.poppler -e

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [FEHLER] Installation fehlgeschlagen!
    echo.
    echo Bitte Poppler manuell installieren:
    echo 1. Download: https://github.com/oschwartz10612/poppler-windows/releases/
    echo 2. Entpacke poppler-XX.XX.X.zip nach C:\Program Files\poppler
    echo 3. Fuege C:\Program Files\poppler\Library\bin zum PATH hinzu
    echo.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo Installation abgeschlossen!
echo ============================================================
echo.
echo WICHTIG: Bitte starte das Terminal neu, damit die PATH-Aenderungen
echo          wirksam werden!
echo.
echo Danach teste mit: python main.py --process-input
echo.
pause
