@echo off
REM ============================================================
REM Werkstatt-Archiv - Windows Start-Skript
REM ============================================================

echo.
echo ============================================================
echo   Werkstatt-Archiv
echo ============================================================
echo.

REM Prüfe ob Python installiert ist
python --version >nul 2>&1
if errorlevel 1 (
    echo [FEHLER] Python ist nicht installiert!
    echo Bitte fuehren Sie zuerst install.bat aus.
    echo.
    pause
    exit /b 1
)

REM Prüfe ob Konfiguration vorhanden ist
if not exist ".archiv_config.json" (
    echo [WARNUNG] Keine Konfiguration gefunden!
    echo Bitte fuehren Sie zuerst install.bat aus.
    echo.
    pause
    exit /b 1
)

REM Zeige Menü
:MENU
cls
echo.
echo ============================================================
echo   Werkstatt-Archiv - Hauptmenue
echo ============================================================
echo.
echo [1] Web-UI starten (empfohlen^)
echo [2] Einmalige Verarbeitung (Batch-Modus^)
echo [3] Watch-Modus (dauerhafte Ueberwachung^)
echo [4] Suche nach Auftragsnummer
echo [5] Suche nach Schlagwort
echo [6] Backup erstellen
echo [7] Tesseract testen
echo [8] Konfiguration anzeigen
echo [9] Beenden
echo.
echo ============================================================

set /p choice="Bitte waehlen Sie [1-9]: "

if "%choice%"=="1" goto WEBUI
if "%choice%"=="2" goto BATCH
if "%choice%"=="3" goto WATCH
if "%choice%"=="4" goto SEARCH_AUFTRAG
if "%choice%"=="5" goto SEARCH_KEYWORD
if "%choice%"=="6" goto BACKUP
if "%choice%"=="7" goto TEST_TESSERACT
if "%choice%"=="8" goto CONFIG
if "%choice%"=="9" goto END

echo Ungueltige Auswahl!
timeout /t 2 >nul
goto MENU

:WEBUI
cls
echo.
echo ============================================================
echo   Web-UI wird gestartet...
echo ============================================================
echo.
echo Die Web-Oberflaeche wird gestartet auf:
echo.
echo   http://localhost:5000
echo   http://127.0.0.1:5000
echo.
echo Weitere IP-Adressen dieses Computers:
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4"') do echo   http:%%a:5000
echo.
echo Oeffnen Sie eine dieser URLs im Browser.
echo Druecken Sie Strg+C um die Web-UI zu beenden.
echo.
echo ============================================================
echo.
python web_app.py
pause
goto MENU

:BATCH
cls
echo.
echo ============================================================
echo   Einmalige Verarbeitung
echo ============================================================
echo.
python main.py --process-input
echo.
pause
goto MENU

:WATCH
cls
echo.
echo ============================================================
echo   Watch-Modus (dauerhafte Ueberwachung)
echo ============================================================
echo.
echo Der Eingangsordner wird kontinuierlich ueberwacht.
echo Neue PDFs werden automatisch verarbeitet.
echo.
echo Druecken Sie Strg+C um den Watch-Modus zu beenden.
echo.
python main.py --watch
pause
goto MENU

:SEARCH_AUFTRAG
cls
echo.
echo ============================================================
echo   Suche nach Auftragsnummer
echo ============================================================
echo.
set /p auftrag="Auftragsnummer eingeben: "
echo.
python main.py --search-auftrag %auftrag%
echo.
pause
goto MENU

:SEARCH_KEYWORD
cls
echo.
echo ============================================================
echo   Suche nach Schlagwort
echo ============================================================
echo.
set /p keyword="Schlagwort eingeben: "
echo.
python main.py --search-keyword "%keyword%"
echo.
pause
goto MENU

:BACKUP
cls
echo.
echo ============================================================
echo   Backup erstellen
echo ============================================================
echo.
set /p include_archive="Archiv mit sichern? (j/n): "
if /i "%include_archive%"=="j" (
    python main.py --backup --include-archive
) else (
    python main.py --backup
)
echo.
pause
goto MENU

:TEST_TESSERACT
cls
echo.
echo ============================================================
echo   Tesseract-Test
echo ============================================================
echo.
python main.py --test-tesseract
echo.
pause
goto MENU

:CONFIG
cls
echo.
echo ============================================================
echo   Aktuelle Konfiguration
echo ============================================================
echo.
python -c "import config; cfg = config.Config(); import json; print(json.dumps(cfg.config, indent=2, ensure_ascii=False))"
echo.
echo ============================================================
echo.
pause
goto MENU

:END
echo.
echo Auf Wiedersehen!
echo.
exit /b 0
