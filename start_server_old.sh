#!/bin/bash
# Werkstatt-Archiv Web-Server Start-Script
# Dieses Script startet den Web-Server mit optimalen Einstellungen

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Farben für Output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}======================================${NC}"
echo -e "${GREEN}Werkstatt-Archiv Web-Server${NC}"
echo -e "${GREEN}======================================${NC}"

# Prüfe ob Virtual Environment existiert
if [ ! -d ".venv" ]; then
    echo -e "${RED}✗ Fehler: Virtual Environment (.venv) nicht gefunden!${NC}"
    echo -e "Erstelle Virtual Environment..."
    python3 -m venv .venv
    echo -e "${GREEN}✓ Virtual Environment erstellt${NC}"
    echo -e "Installiere Dependencies..."
    .venv/bin/pip install --upgrade pip
    .venv/bin/pip install -r requirements.txt
    echo -e "${GREEN}✓ Dependencies installiert${NC}"
fi

echo -e "${GREEN}✓ Virtual Environment gefunden${NC}"

# Prüfe ob bereits ein Server läuft
if lsof -Pi :8080 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo -e "${YELLOW}⚠ Warnung: Port 8080 ist bereits belegt!${NC}"
    echo -e "Möchten Sie den alten Prozess beenden? (j/n)"
    read -r answer
    if [[ "$answer" == "j" || "$answer" == "J" ]]; then
        pkill -f "web_app.py"
        sleep 2
        echo -e "${GREEN}✓ Alter Prozess beendet${NC}"
    else
        exit 1
    fi
fi

# Prüfe Dependencies
echo -e "\nPrüfe Dependencies..."
.venv/bin/python -c "import flask" 2>/dev/null || {
    echo -e "${RED}✗ Flask nicht installiert!${NC}"
    echo -e "Installiere Dependencies..."
    .venv/bin/pip install -r requirements.txt
    echo -e "${GREEN}✓ Dependencies installiert${NC}"
}
echo -e "${GREEN}✓ Alle Dependencies vorhanden${NC}"

# Starte Server
echo -e "\n${GREEN}Starte Server...${NC}"
echo -e "Zugriff über: ${YELLOW}http://127.0.0.1:8080${NC}"
echo -e "Zum Beenden: ${YELLOW}Ctrl+C${NC}\n"

# Server im Vordergrund starten (damit Ctrl+C funktioniert)
.venv/bin/python web_app.py --port 8080 --threaded

echo -e "\n${GREEN}Server wurde beendet.${NC}"
