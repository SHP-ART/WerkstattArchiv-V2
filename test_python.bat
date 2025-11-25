@echo off
REM ============================================================
REM Python-Test Script - Prueft Python und Abhaengigkeiten
REM ============================================================

echo.
echo ============================================================
echo   Python-Test
echo ============================================================
echo.

echo [1] Pruefe Python...
python --version
if errorlevel 1 (
    echo [FEHLER] Python nicht gefunden!
    echo Bitte installieren Sie Python von https://www.python.org/
    pause
    exit /b 1
)
echo [OK] Python gefunden
echo.

echo [2] Pruefe Python-Pfad...
where python
echo.

echo [3] Pruefe Virtual Environment...
if exist ".venv\Scripts\activate.bat" (
    echo [OK] .venv gefunden
    call .venv\Scripts\activate.bat
    echo [OK] venv aktiviert
) else (
    echo [FEHLER] .venv nicht gefunden - Bitte install.bat ausfuehren
    pause
    exit /b 1
)
echo.

echo [4] Pruefe Abhaengigkeiten...
python -c "import sys; print('Python:', sys.version)"
echo.

python -c "import flask; print('[OK] Flask:', flask.__version__)" 2>nul || echo [FEHLER] Flask nicht installiert
python -c "import waitress; print('[OK] Waitress:', waitress.__version__)" 2>nul || echo [FEHLER] Waitress nicht installiert
python -c "import PyPDF2; print('[OK] PyPDF2:', PyPDF2.__version__)" 2>nul || echo [FEHLER] PyPDF2 nicht installiert
python -c "import PIL; print('[OK] Pillow:', PIL.__version__)" 2>nul || echo [FEHLER] Pillow nicht installiert
python -c "import pytesseract; print('[OK] pytesseract installiert')" 2>nul || echo [FEHLER] pytesseract nicht installiert
echo.

echo [5] Teste web_app.py Import...
python -c "import web_app; print('[OK] web_app.py kann importiert werden')" 2>nul
if errorlevel 1 (
    echo [FEHLER] web_app.py Import fehlgeschlagen
    echo Details:
    python -c "import web_app"
) else (
    echo [OK] web_app.py Import erfolgreich
)
echo.

echo ============================================================
echo   Test abgeschlossen
echo ============================================================
echo.

pause
