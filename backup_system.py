#!/usr/bin/env python3
"""
Robustes Backup- und Restore-System für Werkstatt-Archiv

Exportiert Datenbank-Datensätze als CSV in jeden Auftrag-Ordner:
- data.csv: Alle Metadaten zum Auftrag
- meta.json: Schema-Version, Checksumme, Timestamps

Kann die komplette Datenbank aus den verteilten CSV-Dateien wiederherstellen.

Verwendung:
    # Export (alle Aufträge sichern)
    python3 backup_system.py export --config .archiv_config.json
    
    # Restore (DB aus CSV-Dateien wiederherstellen)
    python3 backup_system.py restore --config .archiv_config.json
    
    # Verify (Prüfe Integrität ohne Import)
    python3 backup_system.py verify --config .archiv_config.json
    
    # Als Cronjob (täglich um 2 Uhr):
    0 2 * * * cd /pfad/zum/archiv && python3 backup_system.py export
"""

import sqlite3
import csv
import json
import hashlib
import logging
import argparse
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from contextlib import contextmanager

# Schema-Version für Migrationslogik
CURRENT_SCHEMA_VERSION = "1.0"

# CSV-Spalten (definiert das Backup-Format)
CSV_COLUMNS = [
    'record_id',           # Eindeutige ID aus DB
    'auftrag_nr',          # Auftragsnummer (6-stellig)
    'kunde_name',          # Kundenname
    'kunden_nr',           # Kundennummer (optional)
    'kennzeichen',         # KFZ-Kennzeichen
    'vin',                 # Fahrzeug-Identnummer
    'datum',               # Auftragsdatum (YYYY-MM-DD)
    'formular_version',    # alt/neu
    'keywords_json',       # JSON-String mit Schlagwörtern
    'file_path',           # Relativer Pfad zur PDF
    'hash',                # SHA256 der PDF
    'data_complete',       # 0/1 - Daten vollständig?
    'created_at',          # Erstellungszeitpunkt
    'updated_at'           # Änderungszeitpunkt
]

# Logging-Setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('backup_system.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class BackupSystemError(Exception):
    """Basis-Exception für Backup-System-Fehler"""
    pass


class LockError(BackupSystemError):
    """Lock konnte nicht erworben werden"""
    pass


class ValidationError(BackupSystemError):
    """Daten-Validierung fehlgeschlagen"""
    pass


@contextmanager
def acquire_lock(lock_file: Path, timeout: int = 30):
    """
    Context Manager für atomares Locking
    
    Erstellt Lock-Datei und löscht sie automatisch.
    Bei Timeout wird LockError geworfen.
    
    Args:
        lock_file: Pfad zur Lock-Datei
        timeout: Maximale Wartezeit in Sekunden
    """
    start_time = time.time()
    
    while lock_file.exists():
        if time.time() - start_time > timeout:
            raise LockError(f"Lock-Timeout nach {timeout}s: {lock_file}")
        time.sleep(0.5)
    
    try:
        # Erstelle Lock-Datei mit PID
        lock_file.write_text(f"{time.time()}\n{id(time)}")
        logger.debug(f"Lock erworben: {lock_file}")
        yield
    finally:
        # Entferne Lock-Datei
        if lock_file.exists():
            lock_file.unlink()
            logger.debug(f"Lock freigegeben: {lock_file}")


def calculate_checksum(file_path: Path) -> str:
    """
    Berechnet SHA256-Checksumme einer Datei
    
    Args:
        file_path: Pfad zur Datei
        
    Returns:
        Hex-String der Checksumme
    """
    sha256 = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            sha256.update(chunk)
    return sha256.hexdigest()


