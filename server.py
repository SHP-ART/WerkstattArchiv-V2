#!/usr/bin/env python3
"""
Werkstatt-Archiv Server
Eigenständiger Web-Server für das Werkstatt-Archiv-System
"""

import sys
import logging
from pathlib import Path

# Logging konfigurieren
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger(__name__)

def main():
    """Startet den Werkstatt-Archiv Web-Server"""
    
    logger.info("=" * 60)
    logger.info("Werkstatt-Archiv Server")
    logger.info("=" * 60)
    
    try:
        # Web-App importieren
        logger.info("Lade Web-Anwendung...")
        from web_app import app
        
        # Konfiguration laden
        logger.info("Lade Konfiguration...")
        import config
        import ocr
        
        cfg = config.Config()
        
        # Tesseract und Poppler setup
        tesseract_cmd = cfg.get("tesseract_cmd")
        if tesseract_cmd:
            ocr.setup_tesseract(tesseract_cmd)
        
        poppler_path = cfg.get("poppler_path")
        poppler_bin = ocr.setup_poppler(poppler_path)
        if poppler_bin:
            logger.info(f"Poppler konfiguriert: {poppler_bin}")
        
        # Server-Einstellungen
        host = '0.0.0.0'  # Auf allen Netzwerk-Interfaces
        port = 8080
        
        logger.info("")
        logger.info("=" * 60)
        logger.info(f"Server startet auf http://{host}:{port}")
        logger.info("=" * 60)
        logger.info("")
        logger.info("Zugriff von diesem PC:")
        logger.info(f"  → http://localhost:{port}")
        logger.info(f"  → http://127.0.0.1:{port}")
        logger.info("")
        logger.info("Zugriff aus dem Netzwerk:")
        logger.info(f"  → http://<IP-ADRESSE>:{port}")
        logger.info("")
        logger.info("STRG+C zum Beenden")
        logger.info("=" * 60)
        logger.info("")
        
        # Waitress-Server verwenden (Production-ready)
        try:
            from waitress import serve
            serve(app, host=host, port=port, threads=6)
        except ImportError:
            logger.warning("Waitress nicht installiert, verwende Flask-Dev-Server")
            logger.warning("Für Production: pip install waitress")
            app.run(host=host, port=port, debug=False, threaded=True)
            
    except KeyboardInterrupt:
        logger.info("")
        logger.info("Server gestoppt durch Benutzer")
        sys.exit(0)
        
    except Exception as e:
        logger.error(f"Fehler beim Starten des Servers: {e}", exc_info=True)
        logger.error("")
        logger.error("Mögliche Ursachen:")
        logger.error("  - Port bereits belegt (anderes Programm nutzt Port 8080)")
        logger.error("  - Fehlende Python-Pakete (pip install -r requirements.txt)")
        logger.error("  - Fehlende Konfiguration (.archiv_config.json)")
        logger.error("  - Tesseract/Poppler nicht installiert")
        sys.exit(1)


if __name__ == '__main__':
    main()
