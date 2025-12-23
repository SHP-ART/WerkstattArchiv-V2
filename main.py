#!/usr/bin/env python3
"""
Werkstatt-Archiv - Hauptprogramm

Automatische Archivierung und Verwaltung von Werkstatt-PDF-Aufträgen.
"""

import sys
import argparse
import logging
from pathlib import Path
from typing import Optional

# Module importieren
import config
import ocr
import parser
import archive
import db
import kunden_index
import watcher
import backup


# Logging konfigurieren
def setup_logging(verbose: bool = False) -> None:
    """
    Richtet das Logging ein.
    
    Args:
        verbose: Ob Debug-Level aktiviert werden soll
    """
    level = logging.DEBUG if verbose else logging.INFO
    
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Bei Bedarf zusätzlich in Datei loggen
    # file_handler = logging.FileHandler('werkstatt_archiv.log')
    # file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    # logging.getLogger().addHandler(file_handler)


logger = logging.getLogger(__name__)


def process_single_pdf(pdf_path: Path, cfg: config.Config) -> bool:
    """
    Verarbeitet eine einzelne PDF-Datei.
    
    Neue Logik:
    - PDF wird in Auftrag (Seite 1) und Anhang (Rest) aufgeteilt
    - Beide PDFs werden separat archiviert
    
    Args:
        pdf_path: Pfad zur PDF-Datei
        cfg: Konfigurationsobjekt
    
    Returns:
        True bei Erfolg, False bei Fehler
    """
    logger.info(f"=" * 60)
    logger.info(f"Verarbeite Datei: {pdf_path.name}")
    logger.info(f"=" * 60)
    
    try:
        # 1. OCR durchführen (alle Seiten)
        lang = cfg.get("tesseract_lang", "deu")
        poppler_path = cfg.get("poppler_path", None)
        
        logger.info("Schritt 1/7: OCR-Verarbeitung...")
        page_texts = ocr.pdf_to_ocr_texts(pdf_path, max_pages=None, lang=lang, poppler_path=poppler_path)
        
        if not page_texts:
            logger.error(f"Keine Seiten in PDF gefunden: {pdf_path.name}")
            archive.move_to_error_folder(pdf_path, cfg.get_input_folder())
            return False
        
        logger.info(f"  → {len(page_texts)} Seiten erkannt")
        
        # 2. Metadaten aus Seite 1 extrahieren
        logger.info("Schritt 2/7: Metadaten-Extraktion...")
        try:
            # Dateiname als Fallback übergeben für Auftragsnummer-Extraktion
            metadata = parser.extract_auftrag_metadata(page_texts[0], fallback_filename=pdf_path.name)
        except parser.ParserError as e:
            logger.error(f"Fehler beim Extrahieren der Metadaten: {e}")
            archive.move_to_error_folder(pdf_path, cfg.get_input_folder())
            return False
        
        logger.info(f"  Auftragsnummer: {metadata['auftrag_nr']}")
        logger.info(f"  Kundennummer: {metadata.get('kunden_nr', 'N/A')}")
        logger.info(f"  Kunde: {metadata.get('name', 'N/A')}")
        logger.info(f"  Datum: {metadata.get('datum', 'N/A')}")
        logger.info(f"  Kennzeichen: {metadata.get('kennzeichen', 'N/A')}")
        logger.info(f"  VIN: {metadata.get('vin', 'N/A')}")
        logger.info(f"  Formular: {metadata.get('formular_version', 'N/A')}")
        
        # 3. PDF in Auftrag + Anhang aufteilen
        logger.info("Schritt 3/7: PDF aufteilen (Auftrag + Anhang)...")
        from pdf_split import split_pdf_auftrag_anhang, PDFSplitError
        
        # Temporäres Verzeichnis für Split
        temp_dir = pdf_path.parent / f".temp_{metadata['auftrag_nr']}"
        temp_dir.mkdir(exist_ok=True)
        
        try:
            auftrag_pdf, anhang_pdf = split_pdf_auftrag_anhang(
                pdf_path,
                temp_dir,
                metadata['auftrag_nr']
            )
        except PDFSplitError as e:
            logger.error(f"Fehler beim Aufteilen der PDF: {e}")
            archive.move_to_error_folder(pdf_path, cfg.get_input_folder())
            return False
        
        # 4. Schlagwörter aus Anhang-Seiten extrahieren (falls vorhanden)
        logger.info("Schritt 4/7: Schlagwort-Suche in Anhang...")
        keywords_found = {}
        
        if anhang_pdf and len(page_texts) > 1:
            keywords = cfg.get_keywords()
            # Seiten 2-N für Keywords (page_texts[1:])
            keywords_found = parser.extract_keywords_from_pages(
                page_texts[1:],  # Nur Anhang-Seiten
                keywords,
                start_page=2  # Startet bei Seite 2
            )
            
            if keywords_found:
                logger.info(f"  Gefundene Schlagwörter: {parser.format_keywords_for_display(keywords_found)}")
            else:
                logger.info("  Keine Schlagwörter gefunden")
        else:
            logger.info("  Kein Anhang vorhanden (nur 1 Seite)")
        
        # 5. Auftrag-PDF ins Archiv verschieben
        logger.info("Schritt 5/7: Auftrag archivieren...")
        archiv_root = cfg.get_archiv_root()
        target_path_auftrag, file_hash_auftrag = archive.move_to_archive(
            auftrag_pdf,
            archiv_root,
            metadata['auftrag_nr'],
            cfg.config,
            metadata  # Übergebe Metadaten für flexiblen Dateinamen
        )
        logger.info(f"  Archiviert als: {target_path_auftrag.name}")
        
        # 6. Anhang-PDF ins Archiv verschieben (falls vorhanden)
        anhang_path_in_archive = None
        if anhang_pdf:
            logger.info("Schritt 6/7: Anhang archivieren...")
            # Anhang in denselben Ordner wie Auftrag verschieben
            target_dir = target_path_auftrag.parent
            anhang_filename = anhang_pdf.name
            target_path_anhang = target_dir / anhang_filename
            
            # Falls Datei bereits existiert, versionieren
            version = 1
            while target_path_anhang.exists():
                version += 1
                base_name = anhang_pdf.stem  # z.B. "076329_Anhang_S2-10"
                anhang_filename = f"{base_name}_v{version}.pdf"
                target_path_anhang = target_dir / anhang_filename
            
            import shutil
            shutil.move(str(anhang_pdf), str(target_path_anhang))
            anhang_path_in_archive = target_path_anhang
            logger.info(f"  Archiviert als: {target_path_anhang.name}")
        else:
            logger.info("Schritt 6/7: Kein Anhang vorhanden")
        
        # 7. In Datenbank speichern
        logger.info("Schritt 7/7: Datenbank-Update...")
        db_path = cfg.get_db_path()
        auftrag_id = db.insert_auftrag(
            db_path,
            metadata,
            keywords_found,
            target_path_auftrag,  # Hauptpfad = Auftrag
            file_hash_auftrag
        )
        logger.info(f"  Datenbank-ID: {auftrag_id}")
        
        # Kunden-Index aktualisieren
        index_path = cfg.get_kunden_index_path()
        kunden_index.update_kunden_index(index_path, {
            "file_path": str(target_path_auftrag),
            "auftrag_nr": metadata['auftrag_nr'],
            "kunden_nr": metadata.get('kunden_nr'),
            "kunde_name": metadata.get('name'),
            "kennzeichen": metadata.get('kennzeichen'),
            "vin": metadata.get('vin'),
            "datum": metadata.get('datum'),
            "formular_version": metadata.get('formular_version')
        })
        
        # Original-PDF löschen
        pdf_path.unlink()
        logger.info(f"  Original-PDF gelöscht: {pdf_path.name}")
        
        # Temp-Verzeichnis aufräumen
        import shutil
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
        
        logger.info("=" * 60)
        logger.info(f"✓ Erfolgreich verarbeitet: {pdf_path.name}")
        if anhang_path_in_archive:
            logger.info(f"  → Auftrag: {target_path_auftrag.name}")
            logger.info(f"  → Anhang: {anhang_path_in_archive.name}")
        else:
            logger.info(f"  → Auftrag: {target_path_auftrag.name} (kein Anhang)")
        logger.info("=" * 60)
        return True
        
    except Exception as e:
        logger.error(f"Fehler bei der Verarbeitung von {pdf_path.name}: {e}", exc_info=True)
        return False


