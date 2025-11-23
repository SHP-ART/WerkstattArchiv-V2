# Copilot Instructions - Werkstatt-Archiv

## Project Context

**Werkstatt-Archiv** ist ein Python-basiertes System zur automatischen Archivierung und Verwaltung von eingescannten Werkstatt-PDF-Aufträgen mittels OCR, SQLite-Datenbank und Ordnerüberwachung.

### Hauptkomponenten
- **OCR-Pipeline**: PDF → Bilder → Tesseract → Textextraktion (Seite 1 für Metadaten, Seiten 2-10 für Keywords)
- **Parser-System**: Regex-basierte Extraktion von Auftragsnummer, Kundendaten, Kennzeichen, VIN
- **Archiv-Engine**: Hierarchische Ordnerstruktur nach Auftragsnummer mit Tausender-Blöcken und automatischer Versionierung
- **SQLite-Datenbank**: Volltext-Suche über alle Aufträge, Kunden und Schlagwörter
- **File-Watcher**: Automatische Verarbeitung neuer PDFs im Eingangsordner (watchdog)
- **Backup-System**: ZIP-basierte Sicherung von DB, Config und optional komplettes Archiv

### Architektur
```
Eingangsordner (Netzwerk)
    ↓ (watchdog oder Batch)
OCR (pdf2image + Tesseract)
    ↓
Parser (Regex-Extraktion)
    ↓
Archive (Versionierung + Move)
    ↓
SQLite DB + CSV-Index
    ↓
Archiv-Struktur: /070000-079999/076329/076329_Auftrag.pdf
```

### Key Technologies
- **Python 3.9+**: Standard-Bibliotheken + externe Pakete
- **Tesseract OCR**: Texterkennung (Sprache: Deutsch)
- **SQLite3**: Embedded-Datenbank (Standard-Bibliothek)
- **watchdog**: Ordnerüberwachung
- **pdf2image + Pillow**: PDF-zu-Bild-Konvertierung
- **pytesseract**: Python-Wrapper für Tesseract

## Code Style & Conventions

### Python-Standards
- **PEP 8** für Code-Formatierung
- **PEP 484** Typannotationen für alle Funktionssignaturen
- **Docstrings**: Google-Style für alle Module, Klassen und öffentliche Funktionen
- **Logging**: Verwende `logging` statt `print()`, Level: DEBUG/INFO/WARNING/ERROR

### Naming Conventions
- `snake_case` für Variablen, Funktionen, Module
- `PascalCase` für Klassen und Custom Exceptions
- `UPPER_CASE` für Konstanten
- Präfix `_` für interne/private Funktionen

### Module-Struktur
Jedes Modul folgt diesem Aufbau:
1. Docstring mit Modulbeschreibung
2. Imports (Standard-Lib → Externe Pakete → Lokale Module)
3. Logger-Setup: `logger = logging.getLogger(__name__)`
4. Custom Exceptions (z.B. `OCRError`, `ArchiveError`)
5. Haupt-Funktionen mit Docstrings und Typannotationen

### Error Handling Pattern
```python
try:
    # Operation
    logger.info("Starte Operation X...")
    result = do_something()
    logger.info("✓ Operation erfolgreich")
    return result
except SpecificError as e:
    logger.error(f"Fehler bei Operation X: {e}")
    raise CustomError(f"Details: {e}")
```

## Critical Project Knowledge

### Zwei-Seiten-Konzept (WICHTIG!)
- **Seite 1** (Index 0): Immer der Werkstattauftrag mit Metadaten (Auftragsnr., Kunde, etc.)
- **Seiten 2-10** (Index 1-9): Anhänge (Diagnose, Rechnung, Protokolle) → nur Schlagwortsuche
- OCR-Funktion `pdf_to_ocr_texts()` gibt Liste zurück: `texts[0]` = Seite 1, `texts[1]` = Seite 2, ...

