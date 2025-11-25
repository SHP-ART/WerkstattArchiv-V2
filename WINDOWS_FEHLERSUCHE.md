# Windows Fehlersuche - Werkstatt-Archiv

## Problem: install.bat schließt sich sofort

### Lösung 1: Führe test_python.bat aus
```cmd
test_python.bat
```
Das zeigt dir, ob Python richtig installiert ist.

### Lösung 2: Manuelle Installation
```cmd
REM 1. Python-Version prüfen
python --version

REM 2. Virtual Environment erstellen
python -m venv .venv

REM 3. Virtual Environment aktivieren
.venv\Scripts\activate.bat

REM 4. Abhängigkeiten installieren
pip install -r requirements.txt
```

### Häufige Fehler:

**Python nicht gefunden:**
- Python von https://www.python.org/downloads/ installieren
- Bei Installation **"Add Python to PATH"** aktivieren!
- Nach Installation: CMD neu starten

**venv-Modul nicht gefunden:**
- Python neu installieren
- "pip" und "tcl/tk" Module mit installieren

---

## Problem: start_server.bat startet aber Webseite nicht erreichbar

### Lösung 1: Verwende start_simple.bat
```cmd
start_simple.bat
```
Das startet den Server im Vordergrund und zeigt alle Fehler direkt an.

### Lösung 2: Prüfe Log-Datei
```cmd
type logs\server.log
```

### Lösung 3: Manueller Start mit Debug
```cmd
REM 1. Virtual Environment aktivieren
.venv\Scripts\activate.bat

REM 2. Server manuell starten
python web_app.py --port 8080
```

### Häufige Probleme:

**Port 8080 bereits belegt:**
```cmd
REM Port-Prüfung
netstat -ano | findstr ":8080"

REM Prozess beenden (PID aus netstat verwenden)
taskkill /F /PID <PID>
```

**Fehlende Abhängigkeiten:**
```cmd
.venv\Scripts\activate.bat
pip install -r requirements.txt
```

**Firewall blockiert:**
- Windows Defender Firewall öffnen
- Python den Zugriff erlauben

**Konfiguration fehlt:**
```cmd
REM Erstelle Config
python -c "import config; cfg = config.Config(); cfg.save()"

REM Oder starte mit Web-UI zur Konfiguration
start_simple.bat
REM Dann: http://127.0.0.1:8080/settings
```

---

## Schritt-für-Schritt Neuinstallation

### 1. Python prüfen
```cmd
python --version
```
Sollte zeigen: `Python 3.9.x` oder höher

### 2. Test-Script ausführen
```cmd
test_python.bat
```

### 3. Vollständige Installation
```cmd
install.bat
```

### 4. Server mit Debug starten
```cmd
start_simple.bat
```

### 5. Browser öffnen
```
http://127.0.0.1:8080
```

---

## Weitere Hilfe

**Log-Dateien prüfen:**
```cmd
REM Server-Log
type logs\server.log

REM Alle Logs anzeigen
dir logs\
```

**Python-Umgebung zurücksetzen:**
```cmd
REM Virtual Environment löschen
rmdir /S /Q .venv

REM Neu installieren
install.bat
```

**Tesseract prüfen:**
```cmd
python main.py --test-tesseract
```

**Alternative: PowerShell verwenden**
```powershell
# start_server.ps1 statt .bat verwenden
.\start_server.ps1
```
