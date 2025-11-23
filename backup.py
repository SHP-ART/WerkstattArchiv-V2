"""
Backup-Funktionen für Datenbank und Archiv.

Dieses Modul erstellt ZIP-Backups von Datenbank, Konfiguration und optional
dem kompletten Archiv.
"""

import zipfile
import shutil
from pathlib import Path
from datetime import datetime
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class BackupError(Exception):
    """Fehler bei der Backup-Erstellung."""
    pass


def create_backup(
    archiv_root: Path,
    db_path: Path,
    config_path: Path,
    backup_target_dir: Path,
    include_archive: bool = False
) -> Path:
    """
    Erstellt ein ZIP-Backup.
    
    Args:
        archiv_root: Root-Verzeichnis des Archivs
        db_path: Pfad zur Datenbank
        config_path: Pfad zur Konfigurationsdatei
        backup_target_dir: Zielverzeichnis für Backups
        include_archive: Ob das komplette Archiv gesichert werden soll
    
    Returns:
        Pfad zum erstellten Backup
    
    Raises:
        BackupError: Bei Fehlern bei der Backup-Erstellung
    """
    try:
        # Backup-Verzeichnis erstellen
        backup_target_dir.mkdir(parents=True, exist_ok=True)
        
        # Backup-Dateiname mit Timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        backup_filename = f"werkstatt_backup_{timestamp}.zip"
        backup_path = backup_target_dir / backup_filename
        
        logger.info(f"Erstelle Backup: {backup_path}")
        
        with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Datenbank hinzufügen
            if db_path.exists():
                zipf.write(db_path, arcname=f"backup/{db_path.name}")
                logger.info(f"  + Datenbank: {db_path.name}")
            else:
                logger.warning("Datenbank nicht gefunden, überspringe")
            
            # Konfiguration hinzufügen
            if config_path.exists():
                zipf.write(config_path, arcname=f"backup/{config_path.name}")
                logger.info(f"  + Konfiguration: {config_path.name}")
            else:
                logger.warning("Konfiguration nicht gefunden, überspringe")
            
            # Kunden-Index hinzufügen (falls vorhanden)
            kunden_index = archiv_root / "kunden_index.csv"
            if kunden_index.exists():
                zipf.write(kunden_index, arcname="backup/kunden_index.csv")
                logger.info("  + Kunden-Index")
            
            # Optional: Komplettes Archiv hinzufügen
            if include_archive:
                logger.info("  + Archiv (kann lange dauern)...")
                
                if not archiv_root.exists():
                    logger.warning(f"Archivordner nicht gefunden: {archiv_root}")
                else:
                    # Alle Dateien im Archiv durchgehen
                    file_count = 0
                    for file_path in archiv_root.rglob('*'):
                        if file_path.is_file():
                            # Relativen Pfad berechnen
                            rel_path = file_path.relative_to(archiv_root.parent)
                            zipf.write(file_path, arcname=f"backup/{rel_path}")
                            file_count += 1
                            
                            if file_count % 100 == 0:
                                logger.info(f"    {file_count} Dateien gesichert...")
                    
                    logger.info(f"  + {file_count} Archiv-Dateien gesichert")
        
        # Backup-Größe loggen
        backup_size_mb = backup_path.stat().st_size / (1024 * 1024)
        logger.info(f"Backup erfolgreich erstellt: {backup_path} ({backup_size_mb:.2f} MB)")
        
        return backup_path
        
    except Exception as e:
        raise BackupError(f"Fehler beim Erstellen des Backups: {e}")


def get_last_backup_time(backup_target_dir: Path) -> Optional[datetime]:
    """
    Ermittelt die Zeit des letzten Backups.
    
    Args:
        backup_target_dir: Verzeichnis mit Backups
    
    Returns:
        Datetime des letzten Backups oder None
    """
    if not backup_target_dir.exists():
        return None
    
    try:
        # Alle Backup-Dateien finden
        backups = list(backup_target_dir.glob("werkstatt_backup_*.zip"))
        
        if not backups:
            return None
        
        # Neuestes Backup finden
        latest_backup = max(backups, key=lambda p: p.stat().st_mtime)
        last_time = datetime.fromtimestamp(latest_backup.stat().st_mtime)
        
        logger.debug(f"Letztes Backup: {latest_backup.name} ({last_time})")
        return last_time
        
    except Exception as e:
        logger.error(f"Fehler beim Ermitteln des letzten Backups: {e}")
        return None


def should_create_backup(
    backup_target_dir: Path,
    interval_hours: int
) -> bool:
    """
    Prüft, ob ein neues Backup erstellt werden sollte.
    
    Args:
        backup_target_dir: Verzeichnis mit Backups
        interval_hours: Backup-Intervall in Stunden
    
    Returns:
        True wenn ein Backup erstellt werden sollte
    """
    last_backup = get_last_backup_time(backup_target_dir)
    
    if last_backup is None:
        logger.info("Kein vorheriges Backup gefunden, sollte erstellt werden")
        return True
    
    hours_since_backup = (datetime.now() - last_backup).total_seconds() / 3600
    
    if hours_since_backup >= interval_hours:
        logger.info(f"Letztes Backup ist {hours_since_backup:.1f} Stunden alt "
                   f"(Intervall: {interval_hours}h), sollte erstellt werden")
        return True
    else:
        logger.info(f"Letztes Backup ist {hours_since_backup:.1f} Stunden alt "
                   f"(Intervall: {interval_hours}h), noch aktuell")
        return False


def cleanup_old_backups(
    backup_target_dir: Path,
    keep_count: int = 10
) -> None:
    """
    Löscht alte Backups, behält nur die neuesten.
    
    Args:
        backup_target_dir: Verzeichnis mit Backups
        keep_count: Anzahl der zu behaltenden Backups
    """
    if not backup_target_dir.exists():
        return
    
    try:
        # Alle Backup-Dateien finden
        backups = sorted(
            backup_target_dir.glob("werkstatt_backup_*.zip"),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )
        
        if len(backups) <= keep_count:
            logger.info(f"Nur {len(backups)} Backups vorhanden, keine Bereinigung nötig")
            return
        
        # Alte Backups löschen
        for old_backup in backups[keep_count:]:
            logger.info(f"Lösche altes Backup: {old_backup.name}")
            old_backup.unlink()
        
        logger.info(f"Bereinigung abgeschlossen: {len(backups) - keep_count} alte Backups gelöscht")
        
    except Exception as e:
        logger.error(f"Fehler bei der Backup-Bereinigung: {e}")
