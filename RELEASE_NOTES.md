# Release Notes - Werkstatt-Archiv Server v1.0

## 📦 Release-Paket

Download des kompletten `dist/` Ordners als ZIP für einfaches Deployment.

### Enthaltene Dateien

| Datei | Größe | Beschreibung |
|-------|-------|--------------|
| `WerkstattArchiv-Server.exe` | ~20 MB | Standalone-Server (keine Python-Installation nötig) |
| `start_server.bat` | 2 KB | Server-Starter mit Fehleranzeige |
| `.archiv_config.json` | 1 KB | Beispiel-Konfiguration (muss angepasst werden) |
| `install_tesseract.bat` | 5 KB | **Automatische Tesseract-Installation** |
| `install_poppler.bat` | 4 KB | **Automatische Poppler-Installation** |
| `diagnose_tesseract.bat` | 4 KB | Tesseract-Diagnose-Tool |
| `diagnose_poppler.bat` | 3 KB | Poppler-Diagnose-Tool |
| `README_SERVER.md` | 6 KB | Vollständige Installations- und Konfigurations-Anleitung |

## ⚡ Installation in 4 Schritten

### 1️⃣ Download & Entpacken
```
1. Lade dist.zip herunter
2. Entpacke nach: C:\WerkstattArchiv\
```

### 2️⃣ Tesseract installieren
```
Doppelklick auf: install_tesseract.bat
→ Wähle Option 1 (Automatisch)
→ Warte auf Installation
→ Prüfe mit: diagnose_tesseract.bat
```

### 3️⃣ Poppler installieren
```
Doppelklick auf: install_poppler.bat
→ Wähle Option 1 (Automatisch)
→ Fertig!
→ Prüfe mit: diagnose_poppler.bat
```

### 4️⃣ Konfiguration anpassen
```
Bearbeite .archiv_config.json:
- Netzwerkpfade eintragen (mit \\ statt \)
- Pfade zu Tesseract und Poppler prüfen
```

### 5️⃣ Server starten
```
Doppelklick auf: start_server.bat
→ Server läuft auf http://0.0.0.0:8080
```

## 🌐 Netzwerk-Zugriff

**Von Client-PCs:**
```
http://<SERVER-IP>:8080
```

**Beispiel:**
```
http://192.168.1.100:8080
```

## 🔧 Systemanforderungen

| Komponente | Minimum | Empfohlen |
|------------|---------|-----------|
| **Windows** | Windows 10 | Windows 11 |
| **RAM** | 2 GB | 4 GB+ |
| **Festplatte** | 100 MB (EXE) + Archiv-Größe | SSD empfohlen |
| **Prozessor** | Dual-Core | Quad-Core+ |
| **Netzwerk** | 100 Mbit/s | 1 Gbit/s |

**Hinweis:** Python ist **NICHT** erforderlich! Die EXE enthält alles Notwendige.

## 🔑 Features

✅ Standalone-EXE (kein Python nötig)  
✅ Automatische Tesseract/Poppler-Installation  
✅ Web-Interface auf Port 8080  
✅ Netzwerk-Relay für mehrere Clients  
✅ OCR-Texterkennung (Deutsch)  
✅ PDF-Verarbeitung  
✅ Automatische Archivierung  
✅ Volltext-Suche in SQLite-DB  
✅ Backup-System  
✅ Live-Ordnerüberwachung (Watchdog)

## 🚨 Troubleshooting

### Server startet nicht
```
1. Rechtsklick auf start_server.bat → Als Administrator ausführen
2. Prüfe Firewall (Port 8080 freigeben)
3. Prüfe .archiv_config.json (gültige Pfade?)
```

### OCR funktioniert nicht
```
1. Doppelklick auf diagnose_tesseract.bat
2. Prüfe ob deutsche Sprache installiert ist
3. Pfad in .archiv_config.json korrekt?
```

### PDF-Konvertierung schlägt fehl
```
1. Doppelklick auf diagnose_poppler.bat
2. Prüfe ob pdfinfo.exe gefunden wird
3. Pfad in .archiv_config.json korrekt?
```

### Firewall-Regel erstellen
```powershell
# Als Administrator in PowerShell:
netsh advfirewall firewall add rule name="Werkstatt-Archiv Server" dir=in action=allow protocol=TCP localport=8080
```

## 📝 Beispiel-Konfiguration

```json
{
  "input_folder": "\\\\SERVER\\Scans\\Eingang",
  "archiv_root": "\\\\SERVER\\Archiv",
  "backup_target_dir": "\\\\SERVER\\Backups",
  
  "tesseract_cmd": "C:\\Program Files\\Tesseract-OCR\\tesseract.exe",
  "poppler_path": "C:\\Program Files\\poppler\\Library\\bin",
  
  "keywords": [
    "Garantie",
    "Kulanz",
    "Rückruf",
    "Diagnose"
  ]
}
```

## 📚 Weitere Dokumentation

- **Vollständige Anleitung:** `README_SERVER.md` im dist-Ordner
- **GitHub Repository:** https://github.com/SHP-ART/WerkstattArchiv-V2
- **Projekt-Wiki:** Siehe Repository

## 🐛 Bug Reports & Feature Requests

Bitte GitHub Issues verwenden:
https://github.com/SHP-ART/WerkstattArchiv-V2/issues

## 📄 Lizenz

MIT License - siehe LICENSE Datei im Repository
