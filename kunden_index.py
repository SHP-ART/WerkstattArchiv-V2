"""
Kunden-Index als CSV-Datei.

Dieses Modul verwaltet eine separate CSV-Datei mit allen Auftragsinformationen
für einfachen Zugriff ohne Datenbank.
"""

import csv
from pathlib import Path
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class KundenIndexError(Exception):
    """Fehler bei der Verwaltung des Kunden-Index."""
    pass


def create_kunden_index(index_path: Path) -> None:
    """
    Erstellt eine neue Kunden-Index-Datei mit Headern.
    
    Args:
        index_path: Pfad zur Index-Datei
    """
    headers = [
        "file_path",
        "auftrag_nr",
        "kunden_nr",
        "kunde_name",
        "kennzeichen",
        "vin",
        "datum",
        "formular_version"
    ]
    
    try:
        with open(index_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
        
        logger.info(f"Kunden-Index erstellt: {index_path}")
        
    except Exception as e:
        raise KundenIndexError(f"Fehler beim Erstellen des Kunden-Index: {e}")


def update_kunden_index(
    index_path: Path,
    entry: Dict[str, Any]
) -> None:
    """
    Fügt einen Eintrag zum Kunden-Index hinzu.
    
    Args:
        index_path: Pfad zur Index-Datei
        entry: Dictionary mit Auftragsdaten (file_path, auftrag_nr, etc.)
    
    Raises:
        KundenIndexError: Bei Fehlern beim Aktualisieren
    """
    # Sicherstellen, dass die Datei existiert
    if not index_path.exists():
        create_kunden_index(index_path)
    
    try:
        # Eintrag an die Datei anhängen
        with open(index_path, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=[
                "file_path",
                "auftrag_nr",
                "kunden_nr",
                "kunde_name",
                "kennzeichen",
                "vin",
                "datum",
                "formular_version"
            ])
            
            writer.writerow({
                "file_path": entry.get("file_path", ""),
                "auftrag_nr": entry.get("auftrag_nr", ""),
                "kunden_nr": entry.get("kunden_nr", ""),
                "kunde_name": entry.get("kunde_name", ""),
                "kennzeichen": entry.get("kennzeichen", ""),
                "vin": entry.get("vin", ""),
                "datum": entry.get("datum", ""),
                "formular_version": entry.get("formular_version", "")
            })
        
        logger.debug(f"Kunden-Index aktualisiert: Auftrag {entry.get('auftrag_nr')}")
        
    except Exception as e:
        raise KundenIndexError(f"Fehler beim Aktualisieren des Kunden-Index: {e}")


def read_kunden_index(index_path: Path) -> List[Dict[str, Any]]:
    """
    Liest den kompletten Kunden-Index.
    
    Args:
        index_path: Pfad zur Index-Datei
    
    Returns:
        Liste von Dictionaries mit allen Einträgen
    """
    if not index_path.exists():
        logger.warning(f"Kunden-Index nicht gefunden: {index_path}")
        return []
    
    try:
        with open(index_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            entries = list(reader)
        
        logger.info(f"Kunden-Index gelesen: {len(entries)} Einträge")
        return entries
        
    except Exception as e:
        logger.error(f"Fehler beim Lesen des Kunden-Index: {e}")
        return []
