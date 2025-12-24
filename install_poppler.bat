@echo off
echo ============================================================
echo Poppler Installation fuer Werkstatt-Archiv
echo ============================================================
echo.
echo Poppler wird benoetigt, um PDFs in Bilder zu konvertieren.
echo.

REM Prüfe ob bereits installiert
if exist "C:\Program Files\poppler\Library\bin\pdfinfo.exe" (
    echo [OK] Poppler ist bereits installiert!
    echo Pfad: C:\Program Files\poppler\Library\bin
    echo.
    pause
    exit /b 0
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
set TEMP_DIR=%TEMP%\poppler_install
if not exist "%TEMP_DIR%" mkdir "%TEMP_DIR%"

echo [1/4] Lade Poppler herunter...
echo.
echo Download von: https://github.com/oschwartz10612/poppler-windows/releases/
echo.

REM Download mit PowerShell
powershell -Command "$ProgressPreference = 'SilentlyContinue'; try { $response = Invoke-WebRequest -Uri 'https://api.github.com/repos/oschwartz10612/poppler-windows/releases/latest' -UseBasicParsing; $json = $response.Content | ConvertFrom-Json; $asset = $json.assets | Where-Object { $_.name -like '*-0.zip' } | Select-Object -First 1; Write-Host 'Download:' $asset.name; Invoke-WebRequest -Uri $asset.browser_download_url -OutFile '%TEMP_DIR%\poppler.zip' -UseBasicParsing; exit 0 } catch { Write-Host 'Fehler beim Download:' $_.Exception.Message; exit 1 }"

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [FEHLER] Download fehlgeschlagen!
    goto MANUAL
)

echo.
echo [2/4] Entpacke Poppler...
powershell -Command "Expand-Archive -Path '%TEMP_DIR%\poppler.zip' -DestinationPath '%TEMP_DIR%' -Force"

if %ERRORLEVEL% NEQ 0 (
    echo [FEHLER] Entpacken fehlgeschlagen!
    goto MANUAL
)

echo.
echo [3/4] Installiere nach C:\Program Files\poppler...

REM Finde den entpackten Ordner
for /d %%i in ("%TEMP_DIR%\poppler-*") do set POPPLER_DIR=%%i

REM Kopiere nach Program Files (benötigt Admin-Rechte)
echo Kopiere Dateien... (kann Admin-Rechte erfordern)
xcopy "%POPPLER_DIR%" "C:\Program Files\poppler" /E /I /Y >nul 2>&1

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [WARNUNG] Konnte nicht nach Program Files kopieren (Admin-Rechte?)
    echo Installiere in Benutzerordner stattdessen...
    xcopy "%POPPLER_DIR%" "%USERPROFILE%\poppler" /E /I /Y >nul 2>&1
    set INSTALL_PATH=%USERPROFILE%\poppler\Library\bin
) else (
    set INSTALL_PATH=C:\Program Files\poppler\Library\bin
)

echo.
echo [4/4] Fuege zum PATH hinzu...
echo.

REM Zeige Anleitung für PATH
echo ============================================================
echo Installation abgeschlossen!
echo ============================================================
echo.
echo Installiert nach: %INSTALL_PATH%
echo.
echo WICHTIG: Poppler zum PATH hinzufuegen:
echo.
echo 1. Windows-Suche: "Umgebungsvariablen"
echo 2. "Systemumgebungsvariablen bearbeiten"
echo 3. Button "Umgebungsvariablen"
echo 4. Bei "Benutzervariablen" oder "Systemvariablen":
echo    - "Path" auswaehlen
echo    - "Bearbeiten"
echo    - "Neu"
echo    - Einfuegen: %INSTALL_PATH%
echo 5. OK, OK, OK
echo 6. Terminal NEU starten!
echo.
echo ODER: Setze Pfad in .archiv_config.json:
echo   "poppler_path": "%INSTALL_PATH:\=\\%"
echo.
echo Test: pdfinfo --version
echo.

REM Cleanup
rmdir /s /q "%TEMP_DIR%" >nul 2>&1

pause
exit /b 0

:MANUAL
echo.
echo ============================================================
echo Manuelle Installation
echo ============================================================
echo.
echo 1. Download: https://github.com/oschwartz10612/poppler-windows/releases/
echo    Lade die neueste poppler-XX.XX.X.zip herunter
echo.
echo 2. Entpacke die ZIP-Datei
echo.
echo 3. Kopiere den entpackten Ordner nach:
echo    C:\Program Files\poppler
echo    ODER
echo    %USERPROFILE%\poppler
echo.
echo 4. Fuege zum PATH hinzu:
echo    C:\Program Files\poppler\Library\bin
echo    (siehe Anleitung in POPPLER_INSTALLATION.md)
echo.
echo 5. Terminal NEU starten!
echo.
echo 6. Test: pdfinfo --version
echo.
echo Oder setze Pfad in .archiv_config.json:
echo   "poppler_path": "C:\\Program Files\\poppler\\Library\\bin"
echo.
pause
exit /b 1
