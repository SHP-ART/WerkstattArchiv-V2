@echo off
REM ============================================================
REM Git Installation Helper for Windows
REM ============================================================

echo.
echo ============================================================
echo   Git Installation Helper
echo ============================================================
echo.

REM Pruefe ob Git bereits installiert ist
git --version >nul 2>&1
if not errorlevel 1 (
    echo [OK] Git ist bereits installiert:
    git --version
    echo.
    echo Keine Installation noetig!
    echo.
    pause
    exit /b 0
)

echo [INFO] Git ist nicht installiert
echo.
echo ============================================================
echo   Installationsoptionen
echo ============================================================
echo.
echo [1] AUTOMATISCH - Git mit winget installieren (empfohlen)
echo [2] MANUELL - Git-Installer herunterladen
echo [3] PORTABLE - Git Portable (ohne Installation)
echo [4] Abbrechen
echo.

choice /C 1234 /N /M "Waehlen Sie eine Option (1-4): "
set OPTION=%ERRORLEVEL%

echo.

if %OPTION%==4 (
    echo Installation abgebrochen.
    pause
    exit /b 0
)

if %OPTION%==1 goto WINGET_INSTALL
if %OPTION%==2 goto MANUAL_DOWNLOAD
if %OPTION%==3 goto PORTABLE_INFO

:WINGET_INSTALL
echo ============================================================
echo   Installation mit winget
echo ============================================================
echo.

REM Pruefe ob winget verfuegbar ist
winget --version >nul 2>&1
if errorlevel 1 (
    echo [FEHLER] winget ist nicht verfuegbar!
    echo.
    echo winget ist ab Windows 10 Version 1809 verfuegbar.
    echo Bitte aktualisieren Sie Windows oder waehlen Sie Option 2.
    echo.
    pause
    exit /b 1
)

echo [*] Installiere Git mit winget...
echo.
echo Dies kann einige Minuten dauern...
echo.

winget install --id Git.Git -e --source winget

if errorlevel 1 (
    echo.
    echo [FEHLER] Installation fehlgeschlagen!
    echo.
    echo Moegliche Loesungen:
    echo 1. Als Administrator ausfuehren (Rechtsklick -> Als Admin)
    echo 2. Windows Update durchfuehren
    echo 3. Option 2 waehlen (Manueller Download)
    echo.
    pause
    exit /b 1
)

echo.
echo [OK] Git erfolgreich installiert!
echo.
echo WICHTIG: Bitte schliessen Sie dieses Fenster und oeffnen Sie
echo          ein NEUES CMD/PowerShell Fenster, damit Git verfuegbar ist.
echo.
goto VERIFY

:MANUAL_DOWNLOAD
echo ============================================================
echo   Manueller Download
echo ============================================================
echo.
echo [*] Oeffne Git Download-Seite im Browser...
echo.

start https://git-scm.com/download/win

echo.
echo Bitte folgen Sie diesen Schritten:
echo.
echo 1. Laden Sie Git fuer Windows herunter (64-bit empfohlen)
echo 2. Fuehren Sie den Installer aus
echo 3. Empfohlene Einstellungen:
echo    - "Use Git from the Windows Command Prompt"
echo    - "Checkout Windows-style, commit Unix-style line endings"
echo    - "Use Windows' default console window"
echo 4. Schliessen Sie die Installation ab
echo 5. Oeffnen Sie ein NEUES CMD-Fenster
echo 6. Fuehren Sie diese Datei erneut aus um zu pruefen
echo.
pause
exit /b 0

:PORTABLE_INFO
echo ============================================================
echo   Git Portable
echo ============================================================
echo.
echo [*] Oeffne Git Portable Download-Seite...
echo.

start https://git-scm.com/download/win

echo.
echo Git Portable:
echo.
echo Vorteile:
echo + Keine Installation noetig
echo + Kann auf USB-Stick verwendet werden
echo + Keine Admin-Rechte erforderlich
echo.
echo Nachteile:
echo - Muss manuell zum PATH hinzugefuegt werden
echo - Nicht systemweit verfuegbar
echo.
echo Bitte laden Sie "PortableGit" herunter und entpacken Sie es.
echo.
pause
exit /b 0

:VERIFY
echo ============================================================
echo   Pruefe Installation
echo ============================================================
echo.
echo [*] Warte 3 Sekunden...
timeout /t 3 /nobreak >nul

git --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo [WARNUNG] Git ist noch nicht verfuegbar im aktuellen Terminal.
    echo.
    echo WICHTIG: Bitte schliessen Sie ALLE CMD/PowerShell Fenster
    echo          und oeffnen Sie ein NEUES Fenster.
    echo.
    echo Dann koennen Sie pruefen mit: git --version
    echo.
) else (
    echo [OK] Git ist verfuegbar:
    git --version
    echo.
    echo ============================================================
    echo   Git Konfiguration (optional)
    echo ============================================================
    echo.
    echo Moechten Sie Git jetzt konfigurieren?
    echo (Name und E-Mail fuer Commits)
    echo.
    choice /C JN /M "Jetzt konfigurieren"
    if not errorlevel 2 (
        echo.
        set /p USERNAME="Ihr Name: "
        set /p USEREMAIL="Ihre E-Mail: "
        
        git config --global user.name "!USERNAME!"
        git config --global user.email "!USEREMAIL!"
        
        echo.
        echo [OK] Git konfiguriert:
        git config --global user.name
        git config --global user.email
    )
    echo.
    echo ============================================================
    echo   Installation abgeschlossen!
    echo ============================================================
    echo.
    echo Naechste Schritte:
    echo 1. Fuehren Sie install.bat aus (falls noch nicht geschehen)
    echo 2. Das Update-System funktioniert jetzt: update.bat
    echo.
)

pause
