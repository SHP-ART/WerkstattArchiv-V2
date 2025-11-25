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
    from PyPDF2 import PdfMerger, PdfReader, PdfWriter
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


def find_auftrag_page(texts: List[str]) -> Optional[int]:
    """
    Findet die Seite mit dem Werkstattauftrag (enthält Metadaten).
    
    Args:
        texts: Liste von OCR-Texten (ein Text pro Seite)
    
    Returns:
        Seitennummer (0-basiert) oder None wenn nicht gefunden
    """
    # Suche nach typischen Auftrag-Merkmalen
    auftrag_patterns = [
        r'Werkstattauftrag',
        r'Auftrag\s*Nr',
        r'Auftragsnummer',
        r'Kd\.?\s*Nr',
        r'Kundennummer',
        r'Kennzeichen.*:',
        r'Fahrzeug.*Kennzeichen'
    ]
    
    for i, text in enumerate(texts):
        # Zähle wie viele Patterns matchen
        matches = sum(1 for pattern in auftrag_patterns if re.search(pattern, text, re.IGNORECASE))
        
        # Wenn mindestens 3 Patterns matchen, ist es wahrscheinlich der Auftrag
        if matches >= 3:
            logger.debug(f"Auftrag erkannt auf Seite {i+1} ({matches}/{len(auftrag_patterns)} Patterns)")
            return i
    
    # Fallback: Erste Seite
    logger.warning("Konnte Auftrag nicht eindeutig identifizieren, verwende Seite 1")
    return 0


