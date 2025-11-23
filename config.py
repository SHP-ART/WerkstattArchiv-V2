"""
Konfigurationsverwaltung für das Werkstatt-Archiv.

Dieses Modul verwaltet alle Konfigurationseinstellungen des Programms,
einschließlich Pfade, OCR-Einstellungen, Schlagwortlisten und Backup-Intervalle.
"""

import json
import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)


# Default-Konfiguration
DEFAULT_CONFIG = {
    "input_folder": "",  # Muss vom Benutzer gesetzt werden
    "archiv_root": "",  # Muss vom Benutzer gesetzt werden
    "db_path": "",  # Wird automatisch auf archiv_root/werkstatt.db gesetzt
    "backup_target_dir": "",  # Optional, muss gesetzt werden wenn Backups gewünscht
    "auftragsnummer_pad_length": 6,
    "use_year_folders": True,  # NEU: Jahr-basierte Ordner (z.B. 2024/076329/)
    "use_thousand_blocks": False,  # ALT: Tausender-Blöcke (z.B. 070000-079999/076329/)
    "dateiname_pattern": "{auftrag_nr}_Auftrag{version_suffix}.pdf",
    "max_pages_to_ocr": 10,
    "auto_backup_interval_hours": 24,
    "kunden_index_file": "kunden_index.csv",
    "tesseract_cmd": None,  # None = auto-detect, oder z.B. r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    "tesseract_lang": "deu",
    
    # Schlagwörter für die Suche in Anhängen (Seiten 2-10)
    "keywords": [
        # Garantie / Kulanz / Rückruf / Rechtliches
        "Garantie",
        "Gewährleistung",
        "Garantieantrag",
        "Garantiefall",
        "Garantieprüfung",
        "Kulanz",
        "Kulanzantrag",
        "Rückruf",
        "Rückrufaktion",
        "Serviceaktion",
        "Technische Maßnahme",
        "Produktverbesserung",
        "Feldmaßnahme",
        "Sachmangel",
        "Mangel",
        "Haftung",
        "Nachbesserung",
        "Nacharbeit",
        "Beanstandung",
        "Reklamation",
        
        # Diagnose / Fehler / Motor / Getriebe / Elektrik
        "Fehlerspeicher",
        "Fehlercode",
        "DTC",
        "Diagnose",
        "Messfahrt",
        "Probefahrt",
        "Fehlerbild",
        "Motorstörung",
        "Motorkontrollleuchte",
        "Abgas",
        "Partikelfilter",
        "DPF",
        "AGR",
        "Ladedruck",
        "Kühlmittel",
        "Überhitzung",
        "Getriebestörung",
        "Automatikgetriebe",
        "Kupplung",
        "ZMS",
        "Antriebswelle",
        "Differenzial",
        "Batterie",
        "Starterbatterie",
        "Lichtmaschine",
        "Ladespannung",
        "Steuergerät",
        "Kabelbaum",
        "Massefehler",
        "Kontaktproblem",
        
        # Bremsen / Fahrwerk / Reifen / Sicherheit
        "Bremse",
        "Bremsbelag",
        "Bremsbeläge",
        "Bremsscheibe",
        "Bremsscheiben",
        "Bremsflüssigkeit",
        "Bremsleitung",
        "ABS",
        "ESP",
        "Stoßdämpfer",
        "Dämpfer",
        "Achslager",
        "Querlenker",
        "Spurstange",
        "Traggelenk",
        "Lenkungsspiel",
        "Reifen",
        "Reifenprofil",
        "Reifenalter",
        "DOT",
        "Unwucht",
        "Hauptuntersuchung",
        "HU",
        "AU",
        "TÜV",
        "Sicherheitsrelevanter Mangel",
        "Verkehrssicherheit",
        "nicht verkehrssicher",
        
        # Service / Wartung / Inspektion
        "Wartung",
        "Inspektion",
        "Service",
        "Serviceintervall",
        "Ölwechsel",
        "Filterwechsel",
        "Luftfilter",
        "Pollenfilter",
        "Kraftstofffilter",
        "Zahnriemen",
        "Keilriemen",
        "Riemenspanner",
        "Klimaanlage",
        "Kältemittel",
        "Klimaservice",
        "Druckprüfung",
        
        # Kosten / Freigabe / Dokumente
        "Kostenvoranschlag",
        "KVA",
        "Freigabe",
        "Kostenübernahme",
        "Angebot",
        "Nachkalkulation",
        "Rechnung",
        "Gutschrift",
        "Arbeitskarte",
        "Checkliste",
        "Prüfprotokoll",
        "Messprotokoll",
        "Fotodokumentation",
    ]
}


