# Datenschutz und Sicherheit

## 🔒 Keine sensiblen Daten auf GitHub

Dieses Repository enthält **ausschließlich Code**. Folgende Daten werden **NIEMALS** hochgeladen:

### ❌ Wird NICHT auf GitHub hochgeladen:
- ✗ PDF-Dateien (Werkstattaufträge, Rechnungen, Diagnosen)
- ✗ Datenbanken (`.db`, `.sqlite`) mit Kundendaten
- ✗ Konfigurationsdateien (`.archiv_config.json`) mit lokalen Pfaden
- ✗ CSV-Exporte (`kunden_index.csv`) mit Kundenlisten
- ✗ Backup-Dateien (`.zip`) des Archivs
- ✗ Log-Dateien (`logs/*.log`)
- ✗ Temporäre Dateien und Cache
- ✗ Papierkorb/Trash-Ordner (`.trash/`)

### ✅ Wird auf GitHub hochgeladen:
- ✓ Python-Code (`.py`-Dateien)
- ✓ Dokumentation (`.md`-Dateien)
- ✓ Skripte (`.sh`, `.bat`-Dateien)
- ✓ Abhängigkeiten (`requirements.txt`)
- ✓ Beispiel-Konfiguration (in Dokumentation)

## 🛡️ Schutzmaßnahmen

### .gitignore
Die `.gitignore`-Datei verhindert automatisch, dass sensible Daten committet werden:

```gitignore
# Archiv-Ordner
archiv/
test_archiv/

# Datenbanken
*.db
*.sqlite

# Konfiguration
.archiv_config.json

# CSV-Exporte
kunden_index.csv

# Backups
*.zip
backups/

# Logs
logs/
*.log
```

### Vor dem Push prüfen
Verwenden Sie diese Befehle, um zu prüfen, was hochgeladen wird:

```bash
# Zeige alle Dateien, die für Commit vorgemerkt sind
git status

# Zeige ignorierte Dateien (sollte archiv/, *.db, etc. enthalten)
git status --ignored

# Prüfe, ob sensible Dateien dabei sind
git diff --cached --name-only
```

## ⚠️ Sicherheitsrichtlinien

### Falls versehentlich sensible Daten hochgeladen wurden:

1. **SOFORT** das Repository auf privat setzen
2. **NICHT** einfach die Dateien löschen (History bleibt!)
3. **Git-History bereinigen**:
   ```bash
   # BFG Repo-Cleaner verwenden
   bfg --delete-files "*.db" --delete-folders archiv
   
   # Oder git filter-branch
   git filter-branch --force --index-filter \
     "git rm --cached --ignore-unmatch archiv/*.pdf" \
     --prune-empty --tag-name-filter cat -- --all
   ```
4. **Force-Push** (überschreibt Remote):
   ```bash
   git push origin --force --all
   ```

### Empfohlene Vorgehensweise

1. **Repository als PRIVAT erstellen** (falls mit sensiblen Daten gearbeitet wird)
2. **Vor dem ersten Push**: `git status --ignored` prüfen
3. **Regelmäßig**: `.gitignore` auf Vollständigkeit prüfen
4. **Team schulen**: Keine Testdaten mit echten Kundennamen/Kennzeichen

## 📋 DSGVO-Konformität

### Lokale Datenhaltung
- Alle Kundendaten bleiben auf **lokalem Server/NAS**
- Keine Cloud-Synchronisation (außer explizit gewünscht)
- Zugriff nur über lokales Netzwerk

### Empfohlene Maßnahmen
1. **Verschlüsselung**: FileVault (macOS) / BitLocker (Windows) für Festplatten
2. **Netzwerksicherheit**: VPN für Remote-Zugriff, keine öffentliche Erreichbarkeit
3. **Backups**: Verschlüsselte externe Festplatte
4. **Zugangskontrolle**: Passwortschutz für Server/NAS

## 🚨 Schwachstellen melden

Falls Sie Sicherheitslücken im Code entdecken:
- **NICHT** als öffentliches Issue posten
- **E-Mail** an Repository-Maintainer
- Beschreiben Sie das Problem detailliert
- Geben Sie Reproduktionsschritte an

## ✅ Checkliste vor GitHub-Push

- [ ] `git status --ignored` prüfen → Archiv/DB sollten ignoriert sein
- [ ] Keine `.db`-Dateien in `git status`
- [ ] Keine PDF-Dateien in `git status`
- [ ] `.archiv_config.json` ist in `.gitignore`
- [ ] Keine echten Kundennamen in Code-Kommentaren
- [ ] Keine Passwörter/API-Keys im Code

## 📞 Support

Bei Fragen zur Datensicherheit:
- Erstellen Sie ein Issue auf GitHub (für allgemeine Fragen)
- Kontaktieren Sie den Maintainer direkt (für sensible Themen)
