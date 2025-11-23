# Werkstatt-Archiv

Automatische Archivierung und Verwaltung von Werkstatt-PDF-Aufträgen mit OCR, SQLite-Datenbank und Ordnerüberwachung.

> ⚠️ **WICHTIG**: Dieses Repository enthält **keine Kundendaten, PDFs oder Datenbanken**. Die `.gitignore` stellt sicher, dass nur Code-Dateien auf GitHub hochgeladen werden. Alle sensiblen Daten bleiben lokal auf Ihrem Server.

## Funktionen

- **OCR-Verarbeitung**: Automatische Texterkennung aus eingescannten PDF-Dokumenten
- **Intelligente Metadaten-Extraktion**: Auftragsnummer, Kundennummer, Name, Datum, Kennzeichen, VIN
- **Schlagwort-Erkennung**: Automatische Erkennung von Garantie-, Kulanz-, Diagnose- und Service-Begriffen in Anhängen
- **Strukturierte Archivierung**: Ablage nach Auftragsnummer mit Tausender-Blöcken
- **SQLite-Datenbank**: Volltext-Suche nach Aufträgen, Kunden, Kennzeichen, Schlagwörtern
- **Ordnerüberwachung**: Automatische Verarbeitung neuer PDFs im Eingangsordner
- **Backup-Funktion**: Regelmäßige Sicherung von Datenbank und Archiv
- **Kunden-Index**: CSV-Export aller Aufträge mit Kundendaten

## Voraussetzungen

### Python
- Python 3.9 oder höher

### Externe Software
- **Tesseract OCR**: Erforderlich für die Texterkennung
  - **macOS**: `brew install tesseract tesseract-lang`
  - **Windows**: Download von https://github.com/UB-Mannheim/tesseract/wiki
  - **Linux**: `sudo apt-get install tesseract-ocr tesseract-ocr-deu`

### Python-Pakete
Installiere die Abhängigkeiten mit:
```bash
pip install -r requirements.txt
```

## Installation

1. Repository klonen oder herunterladen
2. Python-Abhängigkeiten installieren:
   ```bash
   pip install -r requirements.txt
   ```
3. Tesseract OCR installieren (siehe oben)
4. Konfiguration einrichten (siehe unten)

## Konfiguration

### Erstkonfiguration

Beim ersten Start erstellt das Programm automatisch eine Standardkonfiguration. Du kannst die Pfade über CLI-Optionen setzen:

```bash
# Eingangsordner setzen (Netzwerkpfad)
python main.py --set-input-folder "/Volumes/Server/Werkstatt/Scans/Eingang"

# Archivordner setzen
python main.py --set-archiv-root "/Volumes/Server/Werkstatt/Archiv"

# Datenbank-Pfad setzen
python main.py --set-db-path "/Volumes/Server/Werkstatt/Archiv/werkstatt.db"

# Backup-Zielordner setzen
python main.py --set-backup-target "/Volumes/Server/Werkstatt/Backups"
```

### Windows UNC-Pfade
Unter Windows kannst du UNC-Pfade verwenden:
```bash
python main.py --set-input-folder "\\SERVER\Werkstatt\Scans\Eingang"
python main.py --set-archiv-root "\\SERVER\Werkstatt\Archiv"
```

### Konfigurationsdatei

Die Konfiguration wird in `.archiv_config.json` im Archivordner gespeichert. Beispiel:

```json
{
  "input_folder": "/Volumes/Server/Werkstatt/Scans/Eingang",
  "archiv_root": "/Volumes/Server/Werkstatt/Archiv",
  "db_path": "/Volumes/Server/Werkstatt/Archiv/werkstatt.db",
  "backup_target_dir": "/Volumes/Server/Werkstatt/Backups",
  "auftragsnummer_pad_length": 6,
  "use_thousand_blocks": true,
  "dateiname_pattern": "{auftrag_nr}_Auftrag{version_suffix}.pdf",
  "max_pages_to_ocr": 10,
  "auto_backup_interval_hours": 24,
  "kunden_index_file": "kunden_index.csv",
  "keywords": [
    "Garantie", "Gewährleistung", "Kulanz", "Rückruf",
    "Fehlerspeicher", "Diagnose", "Motorkontrollleuchte",
    "Bremse", "Bremsbelag", "ABS", "ESP", "TÜV", "HU",
    "Wartung", "Inspektion", "Ölwechsel", "Klimaanlage",
    "Kostenvoranschlag", "Freigabe", "Rechnung"
  ]
}
```

## Verwendung

### Web-UI (empfohlen)

Die moderne Browser-Oberfläche bietet alle Funktionen mit komfortabler Bedienung:

```bash
# Web-UI starten
python web_app.py

# Mit Custom-Port
python web_app.py --port 8080

# Für Zugriff im Netzwerk
python web_app.py --host 0.0.0.0 --port 5000
```

