# Werkstatt-Archiv Server - Standalone Deployment

Dieser Guide erklärt, wie du den Werkstatt-Archiv Web-Server als eigenständige ausführbare Datei (`.exe` für Windows) erstellst und auf anderen PCs deployest.

## Vorteile der Server.exe

- ✅ **Kein Python erforderlich** auf dem Ziel-PC
- ✅ **Einfaches Deployment** - nur eine .exe-Datei
- ✅ **Netzwerk-Zugriff** - Server ist im LAN erreichbar
- ✅ **Relais-Funktion** - Zentrale Instanz für mehrere Clients
- ✅ **Portable** - läuft ohne Installation

## Build-Prozess (auf Entwicklungs-PC)

### Windows

```batch
build_server.bat
```

**Was passiert:**
1. Virtual Environment wird erstellt (falls nicht vorhanden)
2. PyInstaller wird installiert
3. Alle Abhängigkeiten werden installiert
4. Server.exe wird gebaut (in `dist/` Ordner)

**Dauer:** Ca. 2-5 Minuten (abhängig von PC-Leistung)

### macOS/Linux

```bash
chmod +x build_server.sh
./build_server.sh
```

## Deployment auf Ziel-PC

### Schritt 1: Dateien kopieren

Kopiere folgende Dateien auf den Ziel-PC (z.B. Server-PC):

```
DeploymentOrdner/
├── WerkstattArchiv-Server.exe      # Hauptprogramm
├── .archiv_config.json             # Konfiguration
├── templates/                      # HTML-Templates (optional, falls nicht eingebettet)
│   ├── base.html
│   ├── index.html
│   └── ...
└── Logo/                          # Logo-Dateien (optional)
    └── ...
```

**Hinweis:** Wenn templates/Logo nicht kopiert werden, werden sie aus der EXE extrahiert.

### Schritt 2: Tesseract & Poppler installieren

**Auf dem Ziel-PC müssen installiert sein:**

1. **Tesseract OCR**
   ```batch
   install_tesseract.bat
   ```
   Oder manuell: https://github.com/UB-Mannheim/tesseract/wiki

2. **Poppler**
   ```batch
   install_poppler.bat
   ```
   Oder manuell: Siehe [POPPLER_INSTALLATION.md](POPPLER_INSTALLATION.md)

### Schritt 3: Konfiguration anpassen

Bearbeite `.archiv_config.json` auf dem Ziel-PC:

```json
{
  "input_folder": "C:\\Werkstatt\\Eingang",
  "archiv_root": "C:\\Werkstatt\\Archiv",
  "backup_target_dir": "C:\\Werkstatt\\Backups",
  
  "network_archiv_path": "\\\\Server\\Werkstatt\\Archiv",
  "network_input_path": "\\\\Server\\Werkstatt\\Eingang",
  
  "tesseract_cmd": "C:\\Program Files\\Tesseract-OCR\\tesseract.exe",
  "poppler_path": "C:\\Program Files\\poppler\\Library\\bin"
}
```

**Wichtig:**
- Verwende absolute Pfade
- Doppelte Backslashes `\\` in JSON
- Netzwerkpfade für "Ordner öffnen"-Funktion

### Schritt 4: Server starten

**Manueller Start:**
```batch
WerkstattArchiv-Server.exe
```

**Als Windows-Dienst (automatischer Start):**

1. Erstelle `start_server.bat` im gleichen Ordner:
   ```batch
   @echo off
   cd /d "%~dp0"
   WerkstattArchiv-Server.exe
   pause
   ```

2. Verknüpfung im Autostart-Ordner:
   - Drücke `Win + R` → `shell:startup`
   - Erstelle Verknüpfung zu `start_server.bat`

**Mit NSSM (empfohlen für Production):**

```batch
# NSSM installieren: https://nssm.cc/download
nssm install WerkstattArchiv "C:\Pfad\WerkstattArchiv-Server.exe"
nssm set WerkstattArchiv AppDirectory "C:\Pfad"
nssm start WerkstattArchiv
```