def split_pdf_extract_auftrag(pdf_path: Path, output_dir: Path, auftrag_nr: str, auftrag_page_index: int = 0) -> Tuple[Path, Path]:
    """
    Splittet eine PDF: Auftragsseite = Auftrag, ALLE Seiten = Daten.
    
    Args:
        pdf_path: Pfad zur Original-PDF
        output_dir: Ausgabe-Verzeichnis für gesplittete PDFs
        auftrag_nr: Auftragsnummer für Dateinamen
        auftrag_page_index: Index der Auftragsseite (0-basiert)
    
    Returns:
        Tuple: (Auftrag-PDF-Pfad, Daten-PDF-Pfad mit ALLEN Seiten)
    
    Raises:
        FolderImportError: Bei Fehlern beim Splitten
    """
    try:
        logger.info(f"📄 Splitte PDF: {pdf_path.name}")
        reader = PdfReader(str(pdf_path))
        total_pages = len(reader.pages)
        
        logger.info(f"   ℹ️  Gesamt: {total_pages} Seiten")
        logger.info(f"   ℹ️  Auftrag auf Seite: {auftrag_page_index + 1}")
        
        # Auftrag-PDF (nur Auftragsseite)
        auftrag_path = output_dir / f"{auftrag_nr}_Auftrag.pdf"
        writer_auftrag = PdfWriter()
        writer_auftrag.add_page(reader.pages[auftrag_page_index])
        
        with open(auftrag_path, 'wb') as f:
            writer_auftrag.write(f)
        
        logger.info(f"   ✓ Auftrag: {auftrag_path.name} (Seite {auftrag_page_index + 1})")
        
        # Daten-PDF (ALLE Seiten 1-N)
        daten_path = output_dir / f"{auftrag_nr}_Daten.pdf"
        writer_daten = PdfWriter()
        
        for page_num in range(0, total_pages):  # 0-basiert = alle Seiten
            writer_daten.add_page(reader.pages[page_num])
        
        with open(daten_path, 'wb') as f:
            writer_daten.write(f)
        
        logger.info(f"   ✓ Daten: {daten_path.name} (ALLE Seiten 1-{total_pages})")
        
        return auftrag_path, daten_path
        
    except Exception as e:
        raise FolderImportError(f"Fehler beim Splitten von {pdf_path.name}: {e}")


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
        
        # Temp-Verzeichnis für Splitting
        temp_dir = folder_path / ".temp_split"
        temp_dir.mkdir(exist_ok=True)
        
        # 3. PDFs verarbeiten (abhängig von ohne_auftrag)
        keywords = {}
        auftrag_pdf = None
        daten_pdf = None
        auftrag_page_index = 0  # Default: Seite 1
        
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
                
                # OCR (alle Seiten)
                texts = pdf_to_ocr_texts(pdf_path, max_pages=None)
                
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
            
            # OCR auf erster PDF (alle Seiten)
            logger.info(f"⏳ Starte OCR für {main_pdf.name}...")
            main_texts = pdf_to_ocr_texts(main_pdf, max_pages=None)
            logger.info(f"✓ OCR abgeschlossen: {len(main_texts)} Seiten erkannt")
            
            # Finde die Seite mit dem Auftrag
            logger.info(f"🔍 Suche Auftragsseite...")
            auftrag_page_index = find_auftrag_page(main_texts)
            if auftrag_page_index is None:
                auftrag_page_index = 0  # Fallback: Seite 1
            logger.info(f"✓ Auftrag gefunden auf Seite {auftrag_page_index + 1}")
            
            # Metadaten aus Auftragsseite extrahieren
            # Nutze Ordnernamen als Fallback für Auftragsnummer
            logger.info(f"🔍 Extrahiere Metadaten aus Seite {auftrag_page_index + 1}...")
            try:
                metadata = extract_auftrag_metadata(
                    main_texts[auftrag_page_index] if main_texts else "",
                    fallback_filename=folder_path.name  # Ordnername als Fallback
                )
                
                # VALIDIERUNG: Vergleiche OCR-Auftragsnummer mit Ordnername
                ocr_auftrag_nr = metadata.get("auftrag_nr")
                if ocr_auftrag_nr:
                    # Normalisiere beide für Vergleich (entferne führende Nullen)
                    ocr_normalized = str(int(ocr_auftrag_nr))
                    folder_normalized = str(int(auftrag_nr))
                    
                    if ocr_normalized != folder_normalized:
                        logger.warning(f"⚠️  Auftragsnummer-Konflikt erkannt!")
                        logger.warning(f"   Ordnername: {auftrag_nr}")
                        logger.warning(f"   Im PDF gefunden: {ocr_auftrag_nr}")
                        logger.warning(f"   Formular-Typ: {metadata.get('formular_version', 'unbekannt')}")
                        logger.warning(f"   → Verwende Ordnername als korrekte Auftragsnummer")
                    else:
                        logger.info(f"✓ Auftragsnummer validiert: {auftrag_nr} (stimmt mit PDF überein)")
                        logger.info(f"  Formular-Typ: {metadata.get('formular_version', 'unbekannt')}")
                else:
                    logger.info(f"ℹ️  Auftragsnummer nur aus Ordnername: {auftrag_nr} (nicht im PDF gefunden)")
                    
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
            logger.info(f"✓ Metadaten extrahiert:")
            logger.info(f"   • Auftragsnr: {auftrag_nr}")
            logger.info(f"   • Kunde: {metadata.get('name', 'N/A')}")
            logger.info(f"   • Kennzeichen: {metadata.get('kennzeichen', 'N/A')}")
            logger.info(f"   • Datum: {metadata.get('datum', 'N/A')}")
            
            # Schlagwörter aus allen Seiten der ersten PDF
            logger.info(f"🔍 Suche Schlagwörter in {len(main_texts)} Seiten...")
            keywords = extract_keywords_from_pages(
                main_texts,
                config.get_keywords()
            )
            if keywords:
                logger.info(f"✓ Schlagwörter gefunden: {', '.join(keywords.keys())}")
            else:
                logger.info(f"ℹ️  Keine Schlagwörter gefunden")
        
            # 4. Weitere PDFs verarbeiten (nur Schlagwörter)
            if len(pdf_paths) > 1:
                logger.info(f"\n📑 Verarbeite {len(pdf_paths) - 1} weitere PDF(s) (Anhänge)...")
                
                for i, additional_pdf in enumerate(pdf_paths[1:], 2):
                    logger.info(f"  [{i}/{len(pdf_paths)}] {additional_pdf.name}")
                    logger.info(f"      ⏳ OCR läuft...")
                    
                    # OCR auf weiterer PDF (alle Seiten)
                    additional_texts = pdf_to_ocr_texts(additional_pdf, max_pages=None)
                    logger.info(f"      ✓ {len(additional_texts)} Seiten erkannt")
                    
                    # Schlagwörter extrahieren
                    additional_keywords = extract_keywords_from_pages(
                        additional_texts,
                        config.get_keywords()
                    )
                    if additional_keywords:
                        logger.info(f"      ✓ Schlagwörter: {', '.join(additional_keywords.keys())}")
                    else:
                        logger.info(f"      ℹ️  Keine Schlagwörter")
                    
                    # Schlagwörter zusammenführen (Seitenzahlen anpassen)
                    offset = sum(len(pdf_to_ocr_texts(p, max_pages=None)) 
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
        
        # 5. PDF Splitting: Seite 1 = Auftrag, Rest = Daten
        logger.info(f"\n✂️  PDF-Splitting...")
        
        if ohne_auftrag:
            # OHNE AUFTRAG: Alle PDFs zu einer Anhang-PDF
            logger.info(f"Modus: OHNE AUFTRAG - erstelle nur Anhang-PDF")
            anhang_name = f"{auftrag_nr}_OA.pdf"
            anhang_path = temp_dir / anhang_name
            merge_pdfs(pdf_paths, anhang_path)
            auftrag_pdf = anhang_path  # Wird als "final_pdf" für Archivierung genutzt
            daten_pdf = None
        else:
            # MIT AUFTRAG: Split erste PDF in Auftrag + Daten (Daten enthält ALLE Seiten)
            main_pdf = pdf_paths[0]
            auftrag_pdf, daten_pdf = split_pdf_extract_auftrag(main_pdf, temp_dir, auftrag_nr, auftrag_page_index)
            
            # Falls weitere PDFs vorhanden, an Daten-PDF anhängen
            if len(pdf_paths) > 1:
                logger.info(f"\n📎 Füge {len(pdf_paths) - 1} weitere PDF(s) zu Daten-PDF hinzu...")
                
                # Liste für Merge: [Daten-PDF (enthält bereits alle Seiten der ersten PDF), weitere PDFs...]
                pdfs_to_merge = [daten_pdf] + pdf_paths[1:]
                
                # Neue kombinierte Daten-PDF
                combined_daten = temp_dir / f"{auftrag_nr}_Daten_komplett.pdf"
                merge_pdfs(pdfs_to_merge, combined_daten)
                
                # Alte Daten-PDF löschen, neue verwenden
                if daten_pdf.exists():
                    daten_pdf.unlink()
                daten_pdf = combined_daten
                
                logger.info(f"   ✓ Kombinierte Daten-PDF: {daten_pdf.name}")
        
        logger.info(f"✓ Auftrag-PDF: {auftrag_pdf.name}")
        if daten_pdf:
            logger.info(f"✓ Daten-PDF: {daten_pdf.name}")
        
        # 6. Ins Archiv verschieben (BEIDE PDFs)
        logger.info(f"\n📦 Archivierung...")
        logger.info(f"   ⏳ Berechne Ziel-Ordner...")
        
        # Config-Dict vorbereiten
        archive_config = {
            "auftragsnummer_pad_length": 6,
            "use_thousand_blocks": config.config.get("use_thousand_blocks", True),
            "use_year_folders": config.config.get("use_year_folders", True),
            "dateiname_pattern": config.config.get("dateiname_pattern", "{auftrag_nr}_Auftrag{version_suffix}.pdf")
        }
        
        # Auftrag-PDF archivieren
        logger.info(f"   ⏳ Verschiebe Auftrag-PDF ins Archiv...")
        archive_path_auftrag, file_hash_auftrag = move_to_archive(
            auftrag_pdf,
            config.get_archiv_root(),
            auftrag_nr,
            archive_config,
            metadata
        )
        logger.info(f"   ✓ Auftrag archiviert: {archive_path_auftrag.name}")
        
        # Daten-PDF archivieren (falls vorhanden)
        archive_path_daten = None
        if daten_pdf:
            logger.info(f"   ⏳ Verschiebe Daten-PDF ins Archiv...")
            
            # Temporär Dateiname-Pattern für Daten-PDF anpassen
            archive_config_daten = archive_config.copy()
            archive_config_daten["dateiname_pattern"] = "{auftrag_nr}_Daten{version_suffix}.pdf"
            
            archive_path_daten, _ = move_to_archive(
                daten_pdf,
                config.get_archiv_root(),
                auftrag_nr,
                archive_config_daten,
                metadata
            )
            logger.info(f"   ✓ Daten archiviert: {archive_path_daten.name}")
        
        logger.info(f"   ✓ Ordner: {archive_path_auftrag.parent}")
        
        # 7. In Datenbank eintragen
        logger.info(f"\n💾 Datenbank-Eintrag...")
        logger.info(f"   ⏳ Erstelle Auftrag in Datenbank...")
        
        auftrag_id = insert_auftrag(
            config.get_db_path(),
            metadata,
            keywords,
            archive_path_auftrag,
            file_hash_auftrag
        )
        logger.info(f"   ✓ Gespeichert mit ID: {auftrag_id}")
        
        # 8. Aufräumen: Temp-Ordner und Original-Ordner löschen
        logger.info(f"\n🧹 Räume auf...")
        try:
            # Temp-Verzeichnis löschen
            if temp_dir.exists():
                shutil.rmtree(temp_dir)
                logger.debug(f"   ✓ Temp-Ordner gelöscht")
            
            # Original-Ordner löschen
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
            "split": not ohne_auftrag,
            "ohne_auftrag": ohne_auftrag,
            "archive_path_auftrag": str(archive_path_auftrag),
            "archive_path_daten": str(archive_path_daten) if archive_path_daten else None,
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
