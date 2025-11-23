# Backup & Restore System - Werkstatt-Archiv

## Überblick

Robustes Backup-System, das die Datenbank in jeden Auftrag-Ordner repliziert. Schützt vor totalem Datenverlust durch verteilte CSV-Backups mit Checksummen-Validierung.

## Architektur

```
Archiv/
├── 2024/
│   ├── 076329/
│   │   ├── 076329_Auftrag.pdf          # Original-PDF
│   │   ├── data.csv                     # ← Backup der DB-Daten
│   │   └── meta.json                    # ← Checksumme + Metadaten
│   └── 076330/
│       ├── 076330_Auftrag.pdf
│       ├── data.csv
│       └── meta.json
└── werkstatt.db                         # ← Haupt-Datenbank
```

## Dateiformate

### data.csv
```csv
record_id,auftrag_nr,kunde_name,kunden_nr,kennzeichen,vin,datum,formular_version,keywords_json,file_path,hash,data_complete,created_at,updated_at
12,076329,Müller,K12345,B-AB 1234,WVW1234567890,2024-07-29,neu,"{\"Garantie\": [2]}",test_archiv/2024/076329/076329_Auftrag.pdf,abc123...,1,2024-07-29T10:00:00,2024-07-29T10:00:00
```

**Kodierung:** UTF-8  
**Format:** CSV mit Header, Komma-separiert  
**Escape:** Anführungszeichen verdoppelt (`""`)

### meta.json
```json
{
  "schema_version": "1.0",
  "checksum": "abc123def456...",
  "exported_at": "2024-07-29T10:30:00",
  "auftrag_nr": "076329",
  "record_id": 12,
  "file_size": 1024
}
```

## Verwendung

### 1. Export (Backup erstellen)

```bash
# Alle Aufträge sichern
python3 backup_system.py export --config .archiv_config.json

# Mit expliziten Pfaden
python3 backup_system.py export --db ./test_archiv/werkstatt.db --archiv ./test_archiv
```

**Was passiert:**
- Alle Datensätze aus `auftraege`-Tabelle werden gelesen
- Für jeden Auftrag wird `data.csv` + `meta.json` im Ordner erstellt
- Atomares Schreiben über temporäre Datei (`.tmp.csv`)
- Checksumme wird berechnet und in `meta.json` gespeichert
- Lock-Datei verhindert parallele Zugriffe

**Cronjob (täglich um 2 Uhr):**
```bash
# crontab -e
0 2 * * * cd /pfad/zum/archiv && /usr/bin/python3 backup_system.py export >> /var/log/backup.log 2>&1
```

### 2. Verify (Integrität prüfen)

```bash
# Alle CSV-Dateien validieren (ohne DB-Import)
python3 backup_system.py verify --config .archiv_config.json
```

**Was passiert:**
- Rekursiv alle `data.csv` Dateien finden
- Checksumme mit `meta.json` abgleichen
- Schema-Version prüfen
- Datenvalidierung (Pflichtfelder, Formate)
- Duplikate erkennen

### 3. Restore (Datenbank wiederherstellen)

```bash
# Datenbank aus CSV-Dateien wiederherstellen
python3 backup_system.py restore --config .archiv_config.json
```

**⚠️ ACHTUNG:** Löscht die bestehende Datenbank!

**Was passiert:**
- Bestehende `auftraege`-Tabelle wird gelöscht
- Neue leere Tabelle mit Schema wird erstellt
- Alle `data.csv` Dateien werden gefunden und validiert
- Duplikats-Strategie: Neueste Version (nach `updated_at`) gewinnt
- Import in Transaktion (bei Fehler: kompletter Rollback)

## Sicherheitsmechanismen

### 1. Atomares Schreiben
```python
# Niemals direkt data.csv überschreiben!
data.tmp.csv  →  Schreiben + Checksumme
              →  Umbenennen zu data.csv (atomar)
```

### 2. Lock-Datei
```
.backup.lock  →  PID + Timestamp
              →  Verhindert parallele Prozesse
              →  Timeout nach 30 Sekunden
```

### 3. Transaktionen
```python
try:
    cursor.execute(INSERT ...)
    cursor.execute(INSERT ...)
    conn.commit()  # Alles oder nichts
except:
    conn.rollback()  # Bei Fehler: Zurückrollen
```

### 4. Validierung
- **Checksumme:** SHA256 über `data.csv`
- **Pflichtfelder:** `auftrag_nr`, `file_path`
- **Datentypen:** Datum als `YYYY-MM-DD`, Auftragsnummer 6-stellig
- **Schema-Version:** Migrationslogik für zukünftige Änderungen

## Duplikats-Strategie

**Problem:** Mehrere CSV-Dateien mit gleicher `record_id`

**Lösung:**
```python
if record_id in records_by_id:
    existing = records_by_id[record_id]
    if record['updated_at'] > existing['updated_at']:
        # Neuere Version überschreibt
        records_by_id[record_id] = record
    else:
        # Ältere Version ignorieren
        pass
```

**Logik:** Die Datei mit dem neuesten `updated_at` Timestamp gewinnt.

## Schema-Migration

**Aktuell:** `schema_version = "1.0"`

**Zukünftige Änderungen:**