### Dateinamen-Format (Konfigurierbar!)
- **Pattern-basiert**: Konfigurierbar über `dateiname_pattern` in Config
- **Standard**: `{auftrag_nr}_Auftrag{version_suffix}.pdf` → `076329_Auftrag.pdf`
- **Mit Metadaten**: `{auftrag_nr}_{name}_{datum}{version_suffix}.pdf` → `076329_Voigt_2024-07-29.pdf`
- **Verfügbare Platzhalter**: `{auftrag_nr}`, `{name}`, `{datum}`, `{kennzeichen}`, `{vin}`, `{version_suffix}`
- **Fallback-Werte**: Fehlende Daten werden durch Platzhalter ersetzt (z.B. "Unbekannt" für Name, "ohne_kz" für Kennzeichen)
- **Automatische Bereinigung**: Namen werden von Sonderzeichen/Leerzeichen befreit, max. 30 Zeichen

### Formular-Varianten
1. **Neu**: Mit `Kd.Nr.:` → `formular_version = "neu"`
2. **Alt**: Ohne Kundennummer → `formular_version = "alt"`
- Parser muss beide Varianten erkennen (siehe `parser.py`)

### Auftragsnummer-Format
- **Rohe Eingabe**: "303", "76329", "Auftrag Nr. 303"
- **Normalisiert**: `format_auftrag_nr()` → `"000303"`, `"076329"` (6-stellig, Nullen-Padding)
- **Pflichtfeld**: Ohne Auftragsnummer → Datei in `Fehler/`-Ordner

### Archiv-Ordnerstruktur
```
Archiv/
├── 000000-009999/          # Tausender-Block (optional)
│   └── 000303/             # Auftragsnummer-Ordner
│       └── 000303_Auftrag.pdf
├── 070000-079999/
│   └── 076329/
│       ├── 076329_Auftrag.pdf       # Version 1
│       └── 076329_Auftrag_v2.pdf    # Version 2 (automatisch)
└── kunden_index.csv        # CSV-Export aller Aufträge
```

### Netzwerkpfade (Plattform-Unabhängig)
- **macOS**: `/Volumes/Server/Werkstatt/Archiv`
- **Windows**: `\\SERVER\Werkstatt\Archiv`
- **Immer `pathlib.Path()` verwenden** für Pfadoperationen (nicht `os.path`)
- Konfiguration in `.archiv_config.json` oder `.archiv_config.yaml`

### Versionierung
- Beim Verschieben prüft `generate_target_filename()` existierende Dateien
- Automatisches Anhängen von `_v2`, `_v3`, ... bei Duplikaten
- Hash-Prüfung (`calculate_file_hash()`) zur Duplikatserkennung

## Development Workflow

### Setup
```bash
# Dependencies installieren
pip install -r requirements.txt

# Tesseract installieren
# macOS:
brew install tesseract tesseract-lang

# Windows: https://github.com/UB-Mannheim/tesseract/wiki

# Erstkonfiguration
python main.py --set-input-folder "/Volumes/Server/Scans/Eingang"
python main.py --set-archiv-root "/Volumes/Server/Archiv"
python main.py --set-backup-target "/Volumes/Server/Backups"

# Tesseract testen
python main.py --test-tesseract
```

### Entwicklungszyklus
```bash
# Web-UI starten (empfohlen)
python web_app.py

# CLI: Batch-Verarbeitung (einmalig)
python main.py --process-input

# CLI: Watch-Modus (dauerhaft)
python main.py --watch

# CLI: Suche testen
python main.py --search-auftrag 76329
python main.py --search-keyword "Garantie"

# CLI: Backup erstellen
python main.py --backup
```

### Debugging
```bash
# Verbose-Modus (DEBUG-Level)
python main.py --process-input --verbose

# Logs analysieren
# Achte auf: "Auftragsnummer gefunden", "Keywords gefunden", "Archiviert als"
```

### Testing Best Practices
- **Test-PDFs**: Lege Test-PDFs in separatem Ordner an (nicht im produktiven Eingang)
- **Test-Config**: Erstelle separate Konfiguration für Tests
- **Fehlerordner prüfen**: Bei OCR-Fehlern landen PDFs in `Eingang/Fehler/`

## Module-Specific Patterns

