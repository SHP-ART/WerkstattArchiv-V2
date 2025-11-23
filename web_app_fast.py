#!/usr/bin/env python3
"""
Minimale Web-UI für Werkstatt-Archiv (Fast Startup)
Lädt schwere Module nur bei Bedarf (lazy loading)
"""

import logging
import json
from pathlib import Path
from datetime import datetime
from queue import Queue, Empty

from flask import Flask, render_template, request, jsonify

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Flask App
app = Flask(__name__)
app.config['SECRET_KEY'] = 'werkstatt-archiv-secret-key'
app.config['JSON_AS_ASCII'] = False

# Globale State-Variablen
processing_queue = Queue()
watcher_running = False

# Lazy Loading für schwere Module
_config = None
_db = None
_modules_loaded = False


def load_modules():
    """Lazy-Load alle schweren Module"""
    global _config, _db, _modules_loaded
    if not _modules_loaded:
        logger.info("Lade Module...")
        import config
        import db
        _config = config
        _db = db
        _modules_loaded = True
        logger.info("✓ Module geladen")


def get_config():
    """Hole Config (lazy)"""
    load_modules()
    return _config.Config()


@app.route('/')
def index():
    """Hauptseite - Dashboard"""
    return render_template('index.html')


@app.route('/api/stats')
def get_stats():
    """API: Statistiken abrufen"""
    try:
        load_modules()
        c = get_config()
        
        try:
            archiv_root = c.get_archiv_root()
        except ValueError:
            return jsonify({
                'total_auftraege': 0,
                'today_auftraege': 0,
                'watcher_running': watcher_running,
                'config_valid': False
            })
        
        db_path = archiv_root / "werkstatt.db"
        
        if not db_path.exists():
            return jsonify({
                'total_auftraege': 0,
                'today_auftraege': 0,
                'watcher_running': watcher_running,
                'config_valid': False
            })
        
        import sqlite3
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM auftraege')
        total = cursor.fetchone()[0]
        
        today = datetime.now().strftime('%Y-%m-%d')
        cursor.execute('SELECT COUNT(*) FROM auftraege WHERE DATE(created_at) = ?', (today,))
        today_count = cursor.fetchone()[0]
        
        cursor.execute('''
            SELECT auftrag_nr, datum, kunde_name, kennzeichen, created_at 
            FROM auftraege 
            ORDER BY created_at DESC 
            LIMIT 5
        ''')
        recent = [
            {
                'auftrag_nr': row[0],
                'datum': row[1] or 'N/A',
                'kunde_name': row[2] or 'N/A',
                'kennzeichen': row[3] or 'N/A',
                'created_at': row[4]
            }
            for row in cursor.fetchall()
        ]
        
        conn.close()
        
        return jsonify({
            'total_auftraege': total,
            'today_auftraege': today_count,
            'recent_auftraege': recent,
            'watcher_running': watcher_running,
            'config_valid': True
        })
        
    except Exception as e:
        logger.error(f"Fehler: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/processing/status')
def get_processing_status():
    """API: Verarbeitungsstatus"""
    messages = []
    while not processing_queue.empty():
        try:
            msg = processing_queue.get_nowait()
            messages.append(msg)
        except Empty:
            break
    return jsonify({'messages': messages})


@app.route('/settings')
def settings():
    """Einstellungen-Seite"""
    return render_template('settings.html')


@app.route('/search')
def search_page():
    """Suche-Seite"""
    return render_template('search.html')


@app.route('/archive')
def archive_page():
    """Archiv-Seite"""
    return render_template('archive.html')


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Werkstatt-Archiv Web-UI (Fast)')
    parser.add_argument('--host', default='127.0.0.1', help='Host')
    parser.add_argument('--port', type=int, default=8080, help='Port')
    parser.add_argument('--debug', action='store_true', help='Debug-Modus')
    
    args = parser.parse_args()
    
    if args.debug:
        app.config['DEBUG'] = True
    
    logger.info("Starte Werkstatt-Archiv Web-UI (Fast Startup)...")
    logger.info(f"Web-UI: http://{args.host}:{args.port}")
    logger.info("Module werden bei erster Nutzung geladen...")
    
    app.run(host=args.host, port=args.port, debug=args.debug)
