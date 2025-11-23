#!/usr/bin/env python3
"""
Test-Skript für Datenbank-Performance auf Netzwerkspeicher.
Misst Geschwindigkeit von Such- und Schreiboperationen.
"""

import time
import sqlite3
from pathlib import Path
from typing import Dict, List
import sys

# Lokale Module
try:
    from config import Config
    from db import (
        search_by_auftrag_nr,
        search_by_keyword,
        _get_optimized_connection
    )
except ImportError:
    print("❌ Fehler: Module nicht gefunden. Führen Sie das Skript im Projekt-Verzeichnis aus.")
    sys.exit(1)


def measure_time(func, *args, **kwargs) -> tuple:
    """Misst Ausführungszeit einer Funktion."""
    start = time.time()
    result = func(*args, **kwargs)
    elapsed = (time.time() - start) * 1000  # ms
    return result, elapsed


def test_connection_speed(db_path: Path) -> Dict[str, float]:
    """Testet Verbindungsgeschwindigkeit."""
    print("\n🔌 Teste Verbindungsgeschwindigkeit...")
    
    # Standard-Verbindung
    start = time.time()
    conn = sqlite3.connect(db_path)
    conn.close()
    standard_time = (time.time() - start) * 1000
    
    # Optimierte Verbindung
    start = time.time()
    conn = _get_optimized_connection(db_path)
    conn.close()
    optimized_time = (time.time() - start) * 1000
    
    print(f"   Standard:   {standard_time:.1f}ms")
    print(f"   Optimiert:  {optimized_time:.1f}ms")
    print(f"   Speedup:    {standard_time/optimized_time:.1f}x")
    
    return {"standard": standard_time, "optimized": optimized_time}


def test_search_performance(db_path: Path) -> Dict[str, List[float]]:
    """Testet Such-Performance."""
    print("\n🔍 Teste Such-Performance...")
    
    results = {"auftrag": [], "keyword": [], "all": []}
    
    # Test 1: Suche nach Auftragsnummer (3 Durchläufe)
    print("   Suche nach Auftragsnummer (3x)...")
    for i in range(3):
        _, elapsed = measure_time(search_by_auftrag_nr, db_path, "76329")
        results["auftrag"].append(elapsed)
        print(f"     Durchlauf {i+1}: {elapsed:.1f}ms")
    
    # Test 2: Keyword-Suche (3 Durchläufe)
    print("   Suche nach Schlagwort (3x)...")
    for i in range(3):
        _, elapsed = measure_time(search_by_keyword, db_path, "Garantie")
        results["keyword"].append(elapsed)
        print(f"     Durchlauf {i+1}: {elapsed:.1f}ms")
    
    # Test 3: Alle Aufträge laden (1 Durchlauf)
    print("   Lade alle Aufträge...")
    def load_all():
        conn = _get_optimized_connection(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM auftraege")
        result = cursor.fetchall()
        conn.close()
        return result
    
    _, elapsed = measure_time(load_all)
    results["all"].append(elapsed)
    print(f"     Dauer: {elapsed:.1f}ms")
    
    return results


def test_pragma_settings(db_path: Path):
    """Zeigt aktuelle PRAGMA-Einstellungen."""
    print("\n⚙️  Aktuelle Datenbank-Einstellungen:")
    
    conn = _get_optimized_connection(db_path)
    cursor = conn.cursor()
    
    settings = {
        "journal_mode": "PRAGMA journal_mode",
        "synchronous": "PRAGMA synchronous",
        "cache_size": "PRAGMA cache_size",
        "temp_store": "PRAGMA temp_store",
        "mmap_size": "PRAGMA mmap_size",
        "page_size": "PRAGMA page_size",
        "page_count": "PRAGMA page_count"
    }
    
    for name, pragma in settings.items():
        result = cursor.execute(pragma).fetchone()[0]
        if name == "cache_size" and result < 0:
            # Negative Werte sind in KB
            print(f"   {name:15} = {result} ({abs(result)/1024:.0f} MB)")
        elif name == "mmap_size":
            print(f"   {name:15} = {result:,} ({result/1024/1024:.0f} MB)")
        else:
            print(f"   {name:15} = {result}")
    
    conn.close()


def test_file_sizes(db_path: Path):
    """Zeigt Dateigrößen."""
    print("\n💾 Datenbankdateien:")
    
    files = [
        db_path,
        Path(str(db_path) + "-wal"),
        Path(str(db_path) + "-shm"),
        Path(str(db_path) + "-journal")
    ]
    
    total_size = 0
    for f in files:
        if f.exists():
            size = f.stat().st_size
            total_size += size
            print(f"   {f.name:25} {size/1024/1024:>8.2f} MB")
    
    print(f"   {'GESAMT':25} {total_size/1024/1024:>8.2f} MB")


def test_statistics(db_path: Path):
    """Zeigt Datenbank-Statistiken."""
    print("\n📊 Datenbank-Statistiken:")
    
    conn = _get_optimized_connection(db_path)
    cursor = conn.cursor()
    
    # Anzahl Aufträge
    count = cursor.execute("SELECT COUNT(*) FROM auftraege").fetchone()[0]
    print(f"   Anzahl Aufträge:    {count:,}")
    
    # Datumsbereich
    oldest = cursor.execute("SELECT MIN(datum) FROM auftraege WHERE datum IS NOT NULL").fetchone()[0]
    newest = cursor.execute("SELECT MAX(datum) FROM auftraege WHERE datum IS NOT NULL").fetchone()[0]
    if oldest and newest:
        print(f"   Ältester Auftrag:   {oldest}")
        print(f"   Neuester Auftrag:   {newest}")
    
    # Indizes
    indices = cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_%'"
    ).fetchall()
    print(f"   Anzahl Indizes:     {len(indices)}")
    
    conn.close()


