"""
Alternative OCR-Implementierung mit EasyOCR (ohne Tesseract).

EasyOCR ist ein Deep Learning-basiertes OCR-System, das keine externe
Installation benötigt. Alles läuft über Python-Pakete.

WICHTIG: Installiere mit:
    pip install easyocr --no-deps
    pip install torch torchvision opencv-python-headless scipy numpy Pillow python-bidi PyYAML
"""

from pathlib import Path
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)

# Lazy Import - nur laden wenn benötigt
_easyocr_reader = None


class OCRError(Exception):
    """Fehler bei der OCR-Verarbeitung."""
    pass


def _get_easyocr_reader():
    """
    Erstellt oder gibt den EasyOCR Reader zurück (Singleton).
    Lädt die Modelle beim ersten Aufruf herunter (~100 MB).
    """
    global _easyocr_reader
    
    if _easyocr_reader is None:
        try:
            import easyocr
            logger.info("Initialisiere EasyOCR Reader (einmalig, lädt Modelle...)")
            logger.info("Dies kann beim ersten Mal 1-2 Minuten dauern.")
            
            # Erstelle Reader für Deutsch und Englisch
            _easyocr_reader = easyocr.Reader(['de', 'en'], gpu=False)
            
            logger.info("✓ EasyOCR Reader erfolgreich initialisiert")
        except ImportError:
            raise OCRError(
                "EasyOCR nicht installiert. Bitte installieren mit:\n"
                "pip install easyocr"
            )
        except Exception as e:
            raise OCRError(f"Fehler beim Initialisieren von EasyOCR: {e}")
    
    return _easyocr_reader


def pdf_to_images(pdf_path: Path, dpi: int = 300) -> List:
    """
    Konvertiert PDF-Seiten in PIL-Images.
    
    Args:
        pdf_path: Pfad zur PDF-Datei
        dpi: Auflösung für die Konvertierung (Standard: 300)
    
    Returns:
        Liste von PIL.Image-Objekten
    """
    try:
        from pdf2image import convert_from_path
    except ImportError:
        raise OCRError(
            "pdf2image nicht installiert. Bitte installieren mit:\n"
            "pip install pdf2image Pillow"
        )
    
    try:
        images = convert_from_path(str(pdf_path), dpi=dpi)
        logger.info(f"PDF in {len(images)} Seite(n) konvertiert")
        return images
    except Exception as e:
        raise OCRError(f"Fehler beim Konvertieren der PDF: {e}")


def image_to_text_easyocr(image, detail: int = 0) -> str:
    """
    Führt OCR auf einem Bild mit EasyOCR aus.
    
    Args:
        image: PIL.Image-Objekt
        detail: Detail-Level (0=nur Text, 1=mit Konfidenz, 2=mit Bounding Boxes)
    
    Returns:
        Extrahierter Text
    """
    try:
        import numpy as np
        
        # PIL Image zu NumPy Array konvertieren
        img_array = np.array(image)
        
        # EasyOCR ausführen
        reader = _get_easyocr_reader()
        results = reader.readtext(img_array, detail=detail)
        
        # Text extrahieren
        if detail == 0:
            # results ist bereits eine Liste von Strings
            text = '\n'.join(results)
        else:
            # results ist Liste von Tupeln: (bbox, text, confidence)
            text = '\n'.join([item[1] for item in results])
        
        return text
    
    except Exception as e:
        raise OCRError(f"Fehler bei EasyOCR: {e}")


def pdf_to_ocr_texts(pdf_path: Path, max_pages: int = 10, dpi: int = 300) -> List[str]:
    """
    Führt OCR auf PDF-Seiten mit EasyOCR aus.
    
    Args:
        pdf_path: Pfad zur PDF-Datei
        max_pages: Maximale Anzahl zu verarbeitender Seiten
        dpi: Auflösung für Konvertierung
    
    Returns:
        Liste von Texten (ein Text pro Seite)
    """
    if not pdf_path.exists():
        raise OCRError(f"PDF-Datei nicht gefunden: {pdf_path}")
    
    logger.info(f"Starte OCR mit EasyOCR: {pdf_path.name}")
    
    # PDF zu Bildern konvertieren
    images = pdf_to_images(pdf_path, dpi=dpi)
    
    # Auf max_pages begrenzen
    images = images[:max_pages]
    
    # OCR auf jeder Seite
    texts = []
    for i, image in enumerate(images, 1):
        logger.info(f"OCR auf Seite {i}/{len(images)}...")
        try:
            text = image_to_text_easyocr(image)
            texts.append(text)
            logger.debug(f"Seite {i}: {len(text)} Zeichen extrahiert")
        except Exception as e:
            logger.error(f"Fehler bei OCR auf Seite {i}: {e}")
            texts.append("")  # Leerer Text bei Fehler
    
    logger.info(f"✓ OCR abgeschlossen: {len(texts)} Seite(n) verarbeitet")
    return texts


