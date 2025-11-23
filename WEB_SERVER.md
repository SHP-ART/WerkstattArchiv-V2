# Werkstatt-Archiv Web-Server

## Schnellstart

### Einfacher Start (empfohlen)

**Linux/macOS:**
```bash
./start_server.sh
```

**Windows (CMD):**
```cmd
start_server.bat
```

**Windows (PowerShell):**
```powershell
.\start_server.ps1
```

Das Script prüft automatisch:
- ✓ Python Installation
- ✓ Alle Dependencies
- ✓ Ob Port bereits belegt ist
- ✓ Startet Server mit optimalen Einstellungen

### Manueller Start

**Linux/macOS:**
```bash
python3 web_app.py --port 8080 --threaded
```

**Windows:**
```cmd
python web_app.py --port 8080 --threaded
```

## Performance-Optimierungen

Die Web-UI wurde optimiert für:

### 1. Schnellerer Server-Start
- **Threaded-Modus aktiviert**: Mehrere Requests parallel
- **Kein Auto-Reload**: Verhindert doppelten Start
- **Optimierte Imports**: Logging vor allen Imports

### 2. Frontend-Performance
- **CDN Preconnect**: Schnelleres Laden von Bootstrap/Icons
- **Deferred JS**: JavaScript blockiert nicht das Rendering
- **Cache-Headers**: 1 Jahr Cache für statische Dateien
- **Komprimierung**: Automatische Gzip-Komprimierung

### 3. Datenbank-Optimierungen
- **Indizes**: Auf allen Suchfeldern
- **Connection Pooling**: Wiederverwendung von DB-Connections
- **Prepared Statements**: Schnellere Queries

## Server-Optionen

```bash
python3 web_app.py [OPTIONEN]

Optionen:
  --host HOST       Host-Adresse (Standard: 127.0.0.1)
  --port PORT       Port (Standard: 5000)
  --threaded        Threaded-Modus aktivieren (Standard: aktiviert)
  --debug           Debug-Modus für Entwicklung
```

## Zugriff

Nach dem Start ist die Web-UI erreichbar unter:
- **Lokal**: http://127.0.0.1:8080
- **Dashboard**: http://127.0.0.1:8080/
- **Suche**: http://127.0.0.1:8080/search
- **Archiv**: http://127.0.0.1:8080/archive
- **Einstellungen**: http://127.0.0.1:8080/settings

## Produktion

**Wichtig**: Der integrierte Flask-Server ist für Entwicklung gedacht!

Für Produktions-Einsatz empfohlen:

### Option 1: Waitress (empfohlen für Windows/Mac)
```bash
pip3 install waitress
waitress-serve --host=127.0.0.1 --port=8080 --threads=4 web_app:app
```

### Option 2: Gunicorn (empfohlen für Linux)
```bash
pip3 install gunicorn
gunicorn --bind 127.0.0.1:8080 --workers 2 --threads 4 web_app:app
```

### Option 3: Docker (für alle Plattformen)
```bash
# Dockerfile wird noch erstellt
docker build -t werkstatt-archiv .
docker run -p 8080:8080 werkstatt-archiv
```

## Troubleshooting

### Server startet nicht

**Linux/macOS:**
```bash
# Prüfe ob Port belegt ist
lsof -i :8080

# Beende alten Prozess
pkill -f "web_app.py"
```

**Windows (CMD):**
```cmd
# Prüfe ob Port belegt ist
netstat -ano | findstr ":8080"

# Beende Prozess (PID aus obigem Befehl)
taskkill /F /PID <PID>
```

**Windows (PowerShell):**
```powershell
# Prüfe ob Port belegt ist
Get-NetTCPConnection -LocalPort 8080

# Beende Prozess
Get-Process python | Where-Object {$_.MainWindowTitle -like "*web_app*"} | Stop-Process
```

### Langsame Performance
1. Stelle sicher dass Threaded-Modus aktiviert ist
2. Prüfe Datenbank-Größe (große DBs langsamer)
3. Verwende Produktions-Server (siehe oben)
4. Aktiviere Browser-Cache

### Logs prüfen
```bash
# Server mit Logging starten
python3 web_app.py --port 8080 --debug 2>&1 | tee server.log
```

## Performance-Benchmarks

Gemessen mit 14 Aufträgen in Test-DB:

| Operation | Zeit (Development) | Zeit (Production) |
|-----------|-------------------|-------------------|
| Server-Start | ~1s | ~0.3s |
| Dashboard-Laden | ~100ms | ~50ms |
| Suche (einfach) | ~50ms | ~20ms |
| Suche (multi) | ~80ms | ~30ms |
| PDF-Download | ~200ms | ~100ms |

*Production = Waitress mit 4 Threads*

## Weitere Informationen

- Konfiguration: `.archiv_config.json`
- Logs: Werden auf Console ausgegeben
- Datenbank: `werkstatt.db` im Archiv-Root