### config.py
- Lazy-Loading: Config wird erst geladen wenn `get_input_folder()` etc. aufgerufen wird
- Default-Werte in `DEFAULT_CONFIG` Dictionary
- Automatische Ergänzung fehlender Werte beim Laden
- Validierung via `validate()` vor Hauptprogramm-Start

### ocr.py
- **Wichtig**: Tesseract muss installiert sein, sonst ImportError
- `pdf_to_images()`: Konvertiert PDF zu PIL.Image-Liste (DPI: 300 Standard)
- `image_to_text()`: OCR auf einzelnem Bild (PSM 3 = Auto-Segmentierung)
- `pdf_to_ocr_texts()`: Haupt-Funktion, gibt Text-Liste zurück (1 Text pro Seite)
- **Enhanced-Modus**: `pdf_to_ocr_texts_enhanced()` mit Bildvorverarbeitung bei schlechter Qualität

### parser.py
- **Regex-Patterns**: Multiple Varianten pro Feld (z.B. "Auftrag Nr.", "Auftragsnummer", "Auftrags-Nr.")
- `extract_auftragsnummer()`: **Pflichtfeld**, wirft `ParserError` wenn nicht gefunden
- Optionale Felder: Geben `None` zurück wenn nicht gefunden
- `extract_keywords_from_pages()`: Case-insensitive, gibt Dict mit Seitenzahlen zurück

### archive.py
- `format_auftrag_nr()`: Padding mit `zfill()`, configurable Länge
- `get_thousand_block()`: Berechnet Block wie "070000-079999"
- `move_to_archive()`: Berechnet Hash **vor** dem Verschieben (Duplikatsprüfung)
- `move_to_error_folder()`: Bei Parse-Fehlern, mit Timestamp bei Namenskonflikten

### db.py
- SQLite mit `row_factory = sqlite3.Row` für Dict-Zugriff
- `keywords_json`: JSON-serialisiert (z.B. `{"Garantie": [2, 3], "Kulanz": [2]}`)
- Indizes auf allen Such-Feldern (auftrag_nr, kunden_nr, name, datum, kennzeichen, hash)
- `search_by_keyword()`: Sucht im JSON-Feld mit `LIKE '%"keyword"%'`

### watcher.py
- **watchdog-Observer**: Läuft in separatem Thread
- `_wait_for_file_complete()`: Wartet bis Dateigröße stabil (wichtig bei langsamen Scans)
- **Blockierend**: `start_watcher()` läuft bis Ctrl+C
- Callback-Pattern: `process_file_callback(pdf_path)` wird für jede neue PDF aufgerufen

### backup.py
- ZIP mit `zipfile.ZIP_DEFLATED` (Kompression)
- Timestamp-Format: `YYYY-MM-DD_HH-MM-SS`
- `include_archive=True`: Kann **sehr groß** werden (Warnung an User)
- `cleanup_old_backups()`: Behält nur neueste N Backups (Standard: 10)

## Common Extension Points

### Neue Schlagwörter hinzufügen
```python
# In config.py → DEFAULT_CONFIG["keywords"]
"keywords": [
    # ... bestehende
    "Neues Schlagwort",
    "Weiteres Schlagwort"
]
```

### Neue Suchfunktion
```python
# In db.py
def search_by_vin(db_path: Path, vin: str) -> List[Dict[str, Any]]:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM auftraege WHERE vin LIKE ?', (f'%{vin}%',))
    return [dict(row) for row in cursor.fetchall()]

# In main.py → search_group.add_argument()
search_group.add_argument('--search-vin', metavar='VIN', help='Suche nach VIN')
```

### Neue Metadaten-Feld
1. `parser.py`: Neue `extract_X()` Funktion
2. `parser.extract_auftrag_metadata()`: Feld hinzufügen
3. `db.py`: Spalte in `CREATE TABLE` + Index
4. `kunden_index.py`: Spalte im CSV-Header

## Web-UI

### Architektur
- **Flask**: Web-Framework mit Bootstrap 5 UI
- **RESTful API**: JSON-Endpoints für alle Operationen
- **Live-Updates**: Polling-basiertes Status-Update (3s Intervall)
- **Responsive Design**: Mobile-freundlich

