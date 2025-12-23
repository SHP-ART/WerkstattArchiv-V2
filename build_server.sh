#!/bin/bash
# ============================================================
# Werkstatt-Archiv Server - EXE Build Script (macOS/Linux)
# Erstellt eine eigenständige ausführbare Datei
# ============================================================

set -e  # Stop bei Fehler

echo "============================================================"
echo "Werkstatt-Archiv Server - Build"
echo "============================================================"
echo ""

# Prüfe Python
if ! command -v python3 &> /dev/null; then
    echo "[FEHLER] Python 3 nicht gefunden!"
    echo "Bitte Python 3.9+ installieren"
    exit 1
fi

echo "[1/5] Prüfe Virtual Environment..."
if [ ! -f ".venv/bin/python" ]; then
    echo "    Virtual Environment nicht gefunden. Erstelle..."
    python3 -m venv .venv
fi

echo "[2/5] Aktiviere Virtual Environment..."
source .venv/bin/activate

echo "[3/5] Installiere/Aktualisiere PyInstaller..."
pip install --upgrade pyinstaller

echo "[4/5] Installiere Abhängigkeiten..."
pip install -r requirements.txt || echo "    [WARNUNG] Einige Abhängigkeiten fehlen"

echo ""
echo "[5/5] Baue ausführbare Datei..."
echo "    Dies kann einige Minuten dauern..."
echo ""

# Lösche alte Build-Artefakte
rm -rf build dist/WerkstattArchiv-Server 2>/dev/null || true

# PyInstaller ausführen
pyinstaller --clean --noconfirm server.spec

if [ $? -eq 0 ]; then
    echo ""
    echo "============================================================"
    echo "Build erfolgreich!"
    echo "============================================================"
    echo ""
    echo "Die ausführbare Datei wurde erstellt:"
    echo "  dist/WerkstattArchiv-Server"
    echo ""
    echo "WICHTIG:"
    echo "  - Tesseract muss auf dem Zielsystem installiert sein"
    echo "  - Poppler muss auf dem Zielsystem installiert sein"
    echo "  - Konfiguration (.archiv_config.json) muss im gleichen Ordner liegen"
    echo ""
    echo "Zum Testen:"
    echo "  cd dist"
    echo "  ./WerkstattArchiv-Server"
    echo ""
else
    echo ""
    echo "[FEHLER] Build fehlgeschlagen!"
    exit 1
fi
