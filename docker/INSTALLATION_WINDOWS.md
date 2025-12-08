# 🐳 Docker Installation - Windows Anleitung

Diese Anleitung erklärt Schritt für Schritt, wie Sie das Werkstatt-Archiv mit Docker auf Windows installieren und starten.

---

## 📋 Voraussetzungen

- Windows 10/11 (64-bit)
- Mindestens 8 GB RAM (empfohlen: 16 GB)
- Internetverbindung
- Administratorrechte

---

## 🔧 Teil 1: Docker Desktop installieren

### Option A: Mit winget (empfohlen)

1. **PowerShell als Administrator öffnen**
   - Rechtsklick auf Start-Button
   - "Windows PowerShell (Administrator)" oder "Terminal (Administrator)" wählen

2. **Docker installieren**
   ```powershell
   winget install Docker.DockerDesktop
   ```

3. **PC neu starten** (wichtig!)

### Option B: Manueller Download

1. Öffnen Sie: https://www.docker.com/products/docker-desktop/
2. Klicken Sie auf "Download for Windows"
3. Führen Sie die heruntergeladene Datei aus
4. Folgen Sie dem Installationsassistenten
5. **PC neu starten**

---

## 📦 Teil 2: Werkstatt-Archiv herunterladen

### Falls Git installiert ist:

1. **Eingabeaufforderung öffnen** (Win + R, dann `cmd` eingeben)

2. **In Dokumente-Ordner wechseln**
   ```cmd
   cd %USERPROFILE%\Documents
   ```

3. **Projekt klonen**
   ```cmd
   git clone https://github.com/SHP-ART/WerkstattArchiv-V2.git
   ```

### Falls Git NICHT installiert ist:

1. Öffnen Sie: https://github.com/SHP-ART/WerkstattArchiv-V2
2. Klicken Sie auf den grünen Button "Code" → "Download ZIP"
3. Entpacken Sie die ZIP-Datei nach `C:\Users\IHR_NAME\Documents\WerkstattArchiv-V2`

---

## 🚀 Teil 3: Docker Container starten

### Schritt 1: Docker Desktop starten

1. Starten Sie **Docker Desktop** über das Startmenü
2. Warten Sie, bis das Wal-Symbol in der Taskleiste **grün** wird (ca. 30-60 Sekunden)
3. Sie können den Status prüfen mit:
   ```cmd
   docker info
   ```
   Wenn keine Fehlermeldung kommt, ist Docker bereit.

### Schritt 2: Container bauen und starten

1. **Eingabeaufforderung öffnen**

2. **In den Docker-Ordner wechseln**
   ```cmd
   cd %USERPROFILE%\Documents\WerkstattArchiv-V2\docker
   ```

3. **Container bauen und starten**
   ```cmd
   docker-compose up -d --build
   ```
   
   Beim ersten Mal dauert dies 2-5 Minuten (Downloads + Build).

4. **Prüfen ob Container läuft**
   ```cmd
   docker ps
   ```
   Sie sollten `werkstatt-archiv` in der Liste sehen.

### Schritt 3: Web-UI öffnen

1. Öffnen Sie Ihren Browser
2. Gehen Sie zu: **http://localhost:8080**

🎉 **Fertig!** Das Werkstatt-Archiv läuft jetzt.

---

## ⚙️ Teil 4: Netzwerkpfade konfigurieren

Damit das Archiv auf Ihre Netzwerkfreigabe zugreifen kann:

### Schritt 1: Netzlaufwerk einrichten

Das Startscript verbindet automatisch ein Netzlaufwerk. Sie müssen nur die Einstellungen anpassen:

1. Öffnen Sie die Datei `docker\docker_start.bat` mit einem Texteditor (z.B. Notepad)

2. Ändern Sie Zeile 14-15:
   ```batch
   set "SERVER_PATH=\\IHR-SERVER\Freigabe"
   set "DRIVE_LETTER=W:"
   ```
   
   Beispiel:
   ```batch
   set "SERVER_PATH=\\NAS01\Werkstatt"
   set "DRIVE_LETTER=W:"
   ```

### Schritt 2: Volume-Pfade anpassen

1. Öffnen Sie die Datei `docker\docker-compose.yml` mit einem Texteditor

2. Suchen Sie den Abschnitt `volumes:` (ca. Zeile 35-50)

