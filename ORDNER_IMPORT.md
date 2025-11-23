# Ordner-Import

## 📁 Funktion

Der **Ordner-Import** ermöglicht das Importieren mehrerer PDFs eines Auftrags aus einem Ordner.

### Konzept:
```
Ordner-Name = Auftragsnummer
├── 1-Hauptauftrag.pdf    (Metadaten-Extraktion)
├── 2-Diagnose.pdf         (nur Schlagwörter)
├── 3-Rechnung.pdf         (nur Schlagwörter)
└── 4-Fotos.pdf            (nur Schlagwörter)
        ↓
    Zusammenführen
        ↓
076329_Komplett.pdf → Archiv + Datenbank
```

## 🔄 Workflow

### MIT Auftrag (Standard):

1. **Ordnername = Auftragsnummer**
   - `076329` → Auftragsnummer 076329
   - `76329_Komplett` → Auftragsnummer 076329
   - `Auftrag 76329` → Auftragsnummer 076329

2. **Erste PDF = Hauptauftrag**
   - OCR auf allen Seiten
   - Metadaten extrahieren (Kunde, Kennzeichen, VIN, etc.)
   - Schlagwörter aus allen Seiten

3. **Weitere PDFs = Anhänge**
   - OCR auf allen Seiten
   - Nur Schlagwörter extrahieren
   - Seitenzahlen werden angepasst

4. **PDFs zusammenfügen**
   - Alle PDFs zu einer Gesamt-PDF: `076329_Komplett.pdf`
   - Reihenfolge: Alphabetisch nach Dateinamen

5. **Archivierung**
   - Gesamt-PDF ins Archiv
   - Metadaten in Datenbank
   - Originalordner wird gelöscht

### OHNE Auftrag (--oa):

1. **Ordnername = Auftragsnummer**
   - Gleich wie oben

2. **Alle PDFs = Nur Schlagwörter**
   - Keine Metadaten-Extraktion
   - Nur Schlagwörter aus allen PDFs

3. **PDFs zusammenfügen**
   - Dateiname: `076329_OA.pdf` (OA = Ohne Auftrag)

4. **Archivierung**
   - In Datenbank mit `formular_version = "oa"`
   - Keine Kundendaten (Name, KZ, VIN = NULL)

## 💻 Verwendung

### CLI: Einzelner Ordner

```bash
# Standard: MIT Auftrag, PDFs zusammenfügen
python3 folder_import.py /path/to/076329

# OHNE Auftrag (nur Schlagwörter, Dateiname: _OA.pdf)
python3 folder_import.py /path/to/076329 --oa

# Ohne Merge (nur erste PDF)
python3 folder_import.py /path/to/076329 --no-merge

# Simulation (kein Import)
python3 folder_import.py /path/to/076329 --dry-run
```

### CLI: Mehrere Ordner (Batch)

```bash
# Alle Ordner in Verzeichnis (MIT Auftrag)
python3 folder_import.py /path/to/folders --batch

# Alle Ordner OHNE Auftrag
python3 folder_import.py /path/to/folders --batch --oa

# Simulation
python3 folder_import.py /path/to/folders --batch --dry-run
```

### Beispiel-Ordnerstruktur

```
Import/
├── 076329/
│   ├── Auftrag.pdf
│   ├── Diagnose.pdf
│   └── Rechnung.pdf
├── 076330/
│   ├── Werkstattauftrag.pdf
│   └── Protokoll.pdf
└── 076331/
    └── Einzelauftrag.pdf
```

Befehl:
```bash
python3 folder_import.py Import/ --batch
```

Ergebnis:
```
Archiv/
├── 070000-079999/
│   ├── 076329/
│   │   └── 076329_Komplett.pdf  (3 PDFs gemergt)
│   ├── 076330/
│   │   └── 076330_Komplett.pdf  (2 PDFs gemergt)
│   └── 076331/
│       └── 076331_Auftrag.pdf   (1 PDF, kein Merge)
```

## 🎯 Anwendungsfälle

### 1. Scanner mit automatischer Trennung
Scanner speichert jeden Scan separat:
```
Scan1_Auftrag.pdf
Scan2_Diagnose.pdf
Scan3_Rechnung.pdf
```

**Lösung**: Alle in Ordner `076329/` → Automatischer Import + Merge

