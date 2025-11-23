#!/bin/bash
# ============================================================================
# Werkstatt-Archiv UPDATE Script (macOS/Linux)
# ============================================================================
# Dieses Script aktualisiert das Programm ohne Datenbank oder Archiv zu löschen
# - Git Pull (neueste Version)
# - Python Dependencies aktualisieren
# - Konfiguration und Daten bleiben erhalten
# ============================================================================

set -e  # Bei Fehler abbrechen

# Farben für Output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo ""
echo "============================================================================"
echo "Werkstatt-Archiv UPDATE"
echo "============================================================================"
echo ""

# Prüfe ob Git installiert ist
if ! command -v git &> /dev/null; then
    echo -e "${RED}[FEHLER] Git ist nicht installiert!${NC}"
    echo "         macOS: brew install git"
    echo "         Linux: sudo apt install git"
    exit 1
fi

# Prüfe ob wir in einem Git-Repository sind
if [ ! -d ".git" ]; then
    echo -e "${RED}[FEHLER] Kein Git-Repository gefunden!${NC}"
    echo "         Bitte führe dieses Script im Werkstatt-Archiv Ordner aus."
    exit 1
fi

# Prüfe ob Virtual Environment existiert
if [ ! -f ".venv/bin/activate" ]; then
    echo -e "${RED}[FEHLER] Virtual Environment nicht gefunden!${NC}"
    echo "         Bitte zuerst install.sh ausführen: ./install.sh"
    exit 1
fi

echo -e "${BLUE}[1/5] Prüfe auf lokale Änderungen...${NC}"
echo "------------------------------------------------------------------------------"

# Prüfe auf uncommittete Änderungen (nur Code-Dateien)
if ! git diff --quiet HEAD -- *.py *.bat *.sh templates/ static/ 2>/dev/null; then
    echo ""
    echo -e "${YELLOW}[WARNUNG] Du hast lokale Änderungen an Code-Dateien!${NC}"
    echo "          Diese werden beim Update überschrieben."
    echo ""
    git status --short
    echo ""
    read -p "Trotzdem fortfahren? Änderungen gehen verloren! (j/n): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Jj]$ ]]; then
        echo "Update abgebrochen."
        exit 0
    fi
    
    # Setze Code-Dateien zurück (Config und Daten bleiben erhalten)
    echo "Setze Code-Dateien zurück..."
    git checkout -- *.py *.bat *.sh templates/ static/ 2>/dev/null || true
fi

echo -e "${GREEN}✓ OK - Keine Konflikte mit Konfiguration/Daten${NC}"
echo ""

echo -e "${BLUE}[2/5] Hole neueste Version von GitHub...${NC}"
echo "------------------------------------------------------------------------------"

# Aktueller Branch
BRANCH=$(git rev-parse --abbrev-ref HEAD)
echo "Branch: $BRANCH"

# Aktueller Commit (vor Update)
OLD_COMMIT=$(git rev-parse --short HEAD)
echo "Aktueller Commit: $OLD_COMMIT"

# Git Pull
if ! git pull origin "$BRANCH"; then
    echo ""
    echo -e "${RED}[FEHLER] Git Pull fehlgeschlagen!${NC}"
    echo "         Prüfe deine Internetverbindung oder GitHub-Zugriff."
    exit 1
fi

# Neuer Commit (nach Update)
NEW_COMMIT=$(git rev-parse --short HEAD)

echo ""
if [ "$OLD_COMMIT" == "$NEW_COMMIT" ]; then
    echo -e "${GREEN}✓ Bereits auf neuestem Stand ($OLD_COMMIT)${NC}"
else
    echo -e "${GREEN}✓ Update: $OLD_COMMIT → $NEW_COMMIT${NC}"
    echo ""
    echo "Änderungen:"
    git log --oneline "$OLD_COMMIT".."$NEW_COMMIT"
fi
echo ""

echo -e "${BLUE}[3/5] Aktiviere Virtual Environment...${NC}"
echo "------------------------------------------------------------------------------"
source .venv/bin/activate
if [ $? -ne 0 ]; then
    echo -e "${RED}[FEHLER] Konnte Virtual Environment nicht aktivieren!${NC}"
    exit 1
fi
echo -e "${GREEN}✓ OK - Virtual Environment aktiv${NC}"
echo ""

echo -e "${BLUE}[4/5] Aktualisiere Python-Pakete...${NC}"
echo "------------------------------------------------------------------------------"
python -m pip install --upgrade pip > /dev/null 2>&1
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo -e "${RED}[FEHLER] Paket-Installation fehlgeschlagen!${NC}"
    exit 1
fi
echo -e "${GREEN}✓ OK - Alle Pakete aktualisiert${NC}"
echo ""

echo -e "${BLUE}[5/5] Prüfe Konfiguration...${NC}"
echo "------------------------------------------------------------------------------"

# Prüfe ob Config existiert
if [ -f ".archiv_config.json" ]; then
    echo -e "${GREEN}✓ OK - Konfiguration gefunden: .archiv_config.json${NC}"
elif [ -f ".archiv_config.yaml" ]; then
    echo -e "${GREEN}✓ OK - Konfiguration gefunden: .archiv_config.yaml${NC}"
else
    echo -e "${YELLOW}[WARNUNG] Keine Konfiguration gefunden!${NC}"
    echo "          Bitte Config erstellen mit: python main.py --set-input-folder [PFAD]"
fi

# Prüfe ob Datenbank existiert
if python -c "import config; c = config.Config(); db_path = c.get_archiv_root() / 'werkstatt.db'; exit(0 if db_path.exists() else 1)" 2>/dev/null; then
    echo -e "${GREEN}✓ OK - Datenbank gefunden und intakt${NC}"
else
    echo -e "${YELLOW}[INFO] Datenbank wird beim ersten Start automatisch erstellt${NC}"
fi

echo ""
echo "============================================================================"
echo -e "${GREEN}UPDATE ERFOLGREICH ABGESCHLOSSEN!${NC}"
echo "============================================================================"
echo ""
echo "Nächste Schritte:"
echo "  - Server starten:  ./start_server.sh"
echo "  - CLI verwenden:   python main.py --help"
echo ""
echo "Wichtig: Deine Konfiguration, Datenbank und Archiv wurden NICHT verändert!"
echo "============================================================================"
echo ""
