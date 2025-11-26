#!/usr/bin/env python3
"""
Web-UI für Werkstatt-Archiv

Bietet eine moderne Browser-Oberfläche mit:
- Dashboard: Live-Verarbeitung und Statistiken
- Einstellungen: Konfiguration von Ordnern
- Suche: Volltext-Suche in Aufträgen
- Archiv: Übersicht aller archivierten Aufträge

Verwendung:
    python3 web_app.py [--port 5000] [--host 0.0.0.0]
"""

import logging

# Logging MUSS vor allen anderen Imports konfiguriert werden!
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

import json
import sqlite3
import threading
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
from queue import Queue, Empty

from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for
from werkzeug.serving import make_server

import config
import db
import parser as auftrag_parser
import ocr
import archive
import watcher

# Flask App
app = Flask(__name__)
app.config['SECRET_KEY'] = 'werkstatt-archiv-secret-key'
app.config['JSON_AS_ASCII'] = False
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 31536000  # 1 Jahr Cache für statische Dateien
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # Max 500MB Upload

# Globale State-Variablen
cfg: Optional[config.Config] = None  # Wird bei Start initialisiert
processing_queue = Queue()
watcher_thread: Optional[threading.Thread] = None
watcher_running = False
server_thread: Optional[threading.Thread] = None

# Cache für API-Responses (vermeidet zu viele DB-Zugriffe)
stats_cache = {'data': None, 'timestamp': 0}
CACHE_DURATION = 5  # Sekunden


def get_config() -> config.Config:
    """Hole oder erstelle Config-Instanz"""
    global cfg
    if cfg is None:
        cfg = config.Config()
    return cfg


# ============================================================
# ROUTES - Dashboard
# ============================================================

@app.route('/')
def index():
    """Hauptseite - Dashboard"""
    return render_template('index.html')


@app.route('/api/stats')
def get_stats():
    """API: Statistiken abrufen (mit Cache)"""
    global stats_cache

    # Cache prüfen
    current_time = time.time()
    if stats_cache['data'] and (current_time - stats_cache['timestamp']) < CACHE_DURATION:
        # Cache noch gültig
        cached_data = stats_cache['data'].copy()
        cached_data['watcher_running'] = watcher_running  # Immer aktuellen Watcher-Status
        return jsonify(cached_data)

    try:
        # Lade Config
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

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Gesamt-Anzahl
        cursor.execute('SELECT COUNT(*) FROM auftraege')
        total = cursor.fetchone()[0]
        
        # Heute verarbeitet
        today = datetime.now().strftime('%Y-%m-%d')
        cursor.execute('SELECT COUNT(*) FROM auftraege WHERE DATE(created_at) = ?', (today,))
        today_count = cursor.fetchone()[0]
        
        # Letzte 5 Aufträge
        cursor.execute('''
            SELECT id, auftrag_nr, datum, kunde_name, kennzeichen, created_at 
            FROM auftraege 
            ORDER BY created_at DESC 
            LIMIT 5
        ''')
        recent = [
            {
                'id': row[0],
                'auftrag_nr': row[1],
                'datum': row[2] or 'N/A',
                'kunde_name': row[3] or 'N/A',
                'kennzeichen': row[4] or 'N/A',
                'created_at': row[5]
            }
            for row in cursor.fetchall()
        ]
        
        conn.close()

        # Daten für Response und Cache vorbereiten
        response_data = {
            'total_auftraege': total,
            'today_auftraege': today_count,
            'recent_auftraege': recent,
            'watcher_running': watcher_running,
            'config_valid': c.validate()
        }

        # Im Cache speichern
        stats_cache['data'] = response_data.copy()
        stats_cache['timestamp'] = time.time()

        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Fehler beim Abrufen der Statistiken: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/processing/status')
def get_processing_status():
    """API: Verarbeitungsstatus abrufen"""
    try:
        # Hole Status aus Queue (non-blocking)
        messages = []
        while not processing_queue.empty():
            try:
                msg = processing_queue.get_nowait()
                messages.append(msg)
            except Empty:
                break
        
        return jsonify({'messages': messages})
        
    except Exception as e:
        logger.error(f"Fehler beim Abrufen des Status: {e}")
        return jsonify({'error': str(e)}), 500


# ============================================================
# ROUTES - Einstellungen
# ============================================================

@app.route('/settings')
def settings_page():
    """Einstellungen-Seite"""
    return render_template('settings.html')

@app.route('/edit')
def edit_page():
    """Daten korrigieren Seite"""
    return render_template('edit.html')

@app.route('/customers')
def customers_page():
    """Kundenliste Seite"""
    return render_template('customers.html')


@app.route('/backup')
def backup_page():
    """Backup & Restore Seite"""
    return render_template('backup.html')


