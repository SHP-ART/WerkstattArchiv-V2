#!/usr/bin/env python3
"""
Batch-Import für verschachtelte Ordnerstrukturen.

Verarbeitet Strukturen wie:
  2024/
    ├── 076329/
    │   ├── auftrag.pdf
    │   └── anhang.pdf
    └── 076330/
        └── scan.pdf

Verwendung:
  python3 batch_import.py /path/to/2024
  python3 batch_import.py /path/to/Import --year 2024
  python3 batch_import.py /path/to/Import --recursive
"""

import sys
import logging
from pathlib import Path
from typing import List
import argparse

from config import Config
from folder_import import process_folder_for_import, FolderImportError

logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)


def find_order_folders(root: Path, recursive: bool = False) -> List[Path]:
    """
    Findet alle Ordner, die wie Auftragsnummern aussehen.
    
    Args:
        root: Root-Verzeichnis
        recursive: Rekursiv suchen?
    
    Returns:
        Liste der Ordner-Pfade
    """
    folders = []
    
    if recursive:
        # Rekursiv alle Unterordner durchsuchen
        for item in root.rglob('*'):
            if item.is_dir() and not item.name.startswith('.'):
                # Prüfe ob Ordnername Ziffern enthält (potenzielle Auftragsnummer)
                if any(char.isdigit() for char in item.name):
                    # Prüfe ob PDFs im Ordner
                    if list(item.glob('*.pdf')):
                        folders.append(item)
    else:
        # Nur direkte Unterordner
        for item in root.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                # Prüfe ob Ordnername Ziffern enthält
                if any(char.isdigit() for char in item.name):
                    # Prüfe ob PDFs im Ordner
                    if list(item.glob('*.pdf')):
                        folders.append(item)
    
    return sorted(folders)


def batch_import(
    root_path: Path,
    config: Config,
    ohne_auftrag: bool = False,
    dry_run: bool = False,
    year: int | None = None,
    recursive: bool = False
) -> None:
    """
    Batch-Import für verschachtelte Strukturen.
    
    Args:
        root_path: Root-Verzeichnis (z.B. Import/2024/)
        config: Config-Objekt
        ohne_auftrag: OA-Modus
        dry_run: Nur Simulation
        year: Nur Ordner in diesem Jahr verarbeiten
        recursive: Rekursiv suchen
    """
    if not root_path.exists():
        logger.error(f"Verzeichnis nicht gefunden: {root_path}")
        return
    
    logger.info("=" * 60)
    logger.info("BATCH-IMPORT: Verschachtelte Strukturen")
    logger.info("=" * 60)
    logger.info(f"Root: {root_path}")
    logger.info(f"Jahr-Filter: {year or 'Alle'}")
    logger.info(f"Rekursiv: {'Ja' if recursive else 'Nein'}")
    logger.info(f"Modus: {'OA (Ohne Auftrag)' if ohne_auftrag else 'MIT Auftrag'}")
    logger.info(f"Dry-Run: {'Ja (Simulation)' if dry_run else 'Nein'}")
    logger.info("=" * 60)
    
    # Ordner finden
    logger.info("\n🔍 Suche Ordner...")
    folders = find_order_folders(root_path, recursive)
    
    # Jahr-Filter anwenden
    if year:
        folders = [f for f in folders if str(year) in str(f)]
        logger.info(f"Jahr-Filter: {year}")
    
    if not folders:
        logger.warning("Keine passenden Ordner gefunden")
        return
    
    logger.info(f"✓ Gefunden: {len(folders)} Ordner\n")
    
    # Vorschau
    logger.info("📋 Ordner-Liste:")
    for i, folder in enumerate(folders, 1):
        pdf_count = len(list(folder.glob('*.pdf')))
        rel_path = folder.relative_to(root_path)
        logger.info(f"  [{i:3d}] {rel_path} ({pdf_count} PDFs)")
    
    if dry_run:
        logger.info("\n" + "=" * 60)
        logger.info("DRY-RUN: Keine tatsächliche Verarbeitung")
        logger.info("=" * 60)
        return
    
    # Bestätigung
    logger.info("\n" + "=" * 60)
    response = input(f"Möchtest du {len(folders)} Ordner importieren? (ja/nein): ")
    if response.lower() not in ['ja', 'j', 'yes', 'y']:
        logger.info("Abgebrochen")
        return
    
    # Verarbeitung
    logger.info("\n" + "=" * 60)
    logger.info("STARTE VERARBEITUNG")
    logger.info("=" * 60 + "\n")
    
    success_count = 0
    error_count = 0
    errors = []
    
    for i, folder in enumerate(folders, 1):
        logger.info(f"\n[{i}/{len(folders)}] Verarbeite: {folder.name}")
        logger.info("-" * 60)
        
        try:
            result = process_folder_for_import(
                folder,
                config,
                merge_pdfs_flag=True,
                ohne_auftrag=ohne_auftrag
            )
            
            if result.get('success'):
                success_count += 1
                logger.info(f"✅ Erfolgreich: {result['auftrag_nr']}")
            else:
                error_count += 1
                error_msg = result.get('error', 'Unbekannter Fehler')
                errors.append((folder.name, error_msg))
                logger.error(f"❌ Fehler: {error_msg}")
        
        except Exception as e:
            error_count += 1
            errors.append((folder.name, str(e)))
            logger.error(f"❌ Fehler bei {folder.name}: {e}")
    
    # Zusammenfassung
    logger.info("\n" + "=" * 60)
    logger.info("ZUSAMMENFASSUNG")
    logger.info("=" * 60)
    logger.info(f"Gesamt:       {len(folders)}")
    logger.info(f"Erfolgreich:  {success_count}")
    logger.info(f"Fehler:       {error_count}")
    
    if errors:
        logger.info("\n❌ Fehler-Liste:")
        for folder_name, error in errors:
            logger.info(f"  - {folder_name}: {error}")
    
    logger.info("=" * 60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Batch-Import für verschachtelte Ordnerstrukturen',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  # Import aller Ordner in 2024/
  python3 batch_import.py Import/2024/
  
  # Nur Jahr 2024, rekursiv
  python3 batch_import.py Import/ --year 2024 --recursive
  
  # Ohne Auftrag (OA-Modus)
  python3 batch_import.py Import/2024/ --oa
  
  # Simulation (kein Import)
  python3 batch_import.py Import/2024/ --dry-run
  
Strukturen:
  2024/
    ├── 076329/
    │   ├── auftrag.pdf
    │   └── anhang.pdf
    └── 076330/
        └── scan.pdf
        """
    )
    
    parser.add_argument(
        'path',
        type=Path,
        help='Root-Verzeichnis (z.B. Import/2024/)'
    )
    
    parser.add_argument(
        '--year',
        type=int,
        help='Nur Ordner mit diesem Jahr verarbeiten (z.B. 2024)'
    )
    
    parser.add_argument(
        '--recursive', '-r',
        action='store_true',
        help='Rekursiv alle Unterordner durchsuchen'
    )
    
    parser.add_argument(
        '--oa',
        action='store_true',
        help='Ohne Auftrag (nur Schlagwörter, Dateiname: _OA.pdf)'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Simulation ohne tatsächlichen Import'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Ausführliche Ausgabe (DEBUG-Level)'
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Config laden
    config = Config()
    
    try:
        batch_import(
            args.path,
            config,
            ohne_auftrag=args.oa,
            dry_run=args.dry_run,
            year=args.year,
            recursive=args.recursive
        )
    except KeyboardInterrupt:
        logger.info("\n\nAbgebrochen durch Benutzer")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\nFehler: {e}")
        sys.exit(1)
