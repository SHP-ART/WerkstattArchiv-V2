@echo off
setlocal EnableDelayedExpansion
chcp 65001 >nul 2>&1
title Deutsche Sprachdatei fuer Tesseract

echo.
echo ============================================
echo    DEUTSCHE SPRACHDATEI INSTALLIEREN
echo ============================================
echo.

REM Pruefe Admin-Rechte
net session >nul 2>&1
if !errorlevel! neq 0 (
    echo [INFO] Starte mit Administrator-Rechten...
    echo.
    powershell -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
    exit /b
)

echo [OK] Administrator-Rechte vorhanden
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
    echo.
    echo          Fuehre install_tesseract.bat aus.
    pause
    exit /b 1
)

echo Tessdata-Ordner: !TESSDATA!
echo.

REM Zeige vorhandene Sprachen
echo Vorhandene Sprachdateien:
dir /b "!TESSDATA!\*.traineddata" 2>nul
echo.

REM Pruefe ob bereits vorhanden
if exist "!TESSDATA!\deu.traineddata" (
    echo [OK] Deutsche Sprachdatei ist bereits installiert!
    echo.
    echo Dateigroesse:
    for %%A in ("!TESSDATA!\deu.traineddata") do echo %%~zA Bytes
    echo.
    pause
    exit /b 0
)

echo Deutsche Sprachdatei wird heruntergeladen...
echo Quelle: github.com/tesseract-ocr/tessdata
echo Ziel:   !TESSDATA!\deu.traineddata
echo.
echo Dies kann einen Moment dauern (ca. 15 MB)...
echo.

REM Download mit PowerShell und Fortschrittsanzeige
powershell -Command "& {Write-Host 'Starte Download...'; $ProgressPreference = 'Continue'; try { Invoke-WebRequest -Uri 'https://github.com/tesseract-ocr/tessdata/raw/main/deu.traineddata' -OutFile '!TESSDATA!\deu.traineddata' -UseBasicParsing; Write-Host 'Download abgeschlossen.' } catch { Write-Host ('Fehler: ' + $_.Exception.Message) }}"

echo.

REM Pruefe ob Download erfolgreich
if exist "!TESSDATA!\deu.traineddata" (
    REM Pruefe Dateigroesse (sollte ca. 15 MB sein)
    for %%A in ("!TESSDATA!\deu.traineddata") do set FILESIZE=%%~zA
    
    if !FILESIZE! gtr 1000000 (
        echo ============================================
        echo    ERFOLGREICH!
        echo ============================================
        echo.
        echo [OK] Deutsche Sprachdatei installiert!
        echo     Pfad: !TESSDATA!\deu.traineddata
        echo     Groesse: !FILESIZE! Bytes
        echo.
        echo Tesseract kann jetzt deutsche Texte erkennen.
        echo.
        echo NAECHSTER SCHRITT:
        echo   Teste auf der Webseite unter Einstellungen
        echo   mit dem "Testen" Button.
    ) else (
        echo [WARNUNG] Datei ist zu klein - Download war unvollstaendig!
        del "!TESSDATA!\deu.traineddata" 2>nul
        goto :manual_download
    )
) else (
    :manual_download
    echo ============================================
    echo    DOWNLOAD FEHLGESCHLAGEN
    echo ============================================
    echo.
    echo Der automatische Download hat nicht funktioniert.
    echo.
    echo MANUELLE INSTALLATION:
    echo.
    echo 1. Oeffne diesen Link im Browser:
    echo    https://github.com/tesseract-ocr/tessdata/raw/main/deu.traineddata
    echo.
    echo 2. Der Download startet automatisch
    echo.
    echo 3. Verschiebe/Kopiere die heruntergeladene Datei nach:
    echo    !TESSDATA!\deu.traineddata
    echo.
    echo Moechtest du den Link jetzt oeffnen? (j/n)
    set /p "OPEN="
    if /i "!OPEN!"=="j" (
        start https://github.com/tesseract-ocr/tessdata/raw/main/deu.traineddata
        echo.
        echo Der Download sollte jetzt starten.
        echo Die Datei liegt dann in deinem Downloads-Ordner.
        echo.
        echo Kopiere sie nach: !TESSDATA!\
    )
)

echo.
pause