```python
def migrate_v1_to_v2(record: Dict) -> Dict:
    """Migriert von Schema 1.0 zu 2.0"""
    if record.get('schema_version') == '1.0':
        # Beispiel: Neues Feld hinzufügen
        record['neue_spalte'] = 'Standardwert'
        record['schema_version'] = '2.0'
    return record

# In _load_and_validate_csv():
if schema_version != CURRENT_SCHEMA_VERSION:
    if schema_version == '1.0' and CURRENT_SCHEMA_VERSION == '2.0':
        record = migrate_v1_to_v2(record)
    else:
        raise ValidationError(f"Keine Migration von {schema_version}")
```

## Fehlerbehandlung

### Logging

**Logfile:** `backup_system.log`  
**Format:** `YYYY-MM-DD HH:MM:SS - NAME - LEVEL - MESSAGE`

**Beispiel:**
```
2024-07-29 10:30:15 - __main__ - INFO - Starte Export aller Aufträge...
2024-07-29 10:30:16 - __main__ - DEBUG - ✓ Exportiert: 076329 → data.csv
2024-07-29 10:30:17 - __main__ - ERROR - Fehler bei Auftrag 076330: Checksumme ungültig
2024-07-29 10:30:20 - __main__ - INFO - Export abgeschlossen: 150 erfolgreich, 2 Fehler
```

### Fehler-Typen

| Exception | Bedeutung | Lösung |
|-----------|-----------|--------|
| `LockError` | Lock-Timeout | Warten oder alten Lock löschen |
| `ValidationError` | Daten ungültig | CSV/DB-Daten korrigieren |
| `BackupSystemError` | Allgemeiner Fehler | Log prüfen |

## Produktiv-Nutzung

### Docker-Integration

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY backup_system.py .
COPY .archiv_config.json .

# Cronjob installieren
RUN apt-get update && apt-get install -y cron
RUN echo "0 2 * * * python3 /app/backup_system.py export >> /var/log/backup.log 2>&1" | crontab -

CMD ["cron", "-f"]
```

```bash
docker build -t werkstatt-backup .
docker run -v /pfad/zum/archiv:/app/archiv werkstatt-backup
```

### Monitoring

```bash
# Prüfe letzten Backup-Status
tail -100 backup_system.log | grep "Export abgeschlossen"

# Alert bei Fehlern (Slack/Email)
if grep -q "ERROR" backup_system.log; then
    echo "Backup-Fehler!" | mail -s "Werkstatt-Archiv Alert" admin@werkstatt.de
fi
```

### Netzwerk-Ordner (SMB/NFS)

```bash
# Mount Netzwerk-Ordner
mount -t cifs //server/archiv /mnt/archiv -o username=user,password=pass

# Backup auf Netzwerk
python3 backup_system.py export --archiv /mnt/archiv
```

## Performance

**Typische Zeiten (1000 Aufträge):**
- **Export:** ~30 Sekunden (CSV schreiben + Checksummen)
- **Verify:** ~20 Sekunden (Checksummen prüfen, kein DB-Zugriff)
- **Restore:** ~45 Sekunden (CSV lesen + DB-Import)

**Optimierung:**
- Parallelisierung mit `multiprocessing` (Export/Verify)
- Batch-Inserts (1000 Records auf einmal)
- SQLite `PRAGMA journal_mode = WAL` (schnellere Writes)

## Best Practices

✅ **Export täglich um 2 Uhr** (geringe Last)  
✅ **Verify wöchentlich** (Integrität prüfen)  
✅ **Restore nur bei Disaster** (Datenverlust)  
✅ **Log-Rotation** (`logrotate` für `backup_system.log`)  
✅ **Monitoring** (Alert bei Fehlern)  
✅ **Test-Restore** (monatlich in Test-Umgebung)

❌ **Nicht:** Export während Verarbeitung (Race Conditions)  
❌ **Nicht:** Lock-Datei manuell löschen (nur bei Timeout)  
❌ **Nicht:** CSV manuell editieren (Checksumme ungültig)

## Disaster Recovery

**Szenario:** Server-Crash, Datenbank verloren

```bash
# 1. Neues System aufsetzen
python3 web_app.py --port 8080  # Erstellt leere DB

# 2. Backup-Ordner mounten
mount -t cifs //backup-server/archiv /mnt/archiv

# 3. Datenbank wiederherstellen
python3 backup_system.py restore --archiv /mnt/archiv

# 4. Verify
python3 backup_system.py verify --archiv /mnt/archiv

# 5. Web-UI starten
python3 web_app.py --port 8080
```

**Ergebnis:** Alle Aufträge wiederhergestellt (mit letztem Stand)

## Zusammenfassung

| Feature | Status |
|---------|--------|
| CSV-Backup in jedem Ordner | ✅ |
| Checksummen-Validierung | ✅ |
| Atomares Schreiben | ✅ |
| Lock-Mechanismus | ✅ |
| Transaktionale DB-Operationen | ✅ |
| Schema-Versionierung | ✅ |
| Duplikats-Erkennung | ✅ |
| Logging + Fehlerbehandlung | ✅ |
| Cronjob-fähig | ✅ |
| Docker-ready | ✅ |

**➜ Production-Ready Backup-System für kritische Werkstatt-Daten!**
