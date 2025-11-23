# Server starten

## Schnellstart

Öffne ein Terminal im Projekt-Verzeichnis und führe aus:

```bash
./start_server.sh
```

**ODER** manuell:

```bash
.venv/bin/python web_app.py --port 8080
```

## Zugriff

Nach dem Start ist die Web-App erreichbar unter:

**http://127.0.0.1:8080**

## Server stoppen

Drücke `Ctrl+C` im Terminal, um den Server zu beenden.

## Fehlerbehebung

### Port bereits belegt

Wenn Port 8080 bereits belegt ist:

```bash
# Anderen Port verwenden
.venv/bin/python web_app.py --port 8090
```

### Prozess hängt

Falls der Server nicht antwortet:

```bash
# Alle Python-Prozesse beenden
pkill -f "web_app.py"

# Neu starten
.venv/bin/python web_app.py --port 8080
```

### Dependencies fehlen

Wenn Fehler bei den Dependencies auftreten:

```bash
.venv/bin/pip install -r requirements.txt
```

## Debug-Modus

Für Entwicklung mit ausführlichem Logging:

```bash
.venv/bin/python web_app.py --port 8080 --debug
```

## Performance

Die App wurde mit folgenden Optimierungen ausgestattet:

- 5-Sekunden-Cache für API-Responses
- Reduzierte Polling-Intervalle (10s statt 3s)
- Async-Loading für CDN-Ressourcen
- Globale SQLite-Imports

Details siehe: `PERFORMANCE_OPTIMIERUNGEN.md`
