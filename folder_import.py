#!/usr/bin/env python3
"""
Ordner-Import: Importiert Aufträge aus Ordner-Struktur.

Ordner-Name = Auftragsnummer
- Erste PDF: Hauptauftrag (Metadaten-Extraktion)
- Weitere PDFs: Nur Schlagwörter
- Alle PDFs werden zu einer Gesamt-PDF zusammengefügt
"""

import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import shutil
import re
from datetime import datetime

# PDF-Manipulation
try:
    from PyPDF2 import PdfMerger, PdfReader
except ImportError:
    print("❌ PyPDF2 nicht installiert. Führe aus: pip install PyPDF2")
    exit(1)

# Lokale Module
from config import Config
from ocr import pdf_to_ocr_texts
from parser import extract_auftrag_metadata, extract_keywords_from_pages
from archive import format_auftrag_nr, move_to_archive
from db import insert_auftrag

logger = logging.getLogger(__name__)


class FolderImportError(Exception):
    """Fehler beim Ordner-Import."""
    pass


def extract_auftrag_nr_from_folder(folder_name: str) -> Optional[str]:
    """
    Extrahiert Auftragsnummer aus Ordnername.
    
    Beispiele:
        "076329" → "076329"
        "76329" → "076329"
        "Auftrag 76329" → "076329"
        "76329_Komplett" → "076329"
    
    Args:
        folder_name: Name des Ordners
    
    Returns:
        Auftragsnummer (6-stellig, normalisiert) oder None
    """
    # Versuche direkte Nummer zu finden
    match = re.search(r'\d{4,6}', folder_name)
    if match:
        nummer = match.group()
        return format_auftrag_nr(nummer)
    
    return None


def find_pdfs_in_folder(folder_path: Path) -> List[Path]:
    """
    Findet alle PDF-Dateien in einem Ordner (nicht rekursiv).
    
    Args:
        folder_path: Pfad zum Ordner
    
    Returns:
        Liste der PDF-Pfade, sortiert nach Name
    """
    if not folder_path.is_dir():
        raise FolderImportError(f"Kein gültiger Ordner: {folder_path}")
    
    pdfs = sorted(folder_path.glob("*.pdf"))
    if not pdfs:
        raise FolderImportError(f"Keine PDF-Dateien im Ordner: {folder_path}")
    
    return pdfs


def merge_pdfs(pdf_paths: List[Path], output_path: Path) -> None:
    """
    Fügt mehrere PDFs zu einer Gesamt-PDF zusammen.
    
    Args:
        pdf_paths: Liste der zu mergenden PDFs
        output_path: Pfad für die Ausgabe-PDF
    
    Raises:
        FolderImportError: Bei Fehlern beim Mergen
    """
    try:
        logger.info(f"Merge {len(pdf_paths)} PDFs zu: {output_path.name}")
        
        merger = PdfMerger()
        
        for pdf_path in pdf_paths:
            logger.debug(f"  + {pdf_path.name}")
            merger.append(str(pdf_path))
        
        # Ausgabe-Verzeichnis erstellen
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Zusammenführen
        merger.write(str(output_path))
        merger.close()
        
        logger.info(f"✓ PDFs erfolgreich zusammengefügt: {output_path.name}")
        
    except Exception as e:
        raise FolderImportError(f"Fehler beim Mergen der PDFs: {e}")