**Features der Web-UI:**
- 📊 **Dashboard**: Live-Statistiken, Watcher-Steuerung, Verarbeitungs-Log
- ⚙️ **Einstellungen**: Ordner konfigurieren, Pfade validieren, OCR-Einstellungen, **Dateinamen-Format**
- 🔍 **Suche**: Nach Auftragsnummer, Kunde, Kennzeichen, Schlagwort, Datum
- 📁 **Archiv**: Übersicht aller Aufträge mit Pagination, PDF-Download

Die Web-UI ist nach dem Start verfügbar unter: **http://127.0.0.1:5000**

#### Dateinamen-Format konfigurieren

In den Einstellungen kann das Dateinamen-Format für archivierte PDFs angepasst werden:

- **Standard**: `076329_Auftrag.pdf`
- **Mit Name**: `076329_Voigt.pdf`
- **Mit Name + Datum**: `076329_Voigt_2024-07-29.pdf`
- **Mit Kennzeichen + Name**: `076329_SFB-B1005_Voigt.pdf`

Verfügbare Platzhalter: `{auftrag_nr}`, `{name}`, `{datum}`, `{kennzeichen}`, `{vin}`, `{version_suffix}`

### CLI (Kommandozeile)

#### Batch-Verarbeitung aller PDFs im Eingangsordner
```bash
python main.py --process-input
```

#### Ordnerüberwachung starten (automatische Verarbeitung)
```bash
python main.py --watch
```

### Suchfunktionen

```bash
# Nach Auftragsnummer suchen
python main.py --search-auftrag 76329

# Nach Kundenname suchen
python main.py --search-name "Voigt"

# Nach Kundennummer suchen
python main.py --search-kunden-nr 27129

# Nach Schlagwort suchen
python main.py --search-keyword "Garantie"

# Nach Kennzeichen suchen
python main.py --search-kennzeichen "B-AB 1234"
```

### Backup erstellen
```bash
# Backup von Datenbank und Konfiguration
python main.py --backup

# Backup inkl. komplettes Archiv (Achtung: kann sehr groß werden!)
python main.py --backup --include-archive
```

## Archiv-Struktur

PDFs werden nach Auftragsnummer strukturiert abgelegt:

```
Archiv/
├── 070000-079999/
│   └── 076329/
│       ├── 076329_Auftrag.pdf
│       └── 076329_Auftrag_v2.pdf
├── 000000-009999/
│   └── 000303/
│       └── 000303_Auftrag.pdf
└── kunden_index.csv
```

## Datenbank-Schema

Die SQLite-Datenbank enthält eine Tabelle `auftraege` mit folgenden Feldern:

- `auftrag_nr`: Auftragsnummer (gepaddet)
- `kunden_nr`: Kundennummer (optional)
- `kunde_name`: Name des Kunden
- `datum`: Auftragsdatum
- `kennzeichen`: KFZ-Kennzeichen
- `vin`: Fahrgestellnummer
- `formular_version`: "neu" oder "alt"
- `file_path`: Pfad zur archivierten Datei
- `hash`: SHA256-Hash der Datei
- `keywords_json`: JSON mit gefundenen Schlagwörtern und Seitenzahlen
- `created_at`, `updated_at`: Zeitstempel

## Schlagwort-Kategorien

Das System erkennt automatisch folgende Kategorien von Schlagwörtern in PDF-Anhängen (Seiten 2-10):

- **Garantie/Kulanz**: Garantie, Gewährleistung, Kulanz, Rückruf, Serviceaktion
- **Diagnose/Fehler**: Fehlerspeicher, DTC, Diagnose, Motorkontrollleuchte
- **Bremsen/Fahrwerk**: Bremsbelag, Bremsscheibe, ABS, ESP, Stoßdämpfer
- **Service/Wartung**: Inspektion, Ölwechsel, Zahnriemen, Klimaservice
- **Dokumente**: Kostenvoranschlag, Freigabe, Rechnung, Prüfprotokoll

## Fehlerbehandlung

- PDFs ohne erkennbare Auftragsnummer werden in den Unterordner `Fehler/` verschoben
- Alle Aktionen werden ins Log geschrieben
- Bei Netzwerkproblemen wird ein Fehler geloggt, aber das Programm läuft weiter

## Logs

Das Programm schreibt detaillierte Logs über alle Verarbeitungsschritte:
- INFO: Erfolgreiche Verarbeitung, extrahierte Daten
- WARNING: Fehlende optionale Felder, Duplikate
- ERROR: Fehlgeschlagene OCR, fehlende Auftragsnummer, Netzwerkfehler

## Lizenz

Dieses Projekt ist für den internen Werkstatt-Gebrauch entwickelt.
