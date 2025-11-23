# Datensicherheit - Werkstatt-Archiv

## 🛡️ Implementierte Schutzmaßnahmen

### 1. Papierkorb-System (.trash)

**Keine Daten werden mehr direkt gelöscht!** Stattdessen landen alle gelöschten Ordner im Papierkorb.

**Wo landen Daten im Papierkorb?**
- Beim Verschieben von Aufträgen (Auftragsnummer ändert sich)
- Beim Umbenennen von Ordnern
- Bei verwaisten Ordnern (werden NUR gemeldet, NICHT gelöscht)

**Papierkorb-Struktur:**
```
test_archiv/.trash/
├── 2025-11-23_12-30-45/    # Timestamp des Löschvorgangs
│   └── 075203/             # Gelöschter Ordner
│       ├── data.csv
│       ├── meta.json
│       └── 075203_Auftrag.pdf
└── 2025-11-23_14-15-30/
    └── 076329/
```

### 2. Papierkorb-Verwaltung

**Script: `cleanup_trash.py`**

```bash
# Papierkorb anzeigen
python cleanup_trash.py list

# Ordner wiederherstellen (Nummer aus Liste)
python cleanup_trash.py restore 1

# Papierkorb komplett leeren (mit Bestätigung!)
python cleanup_trash.py empty

# Nur Einträge älter als 30 Tage löschen
python cleanup_trash.py empty --days 30
```

### 3. Automatisches Cleanup deaktiviert

**backup_system.py:**
- Funktion `_cleanup_orphaned_backups()` löscht NICHTS mehr
- Verwaiste Ordner werden nur **protokolliert**
- Du musst manuell entscheiden was gelöscht wird

**Beispiel-Log:**
```
⚠️  Verwaister Backup-Ordner gefunden (NICHT gelöscht): 075203
    → Ordner manuell prüfen: test_archiv/backups/075203
⚠️  1 verwaiste Ordner gefunden. Diese wurden NICHT automatisch gelöscht!
    → Prüfe diese Ordner manuell und lösche sie nur wenn sicher
```

### 4. Verschieben statt Löschen

**Alle Löschvorgänge wurden ersetzt:**

| Datei | Alte Funktion | Neue Funktion |
|-------|--------------|---------------|
| `web_app.py` | `shutil.rmtree(ordner)` | `shutil.move(ordner, .trash/)` |
| `reprocess_auftrag.py` | `old_dir.rmdir()` | `shutil.move(old_dir, .trash/)` |
| `backup_system.py` | `shutil.rmtree(ordner)` | **NUR LOGGING** |

## 📋 Workflow bei gelöschten Daten

### Szenario 1: Auftrag wurde verschoben/umbenannt

1. **Prüfe Papierkorb:**
   ```bash
   python cleanup_trash.py list
   ```

2. **Finde den Ordner:**
   ```
   1. 075203
      Gelöscht am: 2025-11-23_12-30-45
      Größe: 2.45 MB
      Pfad: test_archiv/.trash/2025-11-23_12-30-45/075203
   ```

3. **Wiederherstellen:**
   ```bash
   python cleanup_trash.py restore 1
   ```

### Szenario 2: Daten sind komplett weg

**Mögliche Ursachen:**
- Wurde vor Implementation des Papierkorb-Systems gelöscht
- Manuelle Löschung außerhalb des Systems
- Externe Faktoren (Festplatte, Synchronisation, etc.)

**Lösungen:**
1. Prüfe Original-Scans im Eingangsordner
2. Prüfe Netzwerk-Backups (falls vorhanden)
3. Datei neu scannen und archivieren

## ⚙️ Konfiguration

### Papierkorb automatisch leeren (optional)

Du kannst einen Cron-Job einrichten der alte Einträge löscht:

```bash
# Crontab öffnen
crontab -e

# Jeden Monat am 1. um 3 Uhr: Lösche Einträge älter als 90 Tage
0 3 1 * * cd /pfad/zum/archiv && python cleanup_trash.py empty --days 90
```

### Papierkorb-Größe überwachen

```bash
# Gesamtgröße des Papierkorbs
du -sh test_archiv/.trash

# Anzahl gelöschter Ordner
find test_archiv/.trash -mindepth 2 -maxdepth 2 -type d | wc -l
```

## 🔍 Troubleshooting

### "Papierkorb ist voll"

```bash
# Zeige Größe
python cleanup_trash.py list

# Lösche alte Einträge (z.B. älter als 60 Tage)
python cleanup_trash.py empty --days 60
```

### "Ordner existiert bereits beim Wiederherstellen"

Das bedeutet, dass ein Ordner mit dieser Auftragsnummer schon existiert.

**Lösung:**
1. Manuell verschieben:
   ```bash
   mv test_archiv/.trash/2025-11-23_12-30-45/075203 test_archiv/2024/075203_alt
   ```

2. Oder neuen Ordner umbenennen und alten wiederherstellen

## 📊 Logging

Alle Lösch-/Verschiebevorgänge werden geloggt:

```bash
# Live-Log ansehen
tail -f logs/server.log | grep -E "Papierkorb|trash|gelöscht"
```

**Beispiel-Einträge:**
```
✓ Alter Ordner in Papierkorb verschoben: 075203 → test_archiv/.trash/2025-11-23_12-30-45/075203
  Kann bei Bedarf aus test_archiv/.trash/2025-11-23_12-30-45 wiederhergestellt werden
```

## ⚠️ Wichtige Hinweise

1. **Papierkorb wird NICHT automatisch geleert** - das ist Absicht!
2. **Regelmäßig prüfen** ob wichtige Daten im Papierkorb sind
3. **Backup-System** erstellt keine Kopien vom Papierkorb
4. **Bei Festplattenproblemen** könnte auch der Papierkorb betroffen sein

## 🎯 Best Practices

1. **Wöchentlich Papierkorb prüfen:**
   ```bash
   python cleanup_trash.py list
   ```

2. **Monatlich alte Einträge entfernen:**
   ```bash
   python cleanup_trash.py empty --days 30
   ```

3. **Vor Backup immer prüfen:**
   - Sind wichtige Daten im Papierkorb?
   - Sollen diese wiederhergestellt werden?

4. **Nach großen Änderungen:**
   - Papierkorb prüfen
   - Archiv-Konsistenz prüfen mit:
     ```bash
     python main.py --validate
     ```