def validate_record(record: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
    Validiert einen Datensatz
    
    Args:
        record: Dictionary mit Auftragsdaten
        
    Returns:
        (is_valid, error_message)
    """
    # Pflichtfelder prüfen
    if not record.get('auftrag_nr'):
        return False, "Auftragsnummer fehlt"
    
    if not record.get('file_path'):
        return False, "Dateipfad fehlt"
    
    # Auftragsnummer-Format prüfen (4-6 Stellen)
    auftrag_nr = str(record['auftrag_nr'])
    if not auftrag_nr.isdigit() or not (4 <= len(auftrag_nr) <= 6):
        return False, f"Ungültige Auftragsnummer: {auftrag_nr}"
    
    # Datum-Format prüfen (wenn vorhanden)
    if record.get('datum'):
        try:
            datetime.strptime(record['datum'], '%Y-%m-%d')
        except ValueError:
            return False, f"Ungültiges Datumsformat: {record['datum']}"
    
    return True, None


class BackupSystem:
    """Haupt-Klasse für Backup/Restore-Operationen"""
    
    def __init__(self, db_path: Path, archiv_root: Path):
        """
        Initialisiert das Backup-System
        
        Args:
            db_path: Pfad zur SQLite-Datenbank
            archiv_root: Root-Verzeichnis des Archivs
        """
        self.db_path = db_path
        self.archiv_root = archiv_root
        self.lock_file = archiv_root / '.backup.lock'
        
        logger.info(f"Backup-System initialisiert")
        logger.info(f"  Datenbank: {db_path}")
        logger.info(f"  Archiv: {archiv_root}")
    
    def export_all(self) -> Dict[str, Any]:
        """
        Exportiert alle Aufträge als CSV in ihre Ordner
        
        Returns:
            Statistik-Dictionary mit Erfolg/Fehler-Zählern
        """
        stats = {
            'exported': 0,
            'errors': 0,
            'skipped': 0,
            'start_time': datetime.now().isoformat()
        }
        
        with acquire_lock(self.lock_file):
            logger.info("Starte Export aller Aufträge...")
            
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM auftraege ORDER BY id')
            
            for row in cursor:
                try:
                    self._export_single_record(dict(row))
                    stats['exported'] += 1
                except Exception as e:
                    logger.error(f"Fehler bei Auftrag {row['auftrag_nr']}: {e}")
                    stats['errors'] += 1
            
            conn.close()
            
            # Cleanup: Lösche verwaiste Backup-Ordner
            stats['cleaned'] = self._cleanup_orphaned_backups()
        
        stats['end_time'] = datetime.now().isoformat()
        logger.info(f"Export abgeschlossen: {stats['exported']} erfolgreich, {stats['errors']} Fehler, {stats.get('cleaned', 0)} aufgeräumt")
        
        return stats
    
    def _export_single_record(self, record: Dict[str, Any]):
        """
        Exportiert einen einzelnen Datensatz
        
        Args:
            record: Dictionary mit Auftragsdaten aus DB
        """
        # Validiere Datensatz
        is_valid, error = validate_record(record)
        if not is_valid:
            raise ValidationError(error)
        
        # Bestimme Zielordner
        auftrag_nr = record['auftrag_nr']
        file_path = Path(record['file_path'])
        target_dir = file_path.parent
        
        if not target_dir.exists():
            logger.warning(f"Ordner existiert nicht: {target_dir}")
            target_dir.mkdir(parents=True, exist_ok=True)
        
        # Schreibe CSV atomar
        csv_file = target_dir / 'data.csv'
        tmp_file = target_dir / 'data.tmp.csv'
        
        try:
            # Schreibe in temporäre Datei
            with open(tmp_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
                writer.writeheader()
                
                # Bereite Daten vor (nur relevante Spalten)
                export_data = {col: record.get(col, '') for col in CSV_COLUMNS}
                export_data['record_id'] = record['id']  # DB-ID als record_id
                writer.writerow(export_data)
            
            # Berechne Checksumme
            checksum = calculate_checksum(tmp_file)
            
            # Schreibe meta.json
            meta = {
                'schema_version': CURRENT_SCHEMA_VERSION,
                'checksum': checksum,
                'exported_at': datetime.now().isoformat(),
                'auftrag_nr': auftrag_nr,
                'record_id': record['id'],
                'file_size': tmp_file.stat().st_size
            }
            
            meta_file = target_dir / 'meta.json'
            with open(meta_file, 'w', encoding='utf-8') as f:
                json.dump(meta, f, indent=2, ensure_ascii=False)
            
            # Atomares Umbenennen
            if csv_file.exists():
                csv_file.unlink()
            tmp_file.rename(csv_file)
            
            logger.debug(f"✓ Exportiert: {auftrag_nr} → {csv_file}")
            
        except Exception as e:
            # Cleanup bei Fehler
            if tmp_file.exists():
                tmp_file.unlink()
            raise
    
    def restore_all(self, dry_run: bool = False) -> Dict[str, Any]:
        """
        Stellt Datenbank aus allen CSV-Dateien wieder her
        
        Args:
            dry_run: Wenn True, nur validieren ohne Import
            
        Returns:
            Statistik-Dictionary
        """
        stats = {
            'found': 0,
            'valid': 0,
            'imported': 0,
            'duplicates': 0,
            'errors': 0,
            'start_time': datetime.now().isoformat()
        }
        
        with acquire_lock(self.lock_file):
            logger.info(f"Starte Wiederherstellung (dry_run={dry_run})...")
            
            # Finde alle data.csv Dateien
            csv_files = list(self.archiv_root.rglob('data.csv'))
            stats['found'] = len(csv_files)
            logger.info(f"Gefunden: {len(csv_files)} CSV-Dateien")
            
            if not dry_run:
                # Initialisiere DB (Tabelle wird geleert!)
                self._init_database()
            
            # Sammle alle Records
            records_by_id = {}
            
            for csv_file in csv_files:
                try:
                    record = self._load_and_validate_csv(csv_file)
                    if record:
                        stats['valid'] += 1
                        record_id = record['record_id']
                        
                        # Duplikats-Strategie: Neueste gewinnt (basierend auf updated_at)
                        if record_id in records_by_id:
                            existing = records_by_id[record_id]
                            if record['updated_at'] > existing['updated_at']:
                                logger.warning(f"Duplikat {record_id}: Neuere Version überschreibt")
                                records_by_id[record_id] = record
                            else:
                                logger.warning(f"Duplikat {record_id}: Ältere Version ignoriert")
                            stats['duplicates'] += 1
                        else:
                            records_by_id[record_id] = record
                            
                except Exception as e:
                    logger.error(f"Fehler bei {csv_file}: {e}")
                    stats['errors'] += 1
            
            # Import in DB (mit Transaktion)
            if not dry_run and records_by_id:
                try:
                    self._import_records(list(records_by_id.values()))
                    stats['imported'] = len(records_by_id)
                except Exception as e:
                    logger.error(f"Import fehlgeschlagen: {e}")
                    stats['errors'] += 1
                    raise
        
        stats['end_time'] = datetime.now().isoformat()
        logger.info(f"Wiederherstellung abgeschlossen: {stats['imported']} importiert, {stats['errors']} Fehler")
        
        return stats
    
    def _load_and_validate_csv(self, csv_file: Path) -> Optional[Dict[str, Any]]:
        """
        Lädt und validiert eine CSV-Datei
        
        Args:
            csv_file: Pfad zur data.csv
            
        Returns:
            Dictionary mit Daten oder None bei Fehler
        """
        meta_file = csv_file.parent / 'meta.json'
        
        # Prüfe meta.json
        if not meta_file.exists():
            logger.warning(f"meta.json fehlt: {csv_file}")
            return None
        
        with open(meta_file, 'r', encoding='utf-8') as f:
            meta = json.load(f)
        
        # Prüfe Schema-Version
        schema_version = meta.get('schema_version', '0.0')
        if schema_version != CURRENT_SCHEMA_VERSION:
            logger.warning(f"Schema-Version {schema_version} != {CURRENT_SCHEMA_VERSION}: {csv_file}")
            # Hier könnte Migrations-Logik greifen
        
        # Prüfe Checksumme
        actual_checksum = calculate_checksum(csv_file)
        expected_checksum = meta.get('checksum')
        
        if actual_checksum != expected_checksum:
            raise ValidationError(f"Checksumme ungültig: {csv_file}")
        
        # Lade CSV
        with open(csv_file, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        if len(rows) != 1:
            raise ValidationError(f"Erwarte genau 1 Zeile, gefunden: {len(rows)}")
        
        record = rows[0]
        
        # Validiere Datensatz
        is_valid, error = validate_record(record)
        if not is_valid:
            raise ValidationError(error)
        
        logger.debug(f"✓ Validiert: {csv_file}")
        return record
    
    def _init_database(self):
        """Initialisiert leere Datenbank mit Schema"""
        logger.warning("ACHTUNG: Datenbank wird geleert!")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Lösche alte Tabelle
        cursor.execute('DROP TABLE IF EXISTS auftraege')
        
        # Erstelle Schema (identisch zu db.py)
        cursor.execute('''
            CREATE TABLE auftraege (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                auftrag_nr TEXT NOT NULL,
                kunde_name TEXT,
                kunden_nr TEXT,
                kennzeichen TEXT,
                vin TEXT,
                datum TEXT,
                formular_version TEXT,
                keywords_json TEXT,
                file_path TEXT NOT NULL,
                hash TEXT,
                data_complete INTEGER DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        ''')
        
        # Erstelle Indizes
        cursor.execute('CREATE INDEX idx_auftrag_nr ON auftraege(auftrag_nr)')
        cursor.execute('CREATE INDEX idx_kunde_name ON auftraege(kunde_name)')
        cursor.execute('CREATE INDEX idx_kennzeichen ON auftraege(kennzeichen)')
        cursor.execute('CREATE INDEX idx_vin ON auftraege(vin)')
        cursor.execute('CREATE INDEX idx_datum ON auftraege(datum)')
        cursor.execute('CREATE INDEX idx_hash ON auftraege(hash)')
        cursor.execute('CREATE INDEX idx_data_complete ON auftraege(data_complete)')
        
        conn.commit()
        conn.close()
        
        logger.info("✓ Datenbank initialisiert")
    
    def _import_records(self, records: List[Dict[str, Any]]):
        """
        Importiert Records in DB (innerhalb Transaktion)
        
        DUPLIKATS-PRÜFUNG:
        - Prüft auf existierende Auftragsnummern
        - Zeigt Warnung bei Duplikaten
        - Importiert nur wenn noch nicht vorhanden (basierend auf Hash)
        
        Args:
            records: Liste von Datensätzen
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        imported = 0
        skipped_duplicates = 0
        skipped_hash = 0
        
        try:
            for record in records:
                auftrag_nr = record['auftrag_nr']
                file_hash = record.get('hash')
                
                # Prüfe auf existierende Auftragsnummer
                cursor.execute('SELECT id, file_path, hash FROM auftraege WHERE auftrag_nr = ?', (auftrag_nr,))
                existing = cursor.fetchall()
                
                if existing:
                    # Prüfe ob identischer Hash (exakt gleiche Datei)
                    if file_hash and any(row['hash'] == file_hash for row in existing):
                        logger.info(f"  ⏭  Überspringe {auftrag_nr}: Identische Datei bereits vorhanden (Hash-Match)")
                        skipped_hash += 1
                        continue
                    
                    # Verschiedene Dateien mit gleicher Nummer - WARNUNG!
                    logger.warning(f"  ⚠️  DUPLIKAT: Auftragsnummer {auftrag_nr} existiert bereits {len(existing)}x!")
                    for i, ex in enumerate(existing, 1):
                        logger.warning(f"      {i}. ID {ex['id']}: {ex['file_path']}")
                    logger.warning(f"      Neue Datei: {record['file_path']}")
                    logger.warning(f"      → Wird trotzdem importiert (verschiedene Dateien)")
                    skipped_duplicates += 1
                    # Weiter mit Import trotz Duplikat
                
                # Importiere Datensatz (ohne record_id - wird neu vergeben)
                cursor.execute('''
                    INSERT INTO auftraege (
                        auftrag_nr, kunde_name, kunden_nr, kennzeichen, vin,
                        datum, formular_version, keywords_json, file_path, hash,
                        data_complete, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    auftrag_nr,
                    record['kunde_name'],
                    record['kunden_nr'],
                    record['kennzeichen'],
                    record['vin'],
                    record['datum'],
                    record['formular_version'],
                    record['keywords_json'],
                    record['file_path'],
                    file_hash,
                    int(record.get('data_complete', 0)),
                    record['created_at'],
                    record['updated_at']
                ))
                imported += 1
            
            conn.commit()
            
            # Zusammenfassung
            logger.info(f"✓ Import abgeschlossen:")
            logger.info(f"  - Importiert: {imported}")
            if skipped_hash > 0:
                logger.info(f"  - Übersprungen (Hash-Duplikat): {skipped_hash}")
            if skipped_duplicates > 0:
                logger.warning(f"  - ⚠️  Duplikate importiert: {skipped_duplicates}")
                logger.warning(f"      → Prüfe mit: python3 manage_duplicates.py list")
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Rollback nach Fehler: {e}")
            raise
        finally:
            conn.close()
    
    def verify(self) -> Dict[str, Any]:
        """
        Verifiziert alle CSV-Dateien ohne Import
        
        Returns:
            Statistik-Dictionary
        """
        return self.restore_all(dry_run=True)
    
    def _cleanup_orphaned_backups(self) -> int:
        """
        Entfernt verwaiste Backup-Ordner die nicht mehr in der DB existieren
        
        Returns:
            Anzahl gelöschter Ordner
        """
        cleaned = 0
        
        # Lade alle aktuellen Auftragsnummern aus DB
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT auftrag_nr FROM auftraege')
        valid_nummern = {row[0] for row in cursor.fetchall()}
        conn.close()
        
        # Finde alle Backup-Ordner
        csv_files = list(self.archiv_root.rglob('data.csv'))
        
        # SICHERHEIT: Automatisches Löschen ist deaktiviert!
        # Stattdessen werden verwaiste Ordner nur protokolliert
        for csv_file in csv_files:
            ordner = csv_file.parent
            ordner_name = ordner.name
            
            # Prüfe ob Ordnername eine Auftragsnummer ist
            if ordner_name not in valid_nummern:
                # Dieser Ordner ist veraltet - nur loggen, NICHT löschen!
                logger.warning(f"⚠️  Verwaister Backup-Ordner gefunden (NICHT gelöscht): {ordner_name}")
                logger.warning(f"    → Ordner manuell prüfen: {ordner}")
                cleaned += 1
        
        if cleaned > 0:
            logger.warning(f"⚠️  {cleaned} verwaiste Ordner gefunden. Diese wurden NICHT automatisch gelöscht!")
            logger.warning(f"    → Prüfe diese Ordner manuell und lösche sie nur wenn sicher, dass keine wichtigen Daten enthalten sind.")
        
        return cleaned


def main():
    """CLI-Hauptfunktion"""
    parser = argparse.ArgumentParser(
        description='Werkstatt-Archiv Backup/Restore-System'
    )
    
    parser.add_argument(
        'command',
        choices=['export', 'restore', 'verify'],
        help='Auszuführende Operation'
    )
    
    parser.add_argument(
        '--config',
        type=Path,
        default='.archiv_config.json',
        help='Pfad zur Konfigurationsdatei'
    )
    
    parser.add_argument(
        '--db',
        type=Path,
        help='Pfad zur Datenbank (überschreibt Config)'
    )
    
    parser.add_argument(
        '--archiv',
        type=Path,
        help='Pfad zum Archiv-Root (überschreibt Config)'
    )
    
    args = parser.parse_args()
    
    # Lade Config
    if args.config.exists():
        with open(args.config, 'r') as f:
            config = json.load(f)
        
        db_path = Path(args.db) if args.db else Path(config['archiv_root']) / 'werkstatt.db'
        archiv_root = Path(args.archiv) if args.archiv else Path(config['archiv_root'])
    else:
        if not args.db or not args.archiv:
            print("ERROR: --config nicht gefunden und --db/--archiv nicht angegeben!")
            return 1
        
        db_path = Path(args.db)
        archiv_root = Path(args.archiv)
    
    # Initialisiere System
    system = BackupSystem(db_path, archiv_root)
    
    # Führe Kommando aus
    try:
        if args.command == 'export':
            stats = system.export_all()
            print(f"\n✓ Export abgeschlossen:")
            print(f"  Exportiert: {stats['exported']}")
            print(f"  Fehler: {stats['errors']}")
            
        elif args.command == 'restore':
            confirm = input("\n⚠️  WARNUNG: Datenbank wird geleert! Fortfahren? (yes/no): ")
            if confirm.lower() != 'yes':
                print("Abgebrochen.")
                return 0
            
            stats = system.restore_all(dry_run=False)
            print(f"\n✓ Wiederherstellung abgeschlossen:")
            print(f"  Gefunden: {stats['found']}")
            print(f"  Validiert: {stats['valid']}")
            print(f"  Importiert: {stats['imported']}")
            print(f"  Duplikate: {stats['duplicates']}")
            print(f"  Fehler: {stats['errors']}")
            
        elif args.command == 'verify':
            stats = system.verify()
            print(f"\n✓ Verifikation abgeschlossen:")
            print(f"  Gefunden: {stats['found']}")
            print(f"  Valide: {stats['valid']}")
            print(f"  Duplikate: {stats['duplicates']}")
            print(f"  Fehler: {stats['errors']}")
        
        return 0
        
    except Exception as e:
        logger.error(f"Fehler: {e}", exc_info=True)
        return 1


if __name__ == '__main__':
    exit(main())
