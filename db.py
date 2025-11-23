"""
Datenbank-Verwaltung für Werkstatt-Aufträge.

Dieses Modul verwaltet die SQLite-Datenbank mit allen Auftragsinformationen
und stellt Suchfunktionen bereit.
"""

import sqlite3
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class DatabaseError(Exception):
    """Fehler bei Datenbankoperationen."""
    pass


def init_db(db_path: Path) -> None:
    """
    Erstellt die Datenbank und die notwendigen Tabellen.
    
    Args:
        db_path: Pfad zur SQLite-Datenbankdatei
    
    Raises:
        DatabaseError: Bei Fehlern beim Erstellen der Datenbank
    """
    try:
        logger.info(f"Initialisiere Datenbank: {db_path}")
        
        # Sicherstellen, dass das Verzeichnis existiert
        db_path.parent.mkdir(parents=True, exist_ok=True)
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Tabelle für Aufträge
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS auftraege (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                auftrag_nr TEXT NOT NULL,
                kunden_nr TEXT,
                kunde_name TEXT,
                datum TEXT,
                kennzeichen TEXT,
                vin TEXT,
                formular_version TEXT,
                file_path TEXT NOT NULL,
                hash TEXT,
                keywords_json TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                data_complete INTEGER DEFAULT 0
            )
        ''')
        
        # Indizes für schnellere Suche
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_auftrag_nr ON auftraege(auftrag_nr)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_kunden_nr ON auftraege(kunden_nr)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_kunde_name ON auftraege(kunde_name)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_datum ON auftraege(datum)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_kennzeichen ON auftraege(kennzeichen)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_hash ON auftraege(hash)
        ''')
        
        conn.commit()
        conn.close()
        
        logger.info("Datenbank erfolgreich initialisiert")
        
    except Exception as e:
        raise DatabaseError(f"Fehler beim Initialisieren der Datenbank: {e}")