def process_folder_for_import(
    folder_path: Path,
    config: Config,
    merge_pdfs_flag: bool = True,
    ohne_auftrag: bool = False
) -> Dict[str, Any]:
    """
    Verarbeitet einen Ordner für den Import.
    
    NEUE LOGIK:
    - Erste PDF = Auftrag (Seite 1) → separate PDF
    - Weitere PDFs = Anhang → kombiniert in einer Anhang-PDF
    - Keine vollständige Zusammenführung mehr!
    
    Workflow:
    1. Auftragsnummer aus Ordnername extrahieren
    2. Alle PDFs im Ordner finden
    3. MIT Auftrag: 
       - Erste PDF → Seite 1 extrahieren = Auftrag-PDF + Metadaten
       - Rest der ersten PDF + weitere PDFs = Anhang-PDF
    4. OHNE Auftrag: 
       - Alle PDFs = Anhang-PDF, nur Schlagwörter
    5. In Datenbank eintragen
    6. Ins Archiv verschieben
    
    Args:
        folder_path: Pfad zum Ordner
        config: Config-Objekt
        merge_pdfs_flag: DEPRECATED (wird ignoriert, neue Logik immer aktiv)
        ohne_auftrag: True = Kein Auftrag, nur Schlagwörter (Dateiname: _OA.pdf)
    
    Returns:
        Dictionary mit Ergebnis-Informationen
    
    Raises:
        FolderImportError: Bei Fehlern
    """
    try:
        logger.info(f"=" * 60)
        logger.info(f"Verarbeite Ordner: {folder_path.name}")
        logger.info(f"=" * 60)
        
        # 1. Auftragsnummer extrahieren
        auftrag_nr = extract_auftrag_nr_from_folder(folder_path.name)
        if not auftrag_nr:
            raise FolderImportError(
                f"Keine Auftragsnummer im Ordnername gefunden: {folder_path.name}"
            )
        
        logger.info(f"✓ Auftragsnummer: {auftrag_nr}")
        
        # 2. PDFs finden
        pdf_paths = find_pdfs_in_folder(folder_path)
        logger.info(f"✓ Gefunden: {len(pdf_paths)} PDF-Dateien")
        for i, pdf in enumerate(pdf_paths, 1):
            logger.info(f"  [{i}] {pdf.name}")
        
        # Import pdf_split
        from pdf_split import split_pdf_auftrag_anhang, combine_pdfs_to_anhang, PDFSplitError
        
        # Temp-Verzeichnis für Splitting
        temp_dir = folder_path / ".temp_split"
        temp_dir.mkdir(exist_ok=True)
        
        # 3. PDFs verarbeiten (abhängig von ohne_auftrag)
        keywords = {}
        auftrag_pdf = None
        anhang_pdf = None
        
        if ohne_auftrag:
            # OHNE AUFTRAG: Alle PDFs → Eine Anhang-PDF (keine Auftrag-PDF)
            logger.info(f"\n📑 Modus: OHNE AUFTRAG (OA)")
            logger.info(f"Erstelle Anhang-PDF aus {len(pdf_paths)} Datei(en)")
            
            metadata = {
                "auftrag_nr": auftrag_nr,
                "name": None,
                "kunden_nr": None,
                "datum": None,
                "kennzeichen": None,
                "vin": None,
                "formular_version": "oa"
            }
            
            page_offset = 0
            for i, pdf_path in enumerate(pdf_paths, 1):
                logger.info(f"  [{i}] {pdf_path.name}")
                
                # OCR
                texts = pdf_to_ocr_texts(pdf_path, max_pages=10)
                
                # Schlagwörter extrahieren
                pdf_keywords = extract_keywords_from_pages(texts, config.get_keywords())
                
                # Seitenzahlen anpassen
                for keyword, pages in pdf_keywords.items():
                    adjusted_pages = [p + page_offset for p in pages]
                    if keyword in keywords:
                        keywords[keyword].extend(adjusted_pages)
                        keywords[keyword] = sorted(list(set(keywords[keyword])))
                    else:
                        keywords[keyword] = adjusted_pages
                
                logger.info(f"    → {len(pdf_keywords)} Schlagwörter")
                page_offset += len(texts)
            
        else:
            # MIT AUFTRAG: Erste PDF = Metadaten, Rest = Schlagwörter
            main_pdf = pdf_paths[0]
            logger.info(f"\n📄 Verarbeite Hauptauftrag: {main_pdf.name}")
            
            # OCR auf erster PDF
            main_texts = pdf_to_ocr_texts(main_pdf, max_pages=10)
            logger.info(f"✓ OCR: {len(main_texts)} Seiten erkannt")
            
            # Metadaten aus erster Seite extrahieren
            # Nutze Ordnernamen als Fallback für Auftragsnummer
            try:
                metadata = extract_auftrag_metadata(
                    main_texts[0] if main_texts else "",
                    fallback_filename=folder_path.name  # Ordnername als Fallback
                )
            except Exception as e:
                # Wenn Metadaten-Extraktion fehlschlägt, nutze Basis-Metadaten
                logger.warning(f"Metadaten-Extraktion fehlgeschlagen: {e}")
                logger.info(f"Nutze Basis-Metadaten mit Auftragsnummer aus Ordnername")
                metadata = {
                    "auftrag_nr": auftrag_nr,
                    "auftrag_nr_from_ocr": False,
                    "kunden_nr": None,
                    "name": None,
                    "datum": None,
                    "kennzeichen": None,
                    "vin": None,
                    "formular_version": "unbekannt"
                }
            
            # Auftragsnummer überschreiben (Ordnername hat immer Priorität)
            metadata["auftrag_nr"] = auftrag_nr
            logger.info(f"✓ Metadaten: Kunde={metadata.get('name', 'N/A')}, "
                       f"KZ={metadata.get('kennzeichen', 'N/A')}")
            
            # Schlagwörter aus allen Seiten der ersten PDF
            keywords = extract_keywords_from_pages(
                main_texts,
                config.get_keywords()
            )
            logger.info(f"✓ Schlagwörter (Haupt-PDF): {len(keywords)} gefunden")
        
            # 4. Weitere PDFs verarbeiten (nur Schlagwörter)
            if len(pdf_paths) > 1:
                logger.info(f"\n📑 Verarbeite {len(pdf_paths) - 1} weitere PDF(s)...")
                
                for i, additional_pdf in enumerate(pdf_paths[1:], 2):
                    logger.info(f"  [{i}] {additional_pdf.name}")
                    
                    # OCR auf weiterer PDF
                    additional_texts = pdf_to_ocr_texts(additional_pdf, max_pages=10)
                    
                    # Schlagwörter extrahieren
                    additional_keywords = extract_keywords_from_pages(
                        additional_texts,
                        config.get_keywords()
                    )
                    
                    # Schlagwörter zusammenführen (Seitenzahlen anpassen)
                    offset = sum(len(pdf_to_ocr_texts(p, max_pages=10)) 
                               for p in pdf_paths[:i-1])
                    
                    for keyword, pages in additional_keywords.items():
                        adjusted_pages = [p + offset for p in pages]
                        if keyword in keywords:
                            keywords[keyword].extend(adjusted_pages)
                            keywords[keyword] = sorted(list(set(keywords[keyword])))
                        else:
                            keywords[keyword] = adjusted_pages
                    
                    logger.info(f"    → {len(additional_keywords)} Schlagwörter")
        
        logger.info(f"\n✓ GESAMT: {len(keywords)} eindeutige Schlagwörter")
        for kw, pages in sorted(keywords.items()):
            logger.info(f"  - {kw}: Seiten {pages}")
        
        # 5. PDFs zusammenfügen (optional)
        if merge_pdfs_flag and len(pdf_paths) > 1:
            logger.info(f"\n🔗 Füge {len(pdf_paths)} PDFs zusammen...")
            
            # Dateiname abhängig von ohne_auftrag
            if ohne_auftrag:
                merged_name = f"{auftrag_nr}_OA.pdf"
            else:
                merged_name = f"{auftrag_nr}_Komplett.pdf"
            
            merged_path = folder_path / merged_name
            
            merge_pdfs(pdf_paths, merged_path)
            
            # Gemergtes PDF wird verwendet
            final_pdf = merged_path
            logger.info(f"✓ Verwende gemergtes PDF: {merged_name}")
        else:
            # Nur erste PDF verwenden
            final_pdf = pdf_paths[0]
            logger.info(f"✓ Verwende erste PDF: {final_pdf.name}")
        
        # 6. Ins Archiv verschieben
        logger.info(f"\n📦 Verschiebe ins Archiv...")
        
        # Config-Dict vorbereiten
        archive_config = {
            "auftragsnummer_pad_length": 6,
            "use_thousand_blocks": config.config.get("use_thousand_blocks", True),
            "use_year_folders": config.config.get("use_year_folders", True),
            "dateiname_pattern": config.config.get("dateiname_pattern", "{auftrag_nr}_Auftrag{version_suffix}.pdf")
        }
        
        archive_path, file_hash = move_to_archive(
            final_pdf,
            config.get_archiv_root(),
            auftrag_nr,
            archive_config,
            metadata
        )
        logger.info(f"✓ Archiviert: {archive_path}")
        
        # 7. In Datenbank eintragen
        logger.info(f"\n💾 Speichere in Datenbank...")
        
        auftrag_id = insert_auftrag(
            config.get_db_path(),
            metadata,
            keywords,
            archive_path,
            file_hash
        )
        logger.info(f"✓ Datenbank-ID: {auftrag_id}")
        
        # 8. Aufräumen: Ordner löschen (PDFs wurden archiviert)
        if merge_pdfs_flag and len(pdf_paths) > 1:
            # Gemergtes PDF wurde verschoben, Originale löschen
            logger.info(f"\n🧹 Räume auf...")
            try:
                shutil.rmtree(folder_path)
                logger.info(f"✓ Ordner gelöscht: {folder_path.name}")
            except Exception as e:
                logger.warning(f"⚠️  Konnte Ordner nicht löschen: {e}")
        
        # Ergebnis
        result = {
            "success": True,
            "auftrag_nr": auftrag_nr,
            "auftrag_id": auftrag_id,
            "pdf_count": len(pdf_paths),
            "merged": merge_pdfs_flag and len(pdf_paths) > 1,
            "ohne_auftrag": ohne_auftrag,
            "archive_path": str(archive_path),
            "keywords": list(keywords.keys()),
            "metadata": metadata
        }
        
        logger.info(f"\n" + "=" * 60)
        logger.info(f"✅ ORDNER ERFOLGREICH IMPORTIERT")
        logger.info(f"=" * 60)
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Fehler beim Ordner-Import: {e}")
        raise FolderImportError(f"Import fehlgeschlagen: {e}")


