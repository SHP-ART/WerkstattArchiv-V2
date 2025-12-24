# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller Spec-Datei für Werkstatt-Archiv Server (Standalone)
Erstellt eine eigenständige server.exe für Windows
"""

from pathlib import Path

block_cipher = None

a = Analysis(
    ['server.py'],
    pathex=['.'],  # Aktuelles Verzeichnis für lokale Module
    binaries=[],
    datas=[
        ('templates', 'templates'),
        ('Logo', 'Logo'),
        # Lokale Module als Daten
        ('config.py', '.'),
        ('ocr.py', '.'),
        ('parser.py', '.'),
        ('archive.py', '.'),
        ('db.py', '.'),
        ('watcher.py', '.'),
        ('kunden_index.py', '.'),
        ('backup.py', '.'),
        ('web_app.py', '.'),
        # Installations-Scripte für Deployment
        ('install_tesseract.bat', '.'),
        ('install_poppler.bat', '.'),
        ('diagnose_tesseract.bat', '.'),
        ('diagnose_poppler.bat', '.'),
    ],
    hiddenimports=[
        # Web-Framework
        'waitress',
        'flask',
        'flask.app',
        'flask.templating',
        'flask.json',
        'jinja2',
        'jinja2.ext',
        
        # OCR und PDF
        'pytesseract',
        'pdf2image',
        'PIL',
        'PIL.Image',
        'PIL.ImageFilter',
        'PIL.ImageEnhance',
        'PyPDF2',
        
        # Dateisystem-Überwachung
        'watchdog',
        'watchdog.observers',
        'watchdog.events',
        'watchdog.observers.polling',
        
        # Werkstatt-Archiv Module
        'config',
        'ocr',
        'parser',
        'archive',
        'db',
        'watcher',
        'kunden_index',
        'backup',
        'web_app',
        
        # Standard-Bibliotheken
        'yaml',
        'sqlite3',
        'json',
        'pathlib',
        'datetime',
        'logging',
        'queue',
        'threading',
        'hashlib',
        'shutil',
        'zipfile',
        'csv',
        're',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Unnötige Pakete ausschließen
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
        'tkinter',
        'pygame',
        'IPython',
        'jupyter',
        'notebook',
        'pytest',
        'setuptools',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='WerkstattArchiv-Server',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # Console-Fenster für Logs
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Optional: Logo/icon.ico wenn vorhanden
)
