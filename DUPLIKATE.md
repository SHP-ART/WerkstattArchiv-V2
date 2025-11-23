# Umgang mit doppelten Auftragsnummern

## 📋 Aktuelle Situation

**Das System erlaubt standardmäßig doppelte Auftragsnummern!**

Dies ist **absichtlich** so, da legitime Gründe für Duplikate existieren:
- Nacharbeiten/Garantie-Aufträge mit gleicher Nummer
- Verschiedene Versionen eines Auftrags (mit unterschiedlichen Anhängen)
- Ergänzende Dokumente zum selben Auftrag

## ⚠️ Warnsystem

### Bei der Archivierung

Wenn eine PDF mit bereits existierender Auftragsnummer archiviert wird:

```
⚠️  ACHTUNG: Auftragsnummer 076329 wird DOPPELT gespeichert!
   Existierende Einträge: 1
   Neue Datei: test_archiv/2024/076329/076329_v2.pdf
✓ Auftrag als Duplikat gespeichert: ID 15, Auftragsnr. 076329 (Vorkommen: 2)
```

### Im Log

```bash
tail -f logs/server.log | grep "DOPPELT"
```

## 🔍 Duplikate finden

### Tool: manage_duplicates.py

```bash
# Alle Duplikate auflisten
python3 manage_duplicates.py list

# Details zu einer Auftragsnummer
python3 manage_duplicates.py details 076329

# DB-Eintrag löschen (Datei bleibt!)
python3 manage_duplicates.py delete 42
```

### Beispiel-Ausgabe

```
================================================================================
  DOPPELTE AUFTRAGSNUMMERN
================================================================================

Gefunden: 2 verschiedene Auftragsnummern mit insgesamt 6 Einträgen

📋 Auftragsnummer: 076329 (3x vorhanden)
--------------------------------------------------------------------------------
  1. ID: 12 ✓
     Datei: test_archiv/2024/076329/076329_Auftrag.pdf
     Größe: 245.3 KB
     Kunde: Müller GmbH
     Datum: 2024-07-15
     Kennzeichen: B-MW-1234
     Hash: a3f5b8c2d9e1f4a7...
     Erstellt: 2025-01-15T10:30:00
     
  2. ID: 15 ✓
     Datei: test_archiv/2024/076329/076329_v2.pdf
     Größe: 287.1 KB
     Kunde: Müller GmbH
     Datum: 2024-07-15
     Kennzeichen: B-MW-1234
     Hash: 7b2e9f3c5a8d1b4f...
     Erstellt: 2025-01-20T14:45:00
```

## 🎯 Entscheidungshilfe

### Legitime Duplikate

**Behalten** wenn:
- Verschiedene Hashes → unterschiedliche Dateien
- Unterschiedliche Datumsangaben
- Verschiedene Anhänge (Diagnose, Rechnung, etc.)
- Nacharbeiten/Garantie-Dokumente

**Beispiel:**
```
076329_Auftrag.pdf        # Original-Werkstattauftrag
076329_v2.pdf             # Mit Rechnung und Diagnose
```

### Echte Duplikate (sollten entfernt werden)

**Löschen** wenn:
- Identische Hashes → exakt gleiche Datei
- Datei fehlt (✗ FEHLT)
- Offensichtlich aus Versehen doppelt archiviert

**Vorgehen:**
```bash
# 1. Details ansehen
python3 manage_duplicates.py details 076329

# 2. Entscheiden welcher Eintrag weg soll

# 3. DB-Eintrag löschen
python3 manage_duplicates.py delete 12

# 4. Datei prüfen und ggf. in Papierkorb
mv test_archiv/2024/076329/076329_Auftrag.pdf test_archiv/.trash/manual/
```

## 🛡️ Duplikate verhindern

### Option 1: Warnung ignorieren (Standard)

```python
# In main.py oder web_app.py
auftrag_id = db.insert_auftrag(
    db_path,
    metadata,
    keywords_found,
    target_path,
    file_hash,
    allow_duplicate=True  # Standard
)
```

**Warnung wird geloggt, aber Auftrag wird gespeichert**

### Option 2: Duplikate verbieten (strikt)

```python
auftrag_id = db.insert_auftrag(
    db_path,
    metadata,
    keywords_found,
    target_path,
    file_hash,
    allow_duplicate=False  # Fehler bei Duplikat
)
```

**Wirft DatabaseError** → Datei landet in Fehlerordner

### Option 3: Vor Archivierung prüfen

```python
# Vor archive.move_to_archive()
existing = db.check_duplicate_auftrag_nr(db_path, auftrag_nr)

if existing:
    # Entscheidung: Überschreiben, Versionieren, Abbrechen?
    pass
```

## 📊 Statistiken

### Datenbank-Query

