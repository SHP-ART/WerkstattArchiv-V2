# Schlagwort-Verwaltung

## Übersicht

Die Schlagwort-Verwaltung ermöglicht die zentrale Pflege der Keywords, die in PDF-Dokumenten (Seiten 2-10) gesucht werden. Änderungen können über die Web-UI vorgenommen werden und werden sofort in der Konfiguration gespeichert.

## Funktionen

### 1. Schlagwörter verwalten

**Web-UI: Navigation → Schlagwörter**

- **Anzeige**: Alle konfigurierten Schlagwörter in einer Liste
- **Hinzufügen**: Neue Schlagwörter über den Button "Neues Schlagwort"
- **Bearbeiten**: Direktes Editieren in der Liste
- **Löschen**: Entfernen einzelner Schlagwörter mit Bestätigung
- **Filtern**: Schnelles Durchsuchen der Liste mit Suchfeld
- **Speichern**: Änderungen werden in `.archiv_config.json` gespeichert

### 2. Automatische Neu-Verschlagwortung

**Funktion**: Durchsucht alle vorhandenen PDFs im Archiv nach den aktuellen Schlagwörtern und aktualisiert die Datenbank.

**Verwendung**:
1. Öffne "Schlagwörter" in der Navigation
2. Klicke auf "Alle PDFs neu verschlagworten"
3. Bestätige die Aktion im Dialog
4. Der Fortschritt wird in Echtzeit angezeigt

**Wichtig**:
- Die Neu-Verschlagwortung kann bei vielen Aufträgen mehrere Minuten dauern
- Der Prozess läuft im Hintergrund, die Web-UI bleibt bedienbar
- Alle PDFs werden mit OCR neu analysiert (Seiten 2-10)
- Die Datenbank wird automatisch aktualisiert

### 3. Statistik-Dashboard

**Kategorien**:
- Garantie/Kulanz (Rückruf, Serviceaktionen)
- Diagnose/Fehler (Fehlercodes, Motorstörungen)
- Bremsen/Fahrwerk (Sicherheit, TÜV)
- Service/Wartung (Inspektion, Ölwechsel)
- Kosten/Dokumente (Rechnung, Freigabe)

**Anzeige**: Anzahl der Schlagwörter pro Kategorie

## Technische Details

### API-Endpoints

#### Schlagwörter abrufen
```http
GET /api/keywords
```

**Response**:
```json
{
  "keywords": ["Garantie", "Fehlercode", "Bremsbelag", ...],
  "count": 142
}
```

#### Schlagwörter speichern
```http
POST /api/keywords
Content-Type: application/json

{
  "keywords": ["Garantie", "Fehlercode", "Bremsbelag", ...]
}
```

**Response**:
```json
{
  "success": true,
  "count": 142
}
```

#### Neu-Verschlagwortung starten
```http
POST /api/keywords/rescan
```

**Response**:
```json
{
  "success": true,
  "message": "Re-Scan gestartet"
}
```

#### Neu-Verschlagwortung Status
```http
GET /api/keywords/rescan/status
```

**Response**:
```json
{
  "running": true,
  "progress": 45,
  "processed": 234,
  "total": 520,
  "status": "234/520 Aufträge bearbeitet",
  "finished": false
}
```

### Datenfluss

```
Schlagwort-Änderung
    ↓
Web-UI (keywords.html)
    ↓
POST /api/keywords
    ↓
config.py → .archiv_config.json
    ↓
Gespeichert
```

```
Neu-Verschlagwortung
    ↓
POST /api/keywords/rescan
    ↓
Thread gestartet
    ↓
Für jeden Auftrag:
    ↓
    1. PDF laden
    ↓
    2. OCR (Seiten 2-10)
    ↓
    3. Keywords extrahieren
    ↓
    4. Datenbank aktualisieren
    ↓
Status via GET /api/keywords/rescan/status
    ↓
Abgeschlossen
```

### Code-Struktur

