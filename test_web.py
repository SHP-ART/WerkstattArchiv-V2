#!/usr/bin/env python3
"""Minimale Test-Version der Web-UI"""

from flask import Flask, render_template
import config

app = Flask(__name__)

# Config laden
cfg = config.Config()

@app.route('/')
def index():
    return f'''
    <html>
    <head><title>Werkstatt-Archiv</title></head>
    <body>
        <h1>Werkstatt-Archiv Web-UI</h1>
        <p>Server läuft!</p>
        <p>Input: {cfg.get_input_folder()}</p>
        <p>Archiv: {cfg.get_archiv_root()}</p>
    </body>
    </html>
    '''

if __name__ == '__main__':
    print("Starte auf http://127.0.0.1:8080")
    app.run(host='127.0.0.1', port=8080, debug=True)