```bash
# Anzahl Duplikate
sqlite3 test_archiv/werkstatt.db "
SELECT COUNT(*) as duplikate
FROM (
    SELECT auftrag_nr, COUNT(*) as count
    FROM auftraege
    GROUP BY auftrag_nr
    HAVING count > 1
);"
```

### Python-Script

```python
import config
import db

cfg = config.Config()
duplicates = db.check_duplicate_auftrag_nr(cfg.get_db_path(), "076329")
print(f"Auftragsnummer 076329: {len(duplicates)} Einträge")
```

## 🔄 Workflow bei Duplikaten

### Szenario 1: Neuer Auftrag mit existierender Nummer

1. **System warnt** im Log
2. **Prüfe** ob legitim (Nacharbeit, neue Version)
3. **Behalte** wenn legitim, sonst:
   ```bash
   python3 manage_duplicates.py details 076329
   python3 manage_duplicates.py delete <alte_id>
   ```

### Szenario 2: Beim Backup/Import

**Automatische Prüfung beim Import:**

Das System prüft beim Restore automatisch:

1. **Hash-Duplikate** werden übersprungen:
   ```
   ⏭  Überspringe 076329: Identische Datei bereits vorhanden (Hash-Match)
   ```

2. **Auftragsnummer-Duplikate** werden gewarnt:
   ```
   ⚠️  DUPLIKAT: Auftragsnummer 076329 existiert bereits 1x!
       1. ID 12: test_archiv/2024/076329/076329_Auftrag.pdf
       Neue Datei: test_archiv/2024/076329/076329_v2.pdf
       → Wird trotzdem importiert (verschiedene Dateien)
   ```

3. **Nach Import prüfen:**
   ```bash
   python3 manage_duplicates.py list
   ```

**Import-Statistik:**
```
✓ Import abgeschlossen:
  - Importiert: 45
  - Übersprungen (Hash-Duplikat): 3
  - ⚠️  Duplikate importiert: 2
      → Prüfe mit: python3 manage_duplicates.py list
```

### Szenario 3: Regelmäßige Wartung

```bash
# Monatlich ausführen
python3 manage_duplicates.py list > duplikate_$(date +%Y-%m).txt

# Liste durchgehen und Entscheidungen treffen
```

## ⚙️ Konfiguration

### Automatische Versionierung nutzen

Statt Duplikate zu erlauben, nutze die **Versionierungs-Funktion**:

```python
# archive.py erstellt automatisch _v2, _v3 etc.
target_filename = generate_target_filename(
    auftrag_nr,
    config,
    existing_files,  # Prüft existierende Dateien
    metadata
)
```

**Ergebnis:**
```
076329_Auftrag.pdf       # Erste Version
076329_Auftrag_v2.pdf    # Zweite Version (automatisch)
076329_Auftrag_v3.pdf    # Dritte Version
```

**Vorteil:** Keine DB-Duplikate, aber alle Versionen archiviert!

### Dateiname-Muster anpassen

In `.archiv_config.json`:

```json
{
  "dateiname_pattern": "{auftrag_nr}_{name}_{datum}{version_suffix}.pdf"
}
```

Mit `{version_suffix}` werden automatisch `_v2`, `_v3` etc. angehängt.

## 📝 Best Practices

1. **Duplikate erlauben** (Standard) - für Flexibilität
2. **Wöchentlich prüfen:**
   ```bash
   python3 manage_duplicates.py list
   ```
3. **Dokumentieren** warum Duplikate legitim sind (z.B. in Notiz-Feld)
4. **Vor Backup aufräumen** - verhindert unnötige Datenmenge
5. **Hash-Vergleich** nutzen um echte Duplikate zu erkennen

## 🔍 Troubleshooting

### "Ich sehe Duplikate aber sie sind berechtigt"

→ Nichts tun! Das ist OK. Dokumentiere ggf. im System warum.

### "Ich will Duplikate komplett verhindern"

→ Setze `allow_duplicate=False` in `main.py` und `web_app.py`

### "Wie finde ich alle Duplikate mit identischem Hash?"

```bash
sqlite3 test_archiv/werkstatt.db "
SELECT auftrag_nr, hash, COUNT(*) as count
FROM auftraege
WHERE hash IS NOT NULL
GROUP BY hash
HAVING count > 1
ORDER BY count DESC;
"
```

### "Duplikat wurde versehentlich erstellt"

```bash
# Finde IDs
python3 manage_duplicates.py details 076329

# Lösche falschen Eintrag
python3 manage_duplicates.py delete <id>

# Datei in Papierkorb
mv <pfad> test_archiv/.trash/manual/
```

## 📚 Siehe auch

- `DATENSICHERHEIT.md` - Papierkorb-System
- `BACKUP_SYSTEM_README.md` - Backup mit Duplikats-Erkennung
- `db.py` - Datenbank-Funktionen `check_duplicate_auftrag_nr()`
