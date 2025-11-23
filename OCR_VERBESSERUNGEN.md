# OCR-Verbesserungen - November 2025

## Übersicht

Die PDF-Erkennung wurde deutlich verbessert, um verschiedene Formulartypen besser zu unterstützen und häufige OCR-Fehler zu kompensieren.

## Durchgeführte Verbesserungen

### 1. VIN-Erkennung für "Fg-Nr:" Pattern ✅

**Problem**: Bei Ford-Formularen steht die VIN hinter "Fg-Nr:" statt "VIN:" oder "Ident-Nr:"

**Lösung**: parser.py:272-278
```python
# Pattern 0: Fg-Nr (Fahrzeugidentnummer - häufig bei Ford)
pattern_fg = r'Fg[._\s-]*Nr[.:]?\s*([A-HJ-NPR-Z0-9]{17})'
match_fg = re.search(pattern_fg, text, re.IGNORECASE)
if match_fg:
    vin = match_fg.group(1).strip()
    if len(vin) == 17 and not vin.isdigit():
        logger.debug(f"VIN gefunden (Fg-Nr): {vin}")
        return vin
```

**Beispiel**:
- Input: `Fg-Nr: WFOJXXGAHJLK14488`
- Output: VIN = `WFOJXXGAHJLK14488`

### 2. Auftragsnummer-Fallback auf Dateinamen ✅

**Problem**: Bei einigen PDFs fehlt die Auftragsnummer im OCR-Text komplett

**Lösung**: parser.py:414-419
```python
# Fallback: Versuche Extraktion aus Dateinamen
if not auftrag_nr and fallback_filename:
    logger.warning("Auftragsnummer nicht im OCR-Text gefunden, versuche Dateinamen-Extraktion...")
    auftrag_nr = extract_auftragsnummer_from_filename(fallback_filename)
    if auftrag_nr:
        logger.info(f"✓ Auftragsnummer aus Dateinamen extrahiert: {auftrag_nr}")
```

**Beispiel**:
- Dateiname: `033520_ohne_kz_Antje_2025-11-17.pdf`
- OCR-Text: "Werkstatt - Auftrag Nr. Datum: 17.11.2025" (Nummer fehlt!)
- Output: Auftragsnummer = `033520` (aus Dateinamen)

### 3. Kennzeichen-Erkennung ohne Bindestrich ✅

**Problem**: OCR erkennt manchmal `DD GU 9705` statt `DD-GU 9705` (Bindestrich fehlt)

**Lösung**: parser.py:237
```python
# Pattern 3: OHNE Bindestrich "DD GU 9705" (OCR-Fehler - Bindestrich fehlt)
r'\b([A-ZÄÖÜ]{1,3})\s+([A-Z]{1,2})\s+(\d{1,4}[EH]?)\b',
```

**Beispiel**:
- Input: `DD GU 9705`
- Output: Kennzeichen = `DD-GU 9705` (normalisiert mit Bindestrich)

### 4. Zusätzliches Auftragsnummer-Pattern ✅

**Lösung**: parser.py:57
```python
# Nach "Seite:" steht manchmal die Auftragsnummer in der vorherigen Zeile
r'(\d{3,6})\s*[\r\n]+\s*Seite:',
```

## Test-Ergebnisse

### Auftrag 033520 (Ford-Formular)

**Vorher**:
- ❌ Auftragsnummer: Nicht erkannt
- ❌ VIN: Nicht erkannt (Fg-Nr: Pattern unbekannt)
- ❌ Kennzeichen: Nicht erkannt (kein Bindestrich)

**Nachher**:
```
✅ Auftragsnummer:    033520 (aus Dateinamen)
✅ Kundennummer:      11049
✅ Name:              Antje Bär Bertheltstr
✅ Datum:             2025-11-17
✅ Kennzeichen:       DD-GU 9705
✅ VIN:               WFOJXXGAHJLK14488
✅ Formularversion:   neu
```

## Formular-Typen

Das System erkennt jetzt automatisch verschiedene Formulartypen:

### NEU (ab ~2024)
- **Erkennungsmerkmal**: Hat Kundennummer (`Kd.Nr.`)
- **Beispiel**: Auftrag 033520
- **Hersteller**: Autohaus Petsch (Ford, ggf. andere)
- **Besonderheiten**:
  - VIN unter "Fg-Nr:" statt "VIN:"
  - Kennzeichen manchmal ohne Bindestrich

### ALT (bis ~2023)
- **Erkennungsmerkmal**: Keine Kundennummer
- **Beispiel**: Auftrag 76329, 78708
- **Hersteller**: Citroen (LOCO-Soft System)
- **Besonderheiten**:
  - RO-Nummer (Repair Order)
  - Auftragsnummern typisch 70000+

## Geänderte Dateien

1. **parser.py** (Hauptdatei)
   - `extract_vin()`: Fg-Nr Pattern hinzugefügt
   - `extract_auftragsnummer()`: Seiten-Pattern hinzugefügt
   - `extract_kennzeichen()`: Pattern ohne Bindestrich hinzugefügt
   - `extract_auftrag_metadata()`: Dateinamen-Fallback aktiviert

## Bekannte Einschränkungen

1. **Name-Extraktion**: Bei mehrzeiligen Namen wird manchmal die Adresse mit erfasst
   - Beispiel: "Antje Bär\nBertheltstr" statt nur "Antje Bär"
   - Kann durch zusätzliche Filterung verbessert werden

2. **Auftragsnummer**: Wenn weder OCR noch Dateiname die Nummer enthalten, schlägt die Verarbeitung fehl
   - Dies ist gewollt als Sicherheitsmechanismus

3. **Kennzeichen-Filter**: False-Positives wie "TH-P" (Motorcode) werden gefiltert
   - Bei neuen Motorcodes muss der Filter erweitert werden

## Nächste Schritte (Optional)

1. **Name-Bereinigung**: Mehrzeilige Namen auf erste Zeile beschränken
2. **Qualitätsscore**: Confidence-Score für jede Extraktion hinzufügen
3. **Formular-Templates**: Für jeden Formulartyp eigene Extraction-Rules
4. **OCR-Qualität**: Preprocessing-Optionen für schlechte Scans (bereits vorhanden in `ocr.py`)

## Verwendung

Die Verbesserungen sind automatisch aktiv. Beim Verarbeiten einer PDF wird jetzt:

1. Zuerst OCR-Text nach Auftragsnummer durchsucht
2. Falls nicht gefunden: Dateiname als Fallback verwendet
3. VIN mit allen Patterns gesucht (inkl. Fg-Nr)
4. Kennzeichen mit und ohne Bindestrich erkannt
5. Formulartyp automatisch erkannt

**Test-Befehl**:
```bash
python3 -c "
from pathlib import Path
from ocr import pdf_to_ocr_texts
from parser import extract_auftrag_metadata

pdf = Path('test_archiv/2025/033520/033520_ohne_kz_Antje_2025-11-17.pdf')
texts = pdf_to_ocr_texts(pdf, max_pages=1)
metadata = extract_auftrag_metadata(texts[0], fallback_filename=pdf.name)
print(metadata)
"
```

---

**Datum**: 2025-11-23
**Autor**: Claude Code
**Status**: Produktiv
