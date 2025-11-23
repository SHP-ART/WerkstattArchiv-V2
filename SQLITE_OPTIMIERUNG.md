# SQLite Netzwerk-Optimierungen

## ⚡ Performance-Verbesserungen für Netzwerkspeicher

Die Datenbank wurde für die Verwendung auf Netzwerkspeichern (NAS/SMB/NFS) optimiert.

## 🔧 Implementierte Optimierungen

### 1. **WAL-Modus (Write-Ahead Logging)**
```python
PRAGMA journal_mode=WAL
```
- ✅ Bessere Concurrency (mehrere Leser gleichzeitig)
- ✅ Weniger Netzwerk-Roundtrips
- ✅ Schnellere Schreiboperationen
- **Hinweis**: Erstellt `-wal` und `-shm` Dateien neben der `.db`

### 2. **Reduzierte Synchronisation**
```python
PRAGMA synchronous=NORMAL
```
- ✅ Schneller auf Netzwerk (weniger fsync-Aufrufe)
- ✅ Sicher genug für moderne Dateisysteme
- ⚠️ Bei Stromausfall: Nur letzter Commit gefährdet

### 3. **Großer Cache (64 MB)**
```python
PRAGMA cache_size=-64000
```
- ✅ Weniger Netzwerk-Zugriffe
- ✅ Häufig genutzte Daten im RAM
- ✅ Schnellere Suchen

### 4. **Memory-Mapped I/O (256 MB)**
```python
PRAGMA mmap_size=268435456
```
- ✅ Direkter Speicherzugriff ohne Kopieren
- ✅ Sehr schnell für Lesezugriffe
- ⚠️ Benötigt genug RAM

### 5. **Temp-Daten im RAM**
```python
PRAGMA temp_store=MEMORY
```
- ✅ Temporäre Tabellen nicht auf Netzwerk
- ✅ Schnellere JOIN-Operationen

### 6. **Längere Timeouts**
```python
timeout=30.0
PRAGMA busy_timeout=30000
```
- ✅ Keine Fehler bei kurzen Netzwerk-Verzögerungen
- ✅ Bessere Multi-User-Unterstützung

## 📊 Erwartete Performance-Verbesserungen

### Vorher (Standard SQLite):
- Suche: ~500-1000ms auf Netzwerk
- Einfügen: ~200-500ms
- Timeout-Fehler bei gleichzeitigen Zugriffen

### Nachher (Optimiert):
- Suche: ~100-300ms auf Netzwerk (2-3x schneller)
- Einfügen: ~50-150ms (3-4x schneller)
- Robuster bei Netzwerk-Latenzen

## 🔍 Performance Testen

### Benchmark-Befehl:
```bash
python3 -c "
import time
from pathlib import Path
from db import search_by_auftrag_nr

db_path = Path('test_archiv/werkstatt.db')
start = time.time()
results = search_by_auftrag_nr(db_path, '76329')
elapsed = (time.time() - start) * 1000
print(f'Suche dauerte: {elapsed:.1f}ms')
"
```

### Live-Monitoring:
```bash
# SQLite-Statistiken anzeigen
python3 test_db_performance.py
```

## ⚠️ Wichtige Hinweise

### WAL-Dateien
Nach Aktivierung von WAL-Modus entstehen zusätzliche Dateien:
```
werkstatt.db       (Haupt-Datenbank)
werkstatt.db-wal   (Write-Ahead Log)
werkstatt.db-shm   (Shared Memory)
```

**WICHTIG**: Alle 3 Dateien müssen gemeinsam gesichert werden!

### Backup mit WAL:
```bash
# Checkpoint vor Backup (schreibt WAL in DB)
sqlite3 werkstatt.db "PRAGMA wal_checkpoint(TRUNCATE);"

# Dann Backup erstellen
python3 main.py --backup
```

### Deaktivieren bei Problemen:
Falls Probleme mit WAL-Modus auf Ihrem Netzwerk:
```python
# In db.py, Zeile 53 ändern:
cursor.execute('PRAGMA journal_mode=DELETE')  # Statt WAL
```

## 🔧 Weitere Optimierungen (Optional)

### Connection Pooling
Für Web-UI mit vielen gleichzeitigen Nutzern:
```python
# requirements.txt ergänzen:
# sqlalchemy

# Dann in web_app.py:
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

engine = create_engine(
    f'sqlite:///{db_path}',
    poolclass=QueuePool,
    pool_size=5,
    max_overflow=10
)
```

### Read-Only Replika (Fortgeschritten)
Für sehr hohe Last:
```bash
# Haupt-DB auf Netzwerk
/Volumes/Server/Archiv/werkstatt.db (R/W)

# Lokale Replika für Suchen
/Users/user/werkstatt.db.local (R/O)

# Regelmäßig synchronisieren
rsync -av /Volumes/Server/Archiv/werkstatt.db* ~/
```

## 📈 Monitoring

### Statistiken anzeigen:
```bash
python3 -c "
import sqlite3
conn = sqlite3.connect('test_archiv/werkstatt.db')
stats = conn.execute('PRAGMA compile_options').fetchall()
print('SQLite-Optionen:', stats)
print()
print('Journal-Modus:', conn.execute('PRAGMA journal_mode').fetchone()[0])
print('Cache-Größe:', conn.execute('PRAGMA cache_size').fetchone()[0])
print('Sync-Modus:', conn.execute('PRAGMA synchronous').fetchone()[0])
"
```

### Datenbankgröße prüfen:
```bash
# Haupt-DB + WAL
du -sh test_archiv/werkstatt.db*
```

## 🆘 Troubleshooting

### Problem: "database is locked"
**Lösung**: Timeout erhöhen in `_get_optimized_connection()`:
```python
conn = sqlite3.connect(db_path, timeout=60.0)  # 60 Sekunden
```

### Problem: WAL-Datei wächst sehr groß
**Lösung**: Automatisches Checkpoint:
```python
# In db.py nach jeder Transaction:
conn.execute('PRAGMA wal_checkpoint(PASSIVE)')
```

### Problem: Zu viel RAM-Verbrauch
**Lösung**: Cache/MMAP reduzieren:
```python
cursor.execute('PRAGMA cache_size=-32000')  # 32MB statt 64MB
cursor.execute('PRAGMA mmap_size=0')  # MMAP deaktivieren
```

## ✅ Checkliste für Migration

- [x] Optimierungen in `db.py` implementiert
- [ ] Datenbank-Backup erstellen (vor Migration)
- [ ] Server neu starten (WAL-Modus aktivieren)
- [ ] Performance testen (`test_db_performance.py`)
- [ ] Backup-Skript anpassen (WAL-Dateien inkludieren)
- [ ] Monitoring aktivieren

## 📚 Weiterführende Informationen

- [SQLite WAL-Modus](https://www.sqlite.org/wal.html)
- [PRAGMA Befehle](https://www.sqlite.org/pragma.html)
- [SQLite auf Netzwerk](https://www.sqlite.org/useovernet.html)
