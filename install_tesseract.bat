@echo off
setlocal EnableDelayedExpansion
echo ============================================================
echo Tesseract OCR Installation fuer Werkstatt-Archiv
echo ============================================================
echo.
echo Tesseract wird fuer OCR (Texterkennung) benoetigt.
echo.

REM Prüfe ob bereits installiert
if exist "C:\Program Files\Tesseract-OCR\tesseract.exe" (
    echo [OK] Tesseract ist bereits installiert!
    echo Pfad: C:\Program Files\Tesseract-OCR
    echo.
    "C:\Program Files\Tesseract-OCR\tesseract.exe" --version
    echo.
    goto check_german
)

if exist "C:\Program Files (x86)\Tesseract-OCR\tesseract.exe" (
    echo [OK] Tesseract ist bereits installiert!
    echo Pfad: C:\Program Files (x86^)\Tesseract-OCR
    echo.
    "C:\Program Files (x86)\Tesseract-OCR\tesseract.exe" --version
    echo.
    goto check_german
)

echo OPTION 1: Automatischer Download (empfohlen)
echo OPTION 2: Manuelle Installation
echo.
choice /C 12 /M "Waehle Option (1 oder 2)"

if errorlevel 2 goto MANUAL
if errorlevel 1 goto DOWNLOAD

:DOWNLOAD
echo.
echo ============================================================
echo Automatische Installation
echo ============================================================
echo.

REM Erstelle temporäres Verzeichnis
set TEMP_DIR=%TEMP%\tesseract_install
if not exist "%TEMP_DIR%" mkdir "%TEMP_DIR%"

echo [1/3] Lade Tesseract herunter...
echo.
echo Download von: https://github.com/UB-Mannheim/tesseract
echo Version: 5.3.3
echo.

REM Download mit PowerShell
powershell -Command "$ProgressPreference = 'SilentlyContinue'; try { $url = 'https://github.com/UB-Mannheim/tesseract/releases/download/v5.3.3.20231005/tesseract-ocr-w64-setup-5.3.3.20231005.exe'; Write-Host 'Download: tesseract-ocr-w64-setup-5.3.3.20231005.exe'; Invoke-WebRequest -Uri $url -OutFile '%TEMP_DIR%\tesseract_setup.exe' -UseBasicParsing; exit 0 } catch { Write-Host 'Fehler beim Download:' $_.Exception.Message; exit 1 }"

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [FEHLER] Download fehlgeschlagen!
    goto MANUAL
)

echo.
echo [2/3] Installiere Tesseract...
echo.
echo WICHTIG: Im Installations-Dialog bitte folgendes auswaehlen:
echo   - [x] Additional language data
echo   - [x] German (deu.traineddata)
echo.
echo Starte Installation... (Fenster wird sich oeffnen)
timeout /t 3 /nobreak >nul

REM Starte Installer (interaktiv)
"%TEMP_DIR%\tesseract_setup.exe"

echo.
echo Warte auf Installations-Abschluss...
timeout /t 5 /nobreak >nul

REM Prüfe ob installiert wurde
if exist "C:\Program Files\Tesseract-OCR\tesseract.exe" (
    echo.
    echo [OK] Installation erfolgreich!
    set TESS_PATH=C:\Program Files\Tesseract-OCR
    goto check_german
)

if exist "C:\Program Files (x86)\Tesseract-OCR\tesseract.exe" (
    echo.
    echo [OK] Installation erfolgreich!
    set TESS_PATH=C:\Program Files (x86)\Tesseract-OCR
    goto check_german
)

echo.
echo [WARNUNG] Installation konnte nicht verifiziert werden.
echo Bitte manuell pruefen oder Script erneut ausfuehren.
goto END

:check_german
echo.
echo [3/3] Pruefe deutsche Sprachdatei...
echo.

REM Finde tessdata Ordner
if exist "C:\Program Files\Tesseract-OCR\tessdata" (
    set TESSDATA=C:\Program Files\Tesseract-OCR\tessdata
) else if exist "C:\Program Files (x86)\Tesseract-OCR\tessdata" (
    set TESSDATA=C:\Program Files (x86)\Tesseract-OCR\tessdata
) else (
    echo [WARNUNG] tessdata-Ordner nicht gefunden.
    goto END
)

if exist "%TESSDATA%\deu.traineddata" (
    echo [OK] Deutsche Sprachdatei ist installiert!
    goto SUCCESS
)

echo [!] Deutsche Sprachdatei fehlt!
echo Lade deu.traineddata herunter...
echo.

powershell -Command "$ProgressPreference = 'SilentlyContinue'; try { Invoke-WebRequest -Uri 'https://github.com/tesseract-ocr/tessdata/raw/main/deu.traineddata' -OutFile '%TESSDATA%\deu.traineddata' -UseBasicParsing; Write-Host '[OK] Download erfolgreich!'; exit 0 } catch { Write-Host '[FEHLER] Download fehlgeschlagen:' $_.Exception.Message; exit 1 }"

if %ERRORLEVEL% EQU 0 (
    goto SUCCESS
) else (
    echo.
    echo Bitte manuell herunterladen:
    echo 1. https://github.com/tesseract-ocr/tessdata/raw/main/deu.traineddata
    echo 2. Speichern unter: %TESSDATA%\deu.traineddata
    echo.
    goto END
)

:SUCCESS
echo.
echo ============================================================
echo Installation abgeschlossen!
echo ============================================================
echo.
echo Tesseract ist installiert und einsatzbereit.
echo Pfad: %TESSDATA%\..
echo.
echo Das Werkstatt-Archiv findet Tesseract automatisch.
echo.
echo Test: tesseract --version
echo.

REM Cleanup
if exist "%TEMP_DIR%" rmdir /s /q "%TEMP_DIR%" >nul 2>&1

pause
exit /b 0

:MANUAL
echo.
echo ============================================================
echo Manuelle Installation
echo ============================================================
echo.
echo 1. Download: https://github.com/UB-Mannheim/tesseract/wiki
echo    Lade: tesseract-ocr-w64-setup-5.x.x.exe
echo.
echo 2. Bei der Installation WICHTIG auswaehlen:
echo    - [x] Additional language data
echo    - [x] German (deu.traineddata)
echo.
echo 3. Installiere nach: C:\Program Files\Tesseract-OCR
echo.
echo 4. Nach der Installation dieses Script erneut starten
echo    zum Pruefen der Installation.
echo.
choice /C JN /M "Browser jetzt oeffnen"
if errorlevel 2 goto END
start https://github.com/UB-Mannheim/tesseract/wiki

:END
echo.
pause
exit /b 1