def process_input_folder(cfg: config.Config) -> None:
    """
    Verarbeitet alle PDFs im Eingangsordner (Batch-Modus).
    
    Args:
        cfg: Konfigurationsobjekt
    """
    input_folder = cfg.get_input_folder()
    
    if not input_folder.exists():
        logger.error(f"Eingangsordner existiert nicht: {input_folder}")
        return
    
    # Alle PDF-Dateien finden
    pdf_files = list(input_folder.glob("*.pdf"))
    
    if not pdf_files:
        logger.info(f"Keine PDF-Dateien im Eingangsordner gefunden: {input_folder}")
        return
    
    logger.info(f"Gefunden: {len(pdf_files)} PDF-Dateien")
    logger.info("")
    
    # Statistik
    success_count = 0
    error_count = 0
    
    # Jede PDF verarbeiten
    for pdf_file in pdf_files:
        if process_single_pdf(pdf_file, cfg):
            success_count += 1
        else:
            error_count += 1
        
        logger.info("")
    
    # Zusammenfassung
    logger.info("=" * 60)
    logger.info("VERARBEITUNG ABGESCHLOSSEN")
    logger.info(f"Erfolgreich: {success_count}")
    logger.info(f"Fehler: {error_count}")
    logger.info("=" * 60)


def watch_input_folder(cfg: config.Config) -> None:
    """
    Startet die Ordnerüberwachung (Watch-Modus).
    
    Args:
        cfg: Konfigurationsobjekt
    """
    input_folder = cfg.get_input_folder()
    
    logger.info("=" * 60)
    logger.info("ORDNERÜBERWACHUNG STARTEN")
    logger.info(f"Ordner: {input_folder}")
    logger.info("=" * 60)
    
    # Callback-Funktion für neue Dateien
    def process_callback(pdf_path: Path) -> None:
        process_single_pdf(pdf_path, cfg)
    
    # Watcher starten (blockiert bis Ctrl+C)
    watcher.start_watcher(input_folder, process_callback)