class Config:
    """Verwaltung der Konfiguration für das Werkstatt-Archiv."""
    
    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialisiert die Konfiguration.
        
        Args:
            config_path: Pfad zur Konfigurationsdatei. Wenn None, wird versucht,
                        die Datei im Archivordner oder im aktuellen Verzeichnis zu finden.
        """
        self.config_path = config_path
        self.config: Dict[str, Any] = {}
        self._load_config()
    
    def _find_config_file(self) -> Optional[Path]:
        """
        Sucht nach einer vorhandenen Konfigurationsdatei.
        
        Returns:
            Pfad zur Konfigurationsdatei oder None.
        """
        # Mögliche Speicherorte für die Konfiguration
        search_paths = [
            Path(".archiv_config.json"),
            Path(".archiv_config.yaml"),
            Path("config.json"),
            Path("config.yaml"),
        ]
        
        for path in search_paths:
            if path.exists():
                logger.info(f"Konfigurationsdatei gefunden: {path}")
                return path
        
        return None
    
    def _load_config(self) -> None:
        """Lädt die Konfiguration aus einer Datei oder erstellt eine neue."""
        if self.config_path is None:
            self.config_path = self._find_config_file()
        
        if self.config_path and self.config_path.exists():
            # Konfiguration laden
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    if self.config_path.suffix == '.json':
                        self.config = json.load(f)
                    elif self.config_path.suffix in ['.yaml', '.yml']:
                        self.config = yaml.safe_load(f)
                    else:
                        raise ValueError(f"Unbekanntes Konfigurationsformat: {self.config_path.suffix}")
                
                logger.info(f"Konfiguration geladen von: {self.config_path}")
                
                # Fehlende Werte aus Default-Config ergänzen
                for key, value in DEFAULT_CONFIG.items():
                    if key not in self.config:
                        self.config[key] = value
                        logger.info(f"Fehlender Konfigurationswert ergänzt: {key}")
                
            except Exception as e:
                logger.error(f"Fehler beim Laden der Konfiguration: {e}")
                logger.info("Verwende Default-Konfiguration")
                self.config = DEFAULT_CONFIG.copy()
        else:
            # Neue Konfiguration mit Defaults erstellen
            logger.info("Keine Konfigurationsdatei gefunden, erstelle neue Konfiguration")
            self.config = DEFAULT_CONFIG.copy()
            
            # Standard-Pfad für neue Konfiguration
            if self.config_path is None:
                self.config_path = Path(".archiv_config.json")
    
    def save(self) -> None:
        """Speichert die aktuelle Konfiguration."""
        if self.config_path is None:
            self.config_path = Path(".archiv_config.json")
        
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                if self.config_path.suffix == '.json':
                    json.dump(self.config, f, indent=2, ensure_ascii=False)
                elif self.config_path.suffix in ['.yaml', '.yml']:
                    yaml.dump(self.config, f, allow_unicode=True, default_flow_style=False)
            
            logger.info(f"Konfiguration gespeichert nach: {self.config_path}")
        except Exception as e:
            logger.error(f"Fehler beim Speichern der Konfiguration: {e}")
            raise
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Holt einen Konfigurationswert.
        
        Args:
            key: Schlüssel des Konfigurationswerts
            default: Standardwert, falls Schlüssel nicht existiert
        
        Returns:
            Konfigurationswert oder Standardwert
        """
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any, save: bool = True) -> None:
        """
        Setzt einen Konfigurationswert.
        
        Args:
            key: Schlüssel des Konfigurationswerts
            value: Neuer Wert
            save: Ob die Konfiguration sofort gespeichert werden soll
        """
        self.config[key] = value
        logger.info(f"Konfiguration aktualisiert: {key} = {value}")
        
        if save:
            self.save()
    
    def get_input_folder(self) -> Path:
        """Gibt den Eingangsordner zurück."""
        path = self.get("input_folder")
        if not path:
            raise ValueError("input_folder ist nicht konfiguriert. Bitte mit --set-input-folder setzen.")
        return Path(path)
    
    def get_archiv_root(self) -> Path:
        """Gibt den Archivordner zurück."""
        path = self.get("archiv_root")
        if not path:
            raise ValueError("archiv_root ist nicht konfiguriert. Bitte mit --set-archiv-root setzen.")
        return Path(path)
    
    def get_db_path(self) -> Path:
        """Gibt den Datenbank-Pfad zurück."""
        path = self.get("db_path")
        if not path:
            # Standardmäßig im Archivordner
            archiv_root = self.get_archiv_root()
            path = archiv_root / "werkstatt.db"
            self.set("db_path", str(path))
        return Path(path)
    
    def get_backup_target_dir(self) -> Optional[Path]:
        """Gibt den Backup-Zielordner zurück."""
        path = self.get("backup_target_dir")
        return Path(path) if path else None
    
    def get_kunden_index_path(self) -> Path:
        """Gibt den Pfad zur Kunden-Index-Datei zurück."""
        filename = self.get("kunden_index_file", "kunden_index.csv")
        archiv_root = self.get_archiv_root()
        return archiv_root / filename
    
    def get_keywords(self) -> List[str]:
        """Gibt die Liste der Schlagwörter zurück."""
        return self.get("keywords", [])
    
    def validate(self) -> List[str]:
        """
        Validiert die Konfiguration.
        
        Returns:
            Liste von Fehlermeldungen (leer wenn alles OK)
        """
        errors = []
        
        # Pflichtfelder prüfen
        if not self.get("input_folder"):
            errors.append("input_folder ist nicht gesetzt")
        
        if not self.get("archiv_root"):
            errors.append("archiv_root ist nicht gesetzt")
        
        # Pfade prüfen
        try:
            input_folder = self.get_input_folder()
            if not input_folder.exists():
                errors.append(f"Eingangsordner existiert nicht: {input_folder}")
        except ValueError as e:
            errors.append(str(e))
        
        try:
            archiv_root = self.get_archiv_root()
            if not archiv_root.exists():
                logger.warning(f"Archivordner existiert nicht, wird erstellt: {archiv_root}")
                archiv_root.mkdir(parents=True, exist_ok=True)
        except ValueError as e:
            errors.append(str(e))
        
        return errors


def create_default_config(archiv_root: Path) -> Config:
    """
    Erstellt eine neue Konfiguration mit sinnvollen Defaults.
    
    Args:
        archiv_root: Pfad zum Archivordner
    
    Returns:
        Config-Objekt
    """
    config_path = archiv_root / ".archiv_config.json"
    config = Config(config_path)
    
    config.set("archiv_root", str(archiv_root), save=False)
    config.set("db_path", str(archiv_root / "werkstatt.db"), save=False)
    config.save()
    
    logger.info(f"Neue Konfiguration erstellt: {config_path}")
    return config
