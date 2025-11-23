# GitHub Vorbereitung - Anleitung

## ✅ Was wurde vorbereitet

Das Repository ist jetzt bereit für GitHub. Alle sensiblen Daten sind geschützt:

### 📋 Erstellte Dateien:
- ✅ `.gitignore` - Verhindert Upload sensibler Daten
- ✅ `LICENSE` - MIT-Lizenz für Open Source
- ✅ `SECURITY.md` - Datenschutz- und Sicherheitsrichtlinien
- ✅ `README.md` - Aktualisiert mit Sicherheitshinweis

### 🔒 Geschützte Daten (werden NICHT hochgeladen):
- ✅ `.archiv_config.json` - Konfiguration mit lokalen Pfaden
- ✅ `test_archiv/` - Archiv-Ordner mit PDFs
- ✅ `*.db` - Datenbanken mit Kundendaten
- ✅ `kunden_index.csv` - CSV-Export mit Kundenlisten
- ✅ `logs/` - Log-Dateien
- ✅ `backups/` - Backup-ZIP-Dateien
- ✅ `.trash/` - Papierkorb-Ordner

## 🚀 Schritt-für-Schritt: Auf GitHub hochladen

### 1. Repository auf GitHub erstellen

1. Gehe zu https://github.com/new
2. Repository-Name: `Werkstatt-Archiv`
3. Beschreibung: `Automatische Archivierung von Werkstatt-PDF-Aufträgen mit OCR`
4. **Sichtbarkeit wählen**:
   - **Public** (Öffentlich) ✅ EMPFOHLEN - nur Code, keine sensiblen Daten
   - **Private** (Privat) - wenn Sie extra sicher sein möchten
5. **NICHT** README, .gitignore oder License hinzufügen (haben wir schon!)
6. Klicke "Create repository"

### 2. Lokales Repository mit GitHub verbinden

```bash
# Alle Dateien für Commit vorbereiten
git add .

# Überprüfen: Sind sensible Dateien dabei?
git status

# Sollte zeigen:
# - .gitignore, README.md, *.py, *.bat, *.sh → ✅ GUT
# - NICHT: .archiv_config.json, *.db, test_archiv/ → ✅ IGNORIERT

# Ignorierte Dateien anzeigen (zur Sicherheit)
git status --ignored | grep -E "(archiv_config|test_archiv|\.db|logs)"

# Sollte zeigen:
#   .archiv_config.json
#   test_archiv/
#   werkstatt.db
#   logs/

# Ersten Commit erstellen
git commit -m "Initial commit: Werkstatt-Archiv mit OCR und Web-UI"

# Remote-Repository hinzufügen (URL von GitHub kopieren)
git remote add origin https://github.com/IHR_USERNAME/Werkstatt-Archiv.git

# Hochladen zu GitHub
git push -u origin main
```

### 3. Überprüfung auf GitHub

Nach dem Push:
1. Öffne https://github.com/IHR_USERNAME/Werkstatt-Archiv
2. **Prüfe**: Sind nur Code-Dateien sichtbar? ✅
3. **Prüfe**: Keine `.archiv_config.json` oder `test_archiv/`? ✅
4. **Prüfe**: README.md wird angezeigt mit Sicherheitshinweis? ✅

## ⚠️ Wichtige Sicherheitschecks

### Vor jedem Push:

```bash
# 1. Status prüfen
git status

# 2. Diff anzeigen (was wird hochgeladen?)
git diff --cached --name-only

# 3. Ignorierte Dateien überprüfen
git status --ignored | head -30

# 4. Suche nach sensiblen Strings im Code
grep -r "C:/Archiv" *.py *.md  # Sollte nur in Beispielen vorkommen
grep -r "76329" *.py *.md      # Sollte keine echten Auftragsnummern zeigen
```

### Falls versehentlich sensible Daten gepusht:

```bash
# 1. SOFORT: Repository auf GitHub auf PRIVAT setzen!

# 2. Datei aus History entfernen
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch test_archiv/*.pdf" \
  --prune-empty --tag-name-filter cat -- --all

# 3. Force-Push (überschreibt Remote)
git push origin --force --all
git push origin --force --tags

# 4. Lokale Refs aufräumen
rm -rf .git/refs/original/
git reflog expire --expire=now --all
git gc --prune=now --aggressive
```

## 📝 Empfohlene Git-Workflow

### Regelmäßige Updates:

```bash
# 1. Änderungen prüfen
git status

# 2. Nur Code-Dateien hinzufügen
git add *.py *.md *.sh *.bat requirements.txt

# 3. Commit mit Beschreibung
git commit -m "Fix: OCR-Verbesserung für schlechte Scan-Qualität"

# 4. Hochladen
git push origin main
```

### Neue Features:

```bash
# 1. Branch erstellen
git checkout -b feature/neue-funktion

# 2. Änderungen committen
git add neue_datei.py
git commit -m "Add: Neue Export-Funktion für Excel"

# 3. Push zum Branch
git push origin feature/neue-funktion

# 4. Auf GitHub: Pull Request erstellen
```

## 🎯 Checkliste: Bereit für GitHub?

- [x] `.gitignore` erstellt und getestet
- [x] `LICENSE` (MIT) vorhanden
- [x] `SECURITY.md` mit Datenschutzhinweisen
- [x] `README.md` mit Warnung über sensible Daten
- [x] `.archiv_config.json` wird ignoriert
- [x] `test_archiv/` wird ignoriert
- [x] `*.db` wird ignoriert
- [x] `git status --ignored` zeigt sensible Dateien
- [ ] GitHub-Repository erstellt (Ihr nächster Schritt!)
- [ ] `git push` durchgeführt
- [ ] Auf GitHub überprüft: Keine sensiblen Daten sichtbar

## 🆘 Support

Bei Fragen:
1. Lesen Sie `SECURITY.md` für Datenschutz-Details
2. Prüfen Sie `.gitignore` für ignorierte Muster
3. Testen Sie mit `git status --ignored`

## 🎉 Nach dem Upload

Ihr Repository ist jetzt auf GitHub! Sie können:
- ✅ Issues für Bugs erstellen
- ✅ Pull Requests von anderen empfangen
- ✅ Die Software mit anderen Werkstätten teilen
- ✅ CI/CD für automatische Tests einrichten

**Wichtig**: Alle sensiblen Daten bleiben lokal auf Ihrem Server! 🔒
