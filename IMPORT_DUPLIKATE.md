# Import und Duplikats-Prüfung - Zusammenfassung

## ✅ Implementiert

### 1. Duplikats-Prüfung beim Import (`backup_system.py`)

Die `_import_records()` Funktion prüft jetzt automatisch:

**Hash-Prüfung (überspringen):**
```
Wenn: Auftragsnummer existiert UND Hash ist identisch
→ Datensatz wird ÜBERSPRUNGEN (identische Datei bereits vorhanden)
```

**Auftragsnummer-Prüfung (warnen):**
```
Wenn: Auftragsnummer existiert ABER Hash ist verschieden
→ WARNUNG im Log, aber Import wird DURCHGEFÜHRT
→ Grund: Kann legitimes Duplikat sein (z.B. v2 mit Anhängen)
```

### 2. Import-Statistik

Nach jedem Import:
```
✓ Import abgeschlossen:
  - Importiert: 45
  - Übersprungen (Hash-Duplikat): 3
  - ⚠️  Duplikate importiert: 2
      → Prüfe mit: python3 manage_duplicates.py list
```

### 3. Detaillierte Logs

**Hash-Match (übersprungen):**
```
⏭  Überspringe 076329: Identische Datei bereits vorhanden (Hash-Match)
```

**Verschiedene Dateien (Warnung + Import):**
```
⚠️  DUPLIKAT: Auftragsnummer 076329 existiert bereits 1x!
    1. ID 12: test_archiv/2024/076329/076329_Auftrag.pdf
    Neue Datei: test_archiv/2024/076329/076329_v2.pdf
    → Wird trotzdem importiert (verschiedene Dateien)
```

## 🔄 Import-Workflow

```
1. CSV-Dateien werden gefunden
2. Für jeden Datensatz:
   ├─ Prüfe: Existiert Auftragsnummer?
   │  ├─ NEIN → Importiere direkt ✓
   │  └─ JA → Prüfe Hash
   │     ├─ Hash identisch → Überspringe ⏭
   │     └─ Hash verschieden → Warne + Importiere ⚠️
3. Statistik ausgeben
4. Hinweis auf manage_duplicates.py bei Duplikaten
```

## 🎯 Warum verschiedene Dateien importiert werden

**Legitime Gründe für unterschiedliche Hashes:**
- Original-Auftrag + Nacharbeit mit Anhängen
- Version mit Diagnose vs. nur Werkstattauftrag
- Ergänzende Dokumente (Rechnung, Protokoll)
- Verschiedene Scan-Zeitpunkte

**→ System entscheidet NICHT automatisch**, sondern importiert und warnt.
**→ Du entscheidest manuell** mit `manage_duplicates.py` was behalten wird.

## 📊 Prüfung nach Import

```bash
# 1. Alle Duplikate anzeigen
python3 manage_duplicates.py list

# 2. Details zu verdächtigen Einträgen
python3 manage_duplicates.py details 076329

# 3. Entscheidung treffen:
#    - Hash identisch? → Ältere Version löschen
#    - Hash verschieden? → Prüfen ob beide relevant
python3 manage_duplicates.py delete <id>
```

## 🛡️ Sicherheit

**Was wird NICHT automatisch gelöscht:**
- Duplikate mit verschiedenen Hashes
- Einträge ohne Hash
- Alte Versionen

**Was wird automatisch übersprungen:**
- Exakt identische Dateien (Hash-Match)

## 🔧 Konfiguration

### Standardverhalten (empfohlen)
```python
# backup_system.py - Zeile 470-520
# Import mit Warnung bei Duplikaten
# Überspringen bei Hash-Match
```

### Strikteres Verhalten (optional)
Falls du Duplikate komplett blockieren willst, ändere in `backup_system.py`:

```python
if existing:
    if file_hash and any(row['hash'] == file_hash for row in existing):
        skipped_hash += 1
        continue
    
    # NEU: Blockiere auch Auftragsnummer-Duplikate
    logger.error(f"FEHLER: Auftragsnummer {auftrag_nr} existiert bereits!")
    stats['errors'] += 1
    continue  # Überspringe Import
```

## 📝 Beispiel-Szenario

**Ausgangslage:**
- DB hat Auftrag 076329 (Hash: abc123...)
- Import findet 076329_v2 (Hash: xyz789...)

**Was passiert:**
```
1. System prüft: 076329 existiert? JA
2. System prüft: Hash identisch? NEIN (abc123 ≠ xyz789)
3. System warnt:
   ⚠️  DUPLIKAT: Auftragsnummer 076329 existiert bereits 1x!
       1. ID 12: test_archiv/2024/076329/076329_Auftrag.pdf
       Neue Datei: test_archiv/2024/076329/076329_v2.pdf
       → Wird trotzdem importiert (verschiedene Dateien)
4. System importiert v2
5. Statistik:
   - Importiert: 1
   - Duplikate importiert: 1
```

**Deine Aktion:**
```bash
python3 manage_duplicates.py details 076329
# Zeigt beide Versionen
# Du entscheidest: Beide behalten oder eine löschen
```

## ✅ Zusammenfassung

**Beim Import werden jetzt:**
1. ✓ Identische Dateien (Hash-Match) übersprungen
2. ✓ Duplikate mit verschiedenen Hashes gewarnt und importiert
3. ✓ Detaillierte Logs geschrieben
4. ✓ Statistik mit Hinweis auf manage_duplicates.py
5. ✓ Keine automatischen Löschungen

**Du behältst die Kontrolle** über alle Duplikate und entscheidest manuell!
