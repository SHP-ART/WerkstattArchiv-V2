# Werkstatt-Archiv - Windows Installation & Start

## Schnellstart für Windows

### 1. Python installieren
Falls noch nicht vorhanden:
1. Download: https://www.python.org/downloads/
2. **Wichtig**: Bei Installation "Add Python to PATH" aktivieren!
3. Installation durchführen

### 2. Dependencies installieren
Öffne CMD oder PowerShell im Projekt-Ordner:
```cmd
pip install -r requirements.txt
```

Oder manuell:
```cmd
pip install flask pdf2image pillow pytesseract watchdog pyyaml
```

### 3. Tesseract OCR installieren
1. Download: https://github.com/UB-Mannheim/tesseract/wiki
2. Installer ausführen (empfohlen: C:\Program Files\Tesseract-OCR)
3. Tesseract zur PATH hinzufügen oder in Config eintragen

### 4. Server starten

**Option 1: Doppelklick auf Start-Script (empfohlen)**
- Doppelklick auf `start_server.bat`
- Oder: Rechtsklick → "Als Administrator ausführen" (falls Port-Probleme)

**Option 2: CMD/PowerShell**
```cmd
start_server.bat
```

**Option 3: PowerShell (mit mehr Features)**
```powershell
.\start_server.ps1
```

**Option 4: Manuell**
```cmd
python web_app.py --port 8080 --threaded
```

## Zugriff auf Web-UI

Nach dem Start öffne im Browser:
- http://127.0.0.1:8080

## Konfiguration

### Tesseract Pfad einstellen
Wenn Tesseract nicht automatisch gefunden wird:

1. Erstelle/Bearbeite `.archiv_config.json`
2. Füge hinzu:
```json
{
  "tesseract_cmd": "C:\\Program Files\\Tesseract-OCR\\tesseract.exe"
}
```

### Netzwerkpfade
Windows-UNC-Pfade werden unterstützt:
```json
{
  "input_folder": "\\\\SERVER\\Scans\\Eingang",
  "archiv_root": "\\\\SERVER\\Werkstatt\\Archiv",
  "backup_target_dir": "\\\\SERVER\\Backups"
}
```

## Problemlösung

### "Python nicht gefunden"
- Python ist nicht installiert oder nicht im PATH
- Lösung: Python neu installieren mit "Add to PATH" Option

### "Flask nicht gefunden"
```cmd
pip install flask
```

### "Port 8080 bereits belegt"
1. Finde Prozess:
```cmd
netstat -ano | findstr ":8080"
```
2. Beende Prozess (PID aus obigem Befehl):
```cmd
taskkill /F /PID <PID-Nummer>
```

### "Tesseract nicht gefunden"
1. Installiere Tesseract von: https://github.com/UB-Mannheim/tesseract/wiki
2. Oder setze Pfad in Config (siehe oben)

### Server hängt beim Start
- Drücke Strg+C zum Abbrechen
- Starte neu mit:
```cmd
python web_app.py --port 8080 --threaded --debug
```
- Prüfe Logs auf Fehlermeldungen

### Firewall blockiert
Windows Firewall kann nachfragen:
- Erlaube Zugriff für "Privates Netzwerk"
- Oder: Firewall-Regel manuell erstellen für Port 8080

## Autostart (optional)

### Als Windows-Dienst
1. Installiere NSSM: https://nssm.cc/
2. Öffne CMD als Administrator:
```cmd
nssm install WerkstattArchiv "C:\Python\python.exe" "C:\Pfad\zum\web_app.py --port 8080"
nssm start WerkstattArchiv
```

### Task-Scheduler
1. Öffne "Aufgabenplanung"
2. "Einfache Aufgabe erstellen"
3. Trigger: "Bei Anmeldung"
4. Aktion: `start_server.bat` ausführen

## Performance-Tipps für Windows

### 1. Windows Defender Ausnahmen
Füge Ausnahmen hinzu für schnelleren Zugriff:
- Projekt-Ordner
- Archiv-Ordner
- Python-Installation

**Einstellungen → Update & Sicherheit → Windows-Sicherheit → Viren- & Bedrohungsschutz → Ausschlüsse verwalten**

### 2. Netzwerklaufwerke
Mappe UNC-Pfade als Laufwerk für bessere Performance:
```cmd
net use Z: \\SERVER\Werkstatt /persistent:yes
```

### 3. SSD verwenden
Datenbank und Archiv auf SSD speichern für maximale Geschwindigkeit.

## Updates

```cmd
# Dependencies aktualisieren
pip install --upgrade -r requirements.txt

# Oder einzeln
pip install --upgrade flask
```

## Weitere Hilfe

- Hauptdokumentation: siehe README.md
- Server-Details: siehe WEB_SERVER.md
- GitHub Issues: [Link zu Repository]
