@echo off
setlocal EnableDelayedExpansion
chcp 65001 >nul 2>&1
title Tesseract OCR Installation

echo.
echo ============================================
echo    TESSERACT OCR INSTALLATION
echo ============================================
echo.

REM === Schritt 1: Pruefen ob bereits installiert ===
echo [1/4] Pruefe ob Tesseract bereits installiert ist...

where tesseract >nul 2>&1
if !errorlevel!==0 (
    echo.
    echo [OK] Tesseract ist bereits installiert und im PATH!
    echo.
    tesseract --version
    echo.
    goto :test_german
)

REM === Schritt 2: Standard-Pfade pruefen ===
echo       Nicht im PATH, pruefe Standard-Pfade...

set "TESS_EXE="
set "TESS64=C:\Program Files\Tesseract-OCR\tesseract.exe"
set "TESS32=C:\Program Files (x86)\Tesseract-OCR\tesseract.exe"

if exist "!TESS64!" (
    set "TESS_EXE=!TESS64!"
    echo [OK] Gefunden: 64-bit Version
    goto :test_version
)

if exist "!TESS32!" (
    set "TESS_EXE=!TESS32!"
    echo [OK] Gefunden: 32-bit Version
    goto :test_version
)

echo       Nicht gefunden in Standard-Pfaden.
echo.

REM === Schritt 3: Installation ===
echo [2/4] Tesseract muss installiert werden...
echo.

REM Pruefe ob winget verfuegbar ist
where winget >nul 2>&1
if !errorlevel!==0 (
    echo       Winget gefunden - starte automatische Installation...
    echo.
    echo       HINWEIS: Falls ein Fenster erscheint, bitte bestaetigen.
    echo.
    winget install -e --id UB-Mannheim.TesseractOCR --accept-package-agreements --accept-source-agreements
    
    echo.
    echo       Pruefe Installation...
    
    REM Pfad neu pruefen
    if exist "!TESS64!" (
        set "TESS_EXE=!TESS64!"
        echo [OK] Installation erfolgreich!
        goto :test_version
    )
    if exist "!TESS32!" (
        set "TESS_EXE=!TESS32!"
        echo [OK] Installation erfolgreich!
        goto :test_version
    )
    
    echo [!] Installation konnte nicht verifiziert werden.
    goto :manual_install
) else (
    goto :manual_install
)

:manual_install
echo.
echo ============================================
echo    MANUELLE INSTALLATION ERFORDERLICH
echo ============================================
echo.
echo 1. Oeffne im Browser:
echo    https://github.com/UB-Mannheim/tesseract/wiki
echo.
echo 2. Lade herunter: tesseract-ocr-w64-setup-5.x.x.exe
echo.
echo 3. Bei der Installation WICHTIG:
echo    - "Additional language data" auswaehlen
echo    - "German" aktivieren!
echo.
echo 4. Nach der Installation dieses Script erneut starten.
echo.
set /p "OPEN_URL=Browser jetzt oeffnen? (j/n): "
if /i "!OPEN_URL!"=="j" (
    start https://github.com/UB-Mannheim/tesseract/wiki
)
goto :end

:test_version
echo.
echo [3/4] Teste Tesseract...
echo.

if defined TESS_EXE (
    "!TESS_EXE!" --version
    echo.
) else (
    echo [!] Kein Tesseract-Pfad gefunden.
    goto :end
)

:test_german
echo [4/4] Pruefe deutsche Sprachdatei...
echo.

REM Finde tessdata Ordner
set "TESSDATA="
set "TD64=C:\Program Files\Tesseract-OCR\tessdata"
set "TD32=C:\Program Files (x86)\Tesseract-OCR\tessdata"

if exist "!TD64!" set "TESSDATA=!TD64!"
if exist "!TD32!" set "TESSDATA=!TD32!"

if not defined TESSDATA (
    echo [!] Tessdata-Ordner nicht gefunden.
    goto :show_config
)

if exist "!TESSDATA!\deu.traineddata" (
    echo [OK] Deutsche Sprachdatei ist installiert!
) else (
    echo [!] Deutsche Sprachdatei fehlt!
    echo.
    echo     Lade deu.traineddata herunter...
    powershell -Command "Invoke-WebRequest -Uri 'https://github.com/tesseract-ocr/tessdata/raw/main/deu.traineddata' -OutFile '!TESSDATA!\deu.traineddata'" 2>nul
    
    if exist "!TESSDATA!\deu.traineddata" (
        echo [OK] Deutsche Sprachdatei heruntergeladen!
    ) else (
        echo [!] Download fehlgeschlagen.
        echo     Bitte manuell herunterladen:
        echo     https://github.com/tesseract-ocr/tessdata/raw/main/deu.traineddata
        echo     Speichern unter: !TESSDATA!\deu.traineddata
    )
)

:show_config
echo.
echo ============================================
echo    FERTIG!
echo ============================================
echo.
echo Tesseract sollte jetzt funktionieren.
echo Das Werkstatt-Archiv findet es automatisch.
echo.

:end
echo.
echo Druecke eine Taste zum Beenden...
pause >nul
