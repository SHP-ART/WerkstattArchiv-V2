# Netzwerk-Zugriff - Werkstatt-Archiv

## Server im Netzwerk verfügbar machen

### Windows

**Einfach:**
```cmd
start_network.bat
```

**Manuell:**
```cmd
.venv\Scripts\activate.bat
python web_app.py --host 0.0.0.0 --port 8080
```

### macOS / Linux

**Einfach:**
```bash
./start_network.sh
```

**Manuell:**
```bash
source .venv/bin/activate
python3 web_app.py --host 0.0.0.0 --port 8080
```

---

## Zugriff von anderen Rechnern

### 1. Finde die Server-IP

**Windows:**
```cmd
ipconfig
```
Suche nach "IPv4-Adresse" (z.B. `192.168.1.100`)

**macOS:**
```bash
ipconfig getifaddr en0
```

**Linux:**
```bash
hostname -I
```

### 2. Öffne im Browser

Von einem anderen Rechner im gleichen Netzwerk:
```
http://192.168.1.100:8080
```
(Ersetze `192.168.1.100` mit deiner tatsächlichen IP)

---

## Firewall-Konfiguration

### Windows Defender Firewall

**Automatisch (als Administrator):**
```cmd
netsh advfirewall firewall add rule name="Werkstatt-Archiv" dir=in action=allow protocol=TCP localport=8080
```

**Manuell:**
1. Windows Defender Firewall öffnen
2. "Erweiterte Einstellungen"
3. "Eingehende Regeln" → "Neue Regel"
4. Regeltyp: **Port**
5. TCP, Port **8080**
6. Verbindung zulassen
7. Profile: Alle auswählen
8. Name: "Werkstatt-Archiv"

### macOS Firewall

1. Systemeinstellungen → Netzwerk
2. Firewall → Firewall-Optionen
3. Python den eingehenden Zugriff erlauben

**Oder Terminal:**
```bash
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --add /usr/bin/python3
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --unblockapp /usr/bin/python3
```

### Linux (ufw)

```bash
# Port freigeben
sudo ufw allow 8080/tcp

# Status prüfen
sudo ufw status
```

---

## Sicherheitshinweise

### ⚠️ Wichtig

- **Nur im vertrauenswürdigen Netzwerk** verwenden (z.B. Firmen-LAN)
- **NICHT** direkt ins Internet freigeben (keine Passwort-Authentifizierung!)
- Für Internet-Zugriff: Reverse-Proxy mit SSL und Authentifizierung nutzen

### Empfohlene Netzwerk-Umgebungen

✅ **Sicher:**
- Lokales Firmen-Netzwerk (LAN)
- Home-Netzwerk hinter Router
- VPN-Verbindungen

❌ **Unsicher:**
- Öffentliche WLANs
- Direkte Internet-Freigabe
- Ungesicherte Netzwerke

---

## Unterschied: Localhost vs. Netzwerk

### Localhost (`127.0.0.1`)
```bash
python web_app.py --host 127.0.0.1 --port 8080
```
- ✅ Nur vom gleichen Rechner erreichbar
- ✅ Sicherer (keine Netzwerk-Zugriffe)
- ❌ Nicht von anderen PCs nutzbar

**Verwenden für:** Persönliche Nutzung, Entwicklung

### Netzwerk (`0.0.0.0`)
```bash
python web_app.py --host 0.0.0.0 --port 8080
```
- ✅ Von allen Rechnern im Netzwerk erreichbar
- ✅ Mehrere Benutzer gleichzeitig
- ⚠️ Firewall-Konfiguration erforderlich
- ⚠️ Nur in vertrauenswürdigen Netzwerken

**Verwenden für:** Team-Nutzung, Server-Betrieb

---

## Problemlösung

### Server nicht erreichbar von anderem PC

**1. Ping-Test:**
```cmd
ping 192.168.1.100
```
Funktioniert Ping? → Netzwerk OK, Firewall prüfen

**2. Port-Test:**
```bash
# Von anderem PC aus
telnet 192.168.1.100 8080
```
Verbindung fehlgeschlagen? → Firewall blockiert

**3. Server läuft?**
```bash
# Auf dem Server-PC
netstat -ano | findstr :8080     # Windows
lsof -i :8080                     # macOS/Linux
```

**4. Richtige IP?**
- Prüfe ob Server und Client im gleichen Netzwerk sind
- Private IPs: `192.168.x.x` oder `10.x.x.x`

### Firewall blockiert

**Windows:**
- Prüfe Windows Defender Firewall → Erweiterte Einstellungen
- Suche nach Port 8080 in eingehenden Regeln
- Erstelle Regel falls nicht vorhanden

**macOS:**
- Systemeinstellungen → Netzwerk → Firewall
- Python erlauben

**Router:**
- Port-Forwarding nicht nötig (nur LAN-Zugriff)

---

## Performance-Tipps

### Für Server-Betrieb (mehrere Benutzer)

Die Software nutzt bereits **Waitress WSGI Server** mit 6 Threads:
```python
# Bereits in web_app.py konfiguriert
serve(app, host='0.0.0.0', port=8080, threads=6)
```

**Empfehlungen:**
- ✅ Min. 4 GB RAM für OCR-Operationen
- ✅ SSD für Archiv-Verzeichnis
- ✅ Gigabit-Netzwerk für schnelle PDF-Downloads
- ✅ Dedizierter Server-PC (kein Laptop)

### Für viele gleichzeitige Benutzer

Bei mehr als 5 gleichzeitigen Benutzern:
```bash
# Threads erhöhen (web_app.py anpassen)
serve(app, host='0.0.0.0', port=8080, threads=12)
```

---

## Monitoring

### Server-Status prüfen

**Logs anzeigen:**
```cmd
# Windows
type logs\server.log

# macOS/Linux
tail -f logs/server.log
```

**Live-Verbindungen:**
```cmd
# Windows
netstat -ano | findstr :8080

# macOS/Linux
lsof -i :8080
```

**CPU/RAM überwachen:**
- Windows: Task-Manager → Python-Prozess
- macOS: Activity Monitor
- Linux: `htop` oder `top`
