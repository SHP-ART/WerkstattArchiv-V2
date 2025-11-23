#!/usr/bin/env python3
"""Debug-Script um OCR-Text einer PDF zu inspizieren."""

import sys
from pathlib import Path
import ocr
import parser

if len(sys.argv) < 2:
    print("Verwendung: python3 debug_ocr.py <pfad_zur_pdf>")
    sys.exit(1)

pdf_path = Path(sys.argv[1])

if not pdf_path.exists():
    print(f"Fehler: Datei nicht gefunden: {pdf_path}")
    sys.exit(1)

print(f"=== Analysiere: {pdf_path.name} ===\n")

# OCR durchführen
print("Führe OCR durch...")
texts = ocr.pdf_to_ocr_texts(pdf_path, max_pages=1, lang="deu")

if not texts:
    print("Fehler: Kein Text erkannt")
    sys.exit(1)

# Vollständigen Text von Seite 1 anzeigen
print("\n" + "="*60)
print("VOLLSTÄNDIGER OCR-TEXT VON SEITE 1:")
print("="*60)
print(texts[0])
print("="*60)

# Versuche Auftragsnummer zu finden
print("\n=== Parser-Test ===")
try:
    metadata = parser.extract_auftrag_metadata(texts[0])
    print(f"\n✓ Auftragsnummer gefunden: {metadata['auftrag_nr']}")
    print(f"  Kunde: {metadata.get('name', 'N/A')}")
    print(f"  Kundennummer: {metadata.get('kunden_nr', 'N/A')}")
    print(f"  Datum: {metadata.get('datum', 'N/A')}")
    print(f"  Kennzeichen: {metadata.get('kennzeichen', 'N/A')}")
except parser.ParserError as e:
    print(f"\n✗ Parser-Fehler: {e}")
    print("\nSuche nach 'Auftrag' im Text:")
    for i, line in enumerate(texts[0].split('\n'), 1):
        if 'auftrag' in line.lower():
            print(f"  Zeile {i}: {line.strip()}")
