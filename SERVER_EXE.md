# 🚀 Schnellstart: Server.exe erstellen

## Für Eilige

```batch
build_server.bat
```

Das war's! Die `WerkstattArchiv-Server.exe` findest du im `dist/` Ordner.

## Was wird erstellt?

Eine eigenständige ausführbare Datei, die:
- ✅ Als Web-Server im Netzwerk läuft (Port 8080)
- ✅ Von mehreren PCs gleichzeitig nutzbar ist (Relais-Funktion)
- ✅ Kein Python auf dem Ziel-PC benötigt
- ✅ Einfach zu deployen ist

## Deployment (3 Schritte)

### 1. Build erstellen (auf Entwicklungs-PC)
```batch
build_server.bat
```
→ Erstellt `dist\WerkstattArchiv-Server.exe`

### 2. Dateien kopieren (auf Server-PC)
```
Server-PC/
├── WerkstattArchiv-Server.exe
└── .archiv_config.json
```

### 3. Server starten
```batch
WerkstattArchiv-Server.exe
```

Browser öffnen: `http://localhost:8080`

## Netzwerk-Zugriff

**Von anderen PCs im LAN:**

1. Server-IP herausfinden:
   ```batch
   ipconfig
   ```
   Suche "IPv4-Adresse", z.B. `192.168.1.100`

2. Firewall-Regel hinzufügen:
   ```batch
   netsh advfirewall firewall add rule name="Werkstatt-Archiv" dir=in action=allow protocol=TCP localport=8080
   ```

3. Von Client-PCs zugreifen:
   ```
   http://192.168.1.100:8080
   ```

## Voraussetzungen auf Server-PC

Die EXE braucht **keine Python-Installation**, aber:

1. **Tesseract OCR** muss installiert sein
   ```batch
   install_tesseract.bat
   ```

2. **Poppler** muss installiert sein
   ```batch
   install_poppler.bat
   ```

3. **.archiv_config.json** muss im gleichen Ordner liegen

## Konfiguration

Minimale `.archiv_config.json`:

```json
{
  "input_folder": "C:\\Werkstatt\\Eingang",
  "archiv_root": "C:\\Werkstatt\\Archiv",
  "tesseract_cmd": "C:\\Program Files\\Tesseract-OCR\\tesseract.exe",
  "poppler_path": "C:\\Program Files\\poppler\\Library\\bin"
}
```

**Wichtig:** Doppelte Backslashes `\\` in JSON!

## Automatischer Start (Windows)

### Option 1: Autostart-Ordner

1. Erstelle `start_server.bat`:
   ```batch
   @echo off
   cd /d "%~dp0"
   WerkstattArchiv-Server.exe
   ```

2. Verknüpfung in Autostart:
   - `Win + R` → `shell:startup`
   - Verknüpfung zu `start_server.bat` erstellen

### Option 2: Windows-Dienst (mit NSSM)

```batch
# NSSM herunterladen: https://nssm.cc/download
nssm install WerkstattArchiv "C:\Pfad\WerkstattArchiv-Server.exe"
nssm start WerkstattArchiv
```

## Troubleshooting

### Build schlägt fehl
```batch
# Dependencies neu installieren
.venv\Scripts\activate
pip install -r requirements.txt
pyinstaller --clean server.spec
```

### Server startet nicht
```
[FEHLER] Port bereits belegt
```
→ Anderes Programm nutzt Port 8080. Ändere Port in `server.py` (Zeile 44)

### OCR funktioniert nicht
1. Teste Tesseract: `diagnose_tesseract.bat`
2. Teste Poppler: `diagnose_poppler.bat`
3. Prüfe Pfade in `.archiv_config.json`

### Keine Netzwerk-Verbindung
1. Firewall-Regel erstellen (siehe oben)
2. Prüfe IP-Adresse mit `ipconfig`
3. Teste lokal: `http://localhost:8080`

## Weitere Dokumentation

- **Vollständige Anleitung:** [SERVER_DEPLOYMENT.md](SERVER_DEPLOYMENT.md)
- **Poppler-Installation:** [POPPLER_INSTALLATION.md](POPPLER_INSTALLATION.md)
- **Allgemeine Doku:** [README.md](README.md)

## Build-Parameter anpassen

Bearbeite `server.spec` für:
- Icon ändern (Zeile 116)
- Eingebettete Templates (Zeilen 13-16)
- Ausschluss-Liste (Zeilen 60-68)

## Alternative: Docker

Falls Build-Probleme auftreten:
```batch
cd docker
docker_install.bat
docker_start.bat
```

Docker erstellt einen Container mit allem vorkonfiguriert.