def insert_auftrag(
    db_path: Path,
    metadata: Dict[str, Any],
    keywords: Dict[str, List[int]],
    file_path: Path,
    file_hash: Optional[str] = None,
    allow_duplicate: bool = True
) -> int:
    """
    Fügt einen neuen Auftrag in die Datenbank ein.
    
    Args:
        db_path: Pfad zur Datenbank
        metadata: Dictionary mit Metadaten (auftrag_nr, kunden_nr, etc.)
        keywords: Dictionary mit gefundenen Schlagwörtern und Seiten
        file_path: Pfad zur archivierten Datei
        file_hash: SHA256-Hash der Datei (optional)
        allow_duplicate: Erlaube doppelte Auftragsnummern (Standard: True für Kompatibilität)
    
    Returns:
        ID des eingefügten Eintrags
    
    Raises:
        DatabaseError: Bei Fehlern beim Einfügen oder wenn Duplikat nicht erlaubt
    """
    try:
        auftrag_nr = metadata.get("auftrag_nr")
        
        # Prüfe auf doppelte Auftragsnummer
        existing = check_duplicate_auftrag_nr(db_path, auftrag_nr)
        
        if existing and not allow_duplicate:
            raise DatabaseError(
                f"Auftragsnummer {auftrag_nr} existiert bereits {len(existing)}x in der Datenbank! "
                f"Erste Datei: {existing[0]['file_path']}"
            )
        
        if existing:
            logger.warning(f"⚠️  ACHTUNG: Auftragsnummer {auftrag_nr} wird DOPPELT gespeichert!")
            logger.warning(f"   Existierende Einträge: {len(existing)}")
            logger.warning(f"   Neue Datei: {file_path}")
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        now = datetime.now().isoformat()
        keywords_json = json.dumps(keywords, ensure_ascii=False)
        
        cursor.execute('''
            INSERT INTO auftraege (
                auftrag_nr, kunden_nr, kunde_name, datum, kennzeichen, vin,
                formular_version, file_path, hash, keywords_json,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            auftrag_nr,
            metadata.get("kunden_nr"),
            metadata.get("name"),
            metadata.get("datum"),
            metadata.get("kennzeichen"),
            metadata.get("vin"),
            metadata.get("formular_version"),
            str(file_path),
            file_hash,
            keywords_json,
            now,
            now
        ))
        
        auftrag_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        if existing:
            logger.info(f"✓ Auftrag als Duplikat gespeichert: ID {auftrag_id}, "
                       f"Auftragsnr. {auftrag_nr} (Vorkommen: {len(existing) + 1})")
        else:
            logger.info(f"✓ Auftrag in Datenbank gespeichert: ID {auftrag_id}, "
                       f"Auftragsnr. {auftrag_nr}")
        
        return auftrag_id
        
    except Exception as e:
        raise DatabaseError(f"Fehler beim Einfügen des Auftrags: {e}")


def check_duplicate_hash(db_path: Path, file_hash: str) -> Optional[Dict[str, Any]]:
    """
    Prüft, ob ein Datei-Hash bereits in der Datenbank existiert.
    
    Args:
        db_path: Pfad zur Datenbank
        file_hash: SHA256-Hash der Datei
    
    Returns:
        Dictionary mit dem gefundenen Eintrag oder None
    """
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM auftraege WHERE hash = ?
        ''', (file_hash,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            result = dict(row)
            logger.info(f"Duplikat gefunden: Hash {file_hash[:16]}... "
                       f"-> Auftrag {result['auftrag_nr']}")
            return result
        
        return None
        
    except Exception as e:
        logger.error(f"Fehler bei Duplikatsprüfung: {e}")
        return None


def check_duplicate_auftrag_nr(db_path: Path, auftrag_nr: str) -> List[Dict[str, Any]]:
    """
    Prüft, ob eine Auftragsnummer bereits in der Datenbank existiert.
    
    Args:
        db_path: Pfad zur Datenbank
        auftrag_nr: Auftragsnummer (exakte Übereinstimmung)
    
    Returns:
        Liste von Dictionaries mit gefundenen Aufträgen (kann mehrere sein)
    """
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM auftraege WHERE auftrag_nr = ?
            ORDER BY created_at DESC
        ''', (auftrag_nr,))
        
        rows = cursor.fetchall()
        conn.close()
        
        results = [dict(row) for row in rows]
        
        if results:
            logger.warning(f"⚠️  Auftragsnummer {auftrag_nr} existiert bereits {len(results)}x in der Datenbank!")
            for i, result in enumerate(results, 1):
                logger.warning(f"   {i}. ID {result['id']}: {result['file_path']} (erstellt: {result['created_at']})")
        
        return results
        
    except Exception as e:
        logger.error(f"Fehler bei Duplikatsprüfung: {e}")
        return []


def search_by_auftrag_nr(db_path: Path, auftrag_nr: str) -> List[Dict[str, Any]]:
    """
    Sucht Aufträge nach Auftragsnummer.
    
    Args:
        db_path: Pfad zur Datenbank
        auftrag_nr: Auftragsnummer (kann auch Teilstring sein)
    
    Returns:
        Liste von Dictionaries mit gefundenen Aufträgen
    """
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM auftraege 
            WHERE auftrag_nr LIKE ?
            ORDER BY auftrag_nr DESC
        ''', (f'%{auftrag_nr}%',))
        
        rows = cursor.fetchall()
        conn.close()
        
        results = [dict(row) for row in rows]
        logger.info(f"Suche nach Auftragsnummer '{auftrag_nr}': {len(results)} Treffer")
        
        return results
        
    except Exception as e:
        raise DatabaseError(f"Fehler bei der Suche: {e}")


def search_by_kunden_nr(db_path: Path, kunden_nr: str) -> List[Dict[str, Any]]:
    """
    Sucht Aufträge nach Kundennummer.
    
    Args:
        db_path: Pfad zur Datenbank
        kunden_nr: Kundennummer
    
    Returns:
        Liste von Dictionaries mit gefundenen Aufträgen
    """
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM auftraege 
            WHERE kunden_nr LIKE ?
            ORDER BY datum DESC, auftrag_nr DESC
        ''', (f'%{kunden_nr}%',))
        
        rows = cursor.fetchall()
        conn.close()
        
        results = [dict(row) for row in rows]
        logger.info(f"Suche nach Kundennummer '{kunden_nr}': {len(results)} Treffer")
        
        return results
        
    except Exception as e:
        raise DatabaseError(f"Fehler bei der Suche: {e}")


def search_by_name(db_path: Path, name: str, partial: bool = True) -> List[Dict[str, Any]]:
    """
    Sucht Aufträge nach Kundenname.
    
    Args:
        db_path: Pfad zur Datenbank
        name: Kundenname
        partial: Ob Teilstring-Suche aktiviert sein soll
    
    Returns:
        Liste von Dictionaries mit gefundenen Aufträgen
    """
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        if partial:
            cursor.execute('''
                SELECT * FROM auftraege 
                WHERE kunde_name LIKE ?
                ORDER BY datum DESC, auftrag_nr DESC
            ''', (f'%{name}%',))
        else:
            cursor.execute('''
                SELECT * FROM auftraege 
                WHERE kunde_name = ?
                ORDER BY datum DESC, auftrag_nr DESC
            ''', (name,))
        
        rows = cursor.fetchall()
        conn.close()
        
        results = [dict(row) for row in rows]
        logger.info(f"Suche nach Name '{name}': {len(results)} Treffer")
        
        return results
        
    except Exception as e:
        raise DatabaseError(f"Fehler bei der Suche: {e}")


def search_by_datum(db_path: Path, von: str, bis: str) -> List[Dict[str, Any]]:
    """
    Sucht Aufträge nach Datumsbereich.
    
    Args:
        db_path: Pfad zur Datenbank
        von: Startdatum (ISO-Format: YYYY-MM-DD)
        bis: Enddatum (ISO-Format: YYYY-MM-DD)
    
    Returns:
        Liste von Dictionaries mit gefundenen Aufträgen
    """
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM auftraege 
            WHERE datum BETWEEN ? AND ?
            ORDER BY datum DESC, auftrag_nr DESC
        ''', (von, bis))
        
        rows = cursor.fetchall()
        conn.close()
        
        results = [dict(row) for row in rows]
        logger.info(f"Suche nach Datum {von} bis {bis}: {len(results)} Treffer")
        
        return results
        
    except Exception as e:
        raise DatabaseError(f"Fehler bei der Suche: {e}")


