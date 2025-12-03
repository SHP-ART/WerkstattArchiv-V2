@echo off
setlocal EnableDelayedExpansion
chcp 65001 >nul 2>&1
title Deutsche Sprachdatei fuer Tesseract

echo.
echo ============================================
echo    DEUTSCHE SPRACHDATEI INSTALLIEREN
echo ============================================
echo.

REM Finde tessdata Ordner
set "TESSDATA="

if exist "C:\Program Files\Tesseract-OCR\tessdata" (
    set "TESSDATA=C:\Program Files\Tesseract-OCR\tessdata"
)
if exist "C:\Program Files (x86)\Tesseract-OCR\tessdata" (
    set "TESSDATA=C:\Program Files (x86)\Tesseract-OCR\tessdata"
)

if not defined TESSDATA (
    echo [FEHLER] Tesseract tessdata-Ordner nicht gefunden!
    echo          Bitte zuerst Tesseract installieren.
    pause
    exit /b 1
)

echo Tessdata-Ordner: !TESSDATA!
echo.

REM Pruefe ob bereits vorhanden
if exist "!TESSDATA!\deu.traineddata" (
    echo [OK] Deutsche Sprachdatei ist bereits installiert!
    echo.
    pause
    exit /b 0
)

echo Deutsche Sprachdatei wird heruntergeladen...
echo Quelle: github.com/tesseract-ocr/tessdata
echo.

REM Download mit PowerShell
powershell -Command "& {$ProgressPreference = 'SilentlyContinue'; Invoke-WebRequest -Uri 'https://github.com/tesseract-ocr/tessdata/raw/main/deu.traineddata' -OutFile '!TESSDATA!\deu.traineddata'}"

if exist "!TESSDATA!\deu.traineddata" (
    echo.
    echo [OK] Deutsche Sprachdatei erfolgreich installiert!
    echo     Gespeichert: !TESSDATA!\deu.traineddata
    echo.
    echo Du kannst jetzt die OCR-Funktion nutzen.
) else (
    echo.
    echo [FEHLER] Download fehlgeschlagen!
    echo.
    echo MANUELLE INSTALLATION:
    echo 1. Oeffne: https://github.com/tesseract-ocr/tessdata/raw/main/deu.traineddata
    echo 2. Speichere die Datei als: !TESSDATA!\deu.traineddata
    echo.
    echo Moechtest du die Download-Seite oeffnen? (j/n)
    set /p OPEN=
    if /i "!OPEN!"=="j" (
        start https://github.com/tesseract-ocr/tessdata/raw/main/deu.traineddata
    )
)

echo.
pause
