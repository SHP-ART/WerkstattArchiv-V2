#!/usr/bin/env python3
"""
Test der Reprocess-Funktion
"""

import json
from pathlib import Path

# Imports
import config
import ocr
import parser as auftrag_parser
import archive
import db

# Test mit Auftrag ID 13 (033519)
auftrag_id = 13

c = config.Config()
db_path = c.get_archiv_root() / "werkstatt.db"

import sqlite3
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Hole aktuellen Eintrag
cursor.execute('SELECT file_path, auftrag_nr FROM auftraege WHERE id = ?', (auftrag_id,))
row = cursor.fetchone()
conn.close()

if not row:
    print(f"Auftrag {auftrag_id} nicht gefunden")
    exit(1)

old_file_path = Path(row[0])
old_auftrag_nr = row[1]

print(f"Alt: {old_auftrag_nr} - {old_file_path}")

if not old_file_path.exists():
    print(f"Datei nicht gefunden: {old_file_path}")
    exit(1)

print("OCR starten...")
# OCR neu durchführen
texts = ocr.pdf_to_ocr_texts(old_file_path, max_pages=c.config.get('max_pages_to_ocr', 10))
print(f"OCR fertig: {len(texts)} Seiten")

# Metadaten neu extrahieren (nur von Seite 1)
print("Metadaten extrahieren...")
metadata = auftrag_parser.extract_auftrag_metadata(texts[0], fallback_filename=old_file_path.name)
print(f"Metadaten: {metadata}")

# Keywords von allen Seiten
metadata['keywords'] = auftrag_parser.extract_keywords_from_pages(texts, c.config.get('keywords', []))

# Prüfe ob neue Auftragsnummer erkannt wurde
new_auftrag_nr = archive.format_auftrag_nr(metadata['auftrag_nr']) if metadata['auftrag_nr'] else old_auftrag_nr

print(f"Neu: {new_auftrag_nr}")
print(f"Geändert: {new_auftrag_nr != old_auftrag_nr}")
