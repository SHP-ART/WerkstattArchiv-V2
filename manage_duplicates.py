#!/usr/bin/env python3
"""
Duplikate-Verwaltung für Werkstatt-Archiv

Dieses Script findet und verwaltet doppelte Auftragsnummern:
- Listet alle Duplikate auf
- Zeigt Details zu jedem Eintrag
- Hilft bei Entscheidung welcher Eintrag behalten werden soll

SICHERHEIT: Löscht nichts automatisch!
"""

import sys
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

import config


def find_duplicate_auftrag_nummern() -> Dict[str, List[Dict[str, Any]]]:
    """Findet alle doppelten Auftragsnummern"""
    cfg = config.Config()
    db_path = cfg.get_db_path()
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Finde Auftragsnummern die mehrfach vorkommen
    cursor.execute('''
        SELECT auftrag_nr, COUNT(*) as count
        FROM auftraege
        GROUP BY auftrag_nr
        HAVING count > 1
        ORDER BY count DESC, auftrag_nr
    ''')
    
    duplicate_numbers = [(row['auftrag_nr'], row['count']) for row in cursor.fetchall()]
    
    # Lade Details für jede doppelte Nummer
    duplicates = {}
    for auftrag_nr, count in duplicate_numbers:
        cursor.execute('''
            SELECT * FROM auftraege
            WHERE auftrag_nr = ?
            ORDER BY created_at ASC
        ''', (auftrag_nr,))
        
        entries = [dict(row) for row in cursor.fetchall()]
        duplicates[auftrag_nr] = entries
    
    conn.close()
    return duplicates


def show_duplicates_list():
    """Zeigt Liste aller Duplikate"""
    duplicates = find_duplicate_auftrag_nummern()
    
    if not duplicates:
        print("\n✓ Keine doppelten Auftragsnummern gefunden!\n")
        return
    
    print("\n" + "="*80)
    print("  DOPPELTE AUFTRAGSNUMMERN")
    print("="*80)
    print()
    
    total_duplicates = sum(len(entries) for entries in duplicates.values())
    print(f"Gefunden: {len(duplicates)} verschiedene Auftragsnummern mit insgesamt {total_duplicates} Einträgen")
    print()
    
    for auftrag_nr, entries in duplicates.items():
        print(f"📋 Auftragsnummer: {auftrag_nr} ({len(entries)}x vorhanden)")
        print("-" * 80)
        
        for i, entry in enumerate(entries, 1):
            file_path = Path(entry['file_path'])
            file_exists = "✓" if file_path.exists() else "✗ FEHLT"
            file_size = f"{file_path.stat().st_size / 1024:.1f} KB" if file_path.exists() else "-"
            
            print(f"  {i}. ID: {entry['id']} {file_exists}")
            print(f"     Datei: {entry['file_path']}")
            print(f"     Größe: {file_size}")
            print(f"     Kunde: {entry['kunde_name'] or 'N/A'}")
            print(f"     Datum: {entry['datum'] or 'N/A'}")
            print(f"     Kennzeichen: {entry['kennzeichen'] or 'N/A'}")
            print(f"     VIN: {entry['vin'] or 'N/A'}")
            print(f"     Hash: {entry['hash'][:16] if entry['hash'] else 'N/A'}...")
            print(f"     Erstellt: {entry['created_at']}")
            print(f"     Aktualisiert: {entry['updated_at']}")
            print()
        
        print()
    
    print("="*80)
    print()
    print("⚠️  HINWEIS:")
    print("Doppelte Auftragsnummern können legitim sein wenn:")
    print("  - Ein Auftrag mehrfach bearbeitet wurde (Nacharbeit, Garantie)")
    print("  - PDFs mit unterschiedlichen Anhängen existieren")
    print("  - Verschiedene Versionen eines Auftrags archiviert wurden")
    print()
    print("Prüfe die Details und entscheide manuell welche Einträge gelöscht werden sollen.")
    print("="*80)
    print()


