# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller Spec-Datei für Werkstatt-Archiv Server (Standalone)
Erstellt eine eigenständige server.exe für Windows
"""

block_cipher = None

a = Analysis(
    ['server.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('templates', 'templates'),
        ('Logo', 'Logo'),
        ('.archiv_config.json', '.') if Path('.archiv_config.json').exists() else None,
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

# Datas bereinigen (None-Einträge entfernen)
a.datas = [d for d in a.datas if d is not None]

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
