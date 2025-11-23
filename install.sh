#!/bin/bash
################################################################################
# Werkstatt-Archiv - macOS/Linux Installation Script
# Erstellt Virtual Environment und installiert Dependencies
################################################################################

# Farben
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  Werkstatt-Archiv - Installation${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
echo ""

# 1. Python-Version prüfen
echo -e "${YELLOW}[1/6]${NC} Prüfe Python-Installation..."
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}✗${NC} Python3 nicht gefunden!"
    echo ""
    echo "Bitte installieren Sie Python 3.9 oder höher:"
    echo "  macOS: brew install python3"
    echo "  Linux: sudo apt install python3 python3-venv"
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1)
echo -e "${GREEN}✓${NC} $PYTHON_VERSION"
echo ""

# 2. Virtual Environment erstellen
echo -e "${YELLOW}[2/6]${NC} Erstelle Virtual Environment..."
if [ -d ".venv" ]; then
    echo -e "${YELLOW}⚠${NC}  Virtual Environment existiert bereits (.venv)"
    read -p "Neu erstellen? (j/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Jj]$ ]]; then
        rm -rf .venv
        echo -e "${YELLOW}→${NC} Lösche altes venv..."
    else
        echo -e "${BLUE}→${NC} Verwende bestehendes venv"
    fi
fi

if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓${NC} Virtual Environment erstellt (.venv)"
    else
        echo -e "${RED}✗${NC} Fehler beim Erstellen des Virtual Environment!"
        exit 1
    fi
fi
echo ""

# 3. Virtual Environment aktivieren
echo -e "${YELLOW}[3/6]${NC} Aktiviere Virtual Environment..."
source .venv/bin/activate
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓${NC} Virtual Environment aktiviert"
else
    echo -e "${RED}✗${NC} Fehler beim Aktivieren!"
    exit 1
fi
echo ""

# 4. pip aktualisieren
echo -e "${YELLOW}[4/6]${NC} Aktualisiere pip..."
python -m pip install --upgrade pip --quiet
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓${NC} pip aktualisiert"
else
    echo -e "${YELLOW}⚠${NC}  pip-Update fehlgeschlagen (nicht kritisch)"
fi
echo ""

# 5. Requirements installieren
echo -e "${YELLOW}[5/6]${NC} Installiere Python-Pakete..."
if [ ! -f "requirements.txt" ]; then
    echo -e "${RED}✗${NC} requirements.txt nicht gefunden!"
    exit 1
fi

echo -e "${BLUE}→${NC} Installiere aus requirements.txt..."
pip install -r requirements.txt

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓${NC} Alle Pakete installiert"
else
    echo -e "${RED}✗${NC} Installation fehlgeschlagen!"
    exit 1
fi
echo ""

# 6. Tesseract prüfen
echo -e "${YELLOW}[6/6]${NC} Prüfe Tesseract OCR..."
if command -v tesseract &> /dev/null; then
    TESSERACT_VERSION=$(tesseract --version 2>&1 | head -1)
    echo -e "${GREEN}✓${NC} $TESSERACT_VERSION"
    
    # Sprachen prüfen
    if tesseract --list-langs 2>&1 | grep -q "deu"; then
        echo -e "${GREEN}✓${NC} Deutsche Sprachunterstützung vorhanden"
    else
        echo -e "${YELLOW}⚠${NC}  Deutsche Sprache (deu) nicht gefunden"
        echo -e "${BLUE}→${NC} Installiere mit: brew install tesseract-lang (macOS)"
        echo -e "${BLUE}→${NC} oder: sudo apt install tesseract-ocr-deu (Linux)"
    fi
else
    echo -e "${YELLOW}⚠${NC}  Tesseract OCR ist nicht installiert!"
    echo ""
    echo "Tesseract wird für die OCR-Texterkennung benötigt."
    echo ""
    echo "Installation:"
    echo "  macOS:  brew install tesseract tesseract-lang"
    echo "  Linux:  sudo apt install tesseract-ocr tesseract-ocr-deu"
    echo ""
    echo "WICHTIG: Ohne Tesseract kann das Programm keine PDFs verarbeiten!"
fi
echo ""

# 7. Logs-Verzeichnis erstellen
echo "Erstelle Verzeichnisse..."
mkdir -p logs
echo -e "${GREEN}✓${NC} logs/ Verzeichnis erstellt"
echo ""

# Zusammenfassung
echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  Installation abgeschlossen!${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${GREEN}Nächste Schritte:${NC}"
echo ""
echo -e "${YELLOW}[1] Konfiguration (Web-UI - EMPFOHLEN):${NC}"
echo "    ./start_server.sh"
echo "    Öffnen Sie: http://localhost:8080/settings"
echo ""
echo -e "${YELLOW}[2] Konfiguration (CLI):${NC}"
echo "    source .venv/bin/activate"
echo "    python main.py --set-input-folder \"/Volumes/Server/Scans\""
echo "    python main.py --set-archiv-root \"/Volumes/Server/Archiv\""
echo "    python main.py --set-backup-target \"/Volumes/Server/Backups\""
echo ""
echo -e "${YELLOW}[3] Tesseract testen:${NC}"
echo "    source .venv/bin/activate"
echo "    python main.py --test-tesseract"
echo ""
echo -e "${YELLOW}[4] Server starten:${NC}"
echo "    ./start_server.sh"
echo ""
echo -e "${BLUE}Hinweis:${NC} Virtual Environment aktivieren mit:"
echo "    source .venv/bin/activate"
echo ""