### 2. E-Mail-Anhänge
Kunde schickt mehrere PDFs per E-Mail:
```
Auftrag.pdf
Vorschaden.pdf
Kostenvoranschlag.pdf
```

**Lösung**: Alle in Ordner mit Auftragsnummer → Import

### 3. Nachträgliche Dokumente
Zu bestehendem Auftrag kommen neue Dokumente:
```
076329/
├── Ursprungsauftrag.pdf  (bereits archiviert)
└── Neue_Rechnung.pdf     (neu hinzugekommen)
```

**Lösung**: Neu importieren → System erkennt Duplikat und versioniert

### 4. OHNE Auftrag (OA) - Nur Dokumente archivieren
Dokumente ohne Werkstattauftrag (Lieferscheine, Gutachten, etc.):
```
076329/
├── Gutachten.pdf
├── Fotos.pdf
└── Kostenvoranschlag.pdf
```

**Lösung**: Mit `--oa` Flag → Keine Metadaten-Extraktion, nur Schlagwörter
```bash
python3 folder_import.py 076329/ --oa
```

**Ergebnis**: `076329_OA.pdf` im Archiv mit `formular_version = "oa"`

## ⚙️ Optionen

### --oa (OHNE AUFTRAG)
Keine Metadaten-Extraktion, nur Schlagwörter, Dateiname: `_OA.pdf`
```bash
python3 folder_import.py 076329/ --oa
```

**Wann verwenden?**
- Kein Werkstattauftrag vorhanden
- Nur Dokumente archivieren (Gutachten, Fotos, Lieferscheine)
- Keine Kundendaten erforderlich

**Unterschied zu normal**:
- MIT Auftrag: `076329_Komplett.pdf` mit Kundendaten
- OHNE Auftrag: `076329_OA.pdf` ohne Kundendaten

### --no-merge
PDFs **nicht** zusammenfügen, nur erste PDF verwenden:
```bash
python3 folder_import.py 076329/ --no-merge
```

**Wann verwenden?**
- Erste PDF ist bereits vollständig
- Weitere PDFs sind optional und sollen separat bleiben

### --batch
Mehrere Ordner auf einmal verarbeiten:
```bash
python3 folder_import.py Import/ --batch
```

**Ablauf**:
1. Findet alle Unterordner
2. Verarbeitet jeden Ordner einzeln
3. Zeigt Zusammenfassung (Erfolge/Fehler)

### --dry-run
Simulation ohne tatsächlichen Import:
```bash
python3 folder_import.py Import/ --batch --dry-run
```

**Zeigt**:
- Gefundene Ordner
- Extrahierte Auftragsnummern
- Anzahl PDFs pro Ordner
- **Führt KEINEN Import durch**

## 🔍 Schlagwort-Extraktion

### Erste PDF (Hauptauftrag)
```
Seite 1: Auftrag (Metadaten)
Seite 2: Diagnose → "Garantie", "Fehlerspeicher"
Seite 3: Reparatur → "Bremsbelag"
```

**Keywords**: `{"Garantie": [2], "Fehlerspeicher": [2], "Bremsbelag": [3]}`

### Zweite PDF (Anhang)
```
Seite 1: Kostenvoranschlag → "Kulanz"
Seite 2: Rechnung → "Garantie"
```

**Angepasste Keywords**: `{"Kulanz": [4], "Garantie": [5]}`
(Seiten 4-5, da 3 Seiten vorher)

### Gesamt-PDF
```
Seiten 1-3: Hauptauftrag
Seiten 4-5: Anhang
```

**Finale Keywords**: `{"Garantie": [2, 5], "Fehlerspeicher": [2], "Bremsbelag": [3], "Kulanz": [4]}`

## ⚠️ Wichtige Hinweise

### Ordnername muss Auftragsnummer enthalten
❌ Falsch: `Komplett_Auftrag/`
✅ Richtig: `076329/` oder `Auftrag_076329/`

### Mindestens eine PDF erforderlich
❌ Fehler: Leerer Ordner
✅ OK: Mindestens 1 PDF im Ordner

### Reihenfolge der PDFs
PDFs werden **alphabetisch** sortiert:
```
1-Auftrag.pdf      → Erste (Metadaten)
2-Diagnose.pdf     → Zweite (Schlagwörter)
3-Rechnung.pdf     → Dritte (Schlagwörter)
```