def pdf_to_ocr_texts_enhanced(
    pdf_path: Path,
    max_pages: int = 10,
    dpi: int = 400,
    preprocess: bool = True
) -> List[str]:
    """
    Enhanced OCR mit Bildvorverarbeitung für bessere Qualität.
    
    Args:
        pdf_path: Pfad zur PDF-Datei
        max_pages: Maximale Anzahl zu verarbeitender Seiten
        dpi: Höhere Auflösung für bessere Qualität
        preprocess: Bildvorverarbeitung aktivieren
    
    Returns:
        Liste von Texten
    """
    if not pdf_path.exists():
        raise OCRError(f"PDF-Datei nicht gefunden: {pdf_path}")
    
    logger.info(f"Starte Enhanced OCR mit EasyOCR: {pdf_path.name}")
    
    # PDF zu Bildern konvertieren
    images = pdf_to_images(pdf_path, dpi=dpi)
    images = images[:max_pages]
    
    # OCR mit optionaler Vorverarbeitung
    texts = []
    for i, image in enumerate(images, 1):
        logger.info(f"Enhanced OCR auf Seite {i}/{len(images)}...")
        
        try:
            # Bildvorverarbeitung für bessere OCR-Qualität
            if preprocess:
                from PIL import ImageFilter, ImageEnhance
                
                # Kontrast erhöhen
                enhancer = ImageEnhance.Contrast(image)
                image = enhancer.enhance(1.5)
                
                # Schärfen
                image = image.filter(ImageFilter.SHARPEN)
                
                # Optional: In Graustufen konvertieren
                image = image.convert('L')
            
            text = image_to_text_easyocr(image)
            texts.append(text)
            logger.debug(f"Seite {i}: {len(text)} Zeichen extrahiert")
        
        except Exception as e:
            logger.error(f"Fehler bei Enhanced OCR auf Seite {i}: {e}")
            texts.append("")
    
    logger.info(f"✓ Enhanced OCR abgeschlossen: {len(texts)} Seite(n) verarbeitet")
    return texts


def check_easyocr_available() -> bool:
    """
    Prüft ob EasyOCR verfügbar ist.
    
    Returns:
        True wenn EasyOCR installiert ist, sonst False
    """
    try:
        import easyocr
        return True
    except ImportError:
        return False


def setup_ocr() -> None:
    """
    Initialisiert das OCR-System und lädt Modelle.
    Sollte beim Programmstart einmal aufgerufen werden.
    """
    if not check_easyocr_available():
        logger.warning("")
        logger.warning("=" * 60)
        logger.warning("  EASYOCR NICHT GEFUNDEN!")
        logger.warning("=" * 60)
        logger.warning("")
        logger.warning("  INSTALLATION:")
        logger.warning("  pip install easyocr")
        logger.warning("")
        logger.warning("  HINWEIS:")
        logger.warning("  - Lädt beim ersten Start ~100 MB Modelle herunter")
        logger.warning("  - Benötigt keine externe Installation (rein Python)")
        logger.warning("  - Funktioniert auch ohne GPU (langsamer aber OK)")
        logger.warning("")
        logger.warning("=" * 60)
        return
    
    try:
        # Reader initialisieren (lädt Modelle beim ersten Mal)
        _get_easyocr_reader()
        logger.info("✓ OCR-System bereit")
    except Exception as e:
        logger.error(f"Fehler beim Initialisieren des OCR-Systems: {e}")


# Alias-Funktionen für Kompatibilität mit bestehendem Code
def pdf_to_text(pdf_path: Path, max_pages: int = 10) -> str:
    """
    Extrahiert Text aus PDF (alle Seiten zusammen).
    
    Args:
        pdf_path: Pfad zur PDF-Datei
        max_pages: Maximale Anzahl Seiten
    
    Returns:
        Kompletter Text aller Seiten
    """
    texts = pdf_to_ocr_texts(pdf_path, max_pages)
    return '\n\n'.join(texts)