def import_multiple_folders(
    root_path: Path,
    config: Config,
    merge_pdfs_flag: bool = True,
    ohne_auftrag: bool = False,
    dry_run: bool = False
) -> List[Dict[str, Any]]:
    """
    Importiert alle Ordner in einem Verzeichnis.
    
    Args:
        root_path: Pfad zum Verzeichnis mit Ordnern
        config: Config-Objekt
        merge_pdfs_flag: PDFs zusammenfügen?
        ohne_auftrag: True = Kein Auftrag (nur Schlagwörter, _OA.pdf)
        dry_run: Nur Simulation ohne tatsächlichen Import
    
    Returns:
        Liste mit Ergebnissen für jeden Ordner
    """
    if not root_path.is_dir():
        raise FolderImportError(f"Kein gültiges Verzeichnis: {root_path}")
    
    # Alle Unterordner finden
    folders = [f for f in root_path.iterdir() if f.is_dir()]
    
    if not folders:
        logger.warning(f"Keine Ordner gefunden in: {root_path}")
        return []
    
    logger.info(f"Gefunden: {len(folders)} Ordner")
    
    results = []
    success_count = 0
    error_count = 0
    
    for folder in folders:
        try:
            if dry_run:
                logger.info(f"\n[DRY-RUN] Würde verarbeiten: {folder.name}")
                # Nur Auftragsnummer extrahieren
                auftrag_nr = extract_auftrag_nr_from_folder(folder.name)
                pdfs = find_pdfs_in_folder(folder)
                logger.info(f"  → Auftragsnr: {auftrag_nr}")
                logger.info(f"  → PDFs: {len(pdfs)}")
                results.append({
                    "success": True,
                    "dry_run": True,
                    "folder": folder.name,
                    "auftrag_nr": auftrag_nr,
                    "pdf_count": len(pdfs)
                })
                success_count += 1
            else:
                result = process_folder_for_import(folder, config, merge_pdfs_flag, ohne_auftrag)
                results.append(result)
                success_count += 1
        
        except Exception as e:
            logger.error(f"❌ Fehler bei {folder.name}: {e}")
            results.append({
                "success": False,
                "folder": folder.name,
                "error": str(e)
            })
            error_count += 1
    
    # Zusammenfassung
    logger.info(f"\n" + "=" * 60)
    logger.info(f"ZUSAMMENFASSUNG")
    logger.info(f"=" * 60)
    logger.info(f"Gesamt:       {len(folders)}")
    logger.info(f"Erfolgreich:  {success_count}")
    logger.info(f"Fehler:       {error_count}")
    
    return results