@app.route('/api/settings', methods=['GET'])
def get_settings():
    """API: Aktuelle Einstellungen abrufen"""
    try:
        c = get_config()
        current_config = {
            'input_folder': str(c.get_input_folder() if c.get('input_folder') else ''),
            'archiv_root': str(c.get_archiv_root() if c.get('archiv_root') else ''),
            'backup_target': str(c.get_backup_target_dir() if c.get('backup_target_dir') else ''),
            'tesseract_lang': c.config.get('tesseract_lang', 'deu'),
            'max_pages_to_ocr': c.config.get('max_pages_to_ocr', 10),
            'use_year_folders': c.config.get('use_year_folders', False),
            'use_thousand_blocks': c.config.get('use_thousand_blocks', False),
        }
        return jsonify(current_config)
        
    except Exception as e:
        logger.error(f"Fehler beim Laden der Einstellungen: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/settings', methods=['POST'])
def update_settings():
    """API: Einstellungen aktualisieren"""
    try:
        c = get_config()
        data = request.get_json()
        
        # Update Config
        if 'input_folder' in data and data['input_folder']:
            c.set('input_folder', str(Path(data['input_folder'])), save=False)
        
        if 'archiv_root' in data and data['archiv_root']:
            c.set('archiv_root', str(Path(data['archiv_root'])), save=False)
        
        if 'backup_target' in data and data['backup_target']:
            c.set('backup_target_dir', str(Path(data['backup_target'])), save=False)
        
        # Weitere Einstellungen
        if 'tesseract_lang' in data:
            c.config['tesseract_lang'] = data['tesseract_lang']
        
        if 'max_pages_to_ocr' in data:
            c.config['max_pages_to_ocr'] = int(data['max_pages_to_ocr'])
        
        # Ordner-Struktur Änderungen: Validierung
        structure_changed = False
        if 'use_year_folders' in data and data['use_year_folders'] != c.config.get('use_year_folders', False):
            structure_changed = True
        if 'use_thousand_blocks' in data and data['use_thousand_blocks'] != c.config.get('use_thousand_blocks', False):
            structure_changed = True
        
        # Prüfe ob Archiv leer ist bei Struktur-Änderung
        if structure_changed:
            archiv_root = c.get_archiv_root()
            if archiv_root and archiv_root.exists():
                # Zähle PDF-Dateien im Archiv (rekursiv)
                pdf_count = len(list(archiv_root.rglob('*.pdf')))
                if pdf_count > 0:
                    return jsonify({
                        'success': False, 
                        'error': f'Ordner-Struktur kann nicht geändert werden: Archiv enthält bereits {pdf_count} PDF-Datei(en). Bitte leere das Archiv oder erstelle ein neues Archiv-Verzeichnis.'
                    }), 400
        
        if 'use_year_folders' in data:
            c.config['use_year_folders'] = bool(data['use_year_folders'])
        
        if 'use_thousand_blocks' in data:
            c.config['use_thousand_blocks'] = bool(data['use_thousand_blocks'])
        
        # Speichern
        c.save()
        
        # Initialisiere Datenbank
        db_path = c.get_archiv_root() / "werkstatt.db"
        db.init_db(db_path)
        
        return jsonify({'success': True, 'message': 'Einstellungen gespeichert'})
        
    except Exception as e:
        logger.error(f"Fehler beim Speichern der Einstellungen: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/settings/validate', methods=['POST'])
def validate_settings():
    """API: Ordnerpfade validieren"""
    try:
        data = request.get_json()
        path = Path(data.get('path', ''))
        
        result = {
            'exists': path.exists(),
            'is_dir': path.is_dir() if path.exists() else False,
            'writable': False,
            'readable': False
        }
        
        if result['is_dir']:
            # Test Schreibberechtigung
            try:
                test_file = path / '.test_write'
                test_file.touch()
                test_file.unlink()
                result['writable'] = True
            except:
                pass
            
            # Test Leseberechtigung
            try:
                list(path.iterdir())
                result['readable'] = True
            except:
                pass
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/api/system-info', methods=['GET'])
def get_system_info():
    """API: System-Informationen abrufen"""
    try:
        import sys
        import subprocess
        
        # Python-Version
        python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        
        # Tesseract-Version
        tesseract_version = "Nicht installiert"
        try:
            result = subprocess.run(['tesseract', '--version'], 
                                    capture_output=True, text=True, timeout=2)
            if result.returncode == 0:
                # Extrahiere Version aus erster Zeile (z.B. "tesseract 5.3.0")
                first_line = result.stdout.split('\n')[0]
                tesseract_version = first_line.strip()
        except:
            pass
        
        return jsonify({
            'python_version': python_version,
            'tesseract_version': tesseract_version
        })
        
    except Exception as e:
        logger.error(f"Fehler beim Abrufen der System-Info: {e}")
        return jsonify({'error': str(e)}), 500


# ============================================================
# ROUTES - Suche
# ============================================================

@app.route('/search')
def search_page():
    """Suche-Seite"""
    return render_template('search.html')


@app.route('/api/search', methods=['POST'])
def search():
    """API: Suche durchführen"""
    try:
        data = request.get_json()
        search_type = data.get('type', 'auftrag')
        query = data.get('query', '').strip()
        
        if not query:
            return jsonify({'results': []})
        
        c = get_config()
        db_path = c.get_archiv_root() / "werkstatt.db"
        
        if not db_path.exists():
            return jsonify({'results': [], 'error': 'Datenbank nicht gefunden'})
        
        results = []
        sort_order = data.get('sort', 'datum_desc')
        
        if search_type == 'auftrag':
            results = db.search_by_auftrag_nr(db_path, query)
        elif search_type == 'kunde':
            results = db.search_by_kunde(db_path, query)
        elif search_type == 'kennzeichen':
            results = db.search_by_kennzeichen(db_path, query)
        elif search_type == 'vin':
            # VIN-Suche (komplette VIN)
            results = db.search_by_vin(db_path, query)
        elif search_type == 'vis':
            # VIS-Suche (letzte 6 Zeichen der VIN)
            results = db.search_by_vis(db_path, query)
        elif search_type == 'keyword':
            results = db.search_by_keyword(db_path, query)
        elif search_type == 'datum':
            results = db.search_by_date_range(db_path, query, query)
        elif search_type == 'monat':
            # Monat-Suche (z.B. "2024-07")
            results = db.search_by_month(db_path, query)
        elif search_type == 'jahr':
            # Jahr-Suche (z.B. "2024")
            results = db.search_by_year(db_path, query)
        
        # Formatiere Ergebnisse
        formatted_results = []
        for row in results:
            # Parse keywords_json
            keywords = {}
            if row.get('keywords_json'):
                try:
                    keywords = json.loads(row['keywords_json'])
                except:
                    pass
            
            formatted_results.append({
                'id': row.get('id'),
                'auftrag_nr': row.get('auftrag_nr'),
                'kunden_nr': row.get('kunden_nr'),
                'kunde_name': row.get('kunde_name'),
                'datum': row.get('datum'),
                'kennzeichen': row.get('kennzeichen'),
                'vin': row.get('vin'),
                'file_path': row.get('file_path'),
                'keywords': keywords,
                'created_at': row.get('created_at')
            })
        
        # Sortierung anwenden
        if sort_order == 'datum_desc':
            formatted_results.sort(key=lambda x: x.get('datum') or '', reverse=True)
        elif sort_order == 'datum_asc':
            formatted_results.sort(key=lambda x: x.get('datum') or '')
        elif sort_order == 'auftrag_desc':
            formatted_results.sort(key=lambda x: x.get('auftrag_nr') or '', reverse=True)
        elif sort_order == 'auftrag_asc':
            formatted_results.sort(key=lambda x: x.get('auftrag_nr') or '')
        
        return jsonify({'results': formatted_results, 'count': len(formatted_results)})
    
    except Exception as e:
        logger.error(f"Fehler bei der Suche: {e}")
        return jsonify({'results': [], 'error': str(e)}), 500


@app.route('/api/search/multi', methods=['POST'])
def api_search_multi():
    """Multi-Kriterien-Suche (UND-Verknüpfung)"""
    try:
        data = request.get_json()
        criteria = data.get('criteria', {})
        sort_order = data.get('sort', 'datum_desc')
        
        # Filtere leere Werte
        filtered_criteria = {k: v for k, v in criteria.items() if v and str(v).strip()}
        
        if not filtered_criteria:
            return jsonify({'results': [], 'count': 0})
        
        c = get_config()
        db_path = c.get_archiv_root() / "werkstatt.db"
        
        if not db_path.exists():
            return jsonify({'results': [], 'error': 'Datenbank nicht gefunden'})
        
        results = db.search_multi_criteria(db_path, filtered_criteria)
        
        # Formatiere Ergebnisse
        formatted_results = []
        for row in results:
            keywords = {}
            if row.get('keywords_json'):
                try:
                    keywords = json.loads(row['keywords_json'])
                except:
                    pass
            
            formatted_results.append({
                'id': row.get('id'),
                'auftrag_nr': row.get('auftrag_nr'),
                'kunden_nr': row.get('kunden_nr'),
                'kunde_name': row.get('kunde_name'),
                'datum': row.get('datum'),
                'kennzeichen': row.get('kennzeichen'),
                'vin': row.get('vin'),
                'file_path': row.get('file_path'),
                'keywords': keywords,
                'created_at': row.get('created_at')
            })
        
        # Sortierung anwenden
        if sort_order == 'datum_desc':
            formatted_results.sort(key=lambda x: x.get('datum') or '', reverse=True)
        elif sort_order == 'datum_asc':
            formatted_results.sort(key=lambda x: x.get('datum') or '')
        elif sort_order == 'auftrag_desc':
            formatted_results.sort(key=lambda x: x.get('auftrag_nr') or '', reverse=True)
        elif sort_order == 'auftrag_asc':
            formatted_results.sort(key=lambda x: x.get('auftrag_nr') or '')
        
        return jsonify({'results': formatted_results, 'count': len(formatted_results)})
        
    except Exception as e:
        logger.error(f"Fehler bei der Suche: {e}")
        return jsonify({'error': str(e)}), 500


# ============================================================
# ROUTES - Archiv
# ============================================================

@app.route('/archive')
def archive_page():
    """Archiv-Übersicht"""
    return render_template('archive.html')


@app.route('/api/archive/list')
def list_archive():
    """API: Liste aller Aufträge"""
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 50))
        offset = (page - 1) * per_page
        
        c = get_config()
        db_path = c.get_archiv_root() / "werkstatt.db"
        
        if not db_path.exists():
            return jsonify({'results': [], 'total': 0, 'page': page, 'per_page': per_page})
        
        import sqlite3
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Gesamt-Anzahl
        cursor.execute('SELECT COUNT(*) FROM auftraege')
        total = cursor.fetchone()[0]
        
        # Paginierte Ergebnisse
        cursor.execute('''
            SELECT * FROM auftraege 
            ORDER BY created_at DESC 
            LIMIT ? OFFSET ?
        ''', (per_page, offset))
        
        results = []
        for row in cursor.fetchall():
            keywords = {}
            if row['keywords_json']:
                try:
                    keywords = json.loads(row['keywords_json'])
                except:
                    pass
            
            results.append({
                'id': row['id'],
                'auftrag_nr': row['auftrag_nr'],
                'kunden_nr': row['kunden_nr'],
                'kunde_name': row['kunde_name'],
                'datum': row['datum'],
                'kennzeichen': row['kennzeichen'],
                'vin': row['vin'],
                'file_path': row['file_path'],
                'keywords': keywords,
                'created_at': row['created_at']
            })
        
        conn.close()
        
        return jsonify({
            'results': results,
            'total': total,
            'page': page,
            'per_page': per_page,
            'total_pages': (total + per_page - 1) // per_page
        })
        
    except Exception as e:
        logger.error(f"Fehler beim Laden des Archivs: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/archive/view/<int:auftrag_id>')
def view_pdf(auftrag_id):
    """API: PDF im Browser anzeigen"""
    try:
        c = get_config()
        db_path = c.get_archiv_root() / "werkstatt.db"
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT file_path FROM auftraege WHERE id = ?', (auftrag_id,))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return jsonify({'error': 'Auftrag nicht gefunden'}), 404
        
        file_path = Path(row[0])
        
        if not file_path.exists():
            logger.error(f"PDF nicht gefunden: {file_path}")
            return jsonify({'error': 'Datei nicht gefunden'}), 404
        
        logger.info(f"Sende PDF: {file_path}")
        response = send_file(
            file_path,
            mimetype='application/pdf',
            as_attachment=False
        )
        # Header für iframe-Embedding
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['Content-Disposition'] = 'inline'
        return response
        
    except Exception as e:
        logger.error(f"Fehler beim Anzeigen von Auftrag {auftrag_id}: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/archive/download/<int:auftrag_id>')
def download_pdf(auftrag_id):
    """API: PDF herunterladen"""
    try:
        c = get_config()
        db_path = c.get_archiv_root() / "werkstatt.db"
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT file_path, auftrag_nr FROM auftraege WHERE id = ?', (auftrag_id,))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return jsonify({'error': 'Auftrag nicht gefunden'}), 404
        
        file_path = Path(row[0])
        auftrag_nr = row[1]
        
        if not file_path.exists():
            return jsonify({'error': 'Datei nicht gefunden'}), 404
        
        return send_file(
            file_path,
            as_attachment=True,
            download_name=f"{auftrag_nr}_Auftrag.pdf"
        )
        
    except Exception as e:
        logger.error(f"Fehler beim Download: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/archive/reveal/<int:auftrag_id>')
def reveal_in_finder(auftrag_id):
    """API: Datei im Finder/Explorer zeigen"""
    import subprocess
    import platform
    
    try:
        c = get_config()
        db_path = c.get_db_path()  # Verwende config.get_db_path() statt manuell
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT file_path FROM auftraege WHERE id = ?', (auftrag_id,))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return jsonify({'success': False, 'error': 'Auftrag nicht gefunden'}), 404
        
        file_path = Path(row[0])
        
        if not file_path.exists():
            return jsonify({'success': False, 'error': 'Datei nicht gefunden'}), 404
        
        # Öffne Finder/Explorer mit ausgewählter Datei
        system = platform.system()
        
        if system == 'Darwin':  # macOS
            result = subprocess.run(['open', '-R', str(file_path)], capture_output=True, text=True)
            if result.returncode != 0:
                logger.error(f"Finder-Fehler: {result.stderr}")
                return jsonify({'success': False, 'error': f'Fehler beim Öffnen: {result.stderr}'}), 500
            logger.info(f"Finder geöffnet für: {file_path}")
        elif system == 'Windows':
            result = subprocess.run(['explorer', '/select,', str(file_path)], capture_output=True, text=True)
            if result.returncode != 0:
                logger.error(f"Explorer-Fehler: {result.stderr}")
                return jsonify({'success': False, 'error': f'Fehler beim Öffnen: {result.stderr}'}), 500
            logger.info(f"Explorer geöffnet für: {file_path}")
        elif system == 'Linux':
            # Versuche verschiedene Dateimanager
            try:
                result = subprocess.run(['nautilus', '--select', str(file_path)], capture_output=True, text=True)
                if result.returncode != 0:
                    raise FileNotFoundError()
            except FileNotFoundError:
                try:
                    result = subprocess.run(['dolphin', '--select', str(file_path)], capture_output=True, text=True)
                    if result.returncode != 0:
                        raise FileNotFoundError()
                except FileNotFoundError:
                    # Fallback: Öffne nur den Ordner
                    result = subprocess.run(['xdg-open', str(file_path.parent)], capture_output=True, text=True)
                    if result.returncode != 0:
                        return jsonify({'success': False, 'error': 'Kein Dateimanager gefunden'}), 500
            logger.info(f"Dateimanager geöffnet für: {file_path}")
        else:
            return jsonify({'success': False, 'error': f'Betriebssystem {system} nicht unterstützt'}), 400
        
        return jsonify({'success': True, 'message': 'Datei im Finder/Explorer angezeigt'})
        
    except Exception as e:
        logger.error(f"Fehler beim Öffnen im Finder: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/folder/open-input')
def open_input_folder():
    """API: Eingangsordner im Finder/Explorer öffnen"""
    import subprocess
    import platform
    
    try:
        c = get_config()
        input_folder = c.get_input_folder()
        
        if not input_folder.exists():
            return jsonify({'success': False, 'error': 'Eingangsordner nicht gefunden'}), 404
        
        # Öffne Finder/Explorer
        system = platform.system()
        
        if system == 'Darwin':  # macOS
            result = subprocess.run(['open', str(input_folder)], capture_output=True, text=True)
            if result.returncode != 0:
                logger.error(f"Finder-Fehler: {result.stderr}")
                return jsonify({'success': False, 'error': f'Fehler beim Öffnen: {result.stderr}'}), 500
            logger.info(f"Finder geöffnet: {input_folder}")
        elif system == 'Windows':
            result = subprocess.run(['explorer', str(input_folder)], capture_output=True, text=True)
            if result.returncode != 0:
                logger.error(f"Explorer-Fehler: {result.stderr}")
                return jsonify({'success': False, 'error': f'Fehler beim Öffnen: {result.stderr}'}), 500
            logger.info(f"Explorer geöffnet: {input_folder}")
        elif system == 'Linux':
            try:
                result = subprocess.run(['xdg-open', str(input_folder)], capture_output=True, text=True)
                if result.returncode != 0:
                    raise FileNotFoundError()
            except FileNotFoundError:
                try:
                    result = subprocess.run(['nautilus', str(input_folder)], capture_output=True, text=True)
                    if result.returncode != 0:
                        raise FileNotFoundError()
                except FileNotFoundError:
                    result = subprocess.run(['dolphin', str(input_folder)], capture_output=True, text=True)
                    if result.returncode != 0:
                        return jsonify({'success': False, 'error': 'Kein Dateimanager gefunden'}), 500
            logger.info(f"Dateimanager geöffnet: {input_folder}")
        else:
            return jsonify({'success': False, 'error': f'Betriebssystem {system} nicht unterstützt'}), 400
        
        return jsonify({
            'success': True,
            'message': 'Eingangsordner geöffnet',
            'path': str(input_folder)
        })
        
    except Exception as e:
        logger.error(f"Fehler beim Öffnen des Eingangsordners: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/archive/detail/<int:auftrag_id>')
def get_auftrag_detail(auftrag_id):
    """API: Detaillierte Informationen zu einem Auftrag"""
    try:
        c = get_config()
        db_path = c.get_archiv_root() / "werkstatt.db"
        import sqlite3
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM auftraege WHERE id = ?', (auftrag_id,))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return jsonify({'error': 'Auftrag nicht gefunden'}), 404
        
        return jsonify(dict(row))
        
    except Exception as e:
        logger.error(f"Fehler beim Abrufen der Details: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/archive/update', methods=['POST'])
def update_auftrag():
    """API: Auftragsdaten aktualisieren (mit optionaler Auftragsnummer-Änderung)"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'Keine JSON-Daten'}), 400
        
        auftrag_id = data.get('id')
        neue_auftrag_nr = data.get('auftrag_nr')
        
        if not auftrag_id:
            return jsonify({'success': False, 'error': 'ID fehlt'}), 400
        
        c = get_config()
        db_path = c.get_db_path()
        
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Alte Daten laden
        cursor.execute('SELECT * FROM auftraege WHERE id = ?', (auftrag_id,))
        row = cursor.fetchone()
        
        if not row:
            conn.close()
            return jsonify({'success': False, 'error': 'Auftrag nicht gefunden'}), 404
        
        alte_auftrag_nr = row['auftrag_nr']
        alte_datei = Path(row['file_path'])
        
        # Prüfe ob Auftragsnummer geändert wurde
        if neue_auftrag_nr and neue_auftrag_nr != alte_auftrag_nr:
            logger.info(f"Auftragsnummer-Änderung: {alte_auftrag_nr} → {neue_auftrag_nr}")
            
            # Import für Archiv-Operationen
            from archive import format_auftrag_nr, get_thousand_block
            import shutil
            
            # Normalisiere neue Nummer
            neue_auftrag_nr_formatted = format_auftrag_nr(neue_auftrag_nr)
            
            # Berechne neue Pfade
            archiv_root = c.get_archiv_root()
            use_thousand_blocks = c.config.get('use_thousand_blocks', False)
            use_year_folders = c.config.get('use_year_folders', True)
            
            if use_year_folders and row['datum']:
                jahr = row['datum'][:4]  # YYYY-MM-DD → YYYY
            else:
                jahr = None
            
            if use_thousand_blocks:
                block = get_thousand_block(neue_auftrag_nr_formatted)
                if jahr:
                    neuer_ordner = archiv_root / jahr / block / neue_auftrag_nr_formatted
                else:
                    neuer_ordner = archiv_root / block / neue_auftrag_nr_formatted
            else:
                if jahr:
                    neuer_ordner = archiv_root / jahr / neue_auftrag_nr_formatted
                else:
                    neuer_ordner = archiv_root / neue_auftrag_nr_formatted
            
            # Neuer Dateiname
            alter_filename = alte_datei.name
            neuer_filename = alter_filename.replace(alte_auftrag_nr, neue_auftrag_nr_formatted, 1)
            neue_datei = neuer_ordner / neuer_filename
            
            # Archiv aktualisieren
            if alte_datei.exists():
                neuer_ordner.mkdir(parents=True, exist_ok=True)
                shutil.move(str(alte_datei), str(neue_datei))
                logger.info(f"✓ Datei verschoben: {neue_datei.name}")
                
                # Metadaten verschieben
                alter_ordner = alte_datei.parent
                for meta_file in ['data.csv', 'meta.json']:
                    alte_meta = alter_ordner / meta_file
                    if alte_meta.exists():
                        neue_meta = neuer_ordner / meta_file
                        shutil.move(str(alte_meta), str(neue_meta))
                
                # Alten Ordner löschen (falls leer)
                try:
                    if not any(alter_ordner.iterdir()):
                        alter_ordner.rmdir()
                except:
                    pass
            else:
                logger.warning(f"Datei existiert nicht: {alte_datei}")
                neue_datei = neue_datei  # Nutze neuen Pfad trotzdem
            
            # Datenbank aktualisieren (inkl. neuer Auftragsnummer und Pfad)
            cursor.execute('''
                UPDATE auftraege 
                SET auftrag_nr = ?,
                    kunden_nr = ?,
                    kunde_name = ?,
                    datum = ?,
                    kennzeichen = ?,
                    vin = ?,
                    file_path = ?
                WHERE id = ?
            ''', (
                neue_auftrag_nr_formatted,
                data.get('kunden_nr'),
                data.get('kunde_name'),
                data.get('datum'),
                data.get('kennzeichen'),
                data.get('vin'),
                str(neue_datei),
                auftrag_id
            ))
            
            logger.info(f"✓ Auftrag aktualisiert: {alte_auftrag_nr} → {neue_auftrag_nr_formatted}")
        else:
            # Normale Aktualisierung ohne Auftragsnummer-Änderung
            cursor.execute('''
                UPDATE auftraege 
                SET kunden_nr = ?,
                    kunde_name = ?,
                    datum = ?,
                    kennzeichen = ?,
                    vin = ?
                WHERE id = ?
            ''', (
                data.get('kunden_nr'),
                data.get('kunde_name'),
                data.get('datum'),
                data.get('kennzeichen'),
                data.get('vin'),
                auftrag_id
            ))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True})
        
    except Exception as e:
        logger.error(f"Fehler beim Aktualisieren: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/archive/incomplete')
def get_incomplete_auftraege():
    """API: Aufträge mit fehlenden Daten"""
    try:
        c = get_config()
        db_path = c.get_archiv_root() / "werkstatt.db"
        
        import sqlite3
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Prüfe ob data_complete Spalte existiert
        cursor.execute("PRAGMA table_info(auftraege)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'data_complete' not in columns:
            # Füge Spalte hinzu wenn sie fehlt
            cursor.execute('ALTER TABLE auftraege ADD COLUMN data_complete INTEGER DEFAULT 0')
            conn.commit()
        
        # Suche Aufträge wo wichtige Felder fehlen oder N/A sind UND nicht als vollständig markiert
        cursor.execute('''
            SELECT * FROM auftraege 
            WHERE (data_complete IS NULL OR data_complete = 0)
              AND (kunde_name IS NULL 
                   OR kunde_name = 'N/A'
                   OR kennzeichen IS NULL 
                   OR kennzeichen = 'N/A'
                   OR vin IS NULL
                   OR datum IS NULL
                   OR kunden_nr IS NULL)
            ORDER BY created_at DESC
            LIMIT 50
        ''')
        
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return jsonify({'results': results, 'count': len(results)})
        
    except Exception as e:
        logger.error(f"Fehler beim Abrufen unvollständiger Aufträge: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/archive/suggest-data/<int:auftrag_id>')
def suggest_data(auftrag_id):
    """API: Schlägt fehlende Daten vor basierend auf historischen Aufträgen"""
    try:
        c = get_config()
        db_path = c.get_archiv_root() / "werkstatt.db"
        
        # Lade aktuellen Auftrag
        import sqlite3
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM auftraege WHERE id = ?', (auftrag_id,))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return jsonify({'error': 'Auftrag nicht gefunden'}), 404
        
        auftrag_data = dict(row)
        
        # Suche Vorschläge
        suggestions = db.suggest_missing_data(db_path, auftrag_data)
        
        return jsonify(suggestions)

    except Exception as e:
        logger.error(f"Fehler bei Daten-Vorschlägen: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/archive/rescan-pdf/<int:auftrag_id>', methods=['POST'])
def rescan_pdf(auftrag_id):
    """API: PDF neu scannen (OCR) und Vorschläge für Datenverbesserung zurückgeben"""
    try:
        c = get_config()
        db_path = c.get_archiv_root() / "werkstatt.db"

        # Lade aktuellen Auftrag
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM auftraege WHERE id = ?', (auftrag_id,))
        row = cursor.fetchone()
        conn.close()

        if not row:
            return jsonify({'error': 'Auftrag nicht gefunden'}), 404

        current_data = dict(row)
        pdf_path = Path(current_data['file_path'])

        if not pdf_path.exists():
            return jsonify({'error': 'PDF-Datei nicht gefunden'}), 404

        # PDF neu scannen (OCR)
        logger.info(f"Scanne PDF neu: {pdf_path.name} (Auftrag {auftrag_id})")
        texts = ocr.pdf_to_ocr_texts(pdf_path, max_pages=1, dpi=300)

        # Metadaten neu extrahieren
        new_metadata = auftrag_parser.extract_auftrag_metadata(texts[0], fallback_filename=pdf_path.name)

        # Vergleiche alte und neue Daten und erstelle Vorschläge
        suggestions = {}
        changes = []

        # Felder zum Vergleichen
        fields_to_check = {
            'kunden_nr': 'Kundennummer',
            'name': 'Kundenname',
            'datum': 'Datum',
            'kennzeichen': 'Kennzeichen',
            'vin': 'VIN'
        }

        for field_key, field_label in fields_to_check.items():
            current_value = current_data.get(field_key) or current_data.get(f'kunde_{field_key}' if field_key == 'name' else field_key)
            new_value = new_metadata.get(field_key)

            # Nur vorschlagen wenn:
            # 1. Neuer Wert existiert UND
            # 2. Alter Wert fehlt ODER anders ist
            if new_value and (not current_value or current_value != new_value):
                suggestions[field_key] = {
                    'label': field_label,
                    'current': current_value or '',
                    'suggested': new_value,
                    'changed': bool(current_value)  # True = Änderung, False = Ergänzung
                }
                changes.append(field_label)

        logger.info(f"Rescan abgeschlossen: {len(suggestions)} Vorschläge gefunden")

        return jsonify({
            'success': True,
            'has_suggestions': len(suggestions) > 0,
            'suggestions': suggestions,
            'changes': changes,
            'message': f'{len(suggestions)} Verbesserungsvorschläge gefunden' if suggestions else 'Keine Verbesserungen gefunden'
        })

    except Exception as e:
        logger.error(f"Fehler beim PDF Rescan: {e}", exc_info=True)
        return jsonify({'error': f'Fehler beim Scannen: {str(e)}'}), 500


@app.route('/api/customers/list')
def customers_list():
    """API: Kundenliste mit Fahrzeugen"""
    try:
        c = get_config()
        db_path = c.get_archiv_root() / "werkstatt.db"
        
        import sqlite3
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Gruppiere nach Kunde + Fahrzeug (kennzeichen/vin Kombination)
        cursor.execute('''
            SELECT 
                kunde_name,
                kunden_nr,
                kennzeichen,
                vin,
                COUNT(*) as auftraege_count,
                MAX(auftrag_nr) as last_auftrag,
                MAX(datum) as last_date
            FROM auftraege
            WHERE kunde_name IS NOT NULL 
              AND kunde_name != '' 
              AND kunde_name != 'N/A'
            GROUP BY kunde_name, kennzeichen, vin
            ORDER BY kunde_name, kennzeichen
        ''')
        
        customers = [dict(row) for row in cursor.fetchall()]
        
        # Statistiken
        cursor.execute('SELECT COUNT(DISTINCT kunde_name) FROM auftraege WHERE kunde_name IS NOT NULL AND kunde_name != "" AND kunde_name != "N/A"')
        total_customers = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(DISTINCT kennzeichen) FROM auftraege WHERE kennzeichen IS NOT NULL AND kennzeichen != "" AND kennzeichen != "N/A"')
        total_vehicles = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM auftraege')
        total_auftraege = cursor.fetchone()[0]
        
        conn.close()
        
        return jsonify({
            'customers': customers,
            'total_customers': total_customers,
            'total_vehicles': total_vehicles,
            'total_auftraege': total_auftraege
        })
        
    except Exception as e:
        logger.error(f"Fehler beim Laden der Kundenliste: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/customers/update', methods=['POST'])
def update_customer():
    """API: Kundendaten aktualisieren"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'Keine JSON-Daten'}), 400

        # Alte Werte
        old_kunde_name = data.get('old_kunde_name', '')
        old_kunden_nr = data.get('old_kunden_nr', '')
        old_kennzeichen = data.get('old_kennzeichen', '')
        old_vin = data.get('old_vin', '')

        # Neue Werte
        new_kunde_name = data.get('new_kunde_name', '')
        new_kunden_nr = data.get('new_kunden_nr', '')
        new_kennzeichen = data.get('new_kennzeichen', '')
        new_vin = data.get('new_vin', '')

        if not new_kunde_name:
            return jsonify({'success': False, 'error': 'Kundenname darf nicht leer sein'}), 400

        c = get_config()
        db_path = c.get_archiv_root() / "werkstatt.db"

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Baue WHERE-Klausel basierend auf alten Werten
        where_conditions = []
        params = []

        if old_kunde_name:
            where_conditions.append("kunde_name = ?")
            params.append(old_kunde_name)

        if old_kunden_nr:
            where_conditions.append("(kunden_nr = ? OR kunden_nr IS NULL)")
            params.append(old_kunden_nr)

        if old_kennzeichen:
            where_conditions.append("(kennzeichen = ? OR kennzeichen IS NULL)")
            params.append(old_kennzeichen)

        if old_vin:
            where_conditions.append("(vin = ? OR vin IS NULL)")
            params.append(old_vin)

        where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"

        # Update durchführen
        update_query = f"""
            UPDATE auftraege
            SET kunde_name = ?,
                kunden_nr = ?,
                kennzeichen = ?,
                vin = ?,
                updated_at = datetime('now')
            WHERE {where_clause}
        """

        update_params = [new_kunde_name, new_kunden_nr, new_kennzeichen, new_vin] + params

        cursor.execute(update_query, update_params)
        updated_count = cursor.rowcount

        conn.commit()
        conn.close()

        logger.info(f"Kundendaten aktualisiert: {old_kunde_name} -> {new_kunde_name} ({updated_count} Aufträge)")

        return jsonify({
            'success': True,
            'message': 'Kundendaten erfolgreich aktualisiert',
            'updated_count': updated_count
        })

    except Exception as e:
        logger.error(f"Fehler beim Aktualisieren der Kundendaten: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/archive/mark-complete', methods=['POST'])
def mark_complete():
    """API: Auftrag als vollständig markieren"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'Keine JSON-Daten'}), 400
        
        auftrag_id = data.get('id')

        if not auftrag_id:
            return jsonify({'success': False, 'error': 'ID fehlt'}), 400

        c = get_config()
        db_path = c.get_archiv_root() / "werkstatt.db"

        success = db.mark_auftrag_complete(db_path, auftrag_id)

        if success:
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Auftrag nicht gefunden'}), 404

    except Exception as e:
        logger.error(f"Fehler beim Markieren: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================
# ROUTES - Scan & Verarbeitung
# ============================================================

@app.route('/api/scan/manual', methods=['POST'])
def manual_scan():
    """API: Eingangsordner manuell scannen und verarbeiten"""
    try:
        c = get_config()

        # Validiere Konfiguration
        errors = c.validate()
        if errors:
            return jsonify({
                'success': False,
                'error': 'Konfiguration ungültig: ' + ', '.join(errors)
            }), 400

        input_folder = c.get_input_folder()
        archiv_root = c.get_archiv_root()
        db_path = c.get_db_path()

        # Prüfe ob Ordner existiert
        if not input_folder.exists():
            return jsonify({
                'success': False,
                'error': f'Eingangsordner nicht gefunden: {input_folder}'
            }), 404

        # Scanne nach PDFs (nur direkte Kinder, keine Unterordner)
        pdf_files = list(input_folder.glob('*.pdf'))
        
        # Prüfe auch ob es Unterordner mit PDFs gibt
        folder_count = 0
        for item in input_folder.iterdir():
            if item.is_dir() and not item.name.startswith('.') and item.name not in ['Fehler', 'temp_backup', '.trash']:
                if list(item.glob('*.pdf')):
                    folder_count += 1

        if not pdf_files and folder_count > 0:
            return jsonify({
                'success': False,
                'processed': 0,
                'success_count': 0,
                'error_count': 0,
                'message': f'Keine einzelnen PDFs gefunden. Es gibt {folder_count} Ordner mit PDFs - bitte den "Ordner importieren" Button verwenden!'
            }), 400
        
        if not pdf_files:
            return jsonify({
                'success': True,
                'processed': 0,
                'success_count': 0,
                'error_count': 0,
                'message': 'Keine PDFs im Eingangsordner gefunden'
            })

        logger.info(f"Manueller Scan gestartet: {len(pdf_files)} PDFs gefunden")
        
        # Log-Nachricht in Queue
        processing_queue.put({
            'type': 'info',
            'message': f'Manueller Scan gestartet: {len(pdf_files)} PDF(s) gefunden',
            'timestamp': datetime.now().isoformat()
        })

        # Verarbeite alle PDFs
        success_count = 0
        error_count = 0

        for idx, pdf_file in enumerate(pdf_files, 1):
            try:
                # Fortschritts-Info
                processing_queue.put({
                    'type': 'info',
                    'message': f'[{idx}/{len(pdf_files)}] Verarbeite: {pdf_file.name}',
                    'timestamp': datetime.now().isoformat()
                })
                
                processing_queue.put({
                    'type': 'info',
                    'message': f'  → Starte OCR und Extraktion...',
                    'timestamp': datetime.now().isoformat()
                })
                
                # Verarbeite PDF mit process_single_pdf aus main.py
                from main import process_single_pdf
                
                success = process_single_pdf(pdf_file, c)
                
                if success:
                    success_count += 1
                    logger.info(f"✓ Verarbeitet: {pdf_file.name}")
                    processing_queue.put({
                        'type': 'success',
                        'message': f'✓ Erfolgreich: {pdf_file.name}',
                        'timestamp': datetime.now().isoformat()
                    })
                else:
                    error_count += 1
                    logger.error(f"✗ Fehler bei {pdf_file.name}")
                    processing_queue.put({
                        'type': 'error',
                        'message': f'✗ Fehler: {pdf_file.name}',
                        'timestamp': datetime.now().isoformat()
                    })

            except Exception as e:
                error_count += 1
                logger.error(f"✗ Exception beim Verarbeiten von {pdf_file.name}: {e}")
                processing_queue.put({
                    'type': 'error',
                    'message': f'✗ Exception: {pdf_file.name} - {str(e)}',
                    'timestamp': datetime.now().isoformat()
                })

        logger.info(f"Manueller Scan abgeschlossen: {success_count} erfolgreich, {error_count} Fehler")
        
        # Abschluss-Nachricht
        processing_queue.put({
            'type': 'success' if error_count == 0 else 'info',
            'message': f'━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━',
            'timestamp': datetime.now().isoformat()
        })
        processing_queue.put({
            'type': 'success' if error_count == 0 else 'info',
            'message': f'Scan abgeschlossen: {success_count} erfolgreich, {error_count} Fehler',
            'timestamp': datetime.now().isoformat()
        })

        return jsonify({
            'success': True,
            'processed': len(pdf_files),
            'success_count': success_count,
            'error_count': error_count,
            'message': f'{success_count} von {len(pdf_files)} PDFs erfolgreich verarbeitet'
        })

    except Exception as e:
        logger.error(f"Fehler beim manuellen Scan: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================================
# ROUTES - Watcher-Steuerung
# ============================================================

@app.route('/api/watcher/start', methods=['POST'])
def start_watcher():
    """API: Watcher starten"""
    global watcher_thread, watcher_running
    
    try:
        if watcher_running:
            return jsonify({'error': 'Watcher läuft bereits'}), 400
        
        c = get_config()
        errors = c.validate()
        if errors:  # Wenn Fehler-Liste nicht leer ist
            return jsonify({'error': f'Konfiguration ungültig: {"; ".join(errors)}'}), 400
        
        watcher_running = True
        
        def watcher_callback(pdf_path: Path):
            """Callback für neue PDFs"""
            processing_queue.put({
                'type': 'info',
                'message': f'Neue Datei erkannt: {pdf_path.name}',
                'timestamp': datetime.now().isoformat()
            })
            
            # Verarbeite PDF
            try:
                from main import process_single_pdf
                c = get_config()
                success = process_single_pdf(pdf_path, c)
                
                if success:
                    processing_queue.put({
                        'type': 'success',
                        'message': f'✓ Erfolgreich verarbeitet: {pdf_path.name}',
                        'timestamp': datetime.now().isoformat()
                    })
                else:
                    processing_queue.put({
                        'type': 'error',
                        'message': f'✗ Fehler beim Verarbeiten: {pdf_path.name}',
                        'timestamp': datetime.now().isoformat()
                    })
            except Exception as e:
                processing_queue.put({
                    'type': 'error',
                    'message': f'✗ Exception: {pdf_path.name} - {str(e)}',
                    'timestamp': datetime.now().isoformat()
                })
        
        def run_watcher():
            try:
                watcher.start_watcher(
                    c.get_input_folder(),
                    process_file_callback=watcher_callback
                )
            except Exception as e:
                logger.error(f"Watcher-Fehler: {e}")
                global watcher_running
                watcher_running = False
        
        watcher_thread = threading.Thread(target=run_watcher, daemon=True)
        watcher_thread.start()
        
        return jsonify({'success': True, 'message': 'Watcher gestartet'})
        
    except Exception as e:
        watcher_running = False
        logger.error(f"Fehler beim Starten des Watchers: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/watcher/stop', methods=['POST'])
def stop_watcher():
    """API: Watcher stoppen"""
    global watcher_running
    
    watcher_running = False
    
    return jsonify({'success': True, 'message': 'Watcher wird gestoppt'})


@app.route('/api/archive/reprocess/<int:auftrag_id>', methods=['POST'])
def reprocess_auftrag(auftrag_id):
    """API: Auftrag neu verarbeiten und korrigieren"""
    try:
        c = get_config()
        db_path = c.get_archiv_root() / "werkstatt.db"
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Hole aktuellen Eintrag
        cursor.execute('SELECT file_path, auftrag_nr FROM auftraege WHERE id = ?', (auftrag_id,))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return jsonify({'error': 'Auftrag nicht gefunden'}), 404
        
        old_file_path = Path(row[0])
        old_auftrag_nr = row[1]
        
        if not old_file_path.exists():
            logger.error(f"PDF nicht gefunden: {old_file_path} (Auftrag {old_auftrag_nr})")
            return jsonify({
                'error': f'PDF-Datei nicht gefunden: {old_file_path.name}',
                'suggestion': 'Die Datei wurde möglicherweise verschoben oder gelöscht. Bitte prüfe das Archiv.'
            }), 404
        
        # OCR neu durchführen - alle Seiten scannen
        texts = ocr.pdf_to_ocr_texts(old_file_path, max_pages=None)
        
        # Metadaten neu extrahieren (nur von Seite 1)
        metadata = auftrag_parser.extract_auftrag_metadata(texts[0], fallback_filename=old_file_path.name)
        
        # Wenn Auftragsnummer NUR aus Dateinamen kam (nicht aus OCR), versuche Enhanced-OCR
        if not metadata.get('auftrag_nr_from_ocr', True):
            logger.info(f"Auftragsnummer kam nur aus Dateinamen, versuche Enhanced-OCR mit höherer DPI...")
            texts_enhanced = ocr.pdf_to_ocr_texts_enhanced(old_file_path, max_pages=None)
            metadata_enhanced = auftrag_parser.extract_auftrag_metadata(texts_enhanced[0], fallback_filename=old_file_path.name)
            
            # Falls Enhanced-OCR die Nummer im Text gefunden hat, verwende diese Version
            if metadata_enhanced.get('auftrag_nr_from_ocr'):
                logger.info(f"✓ Auftragsnummer mit Enhanced-OCR im Text gefunden: {metadata_enhanced['auftrag_nr']}")
                texts = texts_enhanced
                metadata = metadata_enhanced
            else:
                logger.warning(f"Auch Enhanced-OCR konnte Nummer nicht im Text finden, behalte Dateinamen-Nummer")
        
        # Keywords von allen Seiten
        metadata['keywords'] = auftrag_parser.extract_keywords_from_pages(texts, c.config.get('keywords', []))
        
        # Prüfe ob neue Auftragsnummer erkannt wurde
        new_auftrag_nr = archive.format_auftrag_nr(metadata['auftrag_nr']) if metadata['auftrag_nr'] else old_auftrag_nr
        
        # Wenn sich die Nummer geändert hat, verschiebe die Datei
        if new_auftrag_nr != old_auftrag_nr:
            # Neuen Pfad berechnen
            archiv_root = c.get_archiv_root()
            
            # Jahr-basierte Struktur
            if c.config.get('use_year_folders', True):
                year = archive.get_year_from_datum(metadata.get('datum'))
                target_dir = archiv_root / year / new_auftrag_nr
            else:
                thousand_block = archive.get_thousand_block(new_auftrag_nr)
                target_dir = archiv_root / thousand_block / new_auftrag_nr
            
            target_dir.mkdir(parents=True, exist_ok=True)
            
            # Neuer Dateiname generieren
            existing_files = list(target_dir.glob("*.pdf"))
            new_filename = archive.generate_target_filename(
                new_auftrag_nr,
                c.config,
                existing_files,
                metadata
            )
            
            new_file_path = target_dir / new_filename
            
            # Verschiebe Datei
            import shutil
            shutil.move(str(old_file_path), str(new_file_path))
            
            # SICHERHEIT: Verschiebe alten Ordner in Papierkorb statt löschen
            old_dir = old_file_path.parent
            if old_dir.exists():
                # Erstelle Trash-Ordner falls nicht vorhanden
                trash_dir = archiv_root / '.trash' / datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
                trash_dir.mkdir(parents=True, exist_ok=True)
                
                # Verschiebe alten Ordner in Papierkorb statt löschen
                try:
                    import shutil
                    trash_path = trash_dir / old_dir.name
                    shutil.move(str(old_dir), str(trash_path))
                    logger.info(f"✓ Alter Ordner in Papierkorb verschoben: {old_dir.name} → {trash_path}")
                    logger.info(f"  Kann bei Bedarf aus {trash_dir} wiederhergestellt werden")
                except Exception as e:
                    logger.warning(f"Konnte alten Ordner nicht verschieben: {e}")
            
            logger.info(f"Auftrag {old_auftrag_nr} → {new_auftrag_nr}: {new_file_path}")
        else:
            new_file_path = old_file_path
        
        # Datenbank aktualisieren
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
        
        return jsonify({
            'success': True,
            'message': f'Auftrag erfolgreich neu verarbeitet',
            'old_auftrag_nr': old_auftrag_nr,
            'new_auftrag_nr': new_auftrag_nr,
            'changed': new_auftrag_nr != old_auftrag_nr,
            'new_path': str(new_file_path)
        })
        
    except Exception as e:
        logger.error(f"Fehler beim Neu-Verarbeiten: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


# ============================================================
# ROUTES - Backup & Restore
# ============================================================

@app.route('/api/backup/stats', methods=['GET'])
def backup_stats():
    """API: Backup-Statistiken abrufen"""
    try:
        c = get_config()
        db_path = c.get_archiv_root() / "werkstatt.db"
        archiv_root = c.get_archiv_root()
        
        # Zähle Aufträge in DB
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM auftraege')
        db_count = cursor.fetchone()[0]
        conn.close()
        
        # Zähle CSV-Dateien
        csv_files = list(archiv_root.rglob('data.csv'))
        csv_count = len(csv_files)
        
        # Finde neueste CSV
        last_backup = None
        for csv_file in csv_files:
            meta_file = csv_file.parent / 'meta.json'
            if meta_file.exists():
                try:
                    with open(meta_file, 'r') as f:
                        meta = json.load(f)
                        exported_at = meta.get('exported_at')
                        if exported_at:
                            if not last_backup or exported_at > last_backup:
                                last_backup = exported_at
                except:
                    pass
        
        return jsonify({
            'db_count': db_count,
            'csv_count': csv_count,
            'last_backup': last_backup
        })
        
    except Exception as e:
        logger.error(f"Fehler beim Abrufen der Backup-Stats: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/backup/export', methods=['POST'])
def backup_export():
    """API: Backup erstellen"""
    try:
        c = get_config()
        db_path = c.get_archiv_root() / "werkstatt.db"
        archiv_root = c.get_archiv_root()
        
        # Importiere backup_system
        import backup_system
        
        system = backup_system.BackupSystem(db_path, archiv_root)
        start_time = time.time()
        stats = system.export_all()
        stats['duration'] = time.time() - start_time
        
        return jsonify({'success': True, 'stats': stats})
        
    except Exception as e:
        logger.error(f"Fehler beim Backup-Export: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/backup/verify', methods=['POST'])
def backup_verify():
    """API: Backups validieren"""
    try:
        c = get_config()
        db_path = c.get_archiv_root() / "werkstatt.db"
        archiv_root = c.get_archiv_root()
        
        import backup_system
        
        system = backup_system.BackupSystem(db_path, archiv_root)
        start_time = time.time()
        stats = system.verify()
        stats['duration'] = time.time() - start_time
        
        return jsonify({'success': True, 'stats': stats})
        
    except Exception as e:
        logger.error(f"Fehler bei Backup-Verify: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/backup/restore', methods=['POST'])
def backup_restore():
    """API: Datenbank wiederherstellen"""
    try:
        c = get_config()
        db_path = c.get_archiv_root() / "werkstatt.db"
        archiv_root = c.get_archiv_root()
        
        import backup_system
        
        system = backup_system.BackupSystem(db_path, archiv_root)
        start_time = time.time()
        stats = system.restore_all(dry_run=False)
        stats['duration'] = time.time() - start_time
        
        return jsonify({'success': True, 'stats': stats})
        
    except Exception as e:
        logger.error(f"Fehler bei Restore: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/backup/log', methods=['GET'])
def backup_log():
    """API: Backup-Log abrufen"""
    try:
        log_file = Path('backup_system.log')
        
        if not log_file.exists():
            return 'Keine Log-Datei gefunden', 200
        
        # Letzte 50 Zeilen
        with open(log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            last_lines = lines[-50:] if len(lines) > 50 else lines
            return ''.join(last_lines), 200
        
    except Exception as e:
        logger.error(f"Fehler beim Laden des Logs: {e}")
        return f'Fehler: {e}', 500


@app.route('/api/backup/create-zip', methods=['POST'])
def create_zip_backup():
    """API: ZIP-Backup erstellen"""
    try:
        import backup
        
        c = get_config()
        
        # Prüfe ob Backup-Ziel gesetzt ist
        backup_target = c.get_backup_target_dir()
        if not backup_target:
            return jsonify({
                'success': False, 
                'error': 'Kein Backup-Zielordner konfiguriert! Bitte unter Einstellungen setzen.'
            }), 400
        
        # Parameter aus Request
        data = request.get_json() or {}
        include_archive = data.get('include_archive', False)
        
        # Pfade
        archiv_root = c.get_archiv_root()
        db_path = archiv_root / 'werkstatt.db'
        
        # Config-Datei finden (.json oder .yaml)
        config_path = None
        for ext in ['.json', '.yaml']:
            candidate = Path(f'.archiv_config{ext}')
            if candidate.exists():
                config_path = candidate
                break
        
        if not config_path:
            return jsonify({
                'success': False,
                'error': 'Keine Konfigurationsdatei gefunden'
            }), 500
        
        logger.info(f"Starte ZIP-Backup (include_archive={include_archive})")
        
        # Backup erstellen
        backup_path = backup.create_backup(
            archiv_root=archiv_root,
            db_path=db_path,
            config_path=config_path,
            backup_target_dir=backup_target,
            include_archive=include_archive
        )
        
        # Alte Backups aufräumen (behalte 10 neueste)
        backup.cleanup_old_backups(backup_target, keep_count=10)
        
        # Datei-Größe ermitteln
        size_bytes = backup_path.stat().st_size
        
        return jsonify({
            'success': True,
            'path': str(backup_path),
            'filename': backup_path.name,
            'size_bytes': size_bytes
        })
        
    except Exception as e:
        logger.error(f"Fehler beim ZIP-Backup: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================
# ROUTES - Folder Import
# ============================================================

@app.route('/api/folders/list', methods=['GET'])
def list_folders():
    """API: Liste alle Ordner im Eingangsverzeichnis"""
    try:
        c = get_config()
        input_folder = c.get_input_folder()
        
        if not input_folder or not input_folder.exists():
            return jsonify({'success': False, 'error': 'Eingangsordner nicht gefunden'}), 400
        
        folders = []
        
        # Finde alle Unterordner (nicht rekursiv, nur direkte Kinder)
        for item in input_folder.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                # Ignoriere spezielle Ordner
                if item.name in ['Fehler', 'temp_backup', '.trash']:
                    continue
                
                # Zähle PDFs im Ordner
                pdf_count = len(list(item.glob('*.pdf')))
                
                if pdf_count > 0:
                    # Versuche Auftragsnummer aus Ordnername zu extrahieren
                    import re
                    suggested_auftrag = None
                    
                    # Suche nach Zahlen im Ordnername (5-6 Ziffern)
                    match = re.search(r'\b(\d{5,6})\b', item.name)
                    if match:
                        suggested_auftrag = match.group(1)
                    
                    folders.append({
                        'name': item.name,
                        'path': str(item),
                        'pdf_count': pdf_count,
                        'suggested_auftrag': suggested_auftrag
                    })
        
        # Sortiere nach Name
        folders.sort(key=lambda x: x['name'])
        
        return jsonify({
            'success': True,
            'folders': folders,
            'count': len(folders)
        })
        
    except Exception as e:
        logger.error(f"Fehler beim Listen der Ordner: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/folders/import', methods=['POST'])
def import_folders():
    """API: Importiere mehrere Ordner"""
    try:
        import folder_import
        
        c = get_config()
        input_folder = c.get_input_folder()
        
        data = request.get_json() or {}
        folder_names = data.get('folders', [])
        
        if not folder_names:
            return jsonify({'success': False, 'error': 'Keine Ordner angegeben'}), 400
        
        # Log Start
        processing_queue.put({
            'type': 'info',
            'message': f'Starte Ordner-Import: {len(folder_names)} Ordner',
            'timestamp': datetime.now().isoformat()
        })
        
        results = []
        current = 0
        
        for folder_name in folder_names:
            current += 1
            folder_path = input_folder / folder_name
            
            # Fortschritts-Info
            processing_queue.put({
                'type': 'info',
                'message': f'[{current}/{len(folder_names)}] Verarbeite: {folder_name}',
                'timestamp': datetime.now().isoformat()
            })
            
            if not folder_path.exists() or not folder_path.is_dir():
                processing_queue.put({
                    'type': 'error',
                    'message': f'✗ Ordner nicht gefunden: {folder_name}',
                    'timestamp': datetime.now().isoformat()
                })
                results.append({
                    'folder': folder_name,
                    'success': False,
                    'error': 'Ordner nicht gefunden'
                })
                continue
            
            # Zähle PDFs im Ordner
            pdf_count = len(list(folder_path.glob('*.pdf')))
            processing_queue.put({
                'type': 'info',
                'message': f'  → {pdf_count} PDF(s) gefunden in {folder_name}',
                'timestamp': datetime.now().isoformat()
            })
            
            try:
                logger.info(f"Importiere Ordner: {folder_name}")
                processing_queue.put({
                    'type': 'info',
                    'message': f'  → Starte OCR und Extraktion...',
                    'timestamp': datetime.now().isoformat()
                })
                
                # Nutze folder_import.process_folder_for_import (gibt Dict zurück!)
                result = folder_import.process_folder_for_import(folder_path, c)
                
                if result and result.get('success'):
                    processing_queue.put({
                        'type': 'success',
                        'message': f'✓ Erfolgreich importiert: {folder_name} (Auftrag {result.get("auftrag_nr", "?")})',
                        'timestamp': datetime.now().isoformat()
                    })
                    results.append({
                        'folder': folder_name,
                        'success': True,
                        'message': f'Erfolgreich importiert als {result.get("auftrag_nr", "?")}',
                        'auftrag_nr': result.get('auftrag_nr'),
                        'pdf_count': result.get('pdf_count')
                    })
                else:
                    processing_queue.put({
                        'type': 'error',
                        'message': f'✗ Import fehlgeschlagen: {folder_name}',
                        'timestamp': datetime.now().isoformat()
                    })
                    results.append({
                        'folder': folder_name,
                        'success': False,
                        'error': 'Import fehlgeschlagen (siehe Logs)'
                    })
                    
            except Exception as e:
                logger.error(f"Fehler beim Import von {folder_name}: {e}", exc_info=True)
                processing_queue.put({
                    'type': 'error',
                    'message': f'✗ Exception: {folder_name} - {str(e)}',
                    'timestamp': datetime.now().isoformat()
                })
                results.append({
                    'folder': folder_name,
                    'success': False,
                    'error': str(e)
                })
        
        # Zähle Erfolge
        successful = sum(1 for r in results if r['success'])
        failed = len(results) - successful
        
        # Abschluss-Nachricht
        processing_queue.put({
            'type': 'success' if failed == 0 else 'info',
            'message': f'━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━',
            'timestamp': datetime.now().isoformat()
        })
        processing_queue.put({
            'type': 'success' if failed == 0 else 'info',
            'message': f'Ordner-Import abgeschlossen: {successful} erfolgreich, {failed} Fehler',
            'timestamp': datetime.now().isoformat()
        })
        
        return jsonify({
            'success': True,
            'results': results,
            'total': len(results),
            'successful': successful,
            'failed': failed
        })
        
    except Exception as e:
        logger.error(f"Fehler beim Ordner-Import: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================
# ROUTES - Keywords Management
# ============================================================

@app.route('/keywords')
def keywords_page():
    """Schlagwörter-Verwaltung"""
    return render_template('keywords.html')


@app.route('/api/keywords', methods=['GET'])
def get_keywords():
    """API: Schlagwörter abrufen"""
    try:
        c = get_config()
        keywords = c.config.get('keywords', [])
        return jsonify({'keywords': keywords, 'count': len(keywords)})
    except Exception as e:
        logger.error(f"Fehler beim Laden der Schlagwörter: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/keywords', methods=['POST'])
def save_keywords():
    """API: Schlagwörter speichern"""
    try:
        data = request.get_json()
        new_keywords = data.get('keywords', [])
        
        # Validierung
        if not isinstance(new_keywords, list):
            return jsonify({'success': False, 'message': 'Keywords müssen eine Liste sein'}), 400
        
        # Entferne Duplikate und leere Einträge
        cleaned_keywords = list(set([k.strip() for k in new_keywords if k and k.strip()]))
        
        # Speichere in Config
        c = get_config()
        c.config['keywords'] = cleaned_keywords
        c.save_config()
        
        logger.info(f"Schlagwörter aktualisiert: {len(cleaned_keywords)} Einträge")
        return jsonify({'success': True, 'count': len(cleaned_keywords)})
        
    except Exception as e:
        logger.error(f"Fehler beim Speichern der Schlagwörter: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


# Globale Variablen für Re-Scan Status
rescan_status = {
    'running': False,
    'progress': 0,
    'processed': 0,
    'total': 0,
    'status': 'Bereit',
    'finished': False
}


@app.route('/api/keywords/rescan', methods=['POST'])
def start_keyword_rescan():
    """API: Neu-Verschlagwortung aller PDFs starten"""
    global rescan_status
    
    if rescan_status['running']:
        return jsonify({'success': False, 'message': 'Re-Scan läuft bereits'}), 409
    
    # Starte Re-Scan in separatem Thread
    def run_rescan():
        global rescan_status
        
        try:
            rescan_status['running'] = True
            rescan_status['progress'] = 0
            rescan_status['processed'] = 0
            rescan_status['finished'] = False
            rescan_status['status'] = 'Initialisiere...'
            
            c = get_config()
            db_path = c.get_archiv_root() / "werkstatt.db"
            keywords_list = c.config.get('keywords', [])
            
            if not db_path.exists():
                rescan_status['status'] = 'Fehler: Datenbank nicht gefunden'
                rescan_status['running'] = False
                rescan_status['finished'] = True
                return
            
            # Hole alle Aufträge
            conn = sqlite3.connect(str(db_path))
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT id, auftrag_nr, file_path FROM auftraege')
            auftraege = cursor.fetchall()
            conn.close()
            
            rescan_status['total'] = len(auftraege)
            rescan_status['status'] = f'Verarbeite {len(auftraege)} Aufträge...'
            
            # Verarbeite jeden Auftrag
            for idx, auftrag in enumerate(auftraege):
                try:
                    file_path = Path(auftrag['file_path'])
                    
                    if not file_path.exists():
                        logger.warning(f"PDF nicht gefunden: {file_path}")
                        continue
                    
                    # OCR für alle Seiten
                    try:
                        ocr_texts = ocr.pdf_to_ocr_texts(file_path, max_pages=None)
                        
                        # Extrahiere Keywords aus allen Seiten außer Seite 1
                        attachment_texts = ocr_texts[1:] if len(ocr_texts) > 1 else []
                        found_keywords = auftrag_parser.extract_keywords_from_pages(
                            attachment_texts, 
                            keywords_list
                        )
                        
                        # Aktualisiere Datenbank
                        keywords_json = json.dumps(found_keywords, ensure_ascii=False)
                        conn = sqlite3.connect(str(db_path))
                        cursor = conn.cursor()
                        cursor.execute(
                            'UPDATE auftraege SET keywords_json = ? WHERE id = ?',
                            (keywords_json, auftrag['id'])
                        )
                        conn.commit()
                        conn.close()
                        
                        logger.info(f"Re-Scan: {auftrag['auftrag_nr']} - {len(found_keywords)} Schlagwörter gefunden")
                        
                    except Exception as ocr_error:
                        logger.error(f"OCR-Fehler bei {auftrag['auftrag_nr']}: {ocr_error}")
                        continue
                    
                except Exception as e:
                    logger.error(f"Fehler bei Auftrag {auftrag.get('auftrag_nr')}: {e}")
                    continue
                finally:
                    rescan_status['processed'] = idx + 1
                    rescan_status['progress'] = int((idx + 1) / len(auftraege) * 100)
                    rescan_status['status'] = f'{idx + 1}/{len(auftraege)} Aufträge bearbeitet'
            
            rescan_status['status'] = f'Abgeschlossen: {rescan_status["processed"]} Aufträge bearbeitet'
            rescan_status['finished'] = True
            logger.info(f"Re-Scan abgeschlossen: {rescan_status['processed']}/{rescan_status['total']} Aufträge")
            
        except Exception as e:
            logger.error(f"Re-Scan Fehler: {e}")
            rescan_status['status'] = f'Fehler: {e}'
            rescan_status['finished'] = True
        finally:
            rescan_status['running'] = False
    
    # Starte Thread
    thread = threading.Thread(target=run_rescan, daemon=True)
    thread.start()
    
    return jsonify({'success': True, 'message': 'Re-Scan gestartet'})


@app.route('/api/keywords/rescan/status', methods=['GET'])
def get_rescan_status():
    """API: Re-Scan Status abrufen"""
    return jsonify(rescan_status)


# ============================================================
# SERVER-START
# ============================================================

class ServerThread(threading.Thread):
    """Thread für Flask-Server"""
    
    def __init__(self, app, host='127.0.0.1', port=5000):
        threading.Thread.__init__(self)
        self.server = make_server(host, port, app)
        self.ctx = app.app_context()
        self.ctx.push()
    
    def run(self):
        logger.info(f'Server läuft auf http://{self.server.host}:{self.server.port}')
        self.server.serve_forever()
    
    def shutdown(self):
        self.server.shutdown()


def start_server(host='127.0.0.1', port=5000):
    """Starte Web-Server"""
    global server_thread
    
    # Erstelle Template-Ordner wenn nicht vorhanden
    templates_dir = Path(__file__).parent / 'templates'
    templates_dir.mkdir(exist_ok=True)
    
    static_dir = Path(__file__).parent / 'static'
    static_dir.mkdir(exist_ok=True)
    
    server_thread = ServerThread(app, host, port)
    server_thread.daemon = True
    server_thread.start()
    
    logger.info(f"Web-UI verfügbar unter: http://{host}:{port}")
    
    return server_thread


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Werkstatt-Archiv Web-UI')
    parser.add_argument('--host', default='127.0.0.1', help='Host-Adresse (Standard: 127.0.0.1)')
    parser.add_argument('--port', type=int, default=5000, help='Port (Standard: 5000)')
    parser.add_argument('--debug', action='store_true', help='Debug-Modus')
    parser.add_argument('--threaded', action='store_true', default=True, help='Threaded-Modus (Standard: aktiviert)')
    
    args = parser.parse_args()
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        app.config['DEBUG'] = True
    
    # Config initialisieren
    cfg = config.Config()
    
    print("")
    print("=" * 60)
    print("  Werkstatt-Archiv Web-UI")
    print("=" * 60)
    print(f"  Host:    {args.host}")
    print(f"  Port:    {args.port}")
    print(f"  URL:     http://{args.host}:{args.port}")
    print(f"  Debug:   {'Ja' if args.debug else 'Nein'}")
    print("=" * 60)
    print("")
    
    logger.info("="*60)
    logger.info("Werkstatt-Archiv Web-UI")
    logger.info("="*60)
    logger.info(f"Server-Adresse: http://{args.host}:{args.port}")
    logger.info(f"Debug-Modus: {'Aktiviert' if args.debug else 'Deaktiviert'}")
    logger.info(f"Threads: 6 (Waitress Production Server)")
    logger.info("="*60)
    
    try:
        if args.debug:
            # Development-Modus: Flask Development Server
            logger.warning("WARNUNG: Debug-Modus nutzt Flask Development Server!")
            print("[DEBUG] Starte Flask Development Server...")
            app.run(
                host=args.host, 
                port=args.port, 
                debug=True,
                use_reloader=False
            )
        else:
            # Production-Modus: Waitress WSGI Server
            from waitress import serve
            print("[INFO] Starte Waitress Production Server...")
            print(f"[INFO] Server lauscht auf http://{args.host}:{args.port}")
            print("")
            print("[INFO] Druecke Strg+C zum Beenden")
            print("")
            logger.info("Starte Waitress Production Server...")
            serve(
                app,
                host=args.host,
                port=args.port,
                threads=6,
                channel_timeout=60,
                cleanup_interval=30,
                _quiet=False
            )
    except KeyboardInterrupt:
        print("")
        print("[INFO] Server wird beendet...")
        logger.info("\nServer wird beendet...")
    except OSError as e:
        if "Address already in use" in str(e) or "10048" in str(e):
            print("")
            print("=" * 60)
            print("[FEHLER] Port ist bereits belegt!")
            print("=" * 60)
            print(f"Port {args.port} wird bereits verwendet.")
            print("")
            print("Loesungen:")
            print(f"  1. Anderen Port verwenden: python web_app.py --port 8081")
            print(f"  2. Alten Prozess beenden:")
            print(f"     Windows: netstat -ano | findstr :{args.port}")
            print(f"              taskkill /F /PID <PID>")
            print("")
            logger.error(f"Port {args.port} bereits belegt: {e}")
        else:
            print("")
            print("=" * 60)
            print(f"[FEHLER] Netzwerk-Fehler: {e}")
            print("=" * 60)
            logger.error(f"OSError: {e}")
        raise
    except Exception as e:
        print("")
        print("=" * 60)
        print(f"[FEHLER] Server-Fehler: {e}")
        print("=" * 60)
        print("")
        print("Details:")
        import traceback
        traceback.print_exc()
        print("")
        logger.error(f"Server-Fehler: {e}")
        raise
