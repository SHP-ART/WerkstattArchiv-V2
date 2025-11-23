# Ordner-Import: Manuelle Verarbeitung

## Übersicht

**Ordner-Import** wird für strukturierte Aufträge mit mehreren PDFs verwendet und muss **manuell** gestartet werden.

**Watch-Modus** verarbeitet nur **einzelne PDFs** direkt im Eingangsordner automatisch.

## Verwendung

### 1. Einzelnen Ordner importieren

```bash
python3 folder_import.py /path/to/ordner
```

**Beispiel - Einfache Struktur:**
```
076329/
├── auftrag.pdf
├── diagnose.pdf
└── rechnung.pdf
```

```bash
python3 folder_import.py 076329/
```

**Ergebnis:**
```
Archiv/2024/076329/
├── 076329_Auftrag.pdf       ← Seite 1 von auftrag.pdf
└── 076329_Anhang_S2-15.pdf  ← Rest + diagnose + rechnung
```

### 2. Verschachtelte Struktur (2024/73729/)

**Struktur:**
```
Import/
└── 2024/
    ├── 73729/
    │   ├── auftrag.pdf
    │   └── fotos.pdf
    ├── 76329/
    │   └── scan.pdf
    └── 80145/
        ├── werkstatt.pdf
        └── rechnung.pdf
```

**Batch-Import:**
```bash
# Alle Unterordner in 2024/ verarbeiten
for folder in Import/2024/*/; do
    python3 folder_import.py "$folder"
done
```

**ODER mit Script:**
```bash
python3 folder_import.py Import/2024/ --batch
```

### 3. Ohne Auftrag (OA-Modus)

Wenn die PDFs keinen Werkstattauftrag enthalten:

```bash
python3 folder_import.py 076329/ --oa
```

**Ergebnis:**
```
Archiv/2024/076329/
└── 076329_OA_Anhang_S1-10.pdf  ← Alle PDFs kombiniert, nur Schlagwörter
```

## Watch-Modus vs. Ordner-Import

### Watch-Modus (Automatisch)
✅ **Verarbeitet:**
- Einzelne PDFs direkt im Eingangsordner
- Beispiel: `Eingang/scan_076329.pdf`

❌ **Ignoriert:**
- PDFs in Unterordnern
- Beispiel: `Eingang/2024/076329/scan.pdf`
- Ordner (werden nicht automatisch verarbeitet)

**Warum?**
→ Ordner können mehrere PDFs enthalten, die zusammengehören
→ Manuelle Kontrolle für komplexe Strukturen

### Ordner-Import (Manuell)
✅ **Verarbeitet:**
- Ordner mit mehreren PDFs
- Verschachtelte Strukturen (`2024/076329/`)
- Batch-Verarbeitung mehrerer Ordner

**Wann verwenden?**
→ Mehrere PDFs pro Auftrag
→ Strukturierte Daten von externen Quellen
→ Migrationen oder Bulk-Imports

## Praktische Beispiele

### Beispiel 1: Täglicher Scanner-Upload
```
Eingang/
├── scan_morgen_1.pdf    ← Automatisch verarbeitet
├── scan_morgen_2.pdf    ← Automatisch verarbeitet
└── scan_morgen_3.pdf    ← Automatisch verarbeitet
```

**Kein Eingriff nötig** - Watch-Modus übernimmt.

### Beispiel 2: Externe Datenlieferung
```
Eingang/
└── 2024/
    ├── 076329/
    │   ├── auftrag.pdf
    │   ├── diagnose.pdf
    │   └── fotos.pdf
    └── 076330/
        └── komplett.pdf
```

**Manueller Batch-Import:**
```bash
python3 folder_import.py Eingang/2024/ --batch
```

### Beispiel 3: Gemischt
```
Eingang/
├── schnell_076331.pdf         ← Automatisch (Watch)
├── schnell_076332.pdf         ← Automatisch (Watch)
└── komplex/
    └── 076329/
        ├── scan1.pdf          ← Manuell (Ordner-Import)
        └── scan2.pdf
```

**Workflow:**
1. Einzelne PDFs werden automatisch verarbeitet
2. Ordner `komplex/` manuell importieren:
   ```bash
   python3 folder_import.py Eingang/komplex/ --batch
   ```

## Ordner-Struktur Erkennung

Der Ordner-Import erkennt die Auftragsnummer aus:

### Variante 1: Ordnername = Auftragsnummer
```
076329/              ← Auftragsnummer: 076329
├── datei1.pdf
└── datei2.pdf
```

### Variante 2: Mit Präfix/Suffix
```
Auftrag_076329/      ← Auftragsnummer: 076329
076329_komplett/     ← Auftragsnummer: 076329
Kunde_076329_neu/    ← Auftragsnummer: 076329
```

### Variante 3: Verschachtelt
```
2024/076329/         ← Jahr wird ignoriert, Auftragsnummer: 076329
├── scan.pdf
└── anhang.pdf
```

**Wichtig:** Der Ordnername muss mindestens 4-6 Ziffern enthalten!

## Optionen

### --oa (Ohne Auftrag)
```bash
python3 folder_import.py 076329/ --oa
```
→ Keine Metadaten-Extraktion, nur Schlagwörter
→ Dateiname: `076329_OA_Anhang_S1-10.pdf`

### --batch (Mehrere Ordner)
```bash
python3 folder_import.py Import/2024/ --batch
```
→ Verarbeitet alle Unterordner

### --dry-run (Simulation)
```bash
python3 folder_import.py Import/2024/ --batch --dry-run
```
→ Zeigt nur an, was passieren würde (kein Import)

### --no-merge (DEPRECATED)
Diese Option ist veraltet, da PDFs jetzt immer aufgeteilt werden:
- Auftrag-PDF (Seite 1)
- Anhang-PDF (Rest)

## Web-UI Integration

Ordner-Import kann auch über die Web-UI gestartet werden:

1. Navigiere zu **"Einstellungen"**
2. Klicke **"Ordner-Import"**
3. Wähle Ordner aus
4. Optionen setzen (OA-Modus, etc.)
5. Klicke **"Import starten"**

## Fehlerbehandlung

### Problem: Keine Auftragsnummer gefunden
```
❌ Fehler: Keine Auftragsnummer im Ordnername gefunden: Scans/
```

**Lösung:** Ordner umbenennen:
```bash
mv Scans/ 076329/
```

### Problem: PDFs fehlen
```
❌ Fehler: Keine PDF-Dateien im Ordner
```

**Lösung:** Prüfe ob PDFs vorhanden:
```bash
ls -lh 076329/*.pdf
```

### Problem: Ordner bereits verarbeitet
```
⚠️  Auftragsnummer 076329 existiert bereits
```

**Lösung:** System erstellt automatisch Version 2:
```
076329_Auftrag_v2.pdf
```

## Best Practices

### ✅ DO:
- **Einzelne Scans** direkt in Eingang → Automatisch
- **Komplexe Aufträge** in Unterordner → Manuell importieren
- **Batch-Import nachts** für große Datenmengen
- **Dry-Run** vor großen Imports testen

### ❌ DON'T:
- Ordner nicht im Watch-Modus erwarten (werden ignoriert)
- Keine leeren Ordner importieren
- Keine gemischten Auftragsnummern in einem Ordner

## Automatisierung

### Cron-Job für nächtlichen Import
```bash
# Jeden Tag um 2 Uhr: Import von externen Daten
0 2 * * * cd /path/to/archiv && python3 folder_import.py /path/to/import/2024/ --batch
```

### Script für strukturierte Daten
```bash
#!/bin/bash
# import_external.sh

INPUT_DIR="/Volumes/Server/Import"
YEAR=$(date +%Y)

echo "Starte Import für $YEAR..."

# Alle Ordner im aktuellen Jahr verarbeiten
python3 folder_import.py "$INPUT_DIR/$YEAR/" --batch

echo "Import abgeschlossen"
```

## Zusammenfassung

| Szenario | Methode | Befehl |
|----------|---------|--------|
| Einzelne PDF, Eingang | Watch-Modus | Automatisch |
| PDF in Unterordner | Manuell | `python3 main.py --process-input` |
| Ordner mit mehreren PDFs | Ordner-Import | `python3 folder_import.py ordner/` |
| Verschachtelte Struktur | Batch-Import | `python3 folder_import.py root/ --batch` |
| Ohne Auftrag | OA-Modus | `python3 folder_import.py ordner/ --oa` |

**Empfehlung:**
- **Produktiv:** Watch-Modus für tägliche Scans
- **Migrationen:** Batch-Import mit `--dry-run` testen
- **Spezialfälle:** Ordner-Import mit spezifischen Optionen
