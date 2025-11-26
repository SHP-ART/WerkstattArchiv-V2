"""
OCR-Verarbeitung für PDF-Dokumente.

Dieses Modul konvertiert PDF-Seiten in Bilder und führt OCR (Texterkennung)
mit Tesseract durch. Es ist optimiert für deutsche Werkstattaufträge.
"""

from pathlib import Path
from typing import List, Optional
import logging

try:
    from pdf2image import convert_from_path
    from PIL import Image
    import pytesseract
except ImportError as e:
    logging.error(f"Erforderliche OCR-Bibliotheken nicht installiert: {e}")
    logging.error("Bitte installieren mit: pip install pytesseract pdf2image Pillow")
    raise

logger = logging.getLogger(__name__)


class OCRError(Exception):
    """Fehler bei der OCR-Verarbeitung."""
    pass


def _find_tesseract_windows() -> Optional[str]:
    """
    Sucht Tesseract auf Windows in Standard-Installationspfaden.
    
    Returns:
        Pfad zu tesseract.exe oder None wenn nicht gefunden
    """
    import platform
    if platform.system() != 'Windows':
        return None
    
    # Standard-Installationspfade für Windows
    standard_paths = [
        Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe"),
        Path(r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe"),
        Path.home() / "AppData" / "Local" / "Programs" / "Tesseract-OCR" / "tesseract.exe",
        Path(r"D:\Program Files\Tesseract-OCR\tesseract.exe"),
    ]
    
    for path in standard_paths:
        if path.exists():
            logger.info(f"Tesseract gefunden: {path}")
            return str(path)
    
    return None


def setup_tesseract(tesseract_cmd: Optional[str] = None) -> None:
    """
    Konfiguriert den Pfad zur Tesseract-Binary.
    
    Args:
        tesseract_cmd: Pfad zur tesseract.exe (Windows) oder None für Auto-Detection
    """
    import platform
    
    if tesseract_cmd:
        pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
        logger.info(f"Tesseract-Pfad gesetzt: {tesseract_cmd}")
    elif platform.system() == 'Windows':
        # Auf Windows: Automatisch in Standard-Pfaden suchen
        found_path = _find_tesseract_windows()
        if found_path:
            pytesseract.pytesseract.tesseract_cmd = found_path
            logger.info(f"Tesseract automatisch gefunden: {found_path}")
        else:
            logger.warning("Tesseract nicht in Standard-Pfaden gefunden.")
            logger.warning("Bitte 'install_tesseract.bat' ausführen oder Pfad in Config setzen.")


def test_tesseract() -> bool:
    """
    Prüft, ob Tesseract verfügbar ist.
    
    Returns:
        True wenn Tesseract funktioniert, sonst False
    """
    import platform
    
    try:
        version = pytesseract.get_tesseract_version()
        logger.info(f"Tesseract Version: {version}")
        return True
    except Exception as e:
        logger.error(f"Tesseract nicht gefunden oder fehlerhaft: {e}")
        logger.error("")
        logger.error("=" * 60)
        logger.error("  TESSERACT OCR NICHT GEFUNDEN!")
        logger.error("=" * 60)
        
        if platform.system() == 'Windows':
            logger.error("")
            logger.error("  LÖSUNG FÜR WINDOWS:")
            logger.error("  1. Führe 'install_tesseract.bat' aus")
            logger.error("     ODER")
            logger.error("  2. Lade Tesseract manuell herunter:")
            logger.error("     https://github.com/UB-Mannheim/tesseract/wiki")
            logger.error("")
            logger.error("  Nach der Installation:")
            logger.error("  - Füge in .archiv_config.json hinzu:")
            logger.error('    "tesseract_cmd": "C:\\\\Program Files\\\\Tesseract-OCR\\\\tesseract.exe"')
            logger.error("")
            logger.error("  WICHTIG: Bei der Installation 'German' als Sprache auswählen!")
        elif platform.system() == 'Darwin':
            logger.error("")
            logger.error("  LÖSUNG FÜR macOS:")
            logger.error("  brew install tesseract tesseract-lang")
        else:
            logger.error("")
            logger.error("  LÖSUNG FÜR LINUX:")
            logger.error("  sudo apt-get install tesseract-ocr tesseract-ocr-deu")
        
        logger.error("=" * 60)
        return False


def pdf_to_images(pdf_path: Path, max_pages: Optional[int] = 10, dpi: int = 300) -> List[Image.Image]:
    """
    Konvertiert eine PDF-Datei in eine Liste von Bildern.
    
    Args:
        pdf_path: Pfad zur PDF-Datei
        max_pages: Maximale Anzahl der zu konvertierenden Seiten (None = alle Seiten)
        dpi: Auflösung für die Konvertierung (höher = bessere Qualität, aber langsamer)
    
    Returns:
        Liste von PIL Image-Objekten
    
    Raises:
        OCRError: Bei Fehlern bei der PDF-Konvertierung
    """
    if not pdf_path.exists():
        raise OCRError(f"PDF-Datei nicht gefunden: {pdf_path}")
    
    try:
        if max_pages is None:
            logger.info(f"Konvertiere PDF zu Bildern: {pdf_path.name} (alle Seiten, {dpi} DPI)")
        else:
            logger.info(f"Konvertiere PDF zu Bildern: {pdf_path.name} (max. {max_pages} Seiten, {dpi} DPI)")
        
        # PDF zu Bildern konvertieren
        # last_page=None bedeutet: alle Seiten
        images = convert_from_path(
            pdf_path,
            dpi=dpi,
            first_page=1,
            last_page=max_pages,
            fmt='jpeg'
        )
        
        logger.info(f"PDF konvertiert: {len(images)} Seiten")
        return images
        
    except Exception as e:
        raise OCRError(f"Fehler bei PDF-Konvertierung von {pdf_path.name}: {e}")


def image_to_text(image: Image.Image, lang: str = "deu", config: str = "") -> str:
    """
    Führt OCR auf einem Bild durch.
    
    Args:
        image: PIL Image-Objekt
        lang: Tesseract-Sprachcode (deu = Deutsch)
        config: Zusätzliche Tesseract-Konfiguration
    
    Returns:
        Erkannter Text
    
    Raises:
        OCRError: Bei Fehlern bei der OCR-Verarbeitung
    """
    try:
        # Tesseract-Konfiguration für bessere Ergebnisse
        if not config:
            # PSM 1 = Automatic page segmentation with OSD (Orientation and Script Detection)
            # PSM 3 = Fully automatic page segmentation, but no OSD (Default)
            config = '--psm 3'
        
        text = pytesseract.image_to_string(image, lang=lang, config=config)
        return text
        
    except Exception as e:
        raise OCRError(f"Fehler bei OCR-Verarbeitung: {e}")


def pdf_to_ocr_texts(
    pdf_path: Path,
    max_pages: Optional[int] = 10,
    lang: str = "deu",
    dpi: int = 300
) -> List[str]:
    """
    Führt OCR auf einer PDF-Datei durch und gibt eine Liste von Texten zurück.
    
    Der Index entspricht der Seitennummer (0-basiert):
    - texts[0] = Text von Seite 1 (Metadaten)
    - texts[1] = Text von Seite 2 (Anhang)
    - texts[2] = Text von Seite 3 (Anhang)
    - usw.
    
    Args:
        pdf_path: Pfad zur PDF-Datei
        max_pages: Maximale Anzahl der zu verarbeitenden Seiten (None = alle Seiten)
        lang: Tesseract-Sprachcode
        dpi: Auflösung für die PDF-Konvertierung
    
    Returns:
        Liste von Texten (einer pro Seite)
    
    Raises:
        OCRError: Bei Fehlern bei der Verarbeitung
    """
    logger.info(f"Starte OCR-Verarbeitung: {pdf_path.name}")
    
    # PDF zu Bildern konvertieren
    images = pdf_to_images(pdf_path, max_pages=max_pages, dpi=dpi)
    
    if not images:
        raise OCRError(f"Keine Seiten in PDF gefunden: {pdf_path.name}")
    
    # OCR auf jeder Seite durchführen
    texts = []
    for i, image in enumerate(images, start=1):
        logger.info(f"OCR auf Seite {i}/{len(images)}: {pdf_path.name}")
        
        try:
            text = image_to_text(image, lang=lang)
            texts.append(text)
            
            # Debug: Ersten Teil des Textes loggen
            preview = text[:200].replace('\n', ' ').strip()
            if preview:
                logger.debug(f"Seite {i} Text-Vorschau: {preview}...")
            else:
                logger.warning(f"Seite {i}: Kein Text erkannt")
                
        except OCRError as e:
            logger.error(f"Fehler bei OCR auf Seite {i}: {e}")
            texts.append("")  # Leerer Text bei Fehler
    
    logger.info(f"OCR abgeschlossen: {len(texts)} Seiten verarbeitet")
    return texts


def extract_text_from_first_page(pdf_path: Path, lang: str = "deu", dpi: int = 300) -> str:
    """
    Extrahiert nur den Text von der ersten Seite (für Metadaten-Extraktion).
    
    Args:
        pdf_path: Pfad zur PDF-Datei
        lang: Tesseract-Sprachcode
        dpi: Auflösung für die PDF-Konvertierung
    
    Returns:
        Text von Seite 1
    
    Raises:
        OCRError: Bei Fehlern bei der Verarbeitung
    """
    texts = pdf_to_ocr_texts(pdf_path, max_pages=1, lang=lang, dpi=dpi)
    return texts[0] if texts else ""


def preprocess_image_for_ocr(image: Image.Image, enhance: bool = True) -> Image.Image:
    """
    Optional: Bildvorverarbeitung für bessere OCR-Ergebnisse.
    
    Diese Funktion kann verwendet werden, um die Bildqualität für OCR zu verbessern:
    - Konvertierung zu Graustufen
    - Kontrasterhöhung
    - Schärfung
    
    Args:
        image: PIL Image-Objekt
        enhance: Ob Kontrastverbesserung angewendet werden soll
    
    Returns:
        Vorverarbeitetes Image-Objekt
    """
    try:
        from PIL import ImageEnhance, ImageFilter
        
        # Zu Graustufen konvertieren
        if image.mode != 'L':
            image = image.convert('L')
        
        if enhance:
            # Kontrast erhöhen
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(2.0)
            
            # Schärfen
            image = image.filter(ImageFilter.SHARPEN)
        
        return image
        
    except Exception as e:
        logger.warning(f"Bildvorverarbeitung fehlgeschlagen: {e}")
        return image


# Beispiel-Funktion für optimierte OCR bei schlechter Scan-Qualität
def pdf_to_ocr_texts_enhanced(
    pdf_path: Path,
    max_pages: Optional[int] = 10,
    lang: str = "deu",
    dpi: int = 400  # Höhere Auflösung für schlechte Scans
) -> List[str]:
    """
    Wie pdf_to_ocr_texts, aber mit Bildvorverarbeitung für bessere Ergebnisse.
    
    Verwende diese Funktion, wenn die Standard-OCR schlechte Ergebnisse liefert.
    max_pages=None scannt alle Seiten.
    """
    logger.info(f"Starte erweiterte OCR-Verarbeitung: {pdf_path.name}")
    
    images = pdf_to_images(pdf_path, max_pages=max_pages, dpi=dpi)
    
    if not images:
        raise OCRError(f"Keine Seiten in PDF gefunden: {pdf_path.name}")
    
    texts = []
    for i, image in enumerate(images, start=1):
        logger.info(f"OCR auf Seite {i}/{len(images)} (enhanced): {pdf_path.name}")
        
        try:
            # Bildvorverarbeitung
            processed_image = preprocess_image_for_ocr(image, enhance=True)
            
            # PSM 6 als Hauptmethode für Enhanced-OCR
            # PSM 6 = Uniform block of text (optimal für Formulare mit Kästchen/Feldern)
            # Besser als PSM 3 für neue Formulare, wo Auftragsnummer in Kästchen steht
            text = image_to_text(processed_image, lang=lang, config='--psm 6 --oem 3')
            
            texts.append(text)
            
        except Exception as e:
            logger.error(f"Fehler bei erweiterter OCR auf Seite {i}: {e}")
            texts.append("")
    
    logger.info(f"Erweiterte OCR abgeschlossen: {len(texts)} Seiten verarbeitet")
    return texts
