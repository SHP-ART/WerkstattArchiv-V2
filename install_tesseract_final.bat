@echo off
echo ========================================
echo   EINFACHSTE LÖSUNG: Tesseract Portable
echo ========================================
echo.
echo Warum Tesseract statt EasyOCR?
echo.
echo EasyOCR benötigt:
echo - Visual Studio Build Tools (7 GB!)
echo - C++ Compiler
echo - scikit-image kompilieren
echo.
echo Tesseract Portable benötigt:
echo - Nur 1x herunterladen
echo - Entpacken
echo - Fertig!
echo.
pause
echo.
echo Lade Tesseract Portable herunter...
echo.

REM Portable Version von GitHub holen
set "URL=https://github.com/UB-Mannheim/tesseract/releases/download/v5.3.3.20231005/tesseract-ocr-w64-setup-5.3.3.20231005.exe"
set "DOWNLOAD=%TEMP%\tesseract_setup.exe"

powershell -Command "& {[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; $ProgressPreference = 'SilentlyContinue'; Invoke-WebRequest -Uri '%URL%' -OutFile '%DOWNLOAD%' -UserAgent 'Mozilla/5.0'}"

if not exist "%DOWNLOAD%" (
    echo.
    echo DOWNLOAD FEHLGESCHLAGEN!
    echo.
    echo Bitte manuell herunterladen:
    echo %URL%
    echo.
    echo Und dann entpacken nach: %CD%\tesseract_portable
    echo.
    pause
    exit /b 1
)

echo.
echo Download erfolgreich!
echo Installiere nach: %CD%\tesseract_portable
echo.

"%DOWNLOAD%" /S /D=%CD%\tesseract_portable

timeout /t 10 /nobreak >nul

if exist "%CD%\tesseract_portable\tesseract.exe" (
    echo.
    echo ========================================
    echo   ERFOLG!
    echo ========================================
    echo.
    echo Tesseract installiert in:
    echo %CD%\tesseract_portable
    echo.
    
    "%CD%\tesseract_portable\tesseract.exe" --version
    
    echo.
    echo Starte den Web-Server neu - OCR funktioniert jetzt!
) else (
    echo.
    echo Installation fehlgeschlagen.
    echo.
    echo MANUELLE ANLEITUNG:
    echo 1. Lade herunter: %URL%
    echo 2. Doppelklick auf die .exe
    echo 3. Installiere nach: %CD%\tesseract_portable
    echo 4. Bei Sprache: German auswaehlen!
)

echo.
del /f /q "%DOWNLOAD%" 2>nul
pause