def search_by_kennzeichen(db_path: Path, kennzeichen: str) -> List[Dict[str, Any]]:
    """
    Sucht Aufträge nach KFZ-Kennzeichen.
    
    Args:
        db_path: Pfad zur Datenbank
        kennzeichen: KFZ-Kennzeichen
    
    Returns:
        Liste von Dictionaries mit gefundenen Aufträgen
    """
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM auftraege 
            WHERE kennzeichen LIKE ?
            ORDER BY datum DESC, auftrag_nr DESC
        ''', (f'%{kennzeichen}%',))
        
        rows = cursor.fetchall()
        conn.close()
        
        results = [dict(row) for row in rows]
        logger.info(f"Suche nach Kennzeichen '{kennzeichen}': {len(results)} Treffer")
        
        return results
        
    except Exception as e:
        raise DatabaseError(f"Fehler bei der Suche: {e}")


def search_by_keyword(db_path: Path, keyword: str) -> List[Dict[str, Any]]:
    """
    Sucht Aufträge, die ein bestimmtes Schlagwort enthalten.
    
    Args:
        db_path: Pfad zur Datenbank
        keyword: Schlagwort (z.B. "Garantie")
    
    Returns:
        Liste von Dictionaries mit gefundenen Aufträgen
    """
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Suche im JSON-Feld (case-insensitive)
        cursor.execute('''
            SELECT * FROM auftraege 
            WHERE keywords_json LIKE ?
            ORDER BY datum DESC, auftrag_nr DESC
        ''', (f'%"{keyword}"%',))
        
        rows = cursor.fetchall()
        conn.close()
        
        # Filtern: Nur Einträge zurückgeben, wo das Keyword tatsächlich vorhanden ist
        results = []
        for row in rows:
            row_dict = dict(row)
            try:
                keywords = json.loads(row_dict['keywords_json'])
                # Case-insensitive Check
                if any(keyword.lower() == kw.lower() for kw in keywords.keys()):
                    results.append(row_dict)
            except:
                pass
        
        logger.info(f"Suche nach Schlagwort '{keyword}': {len(results)} Treffer")
        
        return results
        
    except Exception as e:
        raise DatabaseError(f"Fehler bei der Suche: {e}")


def get_statistics(db_path: Path) -> Dict[str, Any]:
    """
    Sammelt Statistiken über die Datenbank.
    
    Args:
        db_path: Pfad zur Datenbank
    
    Returns:
        Dictionary mit Statistiken
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Gesamtanzahl Aufträge
        cursor.execute('SELECT COUNT(*) FROM auftraege')
        total_auftraege = cursor.fetchone()[0]
        
        # Anzahl mit Kundennummer
        cursor.execute('SELECT COUNT(*) FROM auftraege WHERE kunden_nr IS NOT NULL')
        mit_kunden_nr = cursor.fetchone()[0]
        
        # Anzahl mit Keywords
        cursor.execute('SELECT COUNT(*) FROM auftraege WHERE keywords_json != "{}"')
        mit_keywords = cursor.fetchone()[0]
        
        # Häufigste Schlagwörter (Top 10)
        cursor.execute('SELECT keywords_json FROM auftraege WHERE keywords_json IS NOT NULL')
        rows = cursor.fetchall()
        
        keyword_counts = {}
        for row in rows:
            try:
                keywords = json.loads(row[0])
                for kw in keywords.keys():
                    keyword_counts[kw] = keyword_counts.get(kw, 0) + 1
            except:
                pass
        
        top_keywords = sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        
        conn.close()
        
        stats = {
            "total_auftraege": total_auftraege,
            "mit_kunden_nr": mit_kunden_nr,
            "mit_keywords": mit_keywords,
            "top_keywords": top_keywords
        }
        
        logger.info(f"Datenbank-Statistik: {stats}")
        return stats
        
    except Exception as e:
        logger.error(f"Fehler beim Sammeln der Statistiken: {e}")
        return {}


def export_to_csv(db_path: Path, output_path: Path) -> None:
    """
    Exportiert alle Aufträge als CSV-Datei.
    
    Args:
        db_path: Pfad zur Datenbank
        output_path: Pfad zur Ausgabe-CSV
    
    Raises:
        DatabaseError: Bei Fehlern beim Export
    """
    import csv
    
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM auftraege ORDER BY auftrag_nr')
        rows = cursor.fetchall()
        
        if not rows:
            logger.warning("Keine Daten zum Exportieren vorhanden")
            return
        
        # CSV schreiben
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            
            for row in rows:
                writer.writerow(dict(row))
        
        conn.close()
        
        logger.info(f"Datenbank exportiert nach: {output_path} ({len(rows)} Einträge)")
        
    except Exception as e:
        raise DatabaseError(f"Fehler beim CSV-Export: {e}")


def search_by_kunde(db_path: Path, kunde_name: str) -> List[Dict[str, Any]]:
    """
    Sucht Aufträge nach Kundenname.
    
    Args:
        db_path: Pfad zur Datenbank
        kunde_name: Kundenname (Teilstring-Suche)
    
    Returns:
        Liste von Dictionaries mit gefundenen Aufträgen
    """
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM auftraege 
            WHERE kunde_name LIKE ?
            ORDER BY datum DESC, auftrag_nr DESC
        ''', (f'%{kunde_name}%',))
        
        rows = cursor.fetchall()
        conn.close()
        
        results = [dict(row) for row in rows]
        logger.info(f"Suche nach Kunde '{kunde_name}': {len(results)} Treffer")
        
        return results
        
    except Exception as e:
        raise DatabaseError(f"Fehler bei der Suche: {e}")