**web_app.py**:
- `keywords_page()`: Route für Web-UI
- `get_keywords()`: API zum Laden der Schlagwörter
- `save_keywords()`: API zum Speichern der Schlagwörter
- `start_keyword_rescan()`: API zum Starten der Neu-Verschlagwortung (mit Thread)
- `get_rescan_status()`: API für Fortschritts-Polling

**templates/keywords.html**:
- Schlagwort-Liste mit Inline-Editing
- Modal-Dialoge für Hinzufügen und Bestätigung
- JavaScript für AJAX-Kommunikation
- Echtzeit-Fortschrittsanzeige für Re-Scan

**config.py**:
- `save_config()`: Speichert Konfiguration nach `.archiv_config.json`
- `get_keywords()`: Lädt Schlagwort-Liste aus Config

## Verwendungsbeispiele

### Beispiel 1: Neues Schlagwort hinzufügen

1. Navigiere zu "Schlagwörter"
2. Klicke "Neues Schlagwort"
3. Gib z.B. "Klimakompressor" ein
4. Klicke "Hinzufügen"
5. Klicke "Speichern"

→ Das Schlagwort wird in `.archiv_config.json` gespeichert und bei neuen PDFs automatisch gesucht.

### Beispiel 2: Vorhandene PDFs aktualisieren

**Szenario**: Du hast 10 neue Schlagwörter hinzugefügt und möchtest diese auch in alten Aufträgen suchen.

1. Öffne "Schlagwörter"
2. Klicke "Alle PDFs neu verschlagworten"
3. Bestätige mit "Neu-Verschlagwortung starten"
4. Warte bis Fortschritt 100% erreicht

→ Alle PDFs werden neu analysiert, Datenbank aktualisiert sich automatisch.

### Beispiel 3: Schlagwort-Kategorien optimieren

**Problem**: Zu viele Schlagwörter, unübersichtlich.

**Lösung**:
1. Nutze die Statistik-Sidebar
2. Prüfe Verteilung über Kategorien
3. Lösche selten genutzte oder doppelte Einträge
4. Speichere und starte Neu-Verschlagwortung

## Best Practices

### Schlagwort-Pflege

**✅ DO:**
- Verwende spezifische Begriffe (z.B. "Bremsbelag" statt "Bremse")
- Nutze Fachbegriffe aus der Werkstatt
- Halte die Liste unter 200 Einträgen (Performance)
- Teste neue Schlagwörter mit Re-Scan auf Test-Daten

**❌ DON'T:**
- Vermeide zu generische Begriffe ("Teil", "Auto")
- Keine Duplikate oder sehr ähnliche Wörter
- Keine Sonderzeichen oder Zahlen als Schlagwörter

### Neu-Verschlagwortung

**Wann ausführen:**
- Nach Hinzufügen vieler neuer Schlagwörter
- Nach Korrektur von Tippfehlern in bestehenden Schlagwörtern
- Bei Migration zu neuer Schlagwort-Strategie

**Wann NICHT ausführen:**
- Während der Arbeitszeit (Performance-Impact)
- Bei laufendem Backup
- Bei aktivem File-Watcher (kann Konflikte verursachen)

## Troubleshooting

### Problem: Re-Scan schlägt fehl

**Symptom**: Status zeigt "Fehler: ..." nach Start

**Lösung**:
1. Prüfe Logs: `logs/server.log`
2. Stelle sicher, dass Archiv-Ordner erreichbar ist
3. Prüfe Dateirechte für PDFs
4. Tesseract muss installiert sein

### Problem: Schlagwörter werden nicht gespeichert

**Symptom**: Nach Reload sind Änderungen weg

**Lösung**:
1. Prüfe `.archiv_config.json` Schreibrechte
2. Klicke "Speichern" vor dem Schließen
3. Prüfe Browser-Console auf JavaScript-Fehler

### Problem: Re-Scan dauert sehr lange

**Symptom**: Fortschritt stockt bei X%

**Lösung**:
1. Normal bei vielen/großen PDFs
2. Prüfe Server-Log auf OCR-Fehler
3. Defekte PDFs überspringen automatisch
4. Geduld: 1000 Aufträge ≈ 10-15 Minuten