def perform_search(cfg: config.Config, args: argparse.Namespace) -> None:
    """
    Führt eine Suche durch und zeigt die Ergebnisse an.
    
    Args:
        cfg: Konfigurationsobjekt
        args: CLI-Argumente
    """
    db_path = cfg.get_db_path()
    
    if not db_path.exists():
        logger.error(f"Datenbank nicht gefunden: {db_path}")
        return
    
    results = []
    
    if args.search_auftrag:
        logger.info(f"Suche nach Auftragsnummer: {args.search_auftrag}")
        results = db.search_by_auftrag_nr(db_path, args.search_auftrag)
    
    elif args.search_kunden_nr:
        logger.info(f"Suche nach Kundennummer: {args.search_kunden_nr}")
        results = db.search_by_kunden_nr(db_path, args.search_kunden_nr)
    
    elif args.search_name:
        logger.info(f"Suche nach Name: {args.search_name}")
        results = db.search_by_name(db_path, args.search_name)
    
    elif args.search_kennzeichen:
        logger.info(f"Suche nach Kennzeichen: {args.search_kennzeichen}")
        results = db.search_by_kennzeichen(db_path, args.search_kennzeichen)
    
    elif args.search_keyword:
        logger.info(f"Suche nach Schlagwort: {args.search_keyword}")
        results = db.search_by_keyword(db_path, args.search_keyword)
    
    # Ergebnisse anzeigen
    logger.info("")
    logger.info(f"Gefunden: {len(results)} Treffer")
    logger.info("=" * 60)
    
    for i, result in enumerate(results, 1):
        logger.info(f"\nTreffer {i}:")
        logger.info(f"  Auftragsnummer: {result['auftrag_nr']}")
        logger.info(f"  Kundennummer: {result['kunden_nr'] or 'N/A'}")
        logger.info(f"  Kunde: {result['kunde_name'] or 'N/A'}")
        logger.info(f"  Datum: {result['datum'] or 'N/A'}")
        logger.info(f"  Kennzeichen: {result['kennzeichen'] or 'N/A'}")
        logger.info(f"  Datei: {result['file_path']}")
        
        # Keywords anzeigen
        if result['keywords_json']:
            import json
            keywords = json.loads(result['keywords_json'])
            if keywords:
                logger.info(f"  Schlagwörter: {parser.format_keywords_for_display(keywords)}")


