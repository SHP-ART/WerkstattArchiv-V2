@echo off
setlocal EnableDelayedExpansion
chcp 65001 >nul 2>&1
title Tesseract Diagnose

echo.
echo ============================================
echo    TESSERACT DIAGNOSE
echo ============================================
echo.

REM === Tesseract Pfad ===
echo [1] Tesseract Installation:
echo.

set "TESS_EXE="
if exist "C:\Program Files\Tesseract-OCR\tesseract.exe" (
    set "TESS_EXE=C:\Program Files\Tesseract-OCR\tesseract.exe"
)
if exist "C:\Program Files (x86)\Tesseract-OCR\tesseract.exe" (
    set "TESS_EXE=C:\Program Files (x86)\Tesseract-OCR\tesseract.exe"
)

if not defined TESS_EXE (
    echo [FEHLER] Tesseract nicht gefunden!
    pause
    exit /b 1
)

echo Tesseract: !TESS_EXE!
echo.
"!TESS_EXE!" --version
echo.

REM === Tessdata Ordner ===
echo ============================================
echo [2] Tessdata Ordner:
echo.

set "TESSDATA=C:\Program Files\Tesseract-OCR\tessdata"
if not exist "!TESSDATA!" (
    set "TESSDATA=C:\Program Files (x86)\Tesseract-OCR\tessdata"
)

echo Ordner: !TESSDATA!
echo.

if exist "!TESSDATA!" (
    echo Inhalt des tessdata-Ordners:
    echo -------------------------------------------
    dir "!TESSDATA!" /b
    echo -------------------------------------------
) else (
    echo [FEHLER] Tessdata-Ordner nicht gefunden!
)

echo.

REM === Deutsche Sprachdatei ===
echo ============================================
echo [3] Deutsche Sprachdatei (deu.traineddata):
echo.

set "DEU_FILE=!TESSDATA!\deu.traineddata"

if exist "!DEU_FILE!" (
    echo Datei existiert: JA
    echo Pfad: !DEU_FILE!
    echo.
    echo Datei-Details:
    for %%A in ("!DEU_FILE!") do (
        echo   Groesse: %%~zA Bytes
        echo   Datum:   %%~tA
    )
    
    REM Pruefe Groesse - sollte ca. 15 MB sein
    for %%A in ("!DEU_FILE!") do set FILESIZE=%%~zA
    
    echo.
    if !FILESIZE! lss 1000000 (
        echo [WARNUNG] Datei ist zu klein! Erwartet: ~15 MB, Gefunden: !FILESIZE! Bytes
        echo           Die Datei ist moeglicherweise beschaedigt oder unvollstaendig.
        echo.
        echo LOESUNG: Loesche die Datei und lade sie neu herunter.
    ) else (
        echo [OK] Dateigroesse sieht gut aus.
    )
) else (
    echo Datei existiert: NEIN
    echo.
    echo Suche nach aehnlichen Dateien...
    dir "!TESSDATA!\deu*" /b 2>nul
    if !errorlevel! neq 0 (
        echo Keine deu-Dateien gefunden.
    )
)

echo.

REM === Verfuegbare Sprachen laut Tesseract ===
echo ============================================
echo [4] Verfuegbare Sprachen laut Tesseract:
echo.

"!TESS_EXE!" --list-langs 2>&1

echo.

REM === TESSDATA_PREFIX Umgebungsvariable ===
echo ============================================
echo [5] Umgebungsvariablen:
echo.

if defined TESSDATA_PREFIX (
    echo TESSDATA_PREFIX: !TESSDATA_PREFIX!
) else (
    echo TESSDATA_PREFIX: (nicht gesetzt)
)

echo.

REM === Test mit deutscher Sprache ===
echo ============================================
echo [6] OCR-Test mit deutscher Sprache:
echo.

echo Teste: tesseract --version mit -l deu
"!TESS_EXE!" -l deu --version 2>&1

echo.
echo ============================================
echo [7] ZUSAMMENFASSUNG UND LOESUNG:
echo ============================================
echo.

REM Pruefe nochmal die Sprachen
"!TESS_EXE!" --list-langs 2>&1 | findstr /i "deu" >nul
if !errorlevel!==0 (
    echo [OK] Deutsch ist verfuegbar - Tesseract sollte funktionieren!
    echo      Starte den Webserver neu und teste erneut.
) else (
    echo [PROBLEM] Deutsch wird von Tesseract nicht erkannt.
    echo.
    echo Moegliche Ursachen:
    echo   1. deu.traineddata ist beschaedigt
    echo   2. Falscher Dateiname (z.B. deu.traineddata.txt)
    echo   3. Falsche Berechtigungen
    echo.
    echo LOESUNG:
    echo   1. Loesche: !DEU_FILE!
    echo   2. Lade neu herunter:
    echo      https://github.com/tesseract-ocr/tessdata/raw/main/deu.traineddata
    echo   3. Speichere als: !DEU_FILE!
    echo.
    
    set /p "DELETE=Soll ich die Datei jetzt loeschen? (j/n): "
    if /i "!DELETE!"=="j" (
        del "!DEU_FILE!" 2>nul
        del "!TESSDATA!\deu.traineddata.txt" 2>nul
        echo Datei geloescht. Bitte lade sie neu herunter.
    )
)

echo.
pause
