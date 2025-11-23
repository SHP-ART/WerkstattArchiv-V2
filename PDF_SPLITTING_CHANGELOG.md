# PDF-Splitting Feature - Änderungsprotokoll

## Übersicht

Das System wurde umgestellt auf eine neue Archivierungs-Logik:

**ALT**: Eine PDF mit allen Seiten zusammen
**NEU**: 
- Auftrag-PDF (nur Seite 1)
- Anhang-PDF (Seiten 2-N)

## Implementierte Änderungen

### 1. Neues Modul: `pdf_split.py`

**Funktionen**:
- `split_pdf_auftrag_anhang()`: Teilt PDF in Auftrag (Seite 1) + Anhang (Rest)
- `combine_pdfs_to_anhang()`: Kombiniert mehrere PDFs zu einem Anhang
- `extract_pages_from_pdf()`: Extrahiert Seitenbereich aus PDF

**Usage**:
```python
from pdf_split import split_pdf_auftrag_anhang

auftrag_pdf, anhang_pdf = split_pdf_auftrag_anhang(
    input_pdf=Path("scan.pdf"),
    output_dir=Path("temp/"),
    auftrag_nr="076329"
)
# → temp/076329_Auftrag.pdf (1 Seite)
# → temp/076329_Anhang_S2-10.pdf (9 Seiten)
```

### 2. Geändert: `main.py` - `process_single_pdf()`

**Workflow NEU**:
1. OCR auf komplettem PDF
2. Metadaten aus Seite 1 extrahieren
3. **PDF aufteilen** in Auftrag + Anhang
4. Schlagwörter aus Anhang-Seiten extrahieren
5. **Auftrag-PDF archivieren** (Hauptdatei)
6. **Anhang-PDF archivieren** (im selben Ordner)
7. Datenbank-Eintrag mit Auftrag-PDF als Hauptpfad
8. Original-PDF löschen

**Ergebnis im Archiv**:
```
070000-079999/076329/
├── 076329_Auftrag.pdf       ← Seite 1 (Metadaten)
└── 076329_Anhang_S2-10.pdf  ← Seiten 2-10 (Schlagwörter)
```

### 3. Geändert: `folder_import.py`

**Workflow bei Ordner-Import**:

#### MIT AUFTRAG:
- Erste PDF im Ordner → Split in Auftrag + Anhang
- Weitere PDFs → Als zusätzliche Anhang-Seiten

**Ergebnis**:
```
Ordner: 076329/
  ├── scan1.pdf (10 Seiten)
  ├── diagnose.pdf (3 Seiten)
  └── rechnung.pdf (2 Seiten)

Archiv: 070000-079999/076329/
  ├── 076329_Auftrag.pdf       ← Seite 1 von scan1.pdf
  └── 076329_Anhang_S2-15.pdf  ← Rest von scan1 + diagnose + rechnung
```

#### OHNE AUFTRAG (--oa):
- Alle PDFs → Eine Anhang-PDF
- Kein Auftrag-PDF!
- Dateiname: `076329_OA_Anhang_S1-15.pdf`

**Ergebnis**:
```
Ordner: 076329/
  ├── diagnose.pdf
  └── fotos.pdf

Archiv: 070000-079999/076329/
  └── 076329_OA_Anhang_S1-5.pdf  ← Alle PDFs kombiniert
```

**Später Auftrag hinzufügen**:
Wenn später ein Auftrag dazu kommt:
```bash
# Auftrag-PDF manuell ins Archiv verschieben
cp neuer_auftrag.pdf /Archiv/070000-079999/076329/076329_Auftrag.pdf
```

Das System erkennt automatisch, dass bereits ein `_OA_Anhang` existiert und behält beide Dateien.

## Vorteile der neuen Logik

### ✅ Flexibilität
- Auftrag und Anhang sind getrennt
- Anhang kann später erweitert werden (Versionierung)
- OA-Dokumente können nachträglich Auftrag bekommen

### ✅ Performance
- Kleinere Auftrag-PDFs (nur 1 Seite)
- Schnellere Anzeige im Browser
- Weniger OCR bei Re-Scan (nur Anhang)

### ✅ Klarheit
- Dateinamen zeigen Seitenzahlen (`_S2-10`)
- Sofort erkennbar: Auftrag oder Anhang?
- OA-Kennzeichnung (`_OA_`)