if __name__ == "__main__":
    import sys
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s: %(message)s'
    )
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  Einzelner Ordner:")
        print("    python3 folder_import.py /path/to/folder")
        print()
        print("  Mehrere Ordner:")
        print("    python3 folder_import.py /path/to/folders --batch")
        print()
        print("  Optionen:")
        print("    --no-merge    : PDFs NICHT zusammenfügen")
        print("    --oa          : OHNE AUFTRAG (nur Schlagwörter, Dateiname: _OA.pdf)")
        print("    --dry-run     : Simulation ohne Import")
        print()
        print("  Beispiele:")
        print("    python3 folder_import.py 076329/")
        print("    python3 folder_import.py 076329/ --oa")
        print("    python3 folder_import.py Import/ --batch --oa")
        sys.exit(1)
    
    # Argumente parsen
    folder_path = Path(sys.argv[1])
    batch_mode = "--batch" in sys.argv
    merge = "--no-merge" not in sys.argv
    ohne_auftrag = "--oa" in sys.argv
    dry_run = "--dry-run" in sys.argv
    
    # Config laden
    config = Config()
    
    try:
        if batch_mode:
            # Mehrere Ordner
            import_multiple_folders(folder_path, config, merge, ohne_auftrag, dry_run)
        else:
            # Einzelner Ordner
            if dry_run:
                logger.info("[DRY-RUN] Simulation - kein tatsächlicher Import")
            
            if ohne_auftrag:
                logger.info("[OHNE AUFTRAG] Nur Schlagwörter, Dateiname: _OA.pdf")
            
            result = process_folder_for_import(folder_path, config, merge, ohne_auftrag)
            
            if result["success"]:
                print(f"\n✅ Import erfolgreich!")
                print(f"   Auftrag: {result['auftrag_nr']}")
                print(f"   Modus: {'OHNE AUFTRAG (OA)' if ohne_auftrag else 'MIT AUFTRAG'}")
                print(f"   PDFs: {result['pdf_count']}")
                print(f"   Archiv: {result['archive_path']}")
    
    except FolderImportError as e:
        logger.error(f"❌ {e}")
        sys.exit(1)
