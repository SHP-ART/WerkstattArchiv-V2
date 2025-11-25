#!/usr/bin/env python3
"""
Werkstatt-Archiv: Auftragsnummer korrigieren

Dieses Script korrigiert eine falsche Auftragsnummer im System:
1. Dateiumbenennung im Archiv
2. Ordnerumbenennung im Archiv  
3. Datenbank-Update
4. Optional: Metadaten-Update (Kunde, Kennzeichen, etc.)

Usage:
    python3 auftrag_korrigieren.py <alte_nr> <neue_nr> [--update-metadata]
    
Beispiel:
    python3 auftrag_korrigieren.py 075238 075239
"""

import sys
import sqlite3
import shutil
from pathlib import Path
from typing import Optional, Dict, Any
import logging
import argparse

from config import Config
from archive import format_auftrag_nr, get_thousand_block

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def find_auftrag_in_db(db_path: Path, auftrag_nr: str) -> Optional[Dict[str, Any]]:
    """
    Sucht einen Auftrag in der Datenbank.
    
    Args:
        db_path: Pfad zur Datenbank
        auftrag_nr: Auftragsnummer (normalisiert)
    
    Returns:
        Dict mit Auftragsdaten oder None
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM auftraege WHERE auftrag_nr = ?', (auftrag_nr,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return dict(row)
    return None


def update_auftrag_nummer(
    db_path: Path,
    archiv_root: Path,
    alte_nr: str,
    neue_nr: str,
    use_thousand_blocks: bool = True,
    use_year_folders: bool = True,
    dry_run: bool = False
) -> bool:
    """
    Korrigiert eine Auftragsnummer im gesamten System.
    
    Args:
        db_path: Pfad zur Datenbank
        archiv_root: Wurzelverzeichnis des Archivs
        alte_nr: Alte Auftragsnummer (normalisiert)
        neue_nr: Neue Auftragsnummer (normalisiert)
        use_thousand_blocks: Tausender-Blöcke verwenden
        use_year_folders: Jahr-Ordner verwenden
        dry_run: Nur Simulation, keine Änderungen
    
    Returns:
        True bei Erfolg
    """
    # 1. Auftrag in DB suchen
    logger.info(f"Suche Auftrag {alte_nr} in Datenbank...")
    auftrag = find_auftrag_in_db(db_path, alte_nr)
    
    if not auftrag:
        logger.error(f"Auftrag {alte_nr} nicht in Datenbank gefunden!")
        return False
    
    logger.info(f"✓ Auftrag gefunden (ID {auftrag['id']})")
    logger.info(f"  Kunde: {auftrag['kunde_name'] or 'N/A'}")
    logger.info(f"  Datum: {auftrag['datum'] or 'N/A'}")
    logger.info(f"  KZ: {auftrag['kennzeichen'] or 'N/A'}")
    logger.info(f"  Datei: {auftrag['file_path']}")
    
    # 2. Alte Dateipfade
    old_file_path = Path(auftrag['file_path'])
    
    if not old_file_path.exists():
        logger.warning(f"⚠️  Datei existiert nicht: {old_file_path}")
        logger.warning(f"   Nur Datenbank wird aktualisiert")
        file_exists = False
    else:
        file_exists = True
        logger.info(f"✓ Datei existiert: {old_file_path}")
    
    # 3. Neue Pfade berechnen
    old_folder = old_file_path.parent
    
    # Neuer Ordner
    if use_year_folders and auftrag['datum']:
        jahr = auftrag['datum'][:4]  # YYYY-MM-DD → YYYY
    else:
        jahr = None
    
    if use_thousand_blocks:
        block = get_thousand_block(neue_nr)
        if jahr:
            new_folder = archiv_root / jahr / block / neue_nr
        else:
            new_folder = archiv_root / block / neue_nr
    else:
        if jahr:
            new_folder = archiv_root / jahr / neue_nr
        else:
            new_folder = archiv_root / neue_nr
    
    # Neuer Dateiname (behalte Suffix nach Auftragsnummer)
    old_filename = old_file_path.name
    # Ersetze alte Nummer durch neue Nummer im Dateinamen
    new_filename = old_filename.replace(alte_nr, neue_nr, 1)
    new_file_path = new_folder / new_filename
    
    logger.info(f"\nGeplante Änderungen:")
    logger.info(f"  Alter Ordner: {old_folder}")
    logger.info(f"  Neuer Ordner: {new_folder}")
    logger.info(f"  Alter Dateiname: {old_filename}")
    logger.info(f"  Neuer Dateiname: {new_filename}")
    
    if dry_run:
        logger.info("\n🔍 DRY RUN - Keine Änderungen werden vorgenommen")
        return True
    
    # 4. Bestätigung
    print(f"\n{'='*60}")
    print(f"WARNUNG: Diese Aktion wird folgende Änderungen vornehmen:")
    print(f"  • Auftragsnummer: {alte_nr} → {neue_nr}")
    if file_exists:
        print(f"  • Ordner umbenennen: {old_folder.name} → {new_folder.name}")
        print(f"  • Datei umbenennen: {old_filename} → {new_filename}")
    print(f"  • Datenbank-Update (ID {auftrag['id']})")
    print(f"{'='*60}")
    
    antwort = input("Fortfahren? (ja/nein): ").strip().lower()
    if antwort not in ['ja', 'j', 'yes', 'y']:
        logger.info("Abgebrochen durch Benutzer")
        return False
    
    # 5. Dateien verschieben
    if file_exists:
        logger.info(f"\n📦 Verschiebe Dateien...")
        
        # Neuen Ordner erstellen
        new_folder.mkdir(parents=True, exist_ok=True)
        logger.info(f"✓ Ordner erstellt: {new_folder}")
        
        # Datei verschieben
        shutil.move(str(old_file_path), str(new_file_path))
        logger.info(f"✓ Datei verschoben: {new_file_path.name}")
        
        # Alte Metadaten-Dateien verschieben (falls vorhanden)
        for meta_file in ['data.csv', 'meta.json']:
            old_meta = old_folder / meta_file
            if old_meta.exists():
                new_meta = new_folder / meta_file
                shutil.move(str(old_meta), str(new_meta))
                logger.info(f"✓ Metadaten verschoben: {meta_file}")
        
        # Alten Ordner löschen (falls leer)
        try:
            if not any(old_folder.iterdir()):
                old_folder.rmdir()
                logger.info(f"✓ Alter Ordner gelöscht: {old_folder}")
        except Exception as e:
            logger.warning(f"⚠️  Konnte alten Ordner nicht löschen: {e}")
    
    # 6. Datenbank aktualisieren
    logger.info(f"\n💾 Aktualisiere Datenbank...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE auftraege 
        SET auftrag_nr = ?, file_path = ?
        WHERE id = ?
    ''', (neue_nr, str(new_file_path), auftrag['id']))
    
    conn.commit()
    conn.close()
    logger.info(f"✓ Datenbank aktualisiert (ID {auftrag['id']})")
    
    logger.info(f"\n{'='*60}")
    logger.info(f"✅ ERFOLG: Auftrag {alte_nr} → {neue_nr} korrigiert")
    logger.info(f"{'='*60}")
    
    return True


def main():
    parser = argparse.ArgumentParser(description='Korrigiert eine Auftragsnummer im Archiv-System')
    parser.add_argument('alte_nummer', help='Alte Auftragsnummer')
    parser.add_argument('neue_nummer', help='Neue (korrekte) Auftragsnummer')
    parser.add_argument('--no-padding', action='store_true', help='Neue Nummer OHNE Padding (z.B. 75238 statt 075238)')
    parser.add_argument('--dry-run', action='store_true', help='Nur Simulation, keine Änderungen')
    
    args = parser.parse_args()
    
    # Normalisiere alte Nummer (immer mit Padding für DB-Suche)
    alte_nr = format_auftrag_nr(args.alte_nummer)
    
    # Neue Nummer: mit oder ohne Padding
    if args.no_padding:
        # Entferne führende Nullen
        neue_nr = str(int(args.neue_nummer))
    else:
        neue_nr = format_auftrag_nr(args.neue_nummer)
    
    logger.info(f"Werkstatt-Archiv: Auftragsnummer korrigieren")
    logger.info(f"{'='*60}")
    logger.info(f"Alte Nummer: {args.alte_nummer} → {alte_nr}")
    logger.info(f"Neue Nummer: {args.neue_nummer} → {neue_nr}")
    logger.info(f"{'='*60}\n")
    
    # Config laden
    try:
        config = Config()
        
        db_path = config.get_db_path()
        archiv_root = config.get_archiv_root()
        use_thousand_blocks = config.config.get('use_thousand_blocks', True)
        use_year_folders = config.config.get('use_year_folders', True)
        
        logger.info(f"Konfiguration geladen:")
        logger.info(f"  Datenbank: {db_path}")
        logger.info(f"  Archiv: {archiv_root}")
        logger.info(f"  Tausender-Blöcke: {use_thousand_blocks}")
        logger.info(f"  Jahr-Ordner: {use_year_folders}\n")
        
    except Exception as e:
        logger.error(f"Fehler beim Laden der Konfiguration: {e}")
        return 1
    
    # Korrektur durchführen
    success = update_auftrag_nummer(
        db_path,
        archiv_root,
        alte_nr,
        neue_nr,
        use_thousand_blocks,
        use_year_folders,
        dry_run=args.dry_run
    )
    
    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())