3. Ändern Sie die Pfade:
   ```yaml
   # VON (Standard für Entwicklung):
   - ../test_archiv:/data/archiv
   - ../test_input:/data/eingang
   - ../test_backup:/data/backup
   
   # ZU (Ihre Netzwerkpfade):
   - W:/Archiv:/data/archiv
   - W:/Eingang:/data/eingang
   - W:/Backup:/data/backup
   ```

### Schritt 3: Container neu starten

```cmd
cd %USERPROFILE%\Documents\WerkstattArchiv-V2\docker
docker-compose down
docker-compose up -d
```

---

## 🌐 Teil 5: Zugriff von anderen PCs

Der Server ist von allen PCs im Netzwerk erreichbar:

1. **IP-Adresse herausfinden** (auf dem PC mit Docker):
   ```cmd
   ipconfig
   ```
   Suchen Sie nach "IPv4-Adresse", z.B. `192.168.1.100`

2. **Von anderen PCs zugreifen**:
   ```
   http://192.168.1.100:8080
   ```

### Windows Firewall freigeben (falls nötig)

```cmd
netsh advfirewall firewall add rule name="Werkstatt-Archiv" dir=in action=allow protocol=TCP localport=8080
```

---

## 📋 Nützliche Befehle

| Aktion | Befehl |
|--------|--------|
| Container starten | `docker-compose up -d` |
| Container stoppen | `docker-compose down` |
| Container neustarten | `docker-compose restart` |
| Logs anzeigen | `docker logs werkstatt-archiv` |
| Live-Logs | `docker logs -f werkstatt-archiv` |
| Status prüfen | `docker ps` |
| Update durchführen | `git pull && docker-compose up -d --build` |

---

## 🔄 Updates installieren

### Mit Git:

```cmd
cd %USERPROFILE%\Documents\WerkstattArchiv-V2
git pull
cd docker
docker-compose up -d --build
```

### Oder mit Batch-Datei:

Doppelklick auf `docker\docker_update.bat`

---

## 🛠️ Fehlerbehebung

### "Docker is not running"

→ Docker Desktop starten und warten bis das Wal-Symbol grün ist

### "Port 8080 already in use"

→ Anderen Port verwenden. In `docker-compose.yml` ändern:
```yaml
ports:
  - "8081:8080"  # Zugriff dann über http://localhost:8081
```

### "Cannot connect to Docker daemon"

1. Docker Desktop neustarten
2. Falls das nicht hilft: PC neustarten

### Container startet, aber Web-UI lädt nicht

Logs prüfen:
```cmd
docker logs werkstatt-archiv
```

### Netzlaufwerk wird nicht verbunden

1. Prüfen Sie ob der Server erreichbar ist:
   ```cmd
   ping IHR-SERVER
   ```
2. Prüfen Sie ob die Freigabe existiert:
   ```cmd
   net view \\IHR-SERVER
   ```

### OCR funktioniert nicht

Tesseract-Status im Container prüfen:
```cmd
docker exec werkstatt-archiv tesseract --version
docker exec werkstatt-archiv tesseract --list-langs
```

---

## 📁 Ordnerstruktur

Nach der Installation:

```
WerkstattArchiv-V2\
├── docker\
│   ├── docker-compose.yml    ← Hier Pfade anpassen
│   ├── docker_start.bat      ← Hier Server-Pfad anpassen
│   ├── docker_stop.bat
│   ├── docker_update.bat
│   ├── docker_backup.bat
│   ├── docker_config.bat
│   └── Dockerfile
├── *.py                      ← Python-Code
├── templates\                ← Web-UI Templates
└── ...
```

---

## 💾 Backup erstellen

### Über Web-UI:
1. Öffnen Sie http://localhost:8080
2. Gehen Sie zu "Einstellungen"
3. Klicken Sie auf "Backup erstellen"

### Per Befehl:
```cmd
docker exec werkstatt-archiv python main.py --backup
```

### Per Batch-Datei:
Doppelklick auf `docker\docker_backup.bat`

---

## ❓ Hilfe & Support

- **GitHub Issues**: https://github.com/SHP-ART/WerkstattArchiv-V2/issues
- **Dokumentation**: Siehe `DOCKER.md` im docker-Ordner

---

## 🎉 Schnellstart (Zusammenfassung)

Nach der Docker-Installation - alle Befehle zum Kopieren:

```cmd
cd %USERPROFILE%\Documents
git clone https://github.com/SHP-ART/WerkstattArchiv-V2.git
cd WerkstattArchiv-V2\docker
docker-compose up -d --build
start http://localhost:8080
```