def search_by_vin(db_path: Path, vin: str) -> List[Dict[str, Any]]:
    """
    Sucht Aufträge nach VIN (Fahrzeugidentifikationsnummer).
    
    Args:
        db_path: Pfad zur Datenbank
        vin: VIN (komplett oder Teilstring)
    
    Returns:
        Liste von Dictionaries mit gefundenen Aufträgen
    """
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM auftraege 
            WHERE vin LIKE ?
            ORDER BY datum DESC, auftrag_nr DESC
        ''', (f'%{vin}%',))
        
        rows = cursor.fetchall()
        conn.close()
        
        results = [dict(row) for row in rows]
        logger.info(f"Suche nach VIN '{vin}': {len(results)} Treffer")
        
        return results
        
    except Exception as e:
        raise DatabaseError(f"Fehler bei der Suche: {e}")


def search_by_vis(db_path: Path, vis: str) -> List[Dict[str, Any]]:
    """
    Sucht Aufträge nach VIS (letzte 6 Zeichen der VIN).
    
    Args:
        db_path: Pfad zur Datenbank
        vis: VIS (letzte 6 Zeichen der VIN)
    
    Returns:
        Liste von Dictionaries mit gefundenen Aufträgen
    """
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Suche nach VIN die mit dem VIS endet
        cursor.execute('''
            SELECT * FROM auftraege 
            WHERE vin LIKE ?
            ORDER BY datum DESC, auftrag_nr DESC
        ''', (f'%{vis}',))
        
        rows = cursor.fetchall()
        conn.close()
        
        results = [dict(row) for row in rows]
        logger.info(f"Suche nach VIS '{vis}': {len(results)} Treffer")
        
        return results
        
    except Exception as e:
        raise DatabaseError(f"Fehler bei der Suche: {e}")


def search_by_date_range(db_path: Path, von: str, bis: str) -> List[Dict[str, Any]]:
    """
    Sucht Aufträge nach Datumsbereich.
    Alias für search_by_datum() für Kompatibilität.
    
    Args:
        db_path: Pfad zur Datenbank
        von: Startdatum (ISO-Format: YYYY-MM-DD)
        bis: Enddatum (ISO-Format: YYYY-MM-DD)
    
    Returns:
        Liste von Dictionaries mit gefundenen Aufträgen
    """
    return search_by_datum(db_path, von, bis)


def search_by_month(db_path: Path, monat: str) -> List[Dict[str, Any]]:
    """
    Sucht Aufträge nach Monat (z.B. "2024-07").
    
    Args:
        db_path: Pfad zur Datenbank
        monat: Jahr-Monat im Format YYYY-MM
    
    Returns:
        Liste von Dictionaries mit gefundenen Aufträgen
    """
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM auftraege 
            WHERE datum LIKE ?
            ORDER BY datum DESC, auftrag_nr DESC
        ''', (f'{monat}%',))
        
        rows = cursor.fetchall()
        conn.close()
        
        results = [dict(row) for row in rows]
        logger.info(f"Suche nach Monat '{monat}': {len(results)} Treffer")
        
        return results
        
    except Exception as e:
        raise DatabaseError(f"Fehler bei der Suche: {e}")


