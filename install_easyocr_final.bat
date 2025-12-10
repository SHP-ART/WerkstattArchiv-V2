@echo off
echo ========================================
echo   EasyOCR Installation (Final)
echo ========================================
echo.

echo Installiere EasyOCR ohne scikit-image...
echo (Workaround fuer Build-Probleme)
echo.

REM Installiere vorkompilierte Wheels zuerst
echo Schritt 1: PyTorch (CPU-Version, ca. 200 MB)...
python -m pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu

if errorlevel 1 (
    echo FEHLER: PyTorch Installation fehlgeschlagen!
    pause
    exit /b 1
)

echo.
echo Schritt 2: OpenCV und Scipy...
python -m pip install opencv-python-headless scipy

if errorlevel 1 (
    echo FEHLER: OpenCV/Scipy Installation fehlgeschlagen!
    pause
    exit /b 1
)

echo.
echo Schritt 3: EasyOCR (ohne scikit-image)...
python -m pip install easyocr --no-deps

if errorlevel 1 (
    echo FEHLER: EasyOCR Installation fehlgeschlagen!
    pause
    exit /b 1
)

REM Manuell die Abhaengigkeiten installieren (ohne scikit-image)
python -m pip install python-bidi pyclipper shapely

echo.
echo ========================================
echo   Installation abgeschlossen!
echo ========================================
echo.

REM Test ob EasyOCR funktioniert
echo Teste EasyOCR...
python -c "import easyocr; print('✓ EasyOCR erfolgreich importiert!')" 2>nul

if errorlevel 1 (
    echo.
    echo WARNUNG: EasyOCR konnte nicht importiert werden.
    echo Versuche scikit-image mit vorkompl. Wheel...
    echo.
    python -m pip install --only-binary :all: scikit-image
)

echo.
echo Moechtest du jetzt auf EasyOCR umschalten?
set /p "SWITCH=Auf EasyOCR umschalten? (j/n): "

if /i "%SWITCH%"=="j" (
    echo.
    echo Erstelle Backup...
    copy ocr.py ocr_tesseract_backup.py >nul
    
    echo Wechsle zu EasyOCR...
    copy /Y ocr_easyocr.py ocr.py >nul
    
    echo.
    echo ✓ Erfolgreich auf EasyOCR umgeschaltet!
)

echo.
echo ========================================
echo   Fertig!
echo ========================================
echo.
echo WICHTIG beim ersten Start:
echo - EasyOCR laedt ca. 100 MB Sprachmodelle
echo - Dies passiert automatisch
echo - Nur beim ersten Mal!
echo.
echo Starte jetzt den Web-Server neu.
echo.
pause
