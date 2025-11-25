"""
Parser für Werkstatt-Aufträge.

Dieses Modul extrahiert Metadaten aus dem OCR-Text von Seite 1 (Auftragsnummer,
Kundendaten, etc.) und sucht nach Schlagwörtern in den Folgeseiten (Seiten 2-10).
"""

import re
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ParserError(Exception):
    """Fehler beim Parsen von Auftragsdaten."""
    pass


def extract_auftragsnummer(text: str) -> Optional[str]:
    """
    Extrahiert die Auftragsnummer aus dem Text.

    Unterstützte Formate:
    - "Auftrag Nr. 303"
    - "Auftrag-Nr.: 303"
    - "Auftragsnummer: 76329"
    - "Werkstatt – Auftrag Nr. 303"
    - "Werkstatt - Auftrag Nr. Datum:" (fehlende Nummer - wird von anderen Patterns gefunden)
    - "Auftrags-Nr. 12345"
    - "AR "Auftragsnummer:\n76329" (LOCO-Soft Format)

    Args:
        text: OCR-Text von Seite 1

    Returns:
        Auftragsnummer als String oder None
    """
    # Verschiedene Muster für Auftragsnummer
    patterns = [
        # Direkt mit Label (3-6 Ziffern)
        r'Auftrag\s*-?\s*Nr\.?\s*[:.]?\s*(\d{3,6})',
        r'Auftragsnummer\s*[:.]?\s*(\d{3,6})',
        r'Auftrags\s*-?\s*Nr\.?\s*[:.]?\s*(\d{3,6})',
        r'Werkstatt\s*[–-]\s*Auftrag\s*Nr\.?\s*[:.]?\s*(\d{3,6})',
        r'Auftrag\s*[:.]?\s*(\d{3,6})',
        # RO-Nummer (Repair Order - alte Citroen-Formulare)
        r'RO!?\s*(\d{5,6})',
        # LOCO-Soft: Auftragsnummer mit Zeilenumbruch
        r'Auftragsnummer\s*[:\.]?\s*[\r\n]+\s*(\d{3,6})',
        # Nach "AR" kommt oft die Auftragsnummer
        r'AR\s*["\']?\s*Auftragsnummer\s*[:\.]?\s*[\r\n]*\s*(\d{3,6})',
        # Citroën/Peugeot Format: "1710 75187" - zweite Zahl ist Auftragsnummer
        r'\b\d{4}\s+(\d{5})\b',
        # 5-6 stellige Zahl am Anfang einer Zeile (typisch für LOCO-Soft)
        r'^\s*(\d{5,6})\s*$',
        # Nach "Seite:" steht manchmal die Auftragsnummer in der vorherigen Zeile
        r'(\d{3,6})\s*[\r\n]+\s*Seite:',
        # Kurze 3-stellige Nummer direkt nach "Auftrag" oder "Nr."
        r'(?:Auftrag|Nr\.)\s*[:.]?\s*(\d{3})(?:\s|$|\D)',
        # "Auftrags Nr" ohne Bindestrich, gefolgt von 3-stelliger Nummer
        r'Auftrags\s+Nr\.?\s*[:.]?\s*(\d{3})(?:\s|$|\D)',
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
        if match:
            auftrag_nr = match.group(1)
            # Prüfe ob die Zahl plausibel ist (nicht z.B. ein Datum oder PLZ)
            if len(auftrag_nr) >= 3:
                logger.debug(f"Auftragsnummer gefunden: {auftrag_nr} (Pattern: {pattern})")
                return auftrag_nr

    logger.warning("Keine Auftragsnummer gefunden")
    return None


def extract_kundennummer(text: str) -> Optional[str]:
    """
    Extrahiert die Kundennummer aus dem Text.
    
    Unterstützte Formate:
    - "Kd.Nr.: 27129"
    - "Kunden-Nr.: 27129"
    - "Kundennummer: 27129"
    
    Args:
        text: OCR-Text von Seite 1
    
    Returns:
        Kundennummer als String oder None
    """
    patterns = [
        r'Kd\.?\s*-?\s*Nr\.?\s*[:.]?\s*(\d+)',
        r'Kunden\s*-?\s*Nr\.?\s*[:.]?\s*(\d+)',
        r'Kundennummer\s*[:.]?\s*(\d+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            kunden_nr = match.group(1)
            logger.debug(f"Kundennummer gefunden: {kunden_nr}")
            return kunden_nr
    
    logger.debug("Keine Kundennummer gefunden (optional)")
    return None


def extract_name(text: str) -> Optional[str]:
    """
    Extrahiert den Kundennamen aus dem Text.
    
    Sucht nach Mustern wie:
    - "Name: Sybille Voigt"
    - "Herrn Max Mustermann"
    - "Frau Maria Schmidt"
    
    Args:
        text: OCR-Text von Seite 1
    
    Returns:
        Kundenname als String oder None
    """
    # Muster: "Name:" gefolgt von Text (bis Zeilenende, inkl. Firmennamen)
    match = re.search(r'Name\s*[:.]?\s*(.+?)(?:\n|$)', text, re.MULTILINE)
    if match:
        name = match.group(1).strip()
        # Bereinige den Namen
        name = re.sub(r'\s+', ' ', name)  # Multiple Leerzeichen zu einem
        # Entferne trailing Sonderzeichen
        name = re.sub(r'[,.\s]+$', '', name)
        # Prüfe dass es mindestens einen Buchstaben enthält
        if re.search(r'[A-ZÄÖÜ][a-zäöüß]', name) and len(name) > 2:
            logger.debug(f"Name gefunden (Feld): {name}")
            return name
    
    # Alternative: Anrede + Name (mit optionalem Zeilenumbruch)
    # Erlaubt "Frau\nAntje Bär" oder "Frau Antje Bär"
    # WICHTIG: Nur bis zum nächsten Zeilenumbruch (nicht über mehrere Zeilen)
    match = re.search(r'(?:Herrn|Frau|Herr)\s*\n?\s*([A-ZÄÖÜ][a-zäöüß]+(?:[ \t]+[A-ZÄÖÜ][a-zäöüß]+)*)', text, re.IGNORECASE | re.MULTILINE)
    if match:
        name = match.group(1).strip()
        # Bereinige mögliche Zeilenumbrüche (sollten nicht vorkommen)
        name = name.split('\n')[0].strip()
        # Prüfe dass Name keine Straße/PLZ/Zahlen enthält
        if not any(char.isdigit() for char in name) and len(name.split()) <= 3:
            logger.debug(f"Name gefunden (Anrede): {name}")
            return name
    
    # Alternative: Freistehender Name nach Vertragswerkstatt/Werkstatt (Citroën-Format)
    # Suche nach "Vertragswerkstatt" oder "Werkstatt" gefolgt von Nummer, dann Name in nächsten Zeilen
    match = re.search(r'(?:Vertrags)?[Ww]erkstatt.*?\n.*?\n\s*([A-ZÄÖÜ][a-zäöüß]+\s+[A-ZÄÖÜ][a-zäöüß]+)', text, re.MULTILINE | re.DOTALL)
    if match:
        name = match.group(1).strip()
        # Prüfe dass es kein Stadt-/Straßenname ist
        if name and not any(word in name.lower() for word in ['straße', 'strasse', 'str.', 'weg', 'platz', 'gmbh', 'autohaus']):
            logger.debug(f"Name gefunden (freistehend): {name}")
            return name
    
    logger.debug("Kein Name gefunden (optional)")
    return None


def extract_datum(text: str) -> Optional[str]:
    """
    Extrahiert das Datum aus dem Text.
    
    Unterstützte Formate:
    - TT.MM.JJJJ (z.B. "17.11.2025")
    - TT.MM.JJ (z.B. "17.11.25")
    
    Args:
        text: OCR-Text von Seite 1
    
    Returns:
        Datum im ISO-Format (YYYY-MM-DD) oder None
    """
    # Muster: TT.MM.JJJJ oder TT.MM.JJ
    patterns = [
        r'\b(\d{2})\.(\d{2})\.(\d{4})\b',  # TT.MM.JJJJ
        r'\b(\d{2})\.(\d{2})\.(\d{2})\b',   # TT.MM.JJ
    ]
    
    for pattern in patterns:
        matches = re.finditer(pattern, text)
        for match in matches:
            day, month, year = match.groups()
            
            # Jahr korrigieren bei zweistelliger Angabe
            if len(year) == 2:
                year_int = int(year)
                # Annahme: 00-50 = 2000-2050, 51-99 = 1951-1999
                if year_int <= 50:
                    year = f"20{year}"
                else:
                    year = f"19{year}"
            
            # Datum validieren
            try:
                date_obj = datetime.strptime(f"{day}.{month}.{year}", "%d.%m.%Y")
                iso_date = date_obj.strftime("%Y-%m-%d")
                logger.debug(f"Datum gefunden: {iso_date}")
                return iso_date
            except ValueError:
                continue
    
    logger.debug("Kein gültiges Datum gefunden (optional)")
    return None


def extract_kennzeichen(text: str) -> Optional[str]:
    """
    Extrahiert das KFZ-Kennzeichen aus dem Text.

    Deutsches Format: 1-3 Buchstaben, Bindestrich (optional), 1-2 Buchstaben, 1-4 Zahlen
    Beispiele:
    - "B-AB 1234"
    - "DD GU 9705" (ohne Bindestrich - häufig bei OCR)
    - "HH-XY 123"
    - "SFB-KI 23E"

    Args:
        text: OCR-Text von Seite 1

    Returns:
        Kennzeichen als String oder None
    """
    # Pattern mit Kontext - suche nach Label "Kennzeichen" oder "Amtl.Kennzeichen"
    context_pattern = r'(?:Amtl\.?\s*)?[Kk]ennzeichen\s*[:.]?\s*([A-ZÄÖÜ]{1,3}\s*-?\s*[A-Z]{1,2}\s+\d{1,4}[EH]?)'
    match = re.search(context_pattern, text)
    if match:
        kennzeichen_raw = match.group(1)
        # Normalisiere
        kennzeichen = re.sub(r'\s+', ' ', kennzeichen_raw.strip())
        kennzeichen = re.sub(r'\s*-\s*', '-', kennzeichen)
        kennzeichen = re.sub(r'([A-Z])(\d)', r'\1 \2', kennzeichen)
        logger.debug(f"Kennzeichen gefunden (Label): {kennzeichen}")
        return kennzeichen

    # Fallback: Deutsches Kennzeichen-Muster (ohne Kontext, kann Fehlerkennungen geben)
    patterns = [
        # Pattern 1: Mit Leerzeichen "SFB-KI 23E" oder "B-AB 1234"
        r'\b([A-ZÄÖÜ]{1,3})\s*-\s*([A-Z]{1,2})\s+(\d{1,4}[EH]?)\b',
        # Pattern 2: Ohne Leerzeichen "SFB-KI23E" oder "SFB-UG1"
        r'\b([A-ZÄÖÜ]{1,3})\s*-\s*([A-Z]{1,2})(\d{1,4}[EH]?)\b',
        # Pattern 3: OHNE Bindestrich "DD GU 9705" (OCR-Fehler - Bindestrich fehlt)
        r'\b([A-ZÄÖÜ]{1,3})\s+([A-Z]{1,2})\s+(\d{1,4}[EH]?)\b',
    ]

    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            ort, buchstaben, zahlen = match.groups()
            # Kennzeichen normalisieren: "B-AB 1234"
            kennzeichen = f"{ort}-{buchstaben} {zahlen}"

            # Filter: Vermeide false positives (THP, EAT, etc. sind keine Orte)
            # Deutsche Orte sind typischerweise 1-3 Buchstaben, aber nicht "TH-P" o.ä.
            if len(ort) <= 3 and len(buchstaben) <= 2 and len(zahlen) <= 4:
                # Prüfe ob es kein Motorcode ist (THP, EAT, etc.)
                if not (ort == 'TH' and buchstaben == 'P') and not (ort == 'EA' and buchstaben == 'T'):
                    logger.debug(f"Kennzeichen gefunden: {kennzeichen}")
                    return kennzeichen
            logger.debug(f"Kennzeichen gefunden: {kennzeichen}")
            return kennzeichen

    logger.debug("Kein Kennzeichen gefunden (optional)")
    return None


def extract_vin(text: str) -> Optional[str]:
    """
    Extrahiert die Fahrgestellnummer (VIN) aus dem Text.

    VIN-Format: 17 alphanumerische Zeichen (ohne I, O, Q)
    Beispiel: "WVWZZZ1JZYW123456" oder "VR7EFYHT2PJ 945716" (mit Leerzeichen durch OCR)

    Unterstützte Patterns:
    - "Fg-Nr: WFOJXXGAHJLK14488" (Ford/Fahrzeugidentnummer)
    - "VIN: ..."
    - "Ident-Nr: ..."
    - Freistehendes 17-Zeichen Pattern

    Args:
        text: OCR-Text von Seite 1

    Returns:
        VIN als String oder None
    """
    # Pattern 0: Fg-Nr (Fahrzeugidentnummer - häufig bei Ford)
    # Erlaubt Leerzeichen in VIN und über mehrere Zeilen
    pattern_fg = r'Fg[._\s-]*Nr[.:]?\s*([A-HJ-NPR-Z0-9\s]{17,25})'
    match_fg = re.search(pattern_fg, text, re.IGNORECASE | re.MULTILINE)
    if match_fg:
        vin_raw = match_fg.group(1).strip()
        # Entferne Leerzeichen und Zeilenumbrüche
        vin = re.sub(r'[\s\n]+', '', vin_raw)
        if len(vin) == 17 and not vin.isdigit():
            logger.debug(f"VIN gefunden (Fg-Nr): {vin}")
            return vin
        # Falls zu lang, schneide auf 17 ab und prüfe erneut
        elif len(vin) > 17:
            vin = vin[:17]
            if not vin.isdigit():
                logger.debug(f"VIN gefunden (Fg-Nr, gekürzt): {vin}")
                return vin

    # Pattern 1: VIN ohne Leerzeichen (Standard)
    pattern = r'\b([A-HJ-NPR-Z0-9]{17})\b'

    matches = re.finditer(pattern, text)
    for match in matches:
        vin = match.group(1)

        # Zusätzliche Validierung: VIN sollte nicht nur Zahlen sein
        if not vin.isdigit():
            logger.debug(f"VIN gefunden: {vin}")
            return vin

    # Pattern 2: VIN mit Leerzeichen (OCR-Fehler)
    # Suche nach "VIN" oder "Ident"/"ldent" Label gefolgt von VIN-ähnlichem String
    pattern2 = r'(?:VIN|[Ii1l]dent|Fzg\.?[_\s]*[Ii1l]dent)[\s.:\-Nr]*\n?\s*([A-HJ-NPR-Z0-9\s]{17,25})'
    matches2 = re.finditer(pattern2, text, re.MULTILINE | re.DOTALL)
    for match in matches2:
        vin_raw = match.group(1).strip()
        # Entferne Leerzeichen und Zeilenumbrüche
        vin = re.sub(r'[\s\n]+', '', vin_raw)
        # Prüfe Länge und dass es nicht nur Zahlen ist
        if 17 <= len(vin) <= 20 and not vin.isdigit():
            # Schneide auf 17 Zeichen ab
            vin = vin[:17]
            if len(vin) == 17:
                logger.debug(f"VIN gefunden (mit Leerzeichen): {vin}")
                return vin

    # Pattern 3: VIN irgendwo im Text (breite Suche als letzter Versuch)
    # OCR-tolerant: erlaubt auch I/O/Q (häufige OCR-Fehler)
    # Ohne strict word boundaries wegen OCR-Fehlern
    pattern3 = r'([VWXYZ][A-Z0-9]{16})'
    matches3 = re.finditer(pattern3, text)
    for match in matches3:
        vin = match.group(1)
        # Nicht nur Zahlen, muss Buchstaben enthalten
        if not vin.isdigit() and any(c.isalpha() for c in vin[1:]):
            logger.debug(f"VIN gefunden (V/W/X/Y/Z-Start): {vin}")
            return vin

    logger.debug("Keine VIN gefunden (optional)")
    return None


def detect_formular_version(text: str, has_kunden_nr: bool) -> str:
    """
    Erkennt die Formularversion (neu oder alt).
    
    NEUES FORMULAR (ab ~2024):
    - Hat IMMER "Kd.Nr." oder "Kunden-Nr." Feld → HAUPTMERKMAL
    - Auftragsnummern typisch 1-500 (033519, 033520, etc.)
    - Moderneres Layout mit klarer Struktur
    
    ALTES FORMULAR (bis ~2023):
    - Hat KEINE Kundennummer
    - Hat oft "RO!" (Repair Order) Feld
    - Auftragsnummern typisch 70000+ (75187, 76329, 78708, etc.)
    - Älteres Citroen-Layout
    
    Args:
        text: OCR-Text von Seite 1
        has_kunden_nr: Ob eine Kundennummer gefunden wurde
    
    Returns:
        "neu" wenn Kundennummer vorhanden, sonst "alt"
    """
    # EINDEUTIGE Erkennung: Nur Kundennummer ist entscheidend
    # Neue Formulare haben IMMER eine Kundennummer
    if has_kunden_nr:
        logger.debug("Formularversion: neu (Kundennummer vorhanden)")
        return "neu"
    else:
        logger.debug("Formularversion: alt (keine Kundennummer)")
        return "alt"


def extract_auftragsnummer_from_filename(filename: str) -> Optional[str]:
    """
    Versucht die Auftragsnummer aus dem Dateinamen zu extrahieren.
    
    Unterstützte Formate:
    - "76329_Auftrag.pdf" → "76329"
    - "76329 Auftrag.pdf" → "76329"
    - "Auftrag_76329.pdf" → "76329"
    - "Auftrag 76329 komplett.pdf" → "76329"
    - "test_76329.pdf" → "76329"
    - "076329.pdf" → "076329"
    
    Args:
        filename: Dateiname (mit oder ohne Pfad)
    
    Returns:
        Auftragsnummer oder None
    """
    from pathlib import Path
    
    # Nur Dateiname ohne Pfad
    basename = Path(filename).stem  # Ohne .pdf
    
    # Suche nach 4-6 stelligen Zahlen im Dateinamen
    patterns = [
        r'^(\d{4,6})[\s_]',     # Beginnt mit Zahl: "76329 ..." oder "76329_..."
        r'[\s_](\d{4,6})[\s_]', # Mit Trennzeichen: "Auftrag 76329 komplett"
        r'[\s_](\d{4,6})$',     # Am Ende: "test_76329" oder "Auftrag 76329"
        r'^(\d{4,6})$',         # Nur Zahl: "76329"
        # Wenn alles andere fehlschlägt: Erste 4-6 stellige Zahl
        r'(\d{4,6})',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, basename)
        if match:
            auftrag_nr = match.group(1)
            logger.debug(f"Auftragsnummer aus Dateinamen extrahiert: {auftrag_nr} (Pattern: {pattern})")
            return auftrag_nr
    
    logger.debug(f"Keine Auftragsnummer im Dateinamen gefunden: {filename}")
    return None


def extract_auftrag_metadata(text: str, fallback_filename: Optional[str] = None) -> Dict[str, Any]:
    """
    Extrahiert alle Metadaten aus dem OCR-Text von Seite 1.
    
    Args:
        text: OCR-Text von Seite 1
        fallback_filename: Optionaler Dateiname für Fallback-Extraktion der Auftragsnummer
    
    Returns:
        Dictionary mit Metadaten:
        {
            "auftrag_nr": "076329",
            "kunden_nr": "27129",
            "name": "Sybille Voigt",
            "datum": "2025-11-17",
            "kennzeichen": "B-AB 1234",
            "vin": "WVWZZZ1JZYW123456",
            "formular_version": "neu"
        }
    
    Raises:
        ParserError: Wenn keine Auftragsnummer gefunden wurde
    """
    logger.info("Extrahiere Metadaten aus Seite 1")
    
    # Auftragsnummer ist Pflichtfeld
    auftrag_nr = extract_auftragsnummer(text)
    auftrag_nr_from_ocr = bool(auftrag_nr)  # Merke ob aus OCR-Text
    
    # Fallback: Versuche Extraktion aus Dateinamen
    if not auftrag_nr and fallback_filename:
        logger.warning("Auftragsnummer nicht im OCR-Text gefunden, versuche Dateinamen-Extraktion...")
        auftrag_nr = extract_auftragsnummer_from_filename(fallback_filename)
        if auftrag_nr:
            logger.info(f"✓ Auftragsnummer aus Dateinamen extrahiert: {auftrag_nr}")
    
    if not auftrag_nr:
        raise ParserError("Keine Auftragsnummer gefunden (weder im Text noch im Dateinamen)")
    
    # Optionale Felder
    kunden_nr = extract_kundennummer(text)
    name = extract_name(text)
    datum = extract_datum(text)
    kennzeichen = extract_kennzeichen(text)
    vin = extract_vin(text)
    
    # Formularversion
    formular_version = detect_formular_version(text, has_kunden_nr=(kunden_nr is not None))
    
    metadata = {
        "auftrag_nr": auftrag_nr,
        "auftrag_nr_from_ocr": auftrag_nr_from_ocr,  # Flag ob aus OCR-Text oder Dateinamen
        "kunden_nr": kunden_nr,
        "name": name,
        "datum": datum,
        "kennzeichen": kennzeichen,
        "vin": vin,
        "formular_version": formular_version,
    }
    
    # Log der gefundenen Metadaten
    logger.info(f"Metadaten extrahiert: Auftrag {auftrag_nr}, "
                f"Kunde {name or 'N/A'} (Nr. {kunden_nr or 'N/A'}), "
                f"Version: {formular_version}")
    
    return metadata


def extract_keywords_from_pages(
    page_texts: List[str],
    keywords: List[str],
    start_page: int = 2
) -> Dict[str, List[int]]:
    """
    Sucht nach Schlagwörtern in den Seiten 2-10 (Anhänge).
    
    Die Suche ist case-insensitive und gibt für jedes gefundene Schlagwort
    die Liste der Seitenzahlen zurück, auf denen es vorkommt.
    
    Args:
        page_texts: Liste von OCR-Texten (Index 0 = Seite 1, Index 1 = Seite 2, ...)
        keywords: Liste der zu suchenden Schlagwörter
        start_page: Ab welcher Seite gesucht werden soll (1-basiert, Standard: 2)
    
    Returns:
        Dictionary: {"Garantie": [2, 3], "Kulanz": [2], ...}
        Seitenzahlen sind 1-basiert (Seite 2 = 2, Seite 3 = 3, ...)
    
    Example:
        >>> page_texts = ["Text Seite 1", "Garantie hier", "Garantie und Kulanz"]
        >>> keywords = ["Garantie", "Kulanz"]
        >>> result = extract_keywords_from_pages(page_texts, keywords)
        >>> result
        {'Garantie': [2, 3], 'Kulanz': [3]}
    """
    logger.info(f"Suche nach {len(keywords)} Schlagwörtern in {len(page_texts)} Seiten")
    
    # Start-Index berechnen (0-basiert)
    start_index = start_page - 1
    
    # Nur Seiten ab start_page betrachten
    if len(page_texts) <= start_index:
        logger.warning(f"Nur {len(page_texts)} Seite(n) vorhanden, keine Anhänge für Schlagwortsuche")
        return {}
    
    # Schlagwörter zu Lowercase für case-insensitive Suche
    keyword_map = {kw.lower(): kw for kw in keywords}
    
    # Ergebnisse sammeln
    found_keywords: Dict[str, List[int]] = {}
    
    # Seiten durchsuchen (ab start_index)
    for page_idx in range(start_index, len(page_texts)):
        page_num = page_idx + 1  # 1-basierte Seitenzahl
        text_lower = page_texts[page_idx].lower()
        
        # Jedes Schlagwort prüfen
        for kw_lower, kw_original in keyword_map.items():
            if kw_lower in text_lower:
                if kw_original not in found_keywords:
                    found_keywords[kw_original] = []
                
                # Seitenzahl hinzufügen, wenn noch nicht vorhanden
                if page_num not in found_keywords[kw_original]:
                    found_keywords[kw_original].append(page_num)
    
    # Seitenzahlen sortieren
    for kw in found_keywords:
        found_keywords[kw].sort()
    
    # Log der Ergebnisse
    if found_keywords:
        logger.info(f"Schlagwörter gefunden: {len(found_keywords)}")
        for kw, pages in found_keywords.items():
            logger.debug(f"  - {kw}: Seiten {', '.join(map(str, pages))}")
    else:
        logger.info("Keine Schlagwörter in Anhängen gefunden")
    
    return found_keywords


def format_keywords_for_display(keywords_dict: Dict[str, List[int]]) -> str:
    """
    Formatiert Schlagwörter für die Anzeige.
    
    Args:
        keywords_dict: Dictionary mit Schlagwörtern und Seitenzahlen
    
    Returns:
        Formatierter String, z.B. "Garantie (S. 2,3), Kulanz (S. 2)"
    """
    if not keywords_dict:
        return "Keine"
    
    parts = []
    for kw, pages in sorted(keywords_dict.items()):
        pages_str = ",".join(map(str, pages))
        parts.append(f"{kw} (S. {pages_str})")
    
    return ", ".join(parts)


def parse_pdf_metadata_and_keywords(
    page_texts: List[str],
    keywords: List[str]
) -> Dict[str, Any]:
    """
    Kombinierte Funktion: Extrahiert Metadaten und Schlagwörter aus allen Seiten.
    
    Args:
        page_texts: Liste von OCR-Texten (Index 0 = Seite 1, Index 1 = Seite 2, ...)
        keywords: Liste der zu suchenden Schlagwörter
    
    Returns:
        Dictionary mit Metadaten und Keywords:
        {
            "auftrag_nr": "076329",
            "kunden_nr": "27129",
            ...
            "keywords": {"Garantie": [2, 3], ...}
        }
    
    Raises:
        ParserError: Wenn keine Seiten vorhanden oder Auftragsnummer fehlt
    """
    if not page_texts:
        raise ParserError("Keine Seiten zum Parsen vorhanden")
    
    # Metadaten aus Seite 1 extrahieren
    metadata = extract_auftrag_metadata(page_texts[0])
    
    # Schlagwörter aus Seiten 2-10 extrahieren
    keywords_found = extract_keywords_from_pages(page_texts, keywords, start_page=2)
    metadata["keywords"] = keywords_found
    
    return metadata
