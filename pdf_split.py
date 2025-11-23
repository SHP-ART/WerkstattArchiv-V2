#!/usr/bin/env python3
"""
PDF-Splitting: Trennt PDFs in Auftrag (Seite 1) und Anhang (Rest).

Neue Logik:
- Auftrag = Seite 1 → separate PDF (z.B. 076329_Auftrag.pdf)
- Anhang = Seiten 2-N → separate PDF (z.B. 076329_Anhang_S2-10.pdf)
"""

import logging
from pathlib import Path
from typing import Tuple, Optional

try:
    from PyPDF2 import PdfReader, PdfWriter
except ImportError:
    print("❌ PyPDF2 nicht installiert. Führe aus: pip install PyPDF2")
    exit(1)

logger = logging.getLogger(__name__)


class PDFSplitError(Exception):
    """Fehler beim Aufteilen einer PDF."""
    pass


def split_pdf_auftrag_anhang(
    input_pdf: Path,
    output_dir: Path,
    auftrag_nr: str
) -> Tuple[Path, Optional[Path]]:
    """
    Teilt PDF in Auftrag (Seite 1) und Anhang (Rest) auf.
    
    Args:
        input_pdf: Pfad zur Eingabe-PDF
        output_dir: Verzeichnis für Ausgabe-PDFs
        auftrag_nr: Auftragsnummer (für Dateinamen)
    
    Returns:
        Tuple (auftrag_pdf_path, anhang_pdf_path)
        anhang_pdf_path ist None, wenn nur 1 Seite vorhanden
    
    Raises:
        PDFSplitError: Bei Fehlern beim Aufteilen
    """
    try:
        logger.info(f"📄 Teile PDF auf: {input_pdf.name}")
        
        # PDF öffnen
        reader = PdfReader(str(input_pdf))
        num_pages = len(reader.pages)
        
        logger.info(f"  → {num_pages} Seiten erkannt")
        
        if num_pages == 0:
            raise PDFSplitError("PDF hat keine Seiten")
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 1. Auftrag-PDF erstellen (nur Seite 1)
        auftrag_pdf_path = output_dir / f"{auftrag_nr}_Auftrag.pdf"
        writer_auftrag = PdfWriter()
        writer_auftrag.add_page(reader.pages[0])
        
        with open(auftrag_pdf_path, 'wb') as f:
            writer_auftrag.write(f)
        
        logger.info(f"  ✓ Auftrag-PDF: {auftrag_pdf_path.name} (Seite 1)")
        
        # 2. Anhang-PDF erstellen (Seiten 2-N), falls vorhanden
        anhang_pdf_path = None
        if num_pages > 1:
            # Dateiname mit Seitenzahlen
            anhang_pdf_path = output_dir / f"{auftrag_nr}_Anhang_S2-{num_pages}.pdf"
            writer_anhang = PdfWriter()
            
            for page_num in range(1, num_pages):  # Seiten 2 bis N (Index 1 bis N-1)
                writer_anhang.add_page(reader.pages[page_num])
            
            with open(anhang_pdf_path, 'wb') as f:
                writer_anhang.write(f)
            
            logger.info(f"  ✓ Anhang-PDF: {anhang_pdf_path.name} (Seiten 2-{num_pages})")
        else:
            logger.info(f"  ℹ Kein Anhang (nur 1 Seite)")
        
        return auftrag_pdf_path, anhang_pdf_path
        
    except Exception as e:
        logger.error(f"Fehler beim Aufteilen der PDF: {e}")
        raise PDFSplitError(f"PDF-Split fehlgeschlagen: {e}")


def combine_pdfs_to_anhang(
    pdf_paths: list[Path],
    output_path: Path,
    start_page: int = 2
) -> None:
    """
    Kombiniert mehrere PDFs zu einer Anhang-PDF.
    
    Args:
        pdf_paths: Liste der zu kombinierenden PDFs
        output_path: Pfad für Ausgabe-PDF
        start_page: Startseite für Nummerierung im Dateinamen
    
    Raises:
        PDFSplitError: Bei Fehlern beim Kombinieren
    """
    try:
        logger.info(f"📑 Kombiniere {len(pdf_paths)} PDFs zu Anhang...")
        
        writer = PdfWriter()
        total_pages = 0
        
        for pdf_path in pdf_paths:
            reader = PdfReader(str(pdf_path))
            num_pages = len(reader.pages)
            
            for page_num in range(num_pages):
                writer.add_page(reader.pages[page_num])
            
            total_pages += num_pages
            logger.info(f"  + {pdf_path.name}: {num_pages} Seiten")
        
        # Speichern
        with open(output_path, 'wb') as f:
            writer.write(f)
        
        logger.info(f"  ✓ Anhang-PDF: {output_path.name} (Gesamt: {total_pages} Seiten)")
        
    except Exception as e:
        logger.error(f"Fehler beim Kombinieren der PDFs: {e}")
        raise PDFSplitError(f"PDF-Kombination fehlgeschlagen: {e}")


def extract_pages_from_pdf(
    input_pdf: Path,
    output_pdf: Path,
    start_page: int,
    end_page: Optional[int] = None
) -> None:
    """
    Extrahiert Seiten aus einer PDF.
    
    Args:
        input_pdf: Eingabe-PDF
        output_pdf: Ausgabe-PDF
        start_page: Startseite (1-basiert)
        end_page: Endseite (1-basiert, None = bis Ende)
    
    Raises:
        PDFSplitError: Bei Fehlern
    """
    try:
        reader = PdfReader(str(input_pdf))
        num_pages = len(reader.pages)
        
        # Validierung
        if start_page < 1 or start_page > num_pages:
            raise PDFSplitError(f"Ungültige Startseite: {start_page}")
        
        if end_page is None:
            end_page = num_pages
        elif end_page < start_page or end_page > num_pages:
            raise PDFSplitError(f"Ungültige Endseite: {end_page}")
        
        # Extraktion
        writer = PdfWriter()
        for page_num in range(start_page - 1, end_page):  # 0-basiert
            writer.add_page(reader.pages[page_num])
        
        # Speichern
        output_pdf.parent.mkdir(parents=True, exist_ok=True)
        with open(output_pdf, 'wb') as f:
            writer.write(f)
        
        logger.info(f"  ✓ Seiten {start_page}-{end_page} extrahiert: {output_pdf.name}")
        
    except Exception as e:
        logger.error(f"Fehler beim Extrahieren von Seiten: {e}")
        raise PDFSplitError(f"Seiten-Extraktion fehlgeschlagen: {e}")


if __name__ == '__main__':
    # Test
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python pdf_split.py <input.pdf> <auftrag_nr>")
        sys.exit(1)
    
    logging.basicConfig(level=logging.INFO)
    
    input_file = Path(sys.argv[1])
    auftrag_nr = sys.argv[2]
    output_dir = Path("test_split")
    
    try:
        auftrag_pdf, anhang_pdf = split_pdf_auftrag_anhang(input_file, output_dir, auftrag_nr)
        print(f"\n✓ Auftrag: {auftrag_pdf}")
        if anhang_pdf:
            print(f"✓ Anhang: {anhang_pdf}")
    except PDFSplitError as e:
        print(f"\n✗ Fehler: {e}")
        sys.exit(1)
