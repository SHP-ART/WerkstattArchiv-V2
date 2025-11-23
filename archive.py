"""
Archivverwaltung für Werkstatt-PDFs.

Dieses Modul verwaltet die Ordnerstruktur nach Auftragsnummer,
generiert Dateinamen mit Versionierung und verschiebt Dateien ins Archiv.
"""

import shutil
import hashlib
from pathlib import Path
from typing import List, Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class ArchiveError(Exception):
    """Fehler bei der Archivierung."""
    pass


def format_auftrag_nr(raw_nr: str, pad_length: int = 6) -> str:
    """
    Formatiert die Auftragsnummer mit führenden Nullen.
    
    Args:
        raw_nr: Rohe Auftragsnummer (z.B. "303", "76329")
        pad_length: Länge der gepaddeten Nummer (Standard: 6)
    
    Returns:
        Gepaddete Auftragsnummer (z.B. "000303", "076329")
    
    Example:
        >>> format_auftrag_nr("303", 6)
        '000303'
        >>> format_auftrag_nr("76329", 6)
        '076329'
    """
    # Nur Ziffern behalten
    digits = ''.join(c for c in raw_nr if c.isdigit())
    
    if not digits:
        raise ArchiveError(f"Keine gültigen Ziffern in Auftragsnummer: {raw_nr}")
    
    # Mit führenden Nullen auffüllen
    padded = digits.zfill(pad_length)
    
    logger.debug(f"Auftragsnummer formatiert: {raw_nr} -> {padded}")
    return padded


