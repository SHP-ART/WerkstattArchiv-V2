# Kundenliste - Daten bearbeiten

## Neue Funktion: Kundendaten ändern ✨

In der Kundenliste unter `/customers` können jetzt alle Kundendaten direkt bearbeitet werden.

## Verwendung

### 1. Kundenliste öffnen

Gehe zu: **http://127.0.0.1:8080/customers**

### 2. Kunden bearbeiten

In der Tabelle gibt es jetzt bei jedem Kunden zwei Buttons:

- 🔍 **Liste** - Zeigt alle Aufträge dieses Kunden
- ✏️ **Stift** - Öffnet den Bearbeitungs-Dialog

### 3. Daten ändern

Im Bearbeitungs-Dialog kannst du folgendes anpassen:

- **Kundenname** (Pflichtfeld)
- **Kundennummer** (optional)
- **Kennzeichen**
- **VIN (Fahrgestellnummer)**

### 4. Speichern

Klicke auf "Speichern" - alle zugehörigen Aufträge werden automatisch aktualisiert!

## Features

✅ **Alle Aufträge werden aktualisiert**
- Wenn du z.B. "Müller" in "Max Müller" änderst, werden ALLE Aufträge dieses Kunden mit dem neuen Namen aktualisiert

✅ **Erfolgsbestätigung**
- Nach dem Speichern siehst du eine Meldung mit der Anzahl der aktualisierten Aufträge

✅ **Sofortige Aktualisierung**
- Die Tabelle lädt sich automatisch neu mit den aktualisierten Daten

✅ **Fehlerbehandlung**
- Falls etwas schief geht, bekommst du eine klare Fehlermeldung

## Beispiel

**Vorher:**
- Kundenname: "Müller"
- Kennzeichen: "B-AB 123"
- VIN: leer

**Nachher:**
- Kundenname: "Max Müller GmbH"
- Kennzeichen: "B-AB 1234" (korrigiert)
- VIN: "WBA12345678901234"

➡️ Alle 5 Aufträge dieses Kunden werden automatisch aktualisiert!

## Hinweise

⚠️ **Vorsicht bei Namen-Änderungen**
- Wenn du den Namen änderst, werden ALLE Aufträge mit diesem alten Namen aktualisiert
- Stelle sicher, dass du wirklich alle Aufträge dieses Kunden meinst

💡 **Tipp**
- Nutze die Filter-Funktion oben, um den richtigen Kunden schnell zu finden
- Die Suche funktioniert für Namen UND Kennzeichen

## Backend-API

Die Funktion nutzt das neue API-Endpoint:

```
POST /api/customers/update
```

Request-Body:
```json
{
  "old_kunde_name": "Müller",
  "old_kunden_nr": "12345",
  "old_kennzeichen": "B-AB 123",
  "old_vin": "",
  "new_kunde_name": "Max Müller GmbH",
  "new_kunden_nr": "12345",
  "new_kennzeichen": "B-AB 1234",
  "new_vin": "WBA12345678901234"
}
```

Response:
```json
{
  "success": true,
  "message": "Kundendaten erfolgreich aktualisiert",
  "updated_count": 5
}
```
