# Poppler Installation für Windows

## Problem

Die Fehlermeldung `Unable to get page count. Is poppler installed and in PATH?` bedeutet, dass **Poppler** nicht installiert ist oder nicht im PATH gefunden wird.

Poppler ist eine Bibliothek, die von `pdf2image` benötigt wird, um PDFs in Bilder zu konvertieren (für die OCR-Verarbeitung).

## Lösung 1: Automatische Installation (Empfohlen)

### Mit Winget (Windows 10/11)

```cmd
install_poppler.bat
```

Oder manuell im Terminal:

```cmd
winget install --id=poppler.poppler -e
```

**Nach der Installation Terminal neu starten!**

## Lösung 2: Manuelle Installation

### Schritt 1: Poppler herunterladen

1. Gehe zu: https://github.com/oschwartz10612/poppler-windows/releases/
2. Lade die neueste Version herunter: `poppler-XX.XX.X.zip`
3. Entpacke die ZIP-Datei

### Schritt 2: Installation

**Option A: System-Installation (empfohlen)**

1. Kopiere den entpackten Ordner nach: `C:\Program Files\poppler`
2. Füge `C:\Program Files\poppler\Library\bin` zum **System-PATH** hinzu:
   - Windows-Taste → "Umgebungsvariablen" suchen
   - "Systemumgebungsvariablen bearbeiten"
   - Button "Umgebungsvariablen"
   - Bei "Systemvariablen" → "Path" auswählen → "Bearbeiten"
   - "Neu" → `C:\Program Files\poppler\Library\bin` eingeben
   - Alle Fenster mit "OK" schließen
   - **Terminal neu starten!**

**Option B: Portable Installation (ohne Admin-Rechte)**

1. Kopiere den entpackten Ordner in das Projektverzeichnis:
   ```
   WerkstattArchiv-V2/
   ├── poppler_portable/
   │   └── Library/
   │       └── bin/
   │           ├── pdfinfo.exe
   │           ├── pdftoppm.exe
   │           └── ...
   ```

2. Oder speichere den Ordner an einem beliebigen Ort und konfiguriere den Pfad (siehe unten)

### Schritt 3: Pfad konfigurieren (wenn nicht im PATH)

Wenn Poppler nicht im System-PATH ist, kannst du den Pfad in der Konfiguration setzen:

**JSON-Config** (`.archiv_config.json`):
```json
{
  "poppler_path": "C:\\Program Files\\poppler\\Library\\bin"
}
```

**YAML-Config** (`.archiv_config.yaml`):
```yaml
poppler_path: "C:\\Program Files\\poppler\\Library\\bin"
```

**WICHTIG:** 
- In JSON: Doppelte Backslashes `\\` verwenden
- In YAML: Einfache Backslashes `\` verwenden

## Lösung 3: Docker verwenden

Wenn du Docker verwendest, ist Poppler bereits enthalten:

```cmd
cd docker
docker_install.bat
docker_start.bat
```

Im Docker-Container ist Poppler automatisch installiert und konfiguriert.

## Test der Installation

Nach der Installation kannst du testen, ob Poppler gefunden wird:

```cmd
python
>>> import ocr
>>> ocr.setup_poppler(None)
```

Wenn eine Meldung wie `Poppler-Pfad gesetzt: C:\...` erscheint, ist die Installation erfolgreich.

Oder teste direkt im Terminal:

```cmd
pdfinfo --version
```

Sollte eine Versionsnummer ausgeben (z.B. `pdfinfo version 24.08.0`).

## Troubleshooting

### Poppler wird nach Installation nicht gefunden

1. **Terminal neu gestartet?** Nach PATH-Änderungen muss das Terminal neu gestartet werden!
2. **Richtiger Pfad?** Prüfe ob `pdfinfo.exe` im angegebenen Ordner existiert
3. **Portable Version:** Verwende die absolute Pfad-Konfiguration (siehe Schritt 3)

### Fehler: "FileNotFoundError: [WinError 2] Das System kann die angegebene Datei nicht finden"

Das bedeutet, dass `pdfinfo.exe` nicht gefunden wird. Prüfe:

1. Ist Poppler installiert? Suche nach `pdfinfo.exe` auf deinem PC
2. Ist der Pfad richtig in der Config? Öffne `.archiv_config.json` und prüfe `poppler_path`
3. Läuft das Programm im richtigen Verzeichnis? `cd` zum Projekt-Ordner

### Antivirus blockiert Poppler

Manche Antivirus-Programme blockieren heruntergeladene EXE-Dateien:

1. Füge den Poppler-Ordner zur Whitelist hinzu
2. Oder verwende die Docker-Installation

## Weitere Hilfe

- GitHub Issues: https://github.com/oschwartz10612/poppler-windows/issues
- Werkstatt-Archiv Dokumentation: README.md
- Tesseract-Installation: TESSERACT_PORTABLE_ANLEITUNG.md
