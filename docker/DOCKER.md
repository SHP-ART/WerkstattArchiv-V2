# 🐳 Docker Setup für Werkstatt-Archiv

## Voraussetzungen

### Windows
1. **Docker Desktop** installieren: https://docker.com/products/docker-desktop
2. Bei der Installation **WSL 2** aktivieren (wird automatisch vorgeschlagen)
3. Nach Installation: PC **neu starten**
4. Docker Desktop starten und warten bis es "running" zeigt

### macOS
```bash
brew install --cask docker
# Oder: https://docker.com/products/docker-desktop
```

---

## 🌐 LAN-Zugriff

Der Server ist von **allen Rechnern im Netzwerk** erreichbar unter:

```
http://<SERVER-IP>:8080
```

**Server-IP herausfinden (Windows):**
```cmd
ipconfig
```
→ Suche nach "IPv4-Adresse", z.B. `192.168.1.100`

**Zugriff von anderen PCs:**
```
http://192.168.1.100:8080
```

---

## 💾 Wo wird die Datenbank gespeichert?

| Datei | Speicherort | Beschreibung |
|-------|-------------|--------------|
| `werkstatt.db` | **Im Archiv-Ordner** | Alle Aufträge, Kunden, Schlagwörter |
| `kunden_index.csv` | **Im Archiv-Ordner** | CSV-Export |
| `.archiv_config.json` | **Projekt-Ordner** | Einstellungen |

**Wichtig:** Die Datenbank liegt im **Archiv-Volume** (`/data/archiv`), das auf Ihr Netzlaufwerk gemountet ist. Sie geht beim Container-Neustart **NICHT verloren**!

---

## 📦 Backup erstellen

### Option 1: Über Web-UI (empfohlen)
1. Browser öffnen: http://localhost:8080
2. Menü → **Einstellungen**
3. Abschnitt "Backup" → **Backup erstellen**

### Option 2: Per Batch-Datei
```
docker_backup.bat
```

### Option 3: Manuell im Container
```bash
docker exec werkstatt-archiv python main.py --backup
```

### Was wird gesichert?
- `werkstatt.db` - Datenbank
- `.archiv_config.json` - Konfiguration
- `kunden_index.csv` - CSV-Export

### Backup-Speicherort
Das Backup landet im **Backup-Volume** (`/data/backup`), das Sie in `docker-compose.yml` konfiguriert haben.

---

## 🚀 Schnellstart (Windows)

### 1. Docker Desktop starten
- Doppelklick auf "Docker Desktop" im Startmenü
- Warten bis das Wal-Symbol in der Taskleiste erscheint

### 2. Netzwerkpfade konfigurieren
```
docker_config.bat
```
Oder manuell `docker-compose.yml` bearbeiten (siehe unten).

### 3. Starten
```
docker_start.bat
```
Der Browser öffnet automatisch http://localhost:8080

### 4. Stoppen
```
docker_stop.bat
```

---

## ⚙️ Konfiguration der Netzwerkpfade

### Wichtig: UNC-Pfade funktionieren NICHT direkt!

Docker unter Windows kann keine UNC-Pfade (`\\Server\Freigabe`) direkt mounten.

**Lösung:** Netzlaufwerk als Laufwerksbuchstabe verbinden:

1. Windows Explorer öffnen
2. Rechtsklick auf "Dieser PC" → "Netzlaufwerk verbinden"
3. Laufwerksbuchstabe wählen (z.B. `Z:`)
4. Ordner eingeben: `\\Server\Freigabe`
5. ✅ "Verbindung bei Anmeldung wiederherstellen" aktivieren

### docker-compose.yml anpassen

Öffnen Sie `docker-compose.yml` und ändern Sie die `volumes`:

```yaml
volumes:
  # Konfiguration (nicht ändern)
  - ./data:/app/data
  - ./.archiv_config.json:/app/.archiv_config.json
  - ./logs:/app/logs
  
  # === HIER IHRE PFADE EINTRAGEN ===
  
  # Beispiel mit Laufwerk Z:
  - Z:/Werkstatt/Archiv:/data/archiv
  - Z:/Werkstatt/Eingang:/data/eingang
  - Z:/Werkstatt/Backup:/data/backup
```

### Pfad-Format

| System | Format | Beispiel |
|--------|--------|----------|
| Windows (Laufwerk) | `X:/Pfad:/container/pfad` | `Z:/Archiv:/data/archiv` |
| macOS | `/Volumes/Name/Pfad:/container/pfad` | `/Volumes/Server/Archiv:/data/archiv` |
| Linux | `/mnt/pfad:/container/pfad` | `/mnt/nas/archiv:/data/archiv` |

---

## 🔧 Befehle

### Container-Verwaltung
```bash
# Starten (im Hintergrund)
docker-compose up -d

# Stoppen
docker-compose down

# Neu bauen und starten
docker-compose up -d --build

# Status anzeigen
docker-compose ps

# Logs anzeigen (live)
docker-compose logs -f

# In Container einloggen (für Debugging)
docker exec -it werkstatt-archiv bash
```

### Image-Verwaltung
```bash
# Image neu bauen
docker-compose build --no-cache

# Alte Images aufräumen
docker image prune -f
```

---

## 📁 Verzeichnisstruktur im Container

```
/app/                    # Anwendung
├── web_app.py
├── *.py
├── templates/
├── .archiv_config.json  # (Volume von Host)
├── data/                # (Volume von Host)
└── logs/                # (Volume von Host)

/data/                   # Daten-Volumes
├── archiv/              # → Ihr Archiv-Ordner
├── eingang/             # → Ihr Eingangs-Ordner
└── backup/              # → Ihr Backup-Ordner
```

---

## ⚠️ Wichtige Hinweise

### Config-Pfade im Container
Die Pfade in `.archiv_config.json` müssen die **Container-Pfade** verwenden:

```json
{
  "input_folder": "/data/eingang",
  "archiv_root": "/data/archiv",
  "backup_target": "/data/backup"
}
```

Beim ersten Start erstellt der Container automatisch eine passende Config.

### Windows: Laufwerk muss verbunden sein
- Das Netzlaufwerk muss **vor** dem Start von Docker verbunden sein
- Bei automatischer Verbindung: PC nach Anmeldung kurz warten

### Firewall
- Port 8080 muss in der Windows-Firewall freigegeben sein
- Docker Desktop fragt normalerweise automatisch

---

## 🐛 Troubleshooting

### "Docker is not running"
→ Docker Desktop starten und warten bis es bereit ist

### "Volume mount failed"
→ Pfad existiert nicht oder keine Berechtigung
→ Prüfen ob Netzlaufwerk verbunden ist

### "Port already in use"
→ Anderer Prozess nutzt Port 8080
→ In `docker-compose.yml` Port ändern: `"8081:8080"`

### Container startet, aber Web-UI lädt nicht
```bash
docker-compose logs werkstatt-archiv
```
→ Logs auf Fehler prüfen

### OCR funktioniert nicht
```bash
docker exec -it werkstatt-archiv tesseract --version
docker exec -it werkstatt-archiv tesseract --list-langs
```
→ Sollte `deu` (Deutsch) anzeigen

---

## 🔄 Updates

```bash
# Neuen Code holen
git pull

# Container neu bauen
docker-compose up -d --build
```

Oder auf Windows: `update.bat` ausführen, dann `docker_start.bat`
