@echo off
echo ========================================
echo   Werkstatt-Archiv EXE Builder
echo ========================================
echo.

REM Pruefen ob PyInstaller installiert ist
python -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo PyInstaller wird installiert...
    python -m pip install pyinstaller
    if errorlevel 1 (
        echo.
        echo FEHLER: PyInstaller konnte nicht installiert werden!
        pause
        exit /b 1
    )
)

echo.
echo Welche EXE moechtest du erstellen?
echo.
echo [1] Web-Server (Empfohlen)
echo [2] Kommandozeilen-Tool
echo [3] Beide
echo.
set /p "CHOICE=Wahl (1-3): "

if "%CHOICE%"=="1" goto BUILD_WEB
if "%CHOICE%"=="2" goto BUILD_CLI
if "%CHOICE%"=="3" goto BUILD_BOTH
goto INVALID

:BUILD_BOTH
call :BUILD_WEB_FUNC
echo.
call :BUILD_CLI_FUNC
goto END

:BUILD_WEB
call :BUILD_WEB_FUNC
goto END

:BUILD_CLI
call :BUILD_CLI_FUNC
goto END

:BUILD_WEB_FUNC
echo.
echo ========================================
echo   Erstelle Web-Server EXE...
echo ========================================
echo.

REM Web-Server kompilieren
python -m PyInstaller ^
    --name="WerkstattArchiv-WebServer" ^
    --onefile ^
    --console ^
    --icon=Logo/logo.ico ^
    --add-data="templates;templates" ^
    --add-data="Logo;Logo" ^
    --hidden-import=waitress ^
    --hidden-import=flask ^
    --hidden-import=pytesseract ^
    --hidden-import=pdf2image ^
    --hidden-import=PIL ^
    --hidden-import=watchdog ^
    --hidden-import=yaml ^
    --collect-all=flask ^
    --collect-all=jinja2 ^
    web_app.py

if errorlevel 1 (
    echo.
    echo FEHLER: Build fehlgeschlagen!
    exit /b 1
)

echo.
echo Web-Server EXE erstellt: dist\WerkstattArchiv-WebServer.exe
exit /b 0

:BUILD_CLI_FUNC
echo.
echo ========================================
echo   Erstelle CLI-Tool EXE...
echo ========================================
echo.

REM CLI-Tool kompilieren
python -m PyInstaller ^
    --name="WerkstattArchiv" ^
    --onefile ^
    --console ^
    --icon=Logo/logo.ico ^
    --hidden-import=pytesseract ^
    --hidden-import=pdf2image ^
    --hidden-import=PIL ^
    --hidden-import=watchdog ^
    --hidden-import=yaml ^
    main.py

if errorlevel 1 (
    echo.
    echo FEHLER: Build fehlgeschlagen!
    exit /b 1
)

echo.
echo CLI-Tool EXE erstellt: dist\WerkstattArchiv.exe
exit /b 0

:INVALID
echo.
echo Ungueltige Wahl!
pause
exit /b 1

:END
echo.
echo ========================================
echo   Build abgeschlossen!
echo ========================================
echo.
echo EXE-Dateien befinden sich in: dist\
echo.
echo WICHTIG:
echo - Die EXE ist eigenstaendig lauffaehig
echo - Tesseract muss separat installiert sein
echo - Oder verwende tesseract_portable im gleichen Ordner
echo.
echo Starte die EXE durch Doppelklick oder:
if "%CHOICE%"=="1" echo   dist\WerkstattArchiv-WebServer.exe
if "%CHOICE%"=="2" echo   dist\WerkstattArchiv.exe
if "%CHOICE%"=="3" (
    echo   dist\WerkstattArchiv-WebServer.exe
    echo   dist\WerkstattArchiv.exe
)
echo.
pause
