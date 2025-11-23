# Server Starten - OHNE venv

Die App ist jetzt so konfiguriert, dass sie **systemweites Python** verwendet.

## Methode 1: Doppelklick (macOS)

Doppelklicke einfach auf diese Datei:

```
run_server.command
```

Ein Terminal-Fenster öffnet sich und der Server startet.

## Methode 2: Terminal

Öffne ein Terminal im Projektordner und führe aus:

```bash
./start_simple.sh
```

ODER direkt:

```bash
python3 web_app.py --port 8080
```

## Zugriff auf die Web-App

Nach dem Start öffne deinen Browser und gehe zu:

**http://127.0.0.1:8080**

## Server stoppen

Drücke `Ctrl+C` im Terminal.

## Fehlerbehebung

### Falls Flask fehlt:

```bash
python3 -m pip install flask werkzeug waitress PyYAML python-dateutil
```

### Falls Port 8080 belegt ist:

```bash
python3 web_app.py --port 8090
```

Dann öffne: http://127.0.0.1:8090

### Falls der Server nicht startet:

```bash
# Alte Prozesse beenden
pkill -f "web_app.py"

# Neu starten
python3 web_app.py --port 8080
```

## Performance-Optimierungen

Die App wurde optimiert:
- ✅ API-Caching (5 Sekunden)
- ✅ Reduzierte Polling-Intervalle
- ✅ Async CDN-Loading
- ✅ 60% weniger Server-Requests

Details: siehe `PERFORMANCE_OPTIMIERUNGEN.md`
