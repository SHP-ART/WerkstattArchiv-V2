# Werkstatt-Archiv Web-Server starten (PowerShell)
# Dieses Script startet den Web-Server mit optimalen Einstellungen

Write-Host "======================================" -ForegroundColor Green
Write-Host "Werkstatt-Archiv Web-Server" -ForegroundColor Green
Write-Host "======================================" -ForegroundColor Green
Write-Host ""

# Wechsle in das Script-Verzeichnis
Set-Location $PSScriptRoot

# Prüfe ob Python installiert ist
try {
    $pythonVersion = python --version 2>&1
    Write-Host "[OK] Python gefunden: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "[FEHLER] Python nicht gefunden!" -ForegroundColor Red
    Write-Host "Bitte installieren Sie Python von https://www.python.org/" -ForegroundColor Yellow
    Read-Host "Drücken Sie Enter zum Beenden"
    exit 1
}

# Prüfe ob Port 8080 bereits belegt ist
$portInUse = Get-NetTCPConnection -LocalPort 8080 -ErrorAction SilentlyContinue
if ($portInUse) {
    Write-Host ""
    Write-Host "[WARNUNG] Port 8080 ist bereits belegt!" -ForegroundColor Yellow
    $answer = Read-Host "Möchten Sie den alten Prozess beenden? (J/N)"
    if ($answer -eq "J" -or $answer -eq "j") {
        $portInUse | ForEach-Object {
            Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue
        }
        Start-Sleep -Seconds 2
        Write-Host "[OK] Alter Prozess beendet" -ForegroundColor Green
    } else {
        Write-Host "Abgebrochen." -ForegroundColor Yellow
        exit 1
    }
}

# Prüfe Flask Installation
try {
    python -c "import flask" 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) { throw }
    Write-Host "[OK] Alle Dependencies vorhanden" -ForegroundColor Green
} catch {
    Write-Host ""
    Write-Host "[FEHLER] Flask nicht installiert!" -ForegroundColor Red
    Write-Host "Installiere mit: pip install flask" -ForegroundColor Yellow
    Read-Host "Drücken Sie Enter zum Beenden"
    exit 1
}

Write-Host ""
Write-Host "[INFO] Starte Server..." -ForegroundColor Cyan
Write-Host "Zugriff über: " -NoNewline
Write-Host "http://127.0.0.1:8080" -ForegroundColor Yellow
Write-Host "Zum Beenden: " -NoNewline
Write-Host "Strg+C" -ForegroundColor Yellow
Write-Host ""
Write-Host "======================================" -ForegroundColor Green
Write-Host ""

# Server starten
try {
    python web_app.py --port 8080 --threaded
} catch {
    Write-Host ""
    Write-Host "[FEHLER] Server konnte nicht gestartet werden!" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
}

Write-Host ""
Write-Host "[INFO] Server wurde beendet." -ForegroundColor Green
Read-Host "Drücken Sie Enter zum Beenden"