def main():
    """Hauptfunktion."""
    print("=" * 60)
    print("SQLite Performance-Test für Netzwerkspeicher")
    print("=" * 60)
    
    # Config laden
    try:
        cfg = Config()
        db_path = cfg.get_db_path()
    except Exception as e:
        print(f"❌ Config-Fehler: {e}")
        sys.exit(1)
    
    if not db_path.exists():
        print(f"❌ Datenbank nicht gefunden: {db_path}")
        sys.exit(1)
    
    print(f"\n📂 Datenbank: {db_path}")
    
    # Tests durchführen
    test_pragma_settings(db_path)
    test_file_sizes(db_path)
    test_statistics(db_path)
    test_connection_speed(db_path)
    search_results = test_search_performance(db_path)
    
    # Zusammenfassung
    print("\n" + "=" * 60)
    print("📈 ZUSAMMENFASSUNG")
    print("=" * 60)
    
    avg_auftrag = sum(search_results["auftrag"]) / len(search_results["auftrag"])
    avg_keyword = sum(search_results["keyword"]) / len(search_results["keyword"])
    
    print(f"   Ø Auftragsnummer-Suche:  {avg_auftrag:.1f}ms")
    print(f"   Ø Schlagwort-Suche:      {avg_keyword:.1f}ms")
    print(f"   Alle Aufträge laden:     {search_results['all'][0]:.1f}ms")
    
    # Bewertung
    print("\n📊 Bewertung:")
    if avg_auftrag < 100:
        print("   ✅ Sehr schnell (< 100ms)")
    elif avg_auftrag < 500:
        print("   ✓ Gut (< 500ms)")
    elif avg_auftrag < 1000:
        print("   ⚠️  Akzeptabel (< 1s)")
    else:
        print("   ❌ Langsam (> 1s) - Netzwerk oder Optimierungen prüfen!")
    
    print("\n💡 Tipps zur Verbesserung:")
    print("   - Siehe SQLITE_OPTIMIERUNG.md")
    print("   - Cache-Größe erhöhen bei viel RAM")
    print("   - WAL-Modus aktiviert überprüfen")
    print("   - Bei sehr langsam: Lokale DB-Kopie erwägen")


if __name__ == "__main__":
    main()