def perform_backup(cfg: config.Config, include_archive: bool = False) -> None:
    """
    Erstellt ein Backup.
    
    Args:
        cfg: Konfigurationsobjekt
        include_archive: Ob das komplette Archiv gesichert werden soll
    """
    backup_target_dir = cfg.get_backup_target_dir()
    
    if not backup_target_dir:
        logger.error("Backup-Zielordner ist nicht konfiguriert. "
                    "Bitte mit --set-backup-target setzen.")
        return
    
    logger.info("=" * 60)
    logger.info("BACKUP ERSTELLEN")
    logger.info("=" * 60)
    
    try:
        backup_path = backup.create_backup(
            cfg.get_archiv_root(),
            cfg.get_db_path(),
            cfg.config_path,
            backup_target_dir,
            include_archive=include_archive
        )
        
        logger.info("=" * 60)
        logger.info(f"✓ Backup erfolgreich erstellt: {backup_path}")
        logger.info("=" * 60)
        
        # Alte Backups aufräumen
        backup.cleanup_old_backups(backup_target_dir, keep_count=10)
        
    except Exception as e:
        logger.error(f"Fehler beim Erstellen des Backups: {e}")


def main() -> None:
    """Hauptfunktion mit CLI-Argument-Parsing."""
    parser_cli = argparse.ArgumentParser(
        description="Werkstatt-Archiv - Automatische PDF-Archivierung",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  # Erstkonfiguration
  %(prog)s --set-input-folder "/Volumes/Server/Werkstatt/Scans/Eingang"
  %(prog)s --set-archiv-root "/Volumes/Server/Werkstatt/Archiv"
  %(prog)s --set-backup-target "/Volumes/Server/Werkstatt/Backups"
  
  # Einmalige Verarbeitung aller PDFs
  %(prog)s --process-input
  
  # Ordnerüberwachung starten
  %(prog)s --watch
  
  # Suche
  %(prog)s --search-auftrag 76329
  %(prog)s --search-name "Voigt"
  %(prog)s --search-keyword "Garantie"
  
  # Backup erstellen
  %(prog)s --backup
        """
    )
    
    # Modi
    mode_group = parser_cli.add_argument_group('Betriebsmodi')
    mode_group.add_argument('--process-input', action='store_true',
                           help='Verarbeite alle PDFs im Eingangsordner (Batch)')
    mode_group.add_argument('--watch', action='store_true',
                           help='Starte Ordnerüberwachung (automatische Verarbeitung)')
    
    # Konfiguration
    config_group = parser_cli.add_argument_group('Konfiguration')
    config_group.add_argument('--set-input-folder', metavar='PATH',
                             help='Setze Eingangsordner')
    config_group.add_argument('--set-archiv-root', metavar='PATH',
                             help='Setze Archivordner')
    config_group.add_argument('--set-db-path', metavar='PATH',
                             help='Setze Datenbank-Pfad')
    config_group.add_argument('--set-backup-target', metavar='PATH',
                             help='Setze Backup-Zielordner')
    
    # Suche
    search_group = parser_cli.add_argument_group('Suchfunktionen')
    search_group.add_argument('--search-auftrag', metavar='NR',
                             help='Suche nach Auftragsnummer')
    search_group.add_argument('--search-kunden-nr', metavar='NR',
                             help='Suche nach Kundennummer')
    search_group.add_argument('--search-name', metavar='NAME',
                             help='Suche nach Kundenname')
    search_group.add_argument('--search-kennzeichen', metavar='KFZ',
                             help='Suche nach Kennzeichen')
    search_group.add_argument('--search-keyword', metavar='KEYWORD',
                             help='Suche nach Schlagwort')
    
    # Backup
    backup_group = parser_cli.add_argument_group('Backup')
    backup_group.add_argument('--backup', action='store_true',
                             help='Erstelle Backup von Datenbank und Konfiguration')
    backup_group.add_argument('--include-archive', action='store_true',
                             help='Inkludiere komplettes Archiv im Backup (nur mit --backup)')
    
    # Allgemein
    parser_cli.add_argument('--verbose', '-v', action='store_true',
                           help='Aktiviere Debug-Logging')
    parser_cli.add_argument('--test-tesseract', action='store_true',
                           help='Teste Tesseract-Installation')
    
    args = parser_cli.parse_args()
    
    # Logging einrichten
    setup_logging(args.verbose)
    
    logger.info("Werkstatt-Archiv gestartet")
    
    # Tesseract-Test
    if args.test_tesseract:
        if ocr.test_tesseract():
            logger.info("✓ Tesseract ist korrekt installiert")
            sys.exit(0)
        else:
            logger.error("✗ Tesseract-Test fehlgeschlagen")
            sys.exit(1)
    
    # Konfiguration laden
    try:
        cfg = config.Config()
    except Exception as e:
        logger.error(f"Fehler beim Laden der Konfiguration: {e}")
        sys.exit(1)
    
    # Tesseract-Pfad setzen (falls konfiguriert)
    tesseract_cmd = cfg.get("tesseract_cmd")
    if tesseract_cmd:
        ocr.setup_tesseract(tesseract_cmd)
    
    # Poppler-Pfad setzen (falls konfiguriert)
    poppler_path = cfg.get("poppler_path")
    if poppler_path:
        poppler_bin = ocr.setup_poppler(poppler_path)
        if not poppler_bin:
            logger.warning("Konfigurierter Poppler-Pfad konnte nicht gefunden werden")
    else:
        # Auto-Detection
        poppler_bin = ocr.setup_poppler(None)
        if poppler_bin:
            logger.info("Poppler automatisch erkannt")
    
    # Konfiguration setzen
    if args.set_input_folder:
        cfg.set("input_folder", args.set_input_folder)
        logger.info(f"Eingangsordner gesetzt: {args.set_input_folder}")
        return
    
    if args.set_archiv_root:
        cfg.set("archiv_root", args.set_archiv_root)
        logger.info(f"Archivordner gesetzt: {args.set_archiv_root}")
        return
    
    if args.set_db_path:
        cfg.set("db_path", args.set_db_path)
        logger.info(f"Datenbank-Pfad gesetzt: {args.set_db_path}")
        return
    
    if args.set_backup_target:
        cfg.set("backup_target_dir", args.set_backup_target)
        logger.info(f"Backup-Zielordner gesetzt: {args.set_backup_target}")
        return
    
    # Konfiguration validieren
    errors = cfg.validate()
    if errors:
        logger.error("Konfigurationsfehler:")
        for error in errors:
            logger.error(f"  - {error}")
        logger.error("Bitte Konfiguration überprüfen (--set-input-folder, --set-archiv-root)")
        sys.exit(1)
    
    # Datenbank initialisieren
    try:
        db.init_db(cfg.get_db_path())
    except Exception as e:
        logger.error(f"Fehler beim Initialisieren der Datenbank: {e}")
        sys.exit(1)
    
    # Modi ausführen
    if args.process_input:
        process_input_folder(cfg)
    
    elif args.watch:
        watch_input_folder(cfg)
    
    elif any([args.search_auftrag, args.search_kunden_nr, args.search_name,
              args.search_kennzeichen, args.search_keyword]):
        perform_search(cfg, args)
    
    elif args.backup:
        perform_backup(cfg, include_archive=args.include_archive)
    
    else:
        parser_cli.print_help()
        logger.info("\nBitte einen Modus wählen (--process-input, --watch, --search-*, --backup)")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\nProgramm durch Benutzer unterbrochen")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unerwarteter Fehler: {e}", exc_info=True)
        sys.exit(1)
