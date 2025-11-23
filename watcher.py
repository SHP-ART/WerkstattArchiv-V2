"""
Ordnerüberwachung für automatische PDF-Verarbeitung.

Dieses Modul überwacht einen Eingangsordner und verarbeitet neue PDFs automatisch.
"""

import time
from pathlib import Path
from typing import Callable
import logging

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler, FileSystemEvent
except ImportError:
    logging.error("watchdog nicht installiert. Bitte installieren mit: pip install watchdog")
    raise

logger = logging.getLogger(__name__)


class PDFHandler(FileSystemEventHandler):
    """Event-Handler für neue PDF-Dateien."""
    
    def __init__(self, callback: Callable[[Path], None]):
        """
        Initialisiert den Handler.
        
        Args:
            callback: Funktion, die für jede neue PDF aufgerufen wird
        """
        self.callback = callback
        self.processing_files = set()
    
    def on_created(self, event: FileSystemEvent) -> None:
        """Wird aufgerufen, wenn eine neue Datei erstellt wird."""
        if event.is_directory:
            return
        
        file_path = Path(event.src_path)
        
        # Nur PDFs verarbeiten
        if file_path.suffix.lower() != '.pdf':
            return
        
        # Vermeiden, dass die gleiche Datei mehrfach verarbeitet wird
        if str(file_path) in self.processing_files:
            return
        
        self.processing_files.add(str(file_path))
        
        logger.info(f"Neue PDF erkannt: {file_path.name}")
        
        # Warten, bis die Datei vollständig geschrieben wurde
        if self._wait_for_file_complete(file_path):
            try:
                self.callback(file_path)
            except Exception as e:
                logger.error(f"Fehler bei der Verarbeitung von {file_path.name}: {e}")
            finally:
                self.processing_files.discard(str(file_path))
        else:
            logger.warning(f"Datei {file_path.name} konnte nicht vollständig gelesen werden")
            self.processing_files.discard(str(file_path))
    
    def _wait_for_file_complete(self, file_path: Path, timeout: int = 30) -> bool:
        """
        Wartet, bis eine Datei vollständig geschrieben wurde.
        
        Args:
            file_path: Pfad zur Datei
            timeout: Maximale Wartezeit in Sekunden
        
        Returns:
            True wenn Datei vollständig, False bei Timeout
        """
        start_time = time.time()
        last_size = -1
        
        while time.time() - start_time < timeout:
            try:
                if not file_path.exists():
                    return False
                
                current_size = file_path.stat().st_size
                
                # Wenn die Größe stabil bleibt, ist die Datei fertig
                if current_size == last_size and current_size > 0:
                    logger.debug(f"Datei vollständig: {file_path.name} ({current_size} Bytes)")
                    return True
                
                last_size = current_size
                time.sleep(0.5)
                
            except Exception as e:
                logger.warning(f"Fehler beim Prüfen der Datei {file_path.name}: {e}")
                time.sleep(0.5)
        
        logger.warning(f"Timeout beim Warten auf vollständige Datei: {file_path.name}")
        return False


def start_watcher(
    input_folder: Path,
    process_file_callback: Callable[[Path], None]
) -> None:
    """
    Startet die Ordnerüberwachung.
    
    Diese Funktion blockiert und läuft, bis sie mit Ctrl+C unterbrochen wird.
    
    Args:
        input_folder: Zu überwachender Ordner
        process_file_callback: Funktion, die für jede neue PDF aufgerufen wird
    
    Raises:
        FileNotFoundError: Wenn der Eingangsordner nicht existiert
    """
    if not input_folder.exists():
        raise FileNotFoundError(f"Eingangsordner nicht gefunden: {input_folder}")
    
    logger.info(f"Starte Ordnerüberwachung: {input_folder}")
    logger.info("Drücke Ctrl+C zum Beenden...")
    
    event_handler = PDFHandler(process_file_callback)
    observer = Observer()
    observer.schedule(event_handler, str(input_folder), recursive=False)
    observer.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Ordnerüberwachung wird beendet...")
        observer.stop()
    
    observer.join()
    logger.info("Ordnerüberwachung beendet")
