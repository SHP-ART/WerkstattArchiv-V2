#!/bin/bash
################################################################################
# Werkstatt-Archiv Web-Server Start-Script
# Mit detailliertem Logging und Fortschrittsanzeige
################################################################################

# Farben für Terminal-Output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Konfiguration
PORT=8080
LOG_DIR="logs"
LOG_FILE="$LOG_DIR/server.log"
STARTUP_LOG="$LOG_DIR/startup.log"
PID_FILE="$LOG_DIR/server.pid"

echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  Werkstatt-Archiv Web-Server Startvorgang${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
echo ""

# Schritt 1: Log-Verzeichnis erstellen
echo -e "${YELLOW}[1/8]${NC} Erstelle Log-Verzeichnis..."
mkdir -p "$LOG_DIR"
echo "$(date '+%Y-%m-%d %H:%M:%S') - Start-Script gestartet" > "$STARTUP_LOG"
echo -e "${GREEN}✓${NC} Log-Verzeichnis bereit: $LOG_DIR"
echo ""

# Schritt 2: Alte Prozesse beenden
echo -e "${YELLOW}[2/8]${NC} Prüfe auf laufende Server-Prozesse..."
OLD_PIDS=$(lsof -ti :$PORT 2>/dev/null)
if [ -n "$OLD_PIDS" ]; then
    echo -e "${YELLOW}⚠${NC}  Port $PORT ist belegt (PIDs: $OLD_PIDS)"
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Beende alte Prozesse: $OLD_PIDS" >> "$STARTUP_LOG"
    kill -9 $OLD_PIDS 2>/dev/null
    sleep 2
    echo -e "${GREEN}✓${NC} Alte Prozesse beendet"
else
    echo -e "${GREEN}✓${NC} Port $PORT ist frei"
fi
echo ""

# Schritt 3: Python-Version prüfen
echo -e "${YELLOW}[3/8]${NC} Prüfe Python-Installation..."
PYTHON_VERSION=$(python3 --version 2>&1)
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓${NC} $PYTHON_VERSION"
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Python-Version: $PYTHON_VERSION" >> "$STARTUP_LOG"
else
    echo -e "${RED}✗${NC} Python3 nicht gefunden!"
    echo "$(date '+%Y-%m-%d %H:%M:%S') - FEHLER: Python3 nicht gefunden" >> "$STARTUP_LOG"
    exit 1
fi
echo ""

# Schritt 4: Abhängigkeiten prüfen
echo -e "${YELLOW}[4/8]${NC} Prüfe Python-Abhängigkeiten..."
echo "$(date '+%Y-%m-%d %H:%M:%S') - Prüfe Dependencies..." >> "$STARTUP_LOG"

MISSING_DEPS=()
for pkg in flask waitress pytesseract; do
    python3 -c "import $pkg" 2>/dev/null
    if [ $? -ne 0 ]; then
        MISSING_DEPS+=($pkg)
    fi
done

if [ ${#MISSING_DEPS[@]} -gt 0 ]; then
    echo -e "${RED}✗${NC} Fehlende Pakete: ${MISSING_DEPS[*]}"
    echo -e "${YELLOW}→${NC} Installiere mit: pip3 install ${MISSING_DEPS[*]}"
    echo "$(date '+%Y-%m-%d %H:%M:%S') - FEHLER: Fehlende Pakete: ${MISSING_DEPS[*]}" >> "$STARTUP_LOG"
    exit 1
else
    echo -e "${GREEN}✓${NC} Alle Abhängigkeiten installiert"
fi
echo ""

# Schritt 5: Konfiguration prüfen
echo -e "${YELLOW}[5/8]${NC} Prüfe Konfiguration..."
if [ -f ".archiv_config.json" ]; then
    echo -e "${GREEN}✓${NC} Konfigurationsdatei gefunden: .archiv_config.json"
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Config: .archiv_config.json" >> "$STARTUP_LOG"
elif [ -f ".archiv_config.yaml" ]; then
    echo -e "${GREEN}✓${NC} Konfigurationsdatei gefunden: .archiv_config.yaml"
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Config: .archiv_config.yaml" >> "$STARTUP_LOG"
else
    echo -e "${YELLOW}⚠${NC}  Keine Konfiguration gefunden (wird beim ersten Start erstellt)"
    echo "$(date '+%Y-%m-%d %H:%M:%S') - WARNING: Keine Config gefunden" >> "$STARTUP_LOG"
fi
echo ""

# Schritt 6: Syntax-Check
echo -e "${YELLOW}[6/8]${NC} Prüfe Python-Syntax..."
echo "$(date '+%Y-%m-%d %H:%M:%S') - Syntax-Check..." >> "$STARTUP_LOG"
python3 -m py_compile web_app.py 2>> "$STARTUP_LOG"
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓${NC} Syntax OK"
else
    echo -e "${RED}✗${NC} Syntax-Fehler!"
    exit 1
fi
echo ""

# Schritt 7: Server starten
echo -e "${YELLOW}[7/8]${NC} Starte Web-Server..."
echo "$(date '+%Y-%m-%d %H:%M:%S') - Starte Server..." >> "$STARTUP_LOG"

nohup python3 -u web_app.py --port $PORT > "$LOG_FILE" 2>&1 &
SERVER_PID=$!
echo $SERVER_PID > "$PID_FILE"

echo -e "${GREEN}✓${NC} Server gestartet (PID: $SERVER_PID)"
echo ""

# Schritt 8: Warte auf Server-Bereitschaft
echo -e "${YELLOW}[8/8]${NC} Warte auf Server-Bereitschaft..."
echo -e "${BLUE}→${NC} Live-Log von: $LOG_FILE"
echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"

MAX_WAIT=30
COUNTER=0
SERVER_READY=false
LAST_LINE=""

while [ $COUNTER -lt $MAX_WAIT ]; do
    # Prüfe ob Prozess noch läuft
    if ! kill -0 $SERVER_PID 2>/dev/null; then
        echo ""
        echo -e "${RED}✗ Server-Prozess abgestürzt!${NC}"
        echo ""
        echo -e "${RED}═══ FEHLER-LOG ═══${NC}"
        tail -20 "$LOG_FILE"
        echo -e "${RED}══════════════════${NC}"
        exit 1
    fi
    
    # Zeige alle neuen Log-Zeilen
    if [ -f "$LOG_FILE" ]; then
        # Zeige die letzten 5 Zeilen live
        NEW_LINES=$(tail -5 "$LOG_FILE" 2>/dev/null)
        if [ "$NEW_LINES" != "$LAST_LINE" ]; then
            # Nur neue Zeilen anzeigen
            echo "$NEW_LINES" | while IFS= read -r line; do
                if [ -n "$line" ]; then
                    # Färbe nach Log-Level
                    if echo "$line" | grep -q "ERROR"; then
                        echo -e "${RED}│${NC} $line"
                    elif echo "$line" | grep -q "WARNING"; then
                        echo -e "${YELLOW}│${NC} $line"
                    elif echo "$line" | grep -q "INFO"; then
                        echo -e "${GREEN}│${NC} $line"
                    else
                        echo -e "${BLUE}│${NC} $line"
                    fi
                fi
            done
            LAST_LINE="$NEW_LINES"
        fi
    fi
    
    # Prüfe HTTP-Verfügbarkeit
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:$PORT/ 2>/dev/null)
    if [ "$HTTP_CODE" = "200" ]; then
        SERVER_READY=true
        break
    fi
    
    sleep 1
    COUNTER=$((COUNTER + 1))
done

echo ""

if [ "$SERVER_READY" = true ]; then
    echo -e "${GREEN}════════════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}  ✓ SERVER ERFOLGREICH GESTARTET!${NC}"
    echo -e "${GREEN}════════════════════════════════════════════════════════════════${NC}"
    echo ""
    echo -e "  ${BLUE}URL:${NC}      http://127.0.0.1:$PORT"
    echo -e "  ${BLUE}PID:${NC}      $SERVER_PID"
    echo -e "  ${BLUE}Logs:${NC}     tail -f $LOG_FILE"
    echo ""
else
    echo -e "${RED}✗ SERVER-START FEHLGESCHLAGEN${NC}"
    echo ""
    tail -30 "$LOG_FILE"
    kill $SERVER_PID 2>/dev/null
    exit 1
fi