def show_duplicate_details(auftrag_nr: str):
    """Zeigt detaillierte Informationen zu einer doppelten Auftragsnummer"""
    cfg = config.Config()
    db_path = cfg.get_db_path()
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM auftraege
        WHERE auftrag_nr = ?
        ORDER BY created_at ASC
    ''', (auftrag_nr,))
    
    entries = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    if not entries:
        print(f"\n❌ Keine Einträge für Auftragsnummer {auftrag_nr} gefunden\n")
        return
    
    if len(entries) == 1:
        print(f"\n✓ Auftragsnummer {auftrag_nr} ist nicht doppelt vorhanden\n")
        return
    
    print("\n" + "="*80)
    print(f"  DETAILS - Auftragsnummer {auftrag_nr} ({len(entries)} Einträge)")
    print("="*80)
    print()
    
    for i, entry in enumerate(entries, 1):
        file_path = Path(entry['file_path'])
        
        print(f"Eintrag {i}/{len(entries)}")
        print("-" * 40)
        print(f"  ID: {entry['id']}")
        print(f"  Datei: {entry['file_path']}")
        print(f"  Existiert: {'✓ Ja' if file_path.exists() else '✗ NEIN - Datei fehlt!'}")
        
        if file_path.exists():
            print(f"  Größe: {file_path.stat().st_size / (1024*1024):.2f} MB")
            print(f"  Erstellt (Datei): {datetime.fromtimestamp(file_path.stat().st_ctime).isoformat()}")
        
        print(f"  Kunde: {entry['kunde_name'] or 'N/A'}")
        print(f"  Kundennummer: {entry['kunden_nr'] or 'N/A'}")
        print(f"  Datum: {entry['datum'] or 'N/A'}")
        print(f"  Kennzeichen: {entry['kennzeichen'] or 'N/A'}")
        print(f"  VIN: {entry['vin'] or 'N/A'}")
        print(f"  Formular: {entry['formular_version'] or 'N/A'}")
        print(f"  Hash: {entry['hash'] or 'N/A'}")
        
        # Schlagwörter
        import json
        keywords = json.loads(entry['keywords_json'] or '{}')
        if keywords:
            kw_str = ", ".join(keywords.keys())
            print(f"  Schlagwörter: {kw_str}")
        else:
            print(f"  Schlagwörter: Keine")
        
        print(f"  Erstellt (DB): {entry['created_at']}")
        print(f"  Aktualisiert: {entry['updated_at']}")
        print()
    
    print("="*80)
    print()
    
    # Empfehlung
    print("💡 EMPFEHLUNG:")
    
    # Prüfe ob Hashes identisch sind
    hashes = [e['hash'] for e in entries if e['hash']]
    if len(set(hashes)) == 1 and hashes[0]:
        print("  ⚠️  Alle Einträge haben identischen Hash - wahrscheinlich gleiche Datei!")
        print("  → Behalte den neuesten Eintrag, lösche die anderen")
    else:
        print("  ℹ️  Verschiedene Hashes - wahrscheinlich verschiedene Dateien")
        print("  → Prüfe Dateien manuell und entscheide welche behalten werden sollen")
    
    # Prüfe fehlende Dateien
    missing = [e for e in entries if not Path(e['file_path']).exists()]
    if missing:
        print(f"  ✗ {len(missing)} Datei(en) fehlen - diese DB-Einträge sollten gelöscht werden!")
        for e in missing:
            print(f"    ID {e['id']}: {e['file_path']}")
    
    print()
    print("="*80)
    print()


def delete_entry(entry_id: int):
    """Löscht einen Datenbank-Eintrag (nur DB, nicht die Datei!)"""
    cfg = config.Config()
    db_path = cfg.get_db_path()
    
    # Lade Eintrag-Details
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM auftraege WHERE id = ?', (entry_id,))
    entry = cursor.fetchone()
    
    if not entry:
        print(f"\n❌ Eintrag mit ID {entry_id} nicht gefunden\n")
        conn.close()
        return
    
    entry_dict = dict(entry)
    
    print("\n" + "="*80)
    print(f"  EINTRAG LÖSCHEN - ID {entry_id}")
    print("="*80)
    print()
    print(f"  Auftragsnummer: {entry_dict['auftrag_nr']}")
    print(f"  Datei: {entry_dict['file_path']}")
    print(f"  Kunde: {entry_dict['kunde_name'] or 'N/A'}")
    print(f"  Datum: {entry_dict['datum'] or 'N/A'}")
    print()
    
    file_path = Path(entry_dict['file_path'])
    if file_path.exists():
        print(f"  ⚠️  ACHTUNG: Die Datei existiert noch!")
        print(f"  Die Datei wird NICHT gelöscht, nur der Datenbank-Eintrag!")
        print()
    
    confirm = input("Wirklich löschen? (ja/nein): ").strip().lower()
    
    if confirm != 'ja':
        print("\n❌ Abgebrochen\n")
        conn.close()
        return
    
    # Lösche Eintrag
    cursor.execute('DELETE FROM auftraege WHERE id = ?', (entry_id,))
    conn.commit()
    conn.close()
    
    print(f"\n✓ Datenbank-Eintrag ID {entry_id} gelöscht\n")
    
    if file_path.exists():
        print(f"ℹ️  Datei existiert noch: {file_path}")
        print(f"   Verschiebe sie manuell in Papierkorb oder lösche sie wenn nicht mehr benötigt")
        print()


def main():
    """Hauptfunktion"""
    if len(sys.argv) < 2:
        print("\nDuplikate-Verwaltung - Werkstatt-Archiv")
        print("\nVerwendung:")
        print("  python3 manage_duplicates.py list                - Zeige alle Duplikate")
        print("  python3 manage_duplicates.py details <nummer>    - Details zu einer Auftragsnummer")
        print("  python3 manage_duplicates.py delete <id>         - Lösche DB-Eintrag (nicht Datei!)")
        print()
        print("Beispiele:")
        print("  python3 manage_duplicates.py list")
        print("  python3 manage_duplicates.py details 076329")
        print("  python3 manage_duplicates.py delete 42")
        print()
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == 'list':
        show_duplicates_list()
    
    elif command == 'details':
        if len(sys.argv) < 3:
            print("❌ Bitte Auftragsnummer angeben")
            sys.exit(1)
        auftrag_nr = sys.argv[2]
        show_duplicate_details(auftrag_nr)
    
    elif command == 'delete':
        if len(sys.argv) < 3:
            print("❌ Bitte Eintrag-ID angeben")
            sys.exit(1)
        try:
            entry_id = int(sys.argv[2])
            delete_entry(entry_id)
        except ValueError:
            print("❌ Ungültige ID")
            sys.exit(1)
    
    else:
        print(f"❌ Unbekannter Befehl: {command}")
        sys.exit(1)


if __name__ == '__main__':
    main()
