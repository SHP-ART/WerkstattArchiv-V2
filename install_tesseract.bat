@echo off
chcp 65001 >nul
title Tesseract OCR Installation

echo ============================================
echo    TESSERACT OCR INSTALLATION FÜR WINDOWS
echo ============================================
echo.

:: Prüfen ob Tesseract bereits installiert ist
where tesseract >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Tesseract ist bereits installiert!
    tesseract --version
    echo.
    echo Pfad: 
    where tesseract
    goto :check_lang
)

:: Standard-Installationspfade prüfen
set "TESS_PATH="
if exist "C:\Program Files\Tesseract-OCR\tesseract.exe" (
    set "TESS_PATH=C:\Program Files\Tesseract-OCR\tesseract.exe"
)
if exist "C:\Program Files (x86)\Tesseract-OCR\tesseract.exe" (
    set "TESS_PATH=C:\Program Files (x86)\Tesseract-OCR\tesseract.exe"
)

if defined TESS_PATH (
    echo [OK] Tesseract gefunden: %TESS_PATH%
    "%TESS_PATH%" --version
    echo.
    echo HINWEIS: Tesseract ist installiert, aber nicht im PATH.
    echo Fuege diesen Pfad zur Config hinzu oder zum System-PATH.
    goto :check_lang
)

echo [!] Tesseract ist NICHT installiert.
echo.
echo ============================================
echo    INSTALLATION
echo ============================================
echo.
echo Option 1: Automatischer Download (empfohlen)
echo -------------------------------------------
echo.

:: Prüfen ob winget verfügbar ist
where winget >nul 2>&1
if %errorlevel% equ 0 (
    echo Winget gefunden! Starte Installation...
    echo.
    winget install UB-Mannheim.TesseractOCR
    if %errorlevel% equ 0 (
        echo.
        echo [OK] Tesseract wurde installiert!
        echo.
        echo WICHTIG: Bitte Terminal neu starten und dieses Script erneut ausfuehren.
        goto :end
    ) else (
        echo [!] Winget-Installation fehlgeschlagen. Versuche manuellen Download...
    )
)

echo.
echo Option 2: Manueller Download
echo ----------------------------
echo.
echo 1. Oeffne: https://github.com/UB-Mannheim/tesseract/wiki
echo 2. Lade die neueste Version herunter (tesseract-ocr-w64-setup-xxx.exe)
echo 3. Installiere mit Standardeinstellungen
echo 4. WICHTIG: Waehle bei der Installation "German" als Sprache aus!
echo.
echo Moechtest du die Download-Seite jetzt oeffnen? (J/N)
set /p OPEN_BROWSER=
if /i "%OPEN_BROWSER%"=="J" (
    start https://github.com/UB-Mannheim/tesseract/wiki
)
goto :end

:check_lang
echo.
echo ============================================
echo    SPRACHPAKETE PRUEFEN
echo ============================================
echo.

:: Pfad zu tessdata finden
set "TESSDATA="
if exist "C:\Program Files\Tesseract-OCR\tessdata" (
    set "TESSDATA=C:\Program Files\Tesseract-OCR\tessdata"
)
if exist "C:\Program Files (x86)\Tesseract-OCR\tessdata" (
    set "TESSDATA=C:\Program Files (x86)\Tesseract-OCR\tessdata"
)

if not defined TESSDATA (
    echo [!] Tessdata-Ordner nicht gefunden.
    echo     Bitte pruefe die Tesseract-Installation.
    goto :config_hint
)

echo Tessdata-Ordner: %TESSDATA%
echo.

:: Deutsch prüfen
if exist "%TESSDATA%\deu.traineddata" (
    echo [OK] Deutsch (deu) ist installiert
) else (
    echo [!] Deutsch (deu) ist NICHT installiert!
    echo.
    echo Download: https://github.com/tesseract-ocr/tessdata/raw/main/deu.traineddata
    echo Speichern in: %TESSDATA%\deu.traineddata
    echo.
    echo Moechtest du die Datei jetzt herunterladen? (J/N)
    set /p DL_DEU=
    if /i "%DL_DEU%"=="J" (
        echo Lade deu.traineddata herunter...
        powershell -Command "Invoke-WebRequest -Uri 'https://github.com/tesseract-ocr/tessdata/raw/main/deu.traineddata' -OutFile '%TESSDATA%\deu.traineddata'"
        if exist "%TESSDATA%\deu.traineddata" (
            echo [OK] Deutsch erfolgreich heruntergeladen!
        ) else (
            echo [!] Download fehlgeschlagen. Bitte manuell herunterladen.
        )
    )
)

:config_hint
echo.
echo ============================================
echo    KONFIGURATION FUER WERKSTATT-ARCHIV
echo ============================================
echo.

:: Tesseract-Pfad ermitteln
set "FINAL_TESS_PATH="
if exist "C:\Program Files\Tesseract-OCR\tesseract.exe" (
    set "FINAL_TESS_PATH=C:\\Program Files\\Tesseract-OCR\\tesseract.exe"
)
if exist "C:\Program Files (x86)\Tesseract-OCR\tesseract.exe" (
    set "FINAL_TESS_PATH=C:\\Program Files (x86)\\Tesseract-OCR\\tesseract.exe"
)

if defined FINAL_TESS_PATH (
    echo Fuege folgende Zeile in deine .archiv_config.json ein:
    echo.
    echo     "tesseract_cmd": "%FINAL_TESS_PATH%"
    echo.
    echo Oder setze die Umgebungsvariable:
    echo     set TESSERACT_CMD=%FINAL_TESS_PATH%
    echo.
) else (
    echo [!] Tesseract-Pfad konnte nicht ermittelt werden.
    echo     Bitte installiere Tesseract zuerst.
)

echo ============================================
echo    TEST
echo ============================================
echo.

:: Test durchführen
if defined FINAL_TESS_PATH (
    echo Teste Tesseract...
    "C:\Program Files\Tesseract-OCR\tesseract.exe" --version 2>nul
    if %errorlevel% equ 0 (
        echo.
        echo [OK] Tesseract funktioniert!
    )
)

:end
echo.
echo ============================================
echo Druecke eine Taste zum Beenden...
pause >nul
