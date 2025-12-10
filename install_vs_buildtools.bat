@echo off
echo ========================================
echo   Visual Studio Build Tools Installation
echo   (Benoetigt fuer EasyOCR)
echo ========================================
echo.

echo EasyOCR benoetigt einen C++ Compiler.
echo Dies wird ca. 2-4 GB herunterladen und installieren.
echo.
echo Fortfahren?
pause

echo.
echo Lade Visual Studio Build Tools Installer...
echo.

REM Download VS Build Tools Installer
set "INSTALLER=%TEMP%\vs_buildtools.exe"
powershell -Command "& {[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://aka.ms/vs/17/release/vs_buildtools.exe' -OutFile '%INSTALLER%' -UseBasicParsing}"

if not exist "%INSTALLER%" (
    echo.
    echo FEHLER: Download fehlgeschlagen!
    echo.
    echo Bitte manuell herunterladen:
    echo https://aka.ms/vs/17/release/vs_buildtools.exe
    echo.
    pause
    exit /b 1
)

echo.
echo Starte Installation...
echo.
echo WICHTIG: Waehle bei der Installation:
echo - "Desktop development with C++"
echo - ODER mindestens: "C++ build tools"
echo.
pause

REM Installer starten (mit minimalen C++ Tools)
"%INSTALLER%" --quiet --wait --norestart --nocache ^
    --add Microsoft.VisualStudio.Workload.VCTools ^
    --add Microsoft.VisualStudio.Component.VC.Tools.x86.x64 ^
    --add Microsoft.VisualStudio.Component.Windows11SDK.22000 ^
    --includeRecommended

echo.
echo ========================================
echo   Build Tools installiert!
echo ========================================
echo.
echo Fuehre jetzt aus: install_easyocr_final.bat
echo.
pause
