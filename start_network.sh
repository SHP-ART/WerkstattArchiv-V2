#!/bin/bash
# ============================================================
# Server-Start - Erreichbar im Netzwerk (macOS/Linux)
# ============================================================

echo ""
echo "============================================================"
echo "  Werkstatt-Archiv - Netzwerk-Modus"
echo "============================================================"
echo ""

# Wechsle ins Script-Verzeichnis
cd "$(dirname "$0")"

# Virtual Environment aktivieren
if [ -f ".venv/bin/activate" ]; then
    echo "[*] Aktiviere Virtual Environment..."
    source .venv/bin/activate
else
    echo "[FEHLER] Virtual Environment nicht gefunden!"
    echo "Bitte führen Sie install.sh aus."
    exit 1
fi

# Port prüfen
echo "[*] Prüfe Port 8080..."
if lsof -ti :8080 >/dev/null 2>&1; then
    echo "[WARNUNG] Port 8080 ist bereits belegt!"
    lsof -ti :8080 | xargs kill -9 2>/dev/null
    sleep 2
fi
echo "[OK] Port 8080 ist frei"
echo ""

# Ermittle lokale IP-Adresse
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    LOCAL_IP=$(ipconfig getifaddr en0 2>/dev/null || ipconfig getifaddr en1 2>/dev/null || echo "IP nicht gefunden")
else
    # Linux
    LOCAL_IP=$(hostname -I | awk '{print $1}')
fi

echo "============================================================"
echo "  Server wird im Netzwerk-Modus gestartet"
echo "============================================================"
echo ""
echo "[INFO] Server ist erreichbar unter:"
echo ""
echo "  Lokal:     http://127.0.0.1:8080"
echo "  Netzwerk:  http://${LOCAL_IP}:8080"
echo ""
echo "[WICHTIG] Firewall-Einstellungen prüfen!"
echo ""
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "macOS Firewall:"
    echo "  Systemeinstellungen -> Netzwerk -> Firewall"
    echo "  Python den Zugriff erlauben"
else
    echo "Linux Firewall (ufw):"
    echo "  sudo ufw allow 8080/tcp"
fi
echo ""
echo "============================================================"
echo ""
echo "Zum Beenden: Strg+C"
echo ""

python3 web_app.py --host 0.0.0.0 --port 8080
