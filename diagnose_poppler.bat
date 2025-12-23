@echo off
echo ============================================================
echo Werkstatt-Archiv - Poppler Diagnose
echo ============================================================
echo.

REM Test 1: Ist pdfinfo im PATH?
echo [1/3] Teste ob Poppler im PATH ist...
where pdfinfo >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo      ✓ Poppler gefunden im PATH!
    for /f "tokens=*" %%i in ('where pdfinfo') do (
        echo      Pfad: %%i
    )
    echo.
    pdfinfo -v
    goto :test_python
) else (
    echo      ✗ Poppler nicht im PATH
)

REM Test 2: Standard-Installationspfade prüfen
echo.
echo [2/3] Suche in Standard-Pfaden...
set FOUND=0

if exist "C:\Program Files\poppler\Library\bin\pdfinfo.exe" (
    echo      ✓ Gefunden: C:\Program Files\poppler\Library\bin
    set FOUND=1
)

if exist "C:\Program Files (x86)\poppler\Library\bin\pdfinfo.exe" (
    echo      ✓ Gefunden: C:\Program Files (x86)\poppler\Library\bin
    set FOUND=1
)

if exist "%~dp0poppler_portable\Library\bin\pdfinfo.exe" (
    echo      ✓ Gefunden: %~dp0poppler_portable\Library\bin
    set FOUND=1
)

if %FOUND% EQU 0 (
    echo      ✗ Poppler nicht gefunden
)

:test_python
echo.
echo [3/3] Teste Python-Integration...
python -c "import ocr; p = ocr.setup_poppler(None); print('      ✓ Poppler-Pfad:', p if p else 'Auto-Detection fehlgeschlagen')" 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo      ✗ Python-Test fehlgeschlagen
)

echo.
echo ============================================================
echo Empfehlung:
echo ============================================================
echo.

where pdfinfo >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Poppler ist NICHT installiert oder nicht im PATH.
    echo.
    echo LÖSUNG 1 ^(Automatisch^):
    echo   1. Führe aus: install_poppler.bat
    echo   2. Starte das Terminal neu
    echo.
    echo LÖSUNG 2 ^(Manuell^):
    echo   1. Download: https://github.com/oschwartz10612/poppler-windows/releases/
    echo   2. Entpacke nach: C:\Program Files\poppler
    echo   3. Füge zum PATH hinzu: C:\Program Files\poppler\Library\bin
    echo   4. Terminal neu starten
    echo.
    echo LÖSUNG 3 ^(Config^):
    echo   Setze in .archiv_config.json:
    echo   "poppler_path": "C:\\\\Program Files\\\\poppler\\\\Library\\\\bin"
    echo.
    echo Mehr Infos: POPPLER_INSTALLATION.md
) else (
    echo ✓ Poppler ist korrekt installiert!
    echo.
    echo Falls es trotzdem nicht funktioniert:
    echo   - Starte das Terminal neu
    echo   - Prüfe die Konfiguration: .archiv_config.json
)

echo.
pause