def get_thousand_block(auftrag_nr_padded: str) -> str:
    """
    Berechnet den Tausender-Block für eine Auftragsnummer.
    
    Args:
        auftrag_nr_padded: Gepaddete Auftragsnummer (z.B. "076329")
    
    Returns:
        Tausender-Block-Name (z.B. "070000-079999")
    
    Example:
        >>> get_thousand_block("076329")
        '070000-079999'
        >>> get_thousand_block("000303")
        '000000-009999'
    """
    nr = int(auftrag_nr_padded)
    
    # Auf Tausender abrunden
    block_start = (nr // 10000) * 10000
    block_end = block_start + 9999
    
    # Länge der gepaddeten Nummer beibehalten
    pad_length = len(auftrag_nr_padded)
    
    block_name = f"{str(block_start).zfill(pad_length)}-{str(block_end).zfill(pad_length)}"
    
    logger.debug(f"Tausender-Block für {auftrag_nr_padded}: {block_name}")
    return block_name


def get_year_from_datum(datum: Optional[str]) -> str:
    """
    Extrahiert das Jahr aus einem Datum im ISO-Format.
    
    Args:
        datum: Datum im Format YYYY-MM-DD (z.B. "2024-07-29") oder None
    
    Returns:
        Jahr als String (z.B. "2024") oder "Unbekannt" bei fehlendem Datum
    
    Example:
        >>> get_year_from_datum("2024-07-29")
        '2024'
        >>> get_year_from_datum(None)
        'Unbekannt'
    """
    if not datum:
        logger.debug("Kein Datum vorhanden, verwende 'Unbekannt' als Jahr")
        return "Unbekannt"
    
    try:
        # Format: YYYY-MM-DD → nimm ersten 4 Zeichen
        year = datum[:4]
        if year.isdigit() and len(year) == 4:
            logger.debug(f"Jahr aus Datum extrahiert: {year}")
            return year
    except (IndexError, AttributeError):
        pass
    
    logger.warning(f"Konnte Jahr nicht aus Datum '{datum}' extrahieren, verwende 'Unbekannt'")
    return "Unbekannt"


def get_archive_dir_for_auftrag(
    archiv_root: Path,
    auftrag_nr: str,
    config: Dict[str, Any],
    datum: Optional[str] = None
) -> Path:
    """
    Bestimmt den Zielordner für eine Auftragsnummer.
    
    Die Struktur hängt von der Konfiguration ab:
    - Mit Jahr-Ordnern: archiv_root/2024/076329/
    - Mit Tausender-Blöcken: archiv_root/070000-079999/076329/
    - Ohne Gruppierung: archiv_root/076329/
    
    Args:
        archiv_root: Root-Verzeichnis des Archivs
        auftrag_nr: Rohe oder gepaddete Auftragsnummer
        config: Konfigurationsdictionary
        datum: Datum im Format YYYY-MM-DD (optional)
    
    Returns:
        Pfad zum Auftragsordner
    
    Raises:
        ArchiveError: Bei ungültiger Auftragsnummer
    """
    # Auftragsnummer formatieren
    pad_length = config.get("auftragsnummer_pad_length", 6)
    auftrag_nr_padded = format_auftrag_nr(auftrag_nr, pad_length)
    
    # Jahr-basierte Ordner verwenden? (NEU, höhere Priorität)
    use_year_folders = config.get("use_year_folders", True)
    use_thousand_blocks = config.get("use_thousand_blocks", False)  # Fallback auf False
    
    if use_year_folders:
        # Mit Jahr-Ordner (z.B. 2024/076329/)
        year = get_year_from_datum(datum)
        archive_dir = archiv_root / year / auftrag_nr_padded
        logger.debug(f"Verwende Jahr-basierte Struktur: {year}/{auftrag_nr_padded}")
    elif use_thousand_blocks:
        # Mit Tausender-Block (alte Logik)
        block_name = get_thousand_block(auftrag_nr_padded)
        archive_dir = archiv_root / block_name / auftrag_nr_padded
        logger.debug(f"Verwende Tausender-Block: {block_name}/{auftrag_nr_padded}")
    else:
        # Direkt im Root
        archive_dir = archiv_root / auftrag_nr_padded
        logger.debug(f"Verwende flache Struktur: {auftrag_nr_padded}")
    
    # Ordner erstellen, falls nicht vorhanden
    archive_dir.mkdir(parents=True, exist_ok=True)
    logger.debug(f"Archivordner: {archive_dir}")
    
    return archive_dir


def get_existing_versions(archive_dir: Path, auftrag_nr_padded: str) -> List[Path]:
    """
    Findet alle existierenden Versionen einer Auftragsnummer.
    
    Args:
        archive_dir: Ordner mit den Auftragsdateien
        auftrag_nr_padded: Gepaddete Auftragsnummer
    
    Returns:
        Liste von Pfaden zu existierenden Dateien
    """
    if not archive_dir.exists():
        return []
    
    # Alle PDFs mit dieser Auftragsnummer finden
    pattern = f"{auftrag_nr_padded}_*.pdf"
    existing = list(archive_dir.glob(pattern))
    
    logger.debug(f"Gefundene Versionen: {len(existing)}")
    return existing


def extract_version_number(filename: str) -> int:
    """
    Extrahiert die Versionsnummer aus einem Dateinamen.
    
    Args:
        filename: Dateiname (z.B. "076329_Auftrag_v2.pdf")
    
    Returns:
        Versionsnummer (1 wenn keine Version im Namen, sonst die erkannte Zahl)
    
    Example:
        >>> extract_version_number("076329_Auftrag.pdf")
        1
        >>> extract_version_number("076329_Auftrag_v2.pdf")
        2
    """
    import re
    match = re.search(r'_v(\d+)\.pdf$', filename)
    if match:
        return int(match.group(1))
    return 1


def generate_target_filename(
    auftrag_nr_padded: str,
    config: Dict[str, Any],
    existing_files: List[Path],
    metadata: Optional[Dict[str, Any]] = None
) -> str:
    """
    Generiert den Zieldateinamen mit automatischer Versionierung und optionalen Metadaten.
    
    Args:
        auftrag_nr_padded: Gepaddete Auftragsnummer
        config: Konfigurationsdictionary mit dateiname_pattern
        existing_files: Liste existierender Dateien im Zielordner
        metadata: Optionale Metadaten (name, datum, kennzeichen, etc.)
    
    Returns:
        Dateiname (z.B. "076329_Auftrag.pdf", "076329_Voigt_2024-07-29.pdf")
    
    Example:
        >>> generate_target_filename("076329", {"dateiname_pattern": "{auftrag_nr}_{name}_{datum}.pdf"}, [], {"name": "Voigt", "datum": "2024-07-29"})
        '076329_Voigt_2024-07-29.pdf'
    """
    # Höchste existierende Version finden
    max_version = 0
    for file_path in existing_files:
        version = extract_version_number(file_path.name)
        max_version = max(max_version, version)
    
    # Neue Version
    new_version = max_version + 1
    
    # Version-Suffix generieren
    if new_version == 1:
        version_suffix = ""
    else:
        version_suffix = f"_v{new_version}"
    
    # Dateinamen-Pattern aus Config
    pattern = config.get("dateiname_pattern", "{auftrag_nr}_Auftrag{version_suffix}.pdf")
    
    # Metadaten vorbereiten
    format_data = {
        "auftrag_nr": auftrag_nr_padded,
        "version_suffix": version_suffix,
        "name": "Unbekannt",
        "datum": "ohne_datum",
        "kennzeichen": "ohne_kz",
        "vin": "ohne_vin"
    }
    
    # Metadaten übernehmen (falls vorhanden)
    if metadata:
        # Name bereinigen (keine Leerzeichen, Sonderzeichen)
        if metadata.get("name"):
            name = metadata["name"]
            # Entferne Titel, Firmenzusätze
            name = name.replace("Herr ", "").replace("Frau ", "").replace("GmbH", "").replace("Firma ", "")
            # Nur erster Nachname (falls mehrere)
            name = name.split()[0] if name.split() else "Unbekannt"
            # Sonderzeichen entfernen
            name = "".join(c for c in name if c.isalnum() or c in "._-")
            format_data["name"] = name[:30]  # Max 30 Zeichen
        
        # Datum formatieren
        if metadata.get("datum"):
            format_data["datum"] = metadata["datum"]
        
        # Kennzeichen bereinigen
        if metadata.get("kennzeichen"):
            kz = metadata["kennzeichen"].replace(" ", "-").replace(":", "")
            format_data["kennzeichen"] = kz[:15]  # Max 15 Zeichen
        
        # VIN (letzte 6 Zeichen)
        if metadata.get("vin"):
            vin = metadata["vin"]
            format_data["vin"] = vin[-6:] if len(vin) >= 6 else vin
    
    # Pattern füllen
    try:
        filename = pattern.format(**format_data)
    except KeyError as e:
        logger.warning(f"Ungültiger Platzhalter im Pattern: {e}. Verwende Standard-Pattern.")
        filename = f"{auftrag_nr_padded}_Auftrag{version_suffix}.pdf"
    
    logger.debug(f"Generierter Dateiname: {filename} (Version {new_version})")
    return filename


def calculate_file_hash(file_path: Path) -> str:
    """
    Berechnet den SHA256-Hash einer Datei.
    
    Args:
        file_path: Pfad zur Datei
    
    Returns:
        Hexadezimaler SHA256-Hash
    """
    sha256 = hashlib.sha256()
    
    with open(file_path, 'rb') as f:
        # Datei in Blöcken lesen für große Dateien
        for block in iter(lambda: f.read(65536), b''):
            sha256.update(block)
    
    file_hash = sha256.hexdigest()
    logger.debug(f"SHA256-Hash: {file_hash[:16]}...")
    return file_hash


def move_to_archive(
    source_path: Path,
    archiv_root: Path,
    auftrag_nr: str,
    config: Dict[str, Any],
    metadata: Optional[Dict[str, Any]] = None
) -> tuple[Path, str]:
    """
    Verschiebt eine Datei ins Archiv.
    
    Args:
        source_path: Pfad zur Quelldatei
        archiv_root: Root-Verzeichnis des Archivs
        auftrag_nr: Auftragsnummer
        config: Konfigurationsdictionary
        metadata: Optionale Metadaten für Dateinamen (name, datum, etc.)
    
    Returns:
        Tuple aus (Zielpfad, SHA256-Hash)
    
    Raises:
        ArchiveError: Bei Fehlern beim Verschieben
    """
    if not source_path.exists():
        raise ArchiveError(f"Quelldatei existiert nicht: {source_path}")
    
    # Hash vor dem Verschieben berechnen
    file_hash = calculate_file_hash(source_path)
    
    # Auftragsnummer formatieren
    pad_length = config.get("auftragsnummer_pad_length", 6)
    auftrag_nr_padded = format_auftrag_nr(auftrag_nr, pad_length)
    
    # Datum aus Metadaten extrahieren (für Jahr-Ordner)
    datum = metadata.get("datum") if metadata else None
    
    # Zielordner bestimmen (mit Datum für Jahr-basierte Struktur)
    archive_dir = get_archive_dir_for_auftrag(archiv_root, auftrag_nr, config, datum)
    
    # Existierende Versionen finden
    existing_files = get_existing_versions(archive_dir, auftrag_nr_padded)
    
    # Dateinamen generieren (mit optionalen Metadaten)
    target_filename = generate_target_filename(auftrag_nr_padded, config, existing_files, metadata)
    target_path = archive_dir / target_filename
    
    # Datei verschieben
    try:
        logger.info(f"Verschiebe {source_path.name} -> {target_path}")
        shutil.move(str(source_path), str(target_path))
        logger.info(f"Datei erfolgreich archiviert: {target_path}")
        
        return target_path, file_hash
        
    except Exception as e:
        raise ArchiveError(f"Fehler beim Verschieben der Datei: {e}")


def move_to_error_folder(source_path: Path, input_folder: Path) -> Path:
    """
    Verschiebt eine fehlerhafte Datei in den Fehlerordner.
    
    Args:
        source_path: Pfad zur Quelldatei
        input_folder: Eingangsordner (Fehlerordner wird hier erstellt)
    
    Returns:
        Pfad zur verschobenen Datei im Fehlerordner
    
    Raises:
        ArchiveError: Bei Fehlern beim Verschieben
    """
    error_folder = input_folder / "Fehler"
    error_folder.mkdir(exist_ok=True)
    
    target_path = error_folder / source_path.name
    
    # Bei Namenskonflikten: Timestamp anhängen
    if target_path.exists():
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        name_without_ext = source_path.stem
        target_path = error_folder / f"{name_without_ext}_{timestamp}.pdf"
    
    try:
        logger.warning(f"Verschiebe fehlerhafte Datei: {source_path.name} -> Fehlerordner")
        shutil.move(str(source_path), str(target_path))
        logger.info(f"Datei verschoben nach: {target_path}")
        
        return target_path
        
    except Exception as e:
        raise ArchiveError(f"Fehler beim Verschieben in Fehlerordner: {e}")


def create_archive_structure(archiv_root: Path) -> None:
    """
    Erstellt die Basis-Ordnerstruktur des Archivs.
    
    Args:
        archiv_root: Root-Verzeichnis des Archivs
    """
    archiv_root.mkdir(parents=True, exist_ok=True)
    logger.info(f"Archiv-Struktur erstellt: {archiv_root}")


def get_archive_statistics(archiv_root: Path) -> Dict[str, Any]:
    """
    Sammelt Statistiken über das Archiv.
    
    Args:
        archiv_root: Root-Verzeichnis des Archivs
    
    Returns:
        Dictionary mit Statistiken (Anzahl Aufträge, Dateien, Gesamtgröße)
    """
    if not archiv_root.exists():
        return {
            "total_auftraege": 0,
            "total_files": 0,
            "total_size_mb": 0.0
        }
    
    # Alle Auftragsordner finden (6-stellige Zahlen)
    auftragsordner = []
    total_files = 0
    total_size = 0
    
    for item in archiv_root.rglob("*"):
        if item.is_dir() and len(item.name) == 6 and item.name.isdigit():
            auftragsordner.append(item)
            
            # PDFs in diesem Ordner zählen
            pdfs = list(item.glob("*.pdf"))
            total_files += len(pdfs)
            
            # Größe berechnen
            for pdf in pdfs:
                try:
                    total_size += pdf.stat().st_size
                except:
                    pass
    
    total_size_mb = total_size / (1024 * 1024)  # Bytes zu MB
    
    stats = {
        "total_auftraege": len(auftragsordner),
        "total_files": total_files,
        "total_size_mb": round(total_size_mb, 2)
    }
    
    logger.info(f"Archiv-Statistik: {stats}")
    return stats
