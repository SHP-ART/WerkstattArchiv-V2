# Tesseract Portable - Einfach entpacken!

## Problem

- Tesseract-Installer funktioniert nicht
- EasyOCR benötigt C++ Compiler (zu kompliziert)

## ✅ Einfachste Lösung: Portable ZIP

### Schritt 1: Download

**Lade diese Datei herunter (bereits fertig kompiliert, ~50 MB):**

https://digi.bib.uni-mannheim.de/tesseract/tesseract-ocr-w64-setup-5.3.3.20231005.exe

### Schritt 2: Mit 7-Zip/WinRAR entpacken

Die `.exe` Datei ist eigentlich ein selbst-entpackendes Archiv:

1. **Rechtsklick** auf die `.exe`
2. Wähle **"7-Zip → Entpacken nach..."** (oder WinRAR)
3. Zielordner: `C:\Users\Sven\Documents\Github\WerkstattArchiv-V2\tesseract_portable`

### Schritt 3: Fertig!

Die Web-UI erkennt Tesseract automatisch.

---

## Alternative: Vorbereitete Portable-Version

Falls du kein 7-Zip hast, hier die Anleitung für eine manuelle portable Version:

### Option A: Choco (Package Manager für Windows)

```powershell
# Choco installieren (Administrator-PowerShell):
Set-ExecutionPolicy Bypass -Scope Process -Force
[System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))

# Tesseract installieren:
choco install tesseract -y
```

### Option B: Scoop (Alternativer Package Manager)

```powershell
# Scoop installieren:
irm get.scoop.sh | iex

# Tesseract installieren:
scoop install tesseract
```

### Option C: Direkt-Download fertige ZIP

**Alternative Download-Links (fertig kompiliert):**

1. **UB Mannheim GitHub Releases:**
   https://github.com/UB-Mannheim/tesseract/releases
   
   → Suche nach: `tesseract-ocr-w64-setup-5.3.3.20231005.exe`
   → Entpacke mit 7-Zip

2. **Tesseract Official:**
   https://tesseract-ocr.github.io/tessdoc/Downloads.html

---

## Was du brauchst

Nur diese Dateien im `tesseract_portable/` Ordner:

```
tesseract_portable/
├── tesseract.exe          ← Hauptprogramm
└── tessdata/
    └── deu.traineddata    ← Deutsche Sprache
```

Das war's! Keine Installation, keine Registry, keine Umgebungsvariablen nötig.

---

## Schnelltest

Teste ob Tesseract funktioniert:

```batch
cd tesseract_portable
tesseract.exe --version
```

Sollte ausgeben: `tesseract 5.3.3`

---

## Warum EasyOCR nicht funktioniert

EasyOCR benötigt:
- Visual Studio Build Tools (~7 GB!)
- C++ Compiler
- Lange Kompilierzeit

Das ist für eine einfache OCR-Lösung übertrieben. Tesseract ist die bessere Wahl für Windows ohne Entwicklungsumgebung.