## Migration bestehender Aufträge

**Optionales Script** (wird NICHT automatisch ausgeführt):

```bash
# Alle bestehenden PDFs splitten
python3 migrate_existing.py --archiv /path/to/archiv
```

**Funktion**:
- Durchsucht alle Aufträge im Archiv
- Findet `076329_Auftrag.pdf` mit >1 Seite
- Splittet in Auftrag (S1) + Anhang (S2-N)
- Aktualisiert Datenbank

**ACHTUNG**: Backup vorher erstellen!

## Testing

### Test 1: Einzelne PDF verarbeiten
```bash
cp test.pdf /Volumes/Server/Scans/Eingang/
python3 main.py --process-input
```

**Erwartung**:
- Archiv: `076329_Auftrag.pdf` + `076329_Anhang_S2-10.pdf`
- Datenbank: Eintrag mit Auftrag-PDF als `file_path`

### Test 2: Ordner-Import MIT Auftrag
```bash
python3 folder_import.py /path/to/076329
```

**Erwartung**:
- Erste PDF → Split
- Weitere PDFs → Anhang kombiniert

### Test 3: Ordner-Import OHNE Auftrag
```bash
python3 folder_import.py /path/to/076329 --oa
```

**Erwartung**:
- Nur Anhang-PDF mit OA-Kennzeichnung
- Keine Auftrag-PDF

### Test 4: Später Auftrag hinzufügen
```bash
# Manuell Auftrag-PDF in bestehenden OA-Ordner kopieren
cp neuer_auftrag.pdf /Archiv/.../076329/076329_Auftrag.pdf
```

**Erwartung**:
- Ordner enthält jetzt beide: Auftrag + OA-Anhang

## Dateinamens-Konventionen

### Auftrag-PDF
```
{auftrag_nr}_Auftrag{version_suffix}.pdf
```

Beispiele:
- `076329_Auftrag.pdf` (Version 1)
- `076329_Auftrag_v2.pdf` (Version 2, bei Duplikaten)

### Anhang-PDF
```
{auftrag_nr}_Anhang_S{start}-{end}.pdf
{auftrag_nr}_Anhang_S{start}-{end}_v{version}.pdf
```

Beispiele:
- `076329_Anhang_S2-10.pdf` (Seiten 2-10)
- `076329_Anhang_S11-15_v2.pdf` (Zusätzliche Seiten, Version 2)

### OA-Anhang
```
{auftrag_nr}_OA_Anhang_S{start}-{end}.pdf
```

Beispiele:
- `076329_OA_Anhang_S1-5.pdf` (Ohne Auftrag, Seiten 1-5)

## Backwards Compatibility

**Alte PDFs** (vor Update):
- Werden NICHT automatisch gesplittet
- Bleiben als einzelne PDF im Archiv
- Datenbank-Einträge bleiben gültig
- Optional: Migration-Script verwenden

**Neue PDFs** (nach Update):
- Werden automatisch gesplittet
- Neue Dateinamen-Konvention
- Kompatibel mit alter Datenbank-Struktur

## Known Issues

### Issue 1: Sehr große Anhänge
**Problem**: Anhang mit >100 Seiten wird langsam
**Workaround**: OCR-Limit auf 50 Seiten erhöhen in Config

### Issue 2: OA später mit Auftrag
**Problem**: Automatische Erkennung fehlt noch
**Workaround**: Manuelle Datei-Kopie (siehe Test 4)
**TODO**: Web-UI Feature "Auftrag hinzufügen zu OA"

## Nächste Schritte

1. **Testing**: Alle 4 Test-Szenarien durchführen
2. **Feedback**: Funktioniert die neue Logik in der Praxis?
3. **Web-UI**: Button "Auftrag zu OA hinzufügen" implementieren
4. **Migration**: Optional alte Aufträge migrieren

## Rollback (falls Probleme)

Falls die neue Logik Probleme macht:

```bash
# Git Commit rückgängig machen
git revert <commit-hash>

# Oder: Alte Dateien wiederherstellen
git checkout HEAD~1 main.py folder_import.py
```

**Wichtig**: Datenbank-Einträge bleiben bestehen (kein Datenverlust).