def search_by_year(db_path: Path, jahr: str) -> List[Dict[str, Any]]:
    """
    Sucht Aufträge nach Jahr (z.B. "2024").
    
    Args:
        db_path: Pfad zur Datenbank
        jahr: Jahr im Format YYYY
    
    Returns:
        Liste von Dictionaries mit gefundenen Aufträgen
    """
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM auftraege 
            WHERE datum LIKE ?
            ORDER BY datum DESC, auftrag_nr DESC
        ''', (f'{jahr}%',))
        
        rows = cursor.fetchall()
        conn.close()
        
        results = [dict(row) for row in rows]
        logger.info(f"Suche nach Jahr '{jahr}': {len(results)} Treffer")
        
        return results
        
    except Exception as e:
        raise DatabaseError(f"Fehler bei der Suche: {e}")


def search_multi_criteria(db_path: Path, criteria: Dict[str, str]) -> List[Dict[str, Any]]:
    """
    Sucht nach mehreren Kriterien gleichzeitig (UND-Verknüpfung).
    
    Args:
        db_path: Pfad zur Datenbank
        criteria: Dictionary mit Suchkriterien:
                  - auftrag_nr: Auftragsnummer (LIKE)
                  - kunde_name: Kundenname (LIKE)
                  - kennzeichen: Kennzeichen (LIKE)
                  - vin: VIN (LIKE)
                  - kunden_nr: Kundennummer (LIKE)
                  - datum_von: Start-Datum (>=)
                  - datum_bis: End-Datum (<=)
                  - jahr: Jahr (LIKE)
                  - monat: Jahr-Monat (LIKE)
                  - keyword: Schlagwort (JSON-Suche)
    
    Returns:
        Liste von Dictionaries mit Auftragsdaten
    
    Raises:
        DatabaseError: Bei Datenbankfehlern
    """
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Baue SQL-Query dynamisch basierend auf vorhandenen Kriterien
        where_clauses = []
        params = []
        
        if criteria.get('auftrag_nr'):
            where_clauses.append('auftrag_nr LIKE ?')
            params.append(f'%{criteria["auftrag_nr"]}%')
        
        if criteria.get('kunde_name'):
            where_clauses.append('kunde_name LIKE ?')
            params.append(f'%{criteria["kunde_name"]}%')
        
        if criteria.get('kennzeichen'):
            where_clauses.append('kennzeichen LIKE ?')
            params.append(f'%{criteria["kennzeichen"]}%')
        
        if criteria.get('vin'):
            where_clauses.append('vin LIKE ?')
            params.append(f'%{criteria["vin"]}%')
        
        if criteria.get('kunden_nr'):
            where_clauses.append('kunden_nr LIKE ?')
            params.append(f'%{criteria["kunden_nr"]}%')
        
        if criteria.get('datum_von'):
            where_clauses.append('datum >= ?')
            params.append(criteria['datum_von'])
        
        if criteria.get('datum_bis'):
            where_clauses.append('datum <= ?')
            params.append(criteria['datum_bis'])
        
        if criteria.get('jahr'):
            where_clauses.append('datum LIKE ?')
            params.append(f'{criteria["jahr"]}%')
        
        if criteria.get('monat'):
            where_clauses.append('datum LIKE ?')
            params.append(f'{criteria["monat"]}%')
        
        if criteria.get('keyword'):
            where_clauses.append('keywords_json LIKE ?')
            params.append(f'%"{criteria["keyword"]}"%')
        
        # Wenn keine Kriterien angegeben, gebe alle zurück
        if not where_clauses:
            query = 'SELECT * FROM auftraege ORDER BY datum DESC, auftrag_nr DESC'
            cursor.execute(query)
        else:
            where_sql = ' AND '.join(where_clauses)
            query = f'SELECT * FROM auftraege WHERE {where_sql} ORDER BY datum DESC, auftrag_nr DESC'
            cursor.execute(query, params)
        
        rows = cursor.fetchall()
        conn.close()
        
        results = [dict(row) for row in rows]
        logger.info(f"Multi-Kriterien-Suche: {len(criteria)} Kriterien, {len(results)} Treffer")
        
        return results
        
    except Exception as e:
        raise DatabaseError(f"Fehler bei der Multi-Kriterien-Suche: {e}")


def mark_auftrag_complete(db_path: Path, auftrag_id: int) -> bool:
    """
    Markiert einen Auftrag als vollständig (data_complete = 1).
    
    Args:
        db_path: Pfad zur Datenbank
        auftrag_id: ID des Auftrags
    
    Returns:
        True wenn erfolgreich, False wenn Auftrag nicht gefunden
    
    Raises:
        DatabaseError: Bei Datenbankfehlern
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Prüfe ob Spalte existiert, wenn nicht, füge sie hinzu
        cursor.execute("PRAGMA table_info(auftraege)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'data_complete' not in columns:
            logger.info("Füge Spalte 'data_complete' zur Datenbank hinzu")
            cursor.execute('ALTER TABLE auftraege ADD COLUMN data_complete INTEGER DEFAULT 0')
            conn.commit()
        
        # Markiere als vollständig
        cursor.execute('UPDATE auftraege SET data_complete = 1 WHERE id = ?', (auftrag_id,))
        affected = cursor.rowcount
        
        conn.commit()
        conn.close()
        
        if affected > 0:
            logger.info(f"Auftrag ID {auftrag_id} als vollständig markiert")
            return True
        else:
            logger.warning(f"Auftrag ID {auftrag_id} nicht gefunden")
            return False
        
    except Exception as e:
        raise DatabaseError(f"Fehler beim Markieren als vollständig: {e}")


def find_matching_vehicle_data(db_path: Path, kennzeichen: Optional[str] = None, 
                                vin: Optional[str] = None, 
                                exclude_auftrag_nr: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Sucht nach historischen Auftragsdaten basierend auf Kennzeichen oder VIN.
    
    Diese Funktion ermöglicht Auto-Vervollständigung fehlender Daten durch 
    Abgleich mit älteren Aufträgen des gleichen Fahrzeugs.
    
    Suchreihenfolge:
    1. Exakte VIN-Übereinstimmung (höchste Priorität)
    2. Exaktes Kennzeichen
    3. Kennzeichen ohne Leerzeichen/Bindestriche (normalisiert)
    
    Args:
        db_path: Pfad zur Datenbank
        kennzeichen: Kennzeichen zum Suchen (optional)
        vin: VIN zum Suchen (optional)
        exclude_auftrag_nr: Auftragsnummer die ausgeschlossen werden soll (aktueller Auftrag)
    
    Returns:
        Dict mit Fahrzeugdaten (kunde_name, kunden_nr, kennzeichen, vin) oder None
    
    Example:
        >>> data = find_matching_vehicle_data(db_path, kennzeichen="B-MW 1234")
        >>> if data:
        >>>     print(f"Gefunden: {data['kunde_name']}, VIN: {data['vin']}")
    """
    try:
        if not kennzeichen and not vin:
            logger.debug("Keine Suchkriterien für Fahrzeugdaten-Matching angegeben")
            return None
        
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # 1. Suche nach VIN (höchste Priorität, da eindeutig)
        if vin and len(vin) >= 10:  # VIN sollte mindestens 10 Zeichen haben
            query = '''
                SELECT kunde_name, kunden_nr, kennzeichen, vin, auftrag_nr, datum
                FROM auftraege 
                WHERE vin = ? AND vin IS NOT NULL AND vin != ''
            '''
            if exclude_auftrag_nr:
                query += ' AND auftrag_nr != ?'
                cursor.execute(query + ' ORDER BY datum DESC LIMIT 1', (vin, exclude_auftrag_nr))
            else:
                cursor.execute(query + ' ORDER BY datum DESC LIMIT 1', (vin,))
            
            row = cursor.fetchone()
            if row:
                result = dict(row)
                logger.info(f"✓ Fahrzeugdaten gefunden via VIN '{vin}': {result['kunde_name']} (Auftrag {result['auftrag_nr']})")
                conn.close()
                return result
        
        # 2. Suche nach exaktem Kennzeichen
        if kennzeichen:
            query = '''
                SELECT kunde_name, kunden_nr, kennzeichen, vin, auftrag_nr, datum
                FROM auftraege 
                WHERE kennzeichen = ? AND kennzeichen IS NOT NULL AND kennzeichen != ''
            '''
            if exclude_auftrag_nr:
                query += ' AND auftrag_nr != ?'
                cursor.execute(query + ' ORDER BY datum DESC LIMIT 1', (kennzeichen, exclude_auftrag_nr))
            else:
                cursor.execute(query + ' ORDER BY datum DESC LIMIT 1', (kennzeichen,))
            
            row = cursor.fetchone()
            if row:
                result = dict(row)
                logger.info(f"✓ Fahrzeugdaten gefunden via Kennzeichen '{kennzeichen}': {result['kunde_name']} (Auftrag {result['auftrag_nr']})")
                conn.close()
                return result
            
            # 3. Normalisierte Suche (ohne Leerzeichen/Bindestriche)
            # OCR erkennt manchmal "B MW 1234" statt "B-MW 1234"
            kz_normalized = kennzeichen.replace(' ', '').replace('-', '').upper()
            if len(kz_normalized) >= 4:  # Mindestlänge für sinnvolles Matching
                query = '''
                    SELECT kunde_name, kunden_nr, kennzeichen, vin, auftrag_nr, datum
                    FROM auftraege 
                    WHERE REPLACE(REPLACE(UPPER(kennzeichen), ' ', ''), '-', '') = ?
                    AND kennzeichen IS NOT NULL AND kennzeichen != ''
                '''
                if exclude_auftrag_nr:
                    query += ' AND auftrag_nr != ?'
                    cursor.execute(query + ' ORDER BY datum DESC LIMIT 1', (kz_normalized, exclude_auftrag_nr))
                else:
                    cursor.execute(query + ' ORDER BY datum DESC LIMIT 1', (kz_normalized,))
                
                row = cursor.fetchone()
                if row:
                    result = dict(row)
                    logger.info(f"✓ Fahrzeugdaten gefunden via normalisiertes Kennzeichen '{kz_normalized}': {result['kunde_name']} (Auftrag {result['auftrag_nr']})")
                    conn.close()
                    return result
        
        conn.close()
        logger.debug(f"Keine historischen Fahrzeugdaten gefunden für KZ='{kennzeichen}', VIN='{vin}'")
        return None
        
    except Exception as e:
        logger.error(f"Fehler bei Fahrzeugdaten-Matching: {e}")
        return None


def suggest_missing_data(db_path: Path, auftrag_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Schlägt fehlende Daten vor basierend auf historischen Aufträgen.
    
    Analysiert die vorhandenen Daten eines Auftrags und ergänzt fehlende Felder
    durch Matching mit älteren Aufträgen (via Kennzeichen oder VIN).
    
    Args:
        db_path: Pfad zur Datenbank
        auftrag_data: Dict mit aktuellen Auftragsdaten (kann unvollständig sein)
            Erwartet: auftrag_nr, kennzeichen, vin, kunde_name, kunden_nr
    
    Returns:
        Dict mit Vorschlägen für fehlende Felder:
        {
            'suggestions': {
                'kunde_name': 'Max Mustermann',
                'kunden_nr': '12345',
                'vin': 'WVWZZZ1KZ8W123456',
                'kennzeichen': 'B-MW 1234'
            },
            'matched': True/False,  # Wurde ein Match gefunden?
            'match_source': 'vin' / 'kennzeichen' / None,  # Wie wurde gematcht?
            'source_auftrag': '076329'  # Quell-Auftragsnummer
        }
    
    Example:
        >>> data = {'auftrag_nr': '076330', 'kennzeichen': 'B-MW 1234', 'kunde_name': None}
        >>> suggestions = suggest_missing_data(db_path, data)
        >>> if suggestions['matched']:
        >>>     print(f"Vorschlag: {suggestions['suggestions']['kunde_name']}")
    """
    try:
        result = {
            'suggestions': {},
            'matched': False,
            'match_source': None,
            'source_auftrag': None
        }
        
        # Extrahiere vorhandene Daten
        current_kz = auftrag_data.get('kennzeichen')
        current_vin = auftrag_data.get('vin')
        current_auftrag_nr = auftrag_data.get('auftrag_nr')
        
        # Suche nach passendem historischen Auftrag
        match = find_matching_vehicle_data(
            db_path, 
            kennzeichen=current_kz, 
            vin=current_vin,
            exclude_auftrag_nr=current_auftrag_nr
        )
        
        if not match:
            logger.debug(f"Keine Matching-Daten für Auftrag {current_auftrag_nr}")
            return result
        
        # Baue Vorschläge für fehlende Felder
        result['matched'] = True
        result['source_auftrag'] = match['auftrag_nr']
        
        # Bestimme Match-Quelle
        if current_vin and match.get('vin') == current_vin:
            result['match_source'] = 'vin'
        elif current_kz:
            result['match_source'] = 'kennzeichen'
        
        # Schlage nur fehlende/ungültige Felder vor
        # WICHTIG: Auftragsnummer wird NIEMALS vorgeschlagen oder überschrieben!
        
        if not auftrag_data.get('kunde_name') or auftrag_data.get('kunde_name') in ['N/A', 'Unbekannt', '']:
            if match.get('kunde_name'):
                result['suggestions']['kunde_name'] = match['kunde_name']
        
        if not auftrag_data.get('kunden_nr'):
            if match.get('kunden_nr'):
                result['suggestions']['kunden_nr'] = match['kunden_nr']
        
        if not auftrag_data.get('vin') or len(auftrag_data.get('vin', '')) < 10:
            if match.get('vin'):
                result['suggestions']['vin'] = match['vin']
        
        if not auftrag_data.get('kennzeichen') or auftrag_data.get('kennzeichen') in ['N/A', 'ohne_kz', '']:
            if match.get('kennzeichen'):
                result['suggestions']['kennzeichen'] = match['kennzeichen']
        
        # Sicherheitscheck: Entferne auftrag_nr falls sie versehentlich hinzugefügt wurde
        result['suggestions'].pop('auftrag_nr', None)
        
        if result['suggestions']:
            logger.info(f"✓ Vorschläge für Auftrag {current_auftrag_nr} gefunden (Quelle: {result['source_auftrag']} via {result['match_source']}): {list(result['suggestions'].keys())}")
        
        return result
        
    except Exception as e:
        logger.error(f"Fehler bei Daten-Vorschlägen: {e}")
        return {
            'suggestions': {},
            'matched': False,
            'match_source': None,
            'source_auftrag': None
        }