### Problem: Neue Schlagwörter finden nichts

**Symptom**: Nach Re-Scan keine Treffer

**Lösung**:
1. Prüfe Schreibweise (Groß-/Kleinschreibung beachten!)
2. Suche ist case-insensitive, aber exakte Übereinstimmung
3. Teste mit bekannten PDFs manuell
4. OCR-Qualität kann Einfluss haben

## Beispiel-Konfiguration

**.archiv_config.json** (Auszug):
```json
{
  "keywords": [
    "Garantie",
    "Gewährleistung",
    "Kulanz",
    "Fehlerspeicher",
    "Fehlercode",
    "DTC",
    "Bremsbelag",
    "Bremsscheibe",
    "TÜV",
    "Hauptuntersuchung",
    "Inspektion",
    "Ölwechsel",
    "Zahnriemen"
  ]
}
```

## Performance-Hinweise

### Datenbank-Indizes

Die Datenbank nutzt JSON-Feld `keywords_json` für Schlagwörter:

```sql
SELECT * FROM auftraege 
WHERE keywords_json LIKE '%"Garantie"%';
```

**Performance**:
- Suche in 10.000 Aufträgen: ~100-200ms
- Re-Scan von 1000 PDFs: ~10-15 Minuten
- OCR pro PDF (10 Seiten): ~3-5 Sekunden

### Optimierungen

1. **Schlagwort-Liste klein halten** (<200 Einträge)
2. **Re-Scan außerhalb Stoßzeiten** (nachts, Wochenende)
3. **Tesseract-Optimierung** in Config (DPI, PSM-Modus)
4. **Netzwerk-Optimierung** (lokale SSD statt NAS für Re-Scan)

## Integration mit anderen Features

### Suche

**Verknüpfung**: Schlagwort-Suche nutzt `keywords_json` aus Datenbank

```
Web-UI → Suche nach "Garantie"
    ↓
API: /api/search?type=keyword&query=Garantie
    ↓
db.search_by_keyword(db_path, "Garantie")
    ↓
Ergebnisse mit Seitenzahlen
```

### Archivierung

**Verknüpfung**: Bei neuen PDFs werden Schlagwörter automatisch extrahiert

```
PDF ins Archiv
    ↓
OCR (Seiten 1-10)
    ↓
Parser extrahiert Keywords (Seiten 2-10)
    ↓
Speicherung in DB mit keywords_json
```

### Backup

**Wichtig**: `.archiv_config.json` wird bei Backup mitgesichert!

```
Backup-Prozess
    ↓
ZIP erstellen
    ↓
    - werkstatt.db
    - .archiv_config.json  ← Schlagwörter hier!
    - (optional) Archiv-Ordner
```

## Weiterentwicklung

### Mögliche Erweiterungen

1. **Import/Export** von Schlagwort-Listen (CSV, JSON)
2. **Schlagwort-Vorschläge** basierend auf Häufigkeit in PDFs
3. **Kategorien-Management** (eigene Kategorien definieren)
4. **Regex-Patterns** für flexible Suche
5. **Schlagwort-Synonyme** (z.B. "KVA" = "Kostenvoranschlag")
6. **OCR-Konfidenz** für gefundene Schlagwörter

### API-Erweiterungen

```python
# Schlagwort-Statistik
GET /api/keywords/stats
→ {"Garantie": 234, "Fehlercode": 189, ...}

# Schlagwort-Vorschläge
GET /api/keywords/suggest?min_count=10
→ {"suggestions": ["Klimakompressor", "Turbolader", ...]}

# Schlagwort-Historie
GET /api/keywords/history
→ Änderungsprotokoll mit Timestamps
```

## Fazit

Die Schlagwort-Verwaltung ist ein zentrales Feature für:
- **Schnelle Anpassung** der Suchkriterien
- **Retroaktive Updates** bestehender Daten
- **Transparenz** durch Statistik und Live-Status
- **Flexibilität** ohne Code-Änderungen

**Zugriff**: http://127.0.0.1:8080/keywords
