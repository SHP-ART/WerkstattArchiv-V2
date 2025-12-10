@echo off
echo ========================================
echo   Tesseract Direkt-Download
echo ========================================
echo.

echo Diese einfache Methode oeffnet nur den Download.
echo Du musst die Datei dann mit 7-Zip/WinRAR entpacken.
echo.
echo Download wird geoeffnet...
echo.

start https://github.com/UB-Mannheim/tesseract/releases/download/v5.3.3.20231005/tesseract-ocr-w64-setup-5.3.3.20231005.exe

echo ========================================
echo   WICHTIG:
echo ========================================
echo.
echo Nach dem Download:
echo.
echo 1. Rechtsklick auf die .exe
echo 2. Waehle "7-Zip" oder "WinRAR"
echo 3. "Entpacken nach..."
echo 4. Zielordner: %CD%\tesseract_portable
echo.
echo Falls du kein 7-Zip hast:
echo https://www.7-zip.org/download.html
echo.
pause