### Module-Struktur
```
web_app.py          # Flask-App mit API-Endpoints
├── templates/      # Jinja2-Templates
│   ├── base.html       # Base-Layout mit Navigation
│   ├── index.html      # Dashboard mit Live-Log
│   ├── settings.html   # Konfiguration
│   ├── search.html     # Suchformular
│   └── archive.html    # Archiv-Übersicht
└── static/         # CSS/JS (via CDN)
```

### API-Endpoints
- `GET /api/stats`: Dashboard-Statistiken
- `GET /api/processing/status`: Live-Verarbeitungs-Log
- `GET/POST /api/settings`: Konfiguration lesen/schreiben
- `POST /api/settings/validate`: Ordnerpfad validieren
- `POST /api/search`: Volltext-Suche
- `GET /api/archive/list?page=1&per_page=50`: Paginierte Aufträge
- `GET /api/archive/download/<id>`: PDF herunterladen
- `POST /api/watcher/start`: Watcher starten
- `POST /api/watcher/stop`: Watcher stoppen

### Watcher-Integration
- Läuft in separatem Thread (daemon=True)
- Callback schreibt in `processing_queue` (Queue-Modul)
- Web-UI pollt Queue für Live-Updates
- Status-Indicator: Rot = gestoppt, Grün = aktiv

### Security-Hinweise
- Nur für lokales Netzwerk (127.0.0.1) oder Intranet
- **Kein HTTPS** standardmäßig (Development-Server)
- Für Produktion: WSGI-Server (gunicorn) + Reverse-Proxy (nginx)

## Troubleshooting

### Tesseract nicht gefunden
- **macOS**: `brew install tesseract tesseract-lang`
- **Windows**: Pfad in Config setzen: `"tesseract_cmd": "C:\\Program Files\\Tesseract-OCR\\tesseract.exe"`

### OCR erkennt nichts
- DPI erhöhen: `dpi=400` in `pdf_to_images()`
- Enhanced-Modus nutzen: `pdf_to_ocr_texts_enhanced()`
- Scan-Qualität prüfen (zu dunkel, zu hell, schräg?)

### Keine Auftragsnummer gefunden
- **Häufigste Ursache**: Nummer nicht im OCR-Text, sondern nur im Dateinamen
- **Lösung**: `extract_auftragsnummer_from_filename()` wird automatisch als Fallback verwendet
- Unterstützte Formate: `"76329 Auftrag.pdf"`, `"Auftrag 76329 komplett.pdf"`, `"test_76329.pdf"`
- OCR-Text-Vorschau loggen: `logger.debug(text[:500])`
- Regex-Pattern in `parser.extract_auftragsnummer()` erweitern

### Netzwerkpfad nicht erreichbar
- Pfad mit `Path().exists()` prüfen
- Auf Windows: UNC-Pfad `\\SERVER\Share` verwenden
- Auf macOS: SMB-Mount in `/Volumes/` prüfen

### Datenbank gesperrt
- Kein paralleler Zugriff: nur ein Prozess gleichzeitig
- Bei Multi-User: SQLite durch PostgreSQL/MySQL ersetzen (größere Änderung)

### Web-UI lädt nicht
- Port bereits belegt: `--port 8080` verwenden
- Firewall: Port 5000 freigeben
- Browser-Console prüfen (F12) für JavaScript-Fehler

## AI Agent Guidance

Bei Änderungen am Projekt:
1. **Immer Typannotationen** hinzufügen
2. **Docstrings** für neue Funktionen (Args, Returns, Raises)
3. **Logging** statt Print (mit passenden Levels)
4. **Error-Handling**: Spezifische Exceptions (z.B. `OCRError` statt generisches `Exception`)
5. **Tests**: Mindestens manuelle Tests mit echten PDFs durchführen
6. **Dokumentation**: README.md aktualisieren bei neuen Features

Bei Bugs:
1. **Verbose-Modus** aktivieren (`--verbose`)
2. **OCR-Text** loggen (erste 500 Zeichen)
3. **Fehlerordner** prüfen (`Eingang/Fehler/`)
4. **Regex-Pattern** mit Beispiel-Text testen (regex101.com)