## Zugriff auf den Server

### Vom Server-PC selbst:
```
http://localhost:8080
http://127.0.0.1:8080
```

### Von anderen PCs im Netzwerk:
```
http://<SERVER-IP>:8080
```

**Server-IP herausfinden:**
```batch
ipconfig
# Suche nach "IPv4-Adresse", z.B. 192.168.1.100
```

Dann von Client-PCs:
```
http://192.168.1.100:8080
```

### Firewall-Regel (Windows)

Falls der Zugriff aus dem Netzwerk nicht funktioniert:

```batch
# Als Administrator ausführen:
netsh advfirewall firewall add rule name="Werkstatt-Archiv Server" dir=in action=allow protocol=TCP localport=8080
```

Oder in Windows Firewall GUI:
1. Windows-Suche: "Windows Defender Firewall"
2. "Erweiterte Einstellungen"
3. "Eingehende Regeln" → "Neue Regel"
4. Port: TCP 8080

## Troubleshooting

### "Port bereits belegt"
```
[ERROR] Address already in use
```

**Lösung:**
- Anderes Programm nutzt Port 8080
- Prüfen: `netstat -ano | findstr :8080`
- Port ändern in `server.py` (Zeile 44)

### "Tesseract nicht gefunden"
```
[ERROR] Tesseract ist nicht installiert
```

**Lösung:**
1. Tesseract installieren: `install_tesseract.bat`
2. Pfad in Config setzen: `"tesseract_cmd": "C:\\Program Files\\Tesseract-OCR\\tesseract.exe"`
3. Testen: `diagnose_tesseract.bat`

### "Poppler nicht gefunden"
```
[ERROR] Unable to get page count. Is poppler installed and in PATH?
```

**Lösung:**
1. Poppler installieren: `install_poppler.bat`
2. Pfad in Config setzen: `"poppler_path": "C:\\Program Files\\poppler\\Library\\bin"`
3. Testen: `diagnose_poppler.bat`

### Server läuft, aber keine Verbindung möglich

**Prüfe:**
1. Ist Server wirklich gestartet? (Console-Fenster offen?)
2. Firewall blockiert Port 8080? (siehe oben)
3. Richtige IP-Adresse verwendet?
4. Client-PC im gleichen Netzwerk?

### Templates nicht gefunden

```
[ERROR] Template not found: index.html
```

**Lösung:**
- Kopiere `templates/` Ordner in den gleichen Ordner wie die .exe
- Oder: Rebuild mit `--onefile` in server.spec

## Performance-Optimierung

### Für lokalen Server (nur ein PC):
```python
# In server.py, Zeile 44:
host = 'localhost'  # Statt '0.0.0.0'
```

### Für Produktions-Server:
- Verwende `waitress` (bereits in requirements.txt)
- Erhöhe Thread-Anzahl: `threads=10` (Zeile 67 in server.py)
- SSD für Archiv verwenden
- Regelmäßige Backups aktivieren

## Updates

**Neuen Build erstellen:**
1. Auf Entwicklungs-PC: Code aktualisieren
2. `build_server.bat` erneut ausführen
3. Neue `WerkstattArchiv-Server.exe` auf Server kopieren
4. Server neu starten

**Konfiguration bleibt erhalten:**
- `.archiv_config.json` nicht überschreiben
- Datenbank (`werkstatt.db`) nicht überschreiben

## Docker Alternative

Falls der EXE-Build Probleme macht, verwende Docker:

```batch
cd docker
docker_install.bat
docker_start.bat
```

Siehe [docker/DOCKER.md](docker/DOCKER.md)

## Support

Bei Problemen:
1. Prüfe Console-Output (Fehlermeldungen)
2. Teste Tesseract: `diagnose_tesseract.bat`
3. Teste Poppler: `diagnose_poppler.bat`
4. Prüfe Logs: Suche nach `.log` Dateien im Programmordner
5. GitHub Issues: https://github.com/SHP-ART/WerkstattArchiv-V2/issues