**Tipp**: Nummerierung voranstellen für gewünschte Reihenfolge

### Große PDFs
Bei vielen/großen PDFs kann der Merge dauern:
- 10 PDFs á 5 MB → ~30 Sekunden
- 50 PDFs á 10 MB → ~2-3 Minuten

**Fortschritt** wird im Log angezeigt.

## 🛠️ Fehlerbehebung

### "Keine Auftragsnummer gefunden"
**Problem**: Ordnername enthält keine erkennbare Nummer

**Lösung**: Ordner umbenennen:
```bash
mv "Komplett" "076329"
```

### "Keine PDF-Dateien im Ordner"
**Problem**: Ordner ist leer oder enthält nur andere Dateien

**Lösung**: PDFs in Ordner kopieren

### "Fehler beim Mergen"
**Problem**: Defekte oder passwortgeschützte PDFs

**Lösung**: 
1. Einzelne PDFs prüfen
2. Mit `--no-merge` importieren
3. PDFs reparieren/entsperren

### Import dauert sehr lange
**Problem**: Viele oder große PDFs

**Lösung**:
- `--dry-run` vorher testen
- Batch in kleinere Gruppen aufteilen
- OCR-DPI reduzieren in Config

## 📊 Beispiel-Output

```bash
$ python3 folder_import.py 076329/

============================================================
Verarbeite Ordner: 076329
============================================================
✓ Auftragsnummer: 076329
✓ Gefunden: 3 PDF-Dateien
  [1] 1-Auftrag.pdf
  [2] 2-Diagnose.pdf
  [3] 3-Rechnung.pdf

📄 Verarbeite Hauptauftrag: 1-Auftrag.pdf
✓ OCR: 3 Seiten erkannt
✓ Metadaten: Kunde=Voigt, KZ=B-AB 1234
✓ Schlagwörter (Haupt-PDF): 2 gefunden

📑 Verarbeite 2 weitere PDF(s)...
  [2] 2-Diagnose.pdf
    → 1 Schlagwörter
  [3] 3-Rechnung.pdf
    → 1 Schlagwörter

✓ GESAMT: 3 eindeutige Schlagwörter
  - Fehlerspeicher: Seiten [2]
  - Garantie: Seiten [2, 5]
  - Kulanz: Seiten [6]

🔗 Füge 3 PDFs zusammen...
  + 1-Auftrag.pdf
  + 2-Diagnose.pdf
  + 3-Rechnung.pdf
✓ PDFs erfolgreich zusammengefügt: 076329_Komplett.pdf

📦 Verschiebe ins Archiv...
✓ Archiviert: /Archiv/070000-079999/076329/076329_Komplett.pdf

💾 Speichere in Datenbank...
✓ Datenbank-ID: 42

🧹 Räume auf...
✓ Ordner gelöscht: 076329

============================================================
✅ ORDNER ERFOLGREICH IMPORTIERT
============================================================
```

## 🔄 Integration mit bestehenden Tools

### Kombiniert mit Watch-Modus
```bash
# Watcher überwacht Eingangsordner
python3 main.py --watch

# Parallel: Ordner-Import für Batch-Aufträge
python3 folder_import.py Batch/ --batch
```

### Mit Backup-System
```bash
# 1. Ordner importieren
python3 folder_import.py Import/ --batch

# 2. Backup erstellen
python3 main.py --backup
```

## 📝 Checkliste

- [ ] Ordner nach Auftragsnummern benannt
- [ ] Mindestens 1 PDF pro Ordner
- [ ] Erste PDF = Hauptauftrag mit Metadaten
- [ ] PDFs alphabetisch sortiert (bei Bedarf nummerieren)
- [ ] Tesseract installiert und konfiguriert
- [ ] Genug Speicherplatz für gemergtes PDF
- [ ] Backup vor großem Batch-Import

## 🎓 Best Practices

1. **Simulation zuerst**: Immer `--dry-run` verwenden vor echtem Import
2. **Kleine Batches**: Nicht mehr als 50 Ordner auf einmal
3. **Nummerierung**: PDFs nummerieren für gewünschte Reihenfolge
4. **Backup**: Vor großen Importen Backup erstellen
5. **Logs prüfen**: Bei Fehlern Log-Ausgabe genau lesen
