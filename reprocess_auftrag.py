#!/usr/bin/env python3
"""
Werkstatt-Archiv: Auftrag neu verarbeiten und korrigieren

Führt OCR und Parsing erneut durch und korrigiert Fehler automatisch.
Nützlich wenn:
- Auftragsnummer falsch erkannt wurde
- Parser-Regeln verbessert wurden
- Metadaten fehlen oder falsch sind

Verwendung:
    python3 reprocess_auftrag.py 033519
    python3 reprocess_auftrag.py --all
"""

import sys
import json
import sqlite3
import shutil
from pathlib import Path
from typing import Dict, Any, Optional

import config
import ocr
import parser as auftrag_parser
import archive


def reprocess_auftrag(auftrag_nr: str, c: config.Config) -> bool:
    """
    Verarbeitet einen Auftrag neu und korrigiert Fehler.
    
    Args:
        auftrag_nr: Auftragsnummer (z.B. "033519" oder "303")
        c: Config-Instanz
    
    Returns:
        True wenn erfolgreich, False bei Fehler
    """
    # Formatiere Auftragsnummer
    auftrag_nr_formatted = archive.format_auftrag_nr(auftrag_nr)
    
    print(f"\n{'='*60}")
    print(f"Verarbeite Auftrag {auftrag_nr_formatted} neu...")
    print(f"{'='*60}")
    
    db_path = c.get_archiv_root() / "werkstatt.db"
    
    # Hole Eintrag aus Datenbank
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('SELECT id, file_path, auftrag_nr FROM auftraege WHERE auftrag_nr = ?', 
                   (auftrag_nr_formatted,))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        print(f"❌ Fehler: Auftrag {auftrag_nr_formatted} nicht in Datenbank gefunden")
        return False
    
    auftrag_id = row[0]
    old_file_path = Path(row[1])
    old_auftrag_nr = row[2]
    
    print(f"📄 Alte Daten:")
    print(f"   Auftragsnr: {old_auftrag_nr}")
    print(f"   Datei: {old_file_path.name}")
    
    if not old_file_path.exists():
        print(f"❌ Fehler: Datei nicht gefunden: {old_file_path}")
        return False
    
    # OCR neu durchführen
    print(f"\n🔍 OCR-Erkennung läuft...")
    try:
        texts = ocr.pdf_to_ocr_texts(old_file_path, max_pages=c.config.get('max_pages_to_ocr', 10))
        print(f"   ✓ {len(texts)} Seite(n) erfolgreich verarbeitet")
    except Exception as e:
        print(f"❌ OCR-Fehler: {e}")
        return False
    
    # Metadaten neu extrahieren
    print(f"\n📋 Extrahiere Metadaten...")
    try:
        metadata = auftrag_parser.extract_auftrag_metadata(texts[0], fallback_filename=old_file_path.name)
        metadata['keywords'] = auftrag_parser.extract_keywords_from_pages(texts, c.config.get('keywords', []))
    except Exception as e:
        print(f"❌ Parser-Fehler: {e}")
        return False
    
    # Neue Auftragsnummer
    new_auftrag_nr = archive.format_auftrag_nr(metadata['auftrag_nr']) if metadata['auftrag_nr'] else old_auftrag_nr
    
    print(f"\n📊 Neue Daten:")
    print(f"   Auftragsnr: {new_auftrag_nr}")
    print(f"   Kunden-Nr: {metadata.get('kunden_nr', 'N/A')}")
    print(f"   Name: {metadata.get('name', 'N/A')}")
    print(f"   Datum: {metadata.get('datum', 'N/A')}")
    print(f"   Kennzeichen: {metadata.get('kennzeichen', 'N/A')}")
    print(f"   VIN: {metadata.get('vin', 'N/A')}")
    print(f"   Keywords: {len(metadata.get('keywords', {}))} gefunden")
    
    # Prüfe ob sich was geändert hat
    changed = new_auftrag_nr != old_auftrag_nr
    
    if changed:
        print(f"\n⚠️  Auftragsnummer hat sich geändert: {old_auftrag_nr} → {new_auftrag_nr}")
    else:
        print(f"\n✓ Auftragsnummer unverändert: {new_auftrag_nr}")
    
    # Bestätigung
    response = input("\n❓ Änderungen übernehmen? [j/N]: ")
    if response.lower() not in ['j', 'ja', 'y', 'yes']:
        print("❌ Abgebrochen")
        return False
    
    # Datei verschieben wenn nötig
    new_file_path = old_file_path
    
    if changed:
        print(f"\n📦 Verschiebe Datei...")
        archiv_root = c.get_archiv_root()
        
        # Jahr-basierte Struktur
        if c.config.get('use_year_folders', True):
            year = archive.get_year_from_datum(metadata.get('datum'))
            target_dir = archiv_root / year / new_auftrag_nr
        else:
            thousand_block = archive.get_thousand_block(new_auftrag_nr)
            target_dir = archiv_root / thousand_block / new_auftrag_nr
        
        target_dir.mkdir(parents=True, exist_ok=True)
        
        # Neuer Dateiname
        existing_files = list(target_dir.glob("*.pdf"))
        new_filename = archive.generate_target_filename(
            new_auftrag_nr,
            c.config,
            existing_files,
            metadata
        )
        
        new_file_path = target_dir / new_filename
        
        # Verschiebe
        shutil.move(str(old_file_path), str(new_file_path))
        print(f"   ✓ Verschoben nach: {new_file_path}")
        
        # SICHERHEIT: Verschiebe alten Ordner in Papierkorb
        old_dir = old_file_path.parent
        try:
            if old_dir.exists():
                # Erstelle Trash-Ordner
                from datetime import datetime
                trash_dir = archiv_root / '.trash' / datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
                trash_dir.mkdir(parents=True, exist_ok=True)
                
                # Verschiebe in Papierkorb
                trash_path = trash_dir / old_dir.name
                shutil.move(str(old_dir), str(trash_path))
                print(f"   ✓ Alter Ordner in Papierkorb: {trash_path}")
        except Exception as e:
            print(f"   ⚠️  Alter Ordner konnte nicht verschoben werden: {e}")
    
    # Datenbank aktualisieren
    print(f"\n💾 Aktualisiere Datenbank...")
    file_hash = archive.calculate_file_hash(new_file_path)
    keywords_json = json.dumps(metadata.get('keywords', {}), ensure_ascii=False)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE auftraege 
        SET auftrag_nr = ?,
            kunden_nr = ?,
            kunde_name = ?,
            datum = ?,
            kennzeichen = ?,
            vin = ?,
            file_path = ?,
            hash = ?,
            keywords_json = ?,
            formular_version = ?
        WHERE id = ?
    ''', (
        new_auftrag_nr,
        metadata.get('kunden_nr'),
        metadata.get('name'),
        metadata.get('datum'),
        metadata.get('kennzeichen'),
        metadata.get('vin'),
        str(new_file_path),
        file_hash,
        keywords_json,
        metadata.get('formular_version', 'alt'),
        auftrag_id
    ))
    
    conn.commit()
    conn.close()
    
    print(f"   ✓ Datenbank aktualisiert")
    print(f"\n✅ Auftrag {new_auftrag_nr} erfolgreich neu verarbeitet!")
    
    return True


def main():
    """Hauptfunktion"""
    if len(sys.argv) < 2:
        print("Verwendung:")
        print("  python3 reprocess_auftrag.py <Auftragsnummer>")
        print("  python3 reprocess_auftrag.py --all")
        print()
        print("Beispiele:")
        print("  python3 reprocess_auftrag.py 033519")
        print("  python3 reprocess_auftrag.py 303")
        sys.exit(1)
    
    c = config.Config()
    
    if sys.argv[1] == '--all':
        print("❌ Fehler: --all noch nicht implementiert")
        sys.exit(1)
    
    auftrag_nr = sys.argv[1]
    success = reprocess_auftrag(auftrag_nr, c)
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
