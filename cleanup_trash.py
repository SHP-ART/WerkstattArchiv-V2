#!/usr/bin/env python3
"""
Papierkorb-Verwaltung für Werkstatt-Archiv

Dieses Script verwaltet den .trash Ordner im Archiv:
- Listet alle gelöschten Ordner auf
- Ermöglicht Wiederherstellung
- Löscht alte Einträge nach Bestätigung

SICHERHEIT: Nichts wird automatisch gelöscht!
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
import shutil

import config


def list_trash_items():
    """Listet alle Einträge im Papierkorb"""
    cfg = config.Config()
    archiv_root = cfg.get_archiv_root()
    trash_dir = archiv_root / '.trash'
    
    if not trash_dir.exists():
        print("✓ Papierkorb ist leer")
        return []
    
    items = []
    for timestamp_dir in sorted(trash_dir.iterdir(), reverse=True):
        if not timestamp_dir.is_dir():
            continue
            
        timestamp = timestamp_dir.name
        for item in timestamp_dir.iterdir():
            size_mb = sum(f.stat().st_size for f in item.rglob('*') if f.is_file()) / (1024*1024)
            items.append({
                'timestamp': timestamp,
                'name': item.name,
                'path': item,
                'size_mb': size_mb
            })
    
    return items


def show_trash_list():
    """Zeigt Papierkorb-Inhalt"""
    items = list_trash_items()
    
    if not items:
        print("\n✓ Papierkorb ist leer\n")
        return
    
    print("\n" + "="*70)
    print("  PAPIERKORB - Gelöschte Ordner")
    print("="*70)
    print()
    
    total_size = 0
    for i, item in enumerate(items, 1):
        print(f"{i}. {item['name']}")
        print(f"   Gelöscht am: {item['timestamp']}")
        print(f"   Größe: {item['size_mb']:.2f} MB")
        print(f"   Pfad: {item['path']}")
        print()
        total_size += item['size_mb']
    
    print(f"Gesamt: {len(items)} Ordner, {total_size:.2f} MB")
    print("="*70)


def restore_item(item_number: int):
    """Stellt einen Ordner wieder her"""
    items = list_trash_items()
    
    if item_number < 1 or item_number > len(items):
        print(f"❌ Ungültige Nummer: {item_number}")
        return False
    
    item = items[item_number - 1]
    cfg = config.Config()
    archiv_root = cfg.get_archiv_root()
    
    # Zielordner bestimmen (z.B. 2024/075203)
    # Annahme: Ordnername ist Auftragsnummer
    auftrag_nr = item['name']
    
    # Finde passenden Jahr-Ordner
    jahr_ordner = None
    for year_dir in archiv_root.iterdir():
        if year_dir.is_dir() and year_dir.name.isdigit():
            jahr_ordner = year_dir
            break
    
    if not jahr_ordner:
        # Erstelle aktuelles Jahr
        jahr_ordner = archiv_root / str(datetime.now().year)
        jahr_ordner.mkdir(exist_ok=True)
    
    restore_path = jahr_ordner / auftrag_nr
    
    if restore_path.exists():
        print(f"❌ Zielordner existiert bereits: {restore_path}")
        print(f"   Bitte manuell wiederherstellen oder umbenennen")
        return False
    
    # Wiederherstellen
    try:
        shutil.move(str(item['path']), str(restore_path))
        print(f"✓ Wiederhergestellt: {auftrag_nr} → {restore_path}")
        
        # Lösche leeren Timestamp-Ordner
        timestamp_dir = item['path'].parent
        if not list(timestamp_dir.iterdir()):
            timestamp_dir.rmdir()
        
        return True
    except Exception as e:
        print(f"❌ Fehler beim Wiederherstellen: {e}")
        return False


def empty_trash(older_than_days: int = 0):
    """Leert Papierkorb (optional nur ältere Einträge)"""
    items = list_trash_items()
    
    if not items:
        print("\n✓ Papierkorb ist bereits leer\n")
        return
    
    # Filter nach Alter
    if older_than_days > 0:
        cutoff_date = datetime.now() - timedelta(days=older_than_days)
        filtered_items = []
        for item in items:
            try:
                item_date = datetime.strptime(item['timestamp'], '%Y-%m-%d_%H-%M-%S')
                if item_date < cutoff_date:
                    filtered_items.append(item)
            except:
                filtered_items.append(item)
        items = filtered_items
    
    if not items:
        print(f"\n✓ Keine Einträge älter als {older_than_days} Tage\n")
        return
    
    print(f"\n⚠️  {len(items)} Ordner werden ENDGÜLTIG gelöscht!")
    for item in items:
        print(f"   - {item['name']} ({item['timestamp']})")
    
    confirm = input("\nWirklich löschen? (ja/nein): ").strip().lower()
    
    if confirm != 'ja':
        print("❌ Abgebrochen")
        return
    
    # Lösche Ordner
    deleted = 0
    cfg = config.Config()
    archiv_root = cfg.get_archiv_root()
    trash_dir = archiv_root / '.trash'
    
    for item in items:
        try:
            shutil.rmtree(item['path'])
            deleted += 1
        except Exception as e:
            print(f"❌ Fehler beim Löschen von {item['name']}: {e}")
    
    # Lösche leere Timestamp-Ordner
    for timestamp_dir in trash_dir.iterdir():
        try:
            if timestamp_dir.is_dir() and not list(timestamp_dir.iterdir()):
                timestamp_dir.rmdir()
        except:
            pass
    
    print(f"\n✓ {deleted} Ordner endgültig gelöscht")


def main():
    """Hauptfunktion"""
    if len(sys.argv) < 2:
        print("\nPapierkorb-Verwaltung - Werkstatt-Archiv")
        print("\nVerwendung:")
        print("  python cleanup_trash.py list              - Zeige Papierkorb-Inhalt")
        print("  python cleanup_trash.py restore <nummer>  - Ordner wiederherstellen")
        print("  python cleanup_trash.py empty             - Papierkorb leeren (mit Bestätigung)")
        print("  python cleanup_trash.py empty --days 30   - Nur Einträge älter als 30 Tage")
        print()
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == 'list':
        show_trash_list()
    
    elif command == 'restore':
        if len(sys.argv) < 3:
            print("❌ Bitte Nummer angeben: python cleanup_trash.py restore <nummer>")
            sys.exit(1)
        try:
            item_number = int(sys.argv[2])
            restore_item(item_number)
        except ValueError:
            print("❌ Ungültige Nummer")
            sys.exit(1)
    
    elif command == 'empty':
        days = 0
        if '--days' in sys.argv:
            try:
                days_idx = sys.argv.index('--days')
                days = int(sys.argv[days_idx + 1])
            except (ValueError, IndexError):
                print("❌ Ungültiger --days Parameter")
                sys.exit(1)
        empty_trash(older_than_days=days)
    
    else:
        print(f"❌ Unbekannter Befehl: {command}")
        sys.exit(1)


if __name__ == '__main__':
    main()
