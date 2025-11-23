#!/bin/bash
# Einfaches Start-Script ohne venv

echo "========================================"
echo "Werkstatt-Archiv Web-Server (System Python)"
echo "========================================"

# Alte Prozesse beenden
pkill -f "web_app.py" 2>/dev/null
sleep 1

# Server starten
echo "Starte Server auf http://127.0.0.1:8080 ..."
python3 web_app.py --port 8080

echo "Server wurde beendet."
